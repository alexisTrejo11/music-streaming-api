#!/bin/sh
set -e

wait_for_service() {
  host="$1"
  port="$2"
  name="$3"
  echo "Waiting for ${name} at ${host}:${port}..."
  until python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect(('${host}', ${port}))
    s.close()
except OSError:
    raise SystemExit(1)
" 2>/dev/null; do
    sleep 1
  done
  echo "${name} is ready."
}

if [ -n "${DATABASE_URL:-}" ]; then
  python -c "
import os
import socket
import sys
from urllib.parse import urlparse

url = os.environ.get('DATABASE_URL', '')
parsed = urlparse(url)
host = parsed.hostname
port = parsed.port or 5432

if not host:
    sys.exit(0)

print(f'Waiting for PostgreSQL at {host}:{port}...', flush=True)
while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            break
    except OSError:
        import time
        time.sleep(1)
print('PostgreSQL is ready.', flush=True)
"
elif [ -n "${DATABASE_HOST:-}" ] && [ -n "${DATABASE_PORT:-}" ]; then
  wait_for_service "${DATABASE_HOST}" "${DATABASE_PORT}" "PostgreSQL"
fi

echo "Running migrations..."
python manage.py migrate --noinput

if [ "${COLLECT_STATIC:-false}" = "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

exec "$@"
