import logging
import os
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.users_alma_models import Base as BaseUsersAlma, User
from models.vanity_hr_models import Base as BaseVanityHr, DataEmpleadas, Vacaciones, Permisos, HorarioEmpleadas
from models.vanity_attendance_models import Base as BaseVanityAttendance, AsistenciaRegistros


# --- DATABASE (MySQL) SETUP ---
def _build_engine(db_name_env_var):
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    db_name = os.getenv(db_name_env_var)
    host = os.getenv("MYSQL_HOST", "db")

    if not all([user, password, db_name]):
        logging.warning(f"Database connection disabled: missing environment variables for {db_name_env_var}.")
        return None

    try:
        db_url = f"mysql+mysqlconnector://{user}:{password}@{host}:3306/{db_name}"
        return create_engine(db_url, pool_pre_ping=True)
    except Exception as exc:
        logging.error(f"Could not create database engine for {db_name}: {exc}")
        return None

# Create engines for each database
engine_users_alma = _build_engine("MYSQL_DATABASE_USERS_ALMA")
engine_vanity_hr = _build_engine("MYSQL_DATABASE_VANITY_HR")
engine_vanity_attendance = _build_engine("MYSQL_DATABASE_VANITY_ATTENDANCE")

# Create sessions for each database
SessionUsersAlma = sessionmaker(autocommit=False, autoflush=False, bind=engine_users_alma) if engine_users_alma else None
SessionVanityHr = sessionmaker(autocommit=False, autoflush=False, bind=engine_vanity_hr) if engine_vanity_hr else None
SessionVanityAttendance = sessionmaker(autocommit=False, autoflush=False, bind=engine_vanity_attendance) if engine_vanity_attendance else None

# --- GOOGLE SHEETS SETUP (REMOVED) ---
# Duplicate checking is now done via database.

def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for parser in (
        lambda v: datetime.fromisoformat(v),
        lambda v: datetime.strptime(v, "%Y-%m-%d"),
        lambda v: datetime.strptime(v, "%d/%m/%Y"),
    ):
        try:
            return parser(str(value)).date()
        except Exception:
            continue
    return None

def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        pass
    try:
        return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def _build_full_address(domicilio: dict) -> str:
    if not domicilio:
        return ""
    partes = []
    calle = domicilio.get("calle")
    num_ext = domicilio.get("num_ext")
    num_int = domicilio.get("num_int")
    colonia = domicilio.get("colonia")
    cp = domicilio.get("cp")
    ciudad = domicilio.get("ciudad")
    estado = domicilio.get("estado")

    if calle:
        linea = f"{calle}"
        if num_ext:
            linea += f" {num_ext}"
        if num_int and num_int not in ("0", "N/A"):
            linea += f" Int {num_int}"
        partes.append(linea)
    if colonia:
        partes.append(colonia)
    if ciudad or estado:
        partes.append(", ".join(filter(None, [ciudad, estado])))
    if cp:
        partes.append(f"CP {cp}")
    return " - ".join(partes)

def _references_with_padding(referencias: list) -> list:
    refs = referencias or []
    if len(refs) < 3:
        refs = refs + [{}] * (3 - len(refs))
    return refs[:3]

def chat_id_exists(chat_id: int) -> bool:
    """Checks if a Telegram chat_id already exists in the USERS_ALMA.users table."""
    if not SessionUsersAlma:
        logging.warning("SessionUsersAlma not initialized. Cannot check if chat_id exists.")
        return False
    
    session = SessionUsersAlma()
    try:
        exists = session.query(User).filter(User.telegram_id == str(chat_id)).first() is not None
        return exists
    except Exception as e:
        logging.error(f"Error checking if chat_id exists in DB: {e}")
        return False
    finally:
        session.close()

def register_user(user_data: dict) -> bool:
    """
    Persists a new colaboradora across the USERS_ALMA.users and vanity_hr.data_empleadas tables.

    Expected structure (all keys optional but recommended):
    {
        "meta": {...}, "metadata": {...}, "candidato": {...}, "contacto": {...},
        "domicilio": {...}, "laboral": {...}, "referencias": [...], "emergencia": {...}
    }
    """
    if not SessionUsersAlma or not SessionVanityHr:
        logging.warning("Database sessions not initialized. Cannot register user.")
        return False

    meta = user_data.get("meta") or {}
    metadata = user_data.get("metadata") or {}
    candidato = user_data.get("candidato") or {}
    contacto = user_data.get("contacto") or {}
    domicilio = user_data.get("domicilio") or {}
    laboral = user_data.get("laboral") or {}
    referencias = _references_with_padding(user_data.get("referencias") or [])
    emergencia = user_data.get("emergencia") or {}

    telegram_id = metadata.get("chat_id") or meta.get("telegram_id")
    if not telegram_id:
        logging.error("register_user: missing telegram_id; aborting persist.")
        return False

    # --- USERS_ALMA.users ---
    session_users = SessionUsersAlma()
    try:
        user_record = session_users.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if user_record:
            user_record.username = metadata.get("telegram_user") or meta.get("username")
            user_record.first_name = candidato.get("nombre_preferido") or meta.get("first_name")
            apellidos = f"{candidato.get('apellido_paterno', '')} {candidato.get('apellido_materno', '')}".strip()
            user_record.last_name = apellidos or user_record.last_name
            user_record.email = contacto.get("email") or user_record.email
            user_record.cell_phone = contacto.get("celular") or user_record.cell_phone
        else:
            user_record = User(
                telegram_id=str(telegram_id),
                username=metadata.get("telegram_user") or meta.get("username"),
                first_name=candidato.get("nombre_preferido") or meta.get("first_name"),
                last_name=f"{candidato.get('apellido_paterno', '')} {candidato.get('apellido_materno', '')}".strip(),
                email=contacto.get("email"),
                cell_phone=contacto.get("celular"),
                role='user'
            )
            session_users.add(user_record)
        session_users.commit()
    except Exception as exc:
        session_users.rollback()
        logging.error(f"Error persisting user in USERS_ALMA: {exc}")
        return False
    finally:
        session_users.close()

    # --- vanity_hr.data_empleadas ---
    numero_empleado = laboral.get("numero_empleado") or f"T{telegram_id}"
    fecha_registro = _parse_datetime(metadata.get("fecha_registro")) or datetime.utcnow()
    fecha_procesamiento = datetime.utcnow()
    fecha_ingreso = _parse_date(laboral.get("fecha_inicio"))
    fecha_nacimiento = _parse_date(candidato.get("fecha_nacimiento"))
    tiempo_registro_minutos = None
    try:
        duracion_segundos = float(metadata.get("duracion_segundos", 0))
        tiempo_registro_minutos = int(round(duracion_segundos / 60))
    except Exception:
        tiempo_registro_minutos = None

    nombre = candidato.get("nombre_oficial") or ""
    apellido_paterno = candidato.get("apellido_paterno") or ""
    apellido_materno = candidato.get("apellido_materno") or ""
    nombre_completo = " ".join(filter(None, [nombre, apellido_paterno, apellido_materno])).strip()

    domicilio_completo = _build_full_address(domicilio)
    telegram_username = metadata.get("telegram_user") or meta.get("username")
    try:
        telegram_chat_id = int(telegram_id)
    except Exception:
        telegram_chat_id = None

    empleada_payload = {
        "numero_empleado": numero_empleado,
        "puesto": laboral.get("rol_id"),
        "sucursal": laboral.get("sucursal_id"),
        "fecha_ingreso": fecha_ingreso,
        "estatus": "activo",
        "nombre_completo": nombre_completo or nombre,
        "nombre": nombre or meta.get("first_name"),
        "nombre_preferido": candidato.get("nombre_preferido"),
        "apellido_paterno": apellido_paterno,
        "apellido_materno": apellido_materno,
        "fecha_nacimiento": fecha_nacimiento,
        "lugar_nacimiento": candidato.get("lugar_nacimiento"),
        "rfc": candidato.get("rfc"),
        "curp": candidato.get("curp"),
        "email": contacto.get("email"),
        "telefono_celular": contacto.get("celular"),
        "domicilio_calle": domicilio.get("calle"),
        "domicilio_numero_exterior": domicilio.get("num_ext"),
        "domicilio_numero_interior": domicilio.get("num_int"),
        "domicilio_numero_texto": domicilio.get("num_ext_texto"),
        "domicilio_colonia": domicilio.get("colonia"),
        "domicilio_codigo_postal": domicilio.get("cp"),
        "domicilio_ciudad": domicilio.get("ciudad"),
        "domicilio_estado": domicilio.get("estado"),
        "domicilio_completo": domicilio_completo,
        "emergencia_nombre": emergencia.get("nombre"),
        "emergencia_telefono": emergencia.get("telefono"),
        "emergencia_parentesco": emergencia.get("relacion"),
        "referencia_1_nombre": referencias[0].get("nombre"),
        "referencia_1_telefono": referencias[0].get("telefono"),
        "referencia_1_tipo": referencias[0].get("relacion"),
        "referencia_2_nombre": referencias[1].get("nombre"),
        "referencia_2_telefono": referencias[1].get("telefono"),
        "referencia_2_tipo": referencias[1].get("relacion"),
        "referencia_3_nombre": referencias[2].get("nombre"),
        "referencia_3_telefono": referencias[2].get("telefono"),
        "referencia_3_tipo": referencias[2].get("relacion"),
        "origen_registro": "telegram_bot",
        "telegram_usuario": telegram_username,
        "telegram_chat_id": telegram_chat_id,
        "bot_version": metadata.get("bot_version"),
        "fecha_registro": fecha_registro,
        "tiempo_registro_minutos": tiempo_registro_minutos,
        "fecha_procesamiento": fecha_procesamiento
    }

    session_hr = SessionVanityHr()
    try:
        existing = session_hr.get(DataEmpleadas, numero_empleado)
        if existing:
            for field, value in empleada_payload.items():
                setattr(existing, field, value)
        else:
            session_hr.add(DataEmpleadas(**empleada_payload))
        session_hr.commit()
        logging.info(f"User {telegram_id} registered in vanity_hr.data_empleadas as {numero_empleado}.")
        return True
    except Exception as exc:
        session_hr.rollback()
        logging.error(f"Error persisting colaboradora in vanity_hr: {exc}")
        return False
    finally:
        session_hr.close()
