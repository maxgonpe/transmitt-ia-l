#!/bin/bash
set -e

echo "🚀 Iniciando Transmitt IA Local..."

# Sólo directorios propios que el despliegue necesita.
mkdir -p /app/staticfiles

if [ "${DB_ENGINE:-}" = "django.db.backends.postgresql" ]; then
    if [ -z "${DB_HOST:-}" ] || [ -z "${DB_PORT:-}" ]; then
        echo "❌ DB_HOST y DB_PORT son obligatorios para PostgreSQL."
        exit 1
    fi

    echo "⏳ Esperando a PostgreSQL en ${DB_HOST}:${DB_PORT}..."

    python - <<'PY'
import os
import socket
import time

host = os.environ["DB_HOST"]
port = int(os.environ.get("DB_PORT", "5432"))

while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            break
    except OSError:
        time.sleep(0.5)
PY

    echo "✅ PostgreSQL está listo"
fi

echo "📦 Ejecutando migraciones..."
python manage.py migrate --noinput

echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Aplicación lista para iniciar"

exec "$@"
