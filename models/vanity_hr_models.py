from sqlalchemy import create_engine, Column, Integer, String, Enum, TIMESTAMP, Date, Text, BigInteger, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class DataEmpleadas(Base):
    __tablename__ = 'data_empleadas'
    __table_args__ = {'schema': 'vanity_hr'}

    numero_empleado = Column(String(15), primary_key=True)
    puesto = Column(String(50))
    sucursal = Column(String(50))
    fecha_ingreso = Column(Date)
    estatus = Column(String(15))
    nombre_completo = Column(String(150))
    nombre = Column(String(50))
    nombre_preferido = Column(String(50))
    apellido_paterno = Column(String(50))
    apellido_materno = Column(String(50))
    fecha_nacimiento = Column(Date)
    lugar_nacimiento = Column(String(50))
    rfc = Column(String(13), unique=True)
    curp = Column(String(18), unique=True)
    email = Column(String(100))
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
    telegram_chat_id = Column(BigInteger)
    bot_version = Column(String(20))
    fecha_registro = Column(DateTime)
    tiempo_registro_minutos = Column(Integer)
    fecha_procesamiento = Column(DateTime)

class Vacaciones(Base):
    __tablename__ = 'vacaciones'
    __table_args__ = {'schema': 'vanity_hr'}

    vacaciones_id = Column(String(50), primary_key=True)
    numero_empleado = Column(String(15), ForeignKey('vanity_hr.data_empleadas.numero_empleado'))
    tipo_solicitud = Column(String(20))
    estatus = Column(Enum('pendiente', 'aprobado', 'rechazado', 'cancelado'))
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    dias_solicitados = Column(Integer)
    dias_habiles = Column(Integer)
    motivo = Column(Text)
    con_goce_sueldo = Column(TINYINT)
    fecha_solicitud = Column(DateTime)
    fecha_procesamiento = Column(DateTime)
    origen = Column(String(20))
    afecta_nomina = Column(TINYINT)
    empleada = relationship("DataEmpleadas")

class Permisos(Base):
    __tablename__ = 'permisos'
    __table_args__ = {'schema': 'vanity_hr'}

    permiso_id = Column(String(50), primary_key=True)
    numero_empleado = Column(String(15), ForeignKey('vanity_hr.data_empleadas.numero_empleado'))
    categoria = Column(Enum('PERSONAL', 'MEDICO', 'OFICIAL', 'OTRO'))
    estatus = Column(Enum('pendiente', 'aprobado', 'rechazado', 'cancelado'))
    fecha_inicio = Column(Date)
    horario_especifico = Column(String(50))
    motivo = Column(Text)
    con_goce_sueldo = Column(TINYINT)
    afecta_nomina = Column(TINYINT)
    empleada = relationship("DataEmpleadas")
