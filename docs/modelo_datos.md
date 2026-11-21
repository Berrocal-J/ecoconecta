# Modelo de Datos - EcoConecta

## Diagrama Entidad-Relación (ER)

```mermaid
erDiagram
    usuarios ||--o{ solicitudes : "realiza"
    solicitudes ||--o| asignaciones : "tiene"
    solicitudes ||--o| recolecciones : "tiene"
    colectivos ||--o{ asignaciones : "recibe"
    usuarios ||--o{ puntuacion_historial : "acumula"
    recolecciones ||--o{ puntuacion_historial : "genera"
    puntuacion_reglas ||--o{ puntuacion_historial : "aplica"

    usuarios {
        int id PK
        string whatsapp UK
        string nombre
        enum tipo_generador
        string direccion
        string barrio
        int puntos
        timestamp creado_en
        timestamp actualizado_en
    }

    solicitudes {
        int id PK
        int usuario_id FK
        enum tipo_residuo
        enum estado
        string direccion
        string disponibilidad_horaria
        text observaciones
        text mensaje_original
        string codigo_unico UK
        timestamp creado_en
        timestamp actualizado_en
    }

    colectivos {
        int id PK
        string nombre
        enum tipo
        string whatsapp
        int activo
        timestamp creado_en
    }

    asignaciones {
        int id PK
        int solicitud_id FK
        int colectivo_id FK
        string persona_encargada
        string observaciones
        timestamp creado_en
    }

    recolecciones {
        int id PK
        int solicitud_id FK UK
        string material_nombre
        float peso_kg
        string cualidades
        text observaciones
        int puntos_asignados
        timestamp creado_en
    }

    puntuacion_reglas {
        int id PK
        string flujo
        string material
        float puntos_por_kg
        int puntos_base
        int bono_limpio
        int bono_separado
        int bono_compactado
        text descripcion
        int activa
        timestamp creado_en
    }

    puntuacion_historial {
        int id PK
        int usuario_id FK
        int recoleccion_id FK
        int puntos
        text regla_aplicada
        timestamp creado_en
    }
```

## Descripción Detallada de Tablas

### 1. usuarios

Almacena información de hogares y unidades productivas.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| id | INTEGER | Identificador único | PRIMARY KEY, AUTO INCREMENT |
| whatsapp | VARCHAR(20) | Número de WhatsApp | UNIQUE, NOT NULL |
| nombre | VARCHAR(100) | Nombre del usuario/hogar/negocio | NOT NULL |
| tipo_generador | ENUM | Tipo de generador: "hogar" o "unidad_productiva" | NOT NULL |
| direccion | VARCHAR(255) | Dirección en Villas de San Pablo | NOT NULL |
| barrio | VARCHAR(100) | Barrio (default: "Villas de San Pablo") | DEFAULT "Villas de San Pablo" |
| puntos | INTEGER | Puntos acumulados | DEFAULT 0 |
| creado_en | TIMESTAMP | Fecha de creación | DEFAULT NOW() |
| actualizado_en | TIMESTAMP | Fecha de última actualización | ON UPDATE NOW() |

**Índices:**
- PRIMARY KEY (id)
- UNIQUE INDEX (whatsapp)
- INDEX (barrio)

---

### 2. solicitudes

Registra cada solicitud de recolección realizada por usuarios.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| id | INTEGER | Identificador único | PRIMARY KEY, AUTO INCREMENT |
| usuario_id | INTEGER | FK a usuarios | NOT NULL, FOREIGN KEY |
| tipo_residuo | ENUM | Tipo: "organico" o "reciclable" | NOT NULL |
| estado | ENUM | Estado del flujo | DEFAULT "recibida" |
| direccion | VARCHAR(255) | Dirección de recolección | NULLABLE |
| disponibilidad_horaria | VARCHAR(100) | Preferencia horaria | NULLABLE |
| observaciones | TEXT | Notas adicionales | NULLABLE |
| mensaje_original | TEXT | Mensaje original de WhatsApp | NULLABLE |
| codigo_unico | VARCHAR(20) | ID único para seguimiento | UNIQUE, NOT NULL |
| creado_en | TIMESTAMP | Fecha de creación | DEFAULT NOW() |
| actualizado_en | TIMESTAMP | Fecha de última actualización | ON UPDATE NOW() |

**Enum estado:**
- `recibida` - Solicitud recibida, pendiente de revisión
- `en_revision` - Coordinador revisando
- `asignada` - Asignada a colectivo
- `programada` - Con fecha/hora confirmada
- `recolectada` - Recolección completada
- `cancelada` - Cancelada por usuario o coordinador

**Índices:**
- PRIMARY KEY (id)
- UNIQUE INDEX (codigo_unico)
- INDEX (usuario_id)
- INDEX (tipo_residuo)
- INDEX (estado)
- INDEX (creado_en)

---

### 3. colectivos

Información de colectivos de huerteros y recicladores.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| id | INTEGER | Identificador único | PRIMARY KEY, AUTO INCREMENT |
| nombre | VARCHAR(100) | Nombre del colectivo | NOT NULL |
| tipo | ENUM | Tipo: "huerteros" o "recicladores" | NOT NULL |
| whatsapp | VARCHAR(20) | Número de contacto | NULLABLE |
| activo | INTEGER | Estado: 1 (activo) o 0 (inactivo) | DEFAULT 1 |
| creado_en | TIMESTAMP | Fecha de creación | DEFAULT NOW() |

**Índices:**
- PRIMARY KEY (id)
- INDEX (tipo)
- INDEX (activo)

---

### 4. asignaciones

Registra asignaciones de solicitudes a colectivos y personas.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| id | INTEGER | Identificador único | PRIMARY KEY, AUTO INCREMENT |
| solicitud_id | INTEGER | FK a solicitudes | NOT NULL, FOREIGN KEY |
| colectivo_id | INTEGER | FK a colectivos | NOT NULL, FOREIGN KEY |
| persona_encargada | VARCHAR(100) | Nombre del huertero/reciclador | NOT NULL |
| observaciones | VARCHAR(255) | Notas de asignación | NULLABLE |
| creado_en | TIMESTAMP | Fecha de creación | DEFAULT NOW() |

**Índices:**
- PRIMARY KEY (id)
- INDEX (solicitud_id)
- INDEX (colectivo_id)

---

### 5. recolecciones

Registra lo realmente recibido en cada recolección.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| id | INTEGER | Identificador único | PRIMARY KEY, AUTO INCREMENT |
| solicitud_id | INTEGER | FK a solicitudes | NOT NULL, UNIQUE, FOREIGN KEY |
| material_nombre | VARCHAR(100) | Tipo de material recibido | NOT NULL |
| peso_kg | FLOAT | Peso en kilogramos | NOT NULL, > 0 |
| cualidades | VARCHAR(255) | JSON string: ["limpio", "separado", "compactado"] | NULLABLE |
| observaciones | TEXT | Notas de recolección | NULLABLE |
| puntos_asignados | INTEGER | Puntos calculados | DEFAULT 0 |
| creado_en | TIMESTAMP | Fecha de creación | DEFAULT NOW() |

**Formato cualidades (JSON):**
```json
["limpio", "separado", "compactado"]
```

**Índices:**
- PRIMARY KEY (id)
- UNIQUE INDEX (solicitud_id)
- INDEX (creado_en)

---

### 6. puntuacion_reglas

Reglas configurables para cálculo de puntos.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| id | INTEGER | Identificador único | PRIMARY KEY, AUTO INCREMENT |
| flujo | VARCHAR(50) | Flujo: "organico" o "reciclable" | NOT NULL |
| material | VARCHAR(100) | Material específico o "general" | NOT NULL |
| puntos_por_kg | FLOAT | Puntos por kilogramo | DEFAULT 0 |
| puntos_base | INTEGER | Puntos base por entrega | DEFAULT 0 |
| bono_limpio | INTEGER | Bonificación por material limpio | DEFAULT 0 |
| bono_separado | INTEGER | Bonificación por bien separado | DEFAULT 0 |
| bono_compactado | INTEGER | Bonificación por compactado | DEFAULT 0 |
| descripcion | TEXT | Descripción de la regla | NULLABLE |
| activa | INTEGER | Estado: 1 (activa) o 0 (inactiva) | DEFAULT 1 |
| creado_en | TIMESTAMP | Fecha de creación | DEFAULT NOW() |

**Índices:**
- PRIMARY KEY (id)
- INDEX (flujo, material)
- INDEX (activa)

---

### 7. puntuacion_historial

Auditoría de todas las asignaciones de puntos.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| id | INTEGER | Identificador único | PRIMARY KEY, AUTO INCREMENT |
| usuario_id | INTEGER | FK a usuarios | NOT NULL, FOREIGN KEY |
| recoleccion_id | INTEGER | FK a recolecciones | NOT NULL, FOREIGN KEY |
| puntos | INTEGER | Puntos asignados | NOT NULL |
| regla_aplicada | TEXT | JSON string con desglose | NOT NULL |
| creado_en | TIMESTAMP | Fecha de creación | DEFAULT NOW() |

**Formato regla_aplicada (JSON):**
```json
{
  "flujo": "reciclable",
  "material": "plastico_pet",
  "peso_kg": 5.0,
  "puntos_base": 10,
  "puntos_por_kg": 30.0,
  "bonos": {
    "limpio": 5,
    "separado": 5,
    "compactado": 3
  },
  "puntos_totales": 53
}
```

**Índices:**
- PRIMARY KEY (id)
- INDEX (usuario_id)
- INDEX (recoleccion_id)
- INDEX (creado_en)

---

## Relaciones

### usuarios ↔ solicitudes
- **Tipo:** One-to-Many
- **Descripción:** Un usuario puede realizar múltiples solicitudes
- **FK:** solicitudes.usuario_id → usuarios.id

### solicitudes ↔ asignaciones
- **Tipo:** One-to-Many
- **Descripción:** Una solicitud puede tener múltiples asignaciones (historial)
- **FK:** asignaciones.solicitud_id → solicitudes.id

### solicitudes ↔ recolecciones
- **Tipo:** One-to-One
- **Descripción:** Una solicitud tiene máximo una recolección registrada
- **FK:** recolecciones.solicitud_id → solicitudes.id (UNIQUE)

### colectivos ↔ asignaciones
- **Tipo:** One-to-Many
- **Descripción:** Un colectivo recibe múltiples asignaciones
- **FK:** asignaciones.colectivo_id → colectivos.id

### usuarios ↔ puntuacion_historial
- **Tipo:** One-to-Many
- **Descripción:** Un usuario acumula múltiples registros de puntuación
- **FK:** puntuacion_historial.usuario_id → usuarios.id

### recolecciones ↔ puntuacion_historial
- **Tipo:** One-to-Many
- **Descripción:** Una recolección genera un registro de puntuación
- **FK:** puntuacion_historial.recoleccion_id → recolecciones.id

### puntuacion_reglas ↔ puntuacion_historial
- **Tipo:** One-to-Many (lógica)
- **Descripción:** Una regla se aplica a múltiples historiales
- **Nota:** No hay FK explícita, la regla se guarda en regla_aplicada (JSON)

---

## Consultas Frecuentes

### Obtener bandeja de coordinador (huerteros)

```sql
SELECT s.*, u.nombre as usuario_nombre, u.whatsapp as usuario_whatsapp
FROM solicitudes s
JOIN usuarios u ON s.usuario_id = u.id
WHERE s.tipo_residuo = 'organico'
  AND s.estado = 'recibida'
ORDER BY s.creado_en DESC;
```

### Obtener historial de puntos de un usuario

```sql
SELECT ph.*, r.material_nombre, r.peso_kg
FROM puntuacion_historial ph
JOIN recolecciones r ON ph.recoleccion_id = r.id
WHERE ph.usuario_id = ?
ORDER BY ph.creado_en DESC;
```

### Obtener estadísticas de recolecciones por material

```sql
SELECT material_nombre, COUNT(*) as total_recolecciones, SUM(peso_kg) as total_peso, AVG(puntos_asignados) as avg_puntos
FROM recolecciones
GROUP BY material_nombre
ORDER BY total_peso DESC;
```

### Obtener ranking de usuarios por puntos

```sql
SELECT id, nombre, tipo_generador, puntos
FROM usuarios
ORDER BY puntos DESC
LIMIT 10;
```

---

## Migraciones

El proyecto usa Alembic para gestionar migraciones.

### Crear nueva migración

```bash
cd backend
alembic revision --autogenerate -m "descripción del cambio"
```

### Aplicar migraciones

```bash
alembic upgrade head
```

### Revertir última migración

```bash
alembic downgrade -1
```

---

## Datos Semilla

El archivo `database/seeds/seed_data.py` inserta datos iniciales:

- **4 usuarios:** 2 hogares, 2 unidades productivas
- **2 colectivos:** Huerteros y Recicladores
- **9 reglas de puntuación:** Para orgánicos y reciclables

Para ejecutar:

```bash
python database/seeds/seed_data.py
```

---

## Consideraciones de Diseño

### Normalización
- Tercera forma normal (3NF)
- Sin redundancia de datos
- Relaciones bien definidas

### Integridad
- Foreign keys en todas las relaciones
- Constraints NOT NULL donde aplica
- UNIQUE en campos identificadores (whatsapp, codigo_unico)

### Performance
- Índices en FKs y campos de búsqueda frecuentes
- Índice compuesto en (flujo, material) para reglas
- Timestamps para ordenamiento por fecha

### Auditabilidad
- Todos los registros tienen creado_en
- puntuacion_historial guarda desglose completo
- solicitudes guarda mensaje_original

### Escalabilidad
- Diseño relacional estándar
- Fácil agregar nuevos campos
- Reglas parametrizables sin cambios de código
