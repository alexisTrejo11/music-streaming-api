# Docker

Lightweight container setup for the Music Streaming API. Everything lives under `docker/`.

Configuration uses the single root **`.env`** file (copy from `.env.example`).

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage slim image (`python:3.12-slim`) |
| `entrypoint.sh` | Wait for DB, run migrations, optional `collectstatic` |
| `docker-compose.local.yml` | App + PostgreSQL + Redis for local development |
| `docker-compose.prod.yml` | App only — external DB and services via env |

## Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2 (`docker compose`)

All commands below are run from the **repository root**.

## Environment setup

```bash
cp .env.example .env
```

Edit `.env` for your setup. See `.env.example` for variables used by Django and Compose.

**Docker local:** `docker-compose.local.yml` overrides connection settings for the `web` service (`DATABASE_URL`, `DJANGO_SETTINGS_MODULE`, `ALLOWED_HOSTS`) so the app always talks to the `postgres` and `redis` containers — even if `.env` still has production values. You only need `WEB_PORT`, `POSTGRES_PORT`, and `REDIS_PORT` in `.env` to customize host port mappings.

`localhost` inside a container refers to the container itself, not sibling services.

---

## Quick start (local)

```bash
docker compose -f docker/docker-compose.local.yml --project-directory . up --build
```

Create a superuser (first time only):

```bash
docker compose -f docker/docker-compose.local.yml --project-directory . exec web python manage.py createsuperuser
```

Open the API:

- GraphQL: http://localhost:8000/graphql
- Admin: http://localhost:8000/admin

### Local stack services

| Service | Image | Host port | Container hostname |
|---------|-------|-----------|-------------------|
| `web` | Built from `docker/Dockerfile` | 8000 | `web` |
| `postgres` | `postgres:16-alpine` | 5432 | `postgres` |
| `redis` | `redis:7-alpine` | 6379 | `redis` |

Settings module for local Docker: `config.settings.docker` (set in compose; overrides `DJANGO_SETTINGS_MODULE` from `.env`).

Local stack DB credentials (fixed in compose): user `music`, password `music`, database `music_db`.

### Useful local commands

```bash
# Detached mode
docker compose -f docker/docker-compose.local.yml --project-directory . up -d --build

# Logs
docker compose -f docker/docker-compose.local.yml --project-directory . logs -f web

# Run migrations manually
docker compose -f docker/docker-compose.local.yml --project-directory . exec web python manage.py migrate

# Open a shell
docker compose -f docker/docker-compose.local.yml --project-directory . exec web python manage.py shell

# Stop and remove containers (keeps volumes)
docker compose -f docker/docker-compose.local.yml --project-directory . down

# Stop and remove containers + volumes
docker compose -f docker/docker-compose.local.yml --project-directory . down -v
```

Source code is bind-mounted into `web` for development; Gunicorn runs with `--reload` so Python changes are picked up automatically.

---

## Cloud / production deploy

The production compose file runs **only the application container**. Point `.env` at managed services (RDS, ElastiCache, OpenSearch, S3, etc.).

1. Set production values in `.env` (`DEBUG=False`, `DJANGO_SETTINGS_MODULE=config.settings.production`, external `DATABASE_URL`, etc.).

2. Build and run:

   ```bash
   docker compose -f docker/docker-compose.prod.yml --project-directory . up -d --build
   ```

Production settings: `config.settings.production` (set in compose). The entrypoint runs `collectstatic` when `COLLECT_STATIC=true`.

### Production checklist

- Set a strong `SECRET_KEY`
- Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` for your domain
- Provide a valid `DATABASE_URL` to your managed PostgreSQL instance
- Mount or use object storage for `media/` in production (local volume is for single-node deploys only)
- Put TLS termination on a load balancer or reverse proxy in front of the container

---

## Build image only

```bash
docker build -f docker/Dockerfile -t music-streaming-api:latest .
```

---

## Image design

- **Base:** `python:3.12-slim-bookworm` (~150 MB base)
- **Multi-stage build:** compile deps in a builder stage; runtime image keeps only wheels and runtime libs (`libpq5`, JPEG/zlib for Pillow)
- **Non-root user:** `appuser` runs Gunicorn
- **Health check:** HTTP probe on `/admin/login/`
- **Dependencies:** root `requirements.txt`

Typical image size is roughly 300–450 MB depending on dependency wheels.

---

## Troubleshooting

**App cannot connect to PostgreSQL**

- Local Docker: confirm `DATABASE_URL` uses `@postgres:5432`, not `@localhost:5432`
- Prod: verify security groups / firewall allow the container host to reach the DB

**Port already in use**

- Change `WEB_PORT`, `POSTGRES_PORT`, or `REDIS_PORT` in `.env`

**Migrations fail on startup**

- Check postgres logs: `docker compose -f docker/docker-compose.local.yml --project-directory . logs postgres`
- Local Docker: credentials are fixed in `docker-compose.local.yml` (`music` / `music_db`). If you changed them in an older setup, reset the volume: `docker compose -f docker/docker-compose.local.yml --project-directory . down -v`
- Production: ensure `DATABASE_URL` credentials match your managed PostgreSQL instance

**`UnknownSchemeError: Scheme '://' is unknown`**

- `DATABASE_URL` must be a full URL: `postgresql://USER:PASSWORD@HOST:5432/DBNAME`
- A hostname alone (e.g. `my-db.rds.amazonaws.com/postgres`) is invalid

**Permission errors on `logs/` or `media/`**

- Named volumes are used in compose to avoid host permission mismatches
