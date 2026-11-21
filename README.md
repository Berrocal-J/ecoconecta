# EcoConecta Villas de San Pablo

> La extracción usa `OPENAI_MODEL` y la transcripción usa `OPENAI_TRANSCRIPTION_MODEL`; los nombres de modelo no están fijados como regla del producto.

Sistema de gestión comunitaria de residuos para Villas de San Pablo, Barranquilla. Desarrollado para la Hackathon Unilibre – Fundación Santo Domingo 2026.

## 🌱 Visión General

EcoConecta es una plataforma que conecta a hogares y unidades productivas con colectivos de huerteros y recicladores para la gestión sostenible de residuos orgánicos y reciclables en Villas de San Pablo.

### Características Principales

- **Solicitudes por WhatsApp:** Los usuarios piden recolecciones vía WhatsApp (texto o nota de voz)
- **Reconocimiento de voz:** Transcripción automática de notas de voz usando OpenAI Whisper
- **Enrutamiento inteligente:** Las solicitudes se dirigen automáticamente al coordinador correcto (huerteros o recicladores)
- **Panel web optimizado:** Interfaz simple y rápida para coordinadores
- **Sistema de puntuación:** Motor parametrizable y auditable para asignar puntos por reciclaje
- **Notificaciones automáticas:** Confirmaciones y actualizaciones por WhatsApp

## 🏗️ Arquitectura

```
┌─────────────────┐
│   WhatsApp      │
│   (Usuario)     │
└────────┬────────┘
         │ (texto/audio)
         ▼
┌─────────────────┐
│  WhatsApp       │
│  Webhook        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  Backend        │
│  - Voice Service│
│  - NLP/GPT-4    │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │  OpenAI API  │
│  Database    │  │  (Whisper)   │
└──────────────┘  └──────────────┘
         │
         ▼
┌─────────────────┐
│  Next.js        │
│  Frontend       │
│  (Coordinadores)│
└─────────────────┘
```

### Componentes

- **Backend (FastAPI):** API REST, lógica de negocio, integración WhatsApp, servicio de voz
- **Frontend (Next.js):** Panel web para coordinadores (huerteros y recicladores)
- **Database (PostgreSQL):** Almacenamiento de datos relacional
- **WhatsApp Business Cloud API:** Mensajería bidireccional
- **OpenAI API:** Whisper (transcripción de voz) y GPT-4 (NLP)

## 📊 Modelo de Datos

### Entidades Principales

#### `usuarios`
- `id`: Identificador único
- `whatsapp`: Número de WhatsApp (único)
- `nombre`: Nombre del usuario/hogar/negocio
- `tipo_generador`: "hogar" o "unidad_productiva"
- `direccion`: Dirección en Villas de San Pablo
- `barrio`: "Villas de San Pablo"
- `puntos`: Puntos acumulados
- `creado_en`, `actualizado_en`: Timestamps

#### `solicitudes`
- `id`: Identificador único
- `usuario_id`: FK a usuarios
- `tipo_residuo`: "organico" o "reciclable"
- `estado`: "recibida", "en_revision", "asignada", "programada", "recolectada", "cancelada"
- `direccion`: Dirección de recolección
- `disponibilidad_horaria`: Preferencia horaria
- `observaciones`: Notas adicionales
- `mensaje_original`: Mensaje original de WhatsApp
- `codigo_unico`: ID único para seguimiento (ej: "ECO-A1B2C3D4")
- `creado_en`, `actualizado_en`: Timestamps

#### `colectivos`
- `id`: Identificador único
- `nombre`: Nombre del colectivo
- `tipo`: "huerteros" o "recicladores"
- `whatsapp`: Número de contacto del colectivo
- `activo`: 1 (activo) o 0 (inactivo)
- `creado_en`: Timestamp

#### `asignaciones`
- `id`: Identificador único
- `solicitud_id`: FK a solicitudes
- `colectivo_id`: FK a colectivos
- `persona_encargada`: Nombre del huertero/reciclador asignado
- `observaciones`: Notas de asignación
- `creado_en`: Timestamp

#### `recolecciones`
- `id`: Identificador único
- `solicitud_id`: FK a solicitudes (único)
- `material_nombre`: Tipo de material recibido
- `peso_kg`: Peso en kilogramos
- `cualidades`: JSON string ["limpio", "separado", "compactado"]
- `observaciones`: Notas de recolección
- `puntos_asignados`: Puntos calculados
- `creado_en`: Timestamp

#### `puntuacion_reglas`
- `id`: Identificador único
- `flujo`: "organico" o "reciclable"
- `material`: Tipo de material o "general"
- `puntos_por_kg`: Puntos por kilogramo
- `puntos_base`: Puntos base por entrega
- `bono_limpio`: Bonificación por material limpio
- `bono_separado`: Bonificación por bien separado
- `bono_compactado`: Bonificación por compactado
- `descripcion`: Descripción de la regla
- `activa`: 1 (activa) o 0 (inactiva)
- `creado_en`: Timestamp

#### `puntuacion_historial`
- `id`: Identificador único
- `usuario_id`: FK a usuarios
- `recoleccion_id`: FK a recolecciones
- `puntos`: Puntos asignados
- `regla_aplicada`: JSON string con desglose del cálculo
- `creado_en`: Timestamp

## 🏆 Sistema de Puntuación

### Fórmula de Cálculo

```
puntos_totales = puntos_base + (puntos_por_kg × peso_kg) + bonos_cualidades
```

### Reglas por Defecto (Configurables)

#### Residuos Orgánicos
- **General:** 5 puntos base + 2.0 puntos/kg + 2 bono separado
- **Restos de cocina:** 5 puntos base + 3.0 puntos/kg + 3 bono separado
- **Poda:** 5 puntos base + 1.5 puntos/kg + 2 bono separado

#### Residuos Reciclables
- **General:** 10 puntos base + 5.0 puntos/kg + 5 limpio + 5 separado + 3 compactado
- **Plástico PET:** 10 puntos base + 6.0 puntos/kg + 5 limpio + 5 separado + 3 compactado
- **Cartón:** 10 puntos base + 4.0 puntos/kg + 5 limpio + 5 separado + 3 compactado
- **Vidrio:** 10 puntos base + 7.0 puntos/kg + 5 limpio + 5 separado
- **Metal:** 10 puntos base + 8.0 puntos/kg + 5 limpio + 5 separado + 3 compactado
- **Papel:** 10 puntos base + 3.0 puntos/kg + 5 limpio + 5 separado + 3 compactado

**Nota:** Los valores son configurables mediante la API y están sujetos a validación de la Fundación Santo Domingo.

### Auditoría

Cada asignación de puntos guarda:
- Usuario y recolección asociados
- Regla aplicada con desglose completo
- Timestamp de asignación

Esto permite total transparencia y auditabilidad del sistema.

## 📱 Flujo WhatsApp + Voz

### 1. Solicitud por WhatsApp

**Usuario envía mensaje:**
- Texto: "Necesito recolección de residuos orgánicos en calle 45 # 23-10"
- Nota de voz: Audio transcrito automáticamente

**Procesamiento:**
1. Webhook recibe mensaje
2. Si es audio → Whisper transcribe a texto
3. GPT-4 extrae datos clave (tipo de residuo, dirección, horario)
4. Sistema crea solicitud en base de datos
5. Enrutamiento automático:
   - Orgánicos → Coordinador de Huerteros
   - Reciclables → Coordinador de Recicladores
6. Confirmación al usuario con código único

### 2. Coordinador Programa Recolección

**Acciones del coordinador:**
1. Revisa bandeja de solicitudes (filtrada por estado)
2. Selecciona solicitud y asigna:
   - Colectivo
   - Persona encargada
   - Fecha y hora
3. Sistema actualiza estado a "programada"
4. Notificación automática al usuario por WhatsApp

### 3. Registro de Recolección y Puntos

**Acciones del coordinador:**
1. Al completar la recolección, registra:
   - Material recibido (dropdown rápido)
   - Peso en kg (input numérico)
   - Cualidades (chips seleccionables: limpio, separado, compactado)
   - Observaciones (opcional)
2. Sistema:
   - Calcula puntos automáticamente
   - Actualiza estado a "recolectada"
   - Actualiza puntos del usuario
   - Guarda historial de puntuación
   - Notifica al usuario con puntos ganados

## 🚀 Instalación y Despliegue

### Requisitos Previos

- Docker y Docker Compose
- Git

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Copiar el archivo de ejemplo
cp .env.example .env
```

El archivo `.env.example` no contiene secretos. Para Docker local define al menos `POSTGRES_PASSWORD` y `SECRET_KEY`; los nombres de usuario/base de datos tienen valores de desarrollo por defecto. `DATABASE_URL` se construye automáticamente en Docker con esos valores. Si usas el backend fuera de Docker, define `DATABASE_URL` manualmente en `backend/.env`.

Editar `.env` con tus credenciales:

```env
# WhatsApp Business Cloud API (opcional - sin esto usa simulador)
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_ACCESS_TOKEN=tu_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=ecoconecta_verify

# OpenAI API (opcional - sin esto usa simulador)
OPENAI_API_KEY=tu_openai_api_key
```

Con las credenciales de WhatsApp y OpenAI vacías, el MVP arranca en modo simulador: `/whatsapp/simulador/entrada` acepta texto y audio, y `/whatsapp/simulador/mensajes` muestra las notificaciones generadas.

**Nota:** Sin configurar estas variables, el sistema usará simuladores para demostración local.

### Iniciar con Docker

```bash
# Clonar repositorio
git clone <repositorio>
cd EcoConecta

# Iniciar todos los servicios
docker-compose up --build

# Acceder a:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - PostgreSQL: localhost:5432
```

### Ejecutar Localmente (sin Docker)

#### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con DATABASE_URL=postgresql://user:password@localhost:5432/ecoconecta

# Iniciar PostgreSQL (usar Docker o instalación local)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=<tu-password-local> -e POSTGRES_DB=ecoconecta postgres:15

# Aplicar esquema y cargar datos semilla
alembic upgrade head
python ../database/seeds/seed_data.py

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Iniciar desarrollo
npm run dev
```

## 🧪 Pruebas

### Simulador de WhatsApp

Para probar sin webhook real:

```bash
# Enviar mensaje simulado
curl -X POST http://localhost:8000/whatsapp/simulador/entrada \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "573001234567",
    "type": "text",
    "content": "Necesito recolección de residuos orgánicos en calle 45 # 23-10"
  }'

# Ver mensajes enviados por simulador
curl http://localhost:8000/whatsapp/simulador/mensajes

# Limpiar mensajes
curl -X POST http://localhost:8000/whatsapp/simulador/limpiar
```

### Flujo Extremo a Extremo

1. **Usuario solicita recolección orgánica:**
   ```bash
   curl -X POST http://localhost:8000/whatsapp/simulador/entrada \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "573001234567",
       "type": "text",
       "content": "Hola, necesito que recojan residuos orgánicos en la calle 45 # 23-10"
     }'
   ```

2. **Coordinador de Huerteros:**
   - Acceder a http://localhost:3000/coordinador/huerteros
   - Ver solicitud en estado "recibida"
   - Programar recolección (asignar persona, fecha/hora)
   - Ver confirmación

3. **Registrar recolección:**
   - En la misma solicitud, hacer clic en "Registrar Recolección"
   - Ingresar material, peso, cualidades
   - Ver puntos asignados

4. **Segunda solicitud (reciclables):**
   ```bash
   curl -X POST http://localhost:8000/whatsapp/simulador/entrada \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "573007654321",
       "type": "text",
       "content": "Necesito recolección de plástico PET"
     }'
   ```

5. **Coordinador de Recicladores:**
   - Acceder a http://localhost:3000/coordinador/recicladores
   - Proceso similar al de huerteros

## 📁 Estructura del Proyecto

```
EcoConecta/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuración y database
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── routers/        # Endpoints FastAPI
│   │   ├── services/       # Lógica de negocio
│   │   ├── alembic/        # Migraciones
│   │   └── main.py         # App FastAPI
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── pages/              # Páginas Next.js
│   ├── components/         # Componentes React
│   ├── lib/                # Utilidades y API client
│   ├── styles/             # Estilos globales
│   ├── package.json
│   ├── Dockerfile
│   └── next.config.js
├── database/
│   └── seeds/
│       └── seed_data.py    # Datos semilla
├── docs/
│   ├── arquitectura.md
│   └── modelo_datos.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Configuración de WhatsApp Business Cloud API
> **Despliegue en la nube:** ver [`docs/despliegue-render.md`](docs/despliegue-render.md) y `render.yaml`. URL publicada: _pendiente de completar tras desplegar_.

> **Guía paso a paso y gratuita:** ver [`docs/whatsapp-gratis.md`](docs/whatsapp-gratis.md) (número de prueba de Meta, webhook con HTTPS y límites).

### 1. Crear App en Meta for Developers

1. Ir a https://developers.facebook.com/
2. Crear nueva app → "Business"
3. Agregar producto "WhatsApp"

### 2. Configurar Webhook

1. En tu app, ir a WhatsApp → Configuration
2. Webhook URL: `https://tu-dominio.com/whatsapp/webhook`
3. Verify Token: `ecoconecta_verify` (o el que configures en `.env`)
4. Suscribirse a eventos: `messages`

### 3. Obtener Credenciales

1. En WhatsApp → Configuration, ver:
   - Phone Number ID
   - Access Token (generar uno de prueba o permanente)
2. Agregar estas credenciales a tu `.env`

### 4. Configurar Ngrok (para desarrollo local)

```bash
# Instalar ngrok
# Descargar desde https://ngrok.com/

# Iniciar ngrok
ngrok http 8000

# Usar la URL generada en webhook:
# https://abc123.ngrok.io/whatsapp/webhook
```

## 🔒 Seguridad

- **Sin secretos hardcodeados:** Todas las credenciales en variables de entorno
- **Validación de datos:** Pydantic schemas en todos los endpoints
- **CORS configurado:** Solo orígenes permitidos
- **SQLAlchemy ORM:** Protección contra SQL injection
- **No exposición de datos sensibles:** Privacidad de contactos y direcciones

## 📝 Notas Importantes

- Los valores de puntuación son **configurables** y deben validarse con la Fundación Santo Domingo
- El sistema usa **simuladores** por defecto si no se configuran las APIs reales
- La interfaz web está **optimizada para coordinadores**, no para usuarios finales
- Los usuarios interactúan **exclusivamente por WhatsApp**
- Las decisiones operativas críticas (asignación final, confirmación) están bajo **control humano**

## 🤝 Contribución

Este proyecto fue desarrollado para la Hackathon Unilibre – Fundación Santo Domingo 2026.

## 📄 Licencia

Proyecto académico para Hackathon.

## Documentación de endurecimiento

- [Conversación WhatsApp](docs/conversacion-whatsapp.md)
- [IA responsable](docs/ia.md)
- [Seguridad y privacidad](docs/seguridad.md)
- [Despliegue](docs/despliegue.md)
- [Estado final](docs/estado-final.md)

---

**EcoConecta Villas de San Pablo** - Hackathon Unilibre – Fundación Santo Domingo 2026
