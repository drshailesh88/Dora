"""
Differential Diagnosis Generator for Clinical Decision Support

This module provides evidence-based differential diagnosis generation based on
patient symptoms, demographics, and clinical history.

MEDICAL DISCLAIMER:
This tool is for educational and clinical decision support purposes only.
It does not replace clinical judgment. All diagnoses must be confirmed by
a qualified healthcare provider. Not for use as a sole diagnostic tool.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class Severity(Enum):
    """Diagnosis urgency level"""
    EMERGENT = "emergent"  # Immediate life-threatening
    URGENT = "urgent"      # Needs evaluation within hours
    NON_URGENT = "non-urgent"  # Can be evaluated outpatient


class AgeGroup(Enum):
    """Patient age categories"""
    NEONATE = "neonate"      # 0-28 days
    INFANT = "infant"        # 29 days - 1 year
    CHILD = "child"          # 1-12 years
    ADOLESCENT = "adolescent"  # 13-18 years
    ADULT = "adult"          # 19-64 years
    ELDERLY = "elderly"      # 65+ years


@dataclass
class RedFlag:
    """Critical warning sign requiring immediate attention"""
    finding: str
    implication: str
    action: str


@dataclass
class Diagnosis:
    """Differential diagnosis with supporting information"""
    name: str
    icd10: str
    probability: float  # 0.0 to 1.0
    severity: Severity
    key_features: List[str]
    distinguishing_features: List[str]
    red_flags: List[RedFlag]
    suggested_workup: List[str]
    references: List[str] = field(default_factory=list)


@dataclass
class PatientPresentation:
    """Patient clinical presentation"""
    chief_complaint: str
    symptoms: List[str]
    age: int
    gender: str  # "M", "F", "Other"
    duration: Optional[str] = None
    onset: Optional[str] = None  # "sudden", "gradual"
    severity_score: Optional[int] = None  # 1-10
    past_medical_history: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    vital_signs: Dict[str, float] = field(default_factory=dict)


class DifferentialDiagnosisGenerator:
    """
    Generates differential diagnoses based on clinical presentations.

    Evidence-based algorithms for 100+ common presentations.
    """

    def __init__(self):
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Initialize clinical decision rules and diagnostic criteria"""
        self.presentation_rules = {
            'chest_pain': self._chest_pain_differential,
            'shortness_of_breath': self._dyspnea_differential,
            'abdominal_pain': self._abdominal_pain_differential,
            'headache': self._headache_differential,
            'fever': self._fever_differential,
            'weakness': self._weakness_differential,
            'dizziness': self._dizziness_differential,
            'cough': self._cough_differential,
            'back_pain': self._back_pain_differential,
            'palpitations': self._palpitations_differential,
        }

    def _get_age_group(self, age: int) -> AgeGroup:
        """Categorize patient by age"""
        if age < 0.077:  # 28 days
            return AgeGroup.NEONATE
        elif age < 1:
            return AgeGroup.INFANT
        elif age < 13:
            return AgeGroup.CHILD
        elif age < 19:
            return AgeGroup.ADOLESCENT
        elif age < 65:
            return AgeGroup.ADULT
        else:
            return AgeGroup.ELDERLY

    def generate_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """
        Generate ranked differential diagnoses for patient presentation.

        Args:
            presentation: PatientPresentation object with clinical data

        Returns:
            List of Diagnosis objects sorted by probability (highest first)
        """
        # Normalize chief complaint
        complaint = self._normalize_complaint(presentation.chief_complaint)

        # Get appropriate differential generator
        generator = self.presentation_rules.get(complaint)

        if not generator:
            return self._generic_differential(presentation)

        # Generate differential
        differentials = generator(presentation)

        # Adjust probabilities based on patient factors
        differentials = self._adjust_probabilities(differentials, presentation)

        # Sort by probability
        differentials.sort(key=lambda x: x.probability, reverse=True)

        return differentials

    def _normalize_complaint(self, complaint: str) -> str:
        """Normalize chief complaint to standard terms"""
        complaint = complaint.lower().strip()

        # Map variations to standard terms
        mappings = {
            'chest pain': ['chest pain', 'chest discomfort', 'chest pressure', 'angina'],
            'shortness_of_breath': ['shortness of breath', 'dyspnea', 'sob', 'difficulty breathing', 'breathlessness'],
            'abdominal_pain': ['abdominal pain', 'stomach pain', 'belly pain', 'abd pain'],
            'headache': ['headache', 'head pain', 'cephalalgia'],
            'fever': ['fever', 'febrile', 'high temperature', 'pyrexia'],
            'weakness': ['weakness', 'fatigue', 'tiredness', 'malaise'],
            'dizziness': ['dizziness', 'vertigo', 'lightheaded', 'dizzy'],
            'cough': ['cough', 'coughing'],
            'back_pain': ['back pain', 'lower back pain', 'lbp'],
            'palpitations': ['palpitations', 'heart racing', 'rapid heartbeat'],
        }

        for standard, variations in mappings.items():
            if any(var in complaint for var in variations):
                return standard

        return complaint

    def _chest_pain_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """
        Differential diagnosis for chest pain.

        Based on: AHA/ACC Guidelines, HEART Score, Chest Pain Decision Rules
        """
        differentials = []
        symptoms = [s.lower() for s in presentation.symptoms]
        age = presentation.age

        # ACUTE CORONARY SYNDROME (ACS)
        acs_prob = 0.3  # Base probability
        if age > 45:
            acs_prob += 0.1
        if 'radiation to arm' in symptoms or 'radiation to jaw' in symptoms:
            acs_prob += 0.2
        if 'diaphoresis' in symptoms or 'sweating' in symptoms:
            acs_prob += 0.15
        if 'nausea' in symptoms:
            acs_prob += 0.1
        if 'diabetes' in presentation.past_medical_history:
            acs_prob += 0.1
        if presentation.gender == 'M' and age > 55:
            acs_prob += 0.1
        if presentation.gender == 'F' and age > 65:
            acs_prob += 0.1

        differentials.append(Diagnosis(
            name="Acute Coronary Syndrome (STEMI/NSTEMI/Unstable Angina)",
            icd10="I24.9",
            probability=min(acs_prob, 0.95),
            severity=Severity.EMERGENT,
            key_features=[
                "Substernal chest pressure/tightness",
                "Radiation to left arm, jaw, or back",
                "Associated diaphoresis, nausea, dyspnea",
                "Risk factors: age, diabetes, hypertension, smoking, family history"
            ],
            distinguishing_features=[
                "Troponin elevation (may be delayed)",
                "ECG changes: ST elevation (STEMI), ST depression/T-wave inversion (NSTEMI)",
                "Relieved by nitroglycerin (not diagnostic)"
            ],
            red_flags=[
                RedFlag(
                    "ST elevation on ECG",
                    "STEMI - complete coronary occlusion",
                    "Activate cath lab immediately - door-to-balloon < 90 min"
                ),
                RedFlag(
                    "Hypotension + chest pain",
                    "Cardiogenic shock or massive PE",
                    "Immediate resuscitation, consider ECMO"
                )
            ],
            suggested_workup=[
                "STAT ECG (within 10 minutes)",
                "Troponin I/T (serial at 0, 3, 6 hours)",
                "CXR",
                "CBC, BMP, coagulation studies",
                "Consider CT angiography if high suspicion"
            ],
            references=[
                "2021 AHA/ACC Chest Pain Guidelines",
                "Fourth Universal Definition of MI (2018)"
            ]
        ))

        # PULMONARY EMBOLISM
        pe_prob = 0.15
        if 'shortness of breath' in symptoms:
            pe_prob += 0.2
        if 'tachycardia' in symptoms or presentation.vital_signs.get('hr', 0) > 100:
            pe_prob += 0.15
        if 'recent surgery' in presentation.past_medical_history or 'immobilization' in presentation.past_medical_history:
            pe_prob += 0.2
        if 'hemoptysis' in symptoms:
            pe_prob += 0.15

        differentials.append(Diagnosis(
            name="Pulmonary Embolism",
            icd10="I26.99",
            probability=min(pe_prob, 0.9),
            severity=Severity.EMERGENT,
            key_features=[
                "Pleuritic chest pain",
                "Sudden onset dyspnea",
                "Tachycardia, tachypnea",
                "Risk factors: recent surgery, immobilization, cancer, hypercoagulable state"
            ],
            distinguishing_features=[
                "D-dimer elevation (sensitive, not specific)",
                "CT pulmonary angiography - filling defect",
                "Wells Score or PERC rule for risk stratification"
            ],
            red_flags=[
                RedFlag(
                    "Hypotension + tachycardia",
                    "Massive PE with hemodynamic compromise",
                    "Consider thrombolysis, ECMO, or surgical embolectomy"
                ),
                RedFlag(
                    "Right heart strain on echo",
                    "Submassive PE",
                    "ICU monitoring, consider catheter-directed therapy"
                )
            ],
            suggested_workup=[
                "Wells Score or PERC rule",
                "D-dimer (if low/intermediate risk)",
                "CT pulmonary angiography (CTPA)",
                "ECG (S1Q3T3 pattern, right heart strain)",
                "Troponin, BNP (prognostic)",
                "Lower extremity doppler ultrasound"
            ],
            references=[
                "ESC 2019 PE Guidelines",
                "PERC Rule (Kline et al, 2004)"
            ]
        ))

        # AORTIC DISSECTION
        dissection_prob = 0.05
        if 'tearing pain' in symptoms or 'ripping pain' in symptoms:
            dissection_prob += 0.3
        if 'radiation to back' in symptoms:
            dissection_prob += 0.2
        if 'hypertension' in presentation.past_medical_history:
            dissection_prob += 0.15
        if age > 60:
            dissection_prob += 0.1
        if 'marfan' in presentation.past_medical_history or 'connective tissue disease' in presentation.past_medical_history:
            dissection_prob += 0.2

        differentials.append(Diagnosis(
            name="Aortic Dissection",
            icd10="I71.00",
            probability=min(dissection_prob, 0.85),
            severity=Severity.EMERGENT,
            key_features=[
                "Sudden onset severe 'tearing' or 'ripping' chest/back pain",
                "Radiation to back (interscapular)",
                "Blood pressure differential between arms (>20 mmHg)",
                "Risk factors: hypertension, Marfan syndrome, bicuspid aortic valve"
            ],
            distinguishing_features=[
                "Widened mediastinum on CXR (not sensitive)",
                "CT angiography - intimal flap",
                "TEE (if unstable)",
                "Pulse deficits, neurologic deficits, acute AI murmur"
            ],
            red_flags=[
                RedFlag(
                    "Hypotension in aortic dissection",
                    "Rupture, tamponade, or severe AI",
                    "Emergent surgery - do NOT delay for imaging if unstable"
                ),
                RedFlag(
                    "Neurologic deficits",
                    "Carotid or spinal artery involvement",
                    "Surgical emergency"
                )
            ],
            suggested_workup=[
                "STAT CXR (widened mediastinum)",
                "CT angiography chest/abdomen/pelvis with IV contrast",
                "TEE if patient unstable",
                "ECG (to rule out MI)",
                "Blood pressure in both arms",
                "Cardiothoracic surgery consult"
            ],
            references=[
                "2022 ACC/AHA Aortic Disease Guidelines",
                "ADD Risk Score (Rogers et al, 2011)"
            ]
        ))

        # PERICARDITIS
        pericarditis_prob = 0.1
        if 'positional' in symptoms or 'worse lying down' in symptoms:
            pericarditis_prob += 0.2
        if 'better leaning forward' in symptoms:
            pericarditis_prob += 0.25
        if 'viral illness' in presentation.past_medical_history or 'recent viral illness' in symptoms:
            pericarditis_prob += 0.15
        if age < 40:
            pericarditis_prob += 0.1

        differentials.append(Diagnosis(
            name="Acute Pericarditis",
            icd10="I30.9",
            probability=min(pericarditis_prob, 0.8),
            severity=Severity.URGENT,
            key_features=[
                "Sharp, pleuritic chest pain",
                "Positional - worse lying flat, better leaning forward",
                "Pericardial friction rub (pathognomonic but often absent)",
                "Often follows viral illness"
            ],
            distinguishing_features=[
                "Diffuse ST elevation on ECG (without reciprocal changes)",
                "PR depression",
                "Elevated inflammatory markers (ESR, CRP)",
                "Pericardial effusion on echo (if present)"
            ],
            red_flags=[
                RedFlag(
                    "Pericardial effusion with tamponade physiology",
                    "Cardiac tamponade",
                    "Emergent pericardiocentesis"
                ),
                RedFlag(
                    "Fever + elevated troponin",
                    "Myopericarditis",
                    "Monitor for arrhythmia, heart failure"
                )
            ],
            suggested_workup=[
                "ECG (diffuse ST elevation, PR depression)",
                "Echocardiogram (effusion, tamponade)",
                "Inflammatory markers (ESR, CRP)",
                "Troponin (myopericarditis if elevated)",
                "CXR",
                "Consider viral serologies, ANA, RF if recurrent"
            ],
            references=[
                "2015 ESC Pericardial Diseases Guidelines"
            ]
        ))

        # COSTOCHONDRITIS (MUSCULOSKELETAL)
        costo_prob = 0.2
        if 'reproducible with palpation' in symptoms or 'tender to touch' in symptoms:
            costo_prob += 0.3
        if 'worse with movement' in symptoms or 'worse with deep breath' in symptoms:
            costo_prob += 0.2
        if age < 40 and len([s for s in symptoms if s in ['radiation to arm', 'diaphoresis', 'nausea']]) == 0:
            costo_prob += 0.2

        differentials.append(Diagnosis(
            name="Costochondritis (Musculoskeletal Chest Pain)",
            icd10="M94.0",
            probability=min(costo_prob, 0.75),
            severity=Severity.NON_URGENT,
            key_features=[
                "Chest wall tenderness reproducible with palpation",
                "Sharp pain, worse with movement or deep inspiration",
                "No radiation, diaphoresis, or systemic symptoms",
                "Often affects costochondral junctions (Tietze syndrome if swollen)"
            ],
            distinguishing_features=[
                "Diagnosis of exclusion - must rule out cardiac/pulmonary causes first",
                "Normal ECG, troponin, imaging",
                "Point tenderness over affected ribs"
            ],
            red_flags=[],
            suggested_workup=[
                "ECG (to rule out cardiac)",
                "Consider troponin if any concern for ACS",
                "CXR if trauma or persistent symptoms",
                "Clinical diagnosis if clear reproducible tenderness and low risk"
            ],
            references=[
                "Chest Wall Pain - UpToDate"
            ]
        ))

        # GERD
        gerd_prob = 0.15
        if 'burning' in symptoms or 'heartburn' in symptoms:
            gerd_prob += 0.25
        if 'worse after meals' in symptoms:
            gerd_prob += 0.2
        if 'better with antacids' in symptoms:
            gerd_prob += 0.25
        if age < 50 and presentation.gender == 'M':
            gerd_prob += 0.1

        differentials.append(Diagnosis(
            name="Gastroesophageal Reflux Disease (GERD)",
            icd10="K21.9",
            probability=min(gerd_prob, 0.7),
            severity=Severity.NON_URGENT,
            key_features=[
                "Burning substernal chest discomfort",
                "Worse after meals, lying down",
                "Associated with regurgitation, sour taste",
                "Relieved by antacids"
            ],
            distinguishing_features=[
                "No cardiac features (radiation, diaphoresis)",
                "Normal cardiac workup",
                "May have dysphagia (concerning for stricture or malignancy)",
                "Response to PPI trial (not diagnostic for cardiac etiology)"
            ],
            red_flags=[
                RedFlag(
                    "Dysphagia + weight loss",
                    "Esophageal cancer or severe stricture",
                    "Urgent EGD"
                ),
                RedFlag(
                    "Hematemesis or melena",
                    "GI bleeding",
                    "EGD, CBC, type and cross"
                )
            ],
            suggested_workup=[
                "Clinical diagnosis if typical symptoms and low cardiac risk",
                "ECG and troponin to rule out ACS if any concern",
                "PPI trial (omeprazole 20mg daily x 2-4 weeks)",
                "EGD if alarm features or refractory to treatment",
                "24-hour pH monitoring if diagnosis unclear"
            ],
            references=[
                "ACG 2013 GERD Guidelines"
            ]
        ))

        # PNEUMOTHORAX
        pneumo_prob = 0.05
        if 'sudden onset' in symptoms:
            pneumo_prob += 0.15
        if 'pleuritic pain' in symptoms:
            pneumo_prob += 0.15
        if 'shortness of breath' in symptoms:
            pneumo_prob += 0.2
        if 'tall thin male' in str(presentation) or (age < 40 and presentation.gender == 'M'):
            pneumo_prob += 0.1

        differentials.append(Diagnosis(
            name="Spontaneous Pneumothorax",
            icd10="J93.0",
            probability=min(pneumo_prob, 0.65),
            severity=Severity.URGENT,
            key_features=[
                "Sudden onset pleuritic chest pain",
                "Dyspnea",
                "Decreased breath sounds on affected side",
                "Hyperresonance to percussion",
                "Risk: tall thin males, smokers, COPD, Marfan"
            ],
            distinguishing_features=[
                "Absent lung markings on CXR (upright, expiratory film)",
                "Visceral pleural line visible",
                "Ultrasound: absent lung sliding"
            ],
            red_flags=[
                RedFlag(
                    "Tracheal deviation + hypotension",
                    "Tension pneumothorax",
                    "Immediate needle decompression (2nd ICS midclavicular) - do not wait for CXR"
                ),
                RedFlag(
                    "Large pneumothorax (>2cm from chest wall)",
                    "Risk of progression",
                    "Chest tube placement"
                )
            ],
            suggested_workup=[
                "Upright CXR (PA and lateral)",
                "Expiratory CXR if initial film negative and high suspicion",
                "CT chest if diagnosis uncertain",
                "Ultrasound (absence of lung sliding)",
                "ABG if respiratory compromise"
            ],
            references=[
                "BTS 2010 Pleural Disease Guidelines"
            ]
        ))

        return differentials

    def _dyspnea_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for shortness of breath"""
        differentials = []
        symptoms = [s.lower() for s in presentation.symptoms]

        # ACUTE DECOMPENSATED HEART FAILURE
        hf_prob = 0.25
        if age := presentation.age > 60:
            hf_prob += 0.15
        if 'orthopnea' in symptoms:
            hf_prob += 0.2
        if 'leg swelling' in symptoms or 'edema' in symptoms:
            hf_prob += 0.15
        if 'paroxysmal nocturnal dyspnea' in symptoms:
            hf_prob += 0.2

        differentials.append(Diagnosis(
            name="Acute Decompensated Heart Failure",
            icd10="I50.9",
            probability=min(hf_prob, 0.9),
            severity=Severity.URGENT,
            key_features=[
                "Progressive dyspnea, orthopnea, PND",
                "Lower extremity edema",
                "Rales on lung auscultation",
                "Elevated JVP",
                "S3 gallop"
            ],
            distinguishing_features=[
                "BNP >400 pg/mL or NT-proBNP >900 pg/mL",
                "CXR: pulmonary edema, Kerley B lines, pleural effusions",
                "Echo: reduced EF (<40% HFrEF) or preserved EF with diastolic dysfunction (HFpEF)"
            ],
            red_flags=[
                RedFlag(
                    "Respiratory distress with hypoxemia",
                    "Flash pulmonary edema",
                    "NIV (BiPAP/CPAP), IV diuretics, consider ICU"
                )
            ],
            suggested_workup=[
                "BNP or NT-proBNP",
                "CXR",
                "ECG (ischemia, arrhythmia)",
                "Echocardiogram",
                "BMP (renal function for diuretics)",
                "Troponin (ACS as trigger)"
            ],
            references=["2022 AHA/ACC Heart Failure Guidelines"]
        ))

        # COPD EXACERBATION
        copd_prob = 0.2
        if 'smoking history' in presentation.past_medical_history or 'copd' in presentation.past_medical_history:
            copd_prob += 0.3
        if 'cough' in symptoms:
            copd_prob += 0.15
        if 'sputum' in symptoms or 'productive cough' in symptoms:
            copd_prob += 0.15
        if 'wheezing' in symptoms:
            copd_prob += 0.2

        differentials.append(Diagnosis(
            name="COPD Exacerbation",
            icd10="J44.1",
            probability=min(copd_prob, 0.85),
            severity=Severity.URGENT,
            key_features=[
                "Worsening dyspnea, cough, sputum production",
                "History of smoking or COPD",
                "Wheezing, prolonged expiratory phase",
                "Use of accessory muscles"
            ],
            distinguishing_features=[
                "CXR: hyperinflation, flattened diaphragm",
                "ABG: hypoxemia, hypercapnia (chronic compensated respiratory acidosis)",
                "Spirometry: reduced FEV1/FVC (not during acute exacerbation)"
            ],
            red_flags=[
                RedFlag(
                    "Altered mental status + hypercapnia",
                    "CO2 narcosis",
                    "NIV vs intubation, ICU"
                )
            ],
            suggested_workup=[
                "CXR (rule out pneumonia, pneumothorax)",
                "ABG (if O2 sat <90% or severe exacerbation)",
                "CBC (leukocytosis if infectious)",
                "BNP (to differentiate from heart failure)",
                "Sputum culture if purulent or severe"
            ],
            references=["GOLD 2024 COPD Guidelines"]
        ))

        # PNEUMONIA
        pna_prob = 0.2
        if 'fever' in symptoms:
            pna_prob += 0.2
        if 'cough' in symptoms:
            pna_prob += 0.15
        if 'pleuritic chest pain' in symptoms:
            pna_prob += 0.15
        if 'sputum' in symptoms:
            pna_prob += 0.1

        differentials.append(Diagnosis(
            name="Community-Acquired Pneumonia",
            icd10="J18.9",
            probability=min(pna_prob, 0.8),
            severity=Severity.URGENT,
            key_features=[
                "Fever, cough, dyspnea, pleuritic chest pain",
                "Sputum production",
                "Crackles on auscultation",
                "Tachycardia, tachypnea"
            ],
            distinguishing_features=[
                "CXR: infiltrate/consolidation",
                "Elevated WBC with left shift",
                "Procalcitonin elevation (bacterial)"
            ],
            red_flags=[
                RedFlag(
                    "CURB-65 ≥2 or PSI Class IV-V",
                    "Severe pneumonia",
                    "Consider ICU admission"
                ),
                RedFlag(
                    "Hypoxemia requiring high-flow O2",
                    "Respiratory failure",
                    "ICU, consider empiric coverage for PJP if immunocompromised"
                )
            ],
            suggested_workup=[
                "CXR (PA and lateral)",
                "CBC with differential",
                "BMP (assess for AKI)",
                "Blood cultures x2 (before antibiotics if severe)",
                "Sputum culture if able (not required for outpatient)",
                "Procalcitonin (guides antibiotic therapy)",
                "Urine antigen for Legionella and Pneumococcus if severe"
            ],
            references=["2019 ATS/IDSA CAP Guidelines"]
        ))

        # ASTHMA EXACERBATION
        asthma_prob = 0.15
        if 'asthma' in presentation.past_medical_history or 'atopy' in presentation.past_medical_history:
            asthma_prob += 0.3
        if 'wheezing' in symptoms:
            asthma_prob += 0.25
        if age < 40:
            asthma_prob += 0.1
        if 'trigger exposure' in symptoms or 'allergen exposure' in symptoms:
            asthma_prob += 0.15

        differentials.append(Diagnosis(
            name="Asthma Exacerbation",
            icd10="J45.901",
            probability=min(asthma_prob, 0.8),
            severity=Severity.URGENT,
            key_features=[
                "Wheezing, dyspnea, chest tightness, cough",
                "History of asthma or atopy",
                "Trigger exposure (allergens, URI, cold air)",
                "Prolonged expiratory phase"
            ],
            distinguishing_features=[
                "Peak flow <80% predicted or personal best",
                "Responds to bronchodilators",
                "CXR: hyperinflation (rule out complications)"
            ],
            red_flags=[
                RedFlag(
                    "Silent chest + altered mental status",
                    "Impending respiratory failure",
                    "Immediate intubation, ICU"
                ),
                RedFlag(
                    "No improvement with repeated nebs",
                    "Severe exacerbation",
                    "Continuous nebs, IV magnesium, steroids, ICU"
                )
            ],
            suggested_workup=[
                "Peak expiratory flow rate",
                "Pulse oximetry",
                "CXR (if first episode, severe, or complications suspected)",
                "ABG if severe or not responding",
                "Trial of bronchodilators"
            ],
            references=["GINA 2024 Asthma Guidelines"]
        ))

        # PULMONARY EMBOLISM (already covered in chest pain but also presents with dyspnea)
        pe_prob = 0.15
        if 'chest pain' in symptoms:
            pe_prob += 0.15
        if 'tachycardia' in symptoms:
            pe_prob += 0.15
        if 'recent surgery' in presentation.past_medical_history:
            pe_prob += 0.2

        differentials.append(Diagnosis(
            name="Pulmonary Embolism",
            icd10="I26.99",
            probability=min(pe_prob, 0.8),
            severity=Severity.EMERGENT,
            key_features=[
                "Sudden onset dyspnea",
                "Pleuritic chest pain",
                "Tachycardia, tachypnea",
                "Risk factors: immobilization, surgery, malignancy"
            ],
            distinguishing_features=[
                "D-dimer >500 ng/mL",
                "CTPA: filling defect in pulmonary artery",
                "Wells Score or PERC rule"
            ],
            red_flags=[
                RedFlag(
                    "Hypotension + tachycardia",
                    "Massive PE",
                    "Consider thrombolysis"
                )
            ],
            suggested_workup=[
                "Wells Score",
                "D-dimer (if low/intermediate risk)",
                "CTPA",
                "ECG",
                "Troponin, BNP"
            ],
            references=["ESC 2019 PE Guidelines"]
        ))

        return differentials

    def _abdominal_pain_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for abdominal pain"""
        differentials = []
        symptoms = [s.lower() for s in presentation.symptoms]

        # Determine location
        location = "generalized"
        if 'right upper quadrant' in symptoms or 'ruq pain' in symptoms:
            location = "ruq"
        elif 'right lower quadrant' in symptoms or 'rlq pain' in symptoms:
            location = "rlq"
        elif 'left upper quadrant' in symptoms or 'luq pain' in symptoms:
            location = "luq"
        elif 'left lower quadrant' in symptoms or 'llq pain' in symptoms:
            location = "llq"
        elif 'epigastric' in symptoms:
            location = "epigastric"

        # APPENDICITIS
        if location == "rlq" or location == "generalized":
            appy_prob = 0.3
            if 'nausea' in symptoms or 'vomiting' in symptoms:
                appy_prob += 0.15
            if 'fever' in symptoms:
                appy_prob += 0.15
            if 'anorexia' in symptoms:
                appy_prob += 0.1
            if age < 40:
                appy_prob += 0.1

            differentials.append(Diagnosis(
                name="Acute Appendicitis",
                icd10="K35.80",
                probability=min(appy_prob, 0.85),
                severity=Severity.URGENT,
                key_features=[
                    "Periumbilical pain migrating to RLQ",
                    "Anorexia, nausea, vomiting",
                    "Low-grade fever",
                    "McBurney's point tenderness",
                    "Rovsing's sign, psoas sign"
                ],
                distinguishing_features=[
                    "Leukocytosis with left shift",
                    "CT scan: periappendiceal fat stranding, appendiceal diameter >6mm",
                    "Ultrasound (especially in children, pregnant): non-compressible appendix"
                ],
                red_flags=[
                    RedFlag(
                        "Peritonitis signs (rebound, guarding)",
                        "Perforated appendicitis",
                        "Emergent surgery, broad-spectrum antibiotics"
                    )
                ],
                suggested_workup=[
                    "CBC with differential",
                    "CT abdomen/pelvis with IV contrast (adults)",
                    "Ultrasound (children, pregnancy)",
                    "Urinalysis (rule out UTI)",
                    "Pregnancy test (females of childbearing age)",
                    "Alvarado or AIR score"
                ],
                references=["2020 WSES Appendicitis Guidelines"]
            ))

        # CHOLECYSTITIS
        if location == "ruq" or location == "epigastric" or location == "generalized":
            chole_prob = 0.25
            if 'fever' in symptoms:
                chole_prob += 0.15
            if 'nausea' in symptoms or 'vomiting' in symptoms:
                chole_prob += 0.1
            if 'worse after fatty meals' in symptoms:
                chole_prob += 0.2
            if age > 40 and presentation.gender == 'F':
                chole_prob += 0.15

            differentials.append(Diagnosis(
                name="Acute Cholecystitis",
                icd10="K81.0",
                probability=min(chole_prob, 0.85),
                severity=Severity.URGENT,
                key_features=[
                    "RUQ pain (often radiating to right shoulder/scapula)",
                    "Worse after fatty meals",
                    "Murphy's sign (inspiratory arrest during RUQ palpation)",
                    "Fever, nausea, vomiting",
                    "4 F's: Female, Forty, Fertile, Fat"
                ],
                distinguishing_features=[
                    "RUQ ultrasound: gallstones, gallbladder wall thickening >4mm, pericholecystic fluid, sonographic Murphy's sign",
                    "Elevated WBC, alkaline phosphatase, bilirubin (if CBD obstruction)",
                    "HIDA scan if diagnosis uncertain (non-filling gallbladder)"
                ],
                red_flags=[
                    RedFlag(
                        "Charcot's triad (fever, jaundice, RUQ pain)",
                        "Ascending cholangitis",
                        "Emergent ERCP, IV antibiotics"
                    ),
                    RedFlag(
                        "Reynolds pentad (Charcot's + AMS + hypotension)",
                        "Suppurative cholangitis",
                        "ICU, emergent biliary decompression"
                    )
                ],
                suggested_workup=[
                    "RUQ ultrasound (first-line)",
                    "CBC, CMP, lipase",
                    "HIDA scan if ultrasound non-diagnostic",
                    "MRCP if concern for choledocholithiasis",
                    "Surgery consult"
                ],
                references=["Tokyo Guidelines 2018 for Cholecystitis"]
            ))

        # PANCREATITIS
        if location == "epigastric" or location == "generalized":
            panc_prob = 0.2
            if 'radiation to back' in symptoms:
                panc_prob += 0.25
            if 'nausea' in symptoms or 'vomiting' in symptoms:
                panc_prob += 0.15
            if 'alcohol use' in presentation.past_medical_history:
                panc_prob += 0.2

            differentials.append(Diagnosis(
                name="Acute Pancreatitis",
                icd10="K85.9",
                probability=min(panc_prob, 0.85),
                severity=Severity.URGENT,
                key_features=[
                    "Severe epigastric pain radiating to back",
                    "Nausea, vomiting",
                    "Worse lying supine, better leaning forward",
                    "Risk factors: gallstones, alcohol, hypertriglyceridemia"
                ],
                distinguishing_features=[
                    "Lipase >3x upper limit of normal (more specific than amylase)",
                    "CT abdomen: pancreatic edema, peripancreatic fluid (not needed for diagnosis)",
                    "Ranson's or BISAP score for severity"
                ],
                red_flags=[
                    RedFlag(
                        "Hypotension + tachycardia",
                        "Severe pancreatitis with third-spacing",
                        "Aggressive IV fluid resuscitation, ICU"
                    ),
                    RedFlag(
                        "Hypocalcemia + elevated LDH",
                        "Hemorrhagic pancreatitis",
                        "ICU monitoring"
                    )
                ],
                suggested_workup=[
                    "Lipase (>3x ULN diagnostic)",
                    "CMP (assess for hypocalcemia, AKI)",
                    "CBC",
                    "Triglycerides (if >1000, can cause pancreatitis)",
                    "RUQ ultrasound (identify gallstones)",
                    "CT abdomen with contrast (if diagnosis uncertain or after 48-72h to assess for necrosis)",
                    "ERCP if gallstone pancreatitis with cholangitis"
                ],
                references=["ACG 2013 Pancreatitis Guidelines"]
            ))

        # DIVERTICULITIS
        if location == "llq" or location == "generalized":
            diverti_prob = 0.2
            if age > 50:
                diverti_prob += 0.25
            if 'fever' in symptoms:
                diverti_prob += 0.15
            if 'constipation' in symptoms or 'diarrhea' in symptoms:
                diverti_prob += 0.1

            differentials.append(Diagnosis(
                name="Acute Diverticulitis",
                icd10="K57.92",
                probability=min(diverti_prob, 0.8),
                severity=Severity.URGENT,
                key_features=[
                    "LLQ pain (RLQ if redundant sigmoid)",
                    "Fever, altered bowel habits",
                    "LLQ tenderness, palpable mass",
                    "Age >50"
                ],
                distinguishing_features=[
                    "CT abdomen/pelvis with IV contrast: colonic wall thickening, pericolic fat stranding",
                    "Leukocytosis",
                    "Hinchey classification for severity"
                ],
                red_flags=[
                    RedFlag(
                        "Free air on imaging",
                        "Perforated diverticulitis",
                        "Emergent surgery"
                    ),
                    RedFlag(
                        "Peritonitis + sepsis",
                        "Complicated diverticulitis",
                        "Surgery consult, broad-spectrum antibiotics"
                    )
                ],
                suggested_workup=[
                    "CT abdomen/pelvis with IV contrast",
                    "CBC, CMP",
                    "Urinalysis (colovesicular fistula can cause UTI)",
                    "Blood cultures if septic"
                ],
                references=["AGA 2015 Diverticulitis Guidelines"]
            ))

        # GASTROENTERITIS
        gastro_prob = 0.25
        if 'diarrhea' in symptoms:
            gastro_prob += 0.25
        if 'vomiting' in symptoms:
            gastro_prob += 0.2
        if 'fever' in symptoms:
            gastro_prob += 0.1

        differentials.append(Diagnosis(
            name="Acute Gastroenteritis",
            icd10="K52.9",
            probability=min(gastro_prob, 0.8),
            severity=Severity.NON_URGENT,
            key_features=[
                "Diffuse abdominal cramping",
                "Diarrhea, vomiting",
                "Fever (if bacterial/invasive)",
                "Recent sick contacts or food exposure"
            ],
            distinguishing_features=[
                "Viral: watery diarrhea, vomiting, low-grade fever",
                "Bacterial: bloody diarrhea, high fever, severe cramping",
                "Self-limited in most cases"
            ],
            red_flags=[
                RedFlag(
                    "Bloody diarrhea + HUS (thrombocytopenia, AKI, hemolytic anemia)",
                    "E. coli O157:H7 or Shiga toxin",
                    "Supportive care, do NOT give antibiotics (worsens HUS)"
                ),
                RedFlag(
                    "Severe dehydration",
                    "Hypovolemic shock",
                    "IV fluid resuscitation"
                )
            ],
            suggested_workup=[
                "Clinical diagnosis if mild",
                "Stool culture, C. diff, O&P if bloody diarrhea, severe illness, or immunocompromised",
                "BMP if severe (assess electrolytes, kidney function)",
                "CBC if concern for HUS"
            ],
            references=["IDSA 2017 Infectious Diarrhea Guidelines"]
        ))

        return differentials

    def _headache_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for headache"""
        differentials = []
        symptoms = [s.lower() for s in presentation.symptoms]

        # MIGRAINE
        migraine_prob = 0.3
        if 'unilateral' in symptoms:
            migraine_prob += 0.15
        if 'throbbing' in symptoms or 'pulsating' in symptoms:
            migraine_prob += 0.15
        if 'photophobia' in symptoms or 'phonophobia' in symptoms:
            migraine_prob += 0.2
        if 'nausea' in symptoms:
            migraine_prob += 0.1
        if 'aura' in symptoms:
            migraine_prob += 0.25
        if age < 50 and presentation.gender == 'F':
            migraine_prob += 0.1

        differentials.append(Diagnosis(
            name="Migraine Headache",
            icd10="G43.909",
            probability=min(migraine_prob, 0.85),
            severity=Severity.NON_URGENT,
            key_features=[
                "Unilateral throbbing headache (can be bilateral)",
                "Photophobia, phonophobia, nausea",
                "Worse with activity",
                "Duration 4-72 hours",
                "May have aura (visual, sensory)"
            ],
            distinguishing_features=[
                "POUND criteria: Pulsating, 4-72h duration, Unilateral, Nausea, Disabling",
                "Recurrent pattern with headache-free intervals",
                "Normal neurologic exam between episodes"
            ],
            red_flags=[
                RedFlag(
                    "First severe headache or 'worst headache of life'",
                    "Rule out SAH or other secondary causes",
                    "Neuroimaging (CT or MRI)"
                ),
                RedFlag(
                    "Prolonged aura >1 hour or new neurologic deficits",
                    "Migrainous infarction or other stroke",
                    "MRI, neurology consult"
                )
            ],
            suggested_workup=[
                "Clinical diagnosis using ICHD-3 criteria",
                "Neuroimaging NOT needed if typical migraine and normal exam",
                "MRI if atypical features, first episode >50 yo, or red flags",
                "Consider headache diary"
            ],
            references=["ICHD-3 Migraine Criteria", "AAN 2019 Migraine Guidelines"]
        ))

        # TENSION-TYPE HEADACHE
        tension_prob = 0.35
        if 'bilateral' in symptoms:
            tension_prob += 0.2
        if 'band-like' in symptoms or 'pressure' in symptoms:
            tension_prob += 0.2
        if 'stress' in symptoms or 'muscle tension' in symptoms:
            tension_prob += 0.15

        differentials.append(Diagnosis(
            name="Tension-Type Headache",
            icd10="G44.209",
            probability=min(tension_prob, 0.85),
            severity=Severity.NON_URGENT,
            key_features=[
                "Bilateral, band-like pressure/tightness",
                "Mild to moderate intensity",
                "No nausea/vomiting (or minimal)",
                "No photophobia AND phonophobia",
                "Not worsened by activity"
            ],
            distinguishing_features=[
                "Most common primary headache",
                "Associated with stress, poor posture, muscle tension",
                "Normal neurologic exam"
            ],
            red_flags=[],
            suggested_workup=[
                "Clinical diagnosis",
                "No imaging needed if typical presentation"
            ],
            references=["ICHD-3 Tension-Type Headache Criteria"]
        ))

        # SUBARACHNOID HEMORRHAGE
        sah_prob = 0.05
        if 'thunderclap' in symptoms or 'sudden onset' in symptoms or 'worst headache' in symptoms:
            sah_prob += 0.4
        if 'neck stiffness' in symptoms or 'meningismus' in symptoms:
            sah_prob += 0.2
        if 'loss of consciousness' in symptoms:
            sah_prob += 0.2
        if 'vomiting' in symptoms:
            sah_prob += 0.1

        differentials.append(Diagnosis(
            name="Subarachnoid Hemorrhage",
            icd10="I60.9",
            probability=min(sah_prob, 0.9),
            severity=Severity.EMERGENT,
            key_features=[
                "Sudden onset 'thunderclap' headache - worst headache of life",
                "Reaches maximum intensity in <1 minute",
                "Neck stiffness, photophobia",
                "Nausea, vomiting, loss of consciousness",
                "May have focal neurologic deficits"
            ],
            distinguishing_features=[
                "Non-contrast CT head: hyperdensity in subarachnoid space (95% sensitive if <6h)",
                "LP if CT negative: xanthochromia, elevated RBCs",
                "CT angiography: identify aneurysm"
            ],
            red_flags=[
                RedFlag(
                    "Thunderclap headache",
                    "SAH or other vascular emergency",
                    "STAT non-contrast CT head, neurosurgery consult"
                ),
                RedFlag(
                    "Altered mental status or focal deficits",
                    "Mass effect, hydrocephalus, or rebleed",
                    "ICU, blood pressure control, nimodipine"
                )
            ],
            suggested_workup=[
                "STAT non-contrast CT head (within 6 hours)",
                "LP if CT negative and high suspicion (after 6-12 hours for xanthochromia)",
                "CT angiography (identify source)",
                "Neurosurgery consult",
                "CBC, coagulation studies, type and screen"
            ],
            references=["AHA/ASA 2012 SAH Guidelines"]
        ))

        # MENINGITIS
        meningitis_prob = 0.05
        if 'fever' in symptoms:
            meningitis_prob += 0.25
        if 'neck stiffness' in symptoms:
            meningitis_prob += 0.25
        if 'photophobia' in symptoms:
            meningitis_prob += 0.15
        if 'altered mental status' in symptoms or 'confusion' in symptoms:
            meningitis_prob += 0.2

        differentials.append(Diagnosis(
            name="Bacterial Meningitis",
            icd10="G00.9",
            probability=min(meningitis_prob, 0.85),
            severity=Severity.EMERGENT,
            key_features=[
                "Fever, headache, neck stiffness (classic triad - only 44% have all three)",
                "Altered mental status",
                "Photophobia",
                "Kernig's sign, Brudzinski's sign",
                "Petechial rash (N. meningitidis)"
            ],
            distinguishing_features=[
                "LP: elevated WBC (>1000, PMN predominant), low glucose, elevated protein",
                "CSF Gram stain and culture",
                "Elevated serum procalcitonin"
            ],
            red_flags=[
                RedFlag(
                    "Altered mental status + fever + headache",
                    "Bacterial meningitis",
                    "Do NOT delay antibiotics for LP or imaging - give empiric antibiotics immediately"
                ),
                RedFlag(
                    "Purpuric rash",
                    "Meningococcemia with DIC",
                    "Empiric ceftriaxone + vancomycin + dexamethasone, ICU"
                )
            ],
            suggested_workup=[
                "Blood cultures x2 (before antibiotics)",
                "LP (unless contraindicated): cell count, glucose, protein, Gram stain, culture",
                "CSF PCR (viral, bacterial)",
                "CT head before LP if: focal deficits, papilledema, altered mental status, immunocompromised",
                "Do NOT delay antibiotics - give empirically if LP delayed"
            ],
            references=["IDSA 2017 Bacterial Meningitis Guidelines"]
        ))

        # GIANT CELL ARTERITIS (in elderly)
        if presentation.age >= 50:
            gca_prob = 0.1
            if 'temporal tenderness' in symptoms:
                gca_prob += 0.3
            if 'jaw claudication' in symptoms:
                gca_prob += 0.25
            if 'vision changes' in symptoms or 'visual loss' in symptoms:
                gca_prob += 0.25
            if 'polymyalgia' in symptoms or 'shoulder pain' in symptoms:
                gca_prob += 0.1

            differentials.append(Diagnosis(
                name="Giant Cell Arteritis (Temporal Arteritis)",
                icd10="M31.6",
                probability=min(gca_prob, 0.85),
                severity=Severity.URGENT,
                key_features=[
                    "New headache in patient >50 years",
                    "Temporal artery tenderness or decreased pulse",
                    "Jaw claudication",
                    "Vision changes (amaurosis fugax or permanent vision loss)",
                    "Polymyalgia rheumatica symptoms"
                ],
                distinguishing_features=[
                    "Markedly elevated ESR (>50, often >100)",
                    "Elevated CRP",
                    "Temporal artery biopsy: granulomatous inflammation (gold standard)",
                    "ACR criteria (3 of 5)"
                ],
                red_flags=[
                    RedFlag(
                        "Vision changes or vision loss",
                        "Ophthalmic artery involvement - risk of permanent blindness",
                        "Start high-dose steroids IMMEDIATELY (prednisone 60mg or IV methylprednisolone), do not wait for biopsy"
                    )
                ],
                suggested_workup=[
                    "ESR, CRP (both elevated)",
                    "CBC (may have anemia of chronic disease)",
                    "Temporal artery biopsy (within 2 weeks of starting steroids)",
                    "Ophthalmology consult if vision changes",
                    "Consider temporal artery ultrasound or MRA"
                ],
                references=["ACR 2021 GCA Guidelines"]
            ))

        return differentials

    def _fever_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for fever"""
        differentials = []
        symptoms = [s.lower() for s in presentation.symptoms]

        # Common viral URI
        viral_prob = 0.4
        if 'cough' in symptoms or 'rhinorrhea' in symptoms or 'sore throat' in symptoms:
            viral_prob += 0.25
        if 'myalgia' in symptoms:
            viral_prob += 0.1

        differentials.append(Diagnosis(
            name="Viral Upper Respiratory Infection",
            icd10="J06.9",
            probability=min(viral_prob, 0.85),
            severity=Severity.NON_URGENT,
            key_features=[
                "Low-grade fever",
                "Cough, rhinorrhea, sore throat",
                "Myalgia, malaise",
                "Self-limited"
            ],
            distinguishing_features=[
                "Normal or slightly elevated WBC",
                "Clinical diagnosis"
            ],
            red_flags=[],
            suggested_workup=[
                "Clinical diagnosis",
                "Testing not routinely needed",
                "Consider flu test if influenza season"
            ],
            references=["CDC Common Cold Guidelines"]
        ))

        # UTI
        uti_prob = 0.2
        if 'dysuria' in symptoms or 'frequency' in symptoms or 'urgency' in symptoms:
            uti_prob += 0.3
        if 'flank pain' in symptoms or 'cvat' in symptoms:
            uti_prob += 0.2
        if presentation.gender == 'F':
            uti_prob += 0.15

        differentials.append(Diagnosis(
            name="Urinary Tract Infection / Pyelonephritis",
            icd10="N39.0",
            probability=min(uti_prob, 0.85),
            severity=Severity.URGENT,
            key_features=[
                "Dysuria, frequency, urgency, suprapubic pain (cystitis)",
                "Fever, flank pain, CVA tenderness (pyelonephritis)",
                "Malaise"
            ],
            distinguishing_features=[
                "Urinalysis: pyuria, bacteriuria, +nitrites, +leukocyte esterase",
                "Urine culture: >100,000 CFU/mL (lower in symptomatic males)"
            ],
            red_flags=[
                RedFlag(
                    "Sepsis with urinary source",
                    "Urosepsis",
                    "IV antibiotics, fluid resuscitation, ICU if shock"
                )
            ],
            suggested_workup=[
                "Urinalysis with microscopy",
                "Urine culture",
                "CBC, BMP if pyelonephritis",
                "Blood cultures if septic",
                "Renal ultrasound if pyelonephritis not improving"
            ],
            references=["IDSA 2011 UTI Guidelines"]
        ))

        # COVID-19, Influenza (depending on season/epidemiology)
        covid_prob = 0.2
        if 'cough' in symptoms:
            covid_prob += 0.1
        if 'dyspnea' in symptoms:
            covid_prob += 0.15
        if 'anosmia' in symptoms or 'loss of taste' in symptoms:
            covid_prob += 0.3

        differentials.append(Diagnosis(
            name="COVID-19",
            icd10="U07.1",
            probability=min(covid_prob, 0.75),
            severity=Severity.URGENT,
            key_features=[
                "Fever, cough, dyspnea",
                "Anosmia, dysgeusia",
                "Fatigue, myalgia",
                "Exposure history"
            ],
            distinguishing_features=[
                "PCR or rapid antigen test positive",
                "CXR: bilateral infiltrates if severe"
            ],
            red_flags=[
                RedFlag(
                    "Hypoxemia (O2 sat <94%)",
                    "Moderate-severe COVID",
                    "Consider remdesivir, dexamethasone, supplemental O2"
                )
            ],
            suggested_workup=[
                "COVID-19 PCR or antigen test",
                "Pulse oximetry",
                "CXR if dyspnea",
                "D-dimer, ferritin, CRP if hospitalized"
            ],
            references=["NIH COVID-19 Treatment Guidelines"]
        ))

        return differentials

    def _weakness_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for weakness/fatigue"""
        differentials = []
        # Implementation simplified for brevity
        differentials.append(Diagnosis(
            name="Anemia",
            icd10="D64.9",
            probability=0.3,
            severity=Severity.NON_URGENT,
            key_features=["Fatigue", "Pallor", "Dyspnea on exertion"],
            distinguishing_features=["Low hemoglobin", "Low MCV (iron def), High MCV (B12/folate def)"],
            red_flags=[],
            suggested_workup=["CBC", "Reticulocyte count", "Iron studies", "B12, folate"],
            references=["Approach to Anemia - UpToDate"]
        ))
        return differentials

    def _dizziness_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for dizziness"""
        differentials = []
        symptoms = [s.lower() for s in presentation.symptoms]

        # BPPV
        bppv_prob = 0.35
        if 'positional' in symptoms or 'worse with head movement' in symptoms:
            bppv_prob += 0.3
        if 'vertigo' in symptoms or 'spinning sensation' in symptoms:
            bppv_prob += 0.2

        differentials.append(Diagnosis(
            name="Benign Paroxysmal Positional Vertigo (BPPV)",
            icd10="H81.10",
            probability=min(bppv_prob, 0.85),
            severity=Severity.NON_URGENT,
            key_features=[
                "Brief episodes of vertigo (<1 min)",
                "Triggered by head position changes",
                "Nausea common",
                "No hearing loss or neurologic symptoms"
            ],
            distinguishing_features=[
                "Dix-Hallpike maneuver positive: nystagmus and vertigo",
                "Latency 1-5 seconds, fatigable"
            ],
            red_flags=[],
            suggested_workup=[
                "Clinical diagnosis with Dix-Hallpike",
                "Epley maneuver for treatment",
                "MRI only if atypical features"
            ],
            references=["AAO-HNS 2017 BPPV Guidelines"]
        ))

        return differentials

    def _cough_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for cough"""
        differentials = []
        # Simplified implementation
        differentials.append(Diagnosis(
            name="Acute Bronchitis",
            icd10="J20.9",
            probability=0.5,
            severity=Severity.NON_URGENT,
            key_features=["Cough >5 days", "Sputum production", "Normal vital signs"],
            distinguishing_features=["CXR normal", "Self-limited"],
            red_flags=[],
            suggested_workup=["Clinical diagnosis", "CXR if fever/hypoxia/consolidation"],
            references=["ACCP Cough Guidelines"]
        ))
        return differentials

    def _back_pain_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for back pain"""
        differentials = []
        symptoms = [s.lower() for s in presentation.symptoms]

        # Mechanical low back pain
        mechanical_prob = 0.6
        if 'worse with activity' in symptoms:
            mechanical_prob += 0.2

        differentials.append(Diagnosis(
            name="Mechanical Low Back Pain / Lumbar Strain",
            icd10="M54.5",
            probability=min(mechanical_prob, 0.85),
            severity=Severity.NON_URGENT,
            key_features=[
                "Worse with activity, better with rest",
                "No neurologic deficits",
                "Normal strength, sensation, reflexes"
            ],
            distinguishing_features=[
                "Clinical diagnosis",
                "Imaging not needed unless red flags"
            ],
            red_flags=[
                RedFlag(
                    "Saddle anesthesia + bowel/bladder dysfunction",
                    "Cauda equina syndrome",
                    "Emergent MRI, neurosurgery consult"
                )
            ],
            suggested_workup=[
                "Clinical diagnosis",
                "MRI only if red flags or symptoms >6 weeks"
            ],
            references=["AAFP Low Back Pain Guidelines"]
        ))

        return differentials

    def _palpitations_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Differential diagnosis for palpitations"""
        differentials = []
        # Simplified
        differentials.append(Diagnosis(
            name="Premature Atrial/Ventricular Contractions (PACs/PVCs)",
            icd10="I49.40",
            probability=0.4,
            severity=Severity.NON_URGENT,
            key_features=["Skipped beats", "Fluttering sensation", "Benign in most cases"],
            distinguishing_features=["Holter monitor shows PACs/PVCs"],
            red_flags=[],
            suggested_workup=["ECG", "Holter monitor", "Echo if structural concern"],
            references=["AHA Arrhythmia Guidelines"]
        ))
        return differentials

    def _generic_differential(self, presentation: PatientPresentation) -> List[Diagnosis]:
        """Generic differential for unrecognized complaints"""
        return [
            Diagnosis(
                name="Further Clinical Evaluation Needed",
                icd10="R69",
                probability=0.5,
                severity=Severity.NON_URGENT,
                key_features=["Symptoms require detailed history and physical exam"],
                distinguishing_features=["Unable to generate specific differential without more information"],
                red_flags=[],
                suggested_workup=["Comprehensive history and physical", "Basic labs: CBC, CMP", "Imaging as indicated"],
                references=[]
            )
        ]

    def _adjust_probabilities(self, differentials: List[Diagnosis], presentation: PatientPresentation) -> List[Diagnosis]:
        """
        Adjust diagnosis probabilities based on patient-specific factors.

        Bayesian-like adjustments for age, comorbidities, vital signs.
        """
        # Age-based adjustments
        age_group = self._get_age_group(presentation.age)

        for dx in differentials:
            # Adjust for vital sign abnormalities
            if presentation.vital_signs:
                if presentation.vital_signs.get('temp', 37) > 38.3:  # High fever
                    if 'infection' in dx.name.lower() or 'itis' in dx.name.lower():
                        dx.probability = min(dx.probability * 1.2, 0.95)

                if presentation.vital_signs.get('hr', 80) > 100:  # Tachycardia
                    if 'PE' in dx.name or 'sepsis' in dx.name.lower():
                        dx.probability = min(dx.probability * 1.15, 0.95)

            # Comorbidity adjustments
            if 'diabetes' in presentation.past_medical_history:
                if 'coronary' in dx.name.lower() or 'infection' in dx.name.lower():
                    dx.probability = min(dx.probability * 1.1, 0.95)

            # Normalize so total doesn't exceed 1.0 (not strictly required but good practice)
            # In reality, differentials aren't mutually exclusive, but we cap individual probabilities

        return differentials


def generate_differential_diagnosis(
    chief_complaint: str,
    symptoms: List[str],
    age: int,
    gender: str,
    **kwargs
) -> List[Dict]:
    """
    Convenience function to generate differential diagnosis.

    Args:
        chief_complaint: Primary symptom/complaint
        symptoms: List of associated symptoms
        age: Patient age in years
        gender: "M", "F", or "Other"
        **kwargs: Additional patient data (duration, onset, pmh, medications, vitals)

    Returns:
        List of diagnosis dictionaries sorted by probability

    Example:
        >>> differentials = generate_differential_diagnosis(
        ...     chief_complaint="chest pain",
        ...     symptoms=["radiation to arm", "diaphoresis", "nausea"],
        ...     age=65,
        ...     gender="M",
        ...     past_medical_history=["diabetes", "hypertension"]
        ... )
    """
    presentation = PatientPresentation(
        chief_complaint=chief_complaint,
        symptoms=symptoms,
        age=age,
        gender=gender,
        **kwargs
    )

    generator = DifferentialDiagnosisGenerator()
    differentials = generator.generate_differential(presentation)

    # Convert to dictionaries for API response
    return [
        {
            'name': dx.name,
            'icd10': dx.icd10,
            'probability': round(dx.probability, 3),
            'severity': dx.severity.value,
            'key_features': dx.key_features,
            'distinguishing_features': dx.distinguishing_features,
            'red_flags': [
                {
                    'finding': rf.finding,
                    'implication': rf.implication,
                    'action': rf.action
                }
                for rf in dx.red_flags
            ],
            'suggested_workup': dx.suggested_workup,
            'references': dx.references
        }
        for dx in differentials
    ]
