---
features:
  - id: "graphql-catalog"
    title: "GraphQL music catalog"
    description: "Songs, albums, genres, and audio features exposed via filterable queries—search, trending, artist/album listings, and single-song lookup by id or slug."
    icon: "music-note"
    category: "api"
    status: "stable"
    highlights:
      - "Queries: song, allSongs, searchSongs, trendingSongs, artistSongs, albumSongs"
      - "Mutations: createSong, updateSong, deleteSong, likeSong, playSong"
      - "DjangoFilterConnectionField pagination on allSongs"
    techStack:
      - "graphene-django"
      - "django-filter"
      - "apps/music"
    metrics:
      - label: "Default page size"
        value: "20"
        trend: "stable"
        icon: "list"

  - id: "jwt-auth"
    title: "User registration & JWT auth"
    description: "Email/username registration, login, profile and preferences updates, password change, and account deletion via GraphQL mutations backed by AuthService and SimpleJWT."
    icon: "shield-lock"
    category: "authentication"
    status: "beta"
    highlights:
      - "Mutations: registerUser, loginUser, updateProfile, changePassword"
      - "Returns access_token + refresh_token in AuthPayloadType"
      - "RefreshToken mutation implemented but NOT registered in schema __init__"
      - "graphql_jwt middleware commented out—Bearer auth gap"
    techStack:
      - "djangorestframework-simplejwt"
      - "apps/users"
    metrics:
      - label: "Min password length"
        value: "8 chars"
        trend: "stable"
        icon: "key"
    codeSnippet:
      language: "python"
      filename: "apps/users/services.py"
      code: |
        refresh = RefreshToken.for_user(user)
        return {
            "user": user,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

  - id: "playlists-collab"
    title: "Playlists & collaboration"
    description: "User playlists with public/private visibility, song ordering, follows, duplication, and collaborator management."
    icon: "list-music"
    category: "api"
    status: "stable"
    highlights:
      - "Queries: myPlaylists, featuredPlaylists, trendingPlaylists, searchPlaylists"
      - "Mutations: createPlaylist, addSongToPlaylist, reorderPlaylistSongs"
      - "Collaborators and playlist followers"
    techStack:
      - "apps/playlists"
    metrics:
      - label: "Mutations"
        value: "11"
        trend: "stable"
        icon: "edit"

  - id: "interactions-social"
    title: "Likes, reviews & listening history"
    description: "Social layer: like/unlike songs, save albums, album reviews with helpful votes, play tracking, and listening history with analytics queries."
    icon: "heart"
    category: "integration"
    status: "stable"
    highlights:
      - "trackPlay mutation feeds recommendation taste model"
      - "Reviews with add/update/delete and markReviewHelpful"
      - "Analytics queries for user listening stats"
    techStack:
      - "apps/interactions"
    metrics:
      - label: "History retention"
        value: "Configurable"
        trend: "stable"
        icon: "clock"

  - id: "recommendations-engine"
    title: "Personalized recommendations"
    description: "NumPy-weighted scoring with explainable reasons, Discover Weekly, artist/album suggestions, mood playlists, custom radio stations, and taste profiles."
    icon: "sparkles"
    category: "performance"
    status: "stable"
    highlights:
      - "recommendedSongs returns score + reasons[]"
      - "discoverWeekly, songsByMood, trendingForYou"
      - "UserTaste auto-refresh after 7 days"
      - "Anonymous users get popular/trending fallbacks"
    techStack:
      - "numpy"
      - "apps/recommendations"
    metrics:
      - label: "Candidate sample"
        value: "500 songs"
        trend: "stable"
        icon: "target"
    codeSnippet:
      language: "python"
      filename: "apps/recommendations/services/recommendation_service.py"
      code: |
        if song.genre_id in favorite_genres:
            score += 0.3
            reasons.append({
                "type": "genre_match",
                "description": f"Matches your favorite genre: {song.genre.name}",
            })

  - id: "artist-catalog"
    title: "Artist management"
    description: "Artist profiles with members, genres, social links, search, and CRUD mutations for catalog operators."
    icon: "user-music"
    category: "api"
    status: "stable"
    highlights:
      - "Public artist browse and detail queries"
      - "createArtist, updateArtist, addArtistMember mutations"
      - "Follow artist mutations commented out in schema"
    techStack:
      - "apps/artists"

  - id: "structured-logging"
    title: "JSON & audit logging"
    description: "Rotating file handlers, JSON logs for ELK-style ingestion, audit trail, and optional DB error handler."
    icon: "file-text"
    category: "monitoring"
    status: "stable"
    highlights:
      - "ExcludeSensitiveFilter on log output"
      - "Separate errors.log, audit.log, celery.log"
      - "CloudWatch agent can tail /app/logs in ECS"
    techStack:
      - "apps/core/logging"

  - id: "docker-aws-deploy"
    title: "Docker production image"
    description: "Multi-stage Python 3.12 image, non-root user, migrate-on-start, WhiteNoise static files, health check, prod compose for RDS."
    icon: "docker"
    category: "integration"
    status: "stable"
    highlights:
      - "docker-compose.prod.yml — web only, external RDS"
      - "docker-compose.local.yml — postgres + redis + reload"
      - "COLLECT_STATIC=true runs collectstatic on boot"
    techStack:
      - "Docker"
      - "Gunicorn"
      - "WhiteNoise"

  - id: "celery-stub"
    title: "Background tasks (partial)"
    description: "Celery in requirements with shared tasks for audio processing; broker not configured and workers not in compose."
    icon: "clock"
    category: "messaging"
    status: "experimental"
    highlights:
      - "proccesign_service.py defines @shared_task stubs"
      - "Play count still updated synchronously (TODO in SongService)"
      - "Needs Redis/ElastiCache broker URL in settings"
    techStack:
      - "Celery"
      - "Redis (planned)"
---

# Project Features

> **Stable:** Catalog, playlists, interactions, and recommendation queries are covered by schema tests under `apps/*/tests/`.

> **Beta:** JWT auth—tokens are minted on login but GraphQL Bearer middleware is not enabled; verify auth behavior before shipping a SPA.

> **Experimental:** Celery audio processing and cloud Redis—code paths exist but infra wiring is incomplete.

> **Before AWS production:** Disable GraphiQL, enable JWT context middleware, point media to S3, add ElastiCache + Celery worker ECS service.
