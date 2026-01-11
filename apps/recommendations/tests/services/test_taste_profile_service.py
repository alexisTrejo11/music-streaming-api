from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.recommendations.services.taste_profile_service import TasteProfileService
from apps.recommendations.models import UserTaste
from apps.music.models import Song, Genre, Album
from apps.artists.models import Artist
from apps.interactions.models import ListeningHistory, LikedSong

User = get_user_model()


class TasteProfileServiceTestCase(TestCase):
    """Unit tests for TasteProfileService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

        # Create genres
        self.rock = Genre.objects.create(name="Rock", slug="rock")
        self.pop = Genre.objects.create(name="Pop", slug="pop")
        self.jazz = Genre.objects.create(name="Jazz", slug="jazz")

        # Create artists
        self.artist1 = Artist.objects.create(name="Artist 1", slug="artist-1")
        self.artist1.genres.add(self.rock)

        self.artist2 = Artist.objects.create(name="Artist 2", slug="artist-2")
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
        )

        self.song3 = Song.objects.create(
            title="Song 3",
            slug="song-3",
            artist=self.artist1,
            album=self.album,
            genre=self.rock,
            duration=220,
            energy=0.7,
            danceability=0.5,
            valence=0.6,
            tempo=115.0,
        )

    def test_update_taste_profile_creates_profile(self):
        """Test that update_taste_profile creates a UserTaste if it doesn't exist"""
        self.assertFalse(UserTaste.objects.filter(user=self.user).exists())

        taste = TasteProfileService.update_taste_profile(self.user)

        self.assertIsNotNone(taste)
        self.assertEqual(taste.user, self.user)
        self.assertTrue(UserTaste.objects.filter(user=self.user).exists())

    def test_update_taste_profile_with_no_history(self):
        """Test update_taste_profile with no listening history"""
        taste = TasteProfileService.update_taste_profile(self.user)

        self.assertIsNotNone(taste)
        self.assertEqual(taste.favorite_genres.count(), 0)
        self.assertEqual(taste.top_artists.count(), 0)

    def test_update_taste_profile_with_listening_history(self):
        """Test update_taste_profile with listening history"""
        # Create listening history
        for _ in range(10):
            ListeningHistory.objects.create(
                user=self.user,
                song=self.song1,
                played_at=timezone.now() - timedelta(days=1),
                duration_played=180,
            )

        for _ in range(5):
            ListeningHistory.objects.create(
                user=self.user,
                song=self.song2,
                played_at=timezone.now() - timedelta(days=2),
                duration_played=170,
            )

        taste = TasteProfileService.update_taste_profile(self.user)

        self.assertIsNotNone(taste)
        self.assertGreater(taste.favorite_genres.count(), 0)
        self.assertGreater(taste.top_artists.count(), 0)

        # Rock should be the favorite genre
        self.assertIn(self.rock, taste.favorite_genres.all())

    def test_update_taste_profile_calculates_audio_preferences(self):
        """Test that update_taste_profile calculates audio feature preferences"""
        # Create liked songs
        LikedSong.objects.create(user=self.user, song=self.song1)
        LikedSong.objects.create(user=self.user, song=self.song3)

        taste = TasteProfileService.update_taste_profile(self.user)

        # Should have calculated average preferences
        self.assertGreater(taste.energy_preference, 0.0)
        self.assertLess(taste.energy_preference, 1.0)
        self.assertGreater(taste.danceability_preference, 0.0)
        self.assertLess(taste.danceability_preference, 1.0)
        self.assertGreater(taste.valence_preference, 0.0)
        self.assertLess(taste.valence_preference, 1.0)

    def test_update_taste_profile_manual_with_genres(self):
        """Test manually updating taste profile with favorite genres"""
        data = {"favorite_genre_ids": [self.rock.id, self.pop.id]}

        taste = TasteProfileService.update_taste_profile_manual(self.user, data)

        self.assertEqual(taste.favorite_genres.count(), 2)
        self.assertIn(self.rock, taste.favorite_genres.all())
        self.assertIn(self.pop, taste.favorite_genres.all())

    def test_update_taste_profile_manual_with_artists(self):
        """Test manually updating taste profile with top artists"""
        data = {"top_artist_ids": [self.artist1.id, self.artist2.id]}

        taste = TasteProfileService.update_taste_profile_manual(self.user, data)

        self.assertEqual(taste.top_artists.count(), 2)
        self.assertIn(self.artist1, taste.top_artists.all())
        self.assertIn(self.artist2, taste.top_artists.all())

    def test_get_audio_preferences(self):
        """Test getting audio preferences"""
        # Create liked songs
        LikedSong.objects.create(user=self.user, song=self.song1)
        LikedSong.objects.create(user=self.user, song=self.song2)

        preferences = TasteProfileService.get_audio_preferences(self.user)

        self.assertIn("energy", preferences)
        self.assertIn("danceability", preferences)
        self.assertIn("valence", preferences)
        self.assertIn("tempo_range", preferences)

        # Verify values are in valid ranges
        self.assertGreater(preferences["energy"], 0.0)
        self.assertLessEqual(preferences["energy"], 1.0)
        self.assertGreater(preferences["danceability"], 0.0)
        self.assertLessEqual(preferences["danceability"], 1.0)
        self.assertGreater(preferences["valence"], 0.0)
        self.assertLessEqual(preferences["valence"], 1.0)

        # Verify tempo range
        self.assertIsInstance(preferences["tempo_range"], list)
        self.assertEqual(len(preferences["tempo_range"]), 2)

    def test_get_audio_preferences_no_liked_songs(self):
        """Test getting audio preferences with no liked songs returns defaults"""
        preferences = TasteProfileService.get_audio_preferences(self.user)

        self.assertEqual(preferences["energy"], 0.5)
        self.assertEqual(preferences["danceability"], 0.5)
        self.assertEqual(preferences["valence"], 0.5)
        self.assertEqual(preferences["tempo_range"], [80.0, 140.0])

    def test_calculate_audio_preferences_averages_correctly(self):
        """Test that audio preferences are averaged correctly"""
        # Create liked songs with known values
        LikedSong.objects.create(user=self.user, song=self.song1)
        LikedSong.objects.create(user=self.user, song=self.song3)

        features = TasteProfileService._calculate_audio_preferences(self.user)

        # song1: energy=0.8, danceability=0.6, valence=0.7
        # song3: energy=0.7, danceability=0.5, valence=0.6
        # Expected averages: energy=0.75, danceability=0.55, valence=0.65

        self.assertAlmostEqual(features["energy"], 0.75, places=2)
        self.assertAlmostEqual(features["danceability"], 0.55, places=2)
        self.assertAlmostEqual(features["valence"], 0.65, places=2)

    def test_taste_profile_updates_timestamp(self):
        """Test that taste profile updates last_updated timestamp"""
        taste = TasteProfileService.update_taste_profile(self.user)
        initial_timestamp = taste.last_updated

        # Update again
        taste = TasteProfileService.update_taste_profile(self.user)

        self.assertGreaterEqual(taste.last_updated, initial_timestamp)
