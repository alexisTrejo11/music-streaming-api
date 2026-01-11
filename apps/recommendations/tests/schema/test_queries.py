from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client

from apps.recommendations.models import UserTaste, Radio
from apps.music.models import Song, Album, Genre
from apps.artists.models import Artist
from apps.interactions.models import LikedSong, FollowedArtist, ListeningHistory
from config.schema import schema

User = get_user_model()


class RecommendationQueriesTestCase(TestCase):
    """Test cases for Recommendation GraphQL queries"""

    def setUp(self):
        """Set up test data"""
        self.client = Client(schema)

        # Create user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create genres
        self.rock = Genre.objects.create(name="Rock", slug="rock")
        self.pop = Genre.objects.create(name="Pop", slug="pop")

        # Create artists
        self.artist1 = Artist.objects.create(
            name="Artist 1", slug="artist-1", monthly_listeners=100000
        )
        self.artist1.genres.add(self.rock)

        self.artist2 = Artist.objects.create(
            name="Artist 2", slug="artist-2", monthly_listeners=50000
        )
        self.artist2.genres.add(self.pop)

        # Create album
        self.album = Album.objects.create(
            title="Test Album",
            slug="test-album",
            artist=self.artist1,
            release_date="2024-01-01",
        )

        # Create songs
        self.song1 = Song.objects.create(
            title="Song 1",
            slug="song-1",
            artist=self.artist1,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.8,
            danceability=0.6,
            valence=0.7,
            tempo=120.0,
            play_count=5000,
        )

        self.song2 = Song.objects.create(
            title="Song 2",
            slug="song-2",
            artist=self.artist2,
            album=self.album,
            genre=self.pop,
            duration=180,
            energy=0.6,
            danceability=0.8,
            valence=0.9,
            tempo=110.0,
            play_count=15000,
        )

        self.song3 = Song.objects.create(
            title="Song 3",
            slug="song-3",
            artist=self.artist1,
            album=self.album,
            genre=self.rock,
            duration=220,
            energy=0.75,
            danceability=0.55,
            valence=0.65,
            tempo=118.0,
            play_count=2000,
        )

        # Create taste profile
        self.taste = UserTaste.objects.create(
            user=self.user,
            energy_preference=0.7,
            danceability_preference=0.6,
            valence_preference=0.7,
        )
        self.taste.favorite_genres.add(self.rock)
        self.taste.top_artists.add(self.artist1)

        # Create radio
        self.radio = Radio.objects.create(
            user=self.user, name="Rock Radio", seed_artist=self.artist1
        )

    def _get_user_context(self, user):
        """Helper to create user context"""

        class MockContext:
            def __init__(self, user):
                self.user = user

        return MockContext(user)

    def _get_anonymous_context(self):
        """Helper to create anonymous context"""

        class MockContext:
            def __init__(self):
                self.user = type("AnonymousUser", (), {"is_authenticated": False})()

        return MockContext()

    # === Taste Profile Queries ===

    def test_my_taste_profile_returns_user_taste(self):
        """Test that myTasteProfile returns user's taste profile"""
        query = """
            query {
                myTasteProfile {
                    id
                    energyPreference
                    danceabilityPreference
                    valencePreference
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["myTasteProfile"])
        self.assertEqual(
            float(result["data"]["myTasteProfile"]["energyPreference"]), 0.7
        )

    def test_my_taste_profile_requires_authentication(self):
        """Test that myTasteProfile requires authentication"""
        query = """
            query {
                myTasteProfile {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("Authentication required", str(result["errors"]))

    def test_my_taste_profile_creates_if_not_exists(self):
        """Test that myTasteProfile creates profile if doesn't exist"""
        new_user = User.objects.create_user(
            username="newuser", email="new@example.com", password="testpass"
        )

        query = """
            query {
                myTasteProfile {
                    id
                    energyPreference
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(new_user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["myTasteProfile"])
        self.assertTrue(UserTaste.objects.filter(user=new_user).exists())

    def test_audio_preferences_returns_preferences(self):
        """Test that audioPreferences returns user's audio preferences"""
        query = """
            query {
                audioPreferences {
                    energy
                    danceability
                    valence
                    tempoRange
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["audioPreferences"])
        self.assertIsNotNone(result["data"]["audioPreferences"]["energy"])
        self.assertIsNotNone(result["data"]["audioPreferences"]["tempoRange"])

    def test_audio_preferences_requires_authentication(self):
        """Test that audioPreferences requires authentication"""
        query = """
            query {
                audioPreferences {
                    energy
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    # === Recommendation Queries ===

    def test_recommended_songs_returns_recommendations(self):
        """Test that recommendedSongs returns personalized recommendations"""
        query = """
            query {
                recommendedSongs(limit: 10) {
                    song {
                        id
                        title
                    }
                    score
                    reasons {
                        type
                        description
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["recommendedSongs"])
        self.assertIsInstance(result["data"]["recommendedSongs"], list)

    def test_recommended_songs_respects_limit(self):
        """Test that recommendedSongs respects the limit parameter"""
        # Create more songs
        for i in range(20):
            Song.objects.create(
                title=f"Extra Song {i}",
                slug=f"extra-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
            )

        query = """
            query {
                recommendedSongs(limit: 5) {
                    song {
                        id
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertLessEqual(len(result["data"]["recommendedSongs"]), 5)

    def test_recommended_songs_works_for_unauthenticated_users(self):
        """Test that recommendedSongs returns popular songs for anonymous users"""
        query = """
            query {
                recommendedSongs(limit: 10) {
                    song {
                        id
                        title
                    }
                    score
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["recommendedSongs"])
        self.assertIsInstance(result["data"]["recommendedSongs"], list)

    def test_similar_songs_returns_similar_songs(self):
        """Test that similarSongs returns similar songs"""
        query = f"""
            query {{
                similarSongs(songId: "{self.song1.id}", limit: 10) {{
                    id
                    title
                }}
            }}
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["similarSongs"])
        self.assertIsInstance(result["data"]["similarSongs"], list)

    def test_similar_songs_excludes_reference_song(self):
        """Test that similarSongs excludes the reference song"""
        query = f"""
            query {{
                similarSongs(songId: "{self.song1.id}", limit: 10) {{
                    id
                }}
            }}
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        similar_ids = [s["id"] for s in result["data"]["similarSongs"]]
        self.assertNotIn(str(self.song1.id), similar_ids)

    def test_similar_songs_respects_limit(self):
        """Test that similarSongs respects limit parameter"""
        query = f"""
            query {{
                similarSongs(songId: "{self.song1.id}", limit: 2) {{
                    id
                }}
            }}
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertLessEqual(len(result["data"]["similarSongs"]), 2)

    def test_discover_weekly_returns_playlist(self):
        """Test that discoverWeekly returns discover weekly playlist"""
        query = """
            query {
                discoverWeekly {
                    id
                    name
                    description
                    songs {
                        id
                        title
                    }
                    refreshDate
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["discoverWeekly"])
        self.assertEqual(result["data"]["discoverWeekly"]["name"], "Discover Weekly")
        self.assertIsNotNone(result["data"]["discoverWeekly"]["refreshDate"])

    def test_discover_weekly_requires_authentication(self):
        """Test that discoverWeekly requires authentication"""
        query = """
            query {
                discoverWeekly {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    def test_recommended_artists_returns_artists(self):
        """Test that recommendedArtists returns recommended artists"""
        # Create more artists
        for i in range(5, 10):  # Start from 5 to avoid slug conflicts
            artist = Artist.objects.create(
                name=f"Artist {i}", slug=f"artist-{i}", monthly_listeners=10000
            )
            artist.genres.add(self.rock)

        query = """
            query {
                recommendedArtists(limit: 10) {
                    id
                    name
                    monthlyListeners
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["recommendedArtists"])
        self.assertIsInstance(result["data"]["recommendedArtists"], list)

    def test_recommended_artists_requires_authentication(self):
        """Test that recommendedArtists requires authentication"""
        query = """
            query {
                recommendedArtists {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    def test_recommended_albums_returns_albums(self):
        """Test that recommendedAlbums returns recommended albums"""
        # Create more albums
        for i in range(5):
            Album.objects.create(
                title=f"Album {i}",
                slug=f"album-{i}",
                artist=self.artist1,
                release_date="2024-01-01",
            )

        query = """
            query {
                recommendedAlbums(limit: 10) {
                    id
                    title
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["recommendedAlbums"])
        self.assertIsInstance(result["data"]["recommendedAlbums"], list)

    def test_recommended_albums_requires_authentication(self):
        """Test that recommendedAlbums requires authentication"""
        query = """
            query {
                recommendedAlbums {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    # === Radio Queries ===

    def test_my_radios_returns_user_radios(self):
        """Test that myRadios returns user's radio stations"""
        query = """
            query {
                myRadios {
                    id
                    name
                    seedArtist {
                        id
                        name
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["myRadios"])
        self.assertEqual(len(result["data"]["myRadios"]), 1)
        self.assertEqual(result["data"]["myRadios"][0]["name"], "Rock Radio")

    def test_my_radios_requires_authentication(self):
        """Test that myRadios requires authentication"""
        query = """
            query {
                myRadios {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    def test_radio_returns_specific_radio(self):
        """Test that radio returns a specific radio station"""
        query = f"""
            query {{
                radio(id: "{self.radio.id}") {{
                    id
                    name
                    songs {{
                        id
                        title
                    }}
                }}
            }}
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["radio"])
        self.assertEqual(result["data"]["radio"]["name"], "Rock Radio")

    def test_radio_requires_authentication(self):
        """Test that radio requires authentication"""
        query = f"""
            query {{
                radio(id: "{self.radio.id}") {{
                    id
                }}
            }}
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    def test_radio_not_found_error(self):
        """Test that radio returns error for non-existent radio"""
        query = """
            query {
                radio(id: "99999") {
                    id
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("not found", str(result["errors"]))

    def test_radio_wrong_user_error(self):
        """Test that radio returns error when accessing another user's radio"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass"
        )

        query = f"""
            query {{
                radio(id: "{self.radio.id}") {{
                    id
                }}
            }}
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(other_user)
        )

        self.assertIsNotNone(result.get("errors"))

    # === Mood-based Queries ===

    def test_songs_by_mood_returns_songs(self):
        """Test that songsByMood returns songs matching mood"""
        # Create songs with specific mood features
        Song.objects.create(
            title="Happy Song",
            slug="happy-song",
            artist=self.artist1,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.8,
            danceability=0.7,
            valence=0.9,
        )

        query = """
            query {
                songsByMood(mood: "happy", limit: 10) {
                    id
                    title
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["songsByMood"])
        self.assertIsInstance(result["data"]["songsByMood"], list)

    def test_songs_by_mood_respects_limit(self):
        """Test that songsByMood respects limit parameter"""
        # Create many happy songs
        for i in range(20):
            Song.objects.create(
                title=f"Happy Song {i}",
                slug=f"happy-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.8,
                valence=0.9,
            )

        query = """
            query {
                songsByMood(mood: "happy", limit: 5) {
                    id
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertLessEqual(len(result["data"]["songsByMood"]), 5)

    def test_songs_by_mood_different_moods(self):
        """Test that songsByMood works with different mood values"""
        moods = ["happy", "sad", "energetic", "chill", "party", "focus"]

        for mood in moods:
            query = f"""
                query {{
                    songsByMood(mood: "{mood}", limit: 10) {{
                        id
                    }}
                }}
            """

            result = self.client.execute(
                query, context_value=self._get_user_context(self.user)
            )

            self.assertIsNone(result.get("errors"))
            self.assertIsNotNone(result["data"]["songsByMood"])

    def test_songs_by_mood_works_for_anonymous_users(self):
        """Test that songsByMood works for unauthenticated users"""
        query = """
            query {
                songsByMood(mood: "happy", limit: 10) {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["songsByMood"])

    # === Trending Queries ===

    def test_trending_for_you_returns_trending_songs(self):
        """Test that trendingForYou returns personalized trending songs"""
        query = """
            query {
                trendingForYou(limit: 10) {
                    id
                    title
                    playCount
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["trendingForYou"])
        self.assertIsInstance(result["data"]["trendingForYou"], list)

    def test_trending_for_you_respects_limit(self):
        """Test that trendingForYou respects limit parameter"""
        query = """
            query {
                trendingForYou(limit: 5) {
                    id
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertLessEqual(len(result["data"]["trendingForYou"]), 5)

    def test_trending_for_you_works_for_anonymous_users(self):
        """Test that trendingForYou works for unauthenticated users"""
        query = """
            query {
                trendingForYou(limit: 10) {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["trendingForYou"])
