# Music Streaming API

GraphQL-first backend for a Spotify-style music platform: catalog (artists, albums, songs), playlists, social interactions, listening history, and numpy-powered personalized recommendations. Deployed on AWS with Docker, RDS PostgreSQL, and optional ElastiCache Redis.

| Field | Value |
| --- | --- |
| Project ID | music-streaming-api |
| Version | 1.0.0 |
| Language | Python |
| Framework | Django + Graphene |
| Category | backend |
| Status | stable |
| Featured | Yes |
| Repository | https://github.com/alexisTrejo11/music-streaming-api |
| Live demo | https://api.music-streaming.example.com/graphql/ |
| Created | 2024-01-01T00:00:00.000Z |
| Updated | 2026-06-03T00:00:00.000Z |

## Tech stack

- Django 4.2.11
- Graphene-Django 3.2
- Django REST Framework 3.15
- SimpleJWT 5.3
- PostgreSQL (RDS in production)
- Redis 7 (local Docker stack; ElastiCache planned)
- Celery 5.3
- NumPy 1.26
- Gunicorn + WhiteNoise
- Docker multi-stage (Python 3.12 slim)

## Additional notes

# Project Metadata

> Portfolio metadata for the Music Streaming API. Replace `api.music-streaming.example.com` with your real ALB/domain when publishing. `liveDemoUrl` is a placeholder until a public deployment exists.

