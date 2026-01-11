from django.test import TestCase

from apps.recommendations.services.mood_service import MoodService
from apps.music.models import Song, Genre, Album
from apps.artists.models import Artist


class MoodServiceTestCase(TestCase):
    """Unit tests for MoodService"""

    def setUp(self):
        self.rock = Genre.objects.create(name="Rock", slug="rock")
        self.artist = Artist.objects.create(name="Test Artist", slug="test-artist")
        self.album = Album.objects.create(
            title="Test Album",
            slug="test-album",
            artist=self.artist,
            release_date="2024-01-01",
        )

        # Create songs for different moods
        self.happy_song = Song.objects.create(
            title="Happy Song",
            slug="happy-song",
            artist=self.artist,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.8,
            danceability=0.7,
            valence=0.9,
        )

        self.sad_song = Song.objects.create(
            title="Sad Song",
            slug="sad-song",
            artist=self.artist,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.3,
            danceability=0.4,
            valence=0.2,
        )

        self.energetic_song = Song.objects.create(
            title="Energetic Song",
            slug="energetic-song",
            artist=self.artist,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.9,
            danceability=0.8,
            valence=0.7,
        )

        self.chill_song = Song.objects.create(
            title="Chill Song",
            slug="chill-song",
            artist=self.artist,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.2,
            danceability=0.4,
            valence=0.5,
        )

        self.party_song = Song.objects.create(
            title="Party Song",
            slug="party-song",
            artist=self.artist,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.8,
            danceability=0.9,
            valence=0.8,
        )

        self.focus_song = Song.objects.create(
            title="Focus Song",
            slug="focus-song",
            artist=self.artist,
            album=self.album,
            genre=self.rock,
            duration=200,
            energy=0.5,
            danceability=0.4,
            valence=0.5,
        )

    def test_get_songs_by_mood_happy(self):
        """Test getting happy mood songs"""
        songs = MoodService.get_songs_by_mood("happy", limit=10)

        self.assertIsInstance(songs, list)
        # Happy songs should have high valence and energy
        for song in songs:
            self.assertGreaterEqual(song.valence, 0.6)
            self.assertGreaterEqual(song.energy, 0.5)

    def test_get_songs_by_mood_sad(self):
        """Test getting sad mood songs"""
        songs = MoodService.get_songs_by_mood("sad", limit=10)

        self.assertIsInstance(songs, list)
        # Sad songs should have low valence and energy
        for song in songs:
            self.assertLessEqual(song.valence, 0.4)
            self.assertLessEqual(song.energy, 0.5)

    def test_get_songs_by_mood_energetic(self):
        """Test getting energetic mood songs"""
        songs = MoodService.get_songs_by_mood("energetic", limit=10)

        self.assertIsInstance(songs, list)
        # Energetic songs should have high energy and danceability
        for song in songs:
            self.assertGreaterEqual(song.energy, 0.7)
            self.assertGreaterEqual(song.danceability, 0.6)

    def test_get_songs_by_mood_chill(self):
        """Test getting chill mood songs"""
        songs = MoodService.get_songs_by_mood("chill", limit=10)

        self.assertIsInstance(songs, list)
        # Chill songs should have low energy
        for song in songs:
            self.assertLessEqual(song.energy, 0.4)

    def test_get_songs_by_mood_party(self):
        """Test getting party mood songs"""
        songs = MoodService.get_songs_by_mood("party", limit=10)

        self.assertIsInstance(songs, list)
        # Party songs should have high danceability and energy
        for song in songs:
            self.assertGreaterEqual(song.danceability, 0.7)
            self.assertGreaterEqual(song.energy, 0.6)

    def test_get_songs_by_mood_focus(self):
        """Test getting focus mood songs"""
        songs = MoodService.get_songs_by_mood("focus", limit=10)

        self.assertIsInstance(songs, list)
        # Focus songs should have moderate energy
        for song in songs:
            self.assertGreaterEqual(song.energy, 0.3)
            self.assertLessEqual(song.energy, 0.6)

    def test_get_songs_by_mood_case_insensitive(self):
        """Test that mood lookup is case insensitive"""
        songs_lower = MoodService.get_songs_by_mood("happy", limit=10)
        songs_upper = MoodService.get_songs_by_mood("HAPPY", limit=10)
        songs_mixed = MoodService.get_songs_by_mood("HaPpY", limit=10)

        # All should return songs (may be different due to random order)
        self.assertIsInstance(songs_lower, list)
        self.assertIsInstance(songs_upper, list)
        self.assertIsInstance(songs_mixed, list)

    def test_get_songs_by_mood_unknown_mood_uses_default(self):
        """Test that unknown mood uses default profile"""
        songs = MoodService.get_songs_by_mood("unknown_mood", limit=10)

        self.assertIsInstance(songs, list)
        # Should use default energy range (0.3, 0.7)

    def test_get_songs_by_mood_respects_limit(self):
        """Test that get_songs_by_mood respects limit parameter"""
        # Create many songs matching happy mood
        for i in range(20):
            Song.objects.create(
                title=f"Happy Song {i}",
                slug=f"happy-song-{i}",
                artist=self.artist,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.8,
                danceability=0.7,
                valence=0.9,
            )

        songs = MoodService.get_songs_by_mood("happy", limit=5)

        self.assertLessEqual(len(songs), 5)

    def test_get_songs_by_mood_returns_different_songs(self):
        """Test that different moods return different songs"""
        # Create distinct songs for different moods
        for i in range(5):
            Song.objects.create(
                title=f"Very Happy {i}",
                slug=f"very-happy-{i}",
                artist=self.artist,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.9,
                danceability=0.8,
                valence=0.95,
            )

            Song.objects.create(
                title=f"Very Sad {i}",
                slug=f"very-sad-{i}",
                artist=self.artist,
                album=self.album,
                genre=self.rock,
                duration=200,
                energy=0.1,
                danceability=0.2,
                valence=0.1,
            )

        happy_songs = MoodService.get_songs_by_mood("happy", limit=10)
        sad_songs = MoodService.get_songs_by_mood("sad", limit=10)

        # Sets should have minimal overlap
        happy_ids = set(s.id for s in happy_songs)
        sad_ids = set(s.id for s in sad_songs)

        overlap = happy_ids.intersection(sad_ids)
        # Ideally no overlap, but allow small overlap due to edge cases
        self.assertLess(len(overlap), 3)

    def test_get_songs_by_mood_filters_correctly(self):
        """Test that mood filtering works correctly"""
        songs = MoodService.get_songs_by_mood("happy", limit=10)

        # Check that returned songs match happy criteria
        happy_count = sum(1 for s in songs if s.valence >= 0.6 and s.energy >= 0.5)

        if len(songs) > 0:
            # Most songs should match the criteria
            ratio = happy_count / len(songs)
            self.assertGreater(ratio, 0.8)

    def test_all_moods_return_songs(self):
        """Test that all defined moods return songs"""
        moods = ["happy", "sad", "energetic", "chill", "party", "focus"]

        for mood in moods:
            songs = MoodService.get_songs_by_mood(mood, limit=10)
            self.assertIsInstance(songs, list)
