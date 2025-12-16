# Definición de Tablas y Campos para la Base de Datos

Este documento describe la estructura de la base de datos para el bot Vanessa, diseñada para gestionar la información de empleadas, solicitudes y permisos de forma detallada.

## 1. Tabla de Usuarias (`users`)

Almacena la información central, el estado y el balance de vacaciones de cada empleada.

| Campo                    | Tipo                          | Descripción                                                              |
|--------------------------|-------------------------------|--------------------------------------------------------------------------|
| `id`                     | `INT` (PK)                    | Identificador único de la usuaria.                                       |
| `employee_number`        | `VARCHAR(50)` (Unique)        | Número de empleada único.                                                |
| `telegram_id`            | `BIGINT` (Unique)             | ID de Telegram de la usuaria.                                            |
| `telegram_username`      | `VARCHAR(255)`                | Nombre de usuario de Telegram.                                           |
| `full_name`              | `VARCHAR(255)`                | Nombre completo.                                                         |
| `preferred_name`         | `VARCHAR(100)`                | Nombre preferido de la empleada.                                         |
| `email`                  | `VARCHAR(255)` (Unique)       | Correo electrónico.                                                      |
| `phone_number`           | `VARCHAR(20)`                 | Teléfono celular.                                                        |
| `position`               | `VARCHAR(100)`                | Puesto que desempeña.                                                    |
| `branch`                 | `VARCHAR(100)`                | Sucursal a la que pertenece.                                             |
| `hire_date`              | `DATE`                        | Fecha de ingreso a la empresa.                                           |
| `status`                 | `ENUM('activo', 'inactivo')`  | Estatus actual de la empleada.                                           |
| `role`                   | `ENUM('user', 'manager', 'admin')` | Nivel de permisos en el sistema (por defecto: 'user').                   |
| `vacation_days_assigned` | `INT`                         | Días de vacaciones asignados para el periodo actual.                     |
| `vacation_days_taken`    | `INT` (Default: 0)            | Suma de días de vacaciones aprobados y tomados.                          |
| `created_at`             | `DATETIME`                    | Fecha de creación del registro.                                          |
| `updated_at`             | `DATETIME`                    | Fecha de última actualización.                                           |

## 2. Tabla de Solicitudes de Vacaciones (`vacations`)

Registro detallado de las solicitudes de vacaciones.

| Campo               | Tipo                               | Descripción                                                              |
|---------------------|------------------------------------|--------------------------------------------------------------------------|
| `id`                | `INT` (PK)                         | Identificador numérico de la solicitud.                                  |
| `request_id`        | `VARCHAR(50)` (Unique)             | Identificador alfanumérico único de la solicitud (e.g., "7c32a085...").  |
| `user_id`           | `INT` (FK)                         | Empleada que solicita (`users.id`).                                      |
| `status`            | `ENUM('pendiente', 'aprobado', 'rechazado')` | Estado actual de la solicitud.                                           |
| `start_date`        | `DATE`                             | Fecha de inicio de las vacaciones.                                       |
| `end_date`          | `DATE`                             | Fecha de fin de las vacaciones.                                          |
| `requested_days`    | `INT`                              | Número de días naturales solicitados.                                    |
| `business_days`     | `INT`                              | Número de días hábiles que abarca la solicitud.                          |
| `reason`            | `TEXT`                             | Motivo de la solicitud.                                                  |
| `with_pay`          | `BOOLEAN`                          | `TRUE` si es con goce de sueldo.                                         |
| `leave_type`        | `ENUM('con_goce', 'sin_goce')`     | Clasificación del tipo de permiso.                                       |
| `request_date`      | `DATETIME`                         | Fecha y hora en que se creó la solicitud.                                |
| `processed_date`    | `DATETIME`                         | Fecha y hora en que se procesó en el sistema (e.g., envío a webhook).    |
| `source`            | `VARCHAR(50)`                      | Origen de la solicitud (e.g., "telegram_bot").                           |
| `approver_id`       | `INT` (FK, nullable)               | Usuario (`users.id`) que aprobó o rechazó.                               |
| `approval_date`     | `DATETIME` (nullable)              | Fecha y hora de la aprobación o rechazo.                                 |
| `approver_comments` | `TEXT` (nullable)                  | Comentarios del aprobador.                                               |
| `affects_payroll`   | `BOOLEAN`                          | `TRUE` si la solicitud tiene implicaciones en la nómina.                 |

## 3. Tabla de Solicitudes de Permisos por Horas (`permission_requests`)

Registro detallado de permisos especiales por horas.

| Campo               | Tipo                               | Descripción                                                              |
|---------------------|------------------------------------|--------------------------------------------------------------------------|
| `id`                | `INT` (PK)                         | Identificador numérico del permiso.                                      |
| `request_id`        | `VARCHAR(50)` (Unique)             | Identificador alfanumérico único (e.g., "1LSRADeDNfY").                  |
| `user_id`           | `INT` (FK)                         | Empleada que solicita (`users.id`).                                      |
| `category`          | `VARCHAR(100)`                     | Categoría del permiso (e.g., "PERSONAL", "MÉDICO").                      |
| `status`            | `ENUM('pendiente', 'aprobado', 'rechazado')` | Estado actual del permiso.                                               |
| `permission_date`   | `DATE`                             | Fecha para la cual se solicita el permiso.                               |
| `start_time`        | `TIME`                             | Hora de inicio del permiso.                                              |
| `end_time`          | `TIME`                             | Hora de fin del permiso.                                                 |
| `reason`            | `TEXT`                             | Motivo detallado del permiso.                                            |
| `with_pay`          | `BOOLEAN`                          | `TRUE` si es con goce de sueldo.                                         |
| `leave_type`        | `ENUM('con_goce', 'sin_goce')`     | Clasificación del tipo de permiso.                                       |
| `request_date`      | `DATETIME`                         | Fecha y hora en que se creó la solicitud.                                |
| `processed_date`    | `DATETIME`                         | Fecha y hora en que se procesó.                                          |
| `source`            | `VARCHAR(50)`                      | Origen de la solicitud.                                                  |
| `approver_id`       | `INT` (FK, nullable)               | Usuario (`users.id`) que gestionó el permiso.                            |
| `approval_date`     | `DATETIME` (nullable)              | Fecha y hora de la gestión.                                              |
| `approver_comments` | `TEXT` (nullable)                  | Comentarios del aprobador.                                               |
| `affects_payroll`   | `BOOLEAN`                          | `TRUE` si el permiso tiene implicaciones en la nómina.                   |

## 4. Interacción con la Base de Datos y Lógica de Negocio

### a. Sistema de Roles

- **`user`**: Rol estándar para todas las empleadas. Pueden solicitar vacaciones y permisos, y consultar su propio estado.
- **`manager`**: Puede realizar las mismas acciones que un `user`, y adicionalmente, aprobar/rechazar solicitudes y consultar datos de las usuarias a su cargo.
- **`admin`**: Acceso total. Puede gestionar todos los datos de todas las usuarias y solicitudes.

### b. Flujo de Solicitudes (Vacaciones y Permisos)

1.  **Creación**: Una usuaria crea una solicitud. El sistema la inserta en la tabla `vacations` o `permission_requests` con estado `'pendiente'`.
2.  **Aprobación**: Un `manager` o `admin` revisa la solicitud. Al aprobarla:
    *   El `status` de la solicitud cambia a `'aprobado'`.
    *   Se registran el `approver_id`, `approval_date` y `approver_comments`.
3.  **Actualización de Balance de Vacaciones**:
    *   **Si la solicitud es de vacaciones y fue aprobada**: El sistema debe sumar los `business_days` de la solicitud al campo `vacation_days_taken` de la usuaria en la tabla `users`.
    *   Esta lógica asegura que el balance de días tomados siempre esté sincronizado con los registros aprobados.

### c. Lógica de Negocio Clave

- **Balance de Vacaciones**: El balance de días disponibles de una empleada se calcula en tiempo real como `vacation_days_assigned` - `vacation_days_taken`.
- **Nómina**: El campo `affects_payroll` sirve como una bandera para que los sistemas externos de RRHH sepan que una solicitud específica (e.g., un permiso sin goce de sueldo) requiere un ajuste en la nómina.
- **Auditoría**: Todas las fechas (`request_date`, `approval_date`) y IDs (`user_id`, `approver_id`) permiten una auditoría completa de cada solicitud.
