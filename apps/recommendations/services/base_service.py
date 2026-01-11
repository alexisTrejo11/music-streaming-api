from django.core.exceptions import ValidationError
from typing import Dict, List, Tuple
import numpy as np


class BaseRecommendationService:
    """Base class with common recommendation utilities"""

    @staticmethod
    def _calculate_audio_similarity(
        song,
        target_energy: float,
        target_danceability: float,
        target_valence: float,
    ) -> float:
        """Calculate similarity between song and target audio features"""
        if not all([song.energy, song.danceability, song.valence]):
            return 0.0

        # Calculate Euclidean distance
        distance = np.sqrt(
            (song.energy - target_energy) ** 2
            + (song.danceability - target_danceability) ** 2
            + (song.valence - target_valence) ** 2
        )

        # Normalize to 0-1 similarity (max distance is sqrt(3))
        max_distance = np.sqrt(3)
        similarity = 1 - (distance / max_distance)

        return float(similarity)

    @staticmethod
    def _get_next_monday():
        """Get next Monday date for Discover Weekly refresh"""
        from datetime import datetime, timedelta
        from django.utils import timezone

        today = timezone.now()
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)
