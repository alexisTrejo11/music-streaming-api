# API Schema

**API type:** GraphQL

## Artists

### `POST` /graphql/

**Query: searchArtists**

Search artist catalog by name.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Public — 30/min per IP (placeholder) |
| **Tags** | artists |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "query($q: String!) { searchArtists(query: $q, limit: 10) { id name slug } }",
  "variables": {
    "q": "miles"
  }
}
```

#### Responses

- **200** — Artist results

```json
{
  "data": {
    "searchArtists": [
      {
        "id": "1",
        "name": "Miles Davis",
        "slug": "miles-davis"
      }
    ]
  }
}
```

---

## Auth

### `POST` /graphql/

**Mutation: registerUser**

Create account with email, username, password. Returns AuthPayloadType with JWT tokens.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Placeholder — 10/min per IP recommended |
| **Tags** | auth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "query": "mutation Register($input: RegisterInput!) { registerUser(input: $input) { success message authPayload { accessToken refreshToken user { id email username } } } }",
  "variables": {
    "input": {
      "email": "string",
      "username": "string",
      "password": "string",
      "firstName": "string",
      "lastName": "string"
    }
  }
}
```

**Example:**

```json
{
  "query": "mutation($input: RegisterInput!) { registerUser(input: $input) { success message } }",
  "variables": {
    "input": {
      "email": "listener@example.com",
      "username": "listener42",
      "password": "SecurePass123!",
      "firstName": "Alex",
      "lastName": "Listener"
    }
  }
}
```

#### Responses

- **200** — Registration result

```json
{
  "data": {
    "registerUser": {
      "success": true,
      "message": "Registration successful"
    }
  }
}
```

---

### `POST` /graphql/

**Mutation: loginUser**

Authenticate with email and password; returns access and refresh JWT tokens.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Placeholder — 5/min per email recommended |
| **Tags** | auth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "query": "mutation Login($input: LoginInput!) { loginUser(input: $input) { success authPayload { accessToken refreshToken } } }"
}
```

**Example:**

```json
{
  "query": "mutation($input: LoginInput!) { loginUser(input: $input) { success message authPayload { accessToken refreshToken user { id email } } } }",
  "variables": {
    "input": {
      "email": "listener@example.com",
      "password": "SecurePass123!"
    }
  }
}
```

#### Responses

- **200** — Login successful

```json
{
  "data": {
    "loginUser": {
      "success": true,
      "authPayload": {
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      }
    }
  }
}
```

---

### `POST` /graphql/

**Query: me**

Returns the authenticated user profile. Requires valid session or JWT context (JWT middleware TODO).

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Standard — 60/min per user (placeholder) |
| **Tags** | auth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "query": "query { me { id email username firstName lastName } }"
}
```

**Example:**

```json
{
  "query": "query { me { id email username } }"
}
```

#### Responses

- **200** — Current user

```json
{
  "data": {
    "me": {
      "id": "1",
      "email": "listener@example.com",
      "username": "listener42"
    }
  }
}
```

---

## Graphql

### `POST` /graphql/

**GraphQL API (all queries & mutations)**

Primary API surface. Send JSON body { query, variables, operationName }. GraphiQL available at GET /graphql/ when enabled. CSRF-exempt; use CORS + auth headers in production.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Not implemented — add ALB/WAF or django-ratelimit (placeholder) |
| **Tags** | graphql |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "query": "string (required)",
  "variables": "object (optional)",
  "operationName": "string (optional)"
}
```

**Example:**

```json
{
  "query": "query { trendingSongs(limit: 10) { id title artist { name } } }",
  "variables": {}
}
```

#### Responses

- **200** — GraphQL response with data and/or errors

```json
{
  "data": {
    "trendingSongs": [
      {
        "id": "1",
        "title": "Example Track",
        "artist": {
          "name": "Example Artist"
        }
      }
    ]
  }
}
```

---

## Interactions

### `POST` /graphql/

**Mutation: addReview**

Add an album review with rating and text.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Write — 10/min per user (placeholder) |
| **Tags** | interactions |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "mutation($input: AddReviewInput!) { addReview(input: $input) { success message } }",
  "variables": {
    "input": {
      "albumId": "10",
      "rating": 5,
      "text": "A masterpiece from start to finish."
    }
  }
}
```

#### Responses

- **200** — Review added

```json
{
  "data": {
    "addReview": {
      "success": true,
      "message": "Review added successfully"
    }
  }
}
```

---

## Music

### `POST` /graphql/

**Query: searchSongs**

Full-text search on songs with optional genre and explicit filters.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Public — 30/min per IP (placeholder) |
| **Tags** | music |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| query | query | string | Yes | GraphQL variable — search term |
| limit | query | integer | No | Max results (default 20) |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "query($q: String!) { searchSongs(query: $q, limit: 10) { id title slug artist { name } } }",
  "variables": {
    "q": "jazz"
  }
}
```

#### Responses

- **200** — Matching songs

```json
{
  "data": {
    "searchSongs": [
      {
        "id": "42",
        "title": "Blue in Green",
        "slug": "blue-in-green"
      }
    ]
  }
}
```

---

### `POST` /graphql/

**Query: trendingSongs**

Trending catalog by time range (DAY, WEEK, MONTH).

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Public — 30/min per IP (placeholder) |
| **Tags** | music |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "query { trendingSongs(timeRange: WEEK, limit: 20) { id title playCount } }"
}
```

#### Responses

- **200** — Trending list

```json
{
  "data": {
    "trendingSongs": [
      {
        "id": "1",
        "title": "Hit Single",
        "playCount": 15000
      }
    ]
  }
}
```

---

### `POST` /graphql/

**Mutation: playSong / trackPlay**

Record a play event for analytics and taste profiling. Available as playSong (music app) and trackPlay (interactions app).

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Write — 60/min per user (placeholder) |
| **Tags** | music |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "mutation($songId: ID!) { playSong(songId: $songId) { success message } }",
  "variables": {
    "songId": "42"
  }
}
```

#### Responses

- **200** — Play recorded

```json
{
  "data": {
    "playSong": {
      "success": true,
      "message": "Play recorded"
    }
  }
}
```

---

## Playlists

### `POST` /graphql/

**Query: myPlaylists**

List playlists owned by the authenticated user.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Standard — 60/min per user (placeholder) |
| **Tags** | playlists |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "query { myPlaylists { id name slug isPublic songCount } }"
}
```

#### Responses

- **200** — User playlists

```json
{
  "data": {
    "myPlaylists": [
      {
        "id": "5",
        "name": "Road Trip",
        "isPublic": true,
        "songCount": 24
      }
    ]
  }
}
```

---

### `POST` /graphql/

**Mutation: createPlaylist**

Create a new playlist with name, description, and visibility.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Write — 20/min per user (placeholder) |
| **Tags** | playlists |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "mutation($input: CreatePlaylistInput!) { createPlaylist(input: $input) { success playlist { id name slug } } }",
  "variables": {
    "input": {
      "name": "Sunday Chill",
      "description": "Relaxing tracks",
      "isPublic": false
    }
  }
}
```

#### Responses

- **200** — Playlist created

```json
{
  "data": {
    "createPlaylist": {
      "success": true,
      "playlist": {
        "id": "6",
        "name": "Sunday Chill"
      }
    }
  }
}
```

---

## Recommendations

### `POST` /graphql/

**Query: recommendedSongs**

Personalized recommendations with score and reasons; anonymous users receive popular songs fallback.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Standard — 30/min (placeholder) |
| **Tags** | recommendations |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "query { recommendedSongs(limit: 10) { score reasons { type description } song { id title artist { name } } } }"
}
```

#### Responses

- **200** — Scored recommendations

```json
{
  "data": {
    "recommendedSongs": [
      {
        "score": 0.85,
        "reasons": [
          {
            "type": "genre_match",
            "description": "Matches your favorite genre: Jazz"
          }
        ],
        "song": {
          "id": "42",
          "title": "Take Five"
        }
      }
    ]
  }
}
```

---

### `POST` /graphql/

**Query: discoverWeekly**

Personalized Discover Weekly playlist for authenticated users.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Standard — 10/min per user (placeholder) |
| **Tags** | recommendations |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "query { discoverWeekly { name songs { id title } generatedAt } }"
}
```

#### Responses

- **200** — Discover Weekly payload

```json
{
  "data": {
    "discoverWeekly": {
      "name": "Discover Weekly",
      "generatedAt": "2026-06-03T00:00:00Z"
    }
  }
}
```

---

### `POST` /graphql/

**Mutation: createRadio**

Create a custom radio station from artist, song, or genre seeds.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Write — 10/min per user (placeholder) |
| **Tags** | recommendations |

#### Request body

**Content-Type:** `application/json`

**Example:**

```json
{
  "query": "mutation($input: CreateRadioInput!) { createRadio(input: $input) { success radio { id name } } }",
  "variables": {
    "input": {
      "name": "Jazz Radio",
      "seedArtistIds": [
        "1"
      ]
    }
  }
}
```

#### Responses

- **200** — Radio created

```json
{
  "data": {
    "createRadio": {
      "success": true,
      "radio": {
        "id": "3",
        "name": "Jazz Radio"
      }
    }
  }
}
```

---

## Service

### `GET` /admin/login/

**Django admin & container health check**

Staff admin UI and Docker HEALTHCHECK probe target.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | N/A |
| **Tags** | service |

#### Responses

- **200** — Admin login page HTML

```json
{
  "note": "Used by Docker HEALTHCHECK in docker/Dockerfile"
}
```

---

### `GET` /api/

**DRF browsable API root**

Django REST Framework session-authentication browsable routes (secondary to GraphQL).

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | N/A |
| **Tags** | service |

#### Responses

- **200** — DRF API root

```json
{
  "note": "Session auth; not primary client integration path"
}
```

---

## Additional notes

# API Schema

> **Base URL (production placeholder):** `https://api.music-streaming.example.com`

> **Primary contract:** All domain operations go through **POST /graphql/** with GraphQL query strings. The `httpEndpoints` entries above map individual operations for portfolio tooling (`schema.ts` compatibility)—not separate REST routes.

> **Auth header (when JWT middleware enabled):** `Authorization: Bearer <access_token>`

> **Interactive explorer:** GraphiQL at `/graphql/` (disable in production).

> **Not exposed yet:** `refreshToken` mutation (class exists in mutations.py, not in schema __init__). Artist follow/unfollow mutations commented out.

> **Dangerous:** GraphQL introspection + GraphiQL in production exposes full schema to unauthenticated users—restrict before public AWS deploy.

> **Missing:** Rate limiting, query depth/complexity limits, and persisted-query allowlists—not implemented; rely on ALB/WAF or add graphene validation extensions.

