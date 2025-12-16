# Definición de Tablas y Campos para la Base de Datos

Este documento describe la estructura de la base de datos necesaria para el bot Vanessa, incluyendo tablas para usuarios, permisos y el flujo de bienvenida.

## 1. Tabla de Usuarios (`users`)

Esta tabla almacena la información básica de cada usuario que interactúa con el bot.

| Campo        | Tipo          | Descripción                                      |
|--------------|---------------|--------------------------------------------------|
| `id`         | `INT` (PK)    | Identificador único del usuario.                 |
| `telegram_id`| `BIGINT`      | ID de Telegram del usuario.                      |
| `username`   | `VARCHAR(255)`| Nombre de usuario de Telegram.                   |
| `first_name` | `VARCHAR(255)`| Nombre del usuario.                              |
| `last_name`  | `VARCHAR(255)`| Apellido del usuario.                            |
| `is_active`  | `BOOLEAN`     | Indica si el usuario está activo (default `true`).|
| `created_at` | `DATETIME`    | Fecha y hora de creación del registro.           |
| `updated_at` | `DATETIME`    | Fecha y hora de la última actualización.         |

## 2. Tabla de Permisos (`permissions`)

Esta tabla gestiona los permisos de los usuarios para realizar acciones específicas.

| Campo                 | Tipo       | Descripción                                                              |
|-----------------------|------------|--------------------------------------------------------------------------|
| `id`                  | `INT` (PK) | Identificador único del permiso.                                         |
| `user_id`             | `INT` (FK) | Referencia al `id` del usuario en la tabla `users`.                      |
| `can_update_records`  | `BOOLEAN`  | Permite al usuario actualizar registros (default `false`).               |
| `can_access_reports`  | `BOOLEAN`  | Permite al usuario acceder a reportes (default `false`).                 |
| `created_at`          | `DATETIME` | Fecha y hora de creación del registro.                                   |
| `updated_at`          | `DATETIME` | Fecha y hora de la última actualización.                                 |

## 3. Tabla de Datos del Flujo de Bienvenida (`welcome_flow_data`)

Esta tabla almacena los datos recopilados durante el flujo de `/welcome`.

| Campo           | Tipo          | Descripción                                             |
|-----------------|---------------|---------------------------------------------------------|
| `id`            | `INT` (PK)    | Identificador único del registro.                       |
| `user_id`       | `INT` (FK)    | Referencia al `id` del usuario en la tabla `users`.     |
| `full_name`     | `VARCHAR(255)`| Nombre completo del usuario.                            |
| `curp`          | `VARCHAR(18)` | CURP del usuario.                                       |
| `rfc`           | `VARCHAR(13)` | RFC del usuario.                                        |
| `nss`           | `VARCHAR(11)` | Número de Seguridad Social (NSS) del usuario.           |
| `address`       | `TEXT`        | Dirección del usuario.                                  |
| `bank_account`  | `VARCHAR(20)` | Número de cuenta bancaria del usuario.                  |
| `phone_number`  | `VARCHAR(15)` | Número de teléfono del usuario.                         |
| `status`        | `VARCHAR(50)` | Estado del flujo (e.g., 'in_progress', 'completed').    |
| `created_at`    | `DATETIME`    | Fecha y hora de creación del registro.                  |
| `updated_at`    | `DATETIME`    | Fecha y hora de la última actualización.                |

## 4. Interacción con la Base de Datos

A continuación, se describe cómo el bot interactúa con estas tablas.

### a. Gestión de Usuarios

- **Creación de Usuario**: Cuando un nuevo usuario interactúa con el bot por primera vez (e.g., al usar `/start`), se crea un nuevo registro en la tabla `users` con su `telegram_id`, `username`, `first_name` y `last_name`.
- **Actualización de Usuario**: La información del usuario se puede actualizar si cambia su nombre de usuario, nombre o apellido en Telegram.
- **Estado del Usuario**: El campo `is_active` se utiliza para desactivar a un usuario si deja la empresa, sin eliminar sus registros.

### b. Flujo de `/welcome`

- **Inicio del Flujo**: Cuando un usuario inicia el flujo de `/welcome`, se crea un registro en la tabla `welcome_flow_data` con el `user_id` correspondiente y un estado de `in_progress`.
- **Recopilación de Datos**: A medida que el usuario proporciona su información (nombre, CURP, RFC, etc.), los campos correspondientes en la tabla `welcome_flow_data` se actualizan.
- **Finalización del Flujo**: Una vez que el usuario ha proporcionado toda la información, el estado en `welcome_flow_data` se actualiza a `completed`.

### c. Gestión de Permisos

- **Asignación de Permisos**: Los permisos se asignan a los usuarios a través de la tabla `permissions`. Por defecto, los usuarios no tienen permisos para actualizar registros o acceder a reportes.
- **Verificación de Permisos**: Antes de ejecutar comandos que requieran permisos especiales (e.g., un comando para actualizar la información de otro usuario), el bot consulta la tabla `permissions` para verificar si el usuario tiene los permisos necesarios.
- **Actualización de Registros**: Si un usuario tiene el permiso `can_update_records` establecido en `true`, podrá modificar la información en la tabla `welcome_flow_data` de otros usuarios.
