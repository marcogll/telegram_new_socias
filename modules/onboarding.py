import logging
import os
import requests
from datetime import datetime
from functools import partial
from dotenv import load_dotenv  # pip install python-dotenv

from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    Defaults,
)

from modules.database import log_request

# --- 1. CARGA DE ENTORNO ---
load_dotenv()  # Carga las variables del archivo .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Convertimos la string del webhook en una lista (por si en el futuro hay varios separados por coma)
WEBHOOK_URLS = os.getenv("WEBHOOK_CONTRATO", "").split(",")

# Validación de seguridad
if not TOKEN:
    raise ValueError("⚠️ Error: No se encontró TELEGRAM_TOKEN en el archivo .env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- 2. ESTADOS DEL FLUJO ---
(
    NOMBRE_SALUDO, NOMBRE_COMPLETO, APELLIDO_PATERNO, APELLIDO_MATERNO,
    CUMPLE_DIA, CUMPLE_MES, CUMPLE_ANIO, ESTADO_NACIMIENTO,
    RFC, CURP,
    CORREO, CELULAR,
    CALLE, NUM_EXTERIOR, NUM_INTERIOR, COLONIA, CODIGO_POSTAL, CIUDAD_RESIDENCIA,
    ROL, SUCURSAL, INICIO_DIA, INICIO_MES, INICIO_ANIO,
    REF1_NOMBRE, REF1_TELEFONO, REF1_TIPO,
    REF2_NOMBRE, REF2_TELEFONO, REF2_TIPO,
    REF3_NOMBRE, REF3_TELEFONO, REF3_TIPO,
    EMERGENCIA_NOMBRE, EMERGENCIA_TEL, EMERGENCIA_RELACION
) = range(35)

# --- 3. HELPER: NORMALIZACIÓN Y MAPEOS ---

def normalizar_id(texto: str) -> str:
    """Elimina espacios y convierte a mayúsculas (para RFC y CURP)."""
    if not texto: return "N/A"
    # Elimina todos los espacios en blanco y pone mayúsculas
    limpio = "".join(texto.split()).upper()
    return "N/A" if limpio == "0" else limpio

def limpiar_texto_general(texto: str) -> str:
    t = texto.strip()
    return "N/A" if t == "0" else t

# --- 4. TECLADOS DINÁMICOS ---

# Meses: Texto vs Valor
MAPA_MESES = {
    "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
    "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
    "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
}
# Generamos el teclado de 3 en 3
TECLADO_MESES = ReplyKeyboardMarkup(
    [list(MAPA_MESES.keys())[i:i+3] for i in range(0, 12, 3)],
    one_time_keyboard=True, resize_keyboard=True
)

# Años: Actual y Siguiente
anio_actual = datetime.now().year
TECLADO_ANIOS_INICIO = ReplyKeyboardMarkup(
    [[str(anio_actual), str(anio_actual + 1)]],
    one_time_keyboard=True, resize_keyboard=True
)

# Roles
TECLADO_ROLES = ReplyKeyboardMarkup(
    [["Partner", "Manager"], ["Staff", "Tech"], ["Marketing"]],
    one_time_keyboard=True, resize_keyboard=True
)

# Sucursales (Mapeo Visual -> ID Técnico)
MAPA_SUCURSALES = {
    "Plaza Cima (Sur) ⛰️": "plaza_cima",
    "Plaza O (Carranza) 🏙️": "plaza_o"
}
TECLADO_SUCURSALES = ReplyKeyboardMarkup(
    [["Plaza Cima (Sur) ⛰️", "Plaza O (Carranza) 🏙️"]],
    one_time_keyboard=True, resize_keyboard=True
)

TECLADO_CIUDAD = ReplyKeyboardMarkup(
    [["Saltillo", "Ramos Arizpe", "Arteaga"]],
    one_time_keyboard=True, resize_keyboard=True
)

TECLADO_REF_TIPO = ReplyKeyboardMarkup(
    [["Familiar", "Amistad"], ["Trabajo", "Académica", "Otra"]],
    one_time_keyboard=True, resize_keyboard=True
)

TECLADO_RELACION_EMERGENCIA = ReplyKeyboardMarkup(
    [["Padre/Madre", "Esposo/a", "Hijo/a"], ["Hermano/a", "Amigo/a", "Otro"]],
    one_time_keyboard=True, resize_keyboard=True
)

# --- 5. LOGICA DEL BOT (VANESSA) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data.clear()
    log_request(user.id, user.username, "welcome", update.message.text)
    
    context.user_data["metadata"] = {
        "telegram_id": user.id,
        "username": user.username or "N/A",
        "first_name": user.first_name,
        "start_ts": datetime.now().timestamp()
    }
    context.user_data["respuestas"] = {}
    
    await update.message.reply_text(
        f"¡Hola {user.first_name}! 👋\n\n"
        "Soy *Vanessa de Recursos Humanos* de Vanity. 👩‍💼\n"
        "Bienvenida al equipo Soul. Vamos a dejar listo tu registro en unos minutos.\n\n"
        "💡 _Tip: Si te equivocas, escribe /cancelar y empezamos de nuevo._"
    )
    await update.message.reply_text("Para empezar con el pie derecho, ¿cómo te gusta que te llamemos?")
    return NOMBRE_SALUDO

async def manejar_flujo(update: Update, context: ContextTypes.DEFAULT_TYPE, estado_actual: int) -> int:
    texto_recibido = update.message.text
    respuesta_procesada = limpiar_texto_general(texto_recibido)

    # --- LÓGICA DE PROCESAMIENTO ESPECÍFICA POR ESTADO ---
    
    # 1. Normalización de RFC y CURP (Quitar espacios, Mayúsculas)
    if estado_actual in [RFC, CURP]:
        respuesta_procesada = normalizar_id(texto_recibido)

    # 2. Mapeo de Meses (Texto -> Número)
    if estado_actual in [CUMPLE_MES, INICIO_MES]:
        # Si el usuario seleccionó un botón, buscamos su valor numérico
        respuesta_procesada = MAPA_MESES.get(texto_recibido, texto_recibido) # Fallback al texto si no está en mapa

    # 3. Mapeo de Sucursales (Texto Bonito -> ID Técnico)
    if estado_actual == SUCURSAL:
        respuesta_procesada = MAPA_SUCURSALES.get(texto_recibido, "otra_sucursal")

    # Guardar en memoria
    context.user_data["respuestas"][estado_actual] = respuesta_procesada
    
    # --- GUIÓN DE ENTREVISTA ---
    siguiente_estado = estado_actual + 1
    
    preguntas = {
        NOMBRE_SALUDO: "¡Lindo nombre! ✨\n\nNecesito tus datos oficiales para el contrato.\n¿Cuál es tu *nombre completo* (nombres) tal cual aparece en tu INE?",
        NOMBRE_COMPLETO: "¿Cuál es tu *apellido paterno*?",
        APELLIDO_PATERNO: "¿Y tu *apellido materno*?",
        
        # Cumpleaños
        APELLIDO_MATERNO: "🎂 Hablemos de ti. ¿Qué *día* es tu cumpleaños? (Escribe el número, ej: 13)",
        CUMPLE_DIA: {"texto": "¿De qué *mes*? 🎉", "teclado": TECLADO_MESES},
        CUMPLE_MES: "Entendido. ¿Y de qué *año*? 🗓️",
        CUMPLE_ANIO: "🇲🇽 ¿En qué *estado de la república* naciste?",
        
        # Identificación
        ESTADO_NACIMIENTO: "Pasemos a lo administrativo 📄.\n\nPor favor escribe tu *RFC* (Sin espacios):",
        RFC: "Gracias. Ahora tu *CURP*:",
        
        # Contacto
        CURP: "¡Súper! 📧 ¿A qué *correo electrónico* te enviamos la info?",
        CORREO: "📱 ¿Cuál es tu número de *celular* personal? (10 dígitos)",
        
        # Domicilio
        CELULAR: "🏠 Registremos tu domicilio.\n\n¿En qué *calle* vives?",
        CALLE: "#️⃣ ¿Cuál es el *número exterior*?",
        NUM_EXTERIOR: "🚪 ¿Tienes *número interior*? (Escribe 0 si no aplica)",
        NUM_INTERIOR: "🏘️ ¿Cómo se llama la *colonia*?",
        COLONIA: "📮 ¿Cuál es el *Código Postal*?",
        CODIGO_POSTAL: {"texto": "¿En qué *ciudad* resides actualmente?", "teclado": TECLADO_CIUDAD},
        
        # Laboral
        CIUDAD_RESIDENCIA: {"texto": "¡Excelente! Coahuila es territorio Vanity 🌵.\n\n¿Qué *rol* tendrás en el equipo? 💼", "teclado": TECLADO_ROLES},
        ROL: {"texto": "¿A qué *sucursal* te vas a integrar? 📍", "teclado": TECLADO_SUCURSALES},
        SUCURSAL: "¡Qué emoción! 🎉\n\n¿Qué *día* está programado tu ingreso? (Solo el número, ej: 01)",
        INICIO_DIA: {"texto": "¿De qué *mes* será tu ingreso?", "teclado": TECLADO_MESES},
        INICIO_MES: {"texto": "¿Y de qué *año*?", "teclado": TECLADO_ANIOS_INICIO},
        
        # Referencias
        INICIO_ANIO: "Ya casi acabamos. Necesito 3 referencias.\n\n👤 *Referencia 1*: Nombre completo",
        REF1_NOMBRE: "📞 Teléfono de la Referencia 1:",
        REF1_TELEFONO: {"texto": "🧑‍🤝‍🧑 ¿Qué relación tienes con ella/él?", "teclado": TECLADO_REF_TIPO},
        
        REF1_TIPO: "Ok. Vamos con la *Referencia 2*.\n\n👤 Nombre completo:",
        REF2_NOMBRE: "📞 Teléfono de la Referencia 2:",
        REF2_TELEFONO: {"texto": "🧑‍🤝‍🧑 ¿Qué relación tienen?", "teclado": TECLADO_REF_TIPO},
        
        REF2_TIPO: "Última. *Referencia 3*.\n\n👤 Nombre completo:",
        REF3_NOMBRE: "📞 Teléfono de la Referencia 3:",
        REF3_TELEFONO: {"texto": "🧑‍🤝‍🧑 ¿Qué relación tienen?", "teclado": TECLADO_REF_TIPO},
        
        # Emergencia
        REF3_TIPO: "Finalmente, por seguridad 🚑:\n\n¿A quién llamamos en caso de *emergencia*?",
        EMERGENCIA_NOMBRE: "☎️ ¿Cuál es el teléfono de esa persona?",
        EMERGENCIA_TEL: {"texto": "¿Qué parentesco tiene contigo?", "teclado": TECLADO_RELACION_EMERGENCIA},
    }
    
    siguiente = preguntas.get(estado_actual)
    
    if isinstance(siguiente, dict):
        await update.message.reply_text(siguiente["texto"], reply_markup=siguiente["teclado"])
    else:
        await update.message.reply_text(siguiente, reply_markup=ReplyKeyboardRemove())

    return siguiente_estado

async def finalizar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Guardar última respuesta (Relación Emergencia)
    context.user_data["respuestas"][EMERGENCIA_RELACION] = limpiar_texto_general(update.message.text)
    
    await update.message.reply_text("¡Perfecto! 📝 Guardando tu expediente en el sistema... dame un momento.")

    r = context.user_data["respuestas"]
    meta = context.user_data["metadata"]
    
    # Construcción segura de fechas
    try:
        fecha_nac = f"{r[CUMPLE_ANIO]}-{r[CUMPLE_MES]}-{str(r[CUMPLE_DIA]).zfill(2)}"
        fecha_ini = f"{r[INICIO_ANIO]}-{r[INICIO_MES]}-{str(r[INICIO_DIA]).zfill(2)}"
    except Exception:
        fecha_nac = "ERROR_FECHA"
        fecha_ini = "ERROR_FECHA"
    
    # PAYLOAD ESTRUCTURADO PARA N8N
    payload = {
        "candidato": {
            "nombre_preferido": r.get(NOMBRE_SALUDO),
            "nombre_oficial": r.get(NOMBRE_COMPLETO),
            "apellido_paterno": r.get(APELLIDO_PATERNO),
            "apellido_materno": r.get(APELLIDO_MATERNO),
            "fecha_nacimiento": fecha_nac,
            "rfc": r.get(RFC),
            "curp": r.get(CURP),
            "lugar_nacimiento": r.get(ESTADO_NACIMIENTO)
        },
        "contacto": {
            "email": r.get(CORREO),
            "celular": r.get(CELULAR)
        },
        "domicilio": {
            "calle": r.get(CALLE),
            "num_ext": r.get(NUM_EXTERIOR),
            "num_int": r.get(NUM_INTERIOR),
            "colonia": r.get(COLONIA),
            "cp": r.get(CODIGO_POSTAL),
            "ciudad": r.get(CIUDAD_RESIDENCIA),
            "estado": "Coahuila de Zaragoza"
        },
        "laboral": {
            "rol_id": r.get(ROL).lower(), # partner, manager...
            "sucursal_id": r.get(SUCURSAL), # plaza_cima, plaza_o
            "fecha_inicio": fecha_ini
        },
        "referencias": [
            {"nombre": r.get(REF1_NOMBRE), "telefono": r.get(REF1_TELEFONO), "relacion": r.get(REF1_TIPO)},
            {"nombre": r.get(REF2_NOMBRE), "telefono": r.get(REF2_TELEFONO), "relacion": r.get(REF2_TIPO)},
            {"nombre": r.get(REF3_NOMBRE), "telefono": r.get(REF3_TELEFONO), "relacion": r.get(REF3_TIPO)}
        ],
        "emergencia": {
            "nombre": r.get(EMERGENCIA_NOMBRE),
            "telefono": r.get(EMERGENCIA_TEL),
            "relacion": r.get(EMERGENCIA_RELACION)
        },
        "metadata": {
            "telegram_user": meta["username"],
            "chat_id": meta["telegram_id"],
            "bot_version": "welcome2soul_v2",
            "fecha_registro": datetime.now().isoformat()
        }
    }

    headers = {"Content-Type": "application/json", "User-Agent": "Welcome2Soul-Bot"}
    
    enviado = False
    for url in WEBHOOK_URLS:
        if not url: continue
        try:
            res = requests.post(url.strip(), json=payload, headers=headers, timeout=20)
            res.raise_for_status()
            enviado = True
            logging.info(f"Webhook enviado exitosamente a: {url}")
        except Exception as e:
            logging.error(f"Error enviando webhook: {e}")

    if enviado:
        await update.message.reply_text(
            "✅ *¡Registro Exitoso!*\n\n"
            "Bienvenida a la familia Soul/Vanity. Tu contrato se está generando y te avisaremos pronto.\n"
            "¡Nos vemos el primer día! ✨"
        )
    else:
        await update.message.reply_text("⚠️ Se guardaron tus datos pero hubo un error de conexión. RH lo revisará manualmente.")

    context.user_data.clear()
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Proceso cancelado. ⏸️\nCuando quieras retomar, escribe /contrato.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

def main():
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN)
    application = Application.builder().token(TOKEN).defaults(defaults).build()
    
    # states definition moved to global scope

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("contrato", start)],
        states=states,
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    application.add_handler(conv_handler)
    print("🧠 Welcome2Soul Bot (Vanessa) iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
# ... todo el código del contrato ...

# Definición de estados para el ConversationHandler
states = {}
for i in range(34):
    callback = partial(manejar_flujo, estado_actual=i)
    states[i] = [MessageHandler(filters.TEXT & ~filters.COMMAND, callback)]

states[34] = [MessageHandler(filters.TEXT & ~filters.COMMAND, finalizar)]

# Al final:
onboarding_handler = ConversationHandler(
    entry_points=[CommandHandler("welcome", start)], # Cambiado a /welcome
    states=states, # Tu diccionario de estados
    fallbacks=[CommandHandler("cancelar", cancelar)]
)