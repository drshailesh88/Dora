"""
Laboratory Results Interpreter for Clinical Decision Support

This module interprets common laboratory panels and provides clinical correlations.

MEDICAL DISCLAIMER:
This tool is for educational and clinical decision support purposes only.
Laboratory values must be interpreted in clinical context. Reference ranges
may vary by laboratory. Consult laboratory-specific ranges and clinical judgment.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class Abnormality(Enum):
    """Severity of lab abnormality"""
    CRITICAL = "critical"  # Immediately life-threatening
    SEVERE = "severe"      # Significantly abnormal
    MODERATE = "moderate"  # Abnormal, needs attention
    MILD = "mild"          # Slightly out of range
    NORMAL = "normal"      # Within reference range


@dataclass
class LabResult:
    """Individual laboratory test result"""
    test_name: str
    value: float
    unit: str
    reference_low: float
    reference_high: float
    is_abnormal: bool = False
    severity: Abnormality = Abnormality.NORMAL


@dataclass
class Interpretation:
    """Clinical interpretation of lab finding"""
    finding: str
    severity: Abnormality
    possible_causes: List[str]
    clinical_significance: str
    recommended_actions: List[str]
    follow_up_tests: List[str] = field(default_factory=list)


class LabInterpreter:
    """
    Interprets laboratory results and provides clinical correlation.

    Covers common panels: CBC, CMP, LFT, thyroid, lipids, coagulation, UA, ABG, CSF
    """

    def __init__(self):
        self._initialize_reference_ranges()

    def _initialize_reference_ranges(self):
        """Initialize standard reference ranges (adult values)"""
        self.reference_ranges = {
            # CBC
            'wbc': (4.5, 11.0, 'K/uL'),
            'hemoglobin': (13.5, 17.5, 'g/dL'),  # Male reference; adjust for female
            'hematocrit': (38.8, 50.0, '%'),     # Male
            'platelet': (150, 400, 'K/uL'),
            'neutrophil_percent': (40, 70, '%'),
            'lymphocyte_percent': (20, 40, '%'),
            'mcv': (80, 100, 'fL'),
            'mch': (27, 33, 'pg'),
            'mchc': (32, 36, 'g/dL'),

            # CMP/BMP
            'sodium': (136, 145, 'mEq/L'),
            'potassium': (3.5, 5.0, 'mEq/L'),
            'chloride': (98, 107, 'mEq/L'),
            'bicarbonate': (22, 29, 'mEq/L'),
            'bun': (7, 20, 'mg/dL'),
            'creatinine': (0.7, 1.3, 'mg/dL'),  # Male
            'glucose': (70, 100, 'mg/dL'),  # Fasting
            'calcium': (8.5, 10.5, 'mg/dL'),

            # LFT
            'ast': (10, 40, 'U/L'),
            'alt': (7, 56, 'U/L'),
            'alkaline_phosphatase': (40, 130, 'U/L'),
            'total_bilirubin': (0.1, 1.2, 'mg/dL'),
            'direct_bilirubin': (0.0, 0.3, 'mg/dL'),
            'albumin': (3.5, 5.5, 'g/dL'),
            'total_protein': (6.0, 8.3, 'g/dL'),

            # Thyroid
            'tsh': (0.4, 4.0, 'mIU/L'),
            'free_t4': (0.8, 1.8, 'ng/dL'),
            'free_t3': (2.3, 4.2, 'pg/mL'),

            # Lipids
            'total_cholesterol': (0, 200, 'mg/dL'),  # Desirable <200
            'ldl': (0, 100, 'mg/dL'),  # Optimal <100
            'hdl': (40, float('inf'), 'mg/dL'),  # Higher is better, >60 protective
            'triglycerides': (0, 150, 'mg/dL'),

            # Coagulation
            'pt': (11, 13.5, 'seconds'),
            'inr': (0.8, 1.1, 'ratio'),
            'ptt': (25, 35, 'seconds'),

            # Other
            'troponin': (0, 0.04, 'ng/mL'),  # High-sensitivity varies
            'bnp': (0, 100, 'pg/mL'),
            'd_dimer': (0, 500, 'ng/mL'),
            'crp': (0, 3.0, 'mg/L'),
            'esr': (0, 20, 'mm/hr'),  # Male; female <30
        }

    def interpret_cbc(self, labs: Dict[str, float], gender: str = 'M', age: int = 40) -> List[Interpretation]:
        """
        Interpret Complete Blood Count (CBC)

        Args:
            labs: Dictionary with test names as keys (wbc, hemoglobin, platelet, etc.)
            gender: "M" or "F" for gender-specific reference ranges
            age: Patient age in years

        Returns:
            List of Interpretation objects
        """
        interpretations = []

        # Adjust reference ranges for gender
        hgb_low = 13.5 if gender == 'M' else 12.0
        hgb_high = 17.5 if gender == 'M' else 15.5

        # WHITE BLOOD CELL COUNT
        if 'wbc' in labs:
            wbc = labs['wbc']
            if wbc > 11.0:
                if wbc > 30:
                    severity = Abnormality.CRITICAL
                    causes = [
                        "Leukemia or leukemoid reaction",
                        "Severe infection/sepsis",
                        "Extreme stress (burns, trauma)"
                    ]
                    actions = [
                        "Immediate hematology consult",
                        "Peripheral blood smear",
                        "Flow cytometry if blast cells present",
                        "Bone marrow biopsy consideration"
                    ]
                elif wbc > 15:
                    severity = Abnormality.SEVERE
                    causes = [
                        "Bacterial infection",
                        "Inflammatory process",
                        "Corticosteroid use",
                        "Malignancy (leukemia, solid tumor)",
                        "Acute stress (MI, trauma)"
                    ]
                    actions = [
                        "Review differential count",
                        "Look for left shift (bands >10%)",
                        "Evaluate for infection source",
                        "Consider peripheral smear"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    causes = [
                        "Infection (viral or bacterial)",
                        "Inflammation",
                        "Smoking",
                        "Medications (steroids, G-CSF)",
                        "Physiologic (pregnancy, stress)"
                    ]
                    actions = [
                        "Check differential count",
                        "Clinical correlation for infection",
                        "Repeat if persistent"
                    ]

                interpretations.append(Interpretation(
                    finding=f"Leukocytosis (WBC {wbc} K/uL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance="Elevated WBC suggests infection, inflammation, or hematologic disorder",
                    recommended_actions=actions,
                    follow_up_tests=["CBC with differential", "Peripheral blood smear"]
                ))

            elif wbc < 4.5:
                if wbc < 1.0:
                    severity = Abnormality.CRITICAL
                    causes = [
                        "Severe bone marrow suppression",
                        "Chemotherapy/radiation",
                        "Severe infection (overwhelming sepsis)",
                        "Bone marrow failure/aplastic anemia"
                    ]
                    actions = [
                        "Neutropenic precautions",
                        "Consider G-CSF",
                        "Hematology consult",
                        "Bone marrow biopsy",
                        "Empiric antibiotics if febrile"
                    ]
                elif wbc < 3.0:
                    severity = Abnormality.SEVERE
                    causes = [
                        "Bone marrow suppression (medications)",
                        "Viral infection",
                        "Autoimmune disorder",
                        "Nutritional deficiency (B12, folate, copper)"
                    ]
                    actions = [
                        "Check ANC (absolute neutrophil count)",
                        "Review medications",
                        "Consider B12, folate levels",
                        "Repeat CBC"
                    ]
                else:
                    severity = Abnormality.MILD
                    causes = [
                        "Benign ethnic neutropenia",
                        "Viral infection",
                        "Medications",
                        "Chronic idiopathic"
                    ]
                    actions = [
                        "Check differential",
                        "Establish baseline if chronic",
                        "Monitor"
                    ]

                interpretations.append(Interpretation(
                    finding=f"Leukopenia (WBC {wbc} K/uL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance="Low WBC increases infection risk, especially if neutropenic",
                    recommended_actions=actions,
                    follow_up_tests=["CBC with differential", "B12, folate", "HIV test if risk factors"]
                ))

        # HEMOGLOBIN/ANEMIA
        if 'hemoglobin' in labs:
            hgb = labs['hemoglobin']
            if hgb < hgb_low:
                if hgb < 7.0:
                    severity = Abnormality.CRITICAL
                    significance = "Severe anemia - symptomatic, may need transfusion"
                    actions = [
                        "Consider RBC transfusion if symptomatic",
                        "Urgent workup for cause",
                        "Hemodynamic monitoring",
                        "Type and cross"
                    ]
                elif hgb < 10.0:
                    severity = Abnormality.SEVERE
                    significance = "Moderate anemia - likely symptomatic"
                    actions = [
                        "Complete anemia workup",
                        "Transfusion if symptomatic or CAD",
                        "Identify and treat cause"
                    ]
                else:
                    severity = Abnormality.MILD
                    significance = "Mild anemia - may be asymptomatic"
                    actions = [
                        "Anemia workup",
                        "Outpatient management appropriate"
                    ]

                # Classify anemia by MCV if available
                causes = []
                if 'mcv' in labs:
                    mcv = labs['mcv']
                    if mcv < 80:
                        causes = [
                            "Iron deficiency (most common)",
                            "Thalassemia",
                            "Anemia of chronic disease",
                            "Lead poisoning",
                            "Sideroblastic anemia"
                        ]
                        follow_up = ["Iron studies (ferritin, TIBC, serum iron)", "Reticulocyte count", "Hemoglobin electrophoresis if thalassemia suspected"]
                    elif mcv > 100:
                        causes = [
                            "B12 deficiency",
                            "Folate deficiency",
                            "Alcohol use",
                            "Medications (methotrexate, hydroxyurea, AZT)",
                            "Liver disease",
                            "Hypothyroidism",
                            "Myelodysplastic syndrome"
                        ]
                        follow_up = ["B12, folate levels", "TSH", "Reticulocyte count", "Peripheral smear", "LFTs"]
                    else:
                        causes = [
                            "Anemia of chronic disease",
                            "Acute blood loss",
                            "Hemolysis",
                            "Chronic kidney disease",
                            "Mixed deficiency"
                        ]
                        follow_up = ["Reticulocyte count", "Haptoglobin, LDH (if hemolysis)", "CMP (kidney function)", "Stool guaiac"]
                else:
                    causes = ["Require MCV to classify anemia"]
                    follow_up = ["Complete CBC with indices", "Reticulocyte count"]

                interpretations.append(Interpretation(
                    finding=f"Anemia (Hemoglobin {hgb} g/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=follow_up
                ))

            elif hgb > hgb_high:
                if hgb > 18:
                    severity = Abnormality.SEVERE
                    causes = [
                        "Polycythemia vera",
                        "Secondary polycythemia (hypoxia, COPD, smoking)",
                        "Testosterone use",
                        "EPO-secreting tumor"
                    ]
                    actions = [
                        "Hematology consult",
                        "JAK2 mutation testing",
                        "EPO level",
                        "Consider phlebotomy if symptomatic or PCV >54%",
                        "Rule out secondary causes"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    causes = [
                        "Chronic hypoxia (lung disease, high altitude)",
                        "Smoking",
                        "Dehydration",
                        "Obstructive sleep apnea"
                    ]
                    actions = [
                        "Assess hydration status",
                        "Pulse oximetry, ABG if indicated",
                        "Evaluate for lung disease, OSA",
                        "Repeat when euvolemic"
                    ]

                interpretations.append(Interpretation(
                    finding=f"Polycythemia (Hemoglobin {hgb} g/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance="Increased blood viscosity, thrombosis risk",
                    recommended_actions=actions,
                    follow_up_tests=["Hematocrit", "JAK2 V617F mutation", "EPO level", "ABG"]
                ))

        # PLATELET COUNT
        if 'platelet' in labs:
            plt = labs['platelet']
            if plt < 150:
                if plt < 10:
                    severity = Abnormality.CRITICAL
                    significance = "Severe thrombocytopenia - high spontaneous bleeding risk"
                    causes = [
                        "ITP (immune thrombocytopenic purpura)",
                        "TTP/HUS",
                        "DIC",
                        "Bone marrow failure",
                        "Drug-induced (heparin, chemotherapy)"
                    ]
                    actions = [
                        "Platelet transfusion if active bleeding",
                        "Hematology consult",
                        "Peripheral smear (schistocytes?)",
                        "DIC panel (PT, PTT, fibrinogen, D-dimer)",
                        "Hold anticoagulation/antiplatelets",
                        "Avoid IM injections, avoid NSAIDs"
                    ]
                elif plt < 50:
                    severity = Abnormality.SEVERE
                    significance = "Moderate thrombocytopenia - bleeding risk with trauma/procedures"
                    causes = [
                        "ITP",
                        "Medications (heparin, valproate, antibiotics)",
                        "Viral infection",
                        "Cirrhosis with portal hypertension",
                        "Myelodysplastic syndrome"
                    ]
                    actions = [
                        "Hold anticoagulation if possible",
                        "Review medications",
                        "Peripheral smear",
                        "Consider hematology consult",
                        "Transfuse if surgery/procedure planned"
                    ]
                else:
                    severity = Abnormality.MILD
                    significance = "Mild thrombocytopenia - low bleeding risk"
                    causes = [
                        "ITP",
                        "Medications",
                        "Gestational (pregnancy)",
                        "Splenic sequestration",
                        "Pseudothrombocytopenia (EDTA-dependent)"
                    ]
                    actions = [
                        "Repeat CBC in citrate tube to rule out pseudothrombocytopenia",
                        "Review peripheral smear",
                        "Monitor",
                        "Investigate if persistent or worsening"
                    ]

                interpretations.append(Interpretation(
                    finding=f"Thrombocytopenia (Platelet {plt} K/uL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["Peripheral smear", "Repeat CBC (citrate tube)", "DIC panel if severe"]
                ))

            elif plt > 450:
                if plt > 1000:
                    severity = Abnormality.CRITICAL
                    causes = [
                        "Essential thrombocythemia",
                        "Polycythemia vera",
                        "CML",
                        "Myelofibrosis"
                    ]
                    actions = [
                        "Hematology consult",
                        "JAK2, CALR, MPL mutation testing",
                        "Bone marrow biopsy",
                        "Consider cytoreduction (hydroxyurea) or plateletpheresis if >1500",
                        "Aspirin for thrombosis prophylaxis (if no bleeding)"
                    ]
                    significance = "Extreme thrombocytosis - paradoxical bleeding and thrombosis risk"
                else:
                    severity = Abnormality.MODERATE
                    causes = [
                        "Reactive thrombocytosis (infection, inflammation, iron deficiency)",
                        "Post-splenectomy",
                        "Malignancy",
                        "Acute bleeding/hemolysis",
                        "Essential thrombocythemia"
                    ]
                    actions = [
                        "Identify underlying cause",
                        "Iron studies",
                        "Inflammatory markers (CRP, ESR)",
                        "Monitor",
                        "Hematology if persistent without clear cause"
                    ]
                    significance = "Reactive thrombocytosis usually - low thrombosis risk"

                interpretations.append(Interpretation(
                    finding=f"Thrombocytosis (Platelet {plt} K/uL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["Iron studies", "CRP/ESR", "JAK2 mutation if >600 without clear cause"]
                ))

        return interpretations

    def interpret_cmp(self, labs: Dict[str, float]) -> List[Interpretation]:
        """
        Interpret Comprehensive Metabolic Panel (CMP)

        Includes: Na, K, Cl, HCO3, BUN, Cr, Glucose, Ca
        """
        interpretations = []

        # SODIUM
        if 'sodium' in labs:
            na = labs['sodium']
            if na < 136:
                if na < 120:
                    severity = Abnormality.CRITICAL
                    significance = "Severe hyponatremia - seizure risk"
                    actions = [
                        "Assess volume status, symptoms",
                        "Calculate serum osmolality",
                        "Measure urine sodium and osmolality",
                        "If symptomatic: 3% saline with caution (max 6-8 mEq/L in 24h to avoid osmotic demyelination)",
                        "ICU monitoring"
                    ]
                elif na < 130:
                    severity = Abnormality.SEVERE
                    significance = "Moderate hyponatremia - needs prompt evaluation"
                    actions = [
                        "Assess volume status",
                        "Urine sodium and osmolality",
                        "TSH, cortisol if euvolemic",
                        "Fluid restrict if SIADH"
                    ]
                else:
                    severity = Abnormality.MILD
                    significance = "Mild hyponatremia - usually asymptomatic"
                    actions = [
                        "Assess volume status",
                        "Repeat",
                        "Investigate if persistent"
                    ]

                causes = [
                    "Hypovolemic: diuretics, GI losses, cerebral salt wasting",
                    "Euvolemic: SIADH, hypothyroidism, adrenal insufficiency, psychogenic polydipsia",
                    "Hypervolemic: CHF, cirrhosis, nephrotic syndrome"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hyponatremia (Na {na} mEq/L)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["Serum osmolality", "Urine sodium", "Urine osmolality", "TSH, cortisol"]
                ))

            elif na > 145:
                if na > 160:
                    severity = Abnormality.CRITICAL
                    significance = "Severe hypernatremia - altered mental status, seizures"
                    actions = [
                        "Calculate free water deficit",
                        "Assess volume status",
                        "Replace free water carefully (max decrease 10-12 mEq/L per 24h)",
                        "D5W or hypotonic saline",
                        "ICU monitoring"
                    ]
                elif na > 150:
                    severity = Abnormality.SEVERE
                    significance = "Moderate hypernatremia"
                    actions = [
                        "Assess volume status and fluid intake",
                        "Calculate free water deficit",
                        "Increase free water intake or D5W",
                        "Evaluate for diabetes insipidus if euvolemic"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild hypernatremia"
                    actions = [
                        "Increase fluid intake",
                        "Assess for dehydration",
                        "Monitor"
                    ]

                causes = [
                    "Hypovolemic: inadequate water intake, excessive water loss (diarrhea, burns)",
                    "Euvolemic: diabetes insipidus (central or nephrogenic)",
                    "Hypervolemic: hypertonic saline, sodium bicarbonate, mineralocorticoid excess"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hypernatremia (Na {na} mEq/L)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["Urine sodium", "Urine osmolality", "Serum osmolality", "Trial of DDAVP if DI suspected"]
                ))

        # POTASSIUM
        if 'potassium' in labs:
            k = labs['potassium']
            if k > 5.0:
                if k > 6.5:
                    severity = Abnormality.CRITICAL
                    significance = "Life-threatening hyperkalemia - arrhythmia risk"
                    actions = [
                        "STAT ECG (peaked T waves, wide QRS)",
                        "Calcium gluconate 10% 10mL IV (if ECG changes) - membrane stabilization",
                        "Insulin 10 units + D50 50mL IV - shift K intracellularly",
                        "Albuterol nebulizer - shift K intracellularly",
                        "Kayexalate or Patiromer - remove K",
                        "Dialysis if severe or refractory",
                        "Continuous telemetry"
                    ]
                elif k > 5.5:
                    severity = Abnormality.SEVERE
                    significance = "Severe hyperkalemia"
                    actions = [
                        "ECG",
                        "Stop K-sparing diuretics, ACE-I/ARBs, NSAIDs",
                        "Kayexalate or Patiromer",
                        "Consider insulin + dextrose if progressive",
                        "Monitor closely"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild hyperkalemia"
                    actions = [
                        "Repeat to confirm (hemolysis can cause pseudohyperkalemia)",
                        "Review medications",
                        "Check kidney function",
                        "Dietary potassium restriction"
                    ]

                causes = [
                    "Acute kidney injury or CKD",
                    "Medications: K-sparing diuretics, ACE-I, ARBs, NSAIDs, heparin",
                    "Hypoaldosteronism (Addison's disease, Type 4 RTA)",
                    "Rhabdomyolysis, tumor lysis syndrome",
                    "Pseudohyperkalemia (hemolysis, thrombocytosis, leukocytosis)"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hyperkalemia (K {k} mEq/L)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["ECG", "BMP", "Repeat K (avoid hemolysis)"]
                ))

            elif k < 3.5:
                if k < 2.5:
                    severity = Abnormality.CRITICAL
                    significance = "Severe hypokalemia - arrhythmia, weakness, rhabdomyolysis risk"
                    actions = [
                        "ECG (U waves, flattened T, prolonged QT)",
                        "IV potassium replacement (max 10-20 mEq/hr via central line; 10 mEq/hr peripheral)",
                        "Continuous telemetry",
                        "Check magnesium (hypomagnesemia prevents K repletion)",
                        "Replete magnesium if low"
                    ]
                elif k < 3.0:
                    severity = Abnormality.SEVERE
                    significance = "Moderate hypokalemia"
                    actions = [
                        "IV or PO potassium replacement",
                        "Check magnesium",
                        "Monitor",
                        "Identify cause"
                    ]
                else:
                    severity = Abnormality.MILD
                    significance = "Mild hypokalemia"
                    actions = [
                        "Oral potassium supplementation",
                        "Increase dietary potassium",
                        "Identify cause (diuretics common)"
                    ]

                causes = [
                    "Diuretics (thiazides, loop diuretics)",
                    "GI losses (diarrhea, vomiting, laxatives)",
                    "Renal losses (RTA, hyperaldosteronism)",
                    "Inadequate intake",
                    "Insulin, beta-agonists (shift intracellularly)"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hypokalemia (K {k} mEq/L)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["ECG", "Magnesium", "Urine potassium (spot or 24h)"]
                ))

        # CREATININE & BUN (Kidney Function)
        if 'creatinine' in labs:
            cr = labs['creatinine']
            if cr > 1.3:
                # Estimate GFR (simplified - should use CKD-EPI equation with age, gender, race)
                if cr > 4.0:
                    severity = Abnormality.CRITICAL
                    significance = "Severe renal failure - dialysis may be indicated"
                    actions = [
                        "Nephrology consult",
                        "Assess for uremia (nausea, confusion, pericarditis, bleeding)",
                        "Indications for emergent dialysis: AEIOU (Acidosis, Electrolytes-hyperkalemia, Ingestion, Overload-pulmonary edema, Uremia)",
                        "Avoid nephrotoxins",
                        "Adjust medication doses"
                    ]
                elif cr > 2.0:
                    severity = Abnormality.SEVERE
                    significance = "Moderate-severe renal impairment"
                    actions = [
                        "Determine if acute (AKI) or chronic (CKD)",
                        "Review prior creatinine",
                        "Urinalysis (hematuria, proteinuria, casts)",
                        "Renal ultrasound (obstruction, size)",
                        "Adjust medication doses",
                        "Consider nephrology referral"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild renal impairment"
                    actions = [
                        "Check if acute or chronic",
                        "Urinalysis",
                        "Avoid nephrotoxins (NSAIDs, contrast)",
                        "Monitor"
                    ]

                causes = [
                    "Acute Kidney Injury: prerenal (dehydration, hypotension), intrinsic (ATN, AIN, glomerulonephritis), postrenal (obstruction)",
                    "Chronic Kidney Disease: diabetes, hypertension, glomerulonephritis, PKD",
                    "Medications: NSAIDs, ACE-I/ARBs, aminoglycosides, contrast"
                ]

                follow_up = ["Urinalysis with microscopy", "Renal ultrasound", "BUN:Cr ratio", "Urine electrolytes (FeNa, FeUrea)"]
                if 'bun' in labs:
                    bun_cr_ratio = labs['bun'] / cr
                    if bun_cr_ratio > 20:
                        follow_up.append("Elevated BUN:Cr ratio suggests prerenal azotemia (dehydration)")
                    elif bun_cr_ratio < 10:
                        follow_up.append("Low BUN:Cr ratio suggests intrinsic renal disease or liver disease")

                interpretations.append(Interpretation(
                    finding=f"Elevated Creatinine (Cr {cr} mg/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=follow_up
                ))

        # GLUCOSE
        if 'glucose' in labs:
            gluc = labs['glucose']
            if gluc > 100:
                if gluc > 400:
                    severity = Abnormality.CRITICAL
                    significance = "Severe hyperglycemia - DKA or HHS risk"
                    actions = [
                        "Check for DKA: VBG (pH, HCO3), beta-hydroxybutyrate or urine ketones",
                        "Check for HHS: serum osmolality",
                        "IV insulin infusion if DKA/HHS",
                        "Aggressive IV fluids",
                        "Monitor electrolytes (especially K)"
                    ]
                elif gluc > 200:
                    severity = Abnormality.SEVERE
                    significance = "Marked hyperglycemia"
                    actions = [
                        "If random: confirm with fasting glucose or HbA1c",
                        "Screen for diabetes if not known",
                        "Initiate or intensify diabetes management",
                        "Rule out infection or other stressors"
                    ]
                elif gluc > 125:
                    severity = Abnormality.MODERATE
                    significance = "Fasting glucose >126 on two occasions = diabetes"
                    actions = [
                        "Repeat fasting glucose or HbA1c",
                        "Screen for diabetes complications",
                        "Lifestyle modification",
                        "Consider metformin"
                    ]
                else:
                    severity = Abnormality.MILD
                    significance = "Impaired fasting glucose (pre-diabetes)"
                    actions = [
                        "Lifestyle modification (diet, exercise, weight loss)",
                        "Repeat annually",
                        "Consider metformin if high risk"
                    ]

                causes = [
                    "Type 2 diabetes mellitus",
                    "Type 1 diabetes mellitus",
                    "Steroid-induced hyperglycemia",
                    "Pancreatitis",
                    "Stress hyperglycemia (MI, stroke, sepsis)"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hyperglycemia (Glucose {gluc} mg/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["HbA1c", "Fasting glucose (confirm)", "Urine ketones or beta-hydroxybutyrate if >400"]
                ))

            elif gluc < 70:
                if gluc < 40:
                    severity = Abnormality.CRITICAL
                    significance = "Severe hypoglycemia - neuroglycopenic symptoms, seizures"
                    actions = [
                        "Immediate treatment: D50 (25-50mL IV) or glucagon 1mg IM/SC",
                        "Continuous glucose monitoring",
                        "Identify cause",
                        "Admit if unexplained, elderly, or recurrent"
                    ]
                elif gluc < 54:
                    severity = Abnormality.SEVERE
                    significance = "Clinically significant hypoglycemia"
                    actions = [
                        "Oral glucose 15-20g if conscious",
                        "Recheck in 15 min",
                        "Identify cause (insulin, sulfonylurea, missed meal)"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild hypoglycemia"
                    actions = [
                        "Oral glucose",
                        "Review diabetes medications",
                        "Ensure adequate carbohydrate intake"
                    ]

                causes = [
                    "Diabetes medications (insulin, sulfonylureas)",
                    "Inadequate food intake",
                    "Insulinoma (if fasting and not on diabetes meds)",
                    "Adrenal insufficiency",
                    "Alcohol"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hypoglycemia (Glucose {gluc} mg/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["If recurrent/unexplained: C-peptide, insulin, cortisol during hypoglycemia"]
                ))

        # CALCIUM
        if 'calcium' in labs:
            ca = labs['calcium']
            # Note: Should correct for albumin: Corrected Ca = measured Ca + 0.8 * (4.0 - albumin)
            if ca > 10.5:
                if ca > 14:
                    severity = Abnormality.CRITICAL
                    significance = "Hypercalcemic crisis - altered mental status, cardiac arrhythmias"
                    actions = [
                        "Aggressive IV normal saline (4-6L first 24h)",
                        "IV bisphosphonate (zoledronic acid 4mg)",
                        "Calcitonin for rapid effect",
                        "Dialysis if refractory",
                        "Identify cause urgently"
                    ]
                elif ca > 12:
                    severity = Abnormality.SEVERE
                    significance = "Severe hypercalcemia"
                    actions = [
                        "IV normal saline",
                        "IV bisphosphonate",
                        "PTH, PTHrP, vitamin D levels",
                        "Workup for malignancy"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild hypercalcemia"
                    actions = [
                        "Check ionized calcium or correct for albumin",
                        "PTH level (primary hyperparathyroidism vs malignancy)",
                        "Vitamin D level",
                        "Hydration"
                    ]

                causes = [
                    "Primary hyperparathyroidism (elevated PTH)",
                    "Malignancy (lung, breast, myeloma, lymphoma) - PTHrP or osteolytic",
                    "Vitamin D toxicity",
                    "Thiazide diuretics",
                    "Granulomatous disease (sarcoidosis, TB)"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hypercalcemia (Ca {ca} mg/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["PTH", "Vitamin D (25-OH and 1,25-OH)", "PTHrP", "SPEP/UPEP", "Ionized calcium"]
                ))

            elif ca < 8.5:
                if ca < 7.0:
                    severity = Abnormality.CRITICAL
                    significance = "Severe hypocalcemia - tetany, seizures, QT prolongation"
                    actions = [
                        "IV calcium gluconate 10% 10-20mL over 10 min",
                        "Continuous calcium infusion",
                        "Check magnesium (hypomagnesemia prevents Ca repletion)",
                        "ECG monitoring (prolonged QT)",
                        "Check PTH, vitamin D, albumin"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild-moderate hypocalcemia"
                    actions = [
                        "Correct for albumin",
                        "Check ionized calcium",
                        "Oral calcium and vitamin D supplementation",
                        "Check PTH, vitamin D, magnesium, phosphate"
                    ]

                causes = [
                    "Hypoparathyroidism (post-thyroidectomy, autoimmune)",
                    "Vitamin D deficiency",
                    "Chronic kidney disease",
                    "Hypomagnesemia",
                    "Acute pancreatitis",
                    "Medications (bisphosphonates, denosumab, cinacalcet)"
                ]

                interpretations.append(Interpretation(
                    finding=f"Hypocalcemia (Ca {ca} mg/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["Ionized calcium", "Albumin", "PTH", "Vitamin D", "Magnesium", "Phosphate"]
                ))

        return interpretations

    def interpret_lft(self, labs: Dict[str, float]) -> List[Interpretation]:
        """
        Interpret Liver Function Tests

        Pattern recognition: Hepatocellular vs Cholestatic vs Mixed
        """
        interpretations = []

        # Determine pattern if we have AST, ALT, ALP
        pattern = "unknown"
        if all(k in labs for k in ['ast', 'alt', 'alkaline_phosphatase']):
            ast = labs['ast']
            alt = labs['alt']
            alp = labs['alkaline_phosphatase']

            # R value (ratio) for pattern determination
            # R = (ALT / ULN_ALT) / (ALP / ULN_ALP)
            # R > 5: Hepatocellular
            # R < 2: Cholestatic
            # 2-5: Mixed
            alt_ratio = alt / 40  # Assuming ULN = 40
            alp_ratio = alp / 130  # Assuming ULN = 130
            r_value = alt_ratio / alp_ratio if alp_ratio > 0 else float('inf')

            if r_value > 5:
                pattern = "hepatocellular"
            elif r_value < 2:
                pattern = "cholestatic"
            else:
                pattern = "mixed"

        # AST/ALT elevation
        if 'ast' in labs and 'alt' in labs:
            ast = labs['ast']
            alt = labs['alt']
            ast_alt_ratio = ast / alt if alt > 0 else 0

            if alt > 56 or ast > 40:
                if alt > 1000 or ast > 1000:
                    severity = Abnormality.CRITICAL
                    significance = "Massive transaminase elevation - acute liver injury"
                    causes = [
                        "Acute viral hepatitis (Hep A, B, C, E, EBV, CMV)",
                        "Acetaminophen toxicity (check level)",
                        "Drug-induced liver injury (antibiotics, statins, herbal supplements)",
                        "Ischemic hepatitis (shock liver)",
                        "Acute Budd-Chiari syndrome",
                        "Autoimmune hepatitis"
                    ]
                    actions = [
                        "Hepatology consult",
                        "Acetaminophen level (if any ingestion possible)",
                        "Viral hepatitis serologies (Hep A IgM, HBsAg, HBcAb IgM, Hep C Ab/RNA, HIV)",
                        "Autoimmune workup (ANA, ASMA, immunoglobulins)",
                        "Right upper quadrant ultrasound with Doppler",
                        "INR (assess synthetic function)",
                        "Consider N-acetylcysteine if acetaminophen toxicity"
                    ]
                elif alt > 200 or ast > 200:
                    severity = Abnormality.SEVERE
                    significance = "Severe transaminase elevation"
                    causes = [
                        "Acute hepatitis (viral, drug-induced, autoimmune)",
                        "Alcoholic hepatitis (AST:ALT >2)",
                        "Acute biliary obstruction"
                    ]
                    actions = [
                        "Viral hepatitis panel",
                        "Alcohol history",
                        "Medication review",
                        "RUQ ultrasound",
                        "Consider liver biopsy if diagnosis unclear"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild-moderate transaminase elevation"
                    causes = [
                        "NAFLD/NASH (most common)",
                        "Alcoholic liver disease",
                        "Chronic hepatitis B or C",
                        "Hemochromatosis",
                        "Wilson disease (age <40)",
                        "Alpha-1 antitrypsin deficiency",
                        "Medications (statins common but rarely significant)"
                    ]
                    actions = [
                        "Assess for metabolic syndrome (obesity, diabetes, dyslipidemia)",
                        "Alcohol use history",
                        "Hepatitis B and C screening",
                        "Iron studies (ferritin, transferrin saturation)",
                        "Ceruloplasmin if age <40",
                        "RUQ ultrasound"
                    ]

                # Add note about AST:ALT ratio
                ratio_note = []
                if ast_alt_ratio > 2:
                    ratio_note.append("AST:ALT >2 suggests alcoholic liver disease")
                if ast_alt_ratio < 1:
                    ratio_note.append("AST:ALT <1 typical of viral hepatitis or NAFLD")

                interpretations.append(Interpretation(
                    finding=f"{pattern.capitalize()} pattern - Elevated Transaminases (AST {ast}, ALT {alt})",
                    severity=severity,
                    possible_causes=causes + ratio_note,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["Hepatitis panel", "RUQ ultrasound", "Iron studies", "Ceruloplasmin if <40yo"]
                ))

        # Alkaline Phosphatase elevation
        if 'alkaline_phosphatase' in labs:
            alp = labs['alkaline_phosphatase']
            if alp > 130:
                if alp > 500:
                    severity = Abnormality.SEVERE
                    significance = "Marked ALP elevation - cholestatic process"
                    causes = [
                        "Biliary obstruction (choledocholithiasis, malignancy)",
                        "Primary biliary cholangitis (PBC)",
                        "Primary sclerosing cholangitis (PSC)",
                        "Infiltrative liver disease (sarcoidosis, amyloidosis, lymphoma)"
                    ]
                    actions = [
                        "RUQ ultrasound (dilated ducts?)",
                        "MRCP or ERCP if obstruction suspected",
                        "GGT or 5'-nucleotidase to confirm hepatic source",
                        "AMA (anti-mitochondrial antibody) for PBC",
                        "ANCA for PSC"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Elevated ALP - determine source (liver vs bone)"
                    causes = [
                        "Hepatic: cholestasis, infiltrative disease, medications",
                        "Bone: Paget disease, osteomalacia, healing fracture, malignancy"
                    ]
                    actions = [
                        "GGT or 5'-nucleotidase (elevated if hepatic source)",
                        "Bone-specific ALP or imaging if bone source suspected",
                        "RUQ ultrasound",
                        "Medication review"
                    ]

                interpretations.append(Interpretation(
                    finding=f"Elevated Alkaline Phosphatase (ALP {alp} U/L)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["GGT or 5'-nucleotidase", "RUQ ultrasound", "MRCP if obstruction"]
                ))

        # Bilirubin elevation
        if 'total_bilirubin' in labs:
            tbili = labs['total_bilirubin']
            if tbili > 1.2:
                if tbili > 10:
                    severity = Abnormality.SEVERE
                    significance = "Severe hyperbilirubinemia - jaundice"
                elif tbili > 3:
                    severity = Abnormality.MODERATE
                    significance = "Moderate hyperbilirubinemia"
                else:
                    severity = Abnormality.MILD
                    significance = "Mild hyperbilirubinemia"

                # Determine conjugated vs unconjugated if direct bilirubin available
                if 'direct_bilirubin' in labs:
                    dbili = labs['direct_bilirubin']
                    indirect_bili = tbili - dbili
                    direct_fraction = dbili / tbili if tbili > 0 else 0

                    if direct_fraction > 0.5:  # Conjugated (direct) hyperbilirubinemia
                        causes = [
                            "Hepatocellular: hepatitis, cirrhosis",
                            "Cholestatic: biliary obstruction, PBC, PSC, drugs",
                            "Dubin-Johnson or Rotor syndrome (rare)"
                        ]
                        follow_up = ["RUQ ultrasound", "Hepatitis panel", "Consider MRCP"]
                    else:  # Unconjugated (indirect) hyperbilirubinemia
                        causes = [
                            "Hemolysis (check haptoglobin, LDH, reticulocytes)",
                            "Gilbert syndrome (benign, fasting/stress)",
                            "Crigler-Najjar syndrome (rare, severe)"
                        ]
                        follow_up = ["Haptoglobin", "LDH", "Reticulocyte count", "Peripheral smear"]
                else:
                    causes = ["Need direct bilirubin to classify"]
                    follow_up = ["Direct and indirect bilirubin"]

                interpretations.append(Interpretation(
                    finding=f"Hyperbilirubinemia (Total Bili {tbili} mg/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=["Determine if conjugated or unconjugated", "Assess for jaundice"],
                    follow_up_tests=follow_up
                ))

        # Albumin (synthetic function)
        if 'albumin' in labs:
            alb = labs['albumin']
            if alb < 3.5:
                if alb < 2.5:
                    severity = Abnormality.SEVERE
                    significance = "Severe hypoalbuminemia - edema, ascites"
                    causes = [
                        "Chronic liver disease/cirrhosis (decreased synthesis)",
                        "Nephrotic syndrome (urinary loss)",
                        "Malnutrition",
                        "Protein-losing enteropathy",
                        "Critical illness"
                    ]
                    actions = [
                        "Assess for liver disease (PT/INR, platelets)",
                        "Urinalysis (proteinuria)",
                        "Nutritional assessment",
                        "Consider albumin infusion if symptomatic edema/ascites"
                    ]
                else:
                    severity = Abnormality.MODERATE
                    significance = "Mild-moderate hypoalbuminemia"
                    causes = [
                        "Chronic inflammation",
                        "Liver disease",
                        "Renal losses",
                        "Malnutrition"
                    ]
                    actions = [
                        "Evaluate liver and kidney function",
                        "Nutritional assessment",
                        "Inflammatory markers"
                    ]

                interpretations.append(Interpretation(
                    finding=f"Hypoalbuminemia (Albumin {alb} g/dL)",
                    severity=severity,
                    possible_causes=causes,
                    clinical_significance=significance,
                    recommended_actions=actions,
                    follow_up_tests=["PT/INR", "Urinalysis with protein quantification", "Prealbumin"]
                ))

        return interpretations

    def interpret_thyroid(self, labs: Dict[str, float]) -> List[Interpretation]:
        """Interpret thyroid function tests"""
        interpretations = []

        if 'tsh' in labs:
            tsh = labs['tsh']
            free_t4 = labs.get('free_t4')

            # Primary hypothyroidism
            if tsh > 4.0:
                if tsh > 10:
                    severity = Abnormality.SEVERE
                    if free_t4 and free_t4 < 0.8:
                        interpretations.append(Interpretation(
                            finding=f"Primary Hypothyroidism (TSH {tsh}, Free T4 {free_t4})",
                            severity=severity,
                            possible_causes=[
                                "Hashimoto's thyroiditis (most common)",
                                "Post-ablation (RAI, surgery)",
                                "Medications (amiodarone, lithium)",
                                "Iodine deficiency"
                            ],
                            clinical_significance="Hypothyroidism - fatigue, weight gain, cold intolerance",
                            recommended_actions=[
                                "Start levothyroxine (1.6 mcg/kg/day, lower if elderly/cardiac)",
                                "Recheck TSH in 6-8 weeks",
                                "TPO antibodies (Hashimoto's)"
                            ],
                            follow_up_tests=["TPO antibodies", "Thyroglobulin antibodies"]
                        ))
                    else:
                        interpretations.append(Interpretation(
                            finding=f"Elevated TSH ({tsh})",
                            severity=Abnormality.MODERATE,
                            possible_causes=["Subclinical hypothyroidism", "Need Free T4 to assess"],
                            clinical_significance="May progress to overt hypothyroidism",
                            recommended_actions=["Check Free T4", "Consider treatment if TSH >10 or symptomatic"],
                            follow_up_tests=["Free T4", "TPO antibodies"]
                        ))

            # Hyperthyroidism
            elif tsh < 0.4:
                if free_t4 and free_t4 > 1.8:
                    severity = Abnormality.SEVERE
                    interpretations.append(Interpretation(
                        finding=f"Primary Hyperthyroidism (TSH {tsh}, Free T4 {free_t4})",
                        severity=severity,
                        possible_causes=[
                            "Graves disease",
                            "Toxic multinodular goiter",
                            "Toxic adenoma",
                            "Thyroiditis (subacute, postpartum)",
                            "Exogenous thyroid hormone"
                        ],
                        clinical_significance="Hyperthyroidism - tachycardia, weight loss, tremor, anxiety",
                        recommended_actions=[
                            "Endocrinology referral",
                            "Beta-blocker for symptom control",
                            "Thyroid uptake scan (to differentiate Graves from thyroiditis)",
                            "TSI or TRAB (Graves disease)",
                            "Initiate methimazole or PTU if Graves/nodular disease"
                        ],
                        follow_up_tests=["Free T3", "TSI (thyroid stimulating immunoglobulin)", "Radioiodine uptake scan"]
                    ))

        return interpretations

    def interpret_abg(self, labs: Dict[str, float]) -> List[Interpretation]:
        """
        Interpret Arterial Blood Gas

        Expected keys: ph, pco2, po2, hco3, sao2
        """
        interpretations = []

        if all(k in labs for k in ['ph', 'pco2', 'hco3']):
            ph = labs['ph']
            pco2 = labs['pco2']
            hco3 = labs['hco3']

            # Determine acid-base status
            if ph < 7.35:
                # Acidemia
                if pco2 > 45:
                    # Respiratory acidosis
                    if hco3 > 26:
                        compensation = "Partially compensated (chronic)"
                    else:
                        compensation = "Uncompensated (acute)"

                    interpretations.append(Interpretation(
                        finding=f"Respiratory Acidosis ({compensation}) - pH {ph}, pCO2 {pco2}, HCO3 {hco3}",
                        severity=Abnormality.SEVERE if ph < 7.2 else Abnormality.MODERATE,
                        possible_causes=[
                            "Hypoventilation: COPD, asthma, neuromuscular disease",
                            "CNS depression (opioids, sedatives)",
                            "Obesity hypoventilation"
                        ],
                        clinical_significance="CO2 retention - can cause altered mental status",
                        recommended_actions=[
                            "Treat underlying cause",
                            "NIV (BiPAP) if COPD/OHS and not improving",
                            "Intubation if severe/refractory",
                            "Avoid high-flow O2 in chronic CO2 retainers"
                        ]
                    ))

                elif hco3 < 22:
                    # Metabolic acidosis
                    # Calculate anion gap if Na, Cl available
                    anion_gap_text = ""
                    if 'sodium' in labs and 'chloride' in labs:
                        ag = labs['sodium'] - labs['chloride'] - hco3
                        if ag > 12:
                            anion_gap_text = f"High Anion Gap ({ag}) - "
                            causes = [
                                "MUDPILES: Methanol, Uremia, DKA, Propylene glycol, Iron/Isoniazid, Lactic acidosis, Ethylene glycol, Salicylates"
                            ]
                            follow_up = ["Lactate", "Beta-hydroxybutyrate", "Toxicology screen", "Osmolar gap"]
                        else:
                            anion_gap_text = f"Normal Anion Gap ({ag}) - "
                            causes = [
                                "HARDUPS: Hyperalimentation, Acetazolamide, RTA, Diarrhea, Ureteral diversions, Pancreatic fistula, Saline"
                            ]
                            follow_up = ["Urine anion gap", "Urine pH"]
                    else:
                        causes = ["Need electrolytes to calculate anion gap"]
                        follow_up = ["BMP"]

                    interpretations.append(Interpretation(
                        finding=f"{anion_gap_text}Metabolic Acidosis - pH {ph}, HCO3 {hco3}",
                        severity=Abnormality.SEVERE if ph < 7.2 else Abnormality.MODERATE,
                        possible_causes=causes,
                        clinical_significance="Metabolic acidosis - can impair cardiac contractility",
                        recommended_actions=[
                            "Treat underlying cause",
                            "Bicarbonate therapy controversial (consider if pH <7.1 and non-gap)",
                            "Dialysis if severe uremic or toxic ingestion"
                        ],
                        follow_up_tests=follow_up
                    ))

            elif ph > 7.45:
                # Alkalemia
                if pco2 < 35:
                    # Respiratory alkalosis
                    interpretations.append(Interpretation(
                        finding=f"Respiratory Alkalosis - pH {ph}, pCO2 {pco2}",
                        severity=Abnormality.MODERATE,
                        possible_causes=[
                            "Hyperventilation (anxiety, pain, hypoxia)",
                            "Pulmonary embolism",
                            "Pregnancy",
                            "Sepsis",
                            "Liver disease",
                            "Salicylate toxicity (early)"
                        ],
                        clinical_significance="Usually compensatory or benign",
                        recommended_actions=[
                            "Treat underlying cause",
                            "Reassurance if anxiety/panic"
                        ]
                    ))

                elif hco3 > 28:
                    # Metabolic alkalosis
                    interpretations.append(Interpretation(
                        finding=f"Metabolic Alkalosis - pH {ph}, HCO3 {hco3}",
                        severity=Abnormality.MODERATE,
                        possible_causes=[
                            "Saline-responsive: vomiting, NG suction, diuretics",
                            "Saline-resistant: hyperaldosteronism, Cushing syndrome"
                        ],
                        clinical_significance="Usually from volume depletion or diuretics",
                        recommended_actions=[
                            "IV normal saline if volume depleted",
                            "Potassium repletion",
                            "Discontinue diuretics if possible",
                            "Urine chloride to differentiate saline-responsive vs resistant"
                        ],
                        follow_up_tests=["Urine chloride"]
                    ))

        # Hypoxemia
        if 'po2' in labs:
            po2 = labs['po2']
            if po2 < 60:
                if po2 < 40:
                    severity = Abnormality.CRITICAL
                else:
                    severity = Abnormality.SEVERE

                interpretations.append(Interpretation(
                    finding=f"Hypoxemia (pO2 {po2} mmHg)",
                    severity=severity,
                    possible_causes=[
                        "V/Q mismatch (pneumonia, COPD, PE)",
                        "Shunt (ARDS, pulmonary edema)",
                        "Hypoventilation",
                        "Low FiO2 (high altitude)"
                    ],
                    clinical_significance="Tissue hypoxia",
                    recommended_actions=[
                        "Supplemental oxygen",
                        "Treat underlying cause",
                        "Calculate A-a gradient"
                    ],
                    follow_up_tests=["CXR", "Calculate A-a gradient"]
                ))

        return interpretations


def interpret_labs(panel_type: str, lab_values: Dict[str, float], **kwargs) -> List[Dict]:
    """
    Convenience function to interpret laboratory panels.

    Args:
        panel_type: Type of panel ('cbc', 'cmp', 'lft', 'thyroid', 'abg', etc.)
        lab_values: Dictionary of test names and values
        **kwargs: Additional parameters (gender, age)

    Returns:
        List of interpretation dictionaries

    Example:
        >>> results = interpret_labs('cbc', {
        ...     'wbc': 15.2,
        ...     'hemoglobin': 9.5,
        ...     'platelet': 450
        ... }, gender='F', age=35)
    """
    interpreter = LabInterpreter()

    panel_methods = {
        'cbc': interpreter.interpret_cbc,
        'cmp': interpreter.interpret_cmp,
        'bmp': interpreter.interpret_cmp,  # CMP includes BMP
        'lft': interpreter.interpret_lft,
        'thyroid': interpreter.interpret_thyroid,
        'abg': interpreter.interpret_abg,
    }

    method = panel_methods.get(panel_type.lower())
    if not method:
        return [{'error': f'Unknown panel type: {panel_type}'}]

    interpretations = method(lab_values, **kwargs)

    return [
        {
            'finding': interp.finding,
            'severity': interp.severity.value,
            'possible_causes': interp.possible_causes,
            'clinical_significance': interp.clinical_significance,
            'recommended_actions': interp.recommended_actions,
            'follow_up_tests': interp.follow_up_tests
        }
        for interp in interpretations
    ]
