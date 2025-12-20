# 🤖 Vanessa Bot – Asistente de RH para Vanity

Vanessa es un bot de Telegram escrito en Python que automatiza procesos internos de Recursos Humanos en Vanity. Su objetivo es eliminar fricción operativa: onboarding y solicitudes de RH, todo orquestado desde Telegram y conectado a flujos de n8n, servicios de correo y bases de datos MySQL.

Este repositorio está pensado como **proyecto Python profesional**, modular y listo para correr 24/7 en producción.

---

## 🧠 ¿Qué hace Vanessa?

Vanessa no es un chatbot genérico: es una interfaz conversacional para procesos reales de negocio.

- **Onboarding completo de nuevas socias (`/welcome`)**: Recolecta datos, valida que no existan duplicados en la DB, y ejecuta un registro en dos fases:
  1.  **Crea un usuario de acceso** en la tabla `USERS_ALMA.users` para la autenticación del bot.
  2.  **Crea un perfil de empleada** completo en la tabla `vanity_hr.data_empleadas`, que es la tabla maestra de RRHH.
- **Solicitud de vacaciones (`/vacaciones`)**: Flujo dinámico para gestionar días de descanso.
- **Solicitud de permisos por horas (`/permiso`)**: Incluye clasificación de motivos mediante IA (Gemini).

Cada flujo es un módulo independiente que interactúa con la base de datos y flujos de **n8n**.

---

## 📂 Estructura del Proyecto

```
vanity_bot/
│
├── .env                  # Variables sensibles (tokens, URLs, credenciales)
├── .env.example          # Archivo de ejemplo para variables de entorno
├── main.py               # Cerebro principal del bot
├── requirements.txt      # Dependencias
├── Dockerfile            # Definición del contenedor del bot
├── docker-compose.yml    # Orquestación de servicios (bot + db)
├── README.md             # Este documento
│
├── models/               # Modelos de base de datos (SQLAlchemy)
│   ├── users_alma_models.py
│   ├── vanity_hr_models.py
│   └── vanity_attendance_models.py
│
└── modules/              # Habilidades del bot
    ├── ai.py             # Clasificación de motivos con Gemini
    ├── database.py       # Conexión a DB y lógica de negocio (registro/verificación)
    ├── logger.py         # Registro de auditoría
    ├── onboarding.py     # Flujo /welcome
    ├── rh_requests.py    # /vacaciones y /permiso
    └── ui.py             # Teclados y componentes de interfaz
```

---

## 🔐 Configuración (.env)

Vanessa utiliza múltiples bases de datos y webhooks. Asegúrate de configurar correctamente los nombres de las bases de datos.

```ini
# --- TELEGRAM ---
TELEGRAM_TOKEN=TU_TOKEN_AQUI

# --- AI (Gemini) ---
GOOGLE_API_KEY=AIzaSy...

# --- WEBHOOKS N8N ---
WEBHOOK_ONBOARDING=https://...
WEBHOOK_VACACIONES=https://...
WEBHOOK_PERMISOS=https://...

# --- DATABASE SETUP ---
MYSQL_HOST=db
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_ROOT_PASSWORD=rootpassword

# Nombres de las Bases de Datos
MYSQL_DATABASE_USERS_ALMA=USERS_ALMA
MYSQL_DATABASE_VANITY_HR=vanity_hr
MYSQL_DATABASE_VANITY_ATTENDANCE=vanity_attendance
```

---

## 🐳 Ejecución con Docker (Recomendado)

El proyecto está dockerizado para facilitar su despliegue y aislamiento.

### 1. Pre-requisitos
- Docker y Docker Compose instalaros.

### 2. Levantar los servicios
```bash
docker-compose up --build -d
```
Este comando levantará el bot y un contenedor de MySQL (si se usa el compose por defecto). El bot se reconectará automáticamente a la DB si esta tarda en iniciar.

---

## 🧩 Arquitectura Interna

### main.py (El Cerebro)
- Inicializa el bot de Telegram y carga variables de entorno.
- Registra los handlers de cada módulo y define el menú principal y comandos persistentes.

### modules/database.py
- Centraliza la conexión a las 3 bases de datos (`USERS_ALMA`, `vanity_hr`, `vanity_attendance`).
- **Verificación de duplicados**: Verifica el `telegram_id` en `USERS_ALMA.users` para evitar registros duplicados.
- **Registro de usuarias**: La función `register_user` implementa un registro en dos pasos:
  1.  Crea o actualiza el registro en `USERS_ALMA.users` para control de acceso.
  2.  Crea o actualiza el perfil completo de la empleada en `vanity_hr.data_empleadas`.

### modules/onboarding.py
Recolección exhaustiva de datos. Al finalizar:
1. Valida y formatea datos (RFC, CURP, fechas).
2. Registra a la empleada en la base de datos MySQL.
3. Envía el payload completo al webhook de n8n para generación de contratos.

### modules/ai.py & modules/rh_requests.py
Integración con **Google Gemini** para clasificar automáticamente los motivos de los permisos (Médico, Trámite, etc.) y envío sincronizado a webhooks de gestión humana.

---

## 🗒️ Registro de versiones

- **1.3 (2025-12-18)** — **Adiós Google Sheets**: Migración total a base de datos MySQL para verificación de existencia y registro de nuevas socias. Limpieza de `.env` y optimización de arquitectura de modelos.
- **1.2 (2025-01-25)** — Onboarding: selector de año 2020–2026; `numero_empleado` dinámico; mejoras en flujos de vacaciones/permiso.
- **1.1** — Implementación inicial de webhooks y Docker.
