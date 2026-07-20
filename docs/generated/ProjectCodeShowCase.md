# Code Showcase

## Explainable recommendation scoring

RecommendationService scores candidate songs with weighted factors and returns reason objects—ideal for 'Why this song?' UI.

**Category:** domain | **Duration:** 5 min read | **Tags:** recommendations, numpy, personalization

### recommendation_service.py

**Path:** `apps/recommendations/services/recommendation_service.py`

Samples up to 500 unknown songs, scores by genre, followed artists, audio features, and popularity.

```python
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
```

## Taste profile from listening history

TasteProfileService analyzes the last 90 days of plays to derive favorite genres and top artists stored on UserTaste.

**Category:** domain | **Duration:** 4 min read | **Tags:** analytics, taste

### taste_profile_service.py

**Path:** `apps/recommendations/services/taste_profile_service.py`

Uses last 200 plays to set favorite_genres M2M and top_artists; refreshes last_updated timestamp.

```python
recent_plays = ListeningHistory.objects.filter(
    user=user,
    played_at__gte=timezone.now() - timedelta(days=90),
).select_related("song__genre", "song__artist")[:200]
top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
taste.favorite_genres.set(favorite_genres)
```

## GraphQL authentication decorator

auth_required ensures mutations only run for authenticated users via info.context.user.

**Category:** security | **Duration:** 2 min read | **Tags:** graphql, auth

### decorators.py

**Path:** `apps/core/decorators.py`

Works with classmethod resolvers; raises PermissionDenied when user is anonymous.

```python
def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = args[2] if len(args) >= 3 else args[1]
        if not info.context.user.is_authenticated:
            raise PermissionDenied("Authentication required")
        return func(*args, **kwargs)
    return wrapper
```

## Consistent mutation responses

BaseMutation wraps service calls and returns success/message fields expected by GraphQL clients.

**Category:** api | **Duration:** 3 min read | **Tags:** graphql, patterns

### base_schema.py

**Path:** `apps/core/base_schema.py`

execute_service_method catches ValidationError and maps to failure_response.

```python
class BaseMutation(graphene.Mutation):
    success = graphene.Boolean(required=True)
    message = graphene.String()

    @classmethod
    def execute_service_method(cls, service_method, *args, **kwargs):
        try:
            return service_method(*args, **kwargs)
        except ValidationError as e:
            return cls.failure_response(message=str(e))
```

## Modular schema composition

config.schema merges Query and Mutation classes from every domain app into one deployable schema.

**Category:** api | **Duration:** 2 min read | **Tags:** architecture, graphql

### schema.py

**Path:** `config/schema.py`

Multiple inheritance on Query/Mutation keeps apps decoupled while exposing a single /graphql/ endpoint.

```python
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
```

## Additional notes

# Code Showcase

> Snippets are abbreviated from the repository; open the referenced paths for full scoring logic, tests, and edge cases.

> **Recommended reading order:** merged schema → auth decorator → taste profile → recommendation scoring.

> **Gap to explore:** `apps/music/services/proccesign_service.py` for Celery audio tasks once Redis broker is configured.

