import graphene


class CreateRadioInput(graphene.InputObjectType):
    """Input for creating a radio station"""

    name = graphene.String(required=True)
    seed_artist_id = graphene.ID()
    seed_song_id = graphene.ID()
    seed_genre_id = graphene.ID()


class UpdateTasteProfileInput(graphene.InputObjectType):
    """Input for manually updating taste profile"""

    favorite_genre_ids = graphene.List(graphene.ID)
    top_artist_ids = graphene.List(graphene.ID)
