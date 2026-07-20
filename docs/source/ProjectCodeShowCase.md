---
codeExamples:
  - id: "recommendation-scoring"
    title: "Explainable recommendation scoring"
    description: "RecommendationService scores candidate songs with weighted factors and returns reason objects—ideal for 'Why this song?' UI."
    category: "domain"
    duration: "5 min read"
    views: 0
    tags:
      - "recommendations"
      - "numpy"
      - "personalization"
    files:
      - name: "recommendation_service.py"
        path: "apps/recommendations/services/recommendation_service.py"
        language: "python"
        highlighted: true
        explanation: "Samples up to 500 unknown songs, scores by genre, followed artists, audio features, and popularity."
        content: |
          class RecommendationService(BaseRecommendationService):
              @staticmethod
              def get_personalized_recommendations(user, limit: int = 30) -> List[Dict]:
                  taste, _ = UserTaste.objects.get_or_create(user=user)
                  if not taste.last_updated or (timezone.now() - taste.last_updated) > timedelta(days=7):
                      TasteProfileService.update_taste_profile(user)
                  candidates = Song.objects.exclude(id__in=known_song_ids)
                  sample_size = min(500, candidates.count())
                  for song in candidates.order_by("?")[:sample_size]:
                      score = 0.0
                      reasons = []
                      if song.genre_id in favorite_genres:
                          score += 0.3
                          reasons.append({"type": "genre_match", "description": "..."})

  - id: "taste-profile"
    title: "Taste profile from listening history"
    description: "TasteProfileService analyzes the last 90 days of plays to derive favorite genres and top artists stored on UserTaste."
    category: "domain"
    duration: "4 min read"
    views: 0
    tags:
      - "analytics"
      - "taste"
    files:
      - name: "taste_profile_service.py"
        path: "apps/recommendations/services/taste_profile_service.py"
        language: "python"
        highlighted: true
        explanation: "Uses last 200 plays to set favorite_genres M2M and top_artists; refreshes last_updated timestamp."
        content: |
          recent_plays = ListeningHistory.objects.filter(
              user=user,
              played_at__gte=timezone.now() - timedelta(days=90),
          ).select_related("song__genre", "song__artist")[:200]
          top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
          taste.favorite_genres.set(favorite_genres)

  - id: "graphql-auth-decorator"
    title: "GraphQL authentication decorator"
    description: "auth_required ensures mutations only run for authenticated users via info.context.user."
    category: "security"
    duration: "2 min read"
    views: 0
    tags:
      - "graphql"
      - "auth"
    files:
      - name: "decorators.py"
        path: "apps/core/decorators.py"
        language: "python"
        highlighted: true
        explanation: "Works with classmethod resolvers; raises PermissionDenied when user is anonymous."
        content: |
          def auth_required(func):
              @wraps(func)
              def wrapper(*args, **kwargs):
                  info = args[2] if len(args) >= 3 else args[1]
                  if not info.context.user.is_authenticated:
                      raise PermissionDenied("Authentication required")
                  return func(*args, **kwargs)
              return wrapper

  - id: "base-mutation-envelope"
    title: "Consistent mutation responses"
    description: "BaseMutation wraps service calls and returns success/message fields expected by GraphQL clients."
    category: "api"
    duration: "3 min read"
    views: 0
    tags:
      - "graphql"
      - "patterns"
    files:
      - name: "base_schema.py"
        path: "apps/core/base_schema.py"
        language: "python"
        highlighted: true
        explanation: "execute_service_method catches ValidationError and maps to failure_response."
        content: |
          class BaseMutation(graphene.Mutation):
              success = graphene.Boolean(required=True)
              message = graphene.String()

              @classmethod
              def execute_service_method(cls, service_method, *args, **kwargs):
                  try:
                      return service_method(*args, **kwargs)
                  except ValidationError as e:
                      return cls.failure_response(message=str(e))

  - id: "merged-graphql-schema"
    title: "Modular schema composition"
    description: "config.schema merges Query and Mutation classes from every domain app into one deployable schema."
    category: "api"
    duration: "2 min read"
    views: 0
    tags:
      - "architecture"
      - "graphql"
    files:
      - name: "schema.py"
        path: "config/schema.py"
        language: "python"
        highlighted: true
        explanation: "Multiple inheritance on Query/Mutation keeps apps decoupled while exposing a single /graphql/ endpoint."
        content: |
          class Query(
              artists_schema.Query,
              music_schema.Query,
              users_schema.Query,
              playlists_schema.Query,
              interactions_schema.Query,
              recommendations_schema.Query,
              graphene.ObjectType,
          ):
              pass

          schema = graphene.Schema(query=Query, mutation=Mutation)
---

# Code Showcase

> Snippets are abbreviated from the repository; open the referenced paths for full scoring logic, tests, and edge cases.

> **Recommended reading order:** merged schema → auth decorator → taste profile → recommendation scoring.

> **Gap to explore:** `apps/music/services/proccesign_service.py` for Celery audio tasks once Redis broker is configured.
