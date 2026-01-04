"""
Treatment Protocol Engine for Clinical Decision Support

Evidence-based treatment algorithms for common medical conditions.

MEDICAL DISCLAIMER:
These protocols are guidelines based on current evidence. Always individualize
treatment based on patient-specific factors, local guidelines, and clinical judgment.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class TreatmentLine(Enum):
    """Treatment priority"""
    FIRST_LINE = "first_line"
    SECOND_LINE = "second_line"
    THIRD_LINE = "third_line"
    ADJUNCT = "adjunct"


@dataclass
class TreatmentStep:
    """Individual treatment step in protocol"""
    step_number: int
    description: str
    medications: List[Dict[str, str]] = field(default_factory=list)
    non_pharm: List[str] = field(default_factory=list)
    monitoring: List[str] = field(default_factory=list)
    duration: Optional[str] = None
    success_criteria: Optional[str] = None
    escalation_criteria: Optional[str] = None


@dataclass
class TreatmentProtocol:
    """Complete treatment protocol for a condition"""
    condition: str
    guideline_source: str
    steps: List[TreatmentStep]
    contraindications: List[str] = field(default_factory=list)
    special_populations: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)


class ProtocolEngine:
    """
    Treatment protocol engine with evidence-based algorithms.
    """

    def __init__(self):
        self._initialize_protocols()

    def _initialize_protocols(self):
        """Initialize protocol database"""
        self.protocols = {
            'hypertension': self._hypertension_protocol,
            'diabetes_type2': self._diabetes_t2_protocol,
            'heart_failure': self._heart_failure_protocol,
            'copd': self._copd_protocol,
            'pneumonia_cap': self._cap_protocol,
            'uti': self._uti_protocol,
            'acs_nstemi': self._acs_protocol,
            'stroke_ischemic': self._stroke_protocol,
            'sepsis': self._sepsis_protocol,
            'dka': self._dka_protocol,
        }

    def _hypertension_protocol(self) -> TreatmentProtocol:
        """Hypertension management protocol (JNC/ACC/AHA)"""
        return TreatmentProtocol(
            condition="Hypertension",
            guideline_source="ACC/AHA 2017 Hypertension Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Lifestyle modifications (all patients)",
                    non_pharm=[
                        "DASH diet (high fruits/vegetables, low sodium)",
                        "Sodium restriction <2g/day (ideally <1.5g)",
                        "Weight loss if overweight (goal BMI <25)",
                        "Exercise: 150 min/week moderate aerobic activity",
                        "Limit alcohol: ≤2 drinks/day men, ≤1 drink/day women",
                        "Smoking cessation"
                    ],
                    monitoring=["BP home monitoring", "Office BP q3-6 months"],
                    success_criteria="BP <130/80 mmHg"
                ),
                TreatmentStep(
                    step_number=2,
                    description="First-line pharmacotherapy (if BP ≥130/80 with ASCVD or 10-year risk ≥10%, or BP ≥140/90)",
                    medications=[
                        {
                            'class': 'ACE Inhibitor',
                            'examples': 'Lisinopril 10-40mg daily, Enalapril 5-40mg daily',
                            'line': 'First-line (especially if DM, CKD, HFrEF)',
                            'monitoring': 'Cr, K in 2 weeks, then q6mo; Cough common'
                        },
                        {
                            'class': 'ARB (if ACE-I not tolerated)',
                            'examples': 'Losartan 50-100mg daily, Valsartan 80-320mg daily',
                            'line': 'First-line alternative to ACE-I',
                            'monitoring': 'Cr, K in 2 weeks, then q6mo'
                        },
                        {
                            'class': 'Thiazide/Thiazide-like Diuretic',
                            'examples': 'Chlorthalidone 12.5-25mg daily, HCTZ 25-50mg daily',
                            'line': 'First-line (especially if Black, elderly)',
                            'monitoring': 'Electrolytes (Na, K), Cr; Watch for hypokalemia'
                        },
                        {
                            'class': 'Dihydropyridine CCB',
                            'examples': 'Amlodipine 5-10mg daily, Nifedipine XL 30-90mg daily',
                            'line': 'First-line (especially if Black, ISH)',
                            'monitoring': 'Peripheral edema common'
                        }
                    ],
                    monitoring=["BP q1-2 weeks until controlled, then monthly", "Electrolytes, Cr within 2-4 weeks"],
                    success_criteria="BP <130/80 mmHg on single agent",
                    escalation_criteria="BP remains ≥130/80 after 1 month at max tolerated dose"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Two-drug combination (if BP >20/10 mmHg above goal or uncontrolled on monotherapy)",
                    medications=[
                        {
                            'combination': 'ACE-I or ARB + CCB',
                            'note': 'Preferred combination'
                        },
                        {
                            'combination': 'ACE-I or ARB + Thiazide',
                            'note': 'Also preferred'
                        },
                        {
                            'combination': 'CCB + Thiazide',
                            'note': 'If ACE-I/ARB contraindicated'
                        }
                    ],
                    non_pharm=["Reinforce lifestyle modifications"],
                    success_criteria="BP <130/80 mmHg",
                    escalation_criteria="BP uncontrolled after 1 month"
                ),
                TreatmentStep(
                    step_number=4,
                    description="Three-drug combination (resistant hypertension)",
                    medications=[
                        {
                            'regimen': 'ACE-I or ARB + CCB + Thiazide diuretic',
                            'note': 'Standard triple therapy'
                        },
                        {
                            'fourth_line': 'Spironolactone 25-50mg daily',
                            'note': 'Most effective 4th agent (if K <5.0)',
                            'monitoring': 'K, Cr closely (hyperkalemia risk)'
                        }
                    ],
                    monitoring=["Consider secondary hypertension workup", "Renal artery stenosis", "Primary aldosteronism"],
                    escalation_criteria="Refer to hypertension specialist if uncontrolled on 3+ drugs"
                )
            ],
            contraindications=[
                "ACE-I/ARB: Pregnancy, bilateral renal artery stenosis, history of angioedema",
                "Thiazides: Gout (relative)",
                "CCB: Severe aortic stenosis (non-DHP CCB)"
            ],
            special_populations={
                'Black': 'Prefer CCB or thiazide as first-line (unless CKD/DM)',
                'CKD': 'ACE-I or ARB first-line',
                'Diabetes': 'ACE-I or ARB first-line',
                'Elderly': 'Target <130/80 if tolerated; thiazide or CCB often preferred',
                'Pregnancy': 'Methyldopa, labetalol, nifedipine (avoid ACE-I/ARB)'
            },
            references=[
                "2017 ACC/AHA Hypertension Guidelines",
                "Whelton et al. J Am Coll Cardiol 2018;71:e127-248"
            ]
        )

    def _diabetes_t2_protocol(self) -> TreatmentProtocol:
        """Type 2 Diabetes management (ADA guidelines)"""
        return TreatmentProtocol(
            condition="Type 2 Diabetes Mellitus",
            guideline_source="ADA Standards of Care 2024",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Lifestyle and Metformin (unless contraindicated)",
                    non_pharm=[
                        "Medical nutrition therapy (carb counting, portion control)",
                        "Weight loss goal: 5-10% if overweight",
                        "Exercise: 150 min/week moderate activity + resistance training 2-3x/week",
                        "Diabetes self-management education (DSME)"
                    ],
                    medications=[
                        {
                            'drug': 'Metformin',
                            'dose': 'Start 500mg daily or BID with meals; titrate to 1000mg BID (max 2550mg/day)',
                            'line': 'First-line unless contraindicated',
                            'benefits': 'A1c ↓1-2%, weight neutral/loss, low cost, CV neutral, low hypoglycemia risk',
                            'contraindications': 'eGFR <30, severe liver disease, acidosis',
                            'side_effects': 'GI upset (take with food), B12 deficiency (long-term)'
                        }
                    ],
                    monitoring=["A1c q3mo until goal, then q6mo", "eGFR, Cr annually", "B12 every 1-2 years on metformin"],
                    duration="Indefinite (continue even when adding other agents)",
                    success_criteria="A1c <7% (individualize: <6.5% if newly diagnosed; <8% if elderly/comorbid)",
                    escalation_criteria="A1c ≥7% after 3 months at max tolerated metformin dose"
                ),
                TreatmentStep(
                    step_number=2,
                    description="Add second agent based on comorbidities (ASCVD, HF, CKD) or patient factors",
                    medications=[
                        {
                            'class': 'GLP-1 RA (preferred if ASCVD, need weight loss)',
                            'examples': 'Semaglutide 0.25-1mg SC weekly, Dulaglutide 0.75-1.5mg SC weekly',
                            'benefits': 'A1c ↓1-1.5%, weight loss 3-5kg, CV benefit, low hypoglycemia',
                            'side_effects': 'Nausea (titrate slowly), pancreatitis (rare)',
                            'line': 'Preferred if ASCVD or high CV risk'
                        },
                        {
                            'class': 'SGLT2 inhibitor (preferred if HF or CKD)',
                            'examples': 'Empagliflozin 10-25mg daily, Dapagliflozin 5-10mg daily',
                            'benefits': 'A1c ↓0.5-1%, weight loss, HF benefit, CKD benefit, BP ↓',
                            'side_effects': 'Genital mycotic infections, DKA (rare), Fournier gangrene (very rare)',
                            'contraindications': 'eGFR <20-25 (varies by agent)',
                            'line': 'Preferred if HF or CKD (eGFR >20)'
                        },
                        {
                            'class': 'DPP-4 inhibitor (if cost concern, weight neutral)',
                            'examples': 'Sitagliptin 100mg daily, Linagliptin 5mg daily',
                            'benefits': 'A1c ↓0.5-0.8%, weight neutral, low hypoglycemia',
                            'side_effects': 'Generally well-tolerated',
                            'line': 'Alternative if GLP-1/SGLT2i not suitable'
                        },
                        {
                            'class': 'Sulfonylurea (if cost concern, not preferred)',
                            'examples': 'Glipizide 5-20mg daily, Glimepiride 1-4mg daily',
                            'benefits': 'A1c ↓1-1.5%, low cost',
                            'side_effects': 'Hypoglycemia, weight gain',
                            'line': 'Third-line due to hypoglycemia/weight gain'
                        }
                    ],
                    monitoring=["A1c q3mo", "Weight, BP", "eGFR if on SGLT2i"],
                    escalation_criteria="A1c ≥7% after 3 months"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Triple therapy or consider insulin",
                    medications=[
                        {
                            'option': 'Add third oral/injectable agent',
                            'note': 'GLP-1 + SGLT2i + Metformin is highly effective triple therapy'
                        },
                        {
                            'option': 'Basal insulin',
                            'examples': 'Glargine 10 units SC qHS or Degludec 10 units SC daily',
                            'titration': 'Increase 2 units q3 days until fasting glucose 80-130 mg/dL',
                            'note': 'Consider if A1c >10% or symptomatic hyperglycemia',
                            'side_effects': 'Hypoglycemia, weight gain'
                        }
                    ],
                    escalation_criteria="A1c ≥8-9% or symptomatic hyperglycemia - consider insulin"
                ),
                TreatmentStep(
                    step_number=4,
                    description="Intensive insulin therapy",
                    medications=[
                        {
                            'regimen': 'Basal-bolus insulin',
                            'description': 'Basal (glargine/degludec) + prandial rapid-acting (aspart/lispro) with meals',
                            'note': 'Typically for A1c >9% or Type 1 features'
                        }
                    ],
                    monitoring=["SMBG 4+ times daily", "A1c q3mo", "Hypoglycemia awareness"],
                )
            ],
            contraindications=[
                "Metformin: eGFR <30",
                "SGLT2i: eGFR <20-25, type 1 DM (risk of DKA)",
                "GLP-1 RA: Personal/family hx medullary thyroid CA, MEN 2"
            ],
            special_populations={
                'ASCVD': 'GLP-1 RA or SGLT2i with proven CV benefit (empagliflozin, canagliflozin, liraglutide, semaglutide)',
                'Heart Failure': 'SGLT2i (empagliflozin, dapagliflozin) - reduces HF hospitalizations',
                'CKD': 'SGLT2i (if eGFR >20) + GLP-1 RA',
                'Elderly': 'Avoid sulfonylureas (hypoglycemia risk), less stringent A1c target (<8%)',
                'Pregnancy': 'Insulin only (metformin sometimes used)'
            },
            references=[
                "ADA Standards of Care 2024",
                "Davies et al. Diabetologia 2022 (ADA/EASD Consensus)"
            ]
        )

    def _heart_failure_protocol(self) -> TreatmentProtocol:
        """Heart Failure with reduced EF (HFrEF) management"""
        return TreatmentProtocol(
            condition="Heart Failure with Reduced Ejection Fraction (HFrEF, EF <40%)",
            guideline_source="ACC/AHA/HFSA 2022 Heart Failure Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Guideline-Directed Medical Therapy (GDMT) - Foundational 4 pillars",
                    medications=[
                        {
                            'class': 'ACE-I or ARB (or ARNI)',
                            'examples': 'Lisinopril 5-40mg daily, Enalapril 10-20mg BID; OR Sacubitril/Valsartan 24/26 mg BID → 97/103mg BID',
                            'line': 'FIRST-LINE - Mortality benefit',
                            'titration': 'Start low, double dose q2 weeks to target or max tolerated',
                            'monitoring': 'Cr, K in 1-2 weeks; Target dose'
                        },
                        {
                            'class': 'Beta-Blocker',
                            'examples': 'Carvedilol 3.125mg BID → 25mg BID; Metoprolol succinate 25mg daily → 200mg daily; Bisoprolol',
                            'line': 'FIRST-LINE - Mortality benefit',
                            'titration': 'Start low, titrate q2 weeks',
                            'note': 'Only 3 proven: carvedilol, metoprolol succinate, bisoprolol'
                        },
                        {
                            'class': 'MRA (Mineralocorticoid Receptor Antagonist)',
                            'examples': 'Spironolactone 12.5-25mg daily, Eplerenone 25-50mg daily',
                            'line': 'FIRST-LINE - Mortality benefit',
                            'contraindications': 'K >5.0, Cr >2.5 (men) or >2.0 (women)',
                            'monitoring': 'K, Cr at 1 week, 1 month, then q3-6mo - HYPERKALEMIA risk'
                        },
                        {
                            'class': 'SGLT2 Inhibitor',
                            'examples': 'Dapagliflozin 10mg daily, Empagliflozin 10mg daily',
                            'line': 'FIRST-LINE - Reduces HF hospitalizations and CV death',
                            'note': 'Even if no diabetes - Class I recommendation 2021'
                        }
                    ],
                    non_pharm=[
                        "Sodium restriction <2-3g/day",
                        "Fluid restriction 1.5-2L/day if volume overloaded",
                        "Daily weights (call if gain >2-3 lbs in 1 day or >5 lbs in 1 week)",
                        "Cardiac rehabilitation",
                        "Smoking cessation, limit alcohol"
                    ],
                    monitoring=["BNP/NT-proBNP", "Cr, K, Na q1-3mo", "Weight daily", "Symptoms (NYHA class)"],
                    success_criteria="Symptom improvement, target doses of GDMT, BNP decrease",
                    duration="Lifelong (unless contraindication)"
                ),
                TreatmentStep(
                    step_number=2,
                    description="Diuretics for volume management (symptom relief, no mortality benefit)",
                    medications=[
                        {
                            'class': 'Loop Diuretic',
                            'examples': 'Furosemide 20-240mg daily/BID, Torsemide 10-100mg daily',
                            'note': 'Use lowest dose to maintain euvolemia',
                            'monitoring': 'Electrolytes (K, Mg), Cr'
                        }
                    ],
                    non_pharm=["Titrate based on volume status and daily weights"],
                    duration="Ongoing, adjust dose based on symptoms/weight"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Additional therapies if persistent symptoms on GDMT",
                    medications=[
                        {
                            'option': 'Hydralazine + Isosorbide Dinitrate',
                            'dose': 'Hydralazine 37.5mg TID → 75mg TID; ISDN 20mg TID → 40mg TID',
                            'indication': 'Self-identified Black patients (A-HeFT trial), or if ACE-I/ARB/ARNI intolerant',
                            'benefits': 'Mortality benefit in Black patients'
                        },
                        {
                            'option': 'Ivabradine',
                            'dose': '5-7.5mg BID',
                            'indication': 'HR >70 bpm on max beta-blocker in sinus rhythm',
                            'benefits': 'Reduces HF hospitalizations'
                        },
                        {
                            'option': 'Digoxin',
                            'dose': '0.125-0.25mg daily',
                            'indication': 'Persistent symptoms despite GDMT, or AFib rate control',
                            'note': 'Reduces hospitalizations, no mortality benefit',
                            'monitoring': 'Digoxin level 0.5-0.9 ng/mL, K'
                        }
                    ]
                ),
                TreatmentStep(
                    step_number=4,
                    description="Device therapy consideration",
                    medications=[],
                    non_pharm=[
                        "ICD (Implantable Cardioverter-Defibrillator): EF ≤35% despite ≥3mo GDMT, NYHA II-III, life expectancy >1 year",
                        "CRT (Cardiac Resynchronization Therapy): EF ≤35%, LBBB with QRS ≥150ms, NYHA II-IV on GDMT",
                        "LVAD (Left Ventricular Assist Device): Advanced HF, bridge to transplant or destination therapy",
                        "Heart Transplant: End-stage HF refractory to medical therapy"
                    ],
                    monitoring=["Reassess EF after 3+ months of GDMT before device"]
                )
            ],
            contraindications=[
                "ACE-I/ARNI: Pregnancy, angioedema",
                "Beta-blocker: Decompensated HF (hold until stable), severe bradycardia/heart block",
                "MRA: K >5.0, severe CKD"
            ],
            special_populations={
                'Acute Decompensated HF': 'IV diuretics, vasodilators if HTN, may need ICU',
                'HFpEF (EF ≥50%)': 'SGLT2i (dapagliflozin), diuretics, treat comorbidities - no proven mortality benefit drugs',
                'Pregnant': 'Avoid ACE-I/ARB/ARNI, MRA'
            },
            references=[
                "2022 AHA/ACC/HFSA Heart Failure Guidelines",
                "Heidenreich et al. Circulation 2022"
            ]
        )

    def _copd_protocol(self) -> TreatmentProtocol:
        """COPD management (GOLD guidelines)"""
        return TreatmentProtocol(
            condition="COPD (Chronic Obstructive Pulmonary Disease)",
            guideline_source="GOLD 2024 Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="All patients - Smoking cessation and vaccinations",
                    non_pharm=[
                        "SMOKING CESSATION - most important intervention",
                        "Nicotine replacement, varenicline, or bupropion",
                        "Pulmonary rehabilitation",
                        "Influenza vaccine annually",
                        "Pneumococcal vaccine (PPSV23, PCV20)",
                        "COVID-19 vaccine"
                    ],
                    monitoring=["Spirometry for diagnosis and staging (FEV1/FVC <0.7)", "Assess GOLD grade (FEV1 % predicted)"],
                    duration="Ongoing"
                ),
                TreatmentStep(
                    step_number=2,
                    description="Pharmacotherapy - Based on symptoms (CAT/mMRC) and exacerbation history",
                    medications=[
                        {
                            'group': 'Group A (Low symptoms, low exacerbation)',
                            'treatment': 'Bronchodilator PRN: SABA (albuterol) or SAMA (ipratropium)',
                            'note': 'Can escalate to LABA or LAMA if symptomatic'
                        },
                        {
                            'group': 'Group B (More symptoms, low exacerbation)',
                            'treatment': 'LABA or LAMA (long-acting bronchodilator)',
                            'examples': 'Tiotropium 18mcg daily, Formoterol 12mcg BID',
                            'escalation': 'LABA + LAMA if not controlled'
                        },
                        {
                            'group': 'Group E (Frequent exacerbations)',
                            'treatment': 'LABA + LAMA ± ICS',
                            'examples': 'LABA/LAMA: Umeclidinium/Vilanterol; Add ICS if eosinophils >300 or frequent exacerbations',
                            'note': 'ICS increases pneumonia risk - use selectively'
                        }
                    ],
                    monitoring=["Symptoms (CAT score)", "Exacerbation frequency", "Spirometry annually"],
                    escalation_criteria="Persistent symptoms or exacerbations"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Exacerbation management",
                    medications=[
                        {
                            'treatment': 'Increase bronchodilators (SABA + SAMA)',
                            'dose': 'Albuterol 2.5mg + Ipratropium 0.5mg nebulized q4-6h or continuously if severe'
                        },
                        {
                            'treatment': 'Systemic corticosteroids',
                            'dose': 'Prednisone 40mg daily x 5 days',
                            'note': 'Shorter course (5 days) as effective as longer'
                        },
                        {
                            'treatment': 'Antibiotics (if purulent sputum or severe exacerbation)',
                            'examples': 'Amoxicillin-clavulanate, doxycycline, or azithromycin x 5 days',
                            'note': 'Cover H. influenzae, S. pneumoniae, M. catarrhalis'
                        },
                        {
                            'treatment': 'Oxygen (if hypoxemic)',
                            'target': 'O2 sat 88-92% in COPD (avoid high-flow O2 in chronic CO2 retainers)'
                        },
                        {
                            'treatment': 'NIV (BiPAP) if respiratory acidosis or severe dyspnea',
                            'note': 'Reduces intubation and mortality'
                        }
                    ],
                    duration="Prednisone 5 days, antibiotics 5 days"
                )
            ],
            special_populations={
                'Severe COPD': 'Long-term oxygen therapy if PaO2 <55 mmHg or O2 sat <88%',
                'Frequent exacerbations': 'Consider azithromycin 250mg daily or roflumilast'
            },
            references=["GOLD 2024 COPD Guidelines"]
        )

    def _cap_protocol(self) -> TreatmentProtocol:
        """Community-Acquired Pneumonia protocol"""
        return TreatmentProtocol(
            condition="Community-Acquired Pneumonia (CAP)",
            guideline_source="ATS/IDSA 2019 CAP Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Risk stratification (CURB-65 or PSI)",
                    non_pharm=[
                        "CURB-65: Confusion, Urea >20, RR ≥30, BP <90/60, age ≥65",
                        "0-1: Outpatient; 2: Consider admission; ≥3: Inpatient (ICU if ≥4)",
                        "PSI (Pneumonia Severity Index): Classes I-II outpatient, III consider, IV-V inpatient"
                    ]
                ),
                TreatmentStep(
                    step_number=2,
                    description="Outpatient treatment (no comorbidities, no recent antibiotics)",
                    medications=[
                        {
                            'option_1': 'Amoxicillin 1g TID',
                            'line': 'Preferred',
                            'duration': '5-7 days'
                        },
                        {
                            'option_2': 'Doxycycline 100mg BID',
                            'line': 'Alternative',
                            'duration': '5-7 days'
                        },
                        {
                            'option_3': 'Macrolide (if low resistance area)',
                            'examples': 'Azithromycin 500mg day 1, then 250mg daily x 4 days',
                            'note': 'High S. pneumoniae resistance in many areas'
                        }
                    ],
                    duration="5-7 days total"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Outpatient with comorbidities (COPD, DM, CHF, recent antibiotics)",
                    medications=[
                        {
                            'regimen': 'Amoxicillin-clavulanate 875/125mg BID + Macrolide',
                            'note': 'OR Respiratory fluoroquinolone alone'
                        },
                        {
                            'alternative': 'Levofloxacin 750mg daily OR Moxifloxacin 400mg daily',
                            'line': 'Respiratory fluoroquinolone monotherapy',
                            'duration': '5-7 days'
                        }
                    ]
                ),
                TreatmentStep(
                    step_number=4,
                    description="Inpatient non-severe",
                    medications=[
                        {
                            'preferred': 'Beta-lactam + Macrolide',
                            'examples': 'Ceftriaxone 1-2g IV daily + Azithromycin 500mg IV/PO daily',
                            'duration': 'Transition to PO when improving; total 5-7 days'
                        },
                        {
                            'alternative': 'Respiratory fluoroquinolone',
                            'examples': 'Levofloxacin 750mg IV daily'
                        }
                    ]
                ),
                TreatmentStep(
                    step_number=5,
                    description="Severe CAP (ICU)",
                    medications=[
                        {
                            'regimen': 'Beta-lactam + Macrolide OR Fluoroquinolone',
                            'examples': 'Ceftriaxone 2g IV daily + Azithromycin 500mg IV daily',
                            'alternatives': 'Cefotaxime, Ampicillin-sulbactam'
                        },
                        {
                            'add_coverage': 'If MRSA risk: add Vancomycin or Linezolid',
                            'mrsa_risk': 'Prior MRSA, severe influenza'
                        },
                        {
                            'add_coverage': 'If Pseudomonas risk: Piperacillin-tazobactam or Cefepime + Ciprofloxacin',
                            'pseudo_risk': 'Bronchiectasis, recent antibiotics, severe COPD'
                        }
                    ],
                    duration="Typically 7-10 days (shorter if rapid improvement)"
                )
            ],
            monitoring=["Clinical improvement by day 3-5", "Transition to PO when stable", "Duration based on severity"],
            references=["Metlay et al. Am J Respir Crit Care Med 2019 (ATS/IDSA CAP Guidelines)"]
        )

    def _uti_protocol(self) -> TreatmentProtocol:
        """Urinary Tract Infection protocol"""
        return TreatmentProtocol(
            condition="Urinary Tract Infection",
            guideline_source="IDSA 2011 UTI Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Acute uncomplicated cystitis (healthy women)",
                    medications=[
                        {'drug': 'Nitrofurantoin 100mg BID', 'duration': '5 days', 'line': 'First-line'},
                        {'drug': 'TMP-SMX DS BID', 'duration': '3 days', 'line': 'First-line if local resistance <20%'},
                        {'drug': 'Fosfomycin 3g single dose', 'duration': '1 day', 'line': 'Alternative (lower efficacy)'},
                        {'drug': 'Ciprofloxacin 250mg BID', 'duration': '3 days', 'line': 'Reserve for complicated UTI'}
                    ],
                    monitoring=["Symptoms should improve in 48-72h", "No routine post-treatment culture if asymptomatic"]
                ),
                TreatmentStep(
                    step_number=2,
                    description="Pyelonephritis (outpatient)",
                    medications=[
                        {'drug': 'Ciprofloxacin 500mg BID', 'duration': '7 days', 'line': 'If local resistance <10%'},
                        {'drug': 'Levofloxacin 750mg daily', 'duration': '5 days'},
                        {'drug': 'Ceftriaxone 1g IV x1 then PO step-down', 'note': 'If high resistance or severe'}
                    ],
                    duration="7 days for fluoroquinolones, 10-14 days for beta-lactams"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Complicated UTI or severe pyelonephritis (inpatient)",
                    medications=[
                        {'regimen': 'Ceftriaxone 1-2g IV daily OR Cefepime 1-2g IV q8-12h'},
                        {'add': 'If gram-positive on culture: Ampicillin 1-2g IV q6h (Enterococcus coverage)'},
                        {'add': 'If ESBL or resistant: Carbapenem (ertapenem, meropenem)'}
                    ],
                    duration="10-14 days total",
                    monitoring=["Blood cultures if septic", "Renal ultrasound if not improving"]
                )
            ],
            special_populations={
                'Pregnancy': 'Avoid fluoroquinolones; use cephalexin, amoxicillin-clavulanate; treat ASB',
                'Men': 'Consider prostatitis - treat 7 days minimum',
                'Catheter-associated': 'Remove catheter if possible; treat only if symptomatic'
            },
            references=["Gupta et al. Clin Infect Dis 2011 (IDSA UTI Guidelines)"]
        )

    def _acs_protocol(self) -> TreatmentProtocol:
        """NSTEMI/Unstable Angina protocol"""
        return TreatmentProtocol(
            condition="Acute Coronary Syndrome - NSTEMI/Unstable Angina",
            guideline_source="ACC/AHA 2021 ACS Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Immediate management (ED/CCU)",
                    medications=[
                        {'drug': 'Aspirin 162-325mg chewed', 'note': 'IMMEDIATELY'},
                        {'drug': 'P2Y12 inhibitor', 'options': 'Ticagrelor 180mg load, then 90mg BID OR Clopidogrel 600mg load, then 75mg daily', 'note': 'Ticagrelor preferred'},
                        {'drug': 'Anticoagulation: Heparin or Enoxaparin', 'examples': 'Enoxaparin 1mg/kg SC q12h'},
                        {'drug': 'Beta-blocker', 'examples': 'Metoprolol 25-50mg PO q6h (if no HF/cardiogenic shock)'},
                        {'drug': 'Statin - high intensity', 'examples': 'Atorvastatin 80mg daily'},
                        {'drug': 'Nitroglycerin SL 0.4mg q5min x3 for chest pain'}
                    ],
                    non_pharm=["Oxygen if O2 sat <90%", "Continuous telemetry", "NPO (for potential cath)"],
                    monitoring=["Troponin serial (0, 3, 6h)", "ECG serial", "GRACE or TIMI score for risk stratification"]
                ),
                TreatmentStep(
                    step_number=2,
                    description="Invasive strategy timing",
                    non_pharm=[
                        "Immediate (<2h): Refractory angina, hemodynamic instability, ventricular arrhythmias",
                        "Early (<24h): GRACE >140, elevated troponin, dynamic ECG changes",
                        "Delayed (25-72h): Low-risk patients"
                    ],
                    medications=[],
                    monitoring=["Coronary angiography ± PCI"]
                ),
                TreatmentStep(
                    step_number=3,
                    description="Post-discharge secondary prevention",
                    medications=[
                        {'drug': 'Aspirin 81mg daily', 'duration': 'Lifelong'},
                        {'drug': 'P2Y12 inhibitor', 'duration': '12 months (DAPT)', 'note': 'Then aspirin alone'},
                        {'drug': 'Beta-blocker', 'duration': '3 years minimum if EF normal', 'examples': 'Metoprolol succinate 100-200mg daily'},
                        {'drug': 'ACE-I or ARB', 'indication': 'All patients, especially if EF <40%, DM, HTN', 'examples': 'Lisinopril 10-40mg daily'},
                        {'drug': 'Statin - high intensity', 'examples': 'Atorvastatin 80mg or Rosuvastatin 40mg', 'target': 'LDL <70 mg/dL'},
                        {'drug': 'Ezetimibe if LDL still >70 on statin', 'dose': '10mg daily'}
                    ],
                    non_pharm=["Cardiac rehabilitation", "Smoking cessation", "Diet and exercise"],
                    monitoring=["Lipid panel at 4-12 weeks", "Echo to assess EF"]
                )
            ],
            references=["Gulati et al. J Am Coll Cardiol 2021 (ACS Guidelines)"]
        )

    def _stroke_protocol(self) -> TreatmentProtocol:
        """Acute ischemic stroke protocol"""
        return TreatmentProtocol(
            condition="Acute Ischemic Stroke",
            guideline_source="AHA/ASA 2019 Stroke Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Hyperacute management (<4.5 hours)",
                    non_pharm=[
                        "CODE STROKE activation",
                        "STAT non-contrast CT head (rule out hemorrhage)",
                        "NIH Stroke Scale",
                        "Last known well time"
                    ],
                    medications=[
                        {
                            'drug': 'Alteplase (tPA) 0.9 mg/kg IV',
                            'timing': 'Within 4.5 hours of symptom onset (3 hours if >80 yo)',
                            'dose': '10% bolus, 90% infusion over 60 min',
                            'exclusions': 'Hemorrhage on CT, platelets <100k, INR >1.7, recent surgery, BP >185/110'
                        }
                    ],
                    monitoring=["Neuro checks q15min x 2h, then q30min x 6h, then q1h", "BP control <180/105 post-tPA", "No anticoagulation x 24h post-tPA"]
                ),
                TreatmentStep(
                    step_number=2,
                    description="Mechanical thrombectomy (if large vessel occlusion)",
                    non_pharm=[
                        "CTA or MRA to identify LVO (ICA, M1, M2, basilar)",
                        "Thrombectomy up to 24 hours if favorable penumbra (perfusion imaging)"
                    ]
                ),
                TreatmentStep(
                    step_number=3,
                    description="Secondary prevention",
                    medications=[
                        {'drug': 'Aspirin 325mg daily x 2-4 weeks, then 81mg daily', 'note': 'Start 24h after tPA or immediately if no tPA'},
                        {'drug': 'Statin - high intensity', 'examples': 'Atorvastatin 80mg daily'},
                        {'drug': 'If cardioembolic (AFib): Anticoagulation', 'options': 'Apixaban, rivaroxaban, warfarin', 'timing': 'Delay 4-14 days based on stroke size'},
                        {'drug': 'If atherosclerotic: Dual antiplatelet (ASA + clopidogrel) x 21-90 days', 'note': 'High-risk TIA or minor stroke'}
                    ],
                    non_pharm=["Rehab: PT, OT, speech therapy", "Smoking cessation", "BP control <130/80 long-term"]
                )
            ],
            references=["Powers et al. Stroke 2019 (AHA/ASA Stroke Guidelines)"]
        )

    def _sepsis_protocol(self) -> TreatmentProtocol:
        """Sepsis and Septic Shock protocol"""
        return TreatmentProtocol(
            condition="Sepsis and Septic Shock",
            guideline_source="Surviving Sepsis Campaign 2021",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Hour-1 Bundle (immediately)",
                    medications=[
                        {'action': 'Broad-spectrum antibiotics within 1 hour', 'note': 'After blood cultures'},
                        {'action': '30 mL/kg IV crystalloid for hypotension or lactate ≥4', 'note': 'LR or NS'},
                        {'action': 'Vasopressors if hypotension during/after fluids (MAP ≥65)', 'drug': 'Norepinephrine preferred'}
                    ],
                    non_pharm=[
                        "Measure lactate (repeat if ≥2)",
                        "Obtain blood cultures BEFORE antibiotics",
                        "Assess for source control (abscess, infected device)"
                    ],
                    monitoring=["Lactate clearance", "MAP ≥65 mmHg", "Urine output ≥0.5 mL/kg/hr"]
                ),
                TreatmentStep(
                    step_number=2,
                    description="Antibiotic selection (empiric - narrow based on source/culture)",
                    medications=[
                        {'source': 'Unknown', 'regimen': 'Vancomycin + Piperacillin-tazobactam (or cefepime)'},
                        {'source': 'Abdominal', 'regimen': 'Pip-tazo OR Carbapenem + Metronidazole'},
                        {'source': 'Pneumonia', 'regimen': 'Vanc + Ceftriaxone + Azithromycin'},
                        {'source': 'Urosepsis', 'regimen': 'Ceftriaxone or Cefepime (add vanc if concern for enterococcus)'}
                    ],
                    duration="De-escalate based on cultures at 48-72h; Total 7-10 days"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Supportive care",
                    medications=[
                        {'drug': 'Norepinephrine for shock', 'target': 'MAP ≥65 mmHg'},
                        {'drug': 'Vasopressin or epinephrine if refractory'},
                        {'drug': 'Hydrocortisone 200mg/day if refractory shock', 'note': 'Controversial'}
                    ],
                    non_pharm=["Mechanical ventilation if ARDS", "Source control (drain abscess, remove infected catheter)"]
                )
            ],
            references=["Evans et al. Crit Care Med 2021 (Surviving Sepsis Campaign)"]
        )

    def _dka_protocol(self) -> TreatmentProtocol:
        """Diabetic Ketoacidosis protocol"""
        return TreatmentProtocol(
            condition="Diabetic Ketoacidosis (DKA)",
            guideline_source="ADA DKA Guidelines",
            steps=[
                TreatmentStep(
                    step_number=1,
                    description="Diagnosis and initial management",
                    non_pharm=[
                        "Diagnosis: Glucose >250, pH <7.3, HCO3 <18, ketones positive",
                        "Assess severity: Mild (pH 7.25-7.3), Moderate (pH 7.0-7.24), Severe (pH <7.0)"
                    ],
                    monitoring=["VBG or ABG", "BMP q2-4h", "Glucose q1h", "Anion gap"]
                ),
                TreatmentStep(
                    step_number=2,
                    description="Fluid resuscitation",
                    medications=[
                        {'fluid': 'NS 1L/hr x 1-2 hours', 'then': '250-500 mL/hr'},
                        {'switch': 'D5 1/2 NS when glucose <250 mg/dL', 'note': 'Continue until ketoacidosis resolves'}
                    ],
                    duration="Until euvolemic and ketoacidosis resolved"
                ),
                TreatmentStep(
                    step_number=3,
                    description="Insulin therapy",
                    medications=[
                        {'regimen': 'Regular insulin 0.1 units/kg IV bolus, then 0.1 units/kg/hr infusion'},
                        {'target': 'Decrease glucose 50-75 mg/dL per hour'},
                        {'adjust': 'If glucose not dropping, double insulin rate'}
                    ],
                    monitoring=["Do NOT stop insulin until anion gap closes", "Transition to SC insulin when eating"]
                ),
                TreatmentStep(
                    step_number=4,
                    description="Electrolyte management",
                    medications=[
                        {'electrolyte': 'Potassium', 'goal': 'Keep K 4-5 mEq/L', 'repletion': 'Add 20-40 mEq/L to IV fluids', 'note': 'DO NOT start insulin if K <3.3'},
                        {'electrolyte': 'Phosphate', 'note': 'Usually not needed unless <1.0 mg/dL'},
                        {'electrolyte': 'Bicarbonate', 'indication': 'Only if pH <6.9', 'dose': 'NaHCO3 100 mEq in 400mL H2O over 2h'}
                    ]
                ),
                TreatmentStep(
                    step_number=5,
                    description="Resolution criteria and transition",
                    non_pharm=[
                        "Resolution: Glucose <200, HCO3 ≥18, pH >7.3, anion gap <12",
                        "Transition: Start SC basal insulin 2h before stopping IV insulin",
                        "Identify precipitant (infection, non-compliance, new DM)"
                    ]
                )
            ],
            references=["ADA DKA Management Guidelines"]
        )

    def get_protocol(self, condition: str) -> Optional[TreatmentProtocol]:
        """
        Get treatment protocol for a condition.

        Args:
            condition: Condition name (e.g., 'hypertension', 'diabetes_type2')

        Returns:
            TreatmentProtocol object or None if not found
        """
        condition_lower = condition.lower().replace(' ', '_').replace('-', '_')

        # Map common variations
        condition_map = {
            'htn': 'hypertension',
            'dm': 'diabetes_type2',
            'type_2_diabetes': 'diabetes_type2',
            'chf': 'heart_failure',
            'hfref': 'heart_failure',
            'cap': 'pneumonia_cap',
            'pneumonia': 'pneumonia_cap',
            'nstemi': 'acs_nstemi',
            'unstable_angina': 'acs_nstemi',
            'cva': 'stroke_ischemic',
            'stroke': 'stroke_ischemic',
        }

        condition_key = condition_map.get(condition_lower, condition_lower)

        protocol_method = self.protocols.get(condition_key)
        if protocol_method:
            return protocol_method()

        return None


def get_treatment_protocol(condition: str) -> Optional[Dict]:
    """
    Get treatment protocol for a condition.

    Args:
        condition: Condition name

    Returns:
        Dictionary with treatment protocol or None

    Example:
        >>> protocol = get_treatment_protocol("hypertension")
    """
    engine = ProtocolEngine()
    protocol = engine.get_protocol(condition)

    if not protocol:
        return None

    return {
        'condition': protocol.condition,
        'guideline_source': protocol.guideline_source,
        'steps': [
            {
                'step_number': step.step_number,
                'description': step.description,
                'medications': step.medications,
                'non_pharmacologic': step.non_pharm,
                'monitoring': step.monitoring,
                'duration': step.duration,
                'success_criteria': step.success_criteria,
                'escalation_criteria': step.escalation_criteria
            }
            for step in protocol.steps
        ],
        'contraindications': protocol.contraindications,
        'special_populations': protocol.special_populations,
        'references': protocol.references
    }
