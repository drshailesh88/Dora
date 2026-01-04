"""Specialty detection from query patterns."""

import re
from collections import Counter
from typing import Optional

from src.personalization.models import (
    MedicalSpecialty,
    QueryHistory,
    SpecialtyConfidence,
)


# Specialty-specific keywords (curated medical terms)
SPECIALTY_KEYWORDS = {
    MedicalSpecialty.CARDIOLOGY: [
        "ecg", "echo", "cardiac", "heart", "arrhythmia", "angina", "infarction",
        "stemi", "nstemi", "coronary", "valvular", "pericardial", "endocarditis",
        "tachycardia", "bradycardia", "atrial fibrillation", "af", "heart failure",
        "hf", "ejection fraction", "ef", "myocardial", "troponin", "bnp", "cad",
        "acs", "pci", "cabg", "angiography", "valve", "aortic stenosis",
    ],
    MedicalSpecialty.PULMONOLOGY: [
        "pulmonary", "lung", "respiratory", "copd", "asthma", "pneumonia",
        "bronchitis", "pleural", "pneumothorax", "tuberculosis", "tb",
        "interstitial lung", "ild", "pft", "spirometry", "fev1", "fvc",
        "spo2", "hypoxia", "dyspnea", "wheezing", "cough", "hemoptysis",
        "bronchiectasis", "emphysema", "sleep apnea", "osa",
    ],
    MedicalSpecialty.NEPHROLOGY: [
        "renal", "kidney", "creatinine", "gfr", "dialysis", "hemodialysis",
        "peritoneal dialysis", "aki", "ckd", "nephrotic", "nephritic",
        "proteinuria", "hematuria", "uremia", "electrolyte", "hyperkalemia",
        "hyponatremia", "acid-base", "metabolic acidosis", "urine", "bun",
        "transplant", "glomerular", "glomerulonephritis",
    ],
    MedicalSpecialty.GASTROENTEROLOGY: [
        "gastric", "intestinal", "liver", "hepatic", "gi", "gerd", "ibs",
        "ibd", "crohn", "ulcerative colitis", "cirrhosis", "hepatitis",
        "pancreatitis", "cholecystitis", "ascites", "endoscopy", "colonoscopy",
        "dyspepsia", "diarrhea", "constipation", "melena", "hematemesis",
        "jaundice", "bilirubin", "alt", "ast", "portal hypertension",
        "esophageal varices", "celiac", "malabsorption",
    ],
    MedicalSpecialty.ENDOCRINOLOGY: [
        "diabetes", "thyroid", "hormone", "endocrine", "hba1c", "glucose",
        "insulin", "hypoglycemia", "hyperglycemia", "dka", "hhs",
        "hypothyroid", "hyperthyroid", "graves", "hashimoto", "tsh", "t4",
        "t3", "adrenal", "cushing", "addison", "pituitary", "acromegaly",
        "osteoporosis", "calcium", "parathyroid", "pth", "vitamin d",
        "obesity", "metabolic syndrome", "lipid", "cholesterol",
    ],
    MedicalSpecialty.NEUROLOGY: [
        "neurological", "brain", "stroke", "seizure", "epilepsy", "headache",
        "migraine", "parkinson", "alzheimer", "dementia", "neuropathy",
        "guillain-barre", "myasthenia", "multiple sclerosis", "ms",
        "encephalitis", "meningitis", "csf", "eeg", "mri brain", "ct brain",
        "tremor", "ataxia", "weakness", "paralysis", "tia", "cerebrovascular",
        "intracranial", "hemorrhage", "ischemic",
    ],
    MedicalSpecialty.PSYCHIATRY: [
        "psychiatric", "depression", "anxiety", "bipolar", "schizophrenia",
        "psychosis", "mania", "ocd", "ptsd", "adhd", "autism", "mental health",
        "suicidal", "antidepressant", "ssri", "snri", "antipsychotic",
        "mood disorder", "personality disorder", "substance abuse",
        "addiction", "withdrawal", "cognitive", "behavioral therapy",
        "psychotherapy",
    ],
    MedicalSpecialty.PEDIATRICS: [
        "pediatric", "child", "infant", "newborn", "neonatal", "congenital",
        "vaccination", "immunization", "growth", "developmental", "jaundice",
        "bilirubin", "feeding", "breastfeeding", "formula", "apgar",
        "milestone", "autism", "adhd", "asthma", "rsv", "croup",
        "kawasaki", "febrile seizure", "necrotizing enterocolitis",
    ],
    MedicalSpecialty.OBSTETRICS_GYNECOLOGY: [
        "pregnancy", "pregnant", "obstetric", "gynecologic", "menstrual",
        "menopause", "prenatal", "antenatal", "postpartum", "delivery",
        "cesarean", "c-section", "preeclampsia", "eclampsia", "gestational",
        "trimester", "fetal", "ultrasound", "amniocentesis", "pcos",
        "endometriosis", "fibroid", "ovarian", "uterine", "cervical",
        "contraception", "hcg", "abortion", "miscarriage",
    ],
    MedicalSpecialty.SURGERY_GENERAL: [
        "surgical", "operation", "laparoscopic", "appendectomy", "hernia",
        "cholecystectomy", "bowel obstruction", "perforation", "peritonitis",
        "abscess", "trauma", "wound", "suture", "anastomosis", "resection",
        "exploratory", "laparotomy", "abdominal", "postoperative",
    ],
    MedicalSpecialty.ORTHOPEDICS: [
        "fracture", "bone", "joint", "orthopedic", "arthritis", "osteoarthritis",
        "rheumatoid arthritis", "spine", "vertebral", "disc", "meniscus",
        "ligament", "acl", "pcl", "mcl", "tendon", "rotator cuff",
        "dislocation", "sprain", "strain", "x-ray", "mri spine", "hip",
        "knee", "shoulder", "ankle", "prosthesis", "replacement",
    ],
    MedicalSpecialty.DERMATOLOGY: [
        "skin", "rash", "dermatitis", "eczema", "psoriasis", "acne",
        "melanoma", "basal cell", "squamous cell", "lesion", "mole",
        "urticaria", "hives", "pruritus", "itching", "biopsy skin",
        "cellulitis", "abscess", "fungal", "dermatophyte", "vitiligo",
        "alopecia", "hair loss", "nail",
    ],
    MedicalSpecialty.OPHTHALMOLOGY: [
        "eye", "vision", "ocular", "retinal", "glaucoma", "cataract",
        "conjunctivitis", "uveitis", "macular", "optic nerve", "visual",
        "blindness", "diplopia", "fundus", "intraocular", "iop",
        "retinopathy", "diabetic retinopathy",
    ],
    MedicalSpecialty.ENT: [
        "ear", "nose", "throat", "ent", "otitis", "sinusitis", "rhinitis",
        "tonsillitis", "pharyngitis", "laryngitis", "vertigo", "tinnitus",
        "hearing loss", "deafness", "nasal", "epistaxis", "deviated septum",
        "vocal cord", "hoarseness",
    ],
    MedicalSpecialty.EMERGENCY_MEDICINE: [
        "emergency", "trauma", "resuscitation", "cpr", "acls", "atls",
        "shock", "sepsis", "anaphylaxis", "acute", "critical", "unstable",
        "code blue", "cardiac arrest", "respiratory arrest", "intubation",
        "airway", "triage", "er", "ed",
    ],
    MedicalSpecialty.CRITICAL_CARE: [
        "icu", "intensive care", "ventilator", "mechanical ventilation",
        "septic shock", "mods", "ards", "vasopressor", "norepinephrine",
        "dobutamine", "sedation", "paralytic", "central line", "arterial line",
        "abg", "lactate", "sofa score", "apache",
    ],
    MedicalSpecialty.ONCOLOGY: [
        "cancer", "oncology", "tumor", "malignancy", "metastasis", "chemotherapy",
        "radiation", "biopsy", "stage", "lymphoma", "leukemia", "carcinoma",
        "sarcoma", "neoplasm", "cea", "ca 125", "psa", "immunotherapy",
        "targeted therapy",
    ],
    MedicalSpecialty.INFECTIOUS_DISEASE: [
        "infection", "infectious", "sepsis", "fever", "antibiotic", "bacterial",
        "viral", "fungal", "hiv", "aids", "tuberculosis", "malaria",
        "dengue", "covid", "coronavirus", "culture", "sensitivity",
        "mrsa", "vre", "c diff", "procalcitonin",
    ],
    MedicalSpecialty.RHEUMATOLOGY: [
        "rheumatoid", "arthritis", "sle", "lupus", "sjogren", "scleroderma",
        "vasculitis", "gout", "pseudogout", "ana", "rf", "anti-ccp",
        "inflammatory", "autoimmune", "connective tissue", "arthralgia",
        "myalgia", "dmard", "methotrexate", "biologics",
    ],
    MedicalSpecialty.HEMATOLOGY: [
        "hematology", "blood", "anemia", "hemoglobin", "wbc", "platelet",
        "coagulation", "inr", "pt", "ptt", "bleeding", "thrombosis",
        "dvt", "pe", "anticoagulation", "warfarin", "heparin", "iron",
        "b12", "folate", "transfusion", "hemolysis",
    ],
    MedicalSpecialty.INTERNAL_MEDICINE: [
        "internal medicine", "general medicine", "hypertension", "hyperlipidemia",
        "preventive", "screening", "chronic disease", "comorbidity",
        "polypharmacy", "geriatric", "multisystem",
    ],
    MedicalSpecialty.FAMILY_MEDICINE: [
        "family medicine", "primary care", "preventive", "wellness",
        "health maintenance", "screening", "vaccination", "chronic care",
        "outpatient",
    ],
}


# Drug class to specialty mapping
DRUG_SPECIALTY_MAP = {
    # Cardiology drugs
    "beta blocker": MedicalSpecialty.CARDIOLOGY,
    "ace inhibitor": MedicalSpecialty.CARDIOLOGY,
    "arb": MedicalSpecialty.CARDIOLOGY,
    "calcium channel blocker": MedicalSpecialty.CARDIOLOGY,
    "diuretic": MedicalSpecialty.CARDIOLOGY,
    "antiplatelet": MedicalSpecialty.CARDIOLOGY,
    "anticoagulant": MedicalSpecialty.CARDIOLOGY,
    "statin": MedicalSpecialty.CARDIOLOGY,
    "nitrate": MedicalSpecialty.CARDIOLOGY,
    "digoxin": MedicalSpecialty.CARDIOLOGY,
    "amiodarone": MedicalSpecialty.CARDIOLOGY,

    # Pulmonology drugs
    "bronchodilator": MedicalSpecialty.PULMONOLOGY,
    "inhaled corticosteroid": MedicalSpecialty.PULMONOLOGY,
    "laba": MedicalSpecialty.PULMONOLOGY,
    "lama": MedicalSpecialty.PULMONOLOGY,
    "theophylline": MedicalSpecialty.PULMONOLOGY,

    # Endocrinology drugs
    "insulin": MedicalSpecialty.ENDOCRINOLOGY,
    "metformin": MedicalSpecialty.ENDOCRINOLOGY,
    "sulfonylurea": MedicalSpecialty.ENDOCRINOLOGY,
    "dpp4 inhibitor": MedicalSpecialty.ENDOCRINOLOGY,
    "sglt2 inhibitor": MedicalSpecialty.ENDOCRINOLOGY,
    "glp1 agonist": MedicalSpecialty.ENDOCRINOLOGY,
    "levothyroxine": MedicalSpecialty.ENDOCRINOLOGY,
    "methimazole": MedicalSpecialty.ENDOCRINOLOGY,

    # Psychiatry drugs
    "ssri": MedicalSpecialty.PSYCHIATRY,
    "snri": MedicalSpecialty.PSYCHIATRY,
    "antipsychotic": MedicalSpecialty.PSYCHIATRY,
    "mood stabilizer": MedicalSpecialty.PSYCHIATRY,
    "benzodiazepine": MedicalSpecialty.PSYCHIATRY,
    "antidepressant": MedicalSpecialty.PSYCHIATRY,

    # Neurology drugs
    "antiepileptic": MedicalSpecialty.NEUROLOGY,
    "anticonvulsant": MedicalSpecialty.NEUROLOGY,
    "levodopa": MedicalSpecialty.NEUROLOGY,
    "dopamine agonist": MedicalSpecialty.NEUROLOGY,
    "anticholinergic": MedicalSpecialty.NEUROLOGY,

    # Rheumatology drugs
    "dmard": MedicalSpecialty.RHEUMATOLOGY,
    "biologic": MedicalSpecialty.RHEUMATOLOGY,
    "methotrexate": MedicalSpecialty.RHEUMATOLOGY,
    "hydroxychloroquine": MedicalSpecialty.RHEUMATOLOGY,
}


# ICD-10 code prefix to specialty mapping (simplified)
ICD_SPECIALTY_MAP = {
    "I": MedicalSpecialty.CARDIOLOGY,  # Circulatory
    "J": MedicalSpecialty.PULMONOLOGY,  # Respiratory
    "N": MedicalSpecialty.NEPHROLOGY,  # Genitourinary (kidney)
    "K": MedicalSpecialty.GASTROENTEROLOGY,  # Digestive
    "E": MedicalSpecialty.ENDOCRINOLOGY,  # Endocrine
    "G": MedicalSpecialty.NEUROLOGY,  # Nervous system
    "F": MedicalSpecialty.PSYCHIATRY,  # Mental disorders
    "M": MedicalSpecialty.RHEUMATOLOGY,  # Musculoskeletal
    "L": MedicalSpecialty.DERMATOLOGY,  # Skin
    "O": MedicalSpecialty.OBSTETRICS_GYNECOLOGY,  # Pregnancy
    "P": MedicalSpecialty.PEDIATRICS,  # Perinatal
    "S": MedicalSpecialty.SURGERY_GENERAL,  # Injury
    "T": MedicalSpecialty.SURGERY_GENERAL,  # External causes
}


class SpecialtyDetector:
    """Detects medical specialty from query patterns."""

    def __init__(self):
        """Initialize the detector."""
        self.specialty_keywords = SPECIALTY_KEYWORDS
        self.drug_map = DRUG_SPECIALTY_MAP
        self.icd_map = ICD_SPECIALTY_MAP

    def detect_from_query(self, query: str) -> Optional[tuple[MedicalSpecialty, float]]:
        """
        Detect specialty from a single query.

        Args:
            query: Medical query text.

        Returns:
            Tuple of (specialty, confidence) or None if no clear match.
        """
        query_lower = query.lower()

        # Score each specialty
        specialty_scores: dict[MedicalSpecialty, float] = {}

        for specialty, keywords in self.specialty_keywords.items():
            score = 0.0
            matches = 0

            for keyword in keywords:
                if keyword in query_lower:
                    # Weight longer keywords more heavily
                    weight = len(keyword.split())
                    score += weight
                    matches += 1

            if matches > 0:
                # Normalize by total keywords for this specialty
                specialty_scores[specialty] = score / len(keywords)

        if not specialty_scores:
            return None

        # Get top specialty
        top_specialty = max(specialty_scores.items(), key=lambda x: x[1])

        # Only return if confidence is reasonable
        if top_specialty[1] > 0.05:  # At least 5% of keywords matched
            confidence = min(top_specialty[1] * 10, 1.0)  # Scale to 0-1
            return (top_specialty[0], confidence)

        return None

    def detect_from_drugs(self, drugs: list[str]) -> dict[MedicalSpecialty, int]:
        """
        Detect specialty from drug mentions.

        Args:
            drugs: List of drug names or classes.

        Returns:
            Dictionary of specialty -> count.
        """
        specialty_counts: dict[MedicalSpecialty, int] = {}

        for drug in drugs:
            drug_lower = drug.lower()

            # Check drug class map
            for drug_class, specialty in self.drug_map.items():
                if drug_class in drug_lower:
                    specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1

        return specialty_counts

    def detect_from_icd_codes(self, icd_codes: list[str]) -> dict[MedicalSpecialty, int]:
        """
        Detect specialty from ICD codes.

        Args:
            icd_codes: List of ICD-10 codes.

        Returns:
            Dictionary of specialty -> count.
        """
        specialty_counts: dict[MedicalSpecialty, int] = {}

        for code in icd_codes:
            if not code:
                continue

            # Extract first letter
            prefix = code[0].upper()

            if prefix in self.icd_map:
                specialty = self.icd_map[prefix]
                specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1

        return specialty_counts

    def detect_from_history(
        self,
        query_history: list[QueryHistory],
        min_confidence: float = 0.3,
    ) -> list[SpecialtyConfidence]:
        """
        Detect specialty from query history.

        Args:
            query_history: List of historical queries.
            min_confidence: Minimum confidence to include.

        Returns:
            List of specialty confidences, sorted by confidence.
        """
        specialty_evidence: dict[MedicalSpecialty, list[float]] = {}

        for query_record in query_history:
            # Analyze query text
            detection = self.detect_from_query(query_record.query)
            if detection:
                specialty, confidence = detection
                if specialty not in specialty_evidence:
                    specialty_evidence[specialty] = []
                specialty_evidence[specialty].append(confidence)

            # Analyze drugs
            if query_record.mentioned_drugs:
                drug_specialties = self.detect_from_drugs(query_record.mentioned_drugs)
                for specialty, count in drug_specialties.items():
                    if specialty not in specialty_evidence:
                        specialty_evidence[specialty] = []
                    # Each drug mention adds evidence
                    specialty_evidence[specialty].extend([0.8] * count)

            # Analyze conditions (ICD codes)
            if query_record.mentioned_conditions:
                icd_specialties = self.detect_from_icd_codes(query_record.mentioned_conditions)
                for specialty, count in icd_specialties.items():
                    if specialty not in specialty_evidence:
                        specialty_evidence[specialty] = []
                    specialty_evidence[specialty].extend([0.7] * count)

        # Calculate confidence scores
        results = []
        total_evidence = sum(len(v) for v in specialty_evidence.values())

        for specialty, evidences in specialty_evidence.items():
            # Confidence is average of evidence scores, weighted by frequency
            avg_confidence = sum(evidences) / len(evidences)
            frequency_weight = len(evidences) / total_evidence if total_evidence > 0 else 0

            # Combined confidence
            confidence = (avg_confidence + frequency_weight) / 2

            if confidence >= min_confidence:
                results.append(
                    SpecialtyConfidence(
                        specialty=specialty,
                        confidence=confidence,
                        evidence_count=len(evidences),
                    )
                )

        # Sort by confidence
        results.sort(key=lambda x: x.confidence, reverse=True)

        return results

    def extract_entities(self, query: str) -> dict[str, list[str]]:
        """
        Extract medical entities from query.

        Args:
            query: Query text.

        Returns:
            Dictionary with 'drugs', 'conditions', 'procedures'.
        """
        # Simple pattern-based extraction
        # In production, use NER models like ScispaCy or BioBERT

        result = {
            "drugs": [],
            "conditions": [],
            "procedures": [],
        }

        query_lower = query.lower()

        # Common drug patterns
        drug_patterns = [
            r"\b\w+cillin\b",  # penicillin, amoxicillin
            r"\b\w+mycin\b",   # erythromycin, azithromycin
            r"\b\w+olol\b",    # beta blockers
            r"\b\w+pril\b",    # ACE inhibitors
            r"\b\w+sartan\b",  # ARBs
            r"\b\w+statin\b",  # statins
            r"\b\w+azole\b",   # antifungals
            r"\b\w+triptan\b", # migraine drugs
        ]

        for pattern in drug_patterns:
            matches = re.findall(pattern, query_lower)
            result["drugs"].extend(matches)

        # ICD code patterns
        icd_pattern = r"\b[A-Z]\d{2}(?:\.\d{1,2})?\b"
        icd_matches = re.findall(icd_pattern, query.upper())
        result["conditions"].extend(icd_matches)

        # Common procedures
        procedure_keywords = [
            "biopsy", "endoscopy", "colonoscopy", "angiography", "ct scan",
            "mri", "ultrasound", "x-ray", "echocardiogram", "ekg", "ecg",
        ]

        for proc in procedure_keywords:
            if proc in query_lower:
                result["procedures"].append(proc)

        return result
