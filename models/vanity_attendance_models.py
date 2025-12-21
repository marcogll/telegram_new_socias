from sqlalchemy import create_engine, Column, Integer, String, Date, Time, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class AsistenciaRegistros(Base):
    __tablename__ = 'asistencia_registros'
    __table_args__ = {'schema': 'vanity_attendance'}

    id_asistencia = Column(Integer, primary_key=True, autoincrement=True)
    numero_empleado = Column(String(15), ForeignKey('vanity_hr.data_empleadas.numero_empleado'))
    fecha = Column(Date)
    hora_entrada_real = Column(Time)
    hora_salida_real = Column(Time)
    minutos_retraso = Column(Integer)
    minutos_extra = Column(Integer)
    sucursal_registro = Column(String(50))
    telegram_id_usado = Column(BigInteger)
    empleada = relationship("DataEmpleadas", backref="asistencia_registros")
