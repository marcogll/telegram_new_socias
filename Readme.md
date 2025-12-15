# 🤖 Vanessa Bot – Asistente de RH para Vanity

Vanessa es un bot de Telegram escrito en Python que automatiza procesos internos de Recursos Humanos en Vanity. Su objetivo es eliminar fricción operativa: onboarding y solicitudes de RH, todo orquestado desde Telegram y conectado a flujos de n8n o servicios de correo.

Este repositorio está pensado como **proyecto Python profesional**, modular y listo para correr 24/7 en producción.

---

## 🧠 ¿Qué hace Vanessa?

Vanessa no es un chatbot genérico: es una interfaz conversacional para procesos reales de negocio.

- Onboarding completo de nuevas socias (`/welcome`)
- Solicitud de vacaciones (`/vacaciones`)
- Solicitud de permisos por horas (`/permiso`)

Cada flujo es un módulo independiente, y los datos se envían a **webhooks de n8n**.

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
WEBHOOK_VACACIONES=https://...
WEBHOOK_PERMISOS=https://...

# --- DATABASE ---
# Usado por el servicio de la base de datos en docker-compose.yml
MYSQL_DATABASE=vanessa_logs
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_ROOT_PASSWORD=rootpassword

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

### 4. Despliegue con imagen pre-construida (Collify)
Si Collify solo consume imágenes ya publicadas, usa el archivo `docker-compose.collify.yml` que apunta a una imagen en registro (`DOCKER_IMAGE`).

1) Construir y publicar la imagen (ejemplo con Buildx y tag con timestamp):
```bash
export DOCKER_IMAGE=marcogll/vanessa-bot:prod-$(date +%Y%m%d%H%M)
docker buildx build --platform linux/amd64 -t $DOCKER_IMAGE . --push
```

2) Desplegar en el servidor (Collify) usando la imagen publicada:
```bash
export DOCKER_IMAGE=marcogll/vanessa-bot:prod-20240101
docker compose -f docker-compose.collify.yml pull
docker compose -f docker-compose.collify.yml up -d
```
`docker-compose.collify.yml` usa `env_file: .env`, así que carga las credenciales igual que en local o configúralas como variables de entorno en la plataforma.

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
Incluye derivadas útiles: `num_ext_texto` (número en letras, con interior) y `numero_empleado` (primeras 4 del CURP + fecha de ingreso).

### modules/rh_requests.py
- Maneja solicitudes simples de RH (Vacaciones y Permisos) y las envía a un webhook de n8n.
- Vacaciones: pregunta año (actual o siguiente), día/mes de inicio y fin, calcula métricas y aplica semáforo automático.
- Permisos: ofrece accesos rápidos (hoy/mañana/pasado) o fecha específica (año actual/siguiente, día/mes), pide horario, clasifica motivo con IA y envía al webhook.

---

## 🧠 Filosofía del Proyecto

- **Telegram como UI**: Interfaz conversacional accesible para todos.
- **Python como cerebro**: Lógica de negocio y orquestación.
- **Docker para despliegue**: Entornos consistentes y portátiles.
- **MySQL para persistencia**: Registro auditable de todas las interacciones.
- **Modularidad total**: Cada habilidad es un componente independiente.

---

## 🧪 Estado del Proyecto

✔ Funcional en producción
✔ Modular
✔ Escalable
✔ Auditable

Vanessa está viva. Y aprende con cada flujo nuevo.
