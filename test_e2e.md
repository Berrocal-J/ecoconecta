# Prueba Extremo a Extremo - EcoConecta

## Escenario de Demostración

Este documento describe el flujo completo de prueba para demostrar el MVP de EcoConecta.

## Preparación del Entorno

### Opción 1: Docker (Recomendado)

```bash
# 1. Clonar el repositorio
cd EcoConecta

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env si tienes APIs reales (opcional para demo)

# 3. Iniciar servicios
docker-compose up --build

# Esperar a que todos los servicios inicien (ver logs)
docker-compose logs -f
```

Accesos:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Opción 2: Local (sin Docker)

#### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables
cp .env.example .env
# Editar DATABASE_URL en .env

# Iniciar PostgreSQL (Docker para db solo)
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=<tu-password-local> \
  -e POSTGRES_DB=ecoconecta \
  --name ecoconecta-db \
  postgres:15

# Esperar a que PostgreSQL inicie
sleep 5

# Crear tablas y datos semilla
python -c "from app.core.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
python ../database/seeds/seed_data.py

# Iniciar backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (otra terminal)

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Iniciar desarrollo
npm run dev
```

---

## Escenario 1: Unidad Productiva Solicita Residuos Orgánicos

### Paso 1: Solicitud por WhatsApp (Simulador)

```bash
curl -X POST http://localhost:8000/whatsapp/simulador/entrada \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "573007654321",
    "type": "text",
    "content": "Hola, soy Panadería San Pablo. Necesito que recojan residuos orgánicos (restos de pan y comida) en Carrera 32 # 15-20. Pueden recoger mañana en la mañana."
  }'
```

**Respuesta esperada:**
```json
{
  "status": "simulated",
  "phone_number": "573007654321"
}
```

### Paso 2: Verificar mensaje de confirmación

```bash
curl http://localhost:8000/whatsapp/simulador/mensajes
```

**Debería mostrar:**
```json
{
  "mensajes": [
    {
      "to": "573007654321",
      "mensaje": "✅ Solicitud recibida\n📋 Código: ECO-XXXXXXXX\n🗑️ Tipo: Residuos orgánicos\n📍 Dirección: Carrera 32 # 15-20\n👥 Tu solicitud ha sido enviada al Coordinador de Huerteros\nTe notificaremos cuando sea programada la recolección.",
      "tipo": "texto",
      "timestamp": "simulado"
    }
  ]
}
```

### Paso 3: Coordinador de Huerteros Revisa y Programa

1. Abrir navegador en: http://localhost:3000/coordinador/huerteros
2. Ver solicitud en estado "Recibida"
3. Hacer clic en "Programar"
4. Completar formulario:
   - Colectivo: Colectivo de Huerteros San Pablo
   - Persona encargada: Juan Pérez
   - Fecha y hora: 2024-11-21T09:00
   - Observaciones: (opcional)
5. Hacer clic en "Programar"

**Resultado esperado:**
- Alert: "✅ Recolección programada y notificada al usuario"
- Solicitud cambia a estado "Programada"

### Paso 4: Verificar notificación al usuario

```bash
curl http://localhost:8000/whatsapp/simulador/mensajes
```

**Debería mostrar nueva notificación:**
```json
{
  "mensajes": [
    "...",
    {
      "to": "573007654321",
      "mensaje": "✅ Tu solicitud ECO-XXXXXXXX ha sido programada.\n📅 Fecha y hora: 2024-11-21 09:00\n👤 Persona encargada: Juan Pérez\nGracias por contribuir al cuidado del medio ambiente en Villas de San Pablo.",
      "tipo": "texto",
      "timestamp": "simulado"
    }
  ]
}
```

### Paso 5: Coordinador Registra Recolección

1. En la misma solicitud, hacer clic en "Registrar Recolección"
2. Completar formulario:
   - Material: restos_cocina
   - Peso (kg): 15.5
   - Cualidades: seleccionar "Bien separado"
   - Observaciones: (opcional)
3. Hacer clic en "Registrar y Asignar Puntos"

**Resultado esperado:**
- Alert: "✅ Recolección registrada y puntos asignados"
- Solicitud cambia a estado "Recolectada"

### Paso 6: Verificar notificación con puntos

```bash
curl http://localhost:8000/whatsapp/simulador/mensajes
```

**Debería mostrar:**
```json
{
  "mensajes": [
    "...",
    {
      "to": "573007654321",
      "mensaje": "🎉 ¡Recolección registrada!\n📦 Material: restos_cocina\n⚖️ Peso: 15.5 kg\n✨ Cualidades: separado\n🏆 Puntos ganados: 58\n💰 Total puntos: 58\n¡Gracias por tu aporte a Villas de San Pablo!",
      "tipo": "texto",
      "timestamp": "simulado"
    }
  ]
}
```

**Cálculo de puntos (ejemplo):**
- Puntos base: 5
- Puntos por kg: 15.5 kg × 3.0 = 46.5
- Bono separado: 3
- Total: 5 + 46.5 + 3 = 54.5 → 54 puntos (redondeado)

---

## Escenario 2: Hogar Solicita Residuos Reciclables

### Paso 1: Solicitud por WhatsApp

```bash
curl -X POST http://localhost:8000/whatsapp/simulador/entrada \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "573001234567",
    "type": "text",
    "content": "Hola, soy María González. Tengo botellas PET y cartón para reciclar en Calle 45 # 23-10."
  }'
```

### Paso 2: Coordinador de Recicladores Revisa

1. Abrir navegador en: http://localhost:3000/coordinador/recicladores
2. Ver solicitud en estado "Recibida"
3. Hacer clic en "Programar"
4. Completar formulario:
   - Colectivo: Colectivo de Recicladores San Pablo
   - Persona encargada: Carlos López
   - Fecha y hora: 2024-11-21T14:00
5. Hacer clic en "Programar"

### Paso 3: Registrar Recolección

1. En la solicitud programada, hacer clic en "Registrar Recolección"
2. Completar formulario:
   - Material: plastico_pet
   - Peso (kg): 8.0
   - Cualidades: seleccionar "Limpio" y "Bien separado"
   - Observaciones: Botellas bien lavadas
3. Hacer clic en "Registrar y Asignar Puntos"

**Resultado esperado:**
- Alert: "✅ Recolección registrada y puntos asignados"
- Solicitud cambia a estado "Recolectada"

**Cálculo de puntos:**
- Puntos base: 10
- Puntos por kg: 8.0 kg × 6.0 = 48
- Bono limpio: 5
- Bono separado: 5
- Total: 10 + 48 + 5 + 5 = 68 puntos

---

## Verificación por API

### Obtener todas las solicitudes

```bash
curl http://localhost:8000/solicitudes/
```

### Obtener bandeja de huerteros

```bash
curl http://localhost:8000/solicitudes/coordinador/huerteros
```

### Obtener bandeja de recicladores

```bash
curl http://localhost:8000/solicitudes/coordinador/recicladores
```

### Obtener recolecciones

```bash
curl http://localhost:8000/recolecciones/
```

### Obtener historial de puntuación

```bash
curl http://localhost:8000/puntuacion/historial
```

### Obtener reglas de puntuación

```bash
curl http://localhost:8000/puntuacion/reglas
```

---

## Prueba con Nota de Voz (Simulador)

```bash
curl -X POST http://localhost:8000/whatsapp/simulador/entrada \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "573009876543",
    "type": "audio",
    "content": "simulado_audio_id"
  }'
```

**Nota:** Sin API key de OpenAI, el simulador retornará un texto de ejemplo predefinido.

---

## Limpiar Datos de Prueba

```bash
# Limpiar mensajes del simulador
curl -X POST http://localhost:8000/whatsapp/simulador/limpiar

# Reiniciar database (Docker)
docker-compose down -v
docker-compose up --build
```

---

## Checklist de Validación

- [ ] Backend responde en http://localhost:8000
- [ ] Frontend carga en http://localhost:3000
- [ ] API docs accesibles en http://localhost:8000/docs
- [ ] Simulador de WhatsApp funciona
- [ ] Solicitud orgánica se enruta a huerteros
- [ ] Solicitud reciclable se enruta a recicladores
- [ ] Coordinador puede programar recolección
- [ ] Notificación se envía al usuario
- [ ] Coordinador puede registrar recolección
- [ ] Puntos se calculan correctamente
- [ ] Historial de puntuación se guarda
- [ ] Estados de solicitudes se actualizan correctamente

---

## Troubleshooting

### Backend no inicia

```bash
# Ver logs
docker-compose logs backend

# Verificar PostgreSQL
docker-compose logs postgres

# Reiniciar backend
docker-compose restart backend
```

### Frontend no conecta a backend

```bash
# Verificar NEXT_PUBLIC_API_URL en frontend/.env.local
cat frontend/.env.local

# Debería ser: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Error de conexión a database

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Verificar credenciales en .env
cat .env | grep DATABASE_URL
```

### Simulador no responde

```bash
# Verificar que backend está corriendo
curl http://localhost:8000/health

# Debería retornar: {"status":"healthy"}
```

---

## Resumen del Flujo Demostrado

1. ✅ Usuario solicita recolección por WhatsApp (simulado)
2. ✅ Sistema enruta a coordinador correcto (huerteros/recicladores)
3. ✅ Coordinador programa recolección (asigna persona, fecha/hora)
4. ✅ Usuario recibe notificación con detalles
5. ✅ Coordinador registra recolección (material, peso, cualidades)
6. ✅ Sistema calcula puntos automáticamente
7. ✅ Usuario recibe notificación con puntos ganados
8. ✅ Historial de puntuación se guarda para auditoría

El MVP está listo para demostración en la Hackathon Unilibre – Fundación Santo Domingo 2026.
