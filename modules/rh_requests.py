import os
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from modules.database import log_request

TIPO_SOLICITUD, FECHAS, MOTIVO = range(3)

async def start_vacaciones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_request(user.id, user.username, "vacaciones", update.message.text)
    context.user_data['tipo'] = 'Vacaciones'
    await update.message.reply_text("🌴 **Solicitud de Vacaciones**\n\n¿Para qué fechas las necesitas? (Ej: 10 al 15 de Octubre)")
    return FECHAS

async def start_permiso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_request(user.id, user.username, "permiso", update.message.text)
    context.user_data['tipo'] = 'Permiso Especial'
    await update.message.reply_text("⏱️ **Solicitud de Permiso**\n\n¿Para qué día y horario lo necesitas?")
    return FECHAS

async def recibir_fechas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['fechas'] = update.message.text
    await update.message.reply_text("Entendido. ¿Cuál es el motivo o comentario adicional?")
    return MOTIVO

async def recibir_motivo_fin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    motivo = update.message.text
    datos = context.user_data
    user = update.effective_user

    # Payload para n8n
    payload = {
        "solicitante": user.full_name,
        "id_telegram": user.id,
        "tipo_solicitud": datos['tipo'],
        "fechas": datos['fechas'],
        "motivo": motivo
    }

    webhook = os.getenv("WEBHOOK_VACACIONES")
    try:
        requests.post(webhook, json=payload)
        await update.message.reply_text(f"✅ Solicitud de *{datos['tipo']}* enviada a tu Manager.")
    except:
        await update.message.reply_text("⚠️ Error enviando la solicitud.")

    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Solicitud cancelada.")
    return ConversationHandler.END

# Handlers separados pero comparten lógica
vacaciones_handler = ConversationHandler(
    entry_points=[CommandHandler("vacaciones", start_vacaciones)],
    states={FECHAS: [MessageHandler(filters.TEXT, recibir_fechas)], MOTIVO: [MessageHandler(filters.TEXT, recibir_motivo_fin)]},
    fallbacks=[CommandHandler("cancelar", cancelar)]
)

permiso_handler = ConversationHandler(
    entry_points=[CommandHandler("permiso", start_permiso)],
    states={FECHAS: [MessageHandler(filters.TEXT, recibir_fechas)], MOTIVO: [MessageHandler(filters.TEXT, recibir_motivo_fin)]},
    fallbacks=[CommandHandler("cancelar", cancelar)]
)