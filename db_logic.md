# Sistema Integrado de Gestión (Vanity)

Este repositorio documenta la **especificación técnica completa** del ecosistema Vanity: infraestructura de datos, diccionarios de campos sin truncar, relaciones entre entidades y reglas de negocio que gobiernan los Bots, Recursos Humanos y el sistema de Asistencia.

El objetivo es servir como **fuente de verdad técnica** para desarrollo, mantenimiento, auditoría y escalamiento.

---

## 1. Arquitectura de Datos

El sistema se distribuye en **tres bases de datos** dentro del mismo servidor, permitiendo integridad referencial y consultas cruzadas controladas:

* **USERS_ALMA** → Seguridad, autenticación y control de acceso.
* **vanity_hr** → Gestión de personal, vacaciones, permisos y reglas laborales.
* **vanity_attendance** → Control de asistencia y programación de horarios.

---

## 2. Diccionario de Datos

### 2.1 Base de Datos: `vanity_hr`

#### Tabla: `data_empleadas` (Maestra — 44 campos)

Tabla central de Recursos Humanos. Contiene información contractual, personal, de contacto y metadatos de registro.

| Campo                     | Tipo         | Key | Descripción                        |
| ------------------------- | ------------ | --- | ---------------------------------- |
| numero_empleado           | varchar(15)  | PRI | ID único de nómina                 |
| puesto                    | varchar(50)  |     | Cargo / Puesto                     |
| sucursal                  | varchar(50)  |     | Sucursal asignada                  |
| fecha_ingreso             | date         |     | Fecha de alta (base de antigüedad) |
| estatus                   | varchar(15)  |     | Activo / Baja                      |
| nombre_completo           | varchar(150) |     | Nombre completo concatenado        |
| nombre                    | varchar(50)  |     | Nombre(s)                          |
| nombre_preferido          | varchar(50)  |     | Apodo o nombre de preferencia      |
| apellido_paterno          | varchar(50)  |     | Primer apellido                    |
| apellido_materno          | varchar(50)  |     | Segundo apellido                   |
| fecha_nacimiento          | date         |     | Fecha de nacimiento                |
| lugar_nacimiento          | varchar(50)  |     | Ciudad / Estado                    |
| rfc                       | varchar(13)  | UNI | RFC                                |
| curp                      | varchar(18)  | UNI | CURP                               |
| email                     | varchar(100) |     | Correo electrónico                 |
| telefono_celular          | varchar(15)  |     | Teléfono móvil                     |
| domicilio_calle           | varchar(255) |     | Calle                              |
| domicilio_numero_exterior | varchar(10)  |     | Número exterior                    |
| domicilio_numero_interior | varchar(10)  |     | Número interior                    |
| domicilio_numero_texto    | varchar(50)  |     | Referencias                        |
| domicilio_colonia         | varchar(255) |     | Colonia                            |
| domicilio_codigo_postal   | varchar(10)  |     | CP                                 |
| domicilio_ciudad          | varchar(100) |     | Ciudad                             |
| domicilio_estado          | varchar(50)  |     | Estado                             |
| domicilio_completo        | varchar(255) |     | Dirección formateada               |
| emergencia_nombre         | varchar(100) |     | Contacto de emergencia             |
| emergencia_telefono       | varchar(15)  |     | Teléfono de emergencia             |
| emergencia_parentesco     | varchar(50)  |     | Parentesco                         |
| referencia_1_nombre       | varchar(100) |     | Referencia 1                       |
| referencia_1_telefono     | varchar(15)  |     | Teléfono ref 1                     |
| referencia_1_tipo         | varchar(20)  |     | Tipo ref 1                         |
| referencia_2_nombre       | varchar(100) |     | Referencia 2                       |
| referencia_2_telefono     | varchar(15)  |     | Teléfono ref 2                     |
| referencia_2_tipo         | varchar(20)  |     | Tipo ref 2                         |
| referencia_3_nombre       | varchar(100) |     | Referencia 3                       |
| referencia_3_telefono     | varchar(15)  |     | Teléfono ref 3                     |
| referencia_3_tipo         | varchar(20)  |     | Tipo ref 3                         |
| origen_registro           | varchar(50)  |     | Web / Bot                          |
| telegram_usuario          | varchar(50)  |     | Username Telegram                  |
| telegram_chat_id          | bigint       |     | ID de chat Telegram                |
| bot_version               | varchar(20)  |     | Versión del bot                    |
| fecha_registro            | datetime     |     | Timestamp creación                 |
| tiempo_registro_minutos   | int          |     | Duración del registro              |
| fecha_procesamiento       | datetime(3)  |     | Timestamp procesado                |

---

#### Tabla: `vacaciones` (14 campos)

| Campo               | Tipo        | Key | Descripción                                  |
| ------------------- | ----------- | --- | -------------------------------------------- |
| vacaciones_id       | varchar(50) | PRI | ID de solicitud                              |
| numero_empleado     | varchar(15) | MUL | Relación con empleada                        |
| tipo_solicitud      | varchar(20) |     | VACACIONES                                   |
| estatus             | enum        |     | pendiente / aprobado / rechazado / cancelado |
| fecha_inicio        | date        |     | Inicio                                       |
| fecha_fin           | date        |     | Fin                                          |
| dias_solicitados    | int         |     | Total días                                   |
| dias_habiles        | int         |     | Días descontados                             |
| motivo              | text        |     | Observaciones                                |
| con_goce_sueldo     | tinyint(1)  |     | 1 = Sí                                       |
| fecha_solicitud     | datetime    |     | Creación                                     |
| fecha_procesamiento | datetime(3) |     | Cambio de estatus                            |
| origen              | varchar(20) |     | telegram_bot / web                           |
| afecta_nomina       | tinyint(1)  |     | Impacto en pago                              |

---

#### Tabla: `permisos` (9 campos)

| Campo              | Tipo        | Key | Descripción                                  |
| ------------------ | ----------- | --- | -------------------------------------------- |
| permiso_id         | varchar(50) | PRI | ID de permiso                                |
| numero_empleado    | varchar(15) | MUL | Relación RH                                  |
| categoria          | enum        |     | PERSONAL / MEDICO / OFICIAL / OTRO           |
| estatus            | enum        |     | pendiente / aprobado / rechazado / cancelado |
| fecha_inicio       | date        |     | Fecha                                        |
| horario_especifico | varchar(50) |     | Rango horario                                |
| motivo             | text        |     | Razón                                        |
| con_goce_sueldo    | tinyint(1)  |     | 0 / 1                                        |
| afecta_nomina      | tinyint(1)  |     | Impacto                                      |


#### Tabla: `horario_empleadas` (Diccionario de turnos)

| Campo                | Tipo        | Key | Descripción      |
| -------------------- | ----------- | --- | ---------------- |
| id_horario           | int         | PRI | ID               |
| numero_empleado      | varchar(15) | MUL | Relación RH      |
| telegram_id          | bigint      |     | Llave webhook    |
| dia_semana           | varchar(20) |     | monday, tuesday… |
| hora_entrada_teorica | time        |     | Entrada          |
| hora_salida_teorica  | time        |     | Salida           |

*Los capturados desde `/horario` generan un registro por día mediante upsert (por `telegram_id` + `dia_semana`).*

---

### 2.2 Base de Datos: `vanity_attendance`

#### Tabla: `asistencia_registros` (9 campos)

| Campo             | Tipo        | Key | Descripción    |
| ----------------- | ----------- | --- | -------------- |
| id_asistencia     | int         | PRI | Auto-increment |
| numero_empleado   | varchar(15) | MUL | Relación RH    |
| fecha             | date        |     | Día            |
| hora_entrada_real | time        |     | Entrada        |
| hora_salida_real  | time        |     | Salida         |
| minutos_retraso   | int         |     | Calculado      |
| minutos_extra     | int         |     | Excedente      |
| sucursal_registro | varchar(50) |     | Sucursal       |
| telegram_id_usado | bigint      |     | ID Telegram    |

---

### 2.3 Base de Datos: `USERS_ALMA`

#### Tabla: `users` (10 campos)

| Campo       | Tipo         | Key | Descripción            |
| ----------- | ------------ | --- | ---------------------- |
| id          | int          | PRI | ID interno             |
| username    | varchar(50)  | UNI | Usuario                |
| role        | enum         |     | admin / manager / user |
| first_name  | varchar(100) |     | Nombre                 |
| last_name   | varchar(100) |     | Apellidos              |
| email       | varchar(100) | UNI | Correo                 |
| cell_phone  | varchar(20)  |     | Teléfono               |
| telegram_id | varchar(50)  | UNI | Auth bot               |
| created_at  | timestamp    |     | Creación               |
| updated_at  | timestamp    |     | Actualización          |

---

## 3. Reglas de Negocio

### 3.1 Vacaciones

* **Antigüedad**: `FLOOR(DATEDIFF(fecha_inicio, fecha_ingreso) / 365.25)`
* **Ventana**: mínimo 12 días, máximo 45 días de anticipación
* **Validación**: no se permite solicitar periodos no cumplidos

### 3.2 Asistencia

* Identificación por `telegram_id`
* Cruce con `vanity_hr.horario_empleadas` según día
* Cálculo de retraso contra horario teórico

---

## 4. Integración Webhook (Horarios)

* **Identificación**: `body.telegram.user_id`
* **Operación**: Upsert por día
* **Persistencia**: `vanity_hr.horario_empleadas` (clave `telegram_id` + `dia_semana`)
* **Formato**: conversión de `10:00 AM` → `10:00:00`

---

## 5. Consultas Operativas

```sql
-- Saldo actual de vacaciones
SELECT * FROM vanity_hr.vista_saldos_vacaciones
WHERE numero_empleado = ?;

-- Última solicitud
SELECT * FROM vanity_hr.vacaciones
WHERE numero_empleado = ?
ORDER BY fecha_solicitud DESC
LIMIT 1;

-- Horario del día
SELECT hora_entrada_teorica
FROM vanity_hr.horario_empleadas
WHERE telegram_id = ? AND dia_semana = 'monday';
```

---

Este documento define el **contrato técnico** del sistema Vanity. Cualquier cambio estructural debe reflejarse aquí antes de pasar a producción.

---

# DB Implementation Tasks

1.  **Create initialization script:** Write a SQL script to create the databases and tables.
2.  **Modify `docker-compose.yml`:** Mount the initialization script.
3.  **Update `.env.example`:** Add new environment variables.
4.  **Implement SQLAlchemy models:** Create Python classes for each table.
5.  **Refactor database logic:** Use the new models in the application.
