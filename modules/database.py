import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.users_alma_models import Base as BaseUsersAlma, User
from models.vanity_hr_models import Base as BaseVanityHr, DataEmpleadas, Vacaciones, Permisos
from models.vanity_attendance_models import Base as BaseVanityAttendance, AsistenciaRegistros, HorarioEmpleadas
import gspread
from google.oauth2.service_account import Credentials

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

# --- GOOGLE SHEETS SETUP ---
GSHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")
SHEET_COLUMN_INDEX = 40  # AN is the 40th column

def get_gsheet_client():
    """Returns an authenticated gspread client or None if it fails."""
    if not GSHEET_URL:
        logging.warning("GOOGLE_SHEET_URL is not configured. Duplicate checking is disabled.")
        return None

    creds = None
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

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
        except Exception as e:
            logging.error(f"Error processing Google credentials from environment: {e}")
            return None
    elif os.path.exists(GOOGLE_CREDENTIALS_FILE):
        try:
            creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scopes)
        except Exception as e:
            logging.error(f"Error processing credentials file '{GOOGLE_CREDENTIALS_FILE}': {e}")
            return None
    else:
        logging.warning("Google credentials not found (neither environment variables nor file). Duplicate checking is disabled.")
        return None

    try:
        return gspread.authorize(creds)
    except Exception as e:
        logging.error(f"Error authorizing gspread client: {e}")
        return None

def chat_id_exists(chat_id: int) -> bool:
    """Checks if a Telegram chat_id already exists in the Google Sheet."""
    client = get_gsheet_client()
    if not client:
        return False

    try:
        spreadsheet = client.open_by_url(GSHEET_URL)
        worksheet = spreadsheet.get_worksheet(0)
        chat_ids_in_sheet = worksheet.col_values(SHEET_COLUMN_INDEX)
        return str(chat_id) in chat_ids_in_sheet
    except gspread.exceptions.SpreadsheetNotFound:
        logging.error("Could not find the spreadsheet at the provided URL.")
        return False
    except Exception as e:
        logging.error(f"Error reading the spreadsheet: {e}")
        return False
