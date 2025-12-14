import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@db:3306/vanessa_logs")

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)
metadata = MetaData()

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

# Función para inicializar la base de datos
def init_db():
    try:
        logging.info("Inicializando la base de datos y creando tablas si no existen...")
        Base.metadata.create_all(bind=engine)
        logging.info("Tablas verificadas/creadas correctamente.")
    except Exception as e:
        logging.error(f"Error al inicializar la base de datos: {e}")
        raise

# Crear una sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Función para registrar una solicitud en la base de datos
def log_request(telegram_id, username, command, message):
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
        logging.info(f"Log guardado: {command} de {username}")
    except Exception as e:
        logging.error(f"Error al guardar el log: {e}")
        db_session.rollback()
    finally:
        db_session.close()

# Inicializar la base de datos al arrancar el módulo
init_db()
