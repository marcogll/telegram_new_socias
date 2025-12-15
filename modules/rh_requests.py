import os
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

# Estados de conversación
(
    VAC_ANIO,
    INICIO_DIA,
    INICIO_MES,
    FIN_DIA,
    FIN_MES,
    PERMISO_CUANDO,
    PERMISO_ANIO,
    HORARIO,
    MOTIVO,
) = range(9)

# Teclados de apoyo
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
TECLADO_MESES = ReplyKeyboardMarkup([MESES[i:i+3] for i in range(0, 12, 3)], one_time_keyboard=True, resize_keyboard=True)
MESES_MAP = {nombre.lower(): idx + 1 for idx, nombre in enumerate(MESES)}
ANIO_ACTUAL = datetime.now().year
TECLADO_ANIOS = ReplyKeyboardMarkup([[str(ANIO_ACTUAL), str(ANIO_ACTUAL + 1)]], one_time_keyboard=True, resize_keyboard=True)
TECLADO_PERMISO_CUANDO = ReplyKeyboardMarkup(
    [["Hoy", "Mañana"], ["Pasado mañana", "Fecha específica"]],
    one_time_keyboard=True,
    resize_keyboard=True,
)

def _parse_dia(texto: str) -> int:
    try:
        dia = int(texto)
        if 1 <= dia <= 31:
            return dia
    except Exception:
        pass
    return 0

def _parse_mes(texto: str) -> int:
    return MESES_MAP.get(texto.strip().lower(), 0)

def _parse_anio(texto: str) -> int:
    try:
        return int(texto)
    except Exception:
        return 0

def _build_dates(datos: dict) -> dict:
    """Construye fechas ISO; si fin < inicio, se ajusta a inicio."""
    year = datos.get("anio") or datetime.now().year
    try:
        inicio = date(year, datos["inicio_mes"], datos["inicio_dia"])
        fin_dia = datos.get("fin_dia", datos.get("inicio_dia"))
        fin_mes = datos.get("fin_mes", datos.get("inicio_mes"))
        fin = date(year, fin_mes, fin_dia)
        if fin < inicio:
            fin = inicio
        return {"inicio": inicio, "fin": fin}
    except Exception:
        return {}

def _calculate_vacation_metrics_from_dates(fechas: dict) -> dict:
    today = date.today()
    inicio = fechas.get("inicio")
    fin = fechas.get("fin")
    if not inicio or not fin:
        return {"dias_totales": 0, "dias_anticipacion": 0}
    dias_totales = (fin - inicio).days + 1
    dias_anticipacion = (inicio - today).days
    return {
        "dias_totales": dias_totales,
        "dias_anticipacion": dias_anticipacion,
        "fechas_calculadas": {"inicio": inicio.isoformat(), "fin": fin.isoformat()},
    }

def _fmt_fecha(fecha_iso: str) -> str:
    if not fecha_iso:
        return "N/A"
    try:
        return fecha_iso.split("T")[0]
    except Exception:
        return fecha_iso

# --- Vacaciones ---
async def start_vacaciones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_request(user.id, user.username, "vacaciones", update.message.text)
    context.user_data.clear()
    context.user_data['tipo'] = 'VACACIONES'
    context.user_data["anio"] = ANIO_ACTUAL
    await update.message.reply_text(
        "🌴 **Solicitud de Vacaciones**\n\nUsaré el año actual. ¿En qué *día* inicia tu descanso? (número, ej: 10)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return INICIO_DIA

# --- Permiso ---
async def start_permiso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_request(user.id, user.username, "permiso", update.message.text)
    context.user_data.clear()
    context.user_data['tipo'] = 'PERMISO'
    await update.message.reply_text(
        "⏱️ **Solicitud de Permiso**\n\n¿Para cuándo lo necesitas?",
        reply_markup=TECLADO_PERMISO_CUANDO,
    )
    return PERMISO_CUANDO

# --- Selección de año / cuando ---
async def recibir_anio_vacaciones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    anio = _parse_anio(update.message.text)
    if anio not in (ANIO_ACTUAL, ANIO_ACTUAL + 1):
        await update.message.reply_text("Elige el año del teclado (actual o siguiente).", reply_markup=TECLADO_ANIOS)
        return VAC_ANIO
    context.user_data["anio"] = anio
    await update.message.reply_text("¿Qué *día* termina?", reply_markup=ReplyKeyboardRemove())
    return FIN_DIA

async def recibir_cuando_permiso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip().lower()
    hoy = date.today()
    offset_map = {"hoy": 0, "mañana": 1, "manana": 1, "pasado mañana": 2, "pasado manana": 2}
    if texto in offset_map:
        delta = offset_map[texto]
        fecha = hoy.fromordinal(hoy.toordinal() + delta)
        context.user_data["anio"] = fecha.year
        context.user_data["inicio_dia"] = fecha.day
        context.user_data["inicio_mes"] = fecha.month
        context.user_data["fin_dia"] = fecha.day
        context.user_data["fin_mes"] = fecha.month
        await update.message.reply_text("¿Cuál es el horario? Ej: `09:00-11:00` o `Todo el día`.", reply_markup=ReplyKeyboardRemove())
        return HORARIO
    if "fecha" in texto:
        context.user_data["anio"] = ANIO_ACTUAL
        await update.message.reply_text("¿En qué *día* inicia el permiso? (número, ej: 12)", reply_markup=ReplyKeyboardRemove())
        return INICIO_DIA
    await update.message.reply_text("Elige una opción: Hoy, Mañana, Pasado mañana o Fecha específica.", reply_markup=TECLADO_PERMISO_CUANDO)
    return PERMISO_CUANDO

async def recibir_anio_permiso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    anio = _parse_anio(update.message.text)
    if anio not in (ANIO_ACTUAL, ANIO_ACTUAL + 1):
        await update.message.reply_text("Elige el año del teclado (actual o siguiente).", reply_markup=TECLADO_ANIOS)
        return PERMISO_ANIO
    context.user_data["anio"] = anio
    await update.message.reply_text("¿Qué *día* termina?", reply_markup=ReplyKeyboardRemove())
    return FIN_DIA

# --- Captura de fechas ---
async def recibir_inicio_dia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dia = _parse_dia(update.message.text)
    if not dia:
        await update.message.reply_text("Necesito un número de día válido (1-31). Intenta de nuevo.")
        return INICIO_DIA
    context.user_data["inicio_dia"] = dia
    await update.message.reply_text("¿De qué *mes* inicia?", reply_markup=TECLADO_MESES)
    return INICIO_MES

async def recibir_inicio_mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mes = _parse_mes(update.message.text)
    if not mes:
        await update.message.reply_text("Elige un mes del teclado o escríbelo igual que aparece.", reply_markup=TECLADO_MESES)
        return INICIO_MES
    context.user_data["inicio_mes"] = mes
    context.user_data.setdefault("anio", ANIO_ACTUAL)

    try:
        inicio_candidato = date(context.user_data["anio"], mes, context.user_data["inicio_dia"])
        if inicio_candidato < date.today():
            await update.message.reply_text(
                "Esa fecha ya pasó este año. ¿Para qué año la agendamos?",
                reply_markup=TECLADO_ANIOS
            )
            return VAC_ANIO if context.user_data.get("tipo") == "VACACIONES" else PERMISO_ANIO
    except Exception:
        pass

    await update.message.reply_text("¿Qué *día* termina?", reply_markup=ReplyKeyboardRemove())
    return FIN_DIA

async def recibir_fin_dia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dia = _parse_dia(update.message.text)
    if not dia:
        await update.message.reply_text("Día inválido. Dame un número de 1 a 31.")
        return FIN_DIA
    context.user_data["fin_dia"] = dia
    await update.message.reply_text("¿De qué *mes* termina?", reply_markup=TECLADO_MESES)
    return FIN_MES

async def recibir_fin_mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mes = _parse_mes(update.message.text)
    if not mes:
        await update.message.reply_text("Elige un mes válido.", reply_markup=TECLADO_MESES)
        return FIN_MES
    context.user_data["fin_mes"] = mes

    if context.user_data.get("tipo") == "PERMISO":
        await update.message.reply_text("¿Cuál es el horario? Ej: `09:00-11:00` o `Todo el día`.", reply_markup=ReplyKeyboardRemove())
        return HORARIO

    await update.message.reply_text("Entendido. ¿Cuál es el motivo o comentario adicional?", reply_markup=ReplyKeyboardRemove())
    return MOTIVO

async def recibir_horario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["horario"] = update.message.text.strip()
    await update.message.reply_text("Entendido. ¿Cuál es el motivo o comentario adicional?", reply_markup=ReplyKeyboardRemove())
    return MOTIVO

# --- Motivo y cierre ---
async def recibir_motivo_fin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    motivo = update.message.text
    datos = context.user_data
    user = update.effective_user

    fechas = _build_dates(datos)
    if not fechas:
        await update.message.reply_text("🤔 No entendí las fechas. Por favor, inicia otra vez con /vacaciones o /permiso.")
        return ConversationHandler.END
    
    payload = {
        "record_id": str(uuid.uuid4()),
        "solicitante": {
            "id_telegram": user.id,
            "nombre": user.full_name,
            "username": user.username
        },
        "tipo_solicitud": datos['tipo'],
        "fechas": {
            "inicio": fechas.get("inicio").isoformat() if fechas else None,
            "fin": fechas.get("fin").isoformat() if fechas else None,
        },
        "motivo_usuario": motivo,
        "created_at": datetime.now().isoformat()
    }

    webhooks = []
    if datos['tipo'] == 'PERMISO':
        webhooks = _get_webhook_list("WEBHOOK_PERMISOS")
        categoria = classify_reason(motivo)
        payload["categoria_detectada"] = categoria
        payload["horario"] = datos.get("horario", "N/A")
        await update.message.reply_text(f"Categoría detectada → **{categoria}** 🚨")
    
    elif datos['tipo'] == 'VACACIONES':
        webhooks = _get_webhook_list("WEBHOOK_VACACIONES")
        metrics = _calculate_vacation_metrics_from_dates(fechas)
        
        if metrics["dias_totales"] > 0:
            payload["metricas"] = metrics
            
            dias = metrics["dias_totales"]
            if dias <= 5:
                status = "RECHAZADO"
                mensaje = f"🔴 {dias} días es un periodo muy corto. Las vacaciones deben ser de al menos 6 días."
            elif dias > 30:
                status = "RECHAZADO"
                mensaje = "🔴 Las vacaciones no pueden exceder 30 días. Ajusta tus fechas, por favor."
            elif 6 <= dias <= 11:
                status = "REVISION_MANUAL"
                mensaje = f"🟡 Solicitud de {dias} días recibida. Tu manager la revisará pronto."
            else: # 12-30
                status = "PRE_APROBADO"
                mensaje = f"🟢 ¡Excelente planeación! Tu solicitud de {dias} días ha sido pre-aprobada (ideal: 12 días)."
            
            payload["status_inicial"] = status
            await update.message.reply_text(mensaje)
        else:
            payload["status_inicial"] = "ERROR_FECHAS"
            await update.message.reply_text("🤔 No entendí las fechas. Por favor, comparte día y mes otra vez con /vacaciones.")

    try:
        enviados = _send_webhooks(webhooks, payload) if webhooks else 0
        tipo_solicitud_texto = "Permiso" if datos['tipo'] == 'PERMISO' else 'Vacaciones'
        inicio_txt = _fmt_fecha(payload["fechas"]["inicio"])
        fin_txt = _fmt_fecha(payload["fechas"]["fin"])
        if datos['tipo'] == 'PERMISO':
            resumen = (
                "📝 Resumen enviado:\n"
                f"- Fecha: {inicio_txt} a {fin_txt}\n"
                f"- Horario: {payload.get('horario', 'N/A')}\n"
                f"- Categoría: {payload.get('categoria_detectada', 'N/A')}\n"
                f"- Motivo: {motivo}"
            )
        else:
            m = payload.get("metricas", {})
            resumen = (
                "📝 Resumen enviado:\n"
                f"- Inicio: {inicio_txt}\n"
                f"- Fin: {fin_txt}\n"
                f"- Días totales: {m.get('dias_totales', 'N/A')}\n"
                f"- Anticipación: {m.get('dias_anticipacion', 'N/A')} días\n"
                f"- Estatus inicial: {payload.get('status_inicial', 'N/A')}"
            )
        if enviados > 0:
            await update.message.reply_text(f"✅ Solicitud de *{tipo_solicitud_texto}* enviada a tu Manager.\n\n{resumen}")
        else:
            await update.message.reply_text(f"⚠️ No hay webhook configurado o falló el envío. RH lo revisará.\n\n{resumen}")
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
        VAC_ANIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_anio_vacaciones)],
        INICIO_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_inicio_dia)],
        INICIO_MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_inicio_mes)],
        FIN_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fin_dia)],
        FIN_MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fin_mes)],
        MOTIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_motivo_fin)]
    },
    fallbacks=[CommandHandler("cancelar", cancelar)]
)

permiso_handler = ConversationHandler(
    entry_points=[CommandHandler("permiso", start_permiso)],
    states={
        PERMISO_CUANDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cuando_permiso)],
        PERMISO_ANIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_anio_permiso)],
        INICIO_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_inicio_dia)],
        INICIO_MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_inicio_mes)],
        FIN_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fin_dia)],
        FIN_MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fin_mes)],
        HORARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_horario)],
        MOTIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_motivo_fin)]
    },
    fallbacks=[CommandHandler("cancelar", cancelar)]
)
