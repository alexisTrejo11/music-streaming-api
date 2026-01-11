from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client

from apps.recommendations.models import UserTaste, Radio
from apps.music.models import Song, Album, Genre
from apps.artists.models import Artist
from config.schema import schema

User = get_user_model()


class RecommendationMutationsTestCase(TestCase):
    """Test cases for Recommendation GraphQL mutations"""

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

        # Create song
        self.song1 = Song.objects.create(
            title="Song 1",
            slug="song-1",
            artist=self.artist1,
            album=self.album,
            genre=self.rock,
            duration=200,
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

    # === CreateRadio Mutation ===

    def test_create_radio_with_artist_seed(self):
        """Test creating a radio station with artist seed"""
        mutation = f"""
            mutation {{
                createRadio(input: {{
                    name: "Rock Radio",
                    seedArtistId: "{self.artist1.id}"
                }}) {{
                    success
                    message
                    radio {{
                        id
                        name
                        seedArtist {{
                            id
                            name
                        }}
                    }}
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["createRadio"]["success"])
        self.assertIsNotNone(result["data"]["createRadio"]["radio"])
        self.assertEqual(result["data"]["createRadio"]["radio"]["name"], "Rock Radio")
        self.assertTrue(
            Radio.objects.filter(user=self.user, name="Rock Radio").exists()
        )

    def test_create_radio_with_song_seed(self):
        """Test creating a radio station with song seed"""
        mutation = f"""
            mutation {{
                createRadio(input: {{
                    name: "Song Radio",
                    seedSongId: "{self.song1.id}"
                }}) {{
                    success
                    message
                    radio {{
                        id
                        name
                        seedSong {{
                            id
                            title
                        }}
                    }}
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["createRadio"]["success"])
        self.assertEqual(result["data"]["createRadio"]["radio"]["name"], "Song Radio")

    def test_create_radio_with_genre_seed(self):
        """Test creating a radio station with genre seed"""
        mutation = f"""
            mutation {{
                createRadio(input: {{
                    name: "Genre Radio",
                    seedGenreId: "{self.rock.id}"
                }}) {{
                    success
                    message
                    radio {{
                        id
                        name
                        seedGenre {{
                            id
                            name
                        }}
                    }}
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["createRadio"]["success"])
        self.assertEqual(result["data"]["createRadio"]["radio"]["name"], "Genre Radio")

    def test_create_radio_with_multiple_seeds(self):
        """Test creating a radio station with multiple seeds"""
        mutation = f"""
            mutation {{
                createRadio(input: {{
                    name: "Multi Radio",
                    seedArtistId: "{self.artist1.id}",
                    seedGenreId: "{self.rock.id}"
                }}) {{
                    success
                    message
                    radio {{
                        id
                        name
                    }}
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["createRadio"]["success"])

    def test_create_radio_without_name_fails(self):
        """Test that creating radio without name fails"""
        mutation = f"""
            mutation {{
                createRadio(input: {{
                    seedArtistId: "{self.artist1.id}"
                }}) {{
                    success
                    message
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        # Should have validation error from GraphQL schema
        self.assertIsNotNone(result.get("errors"))

    def test_create_radio_without_seeds_fails(self):
        """Test that creating radio without any seed fails"""
        mutation = """
            mutation {
                createRadio(input: {
                    name: "No Seeds Radio"
                }) {
                    success
                    message
                }
            }
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["createRadio"]["success"])
        self.assertIn("seed", result["data"]["createRadio"]["message"].lower())

    def test_create_radio_with_invalid_artist_fails(self):
        """Test that creating radio with invalid artist ID fails"""
        mutation = """
            mutation {
                createRadio(input: {
                    name: "Invalid Artist Radio",
                    seedArtistId: "99999"
                }) {
                    success
                    message
                }
            }
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["createRadio"]["success"])

    def test_create_radio_requires_authentication(self):
        """Test that createRadio requires authentication"""
        mutation = f"""
            mutation {{
                createRadio(input: {{
                    name: "Test Radio",
                    seedArtistId: "{self.artist1.id}"
                }}) {{
                    success
                    message
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("Authentication required", str(result["errors"]))

    # === DeleteRadio Mutation ===

    def test_delete_radio_success(self):
        """Test deleting a radio station"""
        radio = Radio.objects.create(
            user=self.user, name="Test Radio", seed_artist=self.artist1
        )

        mutation = f"""
            mutation {{
                deleteRadio(id: "{radio.id}") {{
                    success
                    message
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["deleteRadio"]["success"])
        self.assertFalse(Radio.objects.filter(id=radio.id).exists())

    def test_delete_radio_invalid_id_fails(self):
        """Test that deleting invalid radio fails"""
        mutation = """
            mutation {
                deleteRadio(id: "99999") {
                    success
                    message
                }
            }
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["deleteRadio"]["success"])

    def test_delete_radio_wrong_user_fails(self):
        """Test that user cannot delete another user's radio"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass"
        )

        radio = Radio.objects.create(
            user=other_user, name="Other Radio", seed_artist=self.artist1
        )

        mutation = f"""
            mutation {{
                deleteRadio(id: "{radio.id}") {{
                    success
                    message
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["deleteRadio"]["success"])
        self.assertTrue(Radio.objects.filter(id=radio.id).exists())

    def test_delete_radio_requires_authentication(self):
        """Test that deleteRadio requires authentication"""
        radio = Radio.objects.create(
            user=self.user, name="Test Radio", seed_artist=self.artist1
        )

        mutation = f"""
            mutation {{
                deleteRadio(id: "{radio.id}") {{
                    success
                    message
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("Authentication required", str(result["errors"]))

    # === UpdateTasteProfile Mutation ===

    def test_update_taste_profile_with_genres(self):
        """Test updating taste profile with favorite genres"""
        mutation = f"""
            mutation {{
                updateTasteProfile(input: {{
                    favoriteGenreIds: ["{self.rock.id}", "{self.pop.id}"]
                }}) {{
                    success
                    message
                    tasteProfile {{
                        id
                        favoriteGenres {{
                            edges {{
                                node {{
                                    id
                                    name
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["updateTasteProfile"]["success"])
        self.assertIsNotNone(result["data"]["updateTasteProfile"]["tasteProfile"])

        # Verify in database
        taste = UserTaste.objects.get(user=self.user)
        self.assertEqual(taste.favorite_genres.count(), 2)

    def test_update_taste_profile_with_artists(self):
        """Test updating taste profile with top artists"""
        mutation = f"""
            mutation {{
                updateTasteProfile(input: {{
                    topArtistIds: ["{self.artist1.id}", "{self.artist2.id}"]
                }}) {{
                    success
                    message
                    tasteProfile {{
                        id
                        topArtists {{
                            edges {{
                                node {{
                                    id
                                    name
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["updateTasteProfile"]["success"])

        # Verify in database
        taste = UserTaste.objects.get(user=self.user)
        self.assertEqual(taste.top_artists.count(), 2)

    def test_update_taste_profile_with_both_genres_and_artists(self):
        """Test updating taste profile with both genres and artists"""
        mutation = f"""
            mutation {{
                updateTasteProfile(input: {{
                    favoriteGenreIds: ["{self.rock.id}"],
                    topArtistIds: ["{self.artist1.id}"]
                }}) {{
                    success
                    message
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["updateTasteProfile"]["success"])

    def test_update_taste_profile_creates_if_not_exists(self):
        """Test that updateTasteProfile creates profile if doesn't exist"""
        new_user = User.objects.create_user(
            username="newuser", email="new@example.com", password="testpass"
        )

        mutation = f"""
            mutation {{
                updateTasteProfile(input: {{
                    favoriteGenreIds: ["{self.rock.id}"]
                }}) {{
                    success
                    message
                    tasteProfile {{
                        id
                    }}
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(new_user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["updateTasteProfile"]["success"])
        self.assertTrue(UserTaste.objects.filter(user=new_user).exists())

    def test_update_taste_profile_requires_authentication(self):
        """Test that updateTasteProfile requires authentication"""
        mutation = f"""
            mutation {{
                updateTasteProfile(input: {{
                    favoriteGenreIds: ["{self.rock.id}"]
                }}) {{
                    success
                    message
                }}
            }}
        """

        result = self.client.execute(
            mutation, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("Authentication required", str(result["errors"]))

    # === RefreshTasteProfile Mutation ===

    def test_refresh_taste_profile_success(self):
        """Test refreshing taste profile based on activity"""
        mutation = """
            mutation {
                refreshTasteProfile {
                    success
                    message
                    tasteProfile {
                        id
                        energyPreference
                        danceabilityPreference
                        valencePreference
                    }
                }
            }
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["refreshTasteProfile"]["success"])
        self.assertIsNotNone(result["data"]["refreshTasteProfile"]["tasteProfile"])

    def test_refresh_taste_profile_updates_timestamp(self):
        """Test that refreshing updates the last_updated timestamp"""
        taste = UserTaste.objects.create(user=self.user)
        initial_timestamp = taste.last_updated

        mutation = """
            mutation {
                refreshTasteProfile {
                    success
                    message
                }
            }
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(self.user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["refreshTasteProfile"]["success"])

        # Verify timestamp updated
        taste.refresh_from_db()
        self.assertGreaterEqual(taste.last_updated, initial_timestamp)

    def test_refresh_taste_profile_creates_if_not_exists(self):
        """Test that refreshTasteProfile creates profile if doesn't exist"""
        new_user = User.objects.create_user(
            username="newuser", email="new@example.com", password="testpass"
        )

        mutation = """
            mutation {
                refreshTasteProfile {
                    success
                    message
                    tasteProfile {
                        id
                    }
                }
            }
        """

        result = self.client.execute(
            mutation, context_value=self._get_user_context(new_user)
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["refreshTasteProfile"]["success"])
        self.assertTrue(UserTaste.objects.filter(user=new_user).exists())

    def test_refresh_taste_profile_requires_authentication(self):
        """Test that refreshTasteProfile requires authentication"""
        mutation = """
            mutation {
                refreshTasteProfile {
                    success
                    message
                }
            }
        """

        result = self.client.execute(
            mutation, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("Authentication required", str(result["errors"]))

    # === Integration Tests ===

    def test_create_and_delete_radio_workflow(self):
        """Test complete workflow of creating and deleting a radio"""
        # Create radio
        create_mutation = f"""
            mutation {{
                createRadio(input: {{
                    name: "Workflow Radio",
                    seedArtistId: "{self.artist1.id}"
                }}) {{
                    success
                    radio {{
                        id
                    }}
                }}
            }}
        """

        create_result = self.client.execute(
            create_mutation, context_value=self._get_user_context(self.user)
        )

        self.assertTrue(create_result["data"]["createRadio"]["success"])
        radio_id = create_result["data"]["createRadio"]["radio"]["id"]

        # Decode relay ID to get actual database ID
        from graphql_relay import from_global_id

        _, db_radio_id = from_global_id(radio_id)

        # Verify radio exists before deletion
        self.assertTrue(Radio.objects.filter(id=db_radio_id).exists())

        # Delete radio (use the relay ID for the mutation)
        delete_mutation = f"""
            mutation {{
                deleteRadio(id: "{radio_id}") {{
                    success
                }}
            }}
        """

        delete_result = self.client.execute(
            delete_mutation, context_value=self._get_user_context(self.user)
        )

        # Check if there's an error message
        if not delete_result["data"]["deleteRadio"]["success"]:
            message = delete_result["data"]["deleteRadio"].get("message", "No message")
            self.fail(f"Delete failed: {message}, Full result: {delete_result}")

        self.assertTrue(delete_result["data"]["deleteRadio"]["success"])
        self.assertFalse(Radio.objects.filter(id=db_radio_id).exists())

    def test_update_and_refresh_taste_profile_workflow(self):
        """Test complete workflow of updating and refreshing taste profile"""
        # Update taste profile
        update_mutation = f"""
            mutation {{
                updateTasteProfile(input: {{
                    favoriteGenreIds: ["{self.rock.id}"]
                }}) {{
                    success
                }}
            }}
        """

        update_result = self.client.execute(
            update_mutation, context_value=self._get_user_context(self.user)
        )

        self.assertTrue(update_result["data"]["updateTasteProfile"]["success"])

        # Refresh taste profile
        refresh_mutation = """
            mutation {
                refreshTasteProfile {
                    success
                    tasteProfile {
                        favoriteGenres {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        """

        refresh_result = self.client.execute(
            refresh_mutation, context_value=self._get_user_context(self.user)
        )

        self.assertTrue(refresh_result["data"]["refreshTasteProfile"]["success"])
