# Infrastructure

## Metrics

| Label | Value | Description |
| --- | --- | --- |
| Container port | 8000 | Gunicorn binds 0.0.0.0:8000 inside the web container |
| Host mapping | ${WEB_PORT:-8000}:8000 | Configurable via WEB_PORT in .env |
| Gunicorn workers | 2 × 2 threads | docker/Dockerfile CMD — tune per ECS task vCPU |
| DB connection pool | 600s | CONN_MAX_AGE in production via dj-database-url |

## Cloud services

| Service | Purpose | Est. cost |
| --- | --- | --- |
| Amazon ECS or EC2 | Runs Docker container from docker-compose.prod.yml or ECS task definition; ALB forwards HTTPS to port 8000 | ~$15–50/mo (t3.small / 0.25 vCPU Fargate placeholder) |
| Amazon RDS (PostgreSQL) | Primary database—already in use; connect via DATABASE_URL=postgresql://USER:PASS@host.rds.amazonaws.com:5432/dbname | ~$25–100/mo (db.t4g.micro–small placeholder) |
| Amazon ElastiCache (Redis) | Planned for cache, rate limits, and Celery broker—not yet wired in Django settings | ~$15/mo (cache.t4g.micro placeholder) |
| Amazon S3 + CloudFront | Recommended for album art and audio files; local media volume is single-node only | Pay per GB + transfer |
| Application Load Balancer | TLS termination (ACM cert), health checks, path routing to GraphQL and admin | ~$18/mo + LCU usage |
| Amazon CloudWatch | Container logs, RDS metrics, ALB 5xx alarms | Low volume often within free tier |

## Deployment layers

### Clients

- **Streaming web / mobile** — GraphQL clients hitting ALB HTTPS endpoint
- **GraphiQL (dev only)** — Schema explorer at /graphql/ — disable in production

### Edge & compute (AWS)

- **Application Load Balancer** — ACM certificate, target group → container :8000
- **ECS service or EC2 + Docker** — Image from docker/Dockerfile; env from .env or SSM Parameter Store
- **Celery worker (not in prod compose yet)** — Separate task/service for async play counts and audio processing

### Data & storage

- **RDS PostgreSQL** — External managed DB—security group must allow app subnet
- **ElastiCache Redis (planned)** — Optional; local stack uses redis:7-alpine container
- **Docker volumes (prod compose)** — media_data and logs_data named volumes—migrate media to S3 for HA

### Local Docker stack (development)

- **postgres:16-alpine** — Service hostname postgres:5432, credentials music/music_db
- **redis:7-alpine** — Service hostname redis:6379 for future cache/Celery
- **web (bind mount)** — Gunicorn --reload; config.settings.docker

## Docker configuration

### docker-compose.prod.yml

Cloud deploy: application container only. DATABASE_URL in .env must point to RDS.

```yaml
services:
  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: music-api-web
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
      COLLECT_STATIC: "true"
    ports:
      - "${WEB_PORT:-8000}:8000"
    volumes:
      - media_data:/app/media
      - logs_data:/app/logs
# External: RDS PostgreSQL via DATABASE_URL
```

### docker-compose.local.yml

Full local stack: web + PostgreSQL + Redis with bind-mounted source for hot reload.

```yaml
services:
  web:
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.docker
      DATABASE_URL: postgresql://music:music@postgres:5432/music_db
  postgres:
    image: postgres:16-alpine
  redis:
    image: redis:7-alpine
```

### Dockerfile (multi-stage)

Python 3.12 slim; builder compiles wheels; runtime runs as non-root appuser.

```yaml
FROM python:3.12-slim-bookworm AS builder
# pip install -r requirements.txt
FROM python:3.12-slim-bookworm AS runtime
USER appuser
EXPOSE 8000
HEALTHCHECK CMD curl-free probe on /admin/login/
CMD gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 2
```

### entrypoint.sh

Waits for DATABASE_URL host, runs migrate, optional collectstatic, execs Gunicorn.

```yaml
# Parse DATABASE_URL → wait for PostgreSQL TCP
python manage.py migrate --noinput
if COLLECT_STATIC=true → collectstatic
exec gunicorn ...
```

## Additional notes

# Infrastructure

> **Deploy story:** Build image → run `docker compose -f docker/docker-compose.prod.yml --project-directory . up -d --build` on EC2/ECS with `.env` containing `DATABASE_URL` to your **existing RDS** instance.

> **RDS checklist:** Security group ingress from app SG on 5432; SSL optional via RDS CA; rotate credentials via Secrets Manager (placeholder—currently plain `.env`).

> **Dangerous:** Never commit `.env` with real RDS credentials. Set `DEBUG=False`, strong `SECRET_KEY`, and restrict `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` to your domain.

> **Missing for full AWS prod:** ElastiCache Redis, S3 media backend, Celery worker service, JWT GraphQL middleware, and WAF/rate limiting at ALB. GraphiQL should be disabled (`graphiql=False` in urls).

> **Useful note:** Entrypoint validates `DATABASE_URL` format—hostname-only values raise `ImproperlyConfigured` with a helpful message (see docker/README troubleshooting).

