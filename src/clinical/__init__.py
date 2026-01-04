"""
Clinical Decision Support Module for Dora

Comprehensive clinical tools for medical decision support.

Modules:
- differential: Differential diagnosis generation
- lab_interpreter: Laboratory result interpretation
- dosing: Drug dosing with renal/hepatic adjustments
- protocols: Evidence-based treatment protocols
- antibiotics: Antibiotic stewardship recommendations
- risk: Clinical risk stratification calculators
- alerts: Clinical safety alerts

Author: DocAssist Dora Project
Version: 1.0.0
"""

from .differential import generate_differential_diagnosis, DifferentialDiagnosisGenerator
from .lab_interpreter import interpret_labs, LabInterpreter
from .dosing import get_dosing_recommendation, DosingCalculator
from .protocols import get_treatment_protocol, ProtocolEngine
from .antibiotics import get_antibiotic_recommendation, AntibioticStewardship
from .risk import calculate_risk_score, RiskCalculator
from .alerts import check_clinical_alerts, AlertEngine

__all__ = [
    # Functions
    'generate_differential_diagnosis',
    'interpret_labs',
    'get_dosing_recommendation',
    'get_treatment_protocol',
    'get_antibiotic_recommendation',
    'calculate_risk_score',
    'check_clinical_alerts',
    # Classes
    'DifferentialDiagnosisGenerator',
    'LabInterpreter',
    'DosingCalculator',
    'ProtocolEngine',
    'AntibioticStewardship',
    'RiskCalculator',
    'AlertEngine',
]

__version__ = '1.0.0'
__author__ = 'DocAssist Dora Project'

# Medical disclaimer
MEDICAL_DISCLAIMER = """
MEDICAL DISCLAIMER:
This clinical decision support system is for educational and clinical decision
support purposes only. It does not replace clinical judgment, diagnostic testing,
or consultation with qualified healthcare professionals.

All recommendations should be:
1. Verified with current evidence-based guidelines
2. Individualized to patient-specific factors
3. Reviewed by licensed healthcare providers
4. Updated based on local protocols and resistance patterns

Not for use as a sole diagnostic or treatment tool.
Use at your own risk and professional discretion.
"""
