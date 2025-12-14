# 👩‍💼 Vanessa Bot Brain

### Vanity / Soul — HR Automation

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![AI](https://img.shields.io/badge/AI-OpenAI%20%7C%20Gemini-green)
![n8n](https://img.shields.io/badge/Integration-n8n-red)

**Vanessa** es la Asistente Virtual de Recursos Humanos para **Vanity / Soul**. No es solo un bot de comandos: es un **cerebro central modular** diseñado para gestionar el ciclo de vida de las socias —contratación, solicitudes internas y servicios— con una personalidad cálida, eficiente y humana.

---

## 🧠 Filosofía del Diseño

Vanessa fue construida bajo tres principios:

1. **Conversaciones humanas, datos estrictos**
   La UX es natural; la salida siempre es un **payload JSON inmutable**.

2. **Estado efímero, persistencia externa**
   El bot no guarda información sensible. Todo se envía a **n8n + Base de Datos**.

3. **Modularidad real**
   Cada habilidad vive en su propio archivo y puede evolucionar sin romper el sistema.

---

## 🏗️ Arquitectura del Sistema

Arquitectura **modular y desacoplada**:

* **Cerebro (`main.py`)**
  Orquesta Telegram, gestiona sesiones y enruta comandos.

* **Habilidades (`/modules`)**
  Cada módulo implementa un flujo conversacional completo.

* **Inteligencia Artificial**
  OpenAI o Gemini para clasificación semántica y entendimiento de texto libre.

* **Persistencia (n8n + DB)**
  Recepción de eventos mediante Webhooks con UUID y timestamp.

---

## 📂 Estructura del Proyecto

```text
/vanity_bot_brain
│
├── .env                  # Credenciales y Webhooks
├── main.py               # Cerebro / Orquestador
├── requirements.txt      # Dependencias
├── README.md             # Documentación
│
└── modules/              # HABILIDADES
    ├── __init__.py
    ├── onboarding.py     # /welcome — Contrato (35 pasos)
    ├── rh_requests.py    # /vacaciones y /permiso (IA)
    └── printer.py        # /print — Envío de archivos
```

---

## 💬 Módulos y Flujos Conversacionales

### 1️⃣ Onboarding — `/welcome`

**Objetivo**
Recopilar la información completa para el contrato de nuevas socias.

**Características clave**

* Flujo guiado de **35 pasos**
* Normalización de RFC y CURP
* Validación de fechas
* Teclados dinámicos
* Referencias personales en bucle

**Ejemplo de conversación**

```
User: /welcome
Vanessa: ¡Hola Ana! 👋 Soy Vanessa de RH. Vamos a dejar listo tu registro.
Vanessa: ¿Cómo te gusta que te llamemos?
User: Anita
Vanessa: Perfecto ✨ ¿Cuál es tu nombre completo como aparece en tu INE?
...
Vanessa: ¡Listo! ✅ Tu información ya está en el sistema. Bienvenida a Vanity.
```

**Payload enviado a n8n**

```json
{
  "candidato": {
    "nombre_oficial": "ANA MARIA PEREZ",
    "rfc": "PEQA901010...",
    "curp": "PEQA901010...",
    "fecha_nacimiento": "1990-10-10"
  },
  "laboral": {
    "rol_id": "manager",
    "sucursal_id": "plaza_cima",
    "fecha_inicio": "2026-01-15"
  },
  "referencias": [
    { "nombre": "Juan", "telefono": "555...", "relacion": "Trabajo" },
    { "nombre": "Luisa", "telefono": "844...", "relacion": "Familiar" }
  ],
  "metadata": {
    "timestamp": "2025-12-14T10:00:00-06:00"
  }
}
```

---

### 2️⃣ Vacaciones — `/vacaciones`

**Objetivo**
Gestionar descansos aplicando reglas de negocio automáticamente.

**Semáforo de decisión**

* 🔴 Menos de 5 días → Rechazo automático
* 🟡 6 a 11 días → Revisión manual
* 🟢 12+ días → Pre-aprobado

**Ejemplo**

```
Vanessa: Días solicitados: 6
Vanessa: Anticipación: 35 días
🟢 Excelente planeación. Solicitud pre-aprobada.
```

**Payload generado**

```json
{
  "record_id": "uuid-v4-unico",
  "tipo_solicitud": "VACACIONES",
  "fechas": {
    "inicio": "2026-01-20",
    "fin": "2026-01-25"
  },
  "metricas": {
    "dias_totales": 6,
    "dias_anticipacion": 35
  },
  "status_inicial": "PRE_APROBADO",
  "created_at": "2025-12-14T10:05:00-06:00"
}
```

---

### 3️⃣ Permisos con IA — `/permiso`

**Objetivo**
Registrar incidencias, salidas o permisos cortos.

**IA aplicada**
El bot analiza el texto libre y clasifica el motivo:

* EMERGENCIA
* MÉDICO
* TRÁMITE
* PERSONAL

**Ejemplo**

```
Usuario: Mi hijo se cayó en la escuela
Vanessa: Categoría detectada → EMERGENCIA 🚨
```

**Payload**

```json
{
  "record_id": "uuid-v4-unico",
  "tipo_solicitud": "PERMISO",
  "motivo_usuario": "Mi hijo se cayó en la escuela...",
  "categoria_detectada": "EMERGENCIA",
  "fechas": {
    "inicio": "2025-12-15",
    "fin": "2025-12-15"
  },
  "created_at": "2025-12-14T10:10:00-06:00"
}
```

---

### 4️⃣ Impresión — `/print`

**Objetivo**
Enviar documentos directamente a la cola de impresión de la oficina.

**Soporta**

* PDF
* Word
* Imágenes

---

## 🛠️ Instalación y Ejecución con Docker

### Requisitos

*   Docker
*   Docker Compose

### 1. Configuración del Entorno

Antes de iniciar, es necesario configurar las variables de entorno.

1.  **Crear el archivo `.env`**: Copia el archivo de ejemplo `.env.example` y renómbralo a `.env`.
    ```bash
    cp .env.example .env
    ```
2.  **Editar las variables**: Abre el archivo `.env` y rellena todas las variables requeridas:
    *   `TELEGRAM_TOKEN`: El token de tu bot de Telegram.
    *   `GOOGLE_API_KEY`: Tu clave de API de Google para la IA de Gemini.
    *   `WEBHOOK_*`: Las URLs de los webhooks de tu sistema de automatización (ej. n8n).
    *   `MYSQL_*`: Las credenciales para la base de datos (puedes dejar las que vienen por defecto si solo es para desarrollo local).
    *   `SMTP_*`: Las credenciales de tu servidor de correo para la función de impresión.

### 2. Construcción y Ejecución

Una vez configurado el entorno, el proyecto se gestiona fácilmente con Docker Compose.

1.  **Construir las imágenes**: Este comando crea las imágenes de Docker para el bot y la base de datos.
    ```bash
    docker-compose build
    ```
2.  **Iniciar los servicios**: Este comando inicia el bot y la base de datos en segundo plano.
    ```bash
    docker-compose up -d
    ```

El bot ahora estará en funcionamiento. Para detener los servicios, puedes usar `docker-compose down`.

---

## 📊 Esquema de Base de Datos Sugerido

Tabla: **rh_solicitudes**

| Campo             | Tipo      | Descripción            |
| ----------------- | --------- | ---------------------- |
| record_id         | UUID      | Identificador único    |
| user_id           | BIGINT    | Telegram ID            |
| nombre            | VARCHAR   | Nombre del colaborador |
| tipo              | VARCHAR   | VACACIONES / PERMISO   |
| fechas            | JSON      | Rango de fechas        |
| motivo            | TEXT      | Texto original         |
| categoria         | VARCHAR   | Clasificación IA       |
| dias_anticipacion | INT       | Métrica RH             |
| status_bot        | VARCHAR   | Resultado automático   |
| created_at        | TIMESTAMP | Zona MTY               |

---

## 🚀 Extensibilidad

Para agregar un nuevo comando:

1. Crear un archivo en `/modules`
2. Implementar su flujo
3. Registrar el comando en `main.py`

Vanessa ya sabe pensar. Solo enséñale una nueva habilidad. 🧠
