---
problemStatement:
  problemTitle: "Building a streaming backend without reinventing the catalog"
  problemDescription: "Music apps need a unified catalog (artists, albums, songs with audio features), user libraries (playlists, likes, saves), listening telemetry, and personalization—all behind a single API that mobile and web clients can evolve against. Ad-hoc REST endpoints and duplicated business logic make that hard to ship and operate at scale."
  problemList:
    - "Catalog, playlists, and recommendations scattered across inconsistent endpoints"
    - "No shared taste model—hard to explain why a song was recommended"
    - "Play counts and history updated synchronously, blocking request threads"
    - "Local dev on SQLite while production expects managed PostgreSQL on AWS"
    - "Auth tokens issued but GraphQL context not wired for Bearer JWT in all environments"

solution:
  solutionTitle: "One GraphQL API with domain apps and recommendation services"
  solutionList:
    - title: "Unified GraphQL schema"
      description: "Six domain apps expose queries and mutations at `/graphql/` with GraphiQL for exploration—users, artists, music, playlists, interactions, recommendations."
    - title: "Service-layer business rules"
      description: "AuthService, SongService, PlaylistService, RecommendationService, and TasteProfileService keep resolvers thin and testable."
    - title: "Personalization with explanations"
      description: "NumPy-scored recommendations return reasons (genre match, followed artist, audio similarity) for Discover Weekly, radio, and mood playlists."
    - title: "Docker-ready for AWS"
      description: "Local compose runs app + Postgres + Redis; production compose runs app only against external RDS via `DATABASE_URL`."
    - title: "Structured portfolio docs"
      description: "YAML frontmatter in `docs/source/` matches `schema.ts` and renders to readable Markdown in `docs/generated/`."

keyMetrics:
  metricsTitle: "Platform snapshot"
  metricsList:
    - "7 Django domain apps (users, core, artists, music, playlists, interactions, recommendations)"
    - "Single GraphQL endpoint at /graphql/ (GraphiQL enabled)"
    - "105+ Python modules under apps/ (excluding migrations and tests)"
    - "Docker image Python 3.12 slim, Gunicorn 2 workers × 2 threads"
    - "Production DB via DATABASE_URL → Amazon RDS PostgreSQL"

links:
  github: "https://github.com/alexisTrejo11/music-streaming-api"
  demo: "https://api.music-streaming.example.com/graphql/"
  documentation: "https://github.com/alexisTrejo11/music-streaming-api/tree/main/docs/generated"
  dockerHub: null

mediaGallery:
  title: "Music Streaming API — product views"
  description: "Placeholder assets for portfolio presentation. Replace URLs with real GraphiQL screenshots, admin catalog views, or architecture diagrams from your AWS deployment."
  items:
    - type: "image"
      url: "https://placehold.co/1200x630/1DB954/ffffff?text=Music+Streaming+API"
      thumbnail: "https://placehold.co/400x210/1DB954/ffffff?text=Music+API"
      title: "API cover"
      description: "GraphQL backend for music catalog, playlists, and recommendations"
      alt: "Music Streaming API branding placeholder"
      category: "screenshot"
    - type: "image"
      url: "https://placehold.co/1200x800/191414/1DB954?text=GraphiQL"
      thumbnail: "https://placehold.co/400x267/191414/1DB954?text=GraphiQL"
      title: "GraphiQL explorer"
      description: "Interactive schema browser at /graphql/ when DEBUG or graphiql=True"
      alt: "GraphiQL placeholder"
      category: "demo"

mediaItems:
  - type: "image"
    url: "https://placehold.co/800x500/232F3E/FF9900?text=AWS+Architecture"
    thumbnail: "https://placehold.co/320x200/232F3E/FF9900?text=AWS"
    title: "Cloud architecture"
    description: "ECS/EC2 container → ALB → RDS PostgreSQL; Redis/ElastiCache optional for cache and Celery"
    alt: "AWS architecture placeholder"
    category: "architecture"
  - type: "image"
    url: "https://placehold.co/800x500/2496ED/ffffff?text=Docker+Deploy"
    thumbnail: "https://placehold.co/320x200/2496ED/ffffff?text=Docker"
    title: "Docker deployment"
    description: "docker-compose.prod.yml runs web only; DATABASE_URL points to RDS"
    alt: "Docker deployment placeholder"
    category: "diagram"

metrics:
  - label: "Django apps"
    value: "7"
    description: "users, core, artists, music, playlists, interactions, recommendations"
  - label: "API style"
    value: "GraphQL"
    description: "Primary entry POST/GET /graphql/"
  - label: "Python (runtime image)"
    value: "3.12"
    description: "docker/Dockerfile multi-stage build"
  - label: "Auth tokens"
    value: "JWT"
    description: "SimpleJWT on register/login; Bearer wiring for GraphQL still TODO"
---

# Overview

> **Audience:** Developers building a music streaming client (web/mobile) or evaluating this portfolio backend.

> **Highlight:** Recommendation engine returns **scored songs with human-readable reasons**—useful for UX transparency and demos.

> **Gaps before production go-live:** (1) Enable JWT middleware for GraphQL (`graphql_jwt` or custom `Authorization: Bearer` parsing)—tokens are issued but `info.context.user` defaults to session auth only. (2) Register `refresh_token` mutation in `apps/users/schema/__init__.py` (class exists, not exposed). (3) Wire Celery worker in production for async play-count updates (`proccesign_service.py` tasks exist). (4) Mount S3 + `django-storages` for `media/` on multi-node AWS deploys—local volume is single-node only. (5) Disable GraphiQL in production (`graphiql=False`) to reduce introspection exposure.
