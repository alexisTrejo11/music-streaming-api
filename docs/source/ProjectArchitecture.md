---
layers:
  - name: "Presentation (clients)"
    description: "Web and mobile streaming clients consuming GraphQL over HTTPS."
    color: "#1DB954"
    expanded: true
    components:
      - "Streaming web app (React/Vue placeholder)"
      - "Mobile player (iOS/Android placeholder)"
      - "GraphiQL / admin for operators"
    responsibilities:
      - "Send GraphQL queries and mutations"
      - "Store JWT access/refresh tokens securely"
      - "Stream audio from CDN or media URLs returned by API"
    technologies:
      - "HTTPS"
      - "GraphQL JSON"
      - "Authorization: Bearer (when JWT middleware enabled)"

  - name: "Edge & gateway (AWS)"
    description: "TLS termination and routing to the containerized Django app."
    color: "#FF9900"
    expanded: false
    components:
      - "Application Load Balancer (ALB)"
      - "ACM TLS certificates"
      - "Security groups (443 → container 8000)"
    responsibilities:
      - "Terminate TLS and forward to Gunicorn"
      - "Health checks on /admin/login/ or custom path"
      - "Optional AWS WAF rate limiting"
    technologies:
      - "AWS ALB"
      - "ACM"
      - "Route 53 (placeholder)"

  - name: "Application layer"
    description: "Django 4 monolith with Graphene-Django schema merged from six domain apps."
    color: "#3776AB"
    expanded: true
    components:
      - "config.schema — merged Query/Mutation"
      - "apps/users — auth & preferences"
      - "apps/artists — artist catalog"
      - "apps/music — songs, albums, genres"
      - "apps/playlists — CRUD, collaborators, follows"
      - "apps/interactions — likes, reviews, history, analytics"
      - "apps/recommendations — taste, radio, Discover Weekly"
      - "apps/core — decorators, logging, base mutations"
    responsibilities:
      - "GraphQL resolvers delegate to service classes"
      - "Structured logging (JSON + audit files)"
      - "WhiteNoise static files in production"
    technologies:
      - "Graphene-Django"
      - "Django REST Framework"
      - "SimpleJWT"
      - "Gunicorn WSGI"

  - name: "Data layer"
    description: "Relational catalog and user data on managed PostgreSQL; optional Redis for cache/tasks."
    color: "#527FFF"
    expanded: true
    components:
      - "Amazon RDS PostgreSQL (production)"
      - "PostgreSQL 16 container (local Docker stack)"
      - "Redis 7 (local Docker; ElastiCache placeholder)"
    responsibilities:
      - "ACID storage for catalog, playlists, taste profiles"
      - "Listening history and play analytics"
      - "Future: cache hot catalog queries"
    technologies:
      - "psycopg2-binary"
      - "dj-database-url"

  - name: "Async & media (partial)"
    description: "Background processing and binary media—not fully wired for cloud yet."
    color: "#8B5CF6"
    expanded: false
    components:
      - "Celery shared tasks (song processing stub)"
      - "Local media/ volume or future S3 bucket"
      - "NumPy recommendation scoring (in-process)"
    responsibilities:
      - "Async audio processing (planned)"
      - "Album art and audio file storage"
    technologies:
      - "Celery"
      - "Pillow"
      - "NumPy"

designPatterns:
  - title: "Service layer"
    emoji: "🏗️"
    description: "Domain logic in *Service classes (AuthService, RecommendationService, PlaylistService) keeps GraphQL resolvers thin."
    category: "Structural"
    badge: "Core"
  - title: "Mixin composition (GraphQL)"
    emoji: "🧩"
    description: "Each app exports Query/Mutation mixins merged in config.schema — modular schema without microservices."
    category: "Structural"
    badge: "Graphene"
  - title: "BaseMutation envelope"
    emoji: "📦"
    description: "Mutations return { success, message, ...payload } via BaseMutation for consistent client handling."
    category: "Behavioral"
    badge: "API"
  - title: "Decorator — auth_required"
    emoji: "🔐"
    description: "@auth_required on mutations checks info.context.user before calling services."
    category: "Behavioral"
    badge: "Security"
  - title: "Strategy — recommendation scoring"
    emoji: "🎯"
    description: "RecommendationService weights genre, artist follow, audio features, and popularity with configurable reason objects."
    category: "Behavioral"
    badge: "Recommendations"
  - title: "Repository (Django ORM)"
    emoji: "🗄️"
    description: "Models and select_related/prefetch patterns encapsulate data access; services compose queries with transactions."
    category: "Data"
    badge: "Django"

scalabilityStrategies:
  - title: "Stateless API containers on ECS/EC2"
    description: "Scale Gunicorn workers per task; add ECS tasks or EC2 instances behind ALB when CPU or latency grows."
  - title: "Amazon RDS PostgreSQL"
    description: "Managed backups, storage autoscaling, optional read replicas for analytics-heavy recommendation rebuilds."
  - title: "Offload media to S3 + CloudFront"
    description: "Serve album art and audio from CDN; API returns signed URLs—required before horizontal media scaling."
  - title: "Async play telemetry"
    description: "Move play_count increments and taste-profile updates to Celery to keep GraphQL mutations fast under load."

securityStrategies:
  - title: "Password validation & JWT issuance"
    description: "Django validators plus AuthService rules; SimpleJWT access/refresh returned on register/login."
  - title: "auth_required on sensitive mutations"
    description: "Playlist edits, reviews, taste updates require authenticated context user."
  - title: "Production TLS & secure cookies"
    description: "SECURE_SSL_REDIRECT configurable when TLS terminates at ALB; secure session/CSRF cookies when enabled."
  - title: "Structured audit logging"
    description: "Dedicated audit logger with timed rotation and optional DatabaseLogHandler for errors."
  - title: "CSRF exempt GraphQL only"
    description: "GraphQLView is csrf_exempt—acceptable for token-based SPAs but requires strict CORS and auth."

cacheStrategies:
  - name: "Redis (local Docker stack)"
    description: "Redis 7 container in docker-compose.local.yml—ready for django-redis when configured"
    ttl: "TBD — not wired in settings yet"
    coverage: "Future: session cache, rate limits, Celery broker"
  - name: "UserTaste profile cache"
    description: "UserTaste model stores denormalized favorites; refreshed when last_updated > 7 days"
    ttl: "7 days"
    coverage: "Recommendation queries avoid full history scan on every request"
  - name: "ORM query optimization"
    description: "select_related on song → artist, album, genre in hot paths"
    ttl: "N/A"
    coverage: "Catalog list/search/resolvers"

architectureFeatures:
  - title: "Single merged GraphQL schema"
    emoji: "🔗"
    description: "One endpoint for catalog, social, and recommendations—clients fetch exactly the fields they need."
  - title: "Explainable recommendations"
    emoji: "💡"
    description: "RecommendedSongType includes score and reasons array for transparent UX."
  - title: "Rich interaction model"
    emoji: "❤️"
    description: "Likes, saves, reviews, follows, listening history feed taste and trending algorithms."
  - title: "Docker split local vs prod"
    emoji: "🐳"
    description: "Local stack bundles Postgres+Redis; prod compose expects cloud DATABASE_URL (RDS)."

architectureDiagram:
  legendItems:
    - type: "client"
      label: "Client"
      color: "#1DB954"
      icon: "monitor"
    - type: "gateway"
      label: "ALB"
      color: "#FF9900"
      icon: "shield"
    - type: "service"
      label: "API service"
      color: "#3776AB"
      icon: "server"
    - type: "database"
      label: "Database"
      color: "#527FFF"
      icon: "database"
    - type: "queue"
      label: "Cache / queue"
      color: "#8B5CF6"
      icon: "layers"
    - type: "monitoring"
      label: "Monitoring"
      color: "#64748B"
      icon: "activity"

  nodes:
    - id: "streaming-client"
      label: "Web / mobile clients"
      type: "client"
      x: 80
      y: 120
      connections: ["alb"]
      status: "healthy"
      traffic: 200
    - id: "alb"
      label: "AWS ALB (TLS)"
      type: "gateway"
      x: 280
      y: 120
      connections: ["api"]
      status: "healthy"
      traffic: 200
    - id: "api"
      label: "Music API (Docker/Gunicorn)"
      type: "service"
      x: 480
      y: 120
      connections: ["rds", "redis", "s3"]
      status: "healthy"
      traffic: 180
    - id: "rds"
      label: "RDS PostgreSQL"
      type: "database"
      x: 680
      y: 60
      connections: []
      status: "healthy"
      traffic: 120
    - id: "redis"
      label: "ElastiCache Redis"
      type: "queue"
      x: 680
      y: 180
      connections: []
      status: "warning"
      traffic: 0
    - id: "s3"
      label: "S3 + CloudFront (media)"
      type: "service"
      x: 480
      y: 260
      connections: []
      status: "warning"
      traffic: 40
    - id: "celery"
      label: "Celery worker (planned)"
      type: "service"
      x: 280
      y: 260
      connections: ["redis"]
      status: "warning"
      traffic: 10
    - id: "cloudwatch"
      label: "CloudWatch logs"
      type: "monitoring"
      x: 80
      y: 260
      connections: ["api"]
      status: "healthy"
      traffic: 5

  connections:
    - id: "c1"
      from: "streaming-client"
      to: "alb"
      label: "HTTPS"
      protocol: "TLS 1.2+"
      isActive: true
    - id: "c2"
      from: "alb"
      to: "api"
      label: "Proxy"
      protocol: "HTTP"
      isActive: true
    - id: "c3"
      from: "api"
      to: "rds"
      label: "SQL"
      protocol: "PostgreSQL"
      isActive: true
    - id: "c4"
      from: "api"
      to: "redis"
      label: "Cache / broker"
      protocol: "Redis"
      isActive: false
    - id: "c5"
      from: "api"
      to: "s3"
      label: "Media URLs"
      protocol: "HTTPS"
      isActive: false
    - id: "c6"
      from: "celery"
      to: "redis"
      label: "Task queue"
      protocol: "Redis"
      isActive: false
    - id: "c7"
      from: "api"
      to: "cloudwatch"
      label: "Logs"
      protocol: "HTTPS"
      isActive: true

dataFlow:
  requestFlow:
    - number: 1
      title: "GraphQL request"
      description: "Client POSTs query/mutation to /graphql/ with optional Authorization header (JWT wiring pending)."
      icon: "send"
    - number: 2
      title: "Django middleware"
      description: "Security, CORS, session, and auth middleware populate request.user on context."
      icon: "filter"
    - number: 3
      title: "Resolver → service"
      description: "Graphene resolver calls domain service (e.g. RecommendationService.get_personalized_recommendations)."
      icon: "cog"
    - number: 4
      title: "ORM / NumPy"
      description: "PostgreSQL reads/writes; recommendation scoring uses NumPy on candidate samples."
      icon: "database"
    - number: 5
      title: "Typed response"
      description: "GraphQL serializes SongType, RecommendedSongType, or mutation success envelope to JSON."
      icon: "reply"

  eventFlow:
    - number: 1
      title: "Play tracked"
      description: "track_play / play_song mutation records ListeningHistory for analytics and taste."
      icon: "zap"
    - number: 2
      title: "Taste refresh (sync today)"
      description: "TasteProfileService.update_taste_profile runs when profile older than 7 days—could move to Celery."
      icon: "refresh"
    - number: 3
      title: "Recommendation rebuild"
      description: "Discover Weekly and radio seeds recomputed from updated UserTaste and history."
      icon: "sparkles"
    - number: 4
      title: "Async processing (planned)"
      description: "Celery tasks in proccesign_service.py for audio analysis—not yet deployed in compose."
      icon: "clock"

techDecisions:
  decisions:
    - title: "GraphQL vs REST"
      problem: "Clients need flexible catalog queries (nested artist → albums → songs) without over-fetching."
      solution: "Graphene-Django with per-app schema modules merged in config.schema; DRF kept for session browsable /api/."
      alternatives:
        - "REST with nested serializers"
        - "tRPC / OpenAPI-only"
      outcome: "Single /graphql/ endpoint; portfolio docs still map operations to httpEndpoints for schema.ts compatibility."
      icon: "graphql"
    - title: "PostgreSQL on RDS"
      problem: "Relational integrity for playlists, M2M song relations, and listening history at scale."
      solution: "Production uses DATABASE_URL → RDS; local dev SQLite; Docker local uses compose Postgres."
      alternatives:
        - "SQLite in production"
        - "Document store for catalog"
      outcome: "CONN_MAX_AGE 600 and health checks in production settings; aligns with existing AWS RDS deployment."
      icon: "database"
    - title: "In-process NumPy scoring"
      problem: "Personalized recommendations need weighted scoring without standing up a separate ML service yet."
      solution: "RecommendationService samples up to 500 candidates and scores with NumPy weights in the API process."
      alternatives:
        - "Dedicated recommendation microservice"
        - "Collaborative filtering offline batch"
      outcome: "Fast to demo; may need worker offload or vector DB as catalog grows past ~100k songs."
      icon: "chart"
    - title: "Production container-only compose"
      problem: "RDS already exists in AWS—bundling Postgres in prod compose would duplicate managed infra."
      solution: "docker-compose.prod.yml runs web only; DATABASE_URL points to RDS endpoint."
      alternatives:
        - "ECS Fargate task definitions without compose"
        - "Elastic Beanstalk"
      outcome: "Simple EC2/ECS deploy path; media and Redis still need explicit cloud wiring."
      icon: "docker"
---

# Architecture

> **AWS alignment:** Production assumes **RDS PostgreSQL is already provisioned**—the app container connects via `DATABASE_URL`, not an in-compose database service.

> **Dangerous:** GraphQL endpoint is **CSRF-exempt** and GraphiQL may expose full schema introspection—lock down in production (disable GraphiQL, restrict CORS, add rate limits).

> **Technical debt:** JWT middleware commented out in `config/settings/base.py`; login returns tokens but authenticated GraphQL may require session cookies until fixed. Celery broker not configured in settings despite celery in requirements.
