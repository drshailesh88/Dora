"""Drug database and safety module.

Provides comprehensive drug information, interaction checking, safety screening,
and pricing for the Indian pharmaceutical market.
"""

# Core service
from .service import DrugService, DrugLookupResult, PrescriptionSafetyCheck

# Database
from .database import DrugDatabase

# Interactions (legacy compatibility)
from .interactions import DrugInteractionChecker, DrugInfo, DrugInteraction, InteractionSeverity

# Safety
from .safety import DrugSafetyChecker, SafetyCheckResult

# Pricing
from .pricing import IndianDrugPricing, PriceComparison, CostOptimization

# Models
from .models import (
    Drug,
    DrugFormulation,
    DrugPrice,
    PregnancySafety,
    LactationSafety,
    RenalDosingAdjustment,
    HepaticDosingAdjustment,
    PediatricDosing,
    GenericEquivalent,
    DrugAllergy,
    Contraindication,
    DrugSearchResult,
    ComprehensiveDrugInfo,
    # Enums
    TherapeuticClass,
    PregnancyCategory,
    LactationRisk,
    RenalDosing,
    HepaticDosing,
    FormulationType,
)

# UMLS client (legacy)
from .umls import UMLSClient

__all__ = [
    # Main service
    "DrugService",
    "DrugLookupResult",
    "PrescriptionSafetyCheck",
    # Database
    "DrugDatabase",
    # Interactions
    "DrugInteractionChecker",
    "DrugInfo",
    "DrugInteraction",
    "InteractionSeverity",
    # Safety
    "DrugSafetyChecker",
    "SafetyCheckResult",
    # Pricing
    "IndianDrugPricing",
    "PriceComparison",
    "CostOptimization",
    # Models
    "Drug",
    "DrugFormulation",
    "DrugPrice",
    "PregnancySafety",
    "LactationSafety",
    "RenalDosingAdjustment",
    "HepaticDosingAdjustment",
    "PediatricDosing",
    "GenericEquivalent",
    "DrugAllergy",
    "Contraindication",
    "DrugSearchResult",
    "ComprehensiveDrugInfo",
    # Enums
    "TherapeuticClass",
    "PregnancyCategory",
    "LactationRisk",
    "RenalDosing",
    "HepaticDosing",
    "FormulationType",
    # UMLS
    "UMLSClient",
]
