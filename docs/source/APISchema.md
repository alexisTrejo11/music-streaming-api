---
type: "GraphQL"

httpEndpoints:
  - id: "graphql-endpoint"
    method: "POST"
    urlPath: "/graphql/"
    summary: "GraphQL API (all queries & mutations)"
    description: "Primary API surface. Send JSON body { query, variables, operationName }. GraphiQL available at GET /graphql/ when enabled. CSRF-exempt; use CORS + auth headers in production."
    tags: ["graphql"]
    authenticated: false
    rateLimit: "Not implemented — add ALB/WAF or django-ratelimit (placeholder)"
    requestBody:
      contentType: "application/json"
      schema:
        query: "string (required)"
        variables: "object (optional)"
        operationName: "string (optional)"
      example:
        query: "query { trendingSongs(limit: 10) { id title artist { name } } }"
        variables: {}
    responses:
      - status: 200
        description: "GraphQL response with data and/or errors"
        example:
          data:
            trendingSongs:
              - id: "1"
                title: "Example Track"
                artist:
                  name: "Example Artist"

  - id: "admin-login"
    method: "GET"
    urlPath: "/admin/login/"
    summary: "Django admin & container health check"
    description: "Staff admin UI and Docker HEALTHCHECK probe target."
    tags: ["service"]
    authenticated: false
    rateLimit: "N/A"
    responses:
      - status: 200
        description: "Admin login page HTML"
        example:
          note: "Used by Docker HEALTHCHECK in docker/Dockerfile"

  - id: "drf-auth"
    method: "GET"
    urlPath: "/api/"
    summary: "DRF browsable API root"
    description: "Django REST Framework session-authentication browsable routes (secondary to GraphQL)."
    tags: ["service"]
    authenticated: false
    rateLimit: "N/A"
    responses:
      - status: 200
        description: "DRF API root"
        example:
          note: "Session auth; not primary client integration path"

  - id: "auth-register"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Mutation: registerUser"
    description: "Create account with email, username, password. Returns AuthPayloadType with JWT tokens."
    tags: ["auth"]
    authenticated: false
    rateLimit: "Placeholder — 10/min per IP recommended"
    requestBody:
      contentType: "application/json"
      schema:
        query: "mutation Register($input: RegisterInput!) { registerUser(input: $input) { success message authPayload { accessToken refreshToken user { id email username } } } }"
        variables:
          input:
            email: "string"
            username: "string"
            password: "string"
            firstName: "string"
            lastName: "string"
      example:
        query: "mutation($input: RegisterInput!) { registerUser(input: $input) { success message } }"
        variables:
          input:
            email: "listener@example.com"
            username: "listener42"
            password: "SecurePass123!"
            firstName: "Alex"
            lastName: "Listener"
    responses:
      - status: 200
        description: "Registration result"
        example:
          data:
            registerUser:
              success: true
              message: "Registration successful"

  - id: "auth-login"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Mutation: loginUser"
    description: "Authenticate with email and password; returns access and refresh JWT tokens."
    tags: ["auth"]
    authenticated: false
    rateLimit: "Placeholder — 5/min per email recommended"
    requestBody:
      contentType: "application/json"
      schema:
        query: "mutation Login($input: LoginInput!) { loginUser(input: $input) { success authPayload { accessToken refreshToken } } }"
      example:
        query: "mutation($input: LoginInput!) { loginUser(input: $input) { success message authPayload { accessToken refreshToken user { id email } } } }"
        variables:
          input:
            email: "listener@example.com"
            password: "SecurePass123!"
    responses:
      - status: 200
        description: "Login successful"
        example:
          data:
            loginUser:
              success: true
              authPayload:
                accessToken: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                refreshToken: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

  - id: "auth-me"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Query: me"
    description: "Returns the authenticated user profile. Requires valid session or JWT context (JWT middleware TODO)."
    tags: ["auth"]
    authenticated: true
    rateLimit: "Standard — 60/min per user (placeholder)"
    requestBody:
      contentType: "application/json"
      schema:
        query: "query { me { id email username firstName lastName } }"
      example:
        query: "query { me { id email username } }"
    responses:
      - status: 200
        description: "Current user"
        example:
          data:
            me:
              id: "1"
              email: "listener@example.com"
              username: "listener42"

  - id: "music-search"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Query: searchSongs"
    description: "Full-text search on songs with optional genre and explicit filters."
    tags: ["music"]
    authenticated: false
    rateLimit: "Public — 30/min per IP (placeholder)"
    parameters:
      - name: "query"
        in: "query"
        type: "string"
        required: true
        description: "GraphQL variable — search term"
        example: "jazz"
      - name: "limit"
        in: "query"
        type: "integer"
        required: false
        description: "Max results (default 20)"
        example: 20
    requestBody:
      contentType: "application/json"
      example:
        query: "query($q: String!) { searchSongs(query: $q, limit: 10) { id title slug artist { name } } }"
        variables:
          q: "jazz"
    responses:
      - status: 200
        description: "Matching songs"
        example:
          data:
            searchSongs:
              - id: "42"
                title: "Blue in Green"
                slug: "blue-in-green"

  - id: "music-trending"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Query: trendingSongs"
    description: "Trending catalog by time range (DAY, WEEK, MONTH)."
    tags: ["music"]
    authenticated: false
    rateLimit: "Public — 30/min per IP (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "query { trendingSongs(timeRange: WEEK, limit: 20) { id title playCount } }"
    responses:
      - status: 200
        description: "Trending list"
        example:
          data:
            trendingSongs:
              - id: "1"
                title: "Hit Single"
                playCount: 15000

  - id: "music-play"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Mutation: playSong / trackPlay"
    description: "Record a play event for analytics and taste profiling. Available as playSong (music app) and trackPlay (interactions app)."
    tags: ["music"]
    authenticated: true
    rateLimit: "Write — 60/min per user (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "mutation($songId: ID!) { playSong(songId: $songId) { success message } }"
        variables:
          songId: "42"
    responses:
      - status: 200
        description: "Play recorded"
        example:
          data:
            playSong:
              success: true
              message: "Play recorded"

  - id: "playlists-my"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Query: myPlaylists"
    description: "List playlists owned by the authenticated user."
    tags: ["playlists"]
    authenticated: true
    rateLimit: "Standard — 60/min per user (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "query { myPlaylists { id name slug isPublic songCount } }"
    responses:
      - status: 200
        description: "User playlists"
        example:
          data:
            myPlaylists:
              - id: "5"
                name: "Road Trip"
                isPublic: true
                songCount: 24

  - id: "playlists-create"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Mutation: createPlaylist"
    description: "Create a new playlist with name, description, and visibility."
    tags: ["playlists"]
    authenticated: true
    rateLimit: "Write — 20/min per user (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "mutation($input: CreatePlaylistInput!) { createPlaylist(input: $input) { success playlist { id name slug } } }"
        variables:
          input:
            name: "Sunday Chill"
            description: "Relaxing tracks"
            isPublic: false
    responses:
      - status: 200
        description: "Playlist created"
        example:
          data:
            createPlaylist:
              success: true
              playlist:
                id: "6"
                name: "Sunday Chill"

  - id: "recommendations-personalized"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Query: recommendedSongs"
    description: "Personalized recommendations with score and reasons; anonymous users receive popular songs fallback."
    tags: ["recommendations"]
    authenticated: false
    rateLimit: "Standard — 30/min (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "query { recommendedSongs(limit: 10) { score reasons { type description } song { id title artist { name } } } }"
    responses:
      - status: 200
        description: "Scored recommendations"
        example:
          data:
            recommendedSongs:
              - score: 0.85
                reasons:
                  - type: "genre_match"
                    description: "Matches your favorite genre: Jazz"
                song:
                  id: "42"
                  title: "Take Five"

  - id: "recommendations-discover-weekly"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Query: discoverWeekly"
    description: "Personalized Discover Weekly playlist for authenticated users."
    tags: ["recommendations"]
    authenticated: true
    rateLimit: "Standard — 10/min per user (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "query { discoverWeekly { name songs { id title } generatedAt } }"
    responses:
      - status: 200
        description: "Discover Weekly payload"
        example:
          data:
            discoverWeekly:
              name: "Discover Weekly"
              generatedAt: "2026-06-03T00:00:00Z"

  - id: "recommendations-radio"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Mutation: createRadio"
    description: "Create a custom radio station from artist, song, or genre seeds."
    tags: ["recommendations"]
    authenticated: true
    rateLimit: "Write — 10/min per user (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "mutation($input: CreateRadioInput!) { createRadio(input: $input) { success radio { id name } } }"
        variables:
          input:
            name: "Jazz Radio"
            seedArtistIds: ["1"]
    responses:
      - status: 200
        description: "Radio created"
        example:
          data:
            createRadio:
              success: true
              radio:
                id: "3"
                name: "Jazz Radio"

  - id: "artists-search"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Query: searchArtists"
    description: "Search artist catalog by name."
    tags: ["artists"]
    authenticated: false
    rateLimit: "Public — 30/min per IP (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "query($q: String!) { searchArtists(query: $q, limit: 10) { id name slug } }"
        variables:
          q: "miles"
    responses:
      - status: 200
        description: "Artist results"
        example:
          data:
            searchArtists:
              - id: "1"
                name: "Miles Davis"
                slug: "miles-davis"

  - id: "interactions-reviews"
    method: "POST"
    urlPath: "/graphql/"
    summary: "Mutation: addReview"
    description: "Add an album review with rating and text."
    tags: ["interactions"]
    authenticated: true
    rateLimit: "Write — 10/min per user (placeholder)"
    requestBody:
      contentType: "application/json"
      example:
        query: "mutation($input: AddReviewInput!) { addReview(input: $input) { success message } }"
        variables:
          input:
            albumId: "10"
            rating: 5
            text: "A masterpiece from start to finish."
    responses:
      - status: 200
        description: "Review added"
        example:
          data:
            addReview:
              success: true
              message: "Review added successfully"
---

# API Schema

> **Base URL (production placeholder):** `https://api.music-streaming.example.com`

> **Primary contract:** All domain operations go through **POST /graphql/** with GraphQL query strings. The `httpEndpoints` entries above map individual operations for portfolio tooling (`schema.ts` compatibility)—not separate REST routes.

> **Auth header (when JWT middleware enabled):** `Authorization: Bearer <access_token>`

> **Interactive explorer:** GraphiQL at `/graphql/` (disable in production).

> **Not exposed yet:** `refreshToken` mutation (class exists in mutations.py, not in schema __init__). Artist follow/unfollow mutations commented out.

> **Dangerous:** GraphQL introspection + GraphiQL in production exposes full schema to unauthenticated users—restrict before public AWS deploy.

> **Missing:** Rate limiting, query depth/complexity limits, and persisted-query allowlists—not implemented; rely on ALB/WAF or add graphene validation extensions.
