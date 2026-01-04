"""Recommendation engine for personalized suggestions."""

from typing import Optional

from src.personalization.models import (
    DoctorProfile,
    MedicalSpecialty,
    PersonalizationConfig,
    QueryPattern,
)


class PersonalizedRecommender:
    """Generates personalized recommendations for doctors."""

    def __init__(self, config: Optional[PersonalizationConfig] = None):
        """
        Initialize recommender.

        Args:
            config: Personalization configuration.
        """
        self.config = config or PersonalizationConfig()

        # Specialty-specific content recommendations
        self.specialty_topics = self._build_specialty_topics()
        self.specialty_guidelines = self._build_specialty_guidelines()
        self.specialty_calculators = self._build_specialty_calculators()

    def recommend_related_topics(
        self,
        query: str,
        profile: DoctorProfile,
    ) -> list[str]:
        """
        Recommend related topics based on query and profile.

        Args:
            query: Current query.
            profile: Doctor profile.

        Returns:
            List of related topic suggestions.
        """
        recommendations = []

        top_specialty = profile.get_top_specialty()
        if not top_specialty:
            return recommendations

        # Get specialty-specific topics
        topics = self.specialty_topics.get(top_specialty, [])

        # Simple keyword matching (in production, use embeddings)
        query_lower = query.lower()

        for topic in topics:
            topic_lower = topic.lower()
            # Check if topic is related to query
            if any(word in topic_lower for word in query_lower.split()):
                recommendations.append(topic)

        # Limit recommendations
        return recommendations[: self.config.related_topics_count]

    def recommend_guidelines(
        self,
        profile: DoctorProfile,
        context: Optional[str] = None,
    ) -> list[dict]:
        """
        Recommend relevant clinical guidelines.

        Args:
            profile: Doctor profile.
            context: Optional context (e.g., specific condition).

        Returns:
            List of guideline recommendations with metadata.
        """
        recommendations = []

        # Get guidelines for all relevant specialties
        for specialty in profile.get_all_specialties():
            guidelines = self.specialty_guidelines.get(specialty, [])

            for guideline in guidelines:
                # Filter by context if provided
                if context:
                    context_lower = context.lower()
                    if context_lower not in guideline["title"].lower():
                        continue

                recommendations.append({
                    "title": guideline["title"],
                    "organization": guideline["organization"],
                    "year": guideline["year"],
                    "specialty": specialty.value,
                    "relevance_score": guideline.get("relevance", 1.0),
                })

        # Sort by relevance and year
        recommendations.sort(
            key=lambda x: (x["relevance_score"], x["year"]),
            reverse=True,
        )

        return recommendations[: self.config.recommendation_count]

    def recommend_calculators(
        self,
        profile: DoctorProfile,
        query: Optional[str] = None,
    ) -> list[dict]:
        """
        Recommend relevant medical calculators.

        Args:
            profile: Doctor profile.
            query: Optional query context.

        Returns:
            List of calculator recommendations.
        """
        recommendations = []

        # Get calculators for specialty
        top_specialty = profile.get_top_specialty()
        if not top_specialty:
            return recommendations

        calculators = self.specialty_calculators.get(top_specialty, [])

        for calc in calculators:
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                calc_keywords = calc.get("keywords", [])

                if not any(kw in query_lower for kw in calc_keywords):
                    continue

            recommendations.append({
                "name": calc["name"],
                "description": calc["description"],
                "category": calc["category"],
                "specialty": top_specialty.value,
            })

        return recommendations[: self.config.recommendation_count]

    def recommend_cme_topics(
        self,
        profile: DoctorProfile,
        patterns: QueryPattern,
    ) -> list[dict]:
        """
        Recommend CME (Continuing Medical Education) topics.

        Args:
            profile: Doctor profile.
            patterns: Query patterns.

        Returns:
            List of CME topic recommendations.
        """
        recommendations = []

        # Analyze knowledge gaps from patterns
        top_categories = patterns.get_top_categories(top_n=10)

        # Get specialty
        top_specialty = profile.get_top_specialty()
        if not top_specialty:
            return recommendations

        # Recommend based on frequently queried topics
        for category in top_categories:
            recommendations.append({
                "topic": f"Advanced {category.replace('_', ' ').title()}",
                "specialty": top_specialty.value,
                "rationale": f"Frequently queried topic in your practice",
                "estimated_hours": 2,
            })

        # Add specialty-specific trending topics
        trending_topics = self._get_trending_cme_topics(top_specialty)
        for topic in trending_topics:
            recommendations.append({
                "topic": topic["title"],
                "specialty": top_specialty.value,
                "rationale": "Trending in your specialty",
                "estimated_hours": topic["hours"],
            })

        return recommendations[: self.config.recommendation_count]

    def recommend_reading(
        self,
        profile: DoctorProfile,
    ) -> list[dict]:
        """
        Recommend textbooks and reading materials.

        Args:
            profile: Doctor profile.

        Returns:
            List of reading recommendations.
        """
        recommendations = []

        top_specialty = profile.get_top_specialty()
        if not top_specialty:
            return recommendations

        # Essential textbooks by specialty
        specialty_books = {
            MedicalSpecialty.CARDIOLOGY: [
                {"title": "Braunwald's Heart Disease", "edition": "12th", "relevance": 1.0},
                {"title": "Hurst's The Heart", "edition": "15th", "relevance": 0.9},
                {"title": "ECG Interpretation Made Incredibly Easy", "edition": "7th", "relevance": 0.8},
            ],
            MedicalSpecialty.INTERNAL_MEDICINE: [
                {"title": "Harrison's Principles of Internal Medicine", "edition": "21st", "relevance": 1.0},
                {"title": "Cecil Textbook of Medicine", "edition": "26th", "relevance": 0.95},
                {"title": "Current Medical Diagnosis and Treatment", "edition": "2024", "relevance": 0.9},
            ],
            MedicalSpecialty.PULMONOLOGY: [
                {"title": "Murray and Nadel's Textbook of Respiratory Medicine", "edition": "7th", "relevance": 1.0},
                {"title": "Fishman's Pulmonary Diseases and Disorders", "edition": "6th", "relevance": 0.9},
            ],
            MedicalSpecialty.NEUROLOGY: [
                {"title": "Adams and Victor's Principles of Neurology", "edition": "12th", "relevance": 1.0},
                {"title": "Bradley and Daroff's Neurology in Clinical Practice", "edition": "8th", "relevance": 0.95},
            ],
            MedicalSpecialty.PEDIATRICS: [
                {"title": "Nelson Textbook of Pediatrics", "edition": "21st", "relevance": 1.0},
                {"title": "Red Book: Report of the Committee on Infectious Diseases", "edition": "2024", "relevance": 0.9},
            ],
        }

        books = specialty_books.get(top_specialty, [])
        for book in books:
            recommendations.append({
                "title": book["title"],
                "edition": book["edition"],
                "specialty": top_specialty.value,
                "relevance_score": book["relevance"],
                "type": "textbook",
            })

        return recommendations

    def _build_specialty_topics(self) -> dict[MedicalSpecialty, list[str]]:
        """Build specialty-specific topic recommendations."""
        return {
            MedicalSpecialty.CARDIOLOGY: [
                "Acute coronary syndrome management",
                "Heart failure with preserved ejection fraction",
                "Atrial fibrillation anticoagulation",
                "Hypertrophic cardiomyopathy",
                "Valvular heart disease assessment",
                "Cardiac arrhythmia interpretation",
                "Lipid management guidelines",
                "Antiplatelet therapy in ACS",
            ],
            MedicalSpecialty.PULMONOLOGY: [
                "COPD exacerbation management",
                "Asthma control strategies",
                "Interstitial lung disease diagnosis",
                "Pulmonary embolism risk stratification",
                "Sleep apnea treatment options",
                "Lung cancer screening criteria",
                "Pulmonary function test interpretation",
            ],
            MedicalSpecialty.ENDOCRINOLOGY: [
                "Type 2 diabetes treatment algorithms",
                "Thyroid nodule evaluation",
                "Diabetic ketoacidosis management",
                "SGLT2 inhibitor use",
                "Osteoporosis screening and treatment",
                "Adrenal insufficiency diagnosis",
            ],
            MedicalSpecialty.NEUROLOGY: [
                "Acute stroke management",
                "Seizure disorder classification",
                "Migraine prophylaxis options",
                "Parkinson's disease treatment",
                "Multiple sclerosis disease-modifying therapies",
                "Neuropathy workup",
            ],
            MedicalSpecialty.PSYCHIATRY: [
                "Treatment-resistant depression",
                "Bipolar disorder stabilization",
                "Antipsychotic selection",
                "PTSD evidence-based treatments",
                "ADHD management in adults",
            ],
        }

    def _build_specialty_guidelines(self) -> dict[MedicalSpecialty, list[dict]]:
        """Build specialty-specific guideline recommendations."""
        return {
            MedicalSpecialty.CARDIOLOGY: [
                {
                    "title": "AHA/ACC Guideline for the Management of Heart Failure",
                    "organization": "AHA/ACC",
                    "year": 2022,
                    "relevance": 1.0,
                },
                {
                    "title": "ESC Guidelines for Atrial Fibrillation",
                    "organization": "ESC",
                    "year": 2020,
                    "relevance": 0.95,
                },
                {
                    "title": "AHA/ACC Guideline on the Primary Prevention of CVD",
                    "organization": "AHA/ACC",
                    "year": 2019,
                    "relevance": 0.9,
                },
            ],
            MedicalSpecialty.PULMONOLOGY: [
                {
                    "title": "GOLD Guidelines for COPD",
                    "organization": "GOLD",
                    "year": 2024,
                    "relevance": 1.0,
                },
                {
                    "title": "GINA Guidelines for Asthma Management",
                    "organization": "GINA",
                    "year": 2024,
                    "relevance": 1.0,
                },
            ],
            MedicalSpecialty.ENDOCRINOLOGY: [
                {
                    "title": "ADA Standards of Medical Care in Diabetes",
                    "organization": "ADA",
                    "year": 2024,
                    "relevance": 1.0,
                },
                {
                    "title": "ATA Guidelines for Thyroid Nodules and Cancer",
                    "organization": "ATA",
                    "year": 2015,
                    "relevance": 0.9,
                },
            ],
        }

    def _build_specialty_calculators(self) -> dict[MedicalSpecialty, list[dict]]:
        """Build specialty-specific calculator recommendations."""
        return {
            MedicalSpecialty.CARDIOLOGY: [
                {
                    "name": "CHA2DS2-VASc Score",
                    "description": "Stroke risk in atrial fibrillation",
                    "category": "risk_stratification",
                    "keywords": ["atrial fibrillation", "stroke risk", "anticoagulation"],
                },
                {
                    "name": "TIMI Risk Score",
                    "description": "Risk in acute coronary syndrome",
                    "category": "risk_stratification",
                    "keywords": ["acs", "stemi", "nstemi", "risk"],
                },
                {
                    "name": "GRACE Score",
                    "description": "In-hospital and 6-month mortality in ACS",
                    "category": "prognosis",
                    "keywords": ["acs", "mortality", "prognosis"],
                },
            ],
            MedicalSpecialty.PULMONOLOGY: [
                {
                    "name": "CURB-65",
                    "description": "Pneumonia severity assessment",
                    "category": "severity_scoring",
                    "keywords": ["pneumonia", "severity", "admission"],
                },
                {
                    "name": "Wells Score for PE",
                    "description": "Pulmonary embolism probability",
                    "category": "diagnosis",
                    "keywords": ["pulmonary embolism", "pe", "dvt"],
                },
            ],
            MedicalSpecialty.NEPHROLOGY: [
                {
                    "name": "CKD-EPI GFR Calculator",
                    "description": "Estimated glomerular filtration rate",
                    "category": "assessment",
                    "keywords": ["gfr", "renal function", "creatinine"],
                },
                {
                    "name": "Fractional Excretion of Sodium",
                    "description": "Differentiate causes of AKI",
                    "category": "diagnosis",
                    "keywords": ["aki", "acute kidney injury", "fena"],
                },
            ],
        }

    def _get_trending_cme_topics(self, specialty: MedicalSpecialty) -> list[dict]:
        """Get trending CME topics for specialty."""
        # In production, this would query a CME database or API
        # Placeholder implementation

        trending = {
            MedicalSpecialty.CARDIOLOGY: [
                {"title": "SGLT2 Inhibitors in Heart Failure", "hours": 2},
                {"title": "AI in ECG Interpretation", "hours": 1},
            ],
            MedicalSpecialty.PULMONOLOGY: [
                {"title": "Long COVID Management", "hours": 3},
                {"title": "Triple Therapy in COPD", "hours": 2},
            ],
        }

        return trending.get(specialty, [])
