from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.recommendations.services.base_service import BaseRecommendationService
from apps.music.models import Song
from apps.artists.models import Artist
from apps.music.models import Album


class BaseRecommendationServiceTestCase(TestCase):
    """Unit tests for BaseRecommendationService"""

    def setUp(self):
        self.artist = Artist.objects.create(name="Test Artist", slug="test-artist")
        self.album = Album.objects.create(
            title="Test Album",
            slug="test-album",
            artist=self.artist,
            release_date="2024-01-01",
        )

    def test_calculate_audio_similarity_perfect_match(self):
        """Test audio similarity calculation with identical features"""
        song = Song.objects.create(
            title="Test Song",
            slug="test-song",
            artist=self.artist,
            album=self.album,
            duration=200,
            energy=0.8,
            danceability=0.7,
            valence=0.6,
        )

        similarity = BaseRecommendationService._calculate_audio_similarity(
            song, target_energy=0.8, target_danceability=0.7, target_valence=0.6
        )

        self.assertEqual(similarity, 1.0)

    def test_calculate_audio_similarity_no_match(self):
        """Test audio similarity calculation with opposite features"""
        song = Song.objects.create(
            title="Test Song",
            slug="test-song",
            artist=self.artist,
            album=self.album,
            duration=200,
            energy=0.0,
            danceability=0.0,
            valence=0.0,
        )

        similarity = BaseRecommendationService._calculate_audio_similarity(
            song, target_energy=1.0, target_danceability=1.0, target_valence=1.0
        )

        self.assertEqual(similarity, 0.0)

    def test_calculate_audio_similarity_partial_match(self):
        """Test audio similarity calculation with partial match"""
        song = Song.objects.create(
            title="Test Song",
            slug="test-song",
            artist=self.artist,
            album=self.album,
            duration=200,
            energy=0.5,
            danceability=0.5,
            valence=0.5,
        )

        similarity = BaseRecommendationService._calculate_audio_similarity(
            song, target_energy=0.7, target_danceability=0.6, target_valence=0.5
        )

        self.assertGreater(similarity, 0.0)
        self.assertLess(similarity, 1.0)

    def test_calculate_audio_similarity_missing_features(self):
        """Test audio similarity calculation with missing features returns 0"""
        song = Song.objects.create(
            title="Test Song",
            slug="test-song",
            artist=self.artist,
            album=self.album,
            duration=200,
            energy=None,
            danceability=0.7,
            valence=0.6,
        )

        similarity = BaseRecommendationService._calculate_audio_similarity(
            song, target_energy=0.8, target_danceability=0.7, target_valence=0.6
        )

        self.assertEqual(similarity, 0.0)

    def test_get_next_monday_from_monday(self):
        """Test getting next Monday when today is Monday"""
        next_monday = BaseRecommendationService._get_next_monday()

        self.assertIsNotNone(next_monday)
        self.assertEqual(next_monday.weekday(), 0)  # Monday is 0
        self.assertGreaterEqual(next_monday, timezone.now())

    def test_get_next_monday_returns_future_date(self):
        """Test that next Monday is always in the future"""
        next_monday = BaseRecommendationService._get_next_monday()

        self.assertGreater(next_monday, timezone.now())

    def test_get_next_monday_is_within_7_days(self):
        """Test that next Monday is within 7 days"""
        next_monday = BaseRecommendationService._get_next_monday()
        now = timezone.now()

        delta = next_monday - now
        self.assertLessEqual(delta.days, 7)
        self.assertGreaterEqual(delta.days, 0)
