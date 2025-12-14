import logging
import os
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, MetaData, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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

def _build_engine():
    """Crea un engine de SQLAlchemy si hay variables de entorno suficientes."""
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")
    host = os.getenv("MYSQL_HOST") or "db"  # Permitimos override para uso local

    if not all([user, password, database]):
        logging.warning("DB logging deshabilitado: faltan MYSQL_USER/MYSQL_PASSWORD/MYSQL_DATABASE.")
        return None

    try:
        db_url = f"mysql+mysqlconnector://{user}:{password}@{host}:3306/{database}"
        return create_engine(db_url, pool_pre_ping=True)
    except Exception as exc:
        logging.error(f"No se pudo crear el engine de base de datos: {exc}")
        return None

def _disable_db_logging(reason: str):
    """Deshabilita el logging a DB después de un error para evitar spam."""
    global engine, SessionLocal
    engine = None
    SessionLocal = None
    logging.warning(f"DB logging deshabilitado: {reason}")

# Crear el engine y sesión si es posible
engine = _build_engine()
metadata = MetaData() if engine else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

# Función para inicializar la base de datos
def init_db():
    global engine, SessionLocal
    if not engine:
        return
    try:
        logging.info("Inicializando la base de datos y creando tablas si no existen...")
        Base.metadata.create_all(bind=engine)
        logging.info("Tablas verificadas/creadas correctamente.")
    except Exception as e:
        logging.error(f"Error al inicializar la base de datos: {e}")
        _disable_db_logging("no se pudo inicializar la base de datos (se omitirán logs).")
        # No propagamos para que el bot pueda seguir levantando aunque no haya DB

# Función para registrar una solicitud en la base de datos
def log_request(telegram_id, username, command, message):
    if not SessionLocal:
        logging.debug("Log de DB omitido (DB no configurada).")
        return

    try:
        db_session = SessionLocal()
    except Exception as exc:
        logging.error(f"No se pudo crear sesión DB, se deshabilita el log: {exc}")
        _disable_db_logging("no se pudo abrir sesión")
        return
    try:
        log_entry = RequestLog(
            telegram_id=str(telegram_id),
            username=username,
            command=command,
            message=message
        )
        db_session.add(log_entry)
        db_session.commit()
        logging.info(f"Log guardado: {command} de {username}")
    except Exception as e:
        logging.error(f"Error al guardar el log: {e}")
        db_session.rollback()
    finally:
        db_session.close()

# Inicializar la base de datos al arrancar el módulo
init_db()
