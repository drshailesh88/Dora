"""Comprehensive drug data models for the Dora medical platform.

This module defines all data structures for drugs, interactions, safety,
dosing, formulations, and pricing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TherapeuticClass(str, Enum):
    """Major therapeutic drug classes."""

    CARDIOVASCULAR = "cardiovascular"
    ANTIDIABETIC = "antidiabetic"
    ANTIBIOTIC = "antibiotic"
    ANALGESIC = "analgesic"
    GASTROINTESTINAL = "gastrointestinal"
    PSYCHIATRIC = "psychiatric"
    NEUROLOGICAL = "neurological"
    RESPIRATORY = "respiratory"
    ENDOCRINE = "endocrine"
    DERMATOLOGICAL = "dermatological"
    HEMATOLOGICAL = "hematological"
    IMMUNOSUPPRESSANT = "immunosuppressant"
    ONCOLOGY = "oncology"
    OPHTHALMOLOGICAL = "ophthalmological"
    OTHER = "other"


class InteractionSeverity(str, Enum):
    """Drug interaction severity levels."""

    CONTRAINDICATED = "contraindicated"  # Never use together
    MAJOR = "major"  # Serious - avoid combination
    MODERATE = "moderate"  # Monitor closely
    MINOR = "minor"  # Usually safe, minimal monitoring
    UNKNOWN = "unknown"


class PregnancyCategory(str, Enum):
    """FDA pregnancy categories."""

    A = "A"  # Controlled studies show no risk
    B = "B"  # No evidence of risk in humans
    C = "C"  # Risk cannot be ruled out
    D = "D"  # Positive evidence of risk
    X = "X"  # Contraindicated in pregnancy
    UNKNOWN = "UNKNOWN"


class LactationRisk(str, Enum):
    """Lactation risk levels (Hale's categories)."""

    L1 = "L1"  # Safest - compatible with breastfeeding
    L2 = "L2"  # Safer - studied, no increase in adverse effects
    L3 = "L3"  # Moderately safe - no controlled studies
    L4 = "L4"  # Possibly hazardous - evidence of risk
    L5 = "L5"  # Contraindicated - significant risk
    UNKNOWN = "UNKNOWN"


class RenalDosing(str, Enum):
    """Renal function categories (GFR-based)."""

    NORMAL = "normal"  # GFR > 90
    MILD = "mild"  # GFR 60-89
    MODERATE = "moderate"  # GFR 30-59
    SEVERE = "severe"  # GFR 15-29
    ESRD = "esrd"  # GFR < 15 or dialysis


class HepaticDosing(str, Enum):
    """Hepatic function categories (Child-Pugh)."""

    NORMAL = "normal"
    CHILD_A = "child_a"  # Mild
    CHILD_B = "child_b"  # Moderate
    CHILD_C = "child_c"  # Severe


class FormulationType(str, Enum):
    """Drug formulation types."""

    TABLET = "tablet"
    CAPSULE = "capsule"
    SYRUP = "syrup"
    SUSPENSION = "suspension"
    INJECTION = "injection"
    CREAM = "cream"
    OINTMENT = "ointment"
    DROPS = "drops"
    INHALER = "inhaler"
    SUPPOSITORY = "suppository"
    PATCH = "patch"
    OTHER = "other"


@dataclass
class Drug:
    """Complete drug information."""

    id: str
    generic_name: str
    brand_names: list[str] = field(default_factory=list)
    indian_brand_names: list[str] = field(default_factory=list)
    therapeutic_class: TherapeuticClass = TherapeuticClass.OTHER
    mechanism_of_action: str = ""
    indications: list[str] = field(default_factory=list)
    contraindications: list[str] = field(default_factory=list)
    common_side_effects: list[str] = field(default_factory=list)
    serious_side_effects: list[str] = field(default_factory=list)

    # Identifiers
    rxcui: Optional[str] = None
    atc_code: Optional[str] = None

    # Dosing
    adult_dose: Optional[str] = None
    max_dose_per_day: Optional[str] = None

    # Safety
    pregnancy_category: PregnancyCategory = PregnancyCategory.UNKNOWN
    lactation_risk: LactationRisk = LactationRisk.UNKNOWN

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DrugInteraction:
    """Drug-drug interaction details."""

    id: str
    drug1_id: str
    drug1_name: str
    drug2_id: str
    drug2_name: str
    severity: InteractionSeverity
    mechanism: str
    clinical_significance: str
    management_strategy: str
    alternative_suggestions: list[str] = field(default_factory=list)
    source: str = "Dora Database"
    evidence_level: str = "Expert Opinion"  # Controlled Study, Case Reports, etc.
    references: list[str] = field(default_factory=list)


@dataclass
class PregnancySafety:
    """Pregnancy safety information."""

    drug_id: str
    drug_name: str
    category: PregnancyCategory
    trimester_specific: dict[str, str] = field(default_factory=dict)  # first, second, third
    description: str = ""
    fetal_risks: list[str] = field(default_factory=list)
    maternal_risks: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


@dataclass
class LactationSafety:
    """Lactation safety information."""

    drug_id: str
    drug_name: str
    risk_category: LactationRisk
    description: str = ""
    infant_risks: list[str] = field(default_factory=list)
    monitoring_parameters: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    peak_levels_timing: Optional[str] = None  # e.g., "2-3 hours after dose"
    references: list[str] = field(default_factory=list)


@dataclass
class RenalDosingAdjustment:
    """Renal dosing adjustment information."""

    drug_id: str
    drug_name: str
    gfr_category: RenalDosing
    dose_adjustment: str
    frequency_adjustment: Optional[str] = None
    supplemental_dose_dialysis: Optional[str] = None
    monitoring_parameters: list[str] = field(default_factory=list)
    precautions: list[str] = field(default_factory=list)


@dataclass
class HepaticDosingAdjustment:
    """Hepatic dosing adjustment information."""

    drug_id: str
    drug_name: str
    hepatic_category: HepaticDosing
    dose_adjustment: str
    contraindicated: bool = False
    monitoring_parameters: list[str] = field(default_factory=list)
    precautions: list[str] = field(default_factory=list)


@dataclass
class PediatricDosing:
    """Pediatric dosing information."""

    drug_id: str
    drug_name: str
    age_group: str  # e.g., "neonate", "infant", "child", "adolescent"
    min_age: Optional[str] = None
    max_age: Optional[str] = None
    weight_based_formula: Optional[str] = None  # e.g., "10 mg/kg/day"
    age_based_dose: Optional[str] = None
    max_single_dose: Optional[str] = None
    max_daily_dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    precautions: list[str] = field(default_factory=list)


@dataclass
class DrugFormulation:
    """Drug formulation details."""

    id: str
    drug_id: str
    drug_name: str
    formulation_type: FormulationType
    strength: str
    route: str  # oral, IV, IM, topical, etc.
    manufacturer: Optional[str] = None
    is_generic: bool = True
    prescription_required: bool = True


@dataclass
class GenericEquivalent:
    """Generic alternative information."""

    drug_id: str
    brand_name: str
    generic_name: str
    generic_alternatives: list[str] = field(default_factory=list)
    bioequivalent: bool = True
    cost_savings_percent: Optional[float] = None
    therapeutic_equivalence_code: Optional[str] = None  # AB, AA, etc.


@dataclass
class DrugPrice:
    """Indian drug pricing information."""

    drug_id: str
    drug_name: str
    formulation: str
    strength: str
    manufacturer: str
    is_generic: bool
    mrp: float  # Maximum Retail Price in INR
    pharmacy_price: Optional[float] = None
    online_price: Optional[float] = None
    nlem_drug: bool = False  # National List of Essential Medicines
    price_controlled: bool = False
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DrugAllergy:
    """Drug allergy and cross-reactivity information."""

    drug_id: str
    drug_name: str
    drug_class: str
    cross_reactive_classes: list[str] = field(default_factory=list)
    cross_reactive_drugs: list[str] = field(default_factory=list)
    safe_alternatives: list[str] = field(default_factory=list)


@dataclass
class Contraindication:
    """Drug contraindication information."""

    drug_id: str
    drug_name: str
    condition: str
    severity: str  # "absolute" or "relative"
    rationale: str
    alternatives: list[str] = field(default_factory=list)


@dataclass
class DrugSearchResult:
    """Drug search result."""

    drug_id: str
    generic_name: str
    brand_names: list[str]
    therapeutic_class: str
    relevance_score: float = 1.0
    match_type: str = "exact"  # exact, fuzzy, partial


@dataclass
class ComprehensiveDrugInfo:
    """Comprehensive drug information aggregation."""

    drug: Drug
    formulations: list[DrugFormulation] = field(default_factory=list)
    interactions: list[DrugInteraction] = field(default_factory=list)
    pregnancy_safety: Optional[PregnancySafety] = None
    lactation_safety: Optional[LactationSafety] = None
    renal_dosing: list[RenalDosingAdjustment] = field(default_factory=list)
    hepatic_dosing: list[HepaticDosingAdjustment] = field(default_factory=list)
    pediatric_dosing: list[PediatricDosing] = field(default_factory=list)
    pricing: list[DrugPrice] = field(default_factory=list)
    generic_alternatives: Optional[GenericEquivalent] = None
    allergies: list[DrugAllergy] = field(default_factory=list)
    contraindications: list[Contraindication] = field(default_factory=list)
