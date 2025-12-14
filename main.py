import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno antes de importar módulos que las usan
load_dotenv()

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults, CommandHandler, ContextTypes

# --- IMPORTAR HABILIDADES ---
from modules.onboarding import onboarding_handler
from modules.printer import print_handler
from modules.rh_requests import vacaciones_handler, permiso_handler
from modules.database import log_request
# from modules.finder import finder_handler (Si lo creas después)


TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de opciones de Vanessa"""
    user = update.effective_user
    log_request(user.id, user.username, "start", update.message.text)
    texto = (
        "👩‍💼 **Hola, soy Vanessa. ¿En qué puedo ayudarte hoy?**\n\n"
        "📝 `/welcome` - Iniciar onboarding/contrato\n"
        "🖨️ `/print` - Imprimir o enviar archivo\n"
        "🌴 `/vacaciones` - Solicitar días libres\n"
        "⏱️ `/permiso` - Solicitar permiso por horas\n\n"
        "Selecciona un comando para empezar."
    )
    await update.message.reply_text(texto)

def main():
    # Configuración Global
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN)
    app = Application.builder().token(TOKEN).defaults(defaults).build()

    # --- REGISTRO DE HABILIDADES ---
    
    # 1. Comando de Ayuda / Menú
    app.add_handler(CommandHandler("start", menu_principal))
    app.add_handler(CommandHandler("help", menu_principal))

    # 2. Habilidades Complejas (Conversaciones)
    app.add_handler(onboarding_handler)
    app.add_handler(print_handler)
    app.add_handler(vacaciones_handler)
    app.add_handler(permiso_handler)
    # app.add_handler(finder_handler)

    print("🧠 Vanessa Bot Brain iniciada y lista para trabajar en todos los módulos.")
    app.run_polling()

if __name__ == "__main__":
    main()
