import os
import json
import logging
import requests
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from modules.database import get_engine
from models.vanity_attendance_models import HorariosConfigurados

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

    # 1. Prepare data
    schedule_data = {
        "telegram_id": telegram_id,
        "short_name": data.get("SHORT_NAME"),
        "monday_in": _convert_to_time(data.get("MONDAY_IN")),
        "monday_out": _convert_to_time(data.get("MONDAY_OUT")),
        "tuesday_in": _convert_to_time(data.get("TUESDAY_IN")),
        "tuesday_out": _convert_to_time(data.get("TUESDAY_OUT")),
        "wednesday_in": _convert_to_time(data.get("WEDNESDAY_IN")),
        "wednesday_out": _convert_to_time(data.get("WEDNESDAY_OUT")),
        "thursday_in": _convert_to_time(data.get("THURSDAY_IN")),
        "thursday_out": _convert_to_time(data.get("THURSDAY_OUT")),
        "friday_in": _convert_to_time(data.get("FRIDAY_IN")),
        "friday_out": _convert_to_time(data.get("FRIDAY_OUT")),
        "saturday_in": _convert_to_time(data.get("SATURDAY_IN")),
        "saturday_out": _convert_to_time("6:00 PM"), # Hardcoded as per flow
    }

    # 2. Send to webhook
    webhook_url = os.getenv("WEBHOOK_SCHEDULE")
    if webhook_url:
        # Create a JSON-serializable payload
        json_payload = {k: (v.isoformat() if isinstance(v, datetime.time) else v) for k, v in schedule_data.items()}
        json_payload["timestamp"] = datetime.now().isoformat()
        _send_webhook(webhook_url, json_payload)

    # 3. Save to database
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # Upsert logic: Check if a record for this telegram_id already exists
        existing_schedule = session.query(HorariosConfigurados).filter_by(telegram_id=telegram_id).first()
        if existing_schedule:
            # Update existing record
            for key, value in schedule_data.items():
                setattr(existing_schedule, key, value)
            existing_schedule.timestamp = datetime.now()
            logging.info(f"Updating existing schedule for telegram_id: {telegram_id}")
        else:
            # Create new record
            new_schedule = HorariosConfigurados(**schedule_data)
            session.add(new_schedule)
            logging.info(f"Creating new schedule for telegram_id: {telegram_id}")
        
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
