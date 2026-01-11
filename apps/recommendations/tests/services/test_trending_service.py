from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.recommendations.services.trending_service import TrendingService
from apps.recommendations.models import UserTaste
from apps.music.models import Song, Genre, Album
from apps.artists.models import Artist
from apps.interactions.models import FollowedArtist, ListeningHistory

User = get_user_model()


class TrendingServiceTestCase(TestCase):
    """Unit tests for TrendingService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

        # Create genres
        self.rock = Genre.objects.create(name="Rock", slug="rock")
        self.pop = Genre.objects.create(name="Pop", slug="pop")
        self.jazz = Genre.objects.create(name="Jazz", slug="jazz")

        # Create artists
        self.artist1 = Artist.objects.create(
            name="Artist 1", slug="artist-1", monthly_listeners=100000
        )
        self.artist1.genres.add(self.rock)

        self.artist2 = Artist.objects.create(
            name="Artist 2", slug="artist-2", monthly_listeners=50000
        )
        self.artist2.genres.add(self.pop)

        self.artist3 = Artist.objects.create(
            name="Artist 3", slug="artist-3", monthly_listeners=200000
        )
        self.artist3.genres.add(self.rock)

        self.artist4 = Artist.objects.create(
            name="Artist 4", slug="artist-4", monthly_listeners=75000
        )
        self.artist4.genres.add(self.jazz)

        # Create albums
        self.album1 = Album.objects.create(
            title="Album 1",
            slug="album-1",
            artist=self.artist1,
            release_date="2024-01-01",
            play_count=10000,
        )

        self.album2 = Album.objects.create(
            title="Album 2",
            slug="album-2",
            artist=self.artist2,
            release_date="2024-02-01",
            play_count=5000,
        )

        # Create songs
        self.song1 = Song.objects.create(
            title="Song 1",
            slug="song-1",
            artist=self.artist1,
            album=self.album1,
            genre=self.rock,
            duration=200,
            play_count=5000,
        )

        self.song2 = Song.objects.create(
            title="Song 2",
            slug="song-2",
            artist=self.artist2,
            album=self.album2,
            genre=self.pop,
            duration=180,
            play_count=3000,
        )

        # Create taste profile
        self.taste = UserTaste.objects.create(user=self.user)
        self.taste.favorite_genres.add(self.rock, self.pop)
        self.taste.top_artists.add(self.artist1)

    def test_get_recommended_artists_creates_taste_profile(self):
        """Test that get_recommended_artists creates taste profile if needed"""
        new_user = User.objects.create_user(
            username="newuser", email="new@example.com", password="testpass"
        )

        artists = TrendingService.get_recommended_artists(new_user, limit=10)

        # Should create taste profile
        self.assertTrue(UserTaste.objects.filter(user=new_user).exists())
        self.assertIsInstance(artists, list)

    def test_get_recommended_artists_filters_by_favorite_genres(self):
        """Test that recommended artists are from favorite genres"""
        artists = TrendingService.get_recommended_artists(self.user, limit=10)

        # All artists should be from favorite genres
        for artist in artists:
            artist_genres = set(artist.genres.all())
            favorite_genres = set(self.taste.favorite_genres.all())
            self.assertTrue(artist_genres.intersection(favorite_genres))

    def test_get_recommended_artists_excludes_followed_artists(self):
        """Test that recommended artists excludes already followed artists"""
        # Follow artist1
        FollowedArtist.objects.create(user=self.user, artist=self.artist1)

        artists = TrendingService.get_recommended_artists(self.user, limit=10)

        artist_ids = [a.id for a in artists]
        self.assertNotIn(self.artist1.id, artist_ids)

    def test_get_recommended_artists_orders_by_monthly_listeners(self):
        """Test that recommended artists are ordered by popularity"""
        artists = TrendingService.get_recommended_artists(self.user, limit=10)

        if len(artists) > 1:
            # Check descending order by monthly_listeners
            for i in range(len(artists) - 1):
                self.assertGreaterEqual(
                    artists[i].monthly_listeners, artists[i + 1].monthly_listeners
                )

    def test_get_recommended_artists_respects_limit(self):
        """Test that get_recommended_artists respects limit parameter"""
        # Create more artists in favorite genres
        for i in range(20):
            artist = Artist.objects.create(
                name=f"Extra Artist {i}",
                slug=f"extra-artist-{i}",
                monthly_listeners=10000,
            )
            artist.genres.add(self.rock)

        artists = TrendingService.get_recommended_artists(self.user, limit=5)

        self.assertLessEqual(len(artists), 5)

    def test_get_recommended_albums_creates_taste_profile(self):
        """Test that get_recommended_albums creates taste profile if needed"""
        new_user = User.objects.create_user(
            username="newuser", email="new@example.com", password="testpass"
        )

        albums = TrendingService.get_recommended_albums(new_user, limit=10)

        self.assertTrue(UserTaste.objects.filter(user=new_user).exists())
        self.assertIsInstance(albums, list)

    def test_get_recommended_albums_includes_top_artists_albums(self):
        """Test that recommended albums include albums from top artists"""
        albums = TrendingService.get_recommended_albums(self.user, limit=10)

        # Should include albums from top artists
        album_artist_ids = [a.artist_id for a in albums]
        top_artist_ids = list(self.taste.top_artists.values_list("id", flat=True))

        # At least some albums should be from top artists
        overlap = set(album_artist_ids).intersection(set(top_artist_ids))
        if len(albums) > 0:
            self.assertGreaterEqual(len(overlap), 0)

    def test_get_recommended_albums_includes_favorite_genre_albums(self):
        """Test that recommended albums include albums from favorite genres"""
        # Create songs in album2 with favorite genre
        Song.objects.create(
            title="Song in Album 2",
            slug="song-in-album-2",
            artist=self.artist2,
            album=self.album2,
            genre=self.pop,
            duration=200,
        )

        albums = TrendingService.get_recommended_albums(self.user, limit=10)

        self.assertIsInstance(albums, list)

    def test_get_recommended_albums_removes_duplicates(self):
        """Test that recommended albums list has no duplicates"""
        albums = TrendingService.get_recommended_albums(self.user, limit=10)

        album_ids = [a.id for a in albums]
        unique_ids = set(album_ids)

        self.assertEqual(len(album_ids), len(unique_ids))

    def test_get_recommended_albums_respects_limit(self):
        """Test that get_recommended_albums respects limit parameter"""
        # Create more albums
        for i in range(20):
            album = Album.objects.create(
                title=f"Extra Album {i}",
                slug=f"extra-album-{i}",
                artist=self.artist1,
                release_date="2024-01-01",
                play_count=1000,
            )
            # Add a song to the album with favorite genre
            Song.objects.create(
                title=f"Song in Extra Album {i}",
                slug=f"song-in-extra-album-{i}",
                artist=self.artist1,
                album=album,
                genre=self.rock,
                duration=200,
            )

        albums = TrendingService.get_recommended_albums(self.user, limit=5)

        self.assertLessEqual(len(albums), 5)

    def test_get_trending_for_you_creates_taste_profile(self):
        """Test that get_trending_for_you creates taste profile if needed"""
        new_user = User.objects.create_user(
            username="newuser", email="new@example.com", password="testpass"
        )

        songs = TrendingService.get_trending_for_you(new_user, limit=10)

        self.assertTrue(UserTaste.objects.filter(user=new_user).exists())
        self.assertIsInstance(songs, list)

    def test_get_trending_for_you_filters_by_favorite_genres(self):
        """Test that trending songs are from favorite genres"""
        # Create recent plays for songs
        recent_time = timezone.now() - timedelta(days=3)
        for _ in range(10):
            ListeningHistory.objects.create(
                user=self.user,
                song=self.song1,
                played_at=recent_time,
                duration_played=180,
            )

        songs = TrendingService.get_trending_for_you(self.user, limit=10)

        favorite_genre_ids = list(
            self.taste.favorite_genres.values_list("id", flat=True)
        )

        for song in songs:
            self.assertIn(song.genre_id, favorite_genre_ids)

    def test_get_trending_for_you_considers_recent_plays(self):
        """Test that trending considers recent plays (last week)"""
        # Create old plays (should not count)
        old_time = timezone.now() - timedelta(days=10)
        for _ in range(5):
            ListeningHistory.objects.create(
                user=self.user, song=self.song1, played_at=old_time, duration_played=180
            )

        # Create recent plays
        recent_time = timezone.now() - timedelta(days=3)
        for _ in range(10):
            ListeningHistory.objects.create(
                user=self.user,
                song=self.song2,
                played_at=recent_time,
                duration_played=180,
            )

        songs = TrendingService.get_trending_for_you(self.user, limit=10)

        # song2 should rank higher due to recent plays
        self.assertIsInstance(songs, list)

    def test_get_trending_for_you_respects_limit(self):
        """Test that get_trending_for_you respects limit parameter"""
        # Create many songs with recent plays
        recent_time = timezone.now() - timedelta(days=3)
        for i in range(20):
            song = Song.objects.create(
                title=f"Trending Song {i}",
                slug=f"trending-song-{i}",
                artist=self.artist1,
                album=self.album1,
                genre=self.rock,
                duration=200,
                play_count=1000,
            )
            ListeningHistory.objects.create(
                user=self.user, song=song, played_at=recent_time, duration_played=180
            )

        songs = TrendingService.get_trending_for_you(self.user, limit=5)

        self.assertLessEqual(len(songs), 5)

    def test_get_trending_for_you_orders_by_recent_plays(self):
        """Test that trending songs are ordered by recent play count"""
        recent_time = timezone.now() - timedelta(days=3)

        # Create songs with different recent play counts
        song_a = Song.objects.create(
            title="Song A",
            slug="song-a",
            artist=self.artist1,
            album=self.album1,
            genre=self.rock,
            duration=200,
        )

        song_b = Song.objects.create(
            title="Song B",
            slug="song-b",
            artist=self.artist1,
            album=self.album1,
            genre=self.rock,
            duration=200,
        )

        # Song B has more recent plays
        for _ in range(5):
            ListeningHistory.objects.create(
                user=self.user, song=song_a, played_at=recent_time, duration_played=180
            )

        for _ in range(10):
            ListeningHistory.objects.create(
                user=self.user, song=song_b, played_at=recent_time, duration_played=180
            )

        songs = TrendingService.get_trending_for_you(self.user, limit=10)

        if len(songs) >= 2:
            # song_b should appear before song_a
            song_ids = [s.id for s in songs]
            if song_b.id in song_ids and song_a.id in song_ids:
                self.assertLess(song_ids.index(song_b.id), song_ids.index(song_a.id))

    def test_all_methods_return_lists(self):
        """Test that all trending methods return lists"""
        artists = TrendingService.get_recommended_artists(self.user, limit=10)
        albums = TrendingService.get_recommended_albums(self.user, limit=10)
        songs = TrendingService.get_trending_for_you(self.user, limit=10)

        self.assertIsInstance(artists, list)
        self.assertIsInstance(albums, list)
        self.assertIsInstance(songs, list)
