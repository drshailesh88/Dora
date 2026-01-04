"""
Prescription Analytics

Analyzes prescription patterns to provide insights on:
- Generic vs brand usage
- Antibiotic stewardship
- Cost patterns
- Drug class preferences
- Safety metrics
"""

from collections import Counter
from datetime import date
from typing import Optional, List

from .models import PrescriptionPatterns


class PrescriptionAnalyzer:
    """
    Analyzes prescription patterns for practice insights.

    Provides insights on:
    - Generic prescribing rates
    - Antibiotic stewardship
    - Cost optimization
    - Safety scores
    - Prescribing trends
    """

    def __init__(self):
        """Initialize prescription analyzer."""
        # Common antibiotic classes
        self.antibiotic_keywords = [
            'cillin', 'mycin', 'cycline', 'oxacin', 'azole',
            'cephalosporin', 'quinolone', 'macrolide', 'penicillin'
        ]

        # Broad vs narrow spectrum (simplified classification)
        self.broad_spectrum = [
            'ceftriaxone', 'ciprofloxacin', 'levofloxacin',
            'imipenem', 'meropenem', 'piperacillin'
        ]

    def analyze_prescriptions(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        prescriptions: Optional[List[dict]] = None,
    ) -> PrescriptionPatterns:
        """
        Analyze prescription patterns for a user.

        Args:
            user_id: User identifier
            start_date: Start of period
            end_date: End of period
            prescriptions: List of prescription data dicts

        Returns:
            PrescriptionPatterns with metrics
        """
        if not prescriptions:
            # Would fetch from prescription database
            # For now, return empty structure
            return self._empty_patterns(user_id, start_date, end_date)

        # Volume metrics
        total_prescriptions = len(prescriptions)
        total_meds = sum(len(p.get('items', [])) for p in prescriptions)
        avg_meds_per_rx = total_meds / total_prescriptions if total_prescriptions > 0 else 0

        # Generic vs brand analysis
        generic_count = 0
        brand_count = 0
        all_drugs = []

        for rx in prescriptions:
            for item in rx.get('items', []):
                all_drugs.append(item)
                is_generic = item.get('generic_name') is not None
                if is_generic or not item.get('drug_name', '').istitle():
                    # Heuristic: lowercase names are generic
                    generic_count += 1
                else:
                    brand_count += 1

        total_drug_count = generic_count + brand_count
        generic_pct = generic_count / total_drug_count * 100 if total_drug_count > 0 else 0

        # Antibiotic analysis
        antibiotic_count = 0
        broad_spectrum_count = 0
        narrow_spectrum_count = 0

        for drug in all_drugs:
            drug_name = drug.get('drug_name', '').lower()
            if self._is_antibiotic(drug_name):
                antibiotic_count += 1
                if self._is_broad_spectrum(drug_name):
                    broad_spectrum_count += 1
                else:
                    narrow_spectrum_count += 1

        antibiotic_pct = antibiotic_count / total_drug_count * 100 if total_drug_count > 0 else 0

        # Safety metrics
        interactions = sum(len(rx.get('warnings', [])) for rx in prescriptions)
        allergy_alerts = sum(
            1 for rx in prescriptions
            for w in rx.get('warnings', [])
            if 'allergy' in w.lower()
        )
        contraindications = sum(
            1 for rx in prescriptions
            for w in rx.get('warnings', [])
            if 'contraindication' in w.lower()
        )

        # Safety score: penalize interactions and alerts
        safety_score = max(0.0, 1.0 - (interactions * 0.05) - (allergy_alerts * 0.1))

        # Drug class distribution
        drug_classes = self._extract_drug_classes(all_drugs)

        # Most prescribed drugs
        drug_counter = Counter()
        for drug in all_drugs:
            drug_name = drug.get('drug_name', '')
            is_generic = drug.get('generic_name') is not None
            drug_counter[drug_name] += 1

        most_prescribed = [
            {
                'drug': drug,
                'count': count,
                'generic': not drug.istitle()  # Simplified heuristic
            }
            for drug, count in drug_counter.most_common(10)
        ]

        # Prescriptions by condition
        condition_counter = Counter()
        for rx in prescriptions:
            diagnosis = rx.get('diagnosis', 'unknown')
            if diagnosis:
                condition_counter[diagnosis] += 1

        prescriptions_by_condition = dict(condition_counter)

        # Schedule compliance
        schedule_h1 = sum(
            1 for drug in all_drugs
            if drug.get('schedule') == 'schedule_h1'
        )
        schedule_x = sum(
            1 for drug in all_drugs
            if drug.get('schedule') == 'schedule_x'
        )
        controlled_pct = (schedule_h1 + schedule_x) / total_drug_count * 100 if total_drug_count > 0 else 0

        return PrescriptionPatterns(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            total_prescriptions=total_prescriptions,
            total_medications_prescribed=total_meds,
            avg_medications_per_prescription=avg_meds_per_rx,
            top_drug_classes=drug_classes,
            generic_count=generic_count,
            brand_count=brand_count,
            generic_percentage=generic_pct,
            antibiotic_prescriptions=antibiotic_count,
            antibiotic_percentage=antibiotic_pct,
            broad_spectrum_antibiotics=broad_spectrum_count,
            narrow_spectrum_antibiotics=narrow_spectrum_count,
            drug_interactions_detected=interactions,
            allergy_alerts_triggered=allergy_alerts,
            contraindication_alerts=contraindications,
            safety_score=safety_score,
            most_prescribed_drugs=most_prescribed,
            prescriptions_by_condition=prescriptions_by_condition,
            schedule_h1_prescriptions=schedule_h1,
            schedule_x_prescriptions=schedule_x,
            controlled_substance_percentage=controlled_pct,
        )

    def get_antibiotic_stewardship_score(
        self,
        patterns: PrescriptionPatterns,
    ) -> dict:
        """
        Calculate antibiotic stewardship score.

        Args:
            patterns: PrescriptionPatterns data

        Returns:
            Dict with stewardship metrics
        """
        # Good stewardship:
        # - Lower overall antibiotic use
        # - Preference for narrow spectrum
        # - Appropriate indications

        antibiotic_rate = patterns.antibiotic_percentage

        # Ideal is < 20% antibiotic prescriptions
        rate_score = max(0, 1.0 - (antibiotic_rate - 20) / 30) if antibiotic_rate > 20 else 1.0

        # Prefer narrow spectrum
        total_antibiotics = patterns.antibiotic_prescriptions
        if total_antibiotics > 0:
            narrow_ratio = patterns.narrow_spectrum_antibiotics / total_antibiotics
            spectrum_score = narrow_ratio
        else:
            spectrum_score = 1.0

        # Overall stewardship score
        overall_score = (rate_score + spectrum_score) / 2

        # Rating
        if overall_score >= 0.8:
            rating = "excellent"
        elif overall_score >= 0.6:
            rating = "good"
        elif overall_score >= 0.4:
            rating = "fair"
        else:
            rating = "needs_improvement"

        return {
            'overall_score': overall_score,
            'rating': rating,
            'antibiotic_rate': antibiotic_rate,
            'narrow_spectrum_ratio': spectrum_score,
            'recommendations': self._get_stewardship_recommendations(overall_score, patterns),
        }

    def _is_antibiotic(self, drug_name: str) -> bool:
        """Check if drug is an antibiotic."""
        return any(kw in drug_name for kw in self.antibiotic_keywords)

    def _is_broad_spectrum(self, drug_name: str) -> bool:
        """Check if antibiotic is broad spectrum."""
        return any(bs in drug_name for bs in self.broad_spectrum)

    def _extract_drug_classes(self, drugs: List[dict], limit: int = 10) -> List[dict]:
        """Extract top drug classes."""
        # Simplified drug class extraction
        # In production, would use drug database with proper classification

        class_keywords = {
            'Antihypertensives': ['sartan', 'pril', 'olol'],
            'Antidiabetics': ['formin', 'gliptin', 'gliflozin'],
            'Antibiotics': self.antibiotic_keywords,
            'Statins': ['statin'],
            'PPIs': ['prazole'],
            'NSAIDs': ['ibuprofen', 'naproxen', 'diclofenac'],
            'Bronchodilators': ['buterol', 'phylline'],
        }

        class_counter = Counter()
        total_drugs = len(drugs)

        for drug in drugs:
            drug_name = drug.get('drug_name', '').lower()
            classified = False

            for drug_class, keywords in class_keywords.items():
                if any(kw in drug_name for kw in keywords):
                    class_counter[drug_class] += 1
                    classified = True
                    break

            if not classified:
                class_counter['Other'] += 1

        return [
            {
                'class': drug_class,
                'count': count,
                'percentage': count / total_drugs * 100 if total_drugs > 0 else 0
            }
            for drug_class, count in class_counter.most_common(limit)
        ]

    def _get_stewardship_recommendations(
        self,
        score: float,
        patterns: PrescriptionPatterns,
    ) -> List[str]:
        """Get antibiotic stewardship recommendations."""
        recommendations = []

        if patterns.antibiotic_percentage > 30:
            recommendations.append(
                "Consider reducing antibiotic prescriptions. Current rate is above recommended levels."
            )

        if patterns.broad_spectrum_antibiotics > patterns.narrow_spectrum_antibiotics:
            recommendations.append(
                "Prefer narrow-spectrum antibiotics when appropriate to reduce resistance."
            )

        if score >= 0.8:
            recommendations.append(
                "Excellent antibiotic stewardship! Keep up the good work."
            )

        return recommendations

    def _empty_patterns(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> PrescriptionPatterns:
        """Return empty prescription patterns."""
        return PrescriptionPatterns(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
        )


__all__ = ["PrescriptionAnalyzer"]
