import logging
from modules.database import SessionUsersAlma
from models.users_alma_models import RequestLog

def log_request(telegram_id, username, command, message):
    if not SessionUsersAlma:
        logging.debug("DB log omitted (DB not configured).")
        return

    try:
        db_session = SessionUsersAlma()
    except Exception as exc:
        logging.error(f"Could not create DB session, logging is disabled: {exc}")
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
        logging.info(f"Log saved: {command} from {username}")
    except Exception as e:
        logging.error(f"Error saving log: {e}")
        db_session.rollback()
    finally:
        db_session.close()
