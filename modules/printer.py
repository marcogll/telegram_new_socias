import os
import requests
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from modules.database import log_request

# Webhook opcional para notificar el evento de impresión
WEBHOOK_PRINTS = [w.strip() for w in (os.getenv("WEBHOOK_PRINT", "")).split(",") if w.strip()]

# --- SMTP Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
# Permitimos PRINTER_EMAIL como alias legado para SMTP_RECIPIENT
SMTP_RECIPIENT = os.getenv("SMTP_RECIPIENT") or os.getenv("PRINTER_EMAIL")

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
    
    await update.message.reply_text(f"Procesando *{file_name}*... un momento por favor.")

    try:
        if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_RECIPIENT]):
            raise RuntimeError("SMTP no configurado (falta SERVER/USER/PASSWORD/RECIPIENT).")
        
        # 1. Descargar el archivo de Telegram
        file_info = await context.bot.get_file(file_id)
        file_url = file_info.file_path
        file_content = requests.get(file_url).content

        # 2. Construir el correo
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_RECIPIENT
        msg['Subject'] = f"Nuevo archivo para imprimir de {user.full_name}"

        # Cuerpo del correo
        body = f"""
        Hola,

        El usuario {user.full_name} (Username: @{user.username}, ID: {user.id}) ha enviado un archivo para imprimir.

        Nombre del archivo: {file_name}

        Este correo ha sido generado automáticamente por Vanessa Bot.
        """
        msg.attach(MIMEText(body, 'plain'))

        # Adjuntar el archivo
        attachment = MIMEApplication(file_content, Name=file_name)
        attachment['Content-Disposition'] = f'attachment; filename="{file_name}"'
        msg.attach(attachment)

        # 3. Enviar el correo
        ssl_context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ssl_context) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, SMTP_RECIPIENT, msg.as_string())

        await update.message.reply_text(f"✅ Archivo *{file_name}* enviado a la impresora correctamente.")

    except Exception as e:
        print(f"Error al enviar correo: {e}") # Log para el admin
        await update.message.reply_text("❌ Hubo un error al procesar tu archivo. Por favor, contacta a un administrador.")
        return ConversationHandler.END

    # Webhook de notificación (sin archivo, solo metadata)
    if WEBHOOK_PRINTS:
        payload = {
            "accion": "PRINT",
            "usuario": {
                "id": user.id,
                "username": user.username,
                "nombre": user.full_name
            },
            "archivo": {
                "nombre": file_name,
                "telegram_file_id": file_id,
            },
            "enviado_via": "email",
            "timestamp": update.message.date.isoformat() if update.message.date else None
        }
        for url in WEBHOOK_PRINTS:
            try:
                requests.post(url, json=payload, timeout=10).raise_for_status()
            except Exception as e:
                print(f"Error notificando webhook de impresión a {url}: {e}")
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
