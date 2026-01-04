"""Personalization module for Dora medical knowledge platform.

This module provides specialty detection, query personalization, learning,
and recommendations for doctors based on their usage patterns.
"""

from src.personalization.detector import SpecialtyDetector
from src.personalization.learner import ProfileLearner
from src.personalization.models import (
    DoctorProfile,
    MedicalSpecialty,
    PersonalizationConfig,
    PracticeSetting,
    QueryCategory,
    QueryHistory,
    QueryPattern,
    SpecialtyConfidence,
)
from src.personalization.personalizer import QueryPersonalizer
from src.personalization.recommender import PersonalizedRecommender
from src.personalization.storage import PersonalizationStorage

__all__ = [
    # Models
    "DoctorProfile",
    "MedicalSpecialty",
    "PersonalizationConfig",
    "PracticeSetting",
    "QueryCategory",
    "QueryHistory",
    "QueryPattern",
    "SpecialtyConfidence",
    # Components
    "SpecialtyDetector",
    "ProfileLearner",
    "QueryPersonalizer",
    "PersonalizedRecommender",
    "PersonalizationStorage",
]
