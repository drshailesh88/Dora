"""
Medical Calculators Module

Comprehensive medical calculators for Dora platform.
50 calculators across 8 categories.
"""

from .base import (
    Calculator,
    CalculatorResult,
    RiskLevel,
    ValidationError,
    UnitConverter,
    UnitType,
    registry,
)

# Import all calculator modules
from . import cardiovascular
from . import renal
from . import hepatic
from . import pulmonary
from . import endocrine_metabolic
from . import neurology
from . import obstetrics
from . import general


# Register all calculators
def register_all_calculators():
    """Register all calculators with the global registry"""

    # Cardiovascular (10)
    registry.register("ascvd_risk", cardiovascular.ASCVDRiskCalculator())
    registry.register("cha2ds2_vasc", cardiovascular.CHA2DS2VAScCalculator())
    registry.register("has_bled", cardiovascular.HASBLEDCalculator())
    registry.register("heart_score", cardiovascular.HEARTScoreCalculator())
    registry.register("wells_dvt", cardiovascular.WellsDVTCalculator())
    registry.register("wells_pe", cardiovascular.WellsPECalculator())
    registry.register("framingham", cardiovascular.FraminghamCalculator())
    registry.register("timi_risk", cardiovascular.TIMIRiskCalculator())
    registry.register("duke_treadmill", cardiovascular.DukeTreadmillCalculator())
    registry.register("corrected_qt", cardiovascular.CorrectedQTCalculator())

    # Renal (8)
    registry.register("egfr_ckd_epi", renal.eGFRCKDEPICalculator())
    registry.register("cockcroft_gault", renal.CockcroftGaultCalculator())
    registry.register("fena", renal.FENaCalculator())
    registry.register("urine_anion_gap", renal.UrineAnionGapCalculator())
    registry.register("serum_osmolality", renal.SerumOsmolalityCalculator())
    registry.register("osmolar_gap", renal.OsmolarGapCalculator())
    registry.register("rifle_criteria", renal.RIFLECriteriaCalculator())
    registry.register("akin_criteria", renal.AKINCriteriaCalculator())

    # Hepatic (5)
    registry.register("meld", hepatic.MELDCalculator())
    registry.register("meld_na", hepatic.MELDNaCalculator())
    registry.register("child_pugh", hepatic.ChildPughCalculator())
    registry.register("fib4", hepatic.FIB4Calculator())
    registry.register("apri", hepatic.APRICalculator())

    # Pulmonary (5)
    registry.register("aa_gradient", pulmonary.AaGradientCalculator())
    registry.register("pf_ratio", pulmonary.PFRatioCalculator())
    registry.register("curb65", pulmonary.CURB65Calculator())
    registry.register("psi_port", pulmonary.PSICalculator())
    registry.register("bode_index", pulmonary.BODEIndexCalculator())

    # Endocrine/Metabolic (7)
    registry.register("bmi", endocrine_metabolic.BMICalculator())
    registry.register("bsa", endocrine_metabolic.BSACalculator())
    registry.register("ideal_body_weight", endocrine_metabolic.IdealBodyWeightCalculator())
    registry.register("adjusted_body_weight", endocrine_metabolic.AdjustedBodyWeightCalculator())
    registry.register("corrected_calcium", endocrine_metabolic.CorrectedCalciumCalculator())
    registry.register("corrected_sodium", endocrine_metabolic.CorrectedSodiumCalculator())
    registry.register("anion_gap", endocrine_metabolic.AnionGapCalculator())

    # Neurology (5)
    registry.register("glasgow_coma", neurology.GlasgowComaCalculator())
    registry.register("nih_stroke_scale", neurology.NIHStrokeScaleCalculator())
    registry.register("abcd2", neurology.ABCD2Calculator())
    registry.register("hunt_hess", neurology.HuntHessCalculator())
    registry.register("fisher_grade", neurology.FisherGradeCalculator())

    # Obstetrics (3)
    registry.register("estimated_due_date", obstetrics.EstimatedDueDateCalculator())
    registry.register("bishop_score", obstetrics.BishopScoreCalculator())
    registry.register("apgar", obstetrics.ApgarScoreCalculator())

    # General (7)
    registry.register("iv_fluid_rate", general.IVFluidRateCalculator())
    registry.register("drug_dosing", general.DrugDosingCalculator())
    registry.register("infusion_rate", general.InfusionRateCalculator())
    registry.register("unit_converter", general.MedicalUnitConverter())
    registry.register("pediatric_weight", general.PediatricWeightCalculator())
    registry.register("parkland_formula", general.ParklandFormulaCalculator())
    registry.register("maintenance_fluid", general.MaintenanceFluidCalculator())


# Auto-register on import
register_all_calculators()


# Export main components
__all__ = [
    "Calculator",
    "CalculatorResult",
    "RiskLevel",
    "ValidationError",
    "UnitConverter",
    "UnitType",
    "registry",
    "cardiovascular",
    "renal",
    "hepatic",
    "pulmonary",
    "endocrine_metabolic",
    "neurology",
    "obstetrics",
    "general",
    "register_all_calculators",
]


# Metadata
__version__ = "1.0.0"
__author__ = "Dora Medical Platform"
__description__ = "Comprehensive medical calculators for clinical decision support"

# Calculator count by category
CALCULATOR_COUNTS = {
    "cardiovascular": 10,
    "renal": 8,
    "hepatic": 5,
    "pulmonary": 5,
    "endocrine_metabolic": 7,
    "neurology": 5,
    "obstetrics": 3,
    "general": 7,
}

TOTAL_CALCULATORS = sum(CALCULATOR_COUNTS.values())
