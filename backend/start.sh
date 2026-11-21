#!/bin/sh
# Arranque del API: migraciones, datos semilla y servidor.
set -e
alembic upgrade head
python seeds/seed_data.py
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"