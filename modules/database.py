import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.users_alma_models import Base as BaseUsersAlma, User
from models.vanity_hr_models import Base as BaseVanityHr, DataEmpleadas, Vacaciones, Permisos
from models.vanity_attendance_models import Base as BaseVanityAttendance, AsistenciaRegistros, HorarioEmpleadas


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
    """Registers a new user in the USERS_ALMA.users table."""
    if not SessionUsersAlma:
        logging.warning("SessionUsersAlma not initialized. Cannot register user.")
        return False

    session = SessionUsersAlma()
    try:
        new_user = User(
            telegram_id=str(user_data.get("chat_id")),
            username=user_data.get("telegram_user"),
            first_name=user_data.get("first_name"),
            last_name=f"{user_data.get('apellido_paterno', '')} {user_data.get('apellido_materno', '')}".strip(),
            email=user_data.get("email"),
            cell_phone=user_data.get("celular"),
            role='user' # Default role
        )
        session.add(new_user)
        session.commit()
        logging.info(f"User {user_data.get('chat_id')} registered successfully in DB.")
        return True
    except Exception as e:
        session.rollback()
        logging.error(f"Error registering user in DB: {e}")
        return False
    finally:
        session.close()

