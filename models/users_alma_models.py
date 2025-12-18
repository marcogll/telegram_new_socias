from sqlalchemy import create_engine, Column, Integer, String, Enum, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class RequestLog(Base):
    __tablename__ = 'request_logs'
    __table_args__ = {'schema': 'USERS_ALMA'}
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50))
    username = Column(String(100))
    command = Column(String(100))
    message = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'USERS_ALMA'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True)
    role = Column(Enum('admin', 'manager', 'user'))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100), unique=True)
    cell_phone = Column(String(20))
    telegram_id = Column(String(50), unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
