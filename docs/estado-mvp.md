# Estado del MVP y demo local

## Arranque

Desde la raiz del repositorio:

1. Copiar `.env.example` a `.env` y definir al menos `POSTGRES_PASSWORD` y `SECRET_KEY`.
2. Abrir Docker Desktop y esperar que el motor Linux este disponible.
3. Ejecutar:

```powershell
docker compose up --build -d
docker compose ps
```

Abrir [http://localhost:3000](http://localhost:3000). La API queda disponible en
[http://localhost:8000/docs](http://localhost:8000/docs).

## Flujo publico implementado

- El canal principal es WhatsApp: el ciudadano escribe o envia una nota de voz y el webhook procesa la solicitud.
- La portada destaca el chat de WhatsApp. El formulario web queda como alternativa de prueba/accesibilidad, no como canal operativo principal.
- Define `NEXT_PUBLIC_WHATSAPP_NUMBER` en `.env` para activar el boton hacia el numero oficial.
- La portada alternativa permite registrar una solicitud con generador, flujo, direccion, material, disponibilidad y consentimientos.
- Se devuelve un codigo EcoConecta y un token privado para consultar el estado sin exponer telefono ni direccion.
- El endpoint ciudadano es `POST /solicitudes/publica`; la consulta es
  `GET /solicitudes/publica/consulta/{codigo}?token=...`.
- Con `USE_EXTERNAL_SERVICES=false`, las notificaciones usan el simulador local. Para Meta/OpenAI se deben definir credenciales y activar explicitamente
  `USE_EXTERNAL_SERVICES=true`.
- Los enlaces de coordinacion mantienen las bandejas separadas de huerteros y recicladores.

## Demo extremo a extremo

1. Crear una solicitud organica en la portada.
2. Entrar a la bandeja de huerteros, asignar y programar.
3. Registrar la recoleccion con material, peso y cualidades.
4. Verificar puntos, historial y notificacion en el simulador.
5. Repetir con flujo reciclable en la bandeja de recicladores.

## Acceso demo local

Las cuentas nuevas se crean con las variables `DEMO_ADMIN_PASSWORD`, `DEMO_HUERTEROS_PASSWORD` y `DEMO_RECICLADORES_PASSWORD`, o con una clave generada en el primer seed. No se guardan contraseñas en documentación ni en código.

El rol de cada coordinador limita tambien los endpoints del backend; no basta con conocer la URL.

## Alcance y pendientes de produccion

El MVP cubre persistencia PostgreSQL, migraciones Alembic, conversación WhatsApp persistente,
consentimiento, rutas por colectivo, programación, cierre con puntos auditables, webhook HMAC,
simulador, paneles y contenido educativo. La integración Meta/OpenAI real, HTTPS, plantillas,
backups y la vista completa de recolectores requieren credenciales o una iteración de despliegue.
Los valores de puntos son configurables y requieren validación de la Fundación Santo Domingo.
