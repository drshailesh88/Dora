"""
Neurology Calculators

Collection of neurological assessment scores.
"""

from typing import Dict, Any
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError


class GlasgowComaCalculator(Calculator):
    """
    Glasgow Coma Scale (GCS)

    Assesses level of consciousness.

    Reference: Teasdale G, Jennett B. Lancet 1974
    """

    def __init__(self):
        super().__init__()
        self.category = "neurology"
        self.description = "Level of consciousness assessment"
        self.citations = ["Teasdale G, Jennett B. Lancet. 1974;2(7872):81-84"]

    def calculate(
        self,
        eye_opening: int,
        verbal_response: int,
        motor_response: int,
    ) -> CalculatorResult:
        """
        Calculate Glasgow Coma Scale.

        Args:
            eye_opening: 1-4 (1=none, 2=to pain, 3=to speech, 4=spontaneous)
            verbal_response: 1-5 (1=none, 2=incomprehensible, 3=inappropriate, 4=confused, 5=oriented)
            motor_response: 1-6 (1=none, 2=extension, 3=flexion, 4=withdrawal, 5=localizes, 6=obeys)
        """
        self.validate_range(eye_opening, 1, 4, "eye_opening")
        self.validate_range(verbal_response, 1, 5, "verbal_response")
        self.validate_range(motor_response, 1, 6, "motor_response")

        gcs = eye_opening + verbal_response + motor_response

        # Severity classification
        if gcs >= 14:
            risk_level = RiskLevel.LOW
            severity = "Mild"
            interpretation = "Mild brain injury"
            recommendations = [
                "Observation",
                "Serial neurological exams",
                "CT if indicated by risk factors"
            ]
        elif gcs >= 9:
            risk_level = RiskLevel.MODERATE
            severity = "Moderate"
            interpretation = "Moderate brain injury"
            recommendations = [
                "CT head imaging",
                "Close monitoring",
                "ICU admission consideration",
                "Neurosurgery consultation if worsening"
            ]
        else:
            risk_level = RiskLevel.HIGH
            severity = "Severe"
            interpretation = "Severe brain injury"
            recommendations = [
                "Urgent CT head",
                "ICU admission",
                "Neurosurgery consultation",
                "Airway protection (consider intubation if GCS ≤8)",
                "ICP monitoring consideration"
            ]

        warnings = []
        if gcs <= 8:
            warnings.append("GCS ≤8: Consider intubation for airway protection")
        if motor_response <= 2:
            warnings.append("Abnormal posturing present - severe brain injury")

        # Descriptive text
        eye_desc = ["None", "To pain", "To speech", "Spontaneous"][eye_opening - 1]
        verbal_desc = ["None", "Incomprehensible", "Inappropriate", "Confused", "Oriented"][verbal_response - 1]
        motor_desc = ["None", "Extension", "Abnormal flexion", "Withdrawal", "Localizes pain", "Obeys commands"][motor_response - 1]

        return CalculatorResult(
            value=f"{gcs} (E{eye_opening}V{verbal_response}M{motor_response})",
            interpretation=f"{severity} brain injury: {interpretation}",
            risk_level=risk_level,
            reference_range="3-15 (3: worst, 15: best)",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "total_score": gcs,
                "eye": eye_opening,
                "verbal": verbal_response,
                "motor": motor_response,
                "severity": severity,
                "components": {
                    "eye_opening": eye_desc,
                    "verbal_response": verbal_desc,
                    "motor_response": motor_desc
                }
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "eye_opening": {
                    "type": "integer",
                    "min": 1,
                    "max": 4,
                    "description": "1=none, 2=to pain, 3=to speech, 4=spontaneous",
                    "required": True
                },
                "verbal_response": {
                    "type": "integer",
                    "min": 1,
                    "max": 5,
                    "description": "1=none, 2=incomprehensible, 3=inappropriate, 4=confused, 5=oriented",
                    "required": True
                },
                "motor_response": {
                    "type": "integer",
                    "min": 1,
                    "max": 6,
                    "description": "1=none, 2=extension, 3=flexion, 4=withdrawal, 5=localizes, 6=obeys",
                    "required": True
                },
            }
        }


class NIHStrokeScaleCalculator(Calculator):
    """
    NIH Stroke Scale (NIHSS)

    Quantifies stroke severity.
    Simplified version - returns structure for full assessment.

    Reference: Brott T, et al. Stroke 1989
    """

    def __init__(self):
        super().__init__()
        self.category = "neurology"
        self.description = "Stroke severity assessment"
        self.citations = ["Brott T, et al. Stroke. 1989;20(7):864-870"]

    def calculate(
        self,
        total_score: int,
    ) -> CalculatorResult:
        """
        Interpret NIHSS score.

        Args:
            total_score: Total NIHSS score (0-42)

        Note: Full NIHSS requires 15 individual assessments.
        This calculator accepts the total score for interpretation.
        """
        self.validate_range(total_score, 0, 42, "total_score")

        # Severity classification
        if total_score == 0:
            risk_level = RiskLevel.LOW
            severity = "No stroke symptoms"
            interpretation = "No stroke symptoms detected"
            recommendations = [
                "Rule out stroke mimics",
                "Consider TIA if history suggestive",
                "Risk factor modification"
            ]
        elif total_score <= 4:
            risk_level = RiskLevel.LOW
            severity = "Minor stroke"
            interpretation = "Minor stroke"
            recommendations = [
                "Consider thrombolysis if within window",
                "Stroke unit admission",
                "Secondary prevention",
                "Early mobilization"
            ]
        elif total_score <= 15:
            risk_level = RiskLevel.MODERATE
            severity = "Moderate stroke"
            interpretation = "Moderate stroke"
            recommendations = [
                "Thrombolysis if indicated and within window",
                "Consider thrombectomy if LVO",
                "Stroke unit care",
                "Comprehensive rehabilitation"
            ]
        elif total_score <= 20:
            risk_level = RiskLevel.HIGH
            severity = "Moderate to severe stroke"
            interpretation = "Moderate to severe stroke"
            recommendations = [
                "Urgent stroke team evaluation",
                "Thrombectomy evaluation for LVO",
                "ICU monitoring",
                "Aggressive supportive care"
            ]
        else:
            risk_level = RiskLevel.VERY_HIGH
            severity = "Severe stroke"
            interpretation = "Severe stroke"
            recommendations = [
                "Urgent intervention if eligible",
                "ICU admission",
                "Neurosurgery consultation if indicated",
                "Goals of care discussion",
                "Palliative care involvement"
            ]

        # Outcome prediction
        if total_score <= 5:
            outcome = "Good outcome likely with treatment"
        elif total_score <= 15:
            outcome = "Moderate disability likely"
        else:
            outcome = "Severe disability or mortality likely"

        return CalculatorResult(
            value=total_score,
            interpretation=f"{severity}: {interpretation}",
            risk_level=risk_level,
            reference_range="0: no stroke, 1-4: minor, 5-15: moderate, 16-20: mod-severe, 21-42: severe",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "max_score": 42,
                "severity": severity,
                "outcome_prediction": outcome
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "total_score": {
                    "type": "integer",
                    "min": 0,
                    "max": 42,
                    "description": "Sum of all 15 NIHSS components",
                    "required": True
                },
            }
        }


class ABCD2Calculator(Calculator):
    """
    ABCD2 Score

    Predicts stroke risk after TIA.

    Reference: Johnston SC, et al. Lancet 2007
    """

    def __init__(self):
        super().__init__()
        self.category = "neurology"
        self.description = "Stroke risk after TIA"
        self.citations = ["Johnston SC, et al. Lancet. 2007;369(9561):283-292"]

    def calculate(
        self,
        age: int,
        blood_pressure_elevated: bool,
        clinical_features: str,
        diabetes: bool,
        duration_minutes: int,
    ) -> CalculatorResult:
        """
        Calculate ABCD2 score.

        Args:
            age: Age in years
            blood_pressure_elevated: SBP ≥140 or DBP ≥90
            clinical_features: 'unilateral_weakness', 'speech_only', or 'other'
            diabetes: Diabetes mellitus
            duration_minutes: TIA symptom duration in minutes
        """
        self.validate_range(age, 0, 120, "age")
        self.validate_choice(clinical_features, ["unilateral_weakness", "speech_only", "other"], "clinical_features")
        self.validate_range(duration_minutes, 0, 1440, "duration_minutes")

        score = 0

        # A - Age ≥60
        if age >= 60:
            score += 1

        # B - Blood pressure
        if blood_pressure_elevated:
            score += 1

        # C - Clinical features
        if clinical_features == "unilateral_weakness":
            score += 2
        elif clinical_features == "speech_only":
            score += 1

        # D - Diabetes
        if diabetes:
            score += 1

        # D - Duration
        if duration_minutes >= 60:
            score += 2
        elif duration_minutes >= 10:
            score += 1

        # Risk stratification
        if score <= 3:
            risk_level = RiskLevel.LOW
            risk_2day = 1.0
            risk_7day = 1.2
            interpretation = "Low risk of stroke after TIA"
            recommendations = [
                "Outpatient workup may be appropriate",
                "Complete evaluation within 24-48 hours",
                "Start antiplatelet therapy",
                "Vascular imaging and echo"
            ]
        elif score <= 5:
            risk_level = RiskLevel.MODERATE
            risk_2day = 4.1
            risk_7day = 5.9
            interpretation = "Moderate risk of stroke after TIA"
            recommendations = [
                "Hospital admission or urgent observation",
                "Urgent vascular imaging (within 24 hours)",
                "Echocardiogram",
                "Consider dual antiplatelet therapy initially"
            ]
        else:
            risk_level = RiskLevel.HIGH
            risk_2day = 8.1
            risk_7day = 11.7
            interpretation = "High risk of stroke after TIA"
            recommendations = [
                "Hospital admission required",
                "Emergent vascular imaging",
                "Consider IV heparin if crescendo TIAs",
                "Neurology consultation",
                "Echocardiogram and Holter"
            ]

        warnings = []
        if score >= 4:
            warnings.append("High-risk TIA - urgent evaluation and admission recommended")

        return CalculatorResult(
            value=score,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="0-3: low risk, 4-5: moderate, 6-7: high risk",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "max_score": 7,
                "two_day_stroke_risk_percent": risk_2day,
                "seven_day_stroke_risk_percent": risk_7day
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 0, "max": 120, "required": True},
                "blood_pressure_elevated": {"type": "boolean", "description": "SBP ≥140 or DBP ≥90", "required": True},
                "clinical_features": {
                    "type": "string",
                    "choices": ["unilateral_weakness", "speech_only", "other"],
                    "required": True
                },
                "diabetes": {"type": "boolean", "required": True},
                "duration_minutes": {"type": "integer", "unit": "minutes", "min": 0, "max": 1440, "required": True},
            }
        }


class HuntHessCalculator(Calculator):
    """
    Hunt-Hess Grade

    Classification of subarachnoid hemorrhage severity.

    Reference: Hunt WE, Hess RM. J Neurosurg 1968
    """

    def __init__(self):
        super().__init__()
        self.category = "neurology"
        self.description = "SAH severity grading"
        self.citations = ["Hunt WE, Hess RM. J Neurosurg. 1968;28(1):14-20"]

    def calculate(
        self,
        grade: int,
    ) -> CalculatorResult:
        """
        Interpret Hunt-Hess grade.

        Args:
            grade: Hunt-Hess grade (1-5)
                1: Asymptomatic or mild headache
                2: Moderate to severe headache, nuchal rigidity, no neuro deficit except CN palsy
                3: Drowsy or confused, mild focal deficit
                4: Stuporous, moderate to severe hemiparesis
                5: Comatose, decerebrate posturing
        """
        self.validate_range(grade, 1, 5, "grade")

        grade_descriptions = {
            1: {
                "description": "Asymptomatic or mild headache and slight nuchal rigidity",
                "mortality": 30,
                "risk_level": RiskLevel.MODERATE,
                "interpretation": "Grade I - Mild SAH",
                "recommendations": [
                    "Aneurysm securing (coiling or clipping)",
                    "Nimodipine for vasospasm prevention",
                    "Close monitoring",
                    "Serial transcranial Doppler"
                ]
            },
            2: {
                "description": "Moderate to severe headache, nuchal rigidity, no deficit except CN palsy",
                "mortality": 40,
                "risk_level": RiskLevel.MODERATE,
                "interpretation": "Grade II - Moderate SAH",
                "recommendations": [
                    "Early aneurysm treatment",
                    "Nimodipine",
                    "ICU monitoring",
                    "Vasospasm surveillance"
                ]
            },
            3: {
                "description": "Drowsiness, confusion, or mild focal deficit",
                "mortality": 50,
                "risk_level": RiskLevel.HIGH,
                "interpretation": "Grade III - Severe SAH",
                "recommendations": [
                    "Urgent aneurysm securing",
                    "ICU care",
                    "Nimodipine",
                    "EVD if hydrocephalus",
                    "Aggressive vasospasm management"
                ]
            },
            4: {
                "description": "Stupor, moderate to severe hemiparesis, early decerebrate rigidity",
                "mortality": 80,
                "risk_level": RiskLevel.VERY_HIGH,
                "interpretation": "Grade IV - Critical SAH",
                "recommendations": [
                    "ICU admission",
                    "Aneurysm treatment when stabilized",
                    "ICP monitoring",
                    "EVD placement",
                    "Goals of care discussion"
                ]
            },
            5: {
                "description": "Deep coma, decerebrate rigidity, moribund appearance",
                "mortality": 90,
                "risk_level": RiskLevel.VERY_HIGH,
                "interpretation": "Grade V - Moribund",
                "recommendations": [
                    "Supportive care",
                    "Goals of care discussion",
                    "Palliative care consultation",
                    "Aneurysm treatment only if improvement occurs"
                ]
            }
        }

        grade_info = grade_descriptions[grade]

        warnings = []
        if grade >= 4:
            warnings.append("Poor prognosis - goals of care discussion warranted")

        return CalculatorResult(
            value=f"Grade {grade}",
            interpretation=grade_info["interpretation"],
            risk_level=grade_info["risk_level"],
            reference_range="Grade I-V (I: best, V: worst)",
            recommendations=grade_info["recommendations"],
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "grade": grade,
                "description": grade_info["description"],
                "mortality_percent": grade_info["mortality"]
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "grade": {
                    "type": "integer",
                    "min": 1,
                    "max": 5,
                    "description": "1-5 based on clinical presentation",
                    "required": True
                },
            }
        }


class FisherGradeCalculator(Calculator):
    """
    Fisher Grade (Modified)

    Predicts vasospasm risk after SAH based on CT findings.

    Reference: Fisher CM, et al. Neurosurgery 1980
    """

    def __init__(self):
        super().__init__()
        self.category = "neurology"
        self.description = "SAH vasospasm risk by CT"
        self.citations = ["Fisher CM, et al. Neurosurgery. 1980;6(1):1-9"]

    def calculate(
        self,
        grade: int,
    ) -> CalculatorResult:
        """
        Interpret Fisher grade.

        Args:
            grade: Fisher grade (1-4)
                1: No SAH detected
                2: Diffuse thin SAH (<1mm)
                3: Localized clot or thick SAH (>1mm)
                4: Intracerebral or intraventricular hemorrhage
        """
        self.validate_range(grade, 1, 4, "grade")

        grade_info = {
            1: {
                "description": "No subarachnoid blood detected on CT",
                "vasospasm_risk": "Minimal",
                "risk_level": RiskLevel.LOW,
                "interpretation": "Grade 1 - No visible SAH",
                "recommendations": [
                    "Repeat imaging if high clinical suspicion",
                    "Consider LP if CT negative",
                    "Unlikely to develop vasospasm"
                ]
            },
            2: {
                "description": "Diffuse thin SAH (<1mm thick)",
                "vasospasm_risk": "Low (20-30%)",
                "risk_level": RiskLevel.MODERATE,
                "interpretation": "Grade 2 - Thin diffuse SAH",
                "recommendations": [
                    "Standard SAH management",
                    "Nimodipine",
                    "Monitor for vasospasm",
                    "Serial TCD"
                ]
            },
            3: {
                "description": "Localized clot and/or thick SAH (>1mm)",
                "vasospasm_risk": "High (70-80%)",
                "risk_level": RiskLevel.HIGH,
                "interpretation": "Grade 3 - Thick localized SAH",
                "recommendations": [
                    "Aggressive vasospasm surveillance",
                    "Nimodipine",
                    "Daily TCD",
                    "Maintain euvolemia",
                    "Early intervention for vasospasm"
                ]
            },
            4: {
                "description": "Intracerebral or intraventricular hemorrhage with diffuse or no SAH",
                "vasospasm_risk": "Moderate",
                "risk_level": RiskLevel.MODERATE,
                "interpretation": "Grade 4 - IVH/ICH present",
                "recommendations": [
                    "EVD if hydrocephalus",
                    "Monitor for vasospasm",
                    "Nimodipine",
                    "Manage elevated ICP"
                ]
            }
        }

        info = grade_info[grade]

        warnings = []
        if grade == 3:
            warnings.append("Highest vasospasm risk - aggressive monitoring required")

        return CalculatorResult(
            value=f"Grade {grade}",
            interpretation=info["interpretation"],
            risk_level=info["risk_level"],
            reference_range="Grade 1-4",
            recommendations=info["recommendations"],
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "grade": grade,
                "description": info["description"],
                "vasospasm_risk": info["vasospasm_risk"]
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "grade": {
                    "type": "integer",
                    "min": 1,
                    "max": 4,
                    "description": "1-4 based on CT appearance of blood",
                    "required": True
                },
            }
        }
