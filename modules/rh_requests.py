import os
import re
import requests
import uuid
from datetime import datetime, date
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from modules.database import log_request
from modules.ai import classify_reason

# Helpers de webhooks
def _get_webhook_list(env_name: str) -> list:
    raw = os.getenv(env_name, "")
    return [w.strip() for w in raw.split(",") if w.strip()]

def _send_webhooks(urls: list, payload: dict):
    enviados = 0
    for url in urls:
        try:
            res = requests.post(url, json=payload, timeout=15)
            res.raise_for_status()
            enviados += 1
        except Exception as e:
            print(f"[webhook] Error enviando a {url}: {e}")
    return enviados

TIPO_SOLICITITUD, FECHAS, MOTIVO = range(3)

# Teclados de apoyo
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
TECLADO_MESES = ReplyKeyboardMarkup([MESES[i:i+3] for i in range(0, 12, 3)], one_time_keyboard=True, resize_keyboard=True)
TECLADO_PERMISO_RAPIDO = ReplyKeyboardMarkup(
    [["Hoy 09:00-11:00", "Hoy 15:00-18:00"], ["Mañana 09:00-11:00", "Mañana 15:00-18:00"], ["Otra fecha/horario"]],
    one_time_keyboard=True,
    resize_keyboard=True,
)

def _calculate_vacation_metrics(date_string: str) -> dict:
    """
    Calcula métricas de vacaciones a partir de un texto.
    Asume un formato como "10 al 15 de Octubre".
    """
    today = date.today()
    current_year = today.year
    
    # Mapeo de meses en español a número
    meses = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    # Regex para "10 al 15 de Octubre"
    match = re.search(r'(\d{1,2})\s*al\s*(\d{1,2})\s*de\s*(\w+)', date_string, re.IGNORECASE)
    
    if not match:
        return {"dias_totales": 0, "dias_anticipacion": 0}

    start_day, end_day, month_str = match.groups()
    start_day, end_day = int(start_day), int(end_day)
    month = meses.get(month_str.lower())

    if not month:
        return {"dias_totales": 0, "dias_anticipacion": 0}

    try:
        start_date = date(current_year, month, start_day)
        # Si la fecha ya pasó este año, asumir que es del próximo año
        if start_date < today:
            start_date = date(current_year + 1, month, start_day)
            
        end_date = date(start_date.year, month, end_day)
        
        dias_totales = (end_date - start_date).days + 1
        dias_anticipacion = (start_date - today).days
        
        return {"dias_totales": dias_totales, "dias_anticipacion": dias_anticipacion, "fechas_calculadas": {"inicio": start_date.isoformat(), "fin": end_date.isoformat()}}
    except ValueError:
        return {"dias_totales": 0, "dias_anticipacion": 0}


async def start_vacaciones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_request(user.id, user.username, "vacaciones", update.message.text)
    context.user_data['tipo'] = 'VACACIONES'
    await update.message.reply_text(
        "🌴 **Solicitud de Vacaciones**\n\n¿Para qué fechas las necesitas?\nUsa el formato: `10 al 15 de Octubre`.",
        reply_markup=TECLADO_MESES,
    )
    return FECHAS

async def start_permiso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_request(user.id, user.username, "permiso", update.message.text)
    context.user_data['tipo'] = 'PERMISO'
    await update.message.reply_text(
        "⏱️ **Solicitud de Permiso**\n\nSelecciona o escribe el día y horario. Ej: `Jueves 15 09:00-11:00`.",
        reply_markup=TECLADO_PERMISO_RAPIDO,
    )
    return FECHAS

async def recibir_fechas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto_fechas = update.message.text
    es_vacaciones = context.user_data.get('tipo') == 'VACACIONES'

    if es_vacaciones:
        metrics = _calculate_vacation_metrics(texto_fechas)
        if metrics["dias_totales"] == 0:
            await update.message.reply_text(
                "No entendí las fechas. Usa un formato como `10 al 15 de Octubre`.",
                reply_markup=TECLADO_MESES,
            )
            return FECHAS
        # Si se entiende, guardamos también las métricas preliminares
        context.user_data['metricas_preliminares'] = metrics

    context.user_data['fechas'] = texto_fechas
    await update.message.reply_text("Entendido. ¿Cuál es el motivo o comentario adicional?", reply_markup=ReplyKeyboardRemove())
    return MOTIVO

async def recibir_motivo_fin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    motivo = update.message.text
    datos = context.user_data
    user = update.effective_user
    
    # Generar payload base
    payload = {
        "record_id": str(uuid.uuid4()),
        "solicitante": {
            "id_telegram": user.id,
            "nombre": user.full_name,
            "username": user.username
        },
        "tipo_solicitud": datos['tipo'],
        "fechas_texto_original": datos['fechas'],
        "motivo_usuario": motivo,
        "created_at": datetime.now().isoformat()
    }

    webhooks = []
    if datos['tipo'] == 'PERMISO':
        webhooks = _get_webhook_list("WEBHOOK_PERMISOS")
        categoria = classify_reason(motivo)
        payload["categoria_detectada"] = categoria
        await update.message.reply_text(f"Categoría detectada → **{categoria}** 🚨")
    
    elif datos['tipo'] == 'VACACIONES':
        webhooks = _get_webhook_list("WEBHOOK_VACACIONES")
        metrics = datos.get('metricas_preliminares') or _calculate_vacation_metrics(datos['fechas'])
        
        if metrics["dias_totales"] > 0:
            payload["metricas"] = metrics
            
            dias = metrics["dias_totales"]
            if dias <= 5:
                status = "RECHAZADO"
                mensaje = f"🔴 {dias} días es un periodo muy corto. Las vacaciones deben ser de al menos 6 días."
            elif 6 <= dias <= 11:
                status = "REVISION_MANUAL"
                mensaje = f"🟡 Solicitud de {dias} días recibida. Tu manager la revisará pronto."
            else: # 12+
                status = "PRE_APROBADO"
                mensaje = f"🟢 ¡Excelente planeación! Tu solicitud de {dias} días ha sido pre-aprobada."
            
            payload["status_inicial"] = status
            await update.message.reply_text(mensaje)
        else:
            # Si no se pudieron parsear las fechas
            payload["status_inicial"] = "ERROR_FECHAS"
            await update.message.reply_text("🤔 No entendí las fechas. Por favor, usa un formato como '10 al 15 de Octubre'.")

    try:
        enviados = _send_webhooks(webhooks, payload) if webhooks else 0
        tipo_solicitud_texto = "Permiso" if datos['tipo'] == 'PERMISO' else 'Vacaciones'
        if enviados > 0:
            await update.message.reply_text(f"✅ Solicitud de *{tipo_solicitud_texto}* enviada a tu Manager.")
        else:
            await update.message.reply_text("⚠️ No hay webhook configurado o falló el envío. RH lo revisará.")
    except Exception as e:
        print(f"Error enviando webhook: {e}")
        await update.message.reply_text("⚠️ Error enviando la solicitud.")

    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Solicitud cancelada.")
    return ConversationHandler.END

# Handlers separados pero comparten lógica
vacaciones_handler = ConversationHandler(
    entry_points=[CommandHandler("vacaciones", start_vacaciones)],
    states={
        FECHAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fechas)],
        MOTIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_motivo_fin)]
    },
    fallbacks=[CommandHandler("cancelar", cancelar)]
)

permiso_handler = ConversationHandler(
    entry_points=[CommandHandler("permiso", start_permiso)],
    states={
        FECHAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fechas)],
        MOTIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_motivo_fin)]
    },
    fallbacks=[CommandHandler("cancelar", cancelar)]
)
