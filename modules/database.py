import logging
import os
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, MetaData, String, create_engine, BIGINT, Date, INT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# --- DATABASE (MySQL) SETUP ---

# Base para los modelos declarativos
Base = declarative_base()

# Clase que mapea a la tabla de logs
class RequestLog(Base):
    __tablename__ = 'request_logs'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50))
    username = Column(String(100))
    command = Column(String(100))
    message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

# Clase que mapea a la tabla de datos de RRHH
class FullHRData(Base):
    __tablename__ = 'full_HRdata'
    __table_args__ = {'schema': 'vanessa_logs'}
    numero_empleado = Column(String(15), primary_key=True, nullable=False)
    puesto = Column(String(50))
    sucursal = Column(String(50))
    fecha_ingreso = Column(Date, nullable=False)
    estatus = Column(String(15))
    nombre_completo = Column(String(150))
    nombre = Column(String(50), nullable=False)
    nombre_preferido = Column(String(50))
    apellido_paterno = Column(String(50), nullable=False)
    apellido_materno = Column(String(50))
    fecha_nacimiento = Column(Date)
    lugar_nacimiento = Column(String(50))
    rfc = Column(String(13), nullable=False, unique=True)
    curp = Column(String(18), nullable=False, unique=True)
    email = Column(String(100), unique=True)
    telefono_celular = Column(String(15))
    domicilio_calle = Column(String(255))
    domicilio_numero_exterior = Column(String(10))
    domicilio_numero_interior = Column(String(10))
    domicilio_numero_texto = Column(String(50))
    domicilio_colonia = Column(String(255))
    domicilio_codigo_postal = Column(String(10))
    domicilio_ciudad = Column(String(100))
    domicilio_estado = Column(String(50))
    domicilio_completo = Column(String(255))
    emergencia_nombre = Column(String(100))
    emergencia_telefono = Column(String(15))
    emergencia_parentesco = Column(String(50))
    referencia_1_nombre = Column(String(100))
    referencia_1_telefono = Column(String(15))
    referencia_1_tipo = Column(String(20))
    referencia_2_nombre = Column(String(100))
    referencia_2_telefono = Column(String(15))
    referencia_2_tipo = Column(String(20))
    referencia_3_nombre = Column(String(100))
    referencia_3_telefono = Column(String(15))
    referencia_3_tipo = Column(String(20))
    origen_registro = Column(String(50))
    telegram_usuario = Column(String(50))
    telegram_chat_id = Column(BIGINT)
    bot_version = Column(String(20))
    fecha_registro = Column(DateTime)
    tiempo_registro_minutos = Column(INT)
    interacciones_bot = Column(INT)
    fecha_procesamiento = Column(DateTime(timezone=True))


def _build_engine():
    """Crea un engine de SQLAlchemy si hay variables de entorno suficientes."""
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")
    host = os.getenv("MYSQL_HOST") or "db"  # Permitimos override para uso local

    if not all([user, password, database]):
        logging.warning("DB connection disabled: MYSQL_USER/MYSQL_PASSWORD/MYSQL_DATABASE are missing.")
        return None

    try:
        db_url = f"mysql+mysqlconnector://{user}:{password}@{host}:3306/{database}"
        return create_engine(db_url, pool_pre_ping=True)
    except Exception as exc:
        logging.error(f"Could not create database engine: {exc}")
        return None

def _disable_db_logging(reason: str):
    """Deshabilita el logging a DB después de un error para evitar spam."""
    global engine, SessionLocal
    engine = None
    SessionLocal = None
    logging.warning(f"DB logging disabled: {reason}")

# Crear el engine y sesión si es posible
engine = _build_engine()
metadata = MetaData() if engine else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

# Función para inicializar la base de datos
def init_db():
    global engine
    if not engine:
        return
    try:
        logging.info("Initializing the database and creating tables if they do not exist...")
        Base.metadata.create_all(bind=engine)
        logging.info("Tables verified/created successfully.")
    except Exception as e:
        logging.error(f"Error initializing the database: {e}")
        _disable_db_logging("could not initialize database (logging will be skipped).")

def check_user_registration(chat_id: int) -> bool:
    """
    Verifica si un telegram_chat_id ya existe en la tabla full_HRdata.
    Retorna True si el usuario ya está registrado, False en caso contrario.
    """
    if not SessionLocal:
        logging.warning("DB check skipped (DB not configured). Assuming user is not registered.")
        return False

    db_session = SessionLocal()
    try:
        count = db_session.query(FullHRData).filter(FullHRData.telegram_chat_id == chat_id).count()
        if count > 0:
            logging.info(f"User with chat_id {chat_id} is already registered.")
            return True
        else:
            logging.info(f"User with chat_id {chat_id} is not registered.")
            return False
    except Exception as e:
        logging.error(f"Error checking user registration for chat_id {chat_id}: {e}")
        # En caso de error, es más seguro asumir que no está registrado para no bloquear a un usuario legítimo.
        return False
    finally:
        db_session.close()

# Función para registrar una solicitud en la base de datos
def log_request(telegram_id, username, command, message):
    if not SessionLocal:
        logging.debug("DB log skipped (DB not configured).")
        return

    db_session = SessionLocal()
    try:
        log_entry = RequestLog(
            telegram_id=str(telegram_id),
            username=username,
            command=command,
            message=message
        )
        db_session.add(log_entry)
        db_session.commit()
        logging.info(f"Log saved: {command} from {username}")
    except Exception as e:
        logging.error(f"Error saving log: {e}")
        db_session.rollback()
    finally:
        db_session.close()

# Inicializar la base de datos al arrancar el módulo
init_db()
