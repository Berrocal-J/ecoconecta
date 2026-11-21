# Decisiones

- Se conserva el formulario web solo como alternativa de demo; el flujo ciudadano principal es WhatsApp.
- Las conversaciones y la cola de salientes usan PostgreSQL, no Redis ni memoria de proceso.
- La compatibilidad con `persona_encargada` se conserva mientras se migra a `recolector_id` formal.
- Las reglas de puntos, rutas y horarios son ejemplos configurables y requieren validación de la Fundación Santo Domingo.
- Las cuentas iniciales nuevas reciben claves desde variables `DEMO_*_PASSWORD` o una clave generada en el arranque; las cuentas ya existentes no se sobreescriben.
