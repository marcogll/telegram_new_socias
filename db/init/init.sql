CREATE DATABASE IF NOT EXISTS USERS_ALMA;
CREATE DATABASE IF NOT EXISTS vanity_hr;
CREATE DATABASE IF NOT EXISTS vanity_attendance;

USE USERS_ALMA;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    role ENUM('admin', 'manager', 'user'),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    cell_phone VARCHAR(20),
    telegram_id VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS request_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id VARCHAR(50),
    username VARCHAR(100),
    command VARCHAR(100),
    message VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

USE vanity_hr;

CREATE TABLE IF NOT EXISTS data_empleadas (
    numero_empleado VARCHAR(15) PRIMARY KEY,
    puesto VARCHAR(50),
    sucursal VARCHAR(50),
    fecha_ingreso DATE,
    estatus VARCHAR(15),
    nombre_completo VARCHAR(150),
    nombre VARCHAR(50),
    nombre_preferido VARCHAR(50),
    apellido_paterno VARCHAR(50),
    apellido_materno VARCHAR(50),
    fecha_nacimiento DATE,
    lugar_nacimiento VARCHAR(50),
    rfc VARCHAR(13) UNIQUE,
    curp VARCHAR(18) UNIQUE,
    email VARCHAR(100),
    telefono_celular VARCHAR(15),
    domicilio_calle VARCHAR(255),
    domicilio_numero_exterior VARCHAR(10),
    domicilio_numero_interior VARCHAR(10),
    domicilio_numero_texto VARCHAR(50),
    domicilio_colonia VARCHAR(255),
    domicilio_codigo_postal VARCHAR(10),
    domicilio_ciudad VARCHAR(100),
    domicilio_estado VARCHAR(50),
    domicilio_completo VARCHAR(255),
    emergencia_nombre VARCHAR(100),
    emergencia_telefono VARCHAR(15),
    emergencia_parentesco VARCHAR(50),
    referencia_1_nombre VARCHAR(100),
    referencia_1_telefono VARCHAR(15),
    referencia_1_tipo VARCHAR(20),
    referencia_2_nombre VARCHAR(100),
    referencia_2_telefono VARCHAR(15),
    referencia_2_tipo VARCHAR(20),
    referencia_3_nombre VARCHAR(100),
    referencia_3_telefono VARCHAR(15),
    referencia_3_tipo VARCHAR(20),
    origen_registro VARCHAR(50),
    telegram_usuario VARCHAR(50),
    telegram_chat_id BIGINT,
    bot_version VARCHAR(20),
    fecha_registro DATETIME,
    tiempo_registro_minutos INT,
    fecha_procesamiento DATETIME(3)
);

CREATE TABLE IF NOT EXISTS vacaciones (
    vacaciones_id VARCHAR(50) PRIMARY KEY,
    numero_empleado VARCHAR(15),
    tipo_solicitud VARCHAR(20),
    estatus ENUM('pendiente', 'aprobado', 'rechazado', 'cancelado'),
    fecha_inicio DATE,
    fecha_fin DATE,
    dias_solicitados INT,
    dias_habiles INT,
    motivo TEXT,
    con_goce_sueldo TINYINT(1),
    fecha_solicitud DATETIME,
    fecha_procesamiento DATETIME(3),
    origen VARCHAR(20),
    afecta_nomina TINYINT(1),
    FOREIGN KEY (numero_empleado) REFERENCES data_empleadas(numero_empleado)
);

CREATE TABLE IF NOT EXISTS permisos (
    permiso_id VARCHAR(50) PRIMARY KEY,
    numero_empleado VARCHAR(15),
    categoria ENUM('PERSONAL', 'MEDICO', 'OFICIAL', 'OTRO'),
    estatus ENUM('pendiente', 'aprobado', 'rechazado', 'cancelado'),
    fecha_inicio DATE,
    horario_especifico VARCHAR(50),
    motivo TEXT,
    con_goce_sueldo TINYINT(1),
    afecta_nomina TINYINT(1),
    FOREIGN KEY (numero_empleado) REFERENCES data_empleadas(numero_empleado)
);

CREATE TABLE IF NOT EXISTS horario_empleadas (
    id_horario INT AUTO_INCREMENT PRIMARY KEY,
    numero_empleado VARCHAR(15),
    telegram_id BIGINT,
    dia_semana VARCHAR(20),
    hora_entrada_teorica TIME,
    hora_salida_teorica TIME,
    FOREIGN KEY (numero_empleado) REFERENCES data_empleadas(numero_empleado)
);

USE vanity_attendance;

CREATE TABLE IF NOT EXISTS asistencia_registros (
    id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    numero_empleado VARCHAR(15),
    fecha DATE,
    hora_entrada_real TIME,
    hora_salida_real TIME,
    minutos_retraso INT,
    minutos_extra INT,
    sucursal_registro VARCHAR(50),
    telegram_id_usado BIGINT,
    FOREIGN KEY (numero_empleado) REFERENCES vanity_hr.data_empleadas(numero_empleado)
);
