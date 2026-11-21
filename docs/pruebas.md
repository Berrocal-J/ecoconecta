# Pruebas ejecutadas

Fecha: 20 de noviembre de 2026.

## Resultados comprobados

- `docker compose up --build -d backend frontend`: exitoso.
- PostgreSQL healthy: exitoso.
- `GET /health`: `{"status":"healthy"}`.
- Login `coord_huerteros`: exitoso.
- Solicitud sin token a bandeja: HTTP 401.
- Coordinador de huerteros intentando bandeja recicladores: HTTP 403.
- Login `admin`: exitoso.
- Admin consultando usuarios: 4 registros de semilla.
- Admin consultando solicitudes: registros persistidos disponibles.
- Simulador WhatsApp organico con direccion y horario: crea solicitud y enruta a huerteros.
- Programacion: persiste fecha confirmada, cuenta asignadora y estado.
- Cierre: registra recoleccion, puntos y evento de historial.
- Build Next.js: exitoso para `/`, `/login`, `/admin`, `/coordinador/huerteros` y `/coordinador/recicladores`.

## No verificable localmente

- Firma y entrega real desde Meta.
- Transcripcion real de audio con OpenAI.
- HTTPS publico, plantillas y ventanas de mensajeria Meta.
- Compatibilidad en dispositivos fisicos y pruebas de carga.
