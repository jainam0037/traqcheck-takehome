# #!/usr/bin/env bash
# set -e

# echo "Waiting for db..."
# # Try up to 90 times with 2s sleep = ~3 minutes
# for i in {1..90}; do
#   python - <<'PY'
# import sys, os
# import urllib.parse as up
# try:
#     import psycopg2
# except Exception:
#     sys.exit(1)

# url = os.getenv("DATABASE_URL")
# if not url:
#     sys.exit(1)

# try:
#     up.uses_netloc.append("postgres")
#     conn = psycopg2.connect(url)
#     conn.close()
#     sys.exit(0)
# except Exception:
#     sys.exit(1)
# PY
#   if [ $? -eq 0 ]; then
#     echo "DB is ready."
#     break
#   fi
#   sleep 2
# done

# python manage.py migrate --noinput || true
# python manage.py collectstatic --noinput 2>/dev/null || true

# echo "Starting Django dev server..."
# python manage.py runserver 0.0.0.0:8000


#!/bin/sh
set -e

echo "[entrypoint] env: POSTGRES_HOST=${POSTGRES_HOST} POSTGRES_PORT=${POSTGRES_PORT:-5432} DB=${POSTGRES_DB}"

echo "[entrypoint] waiting for db..."
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" >/dev/null 2>&1; do
  echo "  db not ready yet..."
  sleep 1
done

echo "[entrypoint] db is ready. Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] starting django on 0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000
