# Project Features

## GraphQL music catalog

Songs, albums, genres, and audio features exposed via filterable queries—search, trending, artist/album listings, and single-song lookup by id or slug.

| Property | Value |
| --- | --- |
| ID | graphql-catalog |
| Category | api |
| Status | stable |
| Icon | music-note |

### Highlights

- Queries: song, allSongs, searchSongs, trendingSongs, artistSongs, albumSongs
- Mutations: createSong, updateSong, deleteSong, likeSong, playSong
- DjangoFilterConnectionField pagination on allSongs

### Tech stack

- graphene-django
- django-filter
- apps/music

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Default page size | 20 | stable |

## User registration & JWT auth

Email/username registration, login, profile and preferences updates, password change, and account deletion via GraphQL mutations backed by AuthService and SimpleJWT.

| Property | Value |
| --- | --- |
| ID | jwt-auth |
| Category | authentication |
| Status | beta |
| Icon | shield-lock |

### Highlights

- Mutations: registerUser, loginUser, updateProfile, changePassword
- Returns access_token + refresh_token in AuthPayloadType
- RefreshToken mutation implemented but NOT registered in schema __init__
- graphql_jwt middleware commented out—Bearer auth gap

### Tech stack

- djangorestframework-simplejwt
- apps/users

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Min password length | 8 chars | stable |

### Code snippet

_apps/users/services.py_

```python
refresh = RefreshToken.for_user(user)
return {
    "user": user,
    "access_token": str(refresh.access_token),
    "refresh_token": str(refresh),
}
```

## Playlists & collaboration

User playlists with public/private visibility, song ordering, follows, duplication, and collaborator management.

| Property | Value |
| --- | --- |
| ID | playlists-collab |
| Category | api |
| Status | stable |
| Icon | list-music |

### Highlights

- Queries: myPlaylists, featuredPlaylists, trendingPlaylists, searchPlaylists
- Mutations: createPlaylist, addSongToPlaylist, reorderPlaylistSongs
- Collaborators and playlist followers

### Tech stack

- apps/playlists

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Mutations | 11 | stable |

## Likes, reviews & listening history

Social layer: like/unlike songs, save albums, album reviews with helpful votes, play tracking, and listening history with analytics queries.

| Property | Value |
| --- | --- |
| ID | interactions-social |
| Category | integration |
| Status | stable |
| Icon | heart |

### Highlights

- trackPlay mutation feeds recommendation taste model
- Reviews with add/update/delete and markReviewHelpful
- Analytics queries for user listening stats

### Tech stack

- apps/interactions

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| History retention | Configurable | stable |

## Personalized recommendations

NumPy-weighted scoring with explainable reasons, Discover Weekly, artist/album suggestions, mood playlists, custom radio stations, and taste profiles.

| Property | Value |
| --- | --- |
| ID | recommendations-engine |
| Category | performance |
| Status | stable |
| Icon | sparkles |

### Highlights

- recommendedSongs returns score + reasons[]
- discoverWeekly, songsByMood, trendingForYou
- UserTaste auto-refresh after 7 days
- Anonymous users get popular/trending fallbacks

### Tech stack

- numpy
- apps/recommendations

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Candidate sample | 500 songs | stable |

### Code snippet

_apps/recommendations/services/recommendation_service.py_

```python
if song.genre_id in favorite_genres:
    score += 0.3
    reasons.append({
        "type": "genre_match",
        "description": f"Matches your favorite genre: {song.genre.name}",
    })
```

## Artist management

Artist profiles with members, genres, social links, search, and CRUD mutations for catalog operators.

| Property | Value |
| --- | --- |
| ID | artist-catalog |
| Category | api |
| Status | stable |
| Icon | user-music |

### Highlights

- Public artist browse and detail queries
- createArtist, updateArtist, addArtistMember mutations
- Follow artist mutations commented out in schema

### Tech stack

- apps/artists

## JSON & audit logging

Rotating file handlers, JSON logs for ELK-style ingestion, audit trail, and optional DB error handler.

| Property | Value |
| --- | --- |
| ID | structured-logging |
| Category | monitoring |
| Status | stable |
| Icon | file-text |

### Highlights

- ExcludeSensitiveFilter on log output
- Separate errors.log, audit.log, celery.log
- CloudWatch agent can tail /app/logs in ECS

### Tech stack

- apps/core/logging

## Docker production image

Multi-stage Python 3.12 image, non-root user, migrate-on-start, WhiteNoise static files, health check, prod compose for RDS.

| Property | Value |
| --- | --- |
| ID | docker-aws-deploy |
| Category | integration |
| Status | stable |
| Icon | docker |

### Highlights

- docker-compose.prod.yml — web only, external RDS
- docker-compose.local.yml — postgres + redis + reload
- COLLECT_STATIC=true runs collectstatic on boot

### Tech stack

- Docker
- Gunicorn
- WhiteNoise

## Background tasks (partial)

Celery in requirements with shared tasks for audio processing; broker not configured and workers not in compose.

| Property | Value |
| --- | --- |
| ID | celery-stub |
| Category | messaging |
| Status | experimental |
| Icon | clock |

### Highlights

- proccesign_service.py defines @shared_task stubs
- Play count still updated synchronously (TODO in SongService)
- Needs Redis/ElastiCache broker URL in settings

### Tech stack

- Celery
- Redis (planned)

## Additional notes

# Project Features

> **Stable:** Catalog, playlists, interactions, and recommendation queries are covered by schema tests under `apps/*/tests/`.

> **Beta:** JWT auth—tokens are minted on login but GraphQL Bearer middleware is not enabled; verify auth behavior before shipping a SPA.

> **Experimental:** Celery audio processing and cloud Redis—code paths exist but infra wiring is incomplete.

> **Before AWS production:** Disable GraphiQL, enable JWT context middleware, point media to S3, add ElastiCache + Celery worker ECS service.

