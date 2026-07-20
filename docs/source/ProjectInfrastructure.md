---
metrics:
  - label: "Container port"
    value: "8000"
    icon: "server"
    description: "Gunicorn binds 0.0.0.0:8000 inside the web container"
  - label: "Host mapping"
    value: "${WEB_PORT:-8000}:8000"
    icon: "network"
    description: "Configurable via WEB_PORT in .env"
  - label: "Gunicorn workers"
    value: "2 × 2 threads"
    icon: "cpu"
    description: "docker/Dockerfile CMD — tune per ECS task vCPU"
  - label: "DB connection pool"
    value: "600s"
    icon: "database"
    description: "CONN_MAX_AGE in production via dj-database-url"

cloudServices:
  - name: "Amazon ECS or EC2"
    purpose: "Runs Docker container from docker-compose.prod.yml or ECS task definition; ALB forwards HTTPS to port 8000"
    icon: "aws-ec2"
    cost: "~$15–50/mo (t3.small / 0.25 vCPU Fargate placeholder)"
  - name: "Amazon RDS (PostgreSQL)"
    purpose: "Primary database—already in use; connect via DATABASE_URL=postgresql://USER:PASS@host.rds.amazonaws.com:5432/dbname"
    icon: "aws-rds"
    cost: "~$25–100/mo (db.t4g.micro–small placeholder)"
  - name: "Amazon ElastiCache (Redis)"
    purpose: "Planned for cache, rate limits, and Celery broker—not yet wired in Django settings"
    icon: "redis"
    cost: "~$15/mo (cache.t4g.micro placeholder)"
  - name: "Amazon S3 + CloudFront"
    purpose: "Recommended for album art and audio files; local media volume is single-node only"
    icon: "aws-s3"
    cost: "Pay per GB + transfer"
  - name: "Application Load Balancer"
    purpose: "TLS termination (ACM cert), health checks, path routing to GraphQL and admin"
    icon: "aws-alb"
    cost: "~$18/mo + LCU usage"
  - name: "Amazon CloudWatch"
    purpose: "Container logs, RDS metrics, ALB 5xx alarms"
    icon: "cloudwatch"
    cost: "Low volume often within free tier"

deploymentLayers:
  - name: "Clients"
    color: "#1DB954"
    components:
      - name: "Streaming web / mobile"
        icon: "smartphone"
        description: "GraphQL clients hitting ALB HTTPS endpoint"
      - name: "GraphiQL (dev only)"
        icon: "code"
        description: "Schema explorer at /graphql/ — disable in production"

  - name: "Edge & compute (AWS)"
    color: "#FF9900"
    components:
      - name: "Application Load Balancer"
        icon: "globe"
        description: "ACM certificate, target group → container :8000"
      - name: "ECS service or EC2 + Docker"
        icon: "docker"
        description: "Image from docker/Dockerfile; env from .env or SSM Parameter Store"
      - name: "Celery worker (not in prod compose yet)"
        icon: "worker"
        description: "Separate task/service for async play counts and audio processing"

  - name: "Data & storage"
    color: "#527FFF"
    components:
      - name: "RDS PostgreSQL"
        icon: "database"
        description: "External managed DB—security group must allow app subnet"
      - name: "ElastiCache Redis (planned)"
        icon: "redis"
        description: "Optional; local stack uses redis:7-alpine container"
      - name: "Docker volumes (prod compose)"
        icon: "folder"
        description: "media_data and logs_data named volumes—migrate media to S3 for HA"

  - name: "Local Docker stack (development)"
    color: "#2496ED"
    components:
      - name: "postgres:16-alpine"
        icon: "database"
        description: "Service hostname postgres:5432, credentials music/music_db"
      - name: "redis:7-alpine"
        icon: "redis"
        description: "Service hostname redis:6379 for future cache/Celery"
      - name: "web (bind mount)"
        icon: "docker"
        description: "Gunicorn --reload; config.settings.docker"

dockerFiles:
  - service: "docker-compose.prod.yml"
    description: "Cloud deploy: application container only. DATABASE_URL in .env must point to RDS."
    content: |
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

  - service: "docker-compose.local.yml"
    description: "Full local stack: web + PostgreSQL + Redis with bind-mounted source for hot reload."
    content: |
      services:
        web:
          environment:
            DJANGO_SETTINGS_MODULE: config.settings.docker
            DATABASE_URL: postgresql://music:music@postgres:5432/music_db
        postgres:
          image: postgres:16-alpine
        redis:
          image: redis:7-alpine

  - service: "Dockerfile (multi-stage)"
    description: "Python 3.12 slim; builder compiles wheels; runtime runs as non-root appuser."
    content: |
      FROM python:3.12-slim-bookworm AS builder
      # pip install -r requirements.txt
      FROM python:3.12-slim-bookworm AS runtime
      USER appuser
      EXPOSE 8000
      HEALTHCHECK CMD curl-free probe on /admin/login/
      CMD gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 2

  - service: "entrypoint.sh"
    description: "Waits for DATABASE_URL host, runs migrate, optional collectstatic, execs Gunicorn."
    content: |
      # Parse DATABASE_URL → wait for PostgreSQL TCP
      python manage.py migrate --noinput
      if COLLECT_STATIC=true → collectstatic
      exec gunicorn ...
---

# Infrastructure

> **Deploy story:** Build image → run `docker compose -f docker/docker-compose.prod.yml --project-directory . up -d --build` on EC2/ECS with `.env` containing `DATABASE_URL` to your **existing RDS** instance.

> **RDS checklist:** Security group ingress from app SG on 5432; SSL optional via RDS CA; rotate credentials via Secrets Manager (placeholder—currently plain `.env`).

> **Dangerous:** Never commit `.env` with real RDS credentials. Set `DEBUG=False`, strong `SECRET_KEY`, and restrict `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` to your domain.

> **Missing for full AWS prod:** ElastiCache Redis, S3 media backend, Celery worker service, JWT GraphQL middleware, and WAF/rate limiting at ALB. GraphiQL should be disabled (`graphiql=False` in urls).

> **Useful note:** Entrypoint validates `DATABASE_URL` format—hostname-only values raise `ImproperlyConfigured` with a helpful message (see docker/README troubleshooting).
