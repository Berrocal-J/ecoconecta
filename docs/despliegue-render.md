# Despliegue en la nube (Render)

**Proveedor:** Render (https://render.com). Todo se define en `render.yaml` (Blueprint).

| Componente | Servicio de Render | Detalle |
|---|---|---|
| Base de datos | Render Postgres (plan Free) | PostgreSQL gestionado; migraciones con Alembic |
| API | Web Service Docker (Free) | FastAPI, `backend/Dockerfile`; ejecuta `alembic upgrade head` y el seed al arrancar |
| Web | Web Service Docker (Free) | Next.js, `frontend/Dockerfile` |
| Red / TLS | Render | HTTPS automático; API y Web se comunican por URL pública (CORS) |

Diagrama: Navegador -> Web (Next.js) -> API (FastAPI) -> PostgreSQL. WhatsApp (Meta) -> `/whatsapp/webhook` -> API.

## Pasos
1. Sube el código a GitHub (sin `.env`).
2. Render > **New > Blueprint** > elige el repositorio > **Apply**.
3. Cuando pida variables, completa solo las claves demo: `DEMO_ADMIN_PASSWORD`, `DEMO_HUERTEROS_PASSWORD`,
   `DEMO_RECICLADORES_PASSWORD` (inventa claves fuertes). Deja vacías `BACKEND_CORS_ORIGINS` y `NEXT_PUBLIC_API_URL` por ahora.
4. Espera a que ambos servicios queden "Live" y anota sus URLs
   (ej. `https://ecoconecta-api.onrender.com`, `https://ecoconecta-web.onrender.com`).
5. En **ecoconecta-web > Environment**: `NEXT_PUBLIC_API_URL` = URL del API (sin `/` final).
   En **ecoconecta-api > Environment**: `BACKEND_CORS_ORIGINS` = URL de la web.
6. En la web: **Manual Deploy > Clear build cache & deploy** (la URL del API se incrusta al compilar).
7. Prueba: `https://<api>/health` y abre `https://<web>`; entra a `/login` con `coord_huerteros` y la clave que definiste.

## Limitaciones del plan gratuito (declararlas)
- El servicio se duerme tras ~15 min sin visitas y tarda cerca de 1 min en despertar: **ábrelo 5 min antes de la demo**.
- La base de datos gratuita expira a los 30 días (exportar con `pg_dump` si se desea conservar).
- Modo demo: `USE_EXTERNAL_SERVICES=false` (simulador de WhatsApp). Para WhatsApp real: cuenta de Meta con negocio verificado,
  poner `USE_EXTERNAL_SERVICES=true` y las variables `WHATSAPP_*` en el servicio API.
