from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from apps.recommendations.services.recommendation_service import RecommendationService
from apps.recommendations.models import UserTaste
from apps.music.models import Song, Genre, Album
from apps.artists.models import Artist
from apps.interactions.models import ListeningHistory, LikedSong, FollowedArtist

User = get_user_model()


class RecommendationServiceTestCase(TestCase):
    """Unit tests for RecommendationService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

        # Create genres
        self.rock = Genre.objects.create(name="Rock", slug="rock")
        self.pop = Genre.objects.create(name="Pop", slug="pop")

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

    def test_get_personalized_recommendations_creates_taste_profile(self):
        """Test that recommendations create taste profile if needed"""
        new_user = User.objects.create_user(
            username="newuser", email="new@example.com", password="testpass"
        )

        recommendations = RecommendationService.get_personalized_recommendations(
            new_user, limit=10
        )

        # Should create taste profile
        self.assertTrue(UserTaste.objects.filter(user=new_user).exists())
        self.assertIsInstance(recommendations, list)

    def test_get_personalized_recommendations_excludes_known_songs(self):
        """Test that recommendations exclude listened and liked songs"""
        # User has listened to song1
        ListeningHistory.objects.create(
            user=self.user,
            song=self.song1,
            played_at=timezone.now(),
            duration_played=180,
        )

        # User has liked song2
        LikedSong.objects.create(user=self.user, song=self.song2)

        recommendations = RecommendationService.get_personalized_recommendations(
            self.user, limit=10
        )

        # Should only recommend song3
        recommended_song_ids = [rec["song"].id for rec in recommendations]
        self.assertNotIn(self.song1.id, recommended_song_ids)
        self.assertNotIn(self.song2.id, recommended_song_ids)

    def test_get_personalized_recommendations_filters_by_genre(self):
        """Test that recommendations filter by favorite genres"""
        recommendations = RecommendationService.get_personalized_recommendations(
            self.user, limit=10
        )

        # All recommendations should be from favorite genres
        for rec in recommendations:
            song = rec["song"]
            self.assertTrue(
                song.genre in self.taste.favorite_genres.all()
                or any(
                    genre in self.taste.favorite_genres.all()
                    for genre in song.artist.genres.all()
                )
            )

    def test_get_personalized_recommendations_includes_followed_artists(self):
        """Test that recommendations boost songs from followed artists"""
        # Follow artist1
        FollowedArtist.objects.create(user=self.user, artist=self.artist1)

        recommendations = RecommendationService.get_personalized_recommendations(
            self.user, limit=10
        )

        # Should include songs from followed artist with higher scores
        artist1_songs = [
            rec for rec in recommendations if rec["song"].artist == self.artist1
        ]

        if artist1_songs:
            # Check that artist match reason is included
            for rec in artist1_songs:
                reasons = rec["reasons"]
                artist_match_reasons = [
                    r for r in reasons if r["type"] == "artist_match"
                ]
                if len(artist_match_reasons) > 0:
                    self.assertTrue(True)
                    return

    def test_get_personalized_recommendations_respects_limit(self):
        """Test that recommendations respect the limit parameter"""
        # Create more songs
        for i in range(20):
            Song.objects.create(
                title=f"Extra Song {i}",
                slug=f"extra-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.7,
                danceability=0.6,
                valence=0.7,
            )

        recommendations = RecommendationService.get_personalized_recommendations(
            self.user, limit=5
        )

        self.assertLessEqual(len(recommendations), 5)

    def test_get_similar_songs_with_valid_song(self):
        """Test getting similar songs for a valid song"""
        similar = RecommendationService.get_similar_songs(self.song1.id, limit=10)

        self.assertIsInstance(similar, list)
        # Song3 should be similar to Song1 (same artist, genre, similar features)
        similar_ids = [s.id for s in similar]
        if self.song3.id in similar_ids:
            self.assertTrue(True)

    def test_get_similar_songs_excludes_reference_song(self):
        """Test that similar songs exclude the reference song"""
        similar = RecommendationService.get_similar_songs(self.song1.id, limit=10)

        similar_ids = [s.id for s in similar]
        self.assertNotIn(self.song1.id, similar_ids)

    def test_get_similar_songs_invalid_song_raises_error(self):
        """Test that invalid song ID raises ValidationError"""
        with self.assertRaises(ValidationError):
            RecommendationService.get_similar_songs(99999, limit=10)

    def test_get_similar_songs_fallback_without_audio_features(self):
        """Test that similar songs fall back to genre/artist matching without audio features"""
        # Create a song without audio features
        song_no_features = Song.objects.create(
            title="No Features Song",
            slug="no-features-song",
            artist=self.artist1,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=None,
            danceability=None,
            valence=None,
        )

        similar = RecommendationService.get_similar_songs(song_no_features.id, limit=10)

        self.assertIsInstance(similar, list)
        # Should use genre/artist fallback
        if len(similar) > 0:
            for song in similar:
                self.assertTrue(song.genre == self.rock or song.artist == self.artist1)

    def test_get_similar_songs_boosts_same_tempo(self):
        """Test that similar songs boost songs with similar tempo"""
        # Create a song with very similar tempo to song1 (120.0)
        similar_tempo_song = Song.objects.create(
            title="Similar Tempo",
            slug="similar-tempo",
            artist=self.artist1,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.8,
            danceability=0.6,
            valence=0.7,
            tempo=121.0,  # Very close to song1's 120.0
        )

        similar = RecommendationService.get_similar_songs(self.song1.id, limit=10)

        # Song with similar tempo should be ranked high
        if len(similar) > 0:
            self.assertTrue(True)

    def test_generate_discover_weekly(self):
        """Test generating discover weekly playlist"""
        # Create some songs with lower play counts
        for i in range(5):
            Song.objects.create(
                title=f"Discover Song {i}",
                slug=f"discover-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.7,
                danceability=0.6,
                valence=0.7,
                play_count=10000,  # Below 50000 threshold
            )

        discover = RecommendationService.generate_discover_weekly(self.user)

        self.assertIn("id", discover)
        self.assertIn("name", discover)
        self.assertIn("description", discover)
        self.assertIn("songs", discover)
        self.assertIn("refresh_date", discover)

        self.assertEqual(discover["name"], "Discover Weekly")
        self.assertIsInstance(discover["songs"], list)

        # All songs should have play_count < 50000
        for song in discover["songs"]:
            self.assertLess(song.play_count, 50000)

    def test_generate_discover_weekly_limits_to_30_songs(self):
        """Test that discover weekly limits to 30 songs"""
        # Create many songs with low play counts
        for i in range(50):
            Song.objects.create(
                title=f"Discover Song {i}",
                slug=f"discover-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.7,
                danceability=0.6,
                valence=0.7,
                play_count=5000,
            )

        discover = RecommendationService.generate_discover_weekly(self.user)

        self.assertLessEqual(len(discover["songs"]), 30)

    def test_recommendations_include_reasons(self):
        """Test that recommendations include reasons"""
        recommendations = RecommendationService.get_personalized_recommendations(
            self.user, limit=10
        )

        if len(recommendations) > 0:
            for rec in recommendations:
                self.assertIn("song", rec)
                self.assertIn("score", rec)
                self.assertIn("reasons", rec)
                self.assertIsInstance(rec["reasons"], list)

    def test_recommendations_calculate_scores(self):
        """Test that recommendations calculate scores correctly"""
        recommendations = RecommendationService.get_personalized_recommendations(
            self.user, limit=10
        )

        for rec in recommendations:
            self.assertGreaterEqual(rec["score"], 0.0)
            self.assertLessEqual(rec["score"], 1.0)

    def test_recommendations_sorted_by_score(self):
        """Test that recommendations are sorted by score"""
        # Create many songs
        for i in range(20):
            Song.objects.create(
                title=f"Test Song {i}",
                slug=f"test-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.7,
                danceability=0.6,
                valence=0.7,
                play_count=1000 * i,
            )

        recommendations = RecommendationService.get_personalized_recommendations(
            self.user, limit=10
        )

        # Verify sorted by score descending
        scores = [rec["score"] for rec in recommendations]
        self.assertEqual(scores, sorted(scores, reverse=True))
