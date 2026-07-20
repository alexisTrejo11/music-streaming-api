# Music Streaming API

GraphQL backend for a Spotify-style music platform—catalog, playlists, social interactions, and explainable recommendations. Deployed on AWS with Docker and Amazon RDS PostgreSQL.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 4.2](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![GraphQL](https://img.shields.io/badge/API-GraphQL-e10098.svg)](https://graphql.org/)

---

## Table of contents

- [About](#about)
- [Features](#features)
- [Documentation](#documentation)
- [Tech stack](#tech-stack)
- [Architecture at a glance](#architecture-at-a-glance)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Project structure](#project-structure)
- [Deployment](#deployment)
- [Testing](#testing)
- [Maintaining documentation](#maintaining-documentation)
- [Contributing](#contributing)
- [Security & compliance](#security--compliance)
- [License](#license)

---

## About

This project is a **Django + Graphene** backend for streaming music applications. It exposes a unified GraphQL schema for artists, albums, songs, user playlists, likes and reviews, listening history, and NumPy-powered personalized recommendations with human-readable “why this song” reasons.

The production deployment model targets **AWS**: the application runs in Docker (EC2 or ECS) behind an ALB, with **Amazon RDS PostgreSQL** as the managed database (`DATABASE_URL`). Local development uses SQLite or a Docker Compose stack with bundled Postgres and Redis.

| | |
|---|---|
| **Version** | 1.0.0 |
| **Status** | Stable (core GraphQL paths); JWT GraphQL middleware still TODO |
| **Primary API** | `POST /graphql/` |
| **GraphiQL (dev)** | [http://127.0.0.1:8000/graphql/](http://127.0.0.1:8000/graphql/) |
| **Admin** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |

---

## Features

Short list for the README; full detail lives in generated docs.

- **GraphQL catalog** — songs, albums, genres, search, trending, likes, and play tracking
- **Playlists** — CRUD, collaborators, follows, reordering, and duplication
- **Recommendations** — personalized songs with scores/reasons, Discover Weekly, mood, radio, taste profiles
- **Docker + AWS** — prod compose runs app only against external RDS; local compose includes Postgres + Redis

See [Project Features](docs/generated/ProjectFeature.md) for the complete feature breakdown.

---

## Documentation

This repository keeps **structured source** in `docs/source/` (YAML frontmatter + notes) and **human-readable docs** in `docs/generated/`, produced by `docs/yaml_to_markdown.py`. The TypeScript contract for portfolio tools is [`docs/source/schema.ts`](docs/source/schema.ts).

### Documentation index

| Document | What you will find | Read |
|----------|-------------------|------|
| **Overview** | Problem, solution, metrics, links | [ProjectOverview.md](docs/generated/ProjectOverview.md) |
| **Metadata** | Project id, version, tech stack, URLs | [ProjectMetadata.md](docs/generated/ProjectMetadata.md) |
| **API schema** | GraphQL operations, auth, examples | [APISchema.md](docs/generated/APISchema.md) |
| **Architecture** | Layers, patterns, diagram, data flows | [ProjectArchitecture.md](docs/generated/ProjectArchitecture.md) |
| **Infrastructure** | Docker, ECS/EC2, RDS, Redis, cloud services | [ProjectInfrastructure.md](docs/generated/ProjectInfrastructure.md) |
| **Features** | Feature cards, snippets, status per area | [ProjectFeature.md](docs/generated/ProjectFeature.md) |
| **Code showcase** | Curated code examples from the codebase | [ProjectCodeShowCase.md](docs/generated/ProjectCodeShowCase.md) |
| **Generated index** | Auto-generated hub linking all of the above | [docs/generated/README.md](docs/generated/README.md) |

### Source vs generated

| Path | Purpose |
|------|---------|
| `docs/source/*.md` | Edit YAML frontmatter here (machine-friendly, matches `schema.ts`) |
| `docs/generated/*.md` | Read here on GitHub / in the IDE (do not edit by hand) |
| `docs/yaml_to_markdown.py` | Regenerates `docs/generated/` from `docs/source/` |

```bash
pip install pyyaml
python docs/yaml_to_markdown.py
```

---

## Tech stack

- **Runtime:** Python 3.12, Django 4.2.11
- **API:** Graphene-Django 3.2 (GraphQL), Django REST Framework (secondary)
- **Auth:** SimpleJWT (tokens on login/register; GraphQL Bearer middleware pending)
- **Database:** SQLite (local dev), PostgreSQL on Amazon RDS (production)
- **Cache / tasks:** Redis in local Docker stack; ElastiCache + Celery planned
- **ML / scoring:** NumPy in recommendation services
- **Deploy:** Docker multi-stage image, Gunicorn, WhiteNoise, AWS ALB + RDS

---

## Architecture at a glance

Clients call **GraphQL over HTTPS** through an AWS ALB into a Gunicorn/Django container. The app reads and writes catalog and user data on **RDS PostgreSQL**. Media files and async workers (Celery) are planned for S3 and ElastiCache respectively.

```mermaid
flowchart LR
  Client[Web / mobile clients] --> ALB[AWS ALB]
  ALB --> API[Django GraphQL in Docker]
  API --> RDS[(Amazon RDS PostgreSQL)]
  API --> Redis[(ElastiCache Redis — planned)]
  API --> S3[S3 + CloudFront media — planned]
```

Full diagram, layers, and decisions: [ProjectArchitecture.md](docs/generated/ProjectArchitecture.md).

---

## Prerequisites

- Python 3.12+
- pip / venv
- Docker & Docker Compose v2 (recommended)
- PostgreSQL via RDS for production (SQLite OK for bare-metal local dev)
- NumPy-compatible environment (included in `requirements.txt`)

---

## Quick start

### Local development (SQLite)

```bash
git clone https://github.com/alexisTrejo11/music-streaming-api
cd music-streaming-api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- GraphiQL: http://127.0.0.1:8000/graphql/
- Admin: http://127.0.0.1:8000/admin/

### Docker (local full stack)

```bash
cp .env.example .env
docker compose -f docker/docker-compose.local.yml --project-directory . up --build
```

See [docker/README.md](docker/README.md) for compose details.

### Docker (production / cloud — RDS)

```bash
cp .env.example .env
# Set DATABASE_URL=postgresql://USER:PASS@your-db.rds.amazonaws.com:5432/dbname
# Set DEBUG=False, SECRET_KEY, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS
docker compose -f docker/docker-compose.prod.yml --project-directory . up -d --build
```

Details: [ProjectInfrastructure.md](docs/generated/ProjectInfrastructure.md).

---

## Configuration

Copy [`.env.example`](.env.example) to `.env`.

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret (required) |
| `DEBUG` | `False` in production |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` / `docker` / `production` |
| `DATABASE_URL` | Full PostgreSQL URL for production/RDS (see `.env.example`) |
| `ALLOWED_HOSTS` | Comma-separated domains |
| `CORS_ALLOWED_ORIGINS` | Frontend origins for GraphQL clients |
| `WEB_PORT` | Host port mapped to container 8000 |
| `SECURE_SSL_REDIRECT` | Enable when TLS terminates at the app (usually `False` behind ALB) |

Full Docker variable reference: [docker/README.md](docker/README.md).

---

## API overview

| Area | GraphQL operations | Doc |
|------|-------------------|-----|
| Auth | `registerUser`, `loginUser`, `me`, `updateProfile` | [APISchema.md](docs/generated/APISchema.md#auth) |
| Music | `searchSongs`, `trendingSongs`, `song`, `playSong` | [APISchema.md](docs/generated/APISchema.md#music) |
| Playlists | `myPlaylists`, `createPlaylist`, `addSongToPlaylist` | [APISchema.md](docs/generated/APISchema.md#playlists) |
| Recommendations | `recommendedSongs`, `discoverWeekly`, `createRadio` | [APISchema.md](docs/generated/APISchema.md#recommendations) |
| Artists | `searchArtists`, `artist`, `createArtist` | [APISchema.md](docs/generated/APISchema.md#artists) |
| Interactions | `trackPlay`, `addReview`, `likedSongs` | [APISchema.md](docs/generated/APISchema.md#interactions) |

All operations use **`POST /graphql/`** with a JSON `{ "query": "...", "variables": {} }` body. Explore the schema in GraphiQL during development.

---

## Project structure

```
music-streaming-api/
├── apps/
│   ├── users/            # Auth, profiles, preferences
│   ├── artists/          # Artist catalog
│   ├── music/            # Songs, albums, genres
│   ├── playlists/        # Playlists & collaboration
│   ├── interactions/     # Likes, reviews, history
│   ├── recommendations/  # Taste, radio, Discover Weekly
│   └── core/             # Decorators, logging, base mutations
├── config/               # Settings, urls, merged GraphQL schema
├── docker/               # Dockerfile, compose, entrypoint
├── docs/
│   ├── source/           # YAML source docs (edit these)
│   ├── generated/        # Readable Markdown (generated)
│   └── yaml_to_markdown.py
├── requirements.txt
└── manage.py
```

---

## Deployment

Production runs the **web container only** (`docker/docker-compose.prod.yml`). Point `DATABASE_URL` at your **existing Amazon RDS** PostgreSQL instance, place TLS on an **ALB**, and set `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` for your domain. Plan separate work for S3 media, ElastiCache Redis, Celery workers, and JWT GraphQL middleware before high-traffic launch.

Details: [ProjectInfrastructure.md](docs/generated/ProjectInfrastructure.md).

---

## Testing

```bash
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py test
```

Schema and service tests live under `apps/*/tests/`.

---

## Maintaining documentation

1. Edit YAML in `docs/source/<Section>.md` (keep fields aligned with [`docs/source/schema.ts`](docs/source/schema.ts)).
2. Run `python docs/yaml_to_markdown.py`.
3. Commit both `docs/source/` and `docs/generated/` so docs render on GitHub without running the script.

Optional notes that are not part of the schema (warnings, TODOs) go in the **Markdown body** below the closing `---` in each source file—they appear under **Additional notes** in generated files.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit with clear messages
4. Open a pull request

Issues and PRs welcome via [GitHub](https://github.com/alexisTrejo11/music-streaming-api).

---

## Security & compliance

Do not commit `.env` or RDS credentials. Disable GraphiQL and restrict CORS in production. JWT tokens are issued on login but **Bearer authentication for GraphQL is not fully wired**—treat session-based GraphiQL testing and token-based SPA clients differently until middleware is added. Report vulnerabilities privately to the repository owner.

---

## License

MIT License — see [LICENSE](LICENSE) file.

---

## Links

| Resource | URL |
|----------|-----|
| Repository | [github.com/alexisTrejo11/music-streaming-api](https://github.com/alexisTrejo11/music-streaming-api) |
| Documentation hub | [docs/generated/README.md](docs/generated/README.md) |
| Docker guide | [docker/README.md](docker/README.md) |
| GraphiQL (local) | [http://127.0.0.1:8000/graphql/](http://127.0.0.1:8000/graphql/) |
