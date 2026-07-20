# Architecture

## Presentation (clients)

Web and mobile streaming clients consuming GraphQL over HTTPS.

### Components

- Streaming web app (React/Vue placeholder)
- Mobile player (iOS/Android placeholder)
- GraphiQL / admin for operators

### Responsibilities

- Send GraphQL queries and mutations
- Store JWT access/refresh tokens securely
- Stream audio from CDN or media URLs returned by API

### Technologies

- HTTPS
- GraphQL JSON
- Authorization: Bearer (when JWT middleware enabled)

## Edge & gateway (AWS)

TLS termination and routing to the containerized Django app.

### Components

- Application Load Balancer (ALB)
- ACM TLS certificates
- Security groups (443 → container 8000)

### Responsibilities

- Terminate TLS and forward to Gunicorn
- Health checks on /admin/login/ or custom path
- Optional AWS WAF rate limiting

### Technologies

- AWS ALB
- ACM
- Route 53 (placeholder)

## Application layer

Django 4 monolith with Graphene-Django schema merged from six domain apps.

### Components

- config.schema — merged Query/Mutation
- apps/users — auth & preferences
- apps/artists — artist catalog
- apps/music — songs, albums, genres
- apps/playlists — CRUD, collaborators, follows
- apps/interactions — likes, reviews, history, analytics
- apps/recommendations — taste, radio, Discover Weekly
- apps/core — decorators, logging, base mutations

### Responsibilities

- GraphQL resolvers delegate to service classes
- Structured logging (JSON + audit files)
- WhiteNoise static files in production

### Technologies

- Graphene-Django
- Django REST Framework
- SimpleJWT
- Gunicorn WSGI

## Data layer

Relational catalog and user data on managed PostgreSQL; optional Redis for cache/tasks.

### Components

- Amazon RDS PostgreSQL (production)
- PostgreSQL 16 container (local Docker stack)
- Redis 7 (local Docker; ElastiCache placeholder)

### Responsibilities

- ACID storage for catalog, playlists, taste profiles
- Listening history and play analytics
- Future: cache hot catalog queries

### Technologies

- psycopg2-binary
- dj-database-url

## Async & media (partial)

Background processing and binary media—not fully wired for cloud yet.

### Components

- Celery shared tasks (song processing stub)
- Local media/ volume or future S3 bucket
- NumPy recommendation scoring (in-process)

### Responsibilities

- Async audio processing (planned)
- Album art and audio file storage

### Technologies

- Celery
- Pillow
- NumPy

## Design patterns

| Pattern | Category | Description |
| --- | --- | --- |
| 🏗️ Service layer | Structural | Domain logic in *Service classes (AuthService, RecommendationService, PlaylistService) keeps GraphQL resolvers thin. |
| 🧩 Mixin composition (GraphQL) | Structural | Each app exports Query/Mutation mixins merged in config.schema — modular schema without microservices. |
| 📦 BaseMutation envelope | Behavioral | Mutations return { success, message, ...payload } via BaseMutation for consistent client handling. |
| 🔐 Decorator — auth_required | Behavioral | @auth_required on mutations checks info.context.user before calling services. |
| 🎯 Strategy — recommendation scoring | Behavioral | RecommendationService weights genre, artist follow, audio features, and popularity with configurable reason objects. |
| 🗄️ Repository (Django ORM) | Data | Models and select_related/prefetch patterns encapsulate data access; services compose queries with transactions. |

## Scalability strategies

- **Stateless API containers on ECS/EC2** — Scale Gunicorn workers per task; add ECS tasks or EC2 instances behind ALB when CPU or latency grows.
- **Amazon RDS PostgreSQL** — Managed backups, storage autoscaling, optional read replicas for analytics-heavy recommendation rebuilds.
- **Offload media to S3 + CloudFront** — Serve album art and audio from CDN; API returns signed URLs—required before horizontal media scaling.
- **Async play telemetry** — Move play_count increments and taste-profile updates to Celery to keep GraphQL mutations fast under load.

## Security strategies

- **Password validation & JWT issuance** — Django validators plus AuthService rules; SimpleJWT access/refresh returned on register/login.
- **auth_required on sensitive mutations** — Playlist edits, reviews, taste updates require authenticated context user.
- **Production TLS & secure cookies** — SECURE_SSL_REDIRECT configurable when TLS terminates at ALB; secure session/CSRF cookies when enabled.
- **Structured audit logging** — Dedicated audit logger with timed rotation and optional DatabaseLogHandler for errors.
- **CSRF exempt GraphQL only** — GraphQLView is csrf_exempt—acceptable for token-based SPAs but requires strict CORS and auth.

## Cache strategies

| Name | TTL | Coverage | Description |
| --- | --- | --- | --- |
| Redis (local Docker stack) | TBD — not wired in settings yet | Future: session cache, rate limits, Celery broker | Redis 7 container in docker-compose.local.yml—ready for django-redis when configured |
| UserTaste profile cache | 7 days | Recommendation queries avoid full history scan on every request | UserTaste model stores denormalized favorites; refreshed when last_updated > 7 days |
| ORM query optimization | N/A | Catalog list/search/resolvers | select_related on song → artist, album, genre in hot paths |

## Architecture highlights

### 🔗 Single merged GraphQL schema

One endpoint for catalog, social, and recommendations—clients fetch exactly the fields they need.

### 💡 Explainable recommendations

RecommendedSongType includes score and reasons array for transparent UX.

### ❤️ Rich interaction model

Likes, saves, reviews, follows, listening history feed taste and trending algorithms.

### 🐳 Docker split local vs prod

Local stack bundles Postgres+Redis; prod compose expects cloud DATABASE_URL (RDS).

## Architecture diagram

### Legend

| Type | Label |
| --- | --- |
| client | Client |
| gateway | ALB |
| service | API service |
| database | Database |
| queue | Cache / queue |
| monitoring | Monitoring |

### Nodes

| ID | Label | Type | Status |
| --- | --- | --- | --- |
| streaming-client | Web / mobile clients | client | healthy |
| alb | AWS ALB (TLS) | gateway | healthy |
| api | Music API (Docker/Gunicorn) | service | healthy |
| rds | RDS PostgreSQL | database | healthy |
| redis | ElastiCache Redis | queue | warning |
| s3 | S3 + CloudFront (media) | service | warning |
| celery | Celery worker (planned) | service | warning |
| cloudwatch | CloudWatch logs | monitoring | healthy |

### Connections

| From | To | Label | Protocol |
| --- | --- | --- | --- |
| streaming-client | alb | HTTPS | TLS 1.2+ |
| alb | api | Proxy | HTTP |
| api | rds | SQL | PostgreSQL |
| api | redis | Cache / broker | Redis |
| api | s3 | Media URLs | HTTPS |
| celery | redis | Task queue | Redis |
| api | cloudwatch | Logs | HTTPS |

### Mermaid overview

```mermaid
flowchart LR
    streaming-client([Web / mobile clients])
    alb{AWS ALB (TLS)}
    api[Music API (Docker/Gunicorn)]
    rds[(RDS PostgreSQL)]
    redis[/ElastiCache Redis/]
    s3[S3 + CloudFront (media)]
    celery[Celery worker (planned)]
    cloudwatch>CloudWatch logs]
    streaming-client -->|HTTPS| alb
    alb -->|Proxy| api
    api -->|SQL| rds
    api -->|Cache / broker| redis
    api -->|Media URLs| s3
    celery -->|Task queue| redis
    api -->|Logs| cloudwatch
```

## Data flow

### Request flow

1. **GraphQL request** — Client POSTs query/mutation to /graphql/ with optional Authorization header (JWT wiring pending).
2. **Django middleware** — Security, CORS, session, and auth middleware populate request.user on context.
3. **Resolver → service** — Graphene resolver calls domain service (e.g. RecommendationService.get_personalized_recommendations).
4. **ORM / NumPy** — PostgreSQL reads/writes; recommendation scoring uses NumPy on candidate samples.
5. **Typed response** — GraphQL serializes SongType, RecommendedSongType, or mutation success envelope to JSON.

### Event flow

1. **Play tracked** — track_play / play_song mutation records ListeningHistory for analytics and taste.
2. **Taste refresh (sync today)** — TasteProfileService.update_taste_profile runs when profile older than 7 days—could move to Celery.
3. **Recommendation rebuild** — Discover Weekly and radio seeds recomputed from updated UserTaste and history.
4. **Async processing (planned)** — Celery tasks in proccesign_service.py for audio analysis—not yet deployed in compose.

## Technical decisions

### GraphQL vs REST

**Problem:** Clients need flexible catalog queries (nested artist → albums → songs) without over-fetching.

**Solution:** Graphene-Django with per-app schema modules merged in config.schema; DRF kept for session browsable /api/.

**Outcome:** Single /graphql/ endpoint; portfolio docs still map operations to httpEndpoints for schema.ts compatibility.

#### Alternatives considered

- REST with nested serializers
- tRPC / OpenAPI-only

### PostgreSQL on RDS

**Problem:** Relational integrity for playlists, M2M song relations, and listening history at scale.

**Solution:** Production uses DATABASE_URL → RDS; local dev SQLite; Docker local uses compose Postgres.

**Outcome:** CONN_MAX_AGE 600 and health checks in production settings; aligns with existing AWS RDS deployment.

#### Alternatives considered

- SQLite in production
- Document store for catalog

### In-process NumPy scoring

**Problem:** Personalized recommendations need weighted scoring without standing up a separate ML service yet.

**Solution:** RecommendationService samples up to 500 candidates and scores with NumPy weights in the API process.

**Outcome:** Fast to demo; may need worker offload or vector DB as catalog grows past ~100k songs.

#### Alternatives considered

- Dedicated recommendation microservice
- Collaborative filtering offline batch

### Production container-only compose

**Problem:** RDS already exists in AWS—bundling Postgres in prod compose would duplicate managed infra.

**Solution:** docker-compose.prod.yml runs web only; DATABASE_URL points to RDS endpoint.

**Outcome:** Simple EC2/ECS deploy path; media and Redis still need explicit cloud wiring.

#### Alternatives considered

- ECS Fargate task definitions without compose
- Elastic Beanstalk

## Additional notes

# Architecture

> **AWS alignment:** Production assumes **RDS PostgreSQL is already provisioned**—the app container connects via `DATABASE_URL`, not an in-compose database service.

> **Dangerous:** GraphQL endpoint is **CSRF-exempt** and GraphiQL may expose full schema introspection—lock down in production (disable GraphiQL, restrict CORS, add rate limits).

> **Technical debt:** JWT middleware commented out in `config/settings/base.py`; login returns tokens but authenticated GraphQL may require session cookies until fixed. Celery broker not configured in settings despite celery in requirements.

