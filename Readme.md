# 🤖 Vanessa Bot – Asistente de RH para Vanity

Vanessa es un bot de Telegram escrito en Python que automatiza procesos internos de Recursos Humanos en Vanity. Su objetivo es eliminar fricción operativa: onboarding, solicitudes de RH e impresión de documentos, todo orquestado desde Telegram y conectado a flujos de n8n o servicios de correo.

Este repositorio está pensado como **proyecto Python profesional**, modular y listo para correr 24/7 en producción.

---

## 🧠 ¿Qué hace Vanessa?

Vanessa no es un chatbot genérico: es una interfaz conversacional para procesos reales de negocio.

- Onboarding completo de nuevas socias (`/welcome`)
- Envío de archivos a impresión por correo electrónico (`/print`)
- Solicitud de vacaciones (`/vacaciones`)
- Solicitud de permisos por horas (`/permiso`)

Cada flujo es un módulo independiente, y los datos se envían a **webhooks de n8n** o se procesan directamente, como en el caso de la impresión.

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
└── modules/              # Habilidades del bot
    ├── __init__.py
    ├── database.py       # Módulo de conexión a la base de datos
    ├── onboarding.py     # Flujo /welcome (onboarding RH)
    ├── printer.py        # Flujo /print (impresión por email)
    └── rh_requests.py    # /vacaciones y /permiso
```

---

## 🔐 Configuración (.env)

Copia el archivo `.env.example` a `.env` y rellena los valores correspondientes. Este archivo es ignorado por Git para proteger tus credenciales.

```
# --- TELEGRAM ---
TELEGRAM_TOKEN=TU_TOKEN_AQUI

# --- WEBHOOKS N8N ---
WEBHOOK_ONBOARDING=https://...   # Alias aceptado: WEBHOOK_CONTRATO
WEBHOOK_PRINT=https://...
WEBHOOK_VACACIONES=https://...

# --- DATABASE ---
# Usado por el servicio de la base de datos en docker-compose.yml
MYSQL_DATABASE=vanessa_logs
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_ROOT_PASSWORD=rootpassword

# --- SMTP PARA IMPRESIÓN ---
# Usado por el módulo de impresión para enviar correos
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=465
SMTP_USER=tu_email@dominio.com
SMTP_PASSWORD=tu_password_de_email
SMTP_RECIPIENT=email_destino@dominio.com  # También puedes usar PRINTER_EMAIL
```

---

## 🐳 Ejecución con Docker (Recomendado)

El proyecto está dockerizado para facilitar su despliegue.

### 1. Pre-requisitos
- Docker
- Docker Compose

### 2. Levantar los servicios
Con el archivo `.env` ya configurado, simplemente ejecuta:
```bash
docker-compose up --build
```
Este comando construirá la imagen del bot, descargará la imagen de MySQL, y lanzará ambos servicios. `docker-compose` leerá las variables del archivo `.env` para configurar los contenedores.

### 3. Detener los servicios
Para detener los contenedores, presiona `Ctrl+C` en la terminal donde se están ejecutando, o ejecuta desde otro terminal:
```bash
docker-compose down
```

---

## 🧩 Arquitectura Interna

### main.py (El Cerebro)
- Inicializa el bot de Telegram
- Carga variables de entorno
- Registra los handlers de cada módulo
- Define el menú principal (`/start`, `/help`)

### modules/database.py
- Gestiona la conexión a la base de datos MySQL con SQLAlchemy.
- Define el modelo `RequestLog` para la tabla de logs.
- Provee la función `log_request` para registrar interacciones.

### modules/onboarding.py
Flujo conversacional complejo que recolecta datos de nuevas empleadas y los envía a un webhook de n8n.

### modules/printer.py
- Recibe documentos o imágenes desde Telegram.
- Descarga el archivo de forma segura desde los servidores de Telegram.
- Se conecta a un servidor SMTP para enviar el archivo como un adjunto por correo electrónico a una dirección predefinida.

### modules/rh_requests.py
- Maneja solicitudes simples de RH (Vacaciones y Permisos) y las envía a un webhook de n8n.

---

## 🧠 Filosofía del Proyecto

- **Telegram como UI**: Interfaz conversacional accesible para todos.
- **Python como cerebro**: Lógica de negocio y orquestación.
- **Docker para despliegue**: Entornos consistentes y portátiles.
- **MySQL para persistencia**: Registro auditable de todas las interacciones.
- **SMTP para acciones directas**: Integración con sistemas estándar como el correo.
- **Modularidad total**: Cada habilidad es un componente independiente.

---

## 🧪 Estado del Proyecto

✔ Funcional en producción
✔ Modular
✔ Escalable
✔ Auditable

Vanessa está viva. Y aprende con cada flujo nuevo.
