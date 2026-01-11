"""
Main recommendation GraphQL schema module.

This file provides backward compatibility by re-exporting everything.
New code should import from specific submodules.
"""

from .types import (
    UserTasteType,
    RadioType,
    RecommendationReasonType,
    RecommendedSongType,
    DiscoverWeeklyType,
    AudioPreferencesType,
)

from .inputs import CreateRadioInput, UpdateTasteProfileInput

from .queries import RecommendationQuery
from .mutations import (
    RecommendationMutation,
    CreateRadio,
    DeleteRadio,
    UpdateTasteProfile,
    RefreshTasteProfile,
)

__all__ = [
    # Types
    "UserTasteType",
    "RadioType",
    "RecommendationReasonType",
    "RecommendedSongType",
    "DiscoverWeeklyType",
    "AudioPreferencesType",
    # Inputs
    "CreateRadioInput",
    "UpdateTasteProfileInput",
    # Query classes
    "RecommendationQuery",
    # Mutation classes
    "RecommendationMutation",
    "CreateRadio",
    "DeleteRadio",
    "UpdateTasteProfile",
    "RefreshTasteProfile",
]


class Query(RecommendationQuery):
    """Combined Query class for recommendations"""

    pass


class Mutation(RecommendationMutation):
    """Combined Mutation class for recommendations"""

    pass
