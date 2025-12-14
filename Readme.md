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
├── README.md             # Este documento
│
└── modules/              # Habilidades del bot
    ├── __init__.py
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
```

Nunca subas este archivo al repositorio.

---

## 📦 Instalación

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

---

## 🧩 Arquitectura Interna

### main.py (El Cerebro)

- Inicializa el bot de Telegram
- Carga variables de entorno
- Registra los handlers de cada módulo
- Define el menú principal (/start, /help)

Nada de lógica de negocio vive aquí. Solo coordinación.

---

### modules/onboarding.py

Flujo conversacional complejo basado en `ConversationHandler`.

- Recolecta información personal, laboral y de emergencia
- Normaliza datos (RFC, CURP, fechas)
- Usa teclados guiados para reducir errores
- Envía un payload estructurado a n8n

El diseño es **estado → pregunta → respuesta → siguiente estado**.

---

### modules/printer.py

- Recibe documentos o imágenes desde Telegram
- Obtiene el enlace temporal de Telegram
- Envía el archivo a una cola de impresión vía webhook

Telegram se usa como interfaz, n8n como backend operativo.

---

### modules/rh_requests.py

- Maneja solicitudes simples de RH
- Vacaciones
- Permisos por horas

El bot solo valida y recopila; la lógica de aprobación vive fuera.

---

## ⚙️ Ejecución Automática con systemd (Linux)

Ejemplo de servicio:

```
[Unit]
Description=Vanessa Bot
After=network.target

[Service]
User=vanity
WorkingDirectory=/opt/vanity_bot
EnvironmentFile=/opt/vanity_bot/.env
ExecStart=/opt/vanity_bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Luego:

```
sudo systemctl daemon-reload
sudo systemctl enable vanessa
sudo systemctl start vanessa
```

---

## 🧠 Filosofía del Proyecto

- Telegram como UI
- Python como cerebro
- n8n como sistema nervioso
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
