# Project Overview

## Building a streaming backend without reinventing the catalog

Music apps need a unified catalog (artists, albums, songs with audio features), user libraries (playlists, likes, saves), listening telemetry, and personalization—all behind a single API that mobile and web clients can evolve against. Ad-hoc REST endpoints and duplicated business logic make that hard to ship and operate at scale.

### Pain points

- Catalog, playlists, and recommendations scattered across inconsistent endpoints
- No shared taste model—hard to explain why a song was recommended
- Play counts and history updated synchronously, blocking request threads
- Local dev on SQLite while production expects managed PostgreSQL on AWS
- Auth tokens issued but GraphQL context not wired for Bearer JWT in all environments

## One GraphQL API with domain apps and recommendation services

- **Unified GraphQL schema** — Six domain apps expose queries and mutations at `/graphql/` with GraphiQL for exploration—users, artists, music, playlists, interactions, recommendations.
- **Service-layer business rules** — AuthService, SongService, PlaylistService, RecommendationService, and TasteProfileService keep resolvers thin and testable.
- **Personalization with explanations** — NumPy-scored recommendations return reasons (genre match, followed artist, audio similarity) for Discover Weekly, radio, and mood playlists.
- **Docker-ready for AWS** — Local compose runs app + Postgres + Redis; production compose runs app only against external RDS via `DATABASE_URL`.
- **Structured portfolio docs** — YAML frontmatter in `docs/source/` matches `schema.ts` and renders to readable Markdown in `docs/generated/`.

## Platform snapshot

- 7 Django domain apps (users, core, artists, music, playlists, interactions, recommendations)
- Single GraphQL endpoint at /graphql/ (GraphiQL enabled)
- 105+ Python modules under apps/ (excluding migrations and tests)
- Docker image Python 3.12 slim, Gunicorn 2 workers × 2 threads
- Production DB via DATABASE_URL → Amazon RDS PostgreSQL

## Links

| Resource | URL |
| --- | --- |
| Github | https://github.com/alexisTrejo11/music-streaming-api |
| Demo | https://api.music-streaming.example.com/graphql/ |
| Documentation | https://github.com/alexisTrejo11/music-streaming-api/tree/main/docs/generated |
| Dockerhub | None |

## Music Streaming API — product views

Placeholder assets for portfolio presentation. Replace URLs with real GraphiQL screenshots, admin catalog views, or architecture diagrams from your AWS deployment.

### API cover

GraphQL backend for music catalog, playlists, and recommendations

- **Type:** image | **Category:** screenshot
- ![Music Streaming API branding placeholder](https://placehold.co/1200x630/1DB954/ffffff?text=Music+Streaming+API)

### GraphiQL explorer

Interactive schema browser at /graphql/ when DEBUG or graphiql=True

- **Type:** image | **Category:** demo
- ![GraphiQL placeholder](https://placehold.co/1200x800/191414/1DB954?text=GraphiQL)

## Additional media

### Cloud architecture

ECS/EC2 container → ALB → RDS PostgreSQL; Redis/ElastiCache optional for cache and Celery

### Docker deployment

docker-compose.prod.yml runs web only; DATABASE_URL points to RDS

## Metrics

| Label | Value | Description |
| --- | --- | --- |
| Django apps | 7 | users, core, artists, music, playlists, interactions, recommendations |
| API style | GraphQL | Primary entry POST/GET /graphql/ |
| Python (runtime image) | 3.12 | docker/Dockerfile multi-stage build |
| Auth tokens | JWT | SimpleJWT on register/login; Bearer wiring for GraphQL still TODO |

## Additional notes

# Overview

> **Audience:** Developers building a music streaming client (web/mobile) or evaluating this portfolio backend.

> **Highlight:** Recommendation engine returns **scored songs with human-readable reasons**—useful for UX transparency and demos.

> **Gaps before production go-live:** (1) Enable JWT middleware for GraphQL (`graphql_jwt` or custom `Authorization: Bearer` parsing)—tokens are issued but `info.context.user` defaults to session auth only. (2) Register `refresh_token` mutation in `apps/users/schema/__init__.py` (class exists, not exposed). (3) Wire Celery worker in production for async play-count updates (`proccesign_service.py` tasks exist). (4) Mount S3 + `django-storages` for `media/` on multi-node AWS deploys—local volume is single-node only. (5) Disable GraphiQL in production (`graphiql=False`) to reduce introspection exposure.

