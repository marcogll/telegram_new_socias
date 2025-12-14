import os
import requests
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from modules.database import log_request

# Estado
ESPERANDO_ARCHIVO = 1

async def start_print(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_request(user.id, user.username, "print", update.message.text)
    await update.message.reply_text("🖨️ **Servicio de Impresión**\n\nPor favor, envíame el archivo (PDF, DOCX o Imagen) que deseas imprimir/enviar.")
    return ESPERANDO_ARCHIVO

async def recibir_archivo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    archivo = update.message.document or update.message.photo[-1] # Toma documento o la foto más grande
    
    file_id = archivo.file_id
    file_name = getattr(archivo, 'file_name', f"foto_{file_id}.jpg")
    
    # Obtenemos el link de descarga directo de Telegram
    file_info = await context.bot.get_file(file_id)
    file_url = file_info.file_path

    # Enviamos a n8n
    webhook = os.getenv("WEBHOOK_PRINT")
    payload = {
        "user": user.full_name,
        "email_user": f"{user.username}@telegram.org", # O pedir el mail antes
        "file_url": file_url,
        "file_name": file_name,
        "tipo": "impresion"
    }
    
    try:
        requests.post(webhook, json=payload)
        await update.message.reply_text(f"✅ Archivo *{file_name}* enviado a cola de impresión.")
    except:
        await update.message.reply_text("❌ Error al conectar con el servidor de impresión.")

    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END

# Exportamos el handler
print_handler = ConversationHandler(
    entry_points=[CommandHandler("print", start_print)],
    states={ESPERANDO_ARCHIVO: [MessageHandler(filters.Document.ALL | filters.PHOTO, recibir_archivo)]},
    fallbacks=[CommandHandler("cancelar", cancelar)]
)