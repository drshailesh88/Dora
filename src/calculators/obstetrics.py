"""
Obstetrics Calculators

Collection of obstetric assessment calculators.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError


class EstimatedDueDateCalculator(Calculator):
    """
    Estimated Due Date (EDD)

    Calculates estimated due date from last menstrual period.

    Reference: Naegele's Rule
    """

    def __init__(self):
        super().__init__()
        self.category = "obstetrics"
        self.description = "Pregnancy due date calculation"
        self.citations = ["Naegele's Rule"]

    def calculate(
        self,
        lmp_date: str,
        cycle_length: int = 28,
    ) -> CalculatorResult:
        """
        Calculate estimated due date.

        Args:
            lmp_date: Last menstrual period date (YYYY-MM-DD)
            cycle_length: Menstrual cycle length in days (default 28)
        """
        self.validate_range(cycle_length, 21, 35, "cycle_length")

        try:
            lmp = datetime.strptime(lmp_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("lmp_date must be in YYYY-MM-DD format")

        # Naegele's Rule: LMP + 280 days (40 weeks)
        # Adjust for cycle length: if cycle > 28, add difference
        adjustment = cycle_length - 28
        edd = lmp + timedelta(days=280 + adjustment)

        # Calculate current gestational age if today
        today = datetime.now()
        if lmp <= today:
            days_pregnant = (today - lmp).days
            weeks = days_pregnant // 7
            days = days_pregnant % 7
            gestational_age = f"{weeks} weeks {days} days"

            # Trimester
            if weeks < 13:
                trimester = "First trimester"
            elif weeks < 27:
                trimester = "Second trimester"
            elif weeks < 40:
                trimester = "Third trimester"
            else:
                trimester = "Post-term"
        else:
            gestational_age = "Future LMP date"
            trimester = "N/A"

        # Determine if post-term
        if today > edd + timedelta(days=14):
            risk_level = RiskLevel.HIGH
            interpretation = "Post-term pregnancy (>42 weeks)"
            recommendations = [
                "Immediate obstetric evaluation",
                "Consider induction of labor",
                "Fetal monitoring",
                "Biophysical profile"
            ]
        elif today > edd:
            risk_level = RiskLevel.MODERATE
            interpretation = "Past due date"
            recommendations = [
                "Obstetric follow-up",
                "Fetal monitoring",
                "Discuss induction timing",
                "NST and/or AFI"
            ]
        else:
            risk_level = RiskLevel.LOW
            interpretation = "Normal pregnancy progression"
            recommendations = [
                "Routine prenatal care",
                "Monitor for complications",
                "Patient education on warning signs"
            ]

        return CalculatorResult(
            value=edd.strftime("%Y-%m-%d"),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="40 weeks from LMP",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "lmp": lmp_date,
                "edd": edd.strftime("%Y-%m-%d"),
                "current_gestational_age": gestational_age if lmp <= today else None,
                "trimester": trimester,
                "cycle_length": cycle_length
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "lmp_date": {"type": "string", "format": "YYYY-MM-DD", "required": True},
                "cycle_length": {"type": "integer", "unit": "days", "min": 21, "max": 35, "default": 28, "required": False},
            }
        }


class BishopScoreCalculator(Calculator):
    """
    Bishop Score

    Predicts likelihood of successful vaginal delivery induction.

    Reference: Bishop EH. Obstet Gynecol 1964
    """

    def __init__(self):
        super().__init__()
        self.category = "obstetrics"
        self.description = "Cervical favorability for induction"
        self.citations = ["Bishop EH. Obstet Gynecol. 1964;24:266-268"]

    def calculate(
        self,
        dilation_cm: float,
        effacement_percent: int,
        station: int,
        consistency: str,
        position: str,
    ) -> CalculatorResult:
        """
        Calculate Bishop score.

        Args:
            dilation_cm: Cervical dilation (0-10 cm)
            effacement_percent: Cervical effacement (0-100%)
            station: Fetal station (-3 to +3)
            consistency: 'firm', 'medium', or 'soft'
            position: 'posterior', 'mid', or 'anterior'
        """
        self.validate_range(dilation_cm, 0, 10, "dilation_cm")
        self.validate_range(effacement_percent, 0, 100, "effacement_percent")
        self.validate_range(station, -3, 3, "station")
        self.validate_choice(consistency, ["firm", "medium", "soft"], "consistency")
        self.validate_choice(position, ["posterior", "mid", "anterior"], "position")

        score = 0

        # Dilation (0-3 points)
        if dilation_cm >= 5:
            score += 3
        elif dilation_cm >= 3:
            score += 2
        elif dilation_cm >= 1:
            score += 1

        # Effacement (0-3 points)
        if effacement_percent >= 80:
            score += 3
        elif effacement_percent >= 50:
            score += 2
        elif effacement_percent >= 30:
            score += 1

        # Station (0-3 points)
        if station >= 1:
            score += 3
        elif station >= 0:
            score += 2
        elif station >= -1:
            score += 1

        # Consistency (0-2 points)
        if consistency == "soft":
            score += 2
        elif consistency == "medium":
            score += 1

        # Position (0-2 points)
        if position == "anterior":
            score += 2
        elif position == "mid":
            score += 1

        # Interpretation
        if score >= 9:
            risk_level = RiskLevel.LOW
            success_rate = ">90%"
            interpretation = "Highly favorable cervix"
            recommendations = [
                "Excellent candidate for induction",
                "High likelihood of vaginal delivery",
                "May proceed with oxytocin or amniotomy"
            ]
        elif score >= 6:
            risk_level = RiskLevel.LOW
            success_rate = "70-80%"
            interpretation = "Favorable cervix"
            recommendations = [
                "Good candidate for induction",
                "Likely successful vaginal delivery",
                "Standard induction protocol"
            ]
        elif score >= 4:
            risk_level = RiskLevel.MODERATE
            success_rate = "50-60%"
            interpretation = "Moderately favorable cervix"
            recommendations = [
                "May attempt induction",
                "Consider cervical ripening first",
                "Inform patient of cesarean risk"
            ]
        else:
            risk_level = RiskLevel.HIGH
            success_rate = "<40%"
            interpretation = "Unfavorable cervix"
            recommendations = [
                "Cervical ripening recommended before oxytocin",
                "Consider prostaglandin gel or Foley catheter",
                "Higher risk of cesarean delivery",
                "Counsel patient on expectations"
            ]

        return CalculatorResult(
            value=score,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="≥9: highly favorable, 6-8: favorable, 4-5: intermediate, <4: unfavorable",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "max_score": 13,
                "success_rate": success_rate,
                "components": {
                    "dilation": dilation_cm,
                    "effacement": effacement_percent,
                    "station": station,
                    "consistency": consistency,
                    "position": position
                }
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "dilation_cm": {"type": "float", "unit": "cm", "min": 0, "max": 10, "required": True},
                "effacement_percent": {"type": "integer", "unit": "%", "min": 0, "max": 100, "required": True},
                "station": {"type": "integer", "min": -3, "max": 3, "required": True},
                "consistency": {"type": "string", "choices": ["firm", "medium", "soft"], "required": True},
                "position": {"type": "string", "choices": ["posterior", "mid", "anterior"], "required": True},
            }
        }


class ApgarScoreCalculator(Calculator):
    """
    Apgar Score

    Rapid assessment of newborn health at 1 and 5 minutes.

    Reference: Apgar V. Curr Res Anesth Analg 1953
    """

    def __init__(self):
        super().__init__()
        self.category = "obstetrics"
        self.description = "Newborn health assessment"
        self.citations = ["Apgar V. Curr Res Anesth Analg. 1953;32(4):260-267"]

    def calculate(
        self,
        appearance: int,
        pulse: int,
        grimace: int,
        activity: int,
        respiration: int,
        time_point: str = "1_minute",
    ) -> CalculatorResult:
        """
        Calculate Apgar score.

        Args:
            appearance: Skin color (0-2): 0=blue/pale, 1=body pink/extremities blue, 2=completely pink
            pulse: Heart rate (0-2): 0=absent, 1=<100, 2=≥100
            grimace: Reflex irritability (0-2): 0=no response, 1=grimace, 2=cry/active withdrawal
            activity: Muscle tone (0-2): 0=limp, 1=some flexion, 2=active motion
            respiration: Breathing (0-2): 0=absent, 1=slow/irregular, 2=good/crying
            time_point: '1_minute', '5_minute', or '10_minute'
        """
        self.validate_range(appearance, 0, 2, "appearance")
        self.validate_range(pulse, 0, 2, "pulse")
        self.validate_range(grimace, 0, 2, "grimace")
        self.validate_range(activity, 0, 2, "activity")
        self.validate_range(respiration, 0, 2, "respiration")
        self.validate_choice(time_point, ["1_minute", "5_minute", "10_minute"], "time_point")

        score = appearance + pulse + grimace + activity + respiration

        # Interpretation varies slightly by time point
        if score >= 7:
            risk_level = RiskLevel.LOW
            interpretation = "Normal - good condition"
            if time_point == "1_minute":
                recommendations = [
                    "Routine newborn care",
                    "Reassess at 5 minutes",
                    "No intervention needed"
                ]
            else:
                recommendations = [
                    "Normal newborn transition",
                    "Continue routine care"
                ]
        elif score >= 4:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderately depressed - requires intervention"
            if time_point == "1_minute":
                recommendations = [
                    "Stimulation and oxygen",
                    "Ensure adequate ventilation",
                    "Reassess at 5 minutes",
                    "Prepare for advanced resuscitation"
                ]
            else:
                recommendations = [
                    "Continue resuscitation",
                    "Consider intubation if not improving",
                    "NICU consultation",
                    "Investigate causes"
                ]
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "Severely depressed - requires immediate resuscitation"
            recommendations = [
                "Immediate resuscitation per NRP",
                "Positive pressure ventilation",
                "Consider intubation",
                "Chest compressions if HR <60",
                "Epinephrine if indicated",
                "NICU admission"
            ]

        warnings = []
        if time_point == "5_minute" and score < 7:
            warnings.append("Low 5-minute Apgar associated with increased morbidity - continue resuscitation")
        if score < 4:
            warnings.append("Severe depression - activate full resuscitation team")

        return CalculatorResult(
            value=score,
            interpretation=f"{time_point.replace('_', ' ').title()} Apgar: {interpretation}",
            risk_level=risk_level,
            reference_range="7-10: normal, 4-6: moderate depression, 0-3: severe depression",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "max_score": 10,
                "time_point": time_point,
                "components": {
                    "appearance": appearance,
                    "pulse": pulse,
                    "grimace": grimace,
                    "activity": activity,
                    "respiration": respiration
                }
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "appearance": {"type": "integer", "min": 0, "max": 2, "description": "0=blue/pale, 1=acrocyanosis, 2=pink", "required": True},
                "pulse": {"type": "integer", "min": 0, "max": 2, "description": "0=absent, 1=<100, 2=≥100", "required": True},
                "grimace": {"type": "integer", "min": 0, "max": 2, "description": "0=none, 1=grimace, 2=cry", "required": True},
                "activity": {"type": "integer", "min": 0, "max": 2, "description": "0=limp, 1=some flexion, 2=active", "required": True},
                "respiration": {"type": "integer", "min": 0, "max": 2, "description": "0=absent, 1=slow, 2=good", "required": True},
                "time_point": {"type": "string", "choices": ["1_minute", "5_minute", "10_minute"], "default": "1_minute", "required": False},
            }
        }
