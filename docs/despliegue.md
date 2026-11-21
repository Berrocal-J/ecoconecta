# Despliegue

## Desarrollo

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

El compose de desarrollo monta el código y usa `uvicorn --reload`. No debe exponerse directamente a Internet.

## Producción pendiente

El despliegue requiere un proveedor de cómputo con HTTPS, PostgreSQL gestionado, dominio y variables secretas del proveedor. La URL pública debe terminar en `/whatsapp/webhook`. Registrar la URL y el verify token en Meta, suscribir `messages`, configurar `WHATSAPP_APP_SECRET` y usar un token permanente de sistema.

Antes de publicar:

1. Crear una imagen de backend sin `--reload` ni montaje de código.
2. Construir Next.js y ejecutar `next start`.
3. Configurar CORS con el dominio real.
4. Ejecutar `alembic upgrade head` como paso de release.
5. Activar backups PostgreSQL y probar restauración.
6. Configurar plantillas aprobadas y límites de envío.
7. Mantener el simulador deshabilitado.

No se incluyen credenciales ni se ejecuta un despliegue externo desde este repositorio.
