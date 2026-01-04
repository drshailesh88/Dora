"""
Clinical Pearls

Curated clinical tips, memorable one-liners, and evidence-based facts.
Delivered daily by specialty.
"""

import random
from datetime import datetime
from typing import Any, Optional

from src.engagement.models import ClinicalPearl


class PearlManager:
    """Manages clinical pearls."""

    def __init__(self):
        """Initialize pearl manager."""
        self.pearl_database = self._load_pearl_database()
        self.user_history = {}  # Track which pearls user has seen

    def get_daily_pearl(
        self,
        user_id: str,
        specialty: str,
        difficulty: str = "medium",
    ) -> Optional[ClinicalPearl]:
        """
        Get daily clinical pearl for user.

        Args:
            user_id: User ID
            specialty: User's specialty
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            ClinicalPearl object or None
        """
        # Get pearls for specialty
        specialty_pearls = self._get_pearls_by_specialty(specialty)

        if not specialty_pearls:
            # Fall back to general medicine
            specialty_pearls = self._get_pearls_by_specialty("general")

        if not specialty_pearls:
            return None

        # Filter by difficulty
        filtered = [
            p for p in specialty_pearls
            if p["difficulty"] == difficulty
        ]

        if not filtered:
            filtered = specialty_pearls

        # Exclude previously seen pearls
        seen_ids = self.user_history.get(user_id, set())
        unseen = [p for p in filtered if p["id"] not in seen_ids]

        if not unseen:
            # User has seen all pearls, reset history
            self.user_history[user_id] = set()
            unseen = filtered

        # Select random pearl
        pearl_data = random.choice(unseen)

        # Mark as seen
        if user_id not in self.user_history:
            self.user_history[user_id] = set()
        self.user_history[user_id].add(pearl_data["id"])

        # Convert to ClinicalPearl object
        return self._to_clinical_pearl(pearl_data)

    def get_pearl_by_category(
        self,
        specialty: str,
        category: str,
    ) -> list[ClinicalPearl]:
        """
        Get pearls by category.

        Args:
            specialty: Medical specialty
            category: Pearl category (diagnosis, treatment, etc.)

        Returns:
            List of ClinicalPearl objects
        """
        all_pearls = self._get_pearls_by_specialty(specialty)

        filtered = [
            p for p in all_pearls
            if p.get("category") == category
        ]

        return [self._to_clinical_pearl(p) for p in filtered]

    def search_pearls(
        self,
        query: str,
        specialty: Optional[str] = None,
    ) -> list[ClinicalPearl]:
        """
        Search pearls by keyword.

        Args:
            query: Search query
            specialty: Optional specialty filter

        Returns:
            List of matching ClinicalPearl objects
        """
        query_lower = query.lower()

        if specialty:
            search_pool = self._get_pearls_by_specialty(specialty)
        else:
            search_pool = self.pearl_database

        matches = []
        for pearl_data in search_pool:
            # Search in title, content, and keywords
            if (query_lower in pearl_data["title"].lower() or
                query_lower in pearl_data["content"].lower() or
                any(query_lower in kw.lower() for kw in pearl_data.get("keywords", []))):
                matches.append(self._to_clinical_pearl(pearl_data))

        return matches

    def create_pearl(
        self,
        title: str,
        content: str,
        specialty: str,
        category: str,
        evidence_level: str = "high",
        citations: list[str] = None,
        **kwargs,
    ) -> ClinicalPearl:
        """
        Create a new clinical pearl.

        Args:
            title: Pearl title
            content: Pearl content
            specialty: Specialty
            category: Category
            evidence_level: Evidence level
            citations: Source citations
            **kwargs: Additional fields

        Returns:
            ClinicalPearl object
        """
        pearl = ClinicalPearl(
            title=title,
            content=content,
            specialty=specialty,
            category=category,
            evidence_level=evidence_level,
            citations=citations or [],
            **kwargs,
        )

        # In real implementation, save to database
        self.pearl_database.append(self._to_dict(pearl))

        return pearl

    def get_pearl_quiz(
        self,
        user_id: str,
        specialty: str,
    ) -> Optional[ClinicalPearl]:
        """
        Get a pearl formatted as a quiz question.

        Args:
            user_id: User ID
            specialty: User's specialty

        Returns:
            ClinicalPearl with quiz format or None
        """
        # Get pearls that have quiz format
        specialty_pearls = self._get_pearls_by_specialty(specialty)
        quiz_pearls = [
            p for p in specialty_pearls
            if p.get("question") and p.get("answer")
        ]

        if not quiz_pearls:
            return None

        # Select unseen quiz
        seen_ids = self.user_history.get(user_id, set())
        unseen = [p for p in quiz_pearls if p["id"] not in seen_ids]

        if not unseen:
            unseen = quiz_pearls

        pearl_data = random.choice(unseen)

        # Mark as seen
        if user_id not in self.user_history:
            self.user_history[user_id] = set()
        self.user_history[user_id].add(pearl_data["id"])

        return self._to_clinical_pearl(pearl_data)

    def _get_pearls_by_specialty(self, specialty: str) -> list[dict[str, Any]]:
        """Get pearls for a specific specialty."""
        return [
            p for p in self.pearl_database
            if p.get("specialty", "").lower() == specialty.lower()
        ]

    def _to_clinical_pearl(self, pearl_data: dict[str, Any]) -> ClinicalPearl:
        """Convert dict to ClinicalPearl object."""
        return ClinicalPearl(**pearl_data)

    def _to_dict(self, pearl: ClinicalPearl) -> dict[str, Any]:
        """Convert ClinicalPearl to dict."""
        return pearl.model_dump()

    def _load_pearl_database(self) -> list[dict[str, Any]]:
        """
        Load clinical pearls database.

        In production, this would load from database.
        For now, returns curated pearls.
        """
        return [
            # Cardiology
            {
                "id": "cardio_001",
                "title": "Beta Blockers First in AFib",
                "content": "Remember: BB before CCB in rate control for AFib with heart failure",
                "explanation": "Beta blockers have mortality benefit in HFrEF, while rate-limiting CCBs (diltiazem, verapamil) are contraindicated in systolic heart failure.",
                "specialty": "cardiology",
                "category": "treatment",
                "keywords": ["afib", "heart failure", "beta blocker", "rate control"],
                "citations": ["ACC/AHA 2019 AFib Guidelines"],
                "evidence_level": "high",
                "difficulty": "medium",
            },
            {
                "id": "cardio_002",
                "title": "SGLT2i in HFrEF",
                "content": "SGLT2 inhibitors reduce HF hospitalizations even in non-diabetics",
                "explanation": "DAPA-HF and EMPEROR-Reduced trials showed mortality benefit of SGLT2i in HFrEF regardless of diabetes status.",
                "specialty": "cardiology",
                "category": "treatment",
                "keywords": ["heart failure", "sglt2", "dapagliflozin"],
                "citations": ["NEJM 2019;381:1995-2008"],
                "evidence_level": "high",
                "difficulty": "hard",
                "question": "Do SGLT2 inhibitors benefit HFrEF patients without diabetes?",
                "answer": "Yes, they reduce mortality and HF hospitalizations",
                "distractors": [
                    "No, only effective in diabetics",
                    "Only reduce symptoms, not outcomes",
                    "Contraindicated in non-diabetics",
                ],
            },
            {
                "id": "cardio_003",
                "title": "Troponin in PE",
                "content": "Elevated troponin in PE indicates RV strain and higher risk",
                "explanation": "Troponin elevation in acute PE suggests RV dysfunction and identifies patients who may benefit from thrombolysis.",
                "specialty": "cardiology",
                "category": "diagnosis",
                "keywords": ["pulmonary embolism", "troponin", "rv strain"],
                "citations": ["ESC 2019 PE Guidelines"],
                "evidence_level": "high",
                "difficulty": "easy",
            },

            # Diabetes/Endocrinology
            {
                "id": "endo_001",
                "title": "Metformin Start Low Go Slow",
                "content": "Metformin: Start low (500mg), go slow → 2000mg over 4 weeks",
                "explanation": "Starting at low dose and titrating slowly reduces GI side effects and improves adherence.",
                "specialty": "endocrinology",
                "category": "prescribing",
                "keywords": ["metformin", "diabetes", "titration"],
                "citations": ["ADA Standards of Care 2026"],
                "evidence_level": "high",
                "difficulty": "easy",
            },
            {
                "id": "endo_002",
                "title": "HbA1c < 7% Target",
                "content": "HbA1c target <7% for most, but individualize for elderly/comorbid",
                "explanation": "While <7% is general target, elderly patients or those with limited life expectancy may have higher targets (7.5-8%) to reduce hypoglycemia risk.",
                "specialty": "endocrinology",
                "category": "treatment",
                "keywords": ["hba1c", "diabetes", "target"],
                "citations": ["ADA Standards of Care 2026"],
                "evidence_level": "high",
                "difficulty": "medium",
            },
            {
                "id": "endo_003",
                "title": "Insulin Pen Needles",
                "content": "Insulin pen needles should NOT be reused - risk of lipohypertrophy",
                "explanation": "Reusing needles causes lipohypertrophy and unpredictable insulin absorption.",
                "specialty": "endocrinology",
                "category": "prescribing",
                "keywords": ["insulin", "needles", "injection"],
                "citations": ["EASD Guidelines"],
                "evidence_level": "high",
                "difficulty": "easy",
            },

            # Pediatrics
            {
                "id": "peds_001",
                "title": "Fever in Infants",
                "content": "Fever in <3 months = always septic workup (blood, urine, LP)",
                "explanation": "Infants <3 months have immature immune systems and can decompensate rapidly. Full septic workup is mandatory.",
                "specialty": "pediatrics",
                "category": "diagnosis",
                "keywords": ["fever", "infant", "sepsis"],
                "citations": ["AAP Febrile Infant Guidelines 2021"],
                "evidence_level": "high",
                "difficulty": "easy",
            },
            {
                "id": "peds_002",
                "title": "Ondansetron in Pediatrics",
                "content": "Ondansetron reduces vomiting in pediatric gastroenteritis",
                "explanation": "Single dose of ondansetron reduces vomiting episodes and need for IV hydration in children with viral gastroenteritis.",
                "specialty": "pediatrics",
                "category": "treatment",
                "keywords": ["ondansetron", "vomiting", "gastroenteritis"],
                "citations": ["Cochrane Review 2011"],
                "evidence_level": "high",
                "difficulty": "medium",
                "question": "Is ondansetron effective for vomiting in pediatric gastroenteritis?",
                "answer": "Yes, reduces vomiting and need for IV fluids",
                "distractors": [
                    "No, only placebo effect",
                    "Only in bacterial gastroenteritis",
                    "Contraindicated in children",
                ],
            },

            # Nephrology
            {
                "id": "nephro_001",
                "title": "AKI in Sepsis",
                "content": "In sepsis-induced AKI, avoid NSAIDs and ACEi/ARBs",
                "explanation": "Both NSAIDs and RAS blockers can worsen kidney function in the setting of sepsis-induced AKI.",
                "specialty": "nephrology",
                "category": "treatment",
                "keywords": ["aki", "sepsis", "nsaids"],
                "citations": ["KDIGO AKI Guidelines"],
                "evidence_level": "high",
                "difficulty": "medium",
            },

            # Pulmonology
            {
                "id": "pulm_001",
                "title": "COPD Spirometry Criteria",
                "content": "COPD diagnosis: FEV1/FVC < 0.70 post-bronchodilator",
                "explanation": "Fixed ratio <0.70 after bronchodilator defines airflow obstruction in COPD.",
                "specialty": "pulmonology",
                "category": "diagnosis",
                "keywords": ["copd", "spirometry", "fev1"],
                "citations": ["GOLD 2023 Guidelines"],
                "evidence_level": "high",
                "difficulty": "easy",
            },
            {
                "id": "pulm_002",
                "title": "Asthma ICS First",
                "content": "Inhaled corticosteroids (ICS) are first-line for persistent asthma",
                "explanation": "ICS are the most effective anti-inflammatory therapy and first-line for all severity levels of persistent asthma.",
                "specialty": "pulmonology",
                "category": "treatment",
                "keywords": ["asthma", "inhaled corticosteroid", "treatment"],
                "citations": ["GINA 2023"],
                "evidence_level": "high",
                "difficulty": "easy",
            },

            # Neurology
            {
                "id": "neuro_001",
                "title": "Stroke tPA Window",
                "content": "IV tPA window: 4.5 hours from symptom onset (not arrival time)",
                "explanation": "Time is from when patient was last seen normal, not when they arrived at hospital. Wake-up strokes need imaging to determine eligibility.",
                "specialty": "neurology",
                "category": "treatment",
                "keywords": ["stroke", "tpa", "thrombolysis"],
                "citations": ["AHA/ASA Stroke Guidelines 2019"],
                "evidence_level": "high",
                "difficulty": "medium",
            },

            # General Medicine
            {
                "id": "general_001",
                "title": "Antibiotic Stewardship",
                "content": "Viral URIs don't need antibiotics - educate, don't prescribe",
                "explanation": "Most URIs are viral. Unnecessary antibiotics drive resistance and have side effects. Patient education is key.",
                "specialty": "general",
                "category": "prescribing",
                "keywords": ["antibiotics", "uri", "stewardship"],
                "citations": ["CDC Guidelines"],
                "evidence_level": "high",
                "difficulty": "easy",
            },
            {
                "id": "general_002",
                "title": "DVT Wells Score",
                "content": "Low Wells score + negative D-dimer rules out DVT (99% NPV)",
                "explanation": "Combination of low clinical probability and negative D-dimer has excellent negative predictive value.",
                "specialty": "general",
                "category": "diagnosis",
                "keywords": ["dvt", "wells", "d-dimer"],
                "citations": ["Lancet 2003;361:567"],
                "evidence_level": "high",
                "difficulty": "medium",
                "question": "Can you rule out DVT with low Wells score and negative D-dimer?",
                "answer": "Yes, NPV is 99%",
                "distractors": [
                    "No, always need ultrasound",
                    "Only if D-dimer is very low",
                    "Only in young patients",
                ],
            },

            # Obstetrics
            {
                "id": "obgyn_001",
                "title": "Preeclampsia with Severe Features",
                "content": "Preeclampsia + BP ≥160/110, platelets <100k, or symptoms = deliver",
                "explanation": "Severe features of preeclampsia warrant delivery regardless of gestational age for maternal safety.",
                "specialty": "obstetrics_gynecology",
                "category": "treatment",
                "keywords": ["preeclampsia", "severe", "delivery"],
                "citations": ["ACOG 2019"],
                "evidence_level": "high",
                "difficulty": "hard",
            },

            # Emergency Medicine
            {
                "id": "em_001",
                "title": "PERC Rule",
                "content": "PERC rule: If all 8 criteria negative, PE prevalence <2%, skip testing",
                "explanation": "Pulmonary Embolism Rule-out Criteria can safely exclude PE without D-dimer in low-risk patients.",
                "specialty": "emergency_medicine",
                "category": "diagnosis",
                "keywords": ["pe", "perc", "rule out"],
                "citations": ["Ann Emerg Med 2008"],
                "evidence_level": "high",
                "difficulty": "hard",
            },
        ]
