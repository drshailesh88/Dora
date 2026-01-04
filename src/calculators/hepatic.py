"""
Hepatic Calculators

Collection of liver function and fibrosis assessment calculators.
"""

import math
from typing import Dict, Any
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError


class MELDCalculator(Calculator):
    """
    MELD Score (Model for End-Stage Liver Disease)

    Predicts 3-month mortality in patients with end-stage liver disease.
    Used for liver transplant prioritization.

    Reference: Kamath PS, et al. Hepatology 2001
    """

    def __init__(self):
        super().__init__()
        self.category = "hepatic"
        self.description = "Liver disease mortality prediction"
        self.citations = ["Kamath PS, et al. Hepatology. 2001;33(2):464-470"]

    def calculate(
        self,
        creatinine: float,
        bilirubin: float,
        inr: float,
        dialysis_twice_in_last_week: bool = False,
    ) -> CalculatorResult:
        """
        Calculate MELD score.

        Args:
            creatinine: Serum creatinine (mg/dL)
            bilirubin: Total bilirubin (mg/dL)
            inr: International Normalized Ratio
            dialysis_twice_in_last_week: Boolean
        """
        self.validate_range(creatinine, 0.1, 20, "creatinine")
        self.validate_range(bilirubin, 0.1, 50, "bilirubin")
        self.validate_range(inr, 0.8, 10, "inr")

        # Floor values at 1.0
        creatinine = max(creatinine, 1.0)
        bilirubin = max(bilirubin, 1.0)
        inr = max(inr, 1.0)

        # If on dialysis, set creatinine to 4
        if dialysis_twice_in_last_week:
            creatinine = 4.0

        # MELD = 3.78×ln(bilirubin) + 11.2×ln(INR) + 9.57×ln(creatinine) + 6.43
        meld_raw = (
            3.78 * math.log(bilirubin)
            + 11.2 * math.log(inr)
            + 9.57 * math.log(creatinine)
            + 6.43
        )

        # Round to integer and cap between 6-40
        meld = int(round(meld_raw * 10))
        meld = max(6, min(40, meld))

        # 3-month mortality estimation
        if meld < 10:
            mortality_3mo = 1.9
            risk_level = RiskLevel.LOW
            interpretation = "Low risk - minimal liver dysfunction"
            recommendations = ["Medical management", "Routine follow-up"]
        elif meld < 20:
            mortality_3mo = 6.0
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate risk - significant liver dysfunction"
            recommendations = [
                "Hepatology referral",
                "Consider transplant evaluation if MELD >15",
                "Manage complications"
            ]
        elif meld < 30:
            mortality_3mo = 19.6
            risk_level = RiskLevel.HIGH
            interpretation = "High risk - severe liver dysfunction"
            recommendations = [
                "Urgent hepatology/transplant referral",
                "Transplant evaluation indicated",
                "Aggressive management of complications"
            ]
        else:
            mortality_3mo = 52.6
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "Very high risk - critical liver dysfunction"
            recommendations = [
                "Urgent transplant evaluation",
                "ICU level care may be needed",
                "Hospice discussion if not transplant candidate"
            ]

        return CalculatorResult(
            value=meld,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="6-40 (6-9: low, 10-19: moderate, 20-29: high, 30-40: very high)",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "three_month_mortality_percent": mortality_3mo,
                "transplant_priority": "Higher scores get priority"
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "creatinine": {"type": "float", "unit": "mg/dL", "min": 0.1, "max": 20, "required": True},
                "bilirubin": {"type": "float", "unit": "mg/dL", "min": 0.1, "max": 50, "required": True},
                "inr": {"type": "float", "min": 0.8, "max": 10, "required": True},
                "dialysis_twice_in_last_week": {"type": "boolean", "default": False, "required": False},
            }
        }


class MELDNaCalculator(Calculator):
    """
    MELD-Na Score

    MELD score incorporating serum sodium.
    Better predictor of waitlist mortality than MELD alone.

    Reference: Kim WR, et al. Hepatology 2008
    """

    def __init__(self):
        super().__init__()
        self.category = "hepatic"
        self.description = "MELD with sodium for transplant priority"
        self.citations = ["Kim WR, et al. Hepatology. 2008;47(4):1267-1276"]

    def calculate(
        self,
        creatinine: float,
        bilirubin: float,
        inr: float,
        sodium: float,
        dialysis_twice_in_last_week: bool = False,
    ) -> CalculatorResult:
        """
        Calculate MELD-Na score.

        Args:
            creatinine: Serum creatinine (mg/dL)
            bilirubin: Total bilirubin (mg/dL)
            inr: International Normalized Ratio
            sodium: Serum sodium (mEq/L)
            dialysis_twice_in_last_week: Boolean
        """
        self.validate_range(creatinine, 0.1, 20, "creatinine")
        self.validate_range(bilirubin, 0.1, 50, "bilirubin")
        self.validate_range(inr, 0.8, 10, "inr")
        self.validate_range(sodium, 100, 200, "sodium")

        # Floor values at 1.0
        creatinine = max(creatinine, 1.0)
        bilirubin = max(bilirubin, 1.0)
        inr = max(inr, 1.0)

        # If on dialysis, set creatinine to 4
        if dialysis_twice_in_last_week:
            creatinine = 4.0

        # Calculate MELD first
        meld_raw = (
            3.78 * math.log(bilirubin)
            + 11.2 * math.log(inr)
            + 9.57 * math.log(creatinine)
            + 6.43
        )
        meld = int(round(meld_raw * 10))
        meld = max(6, min(40, meld))

        # Adjust for sodium if MELD > 11
        if meld > 11:
            # Cap sodium between 125-137
            sodium_adj = max(125, min(137, sodium))
            meld_na = meld + 1.32 * (137 - sodium_adj) - (0.033 * meld * (137 - sodium_adj))
            meld_na = int(round(meld_na))
            meld_na = max(6, min(40, meld_na))
        else:
            meld_na = meld

        # Risk stratification
        if meld_na < 10:
            risk_level = RiskLevel.LOW
            interpretation = "Low risk"
            recommendations = ["Medical management", "Routine follow-up"]
        elif meld_na < 20:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate risk"
            recommendations = [
                "Hepatology referral",
                "Consider transplant evaluation",
                "Manage complications"
            ]
        elif meld_na < 30:
            risk_level = RiskLevel.HIGH
            interpretation = "High risk"
            recommendations = [
                "Urgent transplant evaluation",
                "Aggressive management",
                "Monitor for decompensation"
            ]
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "Very high risk"
            recommendations = [
                "Urgent transplant evaluation",
                "ICU level care may be needed",
                "Frequent monitoring"
            ]

        return CalculatorResult(
            value=meld_na,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="6-40 (higher = higher mortality)",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "meld_without_sodium": meld,
                "sodium_value": sodium,
                "transplant_priority": "Higher scores get priority"
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "creatinine": {"type": "float", "unit": "mg/dL", "min": 0.1, "max": 20, "required": True},
                "bilirubin": {"type": "float", "unit": "mg/dL", "min": 0.1, "max": 50, "required": True},
                "inr": {"type": "float", "min": 0.8, "max": 10, "required": True},
                "sodium": {"type": "float", "unit": "mEq/L", "min": 100, "max": 200, "required": True},
                "dialysis_twice_in_last_week": {"type": "boolean", "default": False, "required": False},
            }
        }


class ChildPughCalculator(Calculator):
    """
    Child-Pugh Score

    Assesses prognosis of chronic liver disease, primarily cirrhosis.

    Reference: Pugh RN, et al. Br J Surg 1973
    """

    def __init__(self):
        super().__init__()
        self.category = "hepatic"
        self.description = "Cirrhosis severity classification"
        self.citations = ["Pugh RN, et al. Br J Surg. 1973;60(8):646-649"]

    def calculate(
        self,
        bilirubin: float,
        albumin: float,
        inr: float,
        ascites: str,
        encephalopathy: str,
    ) -> CalculatorResult:
        """
        Calculate Child-Pugh score.

        Args:
            bilirubin: Total bilirubin (mg/dL)
            albumin: Serum albumin (g/dL)
            inr: International Normalized Ratio
            ascites: 'none', 'mild', 'moderate_severe'
            encephalopathy: 'none', 'grade_1_2', 'grade_3_4'
        """
        self.validate_range(bilirubin, 0.1, 50, "bilirubin")
        self.validate_range(albumin, 0.5, 6, "albumin")
        self.validate_range(inr, 0.8, 10, "inr")
        self.validate_choice(ascites, ["none", "mild", "moderate_severe"], "ascites")
        self.validate_choice(encephalopathy, ["none", "grade_1_2", "grade_3_4"], "encephalopathy")

        points = 0

        # Bilirubin
        if bilirubin < 2:
            points += 1
        elif bilirubin <= 3:
            points += 2
        else:
            points += 3

        # Albumin
        if albumin > 3.5:
            points += 1
        elif albumin >= 2.8:
            points += 2
        else:
            points += 3

        # INR
        if inr < 1.7:
            points += 1
        elif inr <= 2.3:
            points += 2
        else:
            points += 3

        # Ascites
        if ascites == "none":
            points += 1
        elif ascites == "mild":
            points += 2
        else:
            points += 3

        # Encephalopathy
        if encephalopathy == "none":
            points += 1
        elif encephalopathy == "grade_1_2":
            points += 2
        else:
            points += 3

        # Classify
        if points <= 6:
            child_class = "A"
            risk_level = RiskLevel.LOW
            one_year_survival = 100
            two_year_survival = 85
            interpretation = "Well-compensated liver disease"
            recommendations = [
                "Medical management",
                "Treat underlying cause",
                "Routine surveillance"
            ]
        elif points <= 9:
            child_class = "B"
            risk_level = RiskLevel.MODERATE
            one_year_survival = 81
            two_year_survival = 57
            interpretation = "Significant functional compromise"
            recommendations = [
                "Consider transplant evaluation",
                "Aggressive management of complications",
                "Hepatology follow-up"
            ]
        else:
            child_class = "C"
            risk_level = RiskLevel.HIGH
            one_year_survival = 45
            two_year_survival = 35
            interpretation = "Decompensated liver disease"
            recommendations = [
                "Transplant evaluation indicated",
                "Consider hospice if not transplant candidate",
                "Intensive management of complications"
            ]

        warnings = []
        if child_class in ["B", "C"]:
            warnings.append("Surgical risk significantly increased")
        if child_class == "C":
            warnings.append("Contraindication to major surgery except transplant")

        return CalculatorResult(
            value=f"Class {child_class} ({points} points)",
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="Class A (5-6): best, Class B (7-9): moderate, Class C (10-15): worst",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "points": points,
                "class": child_class,
                "one_year_survival_percent": one_year_survival,
                "two_year_survival_percent": two_year_survival
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "bilirubin": {"type": "float", "unit": "mg/dL", "min": 0.1, "max": 50, "required": True},
                "albumin": {"type": "float", "unit": "g/dL", "min": 0.5, "max": 6, "required": True},
                "inr": {"type": "float", "min": 0.8, "max": 10, "required": True},
                "ascites": {"type": "string", "choices": ["none", "mild", "moderate_severe"], "required": True},
                "encephalopathy": {"type": "string", "choices": ["none", "grade_1_2", "grade_3_4"], "required": True},
            }
        }


class FIB4Calculator(Calculator):
    """
    FIB-4 Index

    Non-invasive assessment of liver fibrosis.
    Useful for screening for advanced fibrosis.

    Reference: Sterling RK, et al. Hepatology 2006
    """

    def __init__(self):
        super().__init__()
        self.category = "hepatic"
        self.description = "Non-invasive fibrosis assessment"
        self.citations = ["Sterling RK, et al. Hepatology. 2006;43(6):1317-1325"]

    def calculate(
        self,
        age: int,
        ast: float,
        alt: float,
        platelet_count: float,
    ) -> CalculatorResult:
        """
        Calculate FIB-4 index.

        Args:
            age: Age in years
            ast: AST (U/L)
            alt: ALT (U/L)
            platelet_count: Platelet count (×10⁹/L or ×1000/μL)
        """
        self.validate_range(age, 18, 120, "age")
        self.validate_range(ast, 1, 1000, "ast")
        self.validate_range(alt, 1, 1000, "alt")
        self.validate_range(platelet_count, 10, 1000, "platelet_count")

        # FIB-4 = (Age × AST) / (Platelets × √ALT)
        fib4 = (age * ast) / (platelet_count * math.sqrt(alt))

        # Interpretation (for HCV, may differ for other etiologies)
        if fib4 < 1.45:
            risk_level = RiskLevel.LOW
            interpretation = "Low probability of advanced fibrosis"
            fibrosis_stage = "F0-F1"
            recommendations = [
                "Advanced fibrosis unlikely",
                "Routine monitoring",
                "No need for biopsy in most cases"
            ]
        elif fib4 <= 3.25:
            risk_level = RiskLevel.MODERATE
            interpretation = "Indeterminate - intermediate probability"
            fibrosis_stage = "Indeterminate"
            recommendations = [
                "Consider additional testing (FibroScan, biopsy)",
                "Hepatology referral",
                "Cannot rule out advanced fibrosis"
            ]
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "High probability of advanced fibrosis"
            fibrosis_stage = "F3-F4"
            recommendations = [
                "Advanced fibrosis likely",
                "Hepatology referral recommended",
                "Screen for varices",
                "HCC surveillance if cirrhosis"
            ]

        warnings = ["Less accurate in extremes of age (<35 or >65)", "Developed for hepatitis C - may be less accurate in other liver diseases"]

        return CalculatorResult(
            value=round(fib4, 2),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<1.45: low probability, 1.45-3.25: indeterminate, >3.25: high probability",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings,
            metadata={"likely_fibrosis_stage": fibrosis_stage}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 18, "max": 120, "required": True},
                "ast": {"type": "float", "unit": "U/L", "min": 1, "max": 1000, "required": True},
                "alt": {"type": "float", "unit": "U/L", "min": 1, "max": 1000, "required": True},
                "platelet_count": {"type": "float", "unit": "×10⁹/L", "min": 10, "max": 1000, "required": True},
            }
        }


class APRICalculator(Calculator):
    """
    APRI Score (AST to Platelet Ratio Index)

    Simple non-invasive marker of hepatic fibrosis.

    Reference: Wai CT, et al. Hepatology 2003
    """

    def __init__(self):
        super().__init__()
        self.category = "hepatic"
        self.description = "Simple fibrosis marker"
        self.citations = ["Wai CT, et al. Hepatology. 2003;38(2):518-526"]

    def calculate(
        self,
        ast: float,
        platelet_count: float,
        ast_upper_limit_normal: float = 40,
    ) -> CalculatorResult:
        """
        Calculate APRI score.

        Args:
            ast: AST (U/L)
            platelet_count: Platelet count (×10⁹/L or ×1000/μL)
            ast_upper_limit_normal: ULN for AST (default 40 U/L)
        """
        self.validate_range(ast, 1, 1000, "ast")
        self.validate_range(platelet_count, 10, 1000, "platelet_count")
        self.validate_range(ast_upper_limit_normal, 20, 100, "ast_upper_limit_normal")

        # APRI = [(AST / ULN) / Platelet count] × 100
        apri = ((ast / ast_upper_limit_normal) / platelet_count) * 100

        # Interpretation for significant fibrosis (F2-F4)
        if apri < 0.5:
            risk_level = RiskLevel.LOW
            interpretation = "Low probability of significant fibrosis"
            fibrosis_likelihood = "F0-F1 likely"
            recommendations = [
                "Significant fibrosis unlikely",
                "Routine monitoring",
                "No biopsy needed in most cases"
            ]
        elif apri <= 1.5:
            risk_level = RiskLevel.MODERATE
            interpretation = "Indeterminate - cannot exclude fibrosis"
            fibrosis_likelihood = "Indeterminate"
            recommendations = [
                "Consider additional testing",
                "FibroScan or liver biopsy may be helpful",
                "Hepatology consultation"
            ]
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "High probability of significant fibrosis/cirrhosis"
            fibrosis_likelihood = "F3-F4 likely"
            recommendations = [
                "Advanced fibrosis/cirrhosis likely",
                "Hepatology referral",
                "Screen for varices",
                "HCC surveillance"
            ]

        # Additional interpretation for cirrhosis (>2.0 suggests cirrhosis)
        if apri > 2.0:
            cirrhosis_note = "APRI >2.0 suggests cirrhosis"
        else:
            cirrhosis_note = None

        return CalculatorResult(
            value=round(apri, 2),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<0.5: low probability, 0.5-1.5: indeterminate, >1.5: high probability",
            recommendations=recommendations,
            citations=self.citations,
            warnings=[cirrhosis_note] if cirrhosis_note else None,
            metadata={"fibrosis_likelihood": fibrosis_likelihood}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "ast": {"type": "float", "unit": "U/L", "min": 1, "max": 1000, "required": True},
                "platelet_count": {"type": "float", "unit": "×10⁹/L", "min": 10, "max": 1000, "required": True},
                "ast_upper_limit_normal": {"type": "float", "unit": "U/L", "min": 20, "max": 100, "default": 40, "required": False},
            }
        }
