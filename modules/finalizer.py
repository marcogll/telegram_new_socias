import os
import json
import logging
import requests
from datetime import datetime, time as time_cls

from modules.database import SessionVanityHr
from models.vanity_hr_models import HorarioEmpleadas, DataEmpleadas

def _send_webhook(url: str, payload: dict):
    """Sends a POST request to a webhook."""
    if not url:
        logging.warning("No webhook URL provided.")
        return False
    try:
        headers = {"Content-Type": "application/json"}
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        res.raise_for_status()
        logging.info(f"Webhook sent successfully to: {url}")
        return True
    except Exception as e:
        logging.error(f"Error sending webhook to {url}: {e}")
        return False

def _convert_to_time(time_str: str):
    """Converts a string like '10:00 AM' to a datetime.time object."""
    if not time_str or not isinstance(time_str, str):
        return None
    try:
        # Handle 'Todo el día' or other non-time strings
        if ":" not in time_str:
            return None
        return datetime.strptime(time_str, '%I:%M %p').time()
    except ValueError:
        logging.warning(f"Could not parse time string: {time_str}")
        return None

def _finalize_horario(telegram_id: int, data: dict):
    """Finalizes the 'horario' flow."""
    logging.info(f"Finalizing 'horario' flow for telegram_id: {telegram_id}")

    # 1. Prepare data for webhook and DB
    day_pairs = [
        ("monday", "MONDAY_IN", "MONDAY_OUT"),
        ("tuesday", "TUESDAY_IN", "TUESDAY_OUT"),
        ("wednesday", "WEDNESDAY_IN", "WEDNESDAY_OUT"),
        ("thursday", "THURSDAY_IN", "THURSDAY_OUT"),
        ("friday", "FRIDAY_IN", "FRIDAY_OUT"),
        ("saturday", "SATURDAY_IN", None),
    ]

    schedule_data = {
        "telegram_id": telegram_id,
        "short_name": data.get("SHORT_NAME"),
    }

    rows_for_db = []
    for day_key, in_key, out_key in day_pairs:
        entrada = _convert_to_time(data.get(in_key))
        salida_raw = data.get(out_key) if out_key else "6:00 PM"
        salida = _convert_to_time(salida_raw)

        schedule_data[f"{day_key}_in"] = entrada
        schedule_data[f"{day_key}_out"] = salida

        if not entrada or not salida:
            logging.warning(f"Missing schedule data for {day_key}. Entrada: {entrada}, Salida: {salida}")
            continue

        rows_for_db.append(
            {
                "dia_semana": day_key,
                "hora_entrada": entrada,
                "hora_salida": salida,
            }
        )

    # 2. Send to webhook
    webhook_url = os.getenv("WEBHOOK_SCHEDULE")
    if webhook_url:
        json_payload = {
            k: (v.isoformat() if isinstance(v, time_cls) else v) for k, v in schedule_data.items()
        }
        json_payload["timestamp"] = datetime.now().isoformat()
        _send_webhook(webhook_url, json_payload)

    # 3. Save to database (vanity_hr.horario_empleadas)
    if not SessionVanityHr:
        logging.error("SessionVanityHr is not initialized. Cannot persist horarios.")
        return False

    session = SessionVanityHr()
    try:
        empleada = session.query(DataEmpleadas).filter(DataEmpleadas.telegram_chat_id == telegram_id).first()
        numero_empleado = empleada.numero_empleado if empleada else None
        if not numero_empleado:
            logging.warning(f"No se encontró numero_empleado para telegram_id={telegram_id}. Se guardará NULL.")

        existing_rows = {
            row.dia_semana: row
            for row in session.query(HorarioEmpleadas).filter_by(telegram_id=telegram_id).all()
        }

        for row in rows_for_db:
            dia = row["dia_semana"]
            entrada = row["hora_entrada"]
            salida = row["hora_salida"]
            existing = existing_rows.get(dia)
            if existing:
                existing.numero_empleado = numero_empleado or existing.numero_empleado
                existing.hora_entrada_teorica = entrada
                existing.hora_salida_teorica = salida
            else:
                session.add(
                    HorarioEmpleadas(
                        numero_empleado=numero_empleado,
                        telegram_id=telegram_id,
                        dia_semana=dia,
                        hora_entrada_teorica=entrada,
                        hora_salida_teorica=salida,
                    )
                )

        session.commit()
        return True
    except Exception as e:
        logging.error(f"Database error in _finalize_horario: {e}")
        session.rollback()
        return False
    finally:
        session.close()


# Mapping of flow names to finalization functions
FINALIZATION_MAP = {
    "horario": _finalize_horario,
    # Add other flows here, e.g., "onboarding": _finalize_onboarding
}


async def finalize_flow(update, context):
    """Generic function to finalize a conversation flow."""
    flow_name = context.user_data.get("flow_name")
    telegram_id = update.effective_user.id

    if not flow_name:
        logging.error("finalize_flow called without a flow_name in user_data.")
        return

    finalizer_func = FINALIZATION_MAP.get(flow_name)
    if not finalizer_func:
        logging.warning(f"No finalizer function found for flow: {flow_name}")
        await update.message.reply_text("Flujo completado (sin acción final definida).")
        return

    # The final answer needs to be saved first
    current_state_key = context.user_data.get("current_state")
    if current_state_key:
        flow_definition_path = os.path.join("conv-flows", f"{flow_name}.json")
        with open(flow_definition_path, 'r') as f:
            flow = json.load(f)
        current_step = next((step for step in flow["steps"] if step["state"] == current_state_key), None)
        if current_step:
            variable_name = current_step.get("variable")
            if variable_name:
                context.user_data[variable_name] = update.message.text


    success = finalizer_func(telegram_id, context.user_data)

    if success:
        await update.message.reply_text("¡Horario guardado con éxito! 👍")
    else:
        await update.message.reply_text("Ocurrió un error al guardar tu horario. Por favor, contacta a un administrador.")
