# Definición de Tablas y Campos para la Base de Datos

Este documento describe la estructura de la base de datos para el bot Vanessa, diseñada para gestionar la información de empleadas, solicitudes y permisos.

## 1. Tabla de Usuarias (`users`)

Almacena la información central y el estado de cada empleada.

| Campo             | Tipo                          | Descripción                                                        |
|-------------------|-------------------------------|--------------------------------------------------------------------|
| `id`              | `INT` (PK)                    | Identificador único de la usuaria.                                 |
| `employee_number` | `VARCHAR(50)` (Unique)        | Número de empleada único (e.g., "GAMM20260201").                    |
| `telegram_id`     | `BIGINT` (Unique)             | ID de Telegram de la usuaria.                                      |
| `telegram_username`| `VARCHAR(255)`               | Nombre de usuario de Telegram.                                     |
| `full_name`       | `VARCHAR(255)`                | Nombre completo.                                                   |
| `preferred_name`  | `VARCHAR(100)`                | Nombre con el que prefiere que la llamen.                          |
| `email`           | `VARCHAR(255)` (Unique)       | Correo electrónico.                                                |
| `phone_number`    | `VARCHAR(20)`                 | Teléfono celular.                                                  |
| `position`        | `VARCHAR(100)`                | Puesto que desempeña (e.g., "manager").                            |
| `branch`          | `VARCHAR(100)`                | Sucursal a la que pertenece (e.g., "plaza_cima").                  |
| `hire_date`       | `DATE`                        | Fecha de ingreso a la empresa.                                     |
| `status`          | `ENUM('activo', 'inactivo')`  | Estatus actual de la empleada.                                     |
| `role`            | `ENUM('user', 'manager', 'admin')` | Nivel de permisos en el sistema (por defecto: 'user').             |
| `created_at`      | `DATETIME`                    | Fecha de creación del registro.                                    |
| `updated_at`      | `DATETIME`                    | Fecha de última actualización.                                     |

## 2. Tabla de Datos de Onboarding (`onboarding_data`)

Almacena la información detallada recopilada durante el flujo `/welcome`. Se vincula 1-a-1 con la tabla `users`.

| Campo                         | Tipo           | Descripción                                                              |
|-------------------------------|----------------|--------------------------------------------------------------------------|
| `id`                          | `INT` (PK)     | Identificador único.                                                     |
| `user_id`                     | `INT` (FK)     | Referencia a `users.id`.                                                 |
| `date_of_birth`               | `DATE`         | Fecha de nacimiento.                                                     |
| `place_of_birth`              | `VARCHAR(255)` | Lugar de nacimiento.                                                     |
| `rfc`                         | `VARCHAR(13)`  | RFC.                                                                     |
| `curp`                        | `VARCHAR(18)`  | CURP.                                                                    |
| `nss`                         | `VARCHAR(11)`  | Número de Seguridad Social.                                              |
| `address_street`              | `VARCHAR(255)` | Calle del domicilio.                                                     |
| `address_ext_number`          | `VARCHAR(20)`  | Número exterior.                                                         |
| `address_int_number`          | `VARCHAR(20)`  | Número interior (si aplica).                                             |
| `address_neighborhood`        | `VARCHAR(255)` | Colonia.                                                                 |
| `address_zip_code`            | `VARCHAR(10)`  | Código Postal.                                                           |
| `address_city`                | `VARCHAR(255)` | Ciudad.                                                                  |
| `address_state`               | `VARCHAR(255)` | Estado.                                                                  |
| `emergency_contact_name`      | `VARCHAR(255)` | Nombre del contacto de emergencia.                                       |
| `emergency_contact_phone`     | `VARCHAR(20)`  | Teléfono del contacto de emergencia.                                     |
| `emergency_contact_relationship` | `VARCHAR(50)`| Parentesco del contacto de emergencia.                                   |
| `registration_source`         | `VARCHAR(50)`  | Origen del registro (e.g., "telegram_bot").                              |
| `bot_version`                 | `VARCHAR(50)`  | Versión del bot que procesó el alta.                                     |
| `registration_time_minutes`   | `INT`          | Tiempo que tardó el registro en minutos.                                 |
| `bot_interactions`            | `INT`          | Número de interacciones con el bot durante el alta.                      |
| `created_at`                  | `DATETIME`     | Fecha de creación.                                                       |

## 3. Tabla de Vacaciones (`vacations`)

Mantiene un registro de las solicitudes de vacaciones de las empleadas.

| Campo         | Tipo                                | Descripción                                                        |
|---------------|-------------------------------------|--------------------------------------------------------------------|
| `id`          | `INT` (PK)                          | Identificador único de la solicitud.                               |
| `user_id`     | `INT` (FK)                          | Empleada que solicita (`users.id`).                                |
| `start_date`  | `DATE`                              | Fecha de inicio de las vacaciones.                                 |
| `end_date`    | `DATE`                              | Fecha de fin de las vacaciones.                                    |
| `status`      | `ENUM('pending', 'approved', 'rejected')` | Estado de la solicitud.                                            |
| `approver_id` | `INT` (FK, nullable)                | Manager o admin que aprobó/rechazó la solicitud (`users.id`).      |
| `comments`    | `TEXT`                              | Comentarios del solicitante o del aprobador.                       |
| `created_at`  | `DATETIME`                          | Fecha de creación de la solicitud.                                 |
| `updated_at`  | `DATETIME`                          | Fecha de última actualización (aprobación/rechazo).                |

## 4. Tabla de Permisos por Horas (`permission_requests`)

Registro de solicitudes de permisos por horas (llegar tarde, salir temprano, etc.).

| Campo         | Tipo                                | Descripción                                                        |
|---------------|-------------------------------------|--------------------------------------------------------------------|
| `id`          | `INT` (PK)                          | Identificador único del permiso.                                   |
| `user_id`     | `INT` (FK)                          | Empleada que solicita (`users.id`).                                |
| `request_date`| `DATE`                              | Fecha para la cual se solicita el permiso.                         |
| `start_time`  | `TIME`                              | Hora de inicio del permiso.                                        |
| `end_time`    | `TIME`                              | Hora de fin del permiso.                                           |
| `reason`      | `TEXT`                              | Motivo de la solicitud.                                            |
| `status`      | `ENUM('pending', 'approved', 'rejected')` | Estado del permiso.                                                |
| `approver_id` | `INT` (FK, nullable)                | Manager o admin que gestionó el permiso (`users.id`).              |
| `created_at`  | `DATETIME`                          | Fecha de creación de la solicitud.                                 |
| `updated_at`  | `DATETIME`                          | Fecha de la gestión.                                               |

## 5. Interacción con la Base de Datos y Sistema de Roles

El bot utiliza un sistema de roles para gestionar el acceso a los datos y funcionalidades.

### a. Roles de Usuario

- **`user`**: Es el rol por defecto. Puede registrarse (`/welcome`), solicitar vacaciones (`/vacaciones`), pedir permisos (`/permiso`) y recibir notificaciones sobre el estado de sus solicitudes.
- **`manager`**: Tiene los mismos permisos que un `user`, pero además puede consultar la información de otras usuarias a través del flujo `/data_socias`. También puede aprobar o rechazar solicitudes de vacaciones y permisos de las usuarias a su cargo.
- **`admin`**: Tiene acceso completo a toda la información y funcionalidades. Puede gestionar usuarios, aprobar cualquier solicitud y acceder a todos los datos.

### b. Flujo de Solicitudes (Vacaciones y Permisos)

1.  **Creación**: Una usuaria (`user`) inicia el flujo (`/vacaciones` o `/permiso`). El bot crea un nuevo registro en la tabla correspondiente (`vacations` o `permission_requests`) con el estado `'pending'`.
2.  **Notificación**: Se notifica a los `managers` y `admins` sobre la nueva solicitud.
3.  **Gestión**: Un `manager` o `admin` revisa la solicitud.
4.  **Actualización**: El `manager`/`admin` aprueba o rechaza la solicitud. El bot actualiza el registro correspondiente, cambiando el `status` a `'approved'` o `'rejected'`, y guardando el `approver_id`.
5.  **Notificación Final**: Se notifica a la usuaria solicitante sobre la resolución de su petición.

### c. Acceso a Datos (`/data_socias`)

- Cuando un `manager` o `admin` utiliza el comando `/data_socias`, el bot consulta la tabla `users` y `onboarding_data` para devolver la información de las empleadas.
- Un `manager` solo podrá ver la información de las usuarias que reportan a él/ella (lógica de negocio a implementar), mientras que un `admin` podrá ver la de todas.
