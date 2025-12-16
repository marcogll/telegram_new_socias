import logging
import os
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, MetaData, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import gspread
from google.oauth2.service_account import Credentials

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# --- GOOGLE SHEETS SETUP ---
GSHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")
SHEET_COLUMN_INDEX = 40  # AN is the 40th column

def get_gsheet_client():
    """Retorna un cliente de gspread autenticado o None si falla."""
    if not GSHEET_URL:
        logging.warning("GOOGLE_SHEET_URL no está configurada. La verificación de duplicados está deshabilitada.")
        return None

    creds = None
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    # Prioridad 1: Cargar desde variables de entorno
    gsa_creds_dict = {
        "type": os.getenv("GSA_TYPE"),
        "project_id": os.getenv("GSA_PROJECT_ID"),
        "private_key_id": os.getenv("GSA_PRIVATE_KEY_ID"),
        "private_key": (os.getenv("GSA_PRIVATE_KEY") or "").replace("\\n", "\n"),
        "client_email": os.getenv("GSA_CLIENT_EMAIL"),
        "client_id": os.getenv("GSA_CLIENT_ID"),
        "auth_uri": os.getenv("GSA_AUTH_URI"),
        "token_uri": os.getenv("GSA_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("GSA_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("GSA_CLIENT_X509_CERT_URL"),
    }

    if all(gsa_creds_dict.values()):
        try:
            creds = Credentials.from_service_account_info(gsa_creds_dict, scopes=scopes)
            logging.info("Autenticando con Google Sheets usando variables de entorno.")
        except Exception as e:
            logging.error(f"Error al procesar credenciales de entorno de Google: {e}")
            return None
    # Prioridad 2: Cargar desde archivo JSON
    elif os.path.exists(GOOGLE_CREDENTIALS_FILE):
        try:
            creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scopes)
            logging.info(f"Autenticando con Google Sheets usando el archivo '{GOOGLE_CREDENTIALS_FILE}'.")
        except Exception as e:
            logging.error(f"Error al procesar el archivo de credenciales '{GOOGLE_CREDENTIALS_FILE}': {e}")
            return None
    else:
        logging.warning("No se encontraron credenciales de Google (ni por variables de entorno ni por archivo). La verificación de duplicados está deshabilitada.")
        return None

    try:
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logging.error(f"Error al autorizar cliente de gspread: {e}")
        return None

def chat_id_exists(chat_id: int) -> bool:
    """Verifica si un chat_id de Telegram ya existe en la columna AN de la hoja de cálculo."""
    client = get_gsheet_client()
    if not client:
        return False  # Si no hay cliente, no podemos verificar, así que asumimos que no existe.

    try:
        spreadsheet = client.open_by_url(GSHEET_URL)
        worksheet = spreadsheet.get_worksheet(0)  # Primera hoja
        
        # Obtener todos los valores de la columna AN (índice 40)
        chat_ids_in_sheet = worksheet.col_values(SHEET_COLUMN_INDEX)
        
        # El ID de chat puede venir como número o texto, así que comparamos como string
        return str(chat_id) in chat_ids_in_sheet
        
    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"No se pudo encontrar la hoja de cálculo en la URL proporcionada.")
        return False
    except Exception as e:
        logging.error(f"Error al leer la hoja de cálculo: {e}")
        return False


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
