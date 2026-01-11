from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.recommendations.services.radio_service import RadioService
from apps.recommendations.models import Radio
from apps.music.models import Song, Genre, Album
from apps.artists.models import Artist

User = get_user_model()


class RadioServiceTestCase(TestCase):
    """Unit tests for RadioService"""

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
        )

    def test_create_radio_with_artist_seed(self):
        """Test creating a radio with artist seed"""
        data = {"name": "Rock Radio", "seed_artist_id": self.artist1.id}

        radio = RadioService.create_radio(self.user, data)

        self.assertIsNotNone(radio)
        self.assertEqual(radio.name, "Rock Radio")
        self.assertEqual(radio.user, self.user)
        self.assertEqual(radio.seed_artist, self.artist1)
        self.assertIsNone(radio.seed_song)
        self.assertIsNone(radio.seed_genre)

    def test_create_radio_with_song_seed(self):
        """Test creating a radio with song seed"""
        data = {"name": "Song Radio", "seed_song_id": self.song1.id}

        radio = RadioService.create_radio(self.user, data)

        self.assertIsNotNone(radio)
        self.assertEqual(radio.seed_song, self.song1)
        self.assertIsNone(radio.seed_artist)
        self.assertIsNone(radio.seed_genre)

    def test_create_radio_with_genre_seed(self):
        """Test creating a radio with genre seed"""
        data = {"name": "Genre Radio", "seed_genre_id": self.rock.id}

        radio = RadioService.create_radio(self.user, data)

        self.assertIsNotNone(radio)
        self.assertEqual(radio.seed_genre, self.rock)
        self.assertIsNone(radio.seed_artist)
        self.assertIsNone(radio.seed_song)

    def test_create_radio_with_multiple_seeds(self):
        """Test creating a radio with multiple seeds"""
        data = {
            "name": "Multi Radio",
            "seed_artist_id": self.artist1.id,
            "seed_genre_id": self.rock.id,
        }

        radio = RadioService.create_radio(self.user, data)

        self.assertIsNotNone(radio)
        self.assertEqual(radio.seed_artist, self.artist1)
        self.assertEqual(radio.seed_genre, self.rock)

    def test_create_radio_without_name_raises_error(self):
        """Test that creating radio without name raises ValidationError"""
        data = {"seed_artist_id": self.artist1.id}

        with self.assertRaises(ValidationError) as context:
            RadioService.create_radio(self.user, data)

        self.assertIn("name is required", str(context.exception))

    def test_create_radio_with_empty_name_raises_error(self):
        """Test that creating radio with empty name raises ValidationError"""
        data = {"name": "   ", "seed_artist_id": self.artist1.id}

        with self.assertRaises(ValidationError) as context:
            RadioService.create_radio(self.user, data)

        self.assertIn("name is required", str(context.exception))

    def test_create_radio_without_seeds_raises_error(self):
        """Test that creating radio without any seed raises ValidationError"""
        data = {"name": "No Seeds Radio"}

        with self.assertRaises(ValidationError) as context:
            RadioService.create_radio(self.user, data)

        self.assertIn("At least one seed", str(context.exception))

    def test_create_radio_with_invalid_artist_raises_error(self):
        """Test that invalid artist ID raises ValidationError"""
        data = {"name": "Invalid Artist Radio", "seed_artist_id": 99999}

        with self.assertRaises(ValidationError) as context:
            RadioService.create_radio(self.user, data)

        self.assertIn("Artist with ID", str(context.exception))

    def test_create_radio_with_invalid_song_raises_error(self):
        """Test that invalid song ID raises ValidationError"""
        data = {"name": "Invalid Song Radio", "seed_song_id": 99999}

        with self.assertRaises(ValidationError) as context:
            RadioService.create_radio(self.user, data)

        self.assertIn("Song with ID", str(context.exception))

    def test_create_radio_with_invalid_genre_raises_error(self):
        """Test that invalid genre ID raises ValidationError"""
        data = {"name": "Invalid Genre Radio", "seed_genre_id": 99999}

        with self.assertRaises(ValidationError) as context:
            RadioService.create_radio(self.user, data)

        self.assertIn("Genre with ID", str(context.exception))

    def test_delete_radio_success(self):
        """Test deleting a radio station"""
        radio = Radio.objects.create(
            user=self.user, name="Test Radio", seed_artist=self.artist1
        )

        result = RadioService.delete_radio(self.user, radio.id)

        self.assertTrue(result)
        self.assertFalse(Radio.objects.filter(id=radio.id).exists())

    def test_delete_radio_invalid_id_raises_error(self):
        """Test that deleting invalid radio raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            RadioService.delete_radio(self.user, 99999)

        self.assertIn("Radio with ID", str(context.exception))

    def test_delete_radio_wrong_user_raises_error(self):
        """Test that user cannot delete another user's radio"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass"
        )

        radio = Radio.objects.create(
            user=other_user, name="Other Radio", seed_artist=self.artist1
        )

        with self.assertRaises(ValidationError):
            RadioService.delete_radio(self.user, radio.id)

    def test_generate_radio_songs_with_song_seed(self):
        """Test generating radio songs with song seed"""
        radio = Radio.objects.create(
            user=self.user, name="Song Radio", seed_song=self.song1
        )

        songs = RadioService.generate_radio_songs(radio, limit=10)

        self.assertIsInstance(songs, list)
        # Should use similar songs logic

    def test_generate_radio_songs_with_artist_seed(self):
        """Test generating radio songs with artist seed"""
        radio = Radio.objects.create(
            user=self.user, name="Artist Radio", seed_artist=self.artist1
        )

        # Create more songs from the artist
        for i in range(5):
            Song.objects.create(
                title=f"Artist Song {i}",
                slug=f"artist-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
            )

        songs = RadioService.generate_radio_songs(radio, limit=10)

        self.assertIsInstance(songs, list)

    def test_generate_radio_songs_with_genre_seed(self):
        """Test generating radio songs with genre seed"""
        radio = Radio.objects.create(
            user=self.user, name="Genre Radio", seed_genre=self.rock
        )

        # Create more songs in the genre
        for i in range(5):
            Song.objects.create(
                title=f"Rock Song {i}",
                slug=f"rock-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
            )

        songs = RadioService.generate_radio_songs(radio, limit=10)

        self.assertIsInstance(songs, list)
        # All songs should be from the genre
        for song in songs:
            self.assertEqual(song.genre, self.rock)

    def test_generate_radio_songs_respects_limit(self):
        """Test that generate_radio_songs respects limit parameter"""
        radio = Radio.objects.create(
            user=self.user, name="Genre Radio", seed_genre=self.rock
        )

        # Create many songs
        for i in range(20):
            Song.objects.create(
                title=f"Rock Song {i}",
                slug=f"rock-song-{i}",
                artist=self.artist1,
                album=self.album,
                genre=self.rock,
                duration=200,
            )

        songs = RadioService.generate_radio_songs(radio, limit=5)

        self.assertLessEqual(len(songs), 5)

    def test_radio_persists_in_database(self):
        """Test that created radio persists in database"""
        data = {"name": "Persistent Radio", "seed_artist_id": self.artist1.id}

        radio = RadioService.create_radio(self.user, data)

        # Verify it exists in database
        db_radio = Radio.objects.get(id=radio.id)
        self.assertEqual(db_radio.name, "Persistent Radio")
        self.assertEqual(db_radio.user, self.user)
        self.assertEqual(db_radio.seed_artist, self.artist1)
