# 🤖 Vanessa Bot – Asistente de RH para Vanity

Vanessa es un bot de Telegram escrito en Python que automatiza procesos internos de Recursos Humanos en Vanity. Su objetivo es eliminar fricción operativa: onboarding, solicitudes de RH e impresión de documentos, todo orquestado desde Telegram y conectado a flujos de n8n.

Este repositorio está pensado como **proyecto Python profesional**, modular y listo para correr 24/7 en producción.

---

## 🧠 ¿Qué hace Vanessa?

Vanessa no es un chatbot genérico: es una interfaz conversacional para procesos reales de negocio.

- Onboarding completo de nuevas socias (/welcome)
- Envío de archivos a impresión (/print)
- Solicitud de vacaciones (/vacaciones)
- Solicitud de permisos por horas (/permiso)

Cada flujo es un módulo independiente y todos los datos se envían a **webhooks de n8n** para su procesamiento posterior.

---

## 📂 Estructura del Proyecto

```
vanity_bot/
│
├── .env                  # Variables sensibles (tokens, URLs)
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
    ├── printer.py        # Flujo /print (impresión)
    └── rh_requests.py    # /vacaciones y /permiso
```

---

## 🔐 Configuración (.env)

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
# --- TELEGRAM ---
TELEGRAM_TOKEN=TU_TOKEN_AQUI

# --- WEBHOOKS N8N ---
WEBHOOK_ONBOARDING=https://flows.soul23.cloud/webhook/contrato
WEBHOOK_PRINT=https://flows.soul23.cloud/webhook/impresion
WEBHOOK_VACACIONES=https://flows.soul23.cloud/webhook/vacaciones

# --- DATABASE ---
# Esta URL es para la conexión interna de Docker, no la modifiques si usas Docker Compose.
DATABASE_URL=mysql+mysqlconnector://user:password@db:3306/vanessa_logs
```

Nunca subas este archivo al repositorio.

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
Este comando construirá la imagen del bot, descargará la imagen de MySQL, creará los volúmenes y redes, y lanzará ambos servicios. El bot se conectará automáticamente a la base de datos para registrar los logs.

### 3. Detener los servicios
Para detener los contenedores, presiona `Ctrl+C` en la terminal donde se están ejecutando, o ejecuta desde otro terminal:
```bash
docker-compose down
```

---

## 📦 Instalación Manual

Se recomienda usar un entorno virtual.

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ▶️ Ejecución Manual

```
python main.py
```

Si el token es válido, verás:

```
🧠 Vanessa Brain iniciada y escuchando...
```
**Nota**: Para que la ejecución manual funcione, necesitarás tener una base de datos MySQL corriendo localmente y accesible en la URL especificada en `DATABASE_URL` dentro de tu archivo `.env`.

---

## 🧩 Arquitectura Interna

### main.py (El Cerebro)
- Inicializa el bot de Telegram
- Carga variables de entorno
- Registra los handlers de cada módulo
- Define el menú principal (/start, /help)

### modules/database.py
- Gestiona la conexión a la base de datos MySQL con SQLAlchemy.
- Define el modelo `RequestLog` para la tabla de logs.
- Provee la función `log_request` para registrar interacciones.

### modules/onboarding.py
Flujo conversacional complejo basado en `ConversationHandler`.
- Recolecta información personal, laboral y de emergencia
- Normaliza datos (RFC, CURP, fechas)
- Usa teclados guiados para reducir errores
- Envía un payload estructurado a n8n

### modules/printer.py
- Recibe documentos o imágenes desde Telegram
- Obtiene el enlace temporal de Telegram
- Envía el archivo a una cola de impresión vía webhook

### modules/rh_requests.py
- Maneja solicitudes simples de RH: Vacaciones y Permisos por horas.

---

## 🧠 Filosofía del Proyecto

- Telegram como UI
- Python como cerebro
- n8n como sistema nervioso
- Docker para despliegue
- MySQL para persistencia de logs
- Datos estructurados, no mensajes sueltos
- Modularidad total: cada habilidad se enchufa o se quita

Vanessa no reemplaza RH: elimina fricción humana innecesaria.

---

## 🚀 Extensiones Futuras

- Firma digital de contratos
- Finder de documentos
- Reportes automáticos
- Roles y permisos
- Modo administrador

---

## 🧪 Estado del Proyecto

✔ Funcional en producción
✔ Modular
✔ Escalable
✔ Auditable

Vanessa está viva. Y aprende con cada flujo nuevo.
