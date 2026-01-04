"""
Drug Dosing Assistant for Clinical Decision Support

Provides evidence-based dosing recommendations with adjustments for:
- Renal impairment
- Hepatic impairment
- Pediatric patients
- Geriatric patients
- Drug-drug interactions

MEDICAL DISCLAIMER:
This tool is for educational and clinical decision support purposes only.
Always verify dosing with current drug references and consider patient-specific factors.
Consult pharmacy for complex dosing questions.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class RenalFunction(Enum):
    """Renal function categories"""
    NORMAL = "normal"          # CrCl ≥90
    MILD = "mild"              # CrCl 60-89
    MODERATE = "moderate"      # CrCl 30-59
    SEVERE = "severe"          # CrCl 15-29
    ESRD = "esrd"              # CrCl <15 or dialysis


class HepaticFunction(Enum):
    """Hepatic function categories (Child-Pugh)"""
    NORMAL = "normal"
    CHILD_A = "child_a"  # 5-6 points
    CHILD_B = "child_b"  # 7-9 points
    CHILD_C = "child_c"  # 10-15 points


@dataclass
class DosingRecommendation:
    """Drug dosing recommendation"""
    drug_name: str
    indication: str
    dose: str
    frequency: str
    route: str
    duration: Optional[str] = None
    max_dose: Optional[str] = None
    adjustments: List[str] = None
    monitoring: List[str] = None
    warnings: List[str] = None
    references: List[str] = None

    def __post_init__(self):
        if self.adjustments is None:
            self.adjustments = []
        if self.monitoring is None:
            self.monitoring = []
        if self.warnings is None:
            self.warnings = []
        if self.references is None:
            self.references = []


class DosingCalculator:
    """
    Calculate appropriate drug dosing with patient-specific adjustments.
    """

    def __init__(self):
        self._initialize_drug_database()

    def _initialize_drug_database(self):
        """Initialize drug dosing database"""
        # This would ideally be a proper database or API
        # For now, implementing key drugs with complex dosing
        pass

    def calculate_creatinine_clearance(
        self,
        age: int,
        weight_kg: float,
        serum_cr: float,
        gender: str
    ) -> float:
        """
        Calculate creatinine clearance using Cockcroft-Gault equation.

        Args:
            age: Patient age in years
            weight_kg: Patient weight in kg
            serum_cr: Serum creatinine in mg/dL
            gender: "M" or "F"

        Returns:
            Creatinine clearance in mL/min
        """
        crcl = ((140 - age) * weight_kg) / (72 * serum_cr)

        if gender == 'F':
            crcl *= 0.85

        return round(crcl, 1)

    def calculate_ibw(self, height_cm: float, gender: str) -> float:
        """
        Calculate Ideal Body Weight (Devine formula).

        Args:
            height_cm: Height in centimeters
            gender: "M" or "F"

        Returns:
            Ideal body weight in kg
        """
        height_inches = height_cm / 2.54

        if gender == 'M':
            ibw = 50 + 2.3 * (height_inches - 60)
        else:
            ibw = 45.5 + 2.3 * (height_inches - 60)

        return max(ibw, 0)

    def categorize_renal_function(self, crcl: float) -> RenalFunction:
        """Categorize renal function based on CrCl"""
        if crcl >= 90:
            return RenalFunction.NORMAL
        elif crcl >= 60:
            return RenalFunction.MILD
        elif crcl >= 30:
            return RenalFunction.MODERATE
        elif crcl >= 15:
            return RenalFunction.SEVERE
        else:
            return RenalFunction.ESRD

    def dose_vancomycin(
        self,
        indication: str,
        weight_kg: float,
        crcl: float,
        **kwargs
    ) -> DosingRecommendation:
        """
        Vancomycin dosing with renal adjustment.

        Target trough: 10-15 mcg/mL (most infections), 15-20 mcg/mL (serious infections)
        """
        # Loading dose: 25-30 mg/kg for serious infections
        loading_dose = round(25 * weight_kg, 0)  # Conservative 25 mg/kg

        # Maintenance dose based on renal function
        if crcl >= 80:
            dose = "15-20 mg/kg"
            interval = "q8-12h"
        elif crcl >= 50:
            dose = "15-20 mg/kg"
            interval = "q12h"
        elif crcl >= 30:
            dose = "15-20 mg/kg"
            interval = "q24h"
        elif crcl >= 15:
            dose = "15-20 mg/kg"
            interval = "q48h"
        else:
            dose = "Dose after dialysis"
            interval = "Post-HD: 10-15 mg/kg"

        return DosingRecommendation(
            drug_name="Vancomycin",
            indication=indication,
            dose=f"Loading: {loading_dose} mg; Maintenance: {dose}",
            frequency=interval,
            route="IV",
            max_dose="Max single dose: 2000 mg (unless obese)",
            adjustments=[
                f"CrCl {crcl} mL/min - adjusted interval",
                "Use actual body weight unless obese",
                "Consider continuous infusion for severe infections"
            ],
            monitoring=[
                "Trough level before 4th dose (target 10-20 mcg/mL depending on infection)",
                "Renal function (SCr) every 2-3 days",
                "Ototoxicity symptoms",
                "Red man syndrome (infuse over ≥60 min)"
            ],
            warnings=[
                "Nephrotoxicity - avoid concurrent aminoglycosides, NSAIDs if possible",
                "Ototoxicity - especially with loop diuretics",
                "Red man syndrome - histamine release, slow infusion"
            ],
            references=[
                "Vancomycin Therapeutic Guidelines (ASHP/IDSA/SIDP 2020)",
                "Rybak et al. Am J Health Syst Pharm 2020"
            ]
        )

    def dose_gentamicin(
        self,
        indication: str,
        weight_kg: float,
        height_cm: float,
        crcl: float,
        gender: str,
        **kwargs
    ) -> DosingRecommendation:
        """
        Gentamicin dosing (extended-interval dosing preferred).

        Uses Hartford nomogram for extended-interval dosing.
        """
        # Use IBW for non-obese, adjust for obesity
        ibw = self.calculate_ibw(height_cm, gender)
        dosing_weight = weight_kg if weight_kg <= ibw * 1.25 else ibw + 0.4 * (weight_kg - ibw)

        # Extended-interval dosing (preferred)
        if crcl >= 60:
            dose = round(5 * dosing_weight, 0)  # 5-7 mg/kg
            interval = "q24h"
            monitoring_note = "Hartford nomogram: Check level 6-14h after 1st dose"
        elif crcl >= 40:
            dose = round(5 * dosing_weight, 0)
            interval = "q36h"
            monitoring_note = "Check peak and trough levels"
        elif crcl >= 20:
            dose = round(5 * dosing_weight, 0)
            interval = "q48h"
            monitoring_note = "Check peak and trough levels"
        else:
            dose = "Redose based on levels"
            interval = "Give loading dose, then redose when level <1 mcg/mL"
            monitoring_note = "Check levels frequently"

        return DosingRecommendation(
            drug_name="Gentamicin",
            indication=indication,
            dose=f"{dose} mg",
            frequency=interval,
            route="IV",
            duration="Typically 3-7 days (shortest duration possible)",
            adjustments=[
                f"CrCl {crcl} mL/min",
                f"Dosing weight: {round(dosing_weight, 1)} kg (IBW-based with obesity adjustment)",
                "Extended-interval dosing preferred for most indications"
            ],
            monitoring=[
                monitoring_note,
                "Renal function (SCr) every 2-3 days",
                "Ototoxicity symptoms (tinnitus, vertigo, hearing loss)",
                "Target peak: 20-30 mcg/mL; trough: <1 mcg/mL (extended-interval)"
            ],
            warnings=[
                "NEPHROTOXICITY - risk increases with duration >5 days",
                "OTOTOXICITY - often irreversible",
                "Avoid concurrent vancomycin, amphotericin, loop diuretics if possible",
                "Use shortest duration possible"
            ],
            references=[
                "Hartford Nomogram",
                "Once-Daily Aminoglycoside Dosing (Nicolau et al. 1995)"
            ]
        )

    def dose_warfarin(
        self,
        indication: str,
        age: int,
        weight_kg: float,
        interacting_meds: List[str] = None,
        **kwargs
    ) -> DosingRecommendation:
        """
        Warfarin dosing and monitoring recommendations.
        """
        # Initial dosing (lower in elderly, lower BMI)
        if age >= 75 or weight_kg < 60:
            initial_dose = "2.5 mg daily"
        else:
            initial_dose = "5 mg daily"

        # Target INR based on indication
        if indication.lower() in ['dvt', 'pe', 'afib', 'atrial fibrillation']:
            target_inr = "2-3"
        elif indication.lower() in ['mechanical valve', 'aortic valve', 'mitral valve']:
            target_inr = "2.5-3.5"
        else:
            target_inr = "2-3 (verify indication)"

        warnings = [
            "BLEEDING RISK - especially if age >65, prior bleed, uncontrolled HTN",
            "Drug-drug interactions - MANY (see full list)",
            "Dietary vitamin K affects INR",
            "Narrow therapeutic window"
        ]

        if interacting_meds:
            warnings.append(f"Patient on: {', '.join(interacting_meds)} - check interactions")

        return DosingRecommendation(
            drug_name="Warfarin",
            indication=indication,
            dose=initial_dose,
            frequency="Once daily",
            route="PO",
            duration="Variable based on indication",
            adjustments=[
                "Adjust dose based on INR response",
                "Lower starting dose if age >75, weight <60 kg, liver disease",
                "Consider VKORC1/CYP2C9 genotyping if available"
            ],
            monitoring=[
                f"Target INR: {target_inr}",
                "Check INR: Day 3-4, then 1-2x/week x 1-2 weeks, then monthly when stable",
                "CBC baseline and periodically",
                "Signs of bleeding"
            ],
            warnings=warnings,
            references=[
                "ACCP Antithrombotic Guidelines 2012",
                "Warfarin Dosing Calculator (warfarindosing.org)"
            ]
        )

    def dose_heparin_iv(
        self,
        indication: str,
        weight_kg: float,
        **kwargs
    ) -> DosingRecommendation:
        """
        Unfractionated heparin IV dosing (weight-based protocol).
        """
        # Weight-based protocol for VTE
        bolus = round(80 * weight_kg, 0)
        infusion_rate = round(18 * weight_kg, 0)

        return DosingRecommendation(
            drug_name="Heparin (Unfractionated)",
            indication=indication,
            dose=f"Bolus: {bolus} units; Infusion: {infusion_rate} units/hour",
            frequency="Continuous IV infusion",
            route="IV",
            duration="Until transition to oral anticoagulant (overlap 5 days)",
            adjustments=[
                "Adjust based on aPTT (target 1.5-2.5x control, typically 60-80 sec)",
                "Check aPTT 6h after bolus and rate changes",
                "Use protocol-based adjustments"
            ],
            monitoring=[
                "aPTT every 6h until therapeutic x2, then daily",
                "Platelet count on Day 3, 5, 7 (HIT risk)",
                "Signs of bleeding",
                "CBC baseline"
            ],
            warnings=[
                "HIT (Heparin-Induced Thrombocytopenia) - check platelets on Day 3+",
                "Bleeding risk",
                "Osteoporosis with prolonged use",
                "Reversal: Protamine sulfate"
            ],
            references=[
                "Weight-Based Heparin Dosing Protocol (Raschke et al. 1993)"
            ]
        )

    def dose_enoxaparin(
        self,
        indication: str,
        weight_kg: float,
        crcl: float,
        **kwargs
    ) -> DosingRecommendation:
        """
        Enoxaparin (Lovenox) dosing with renal adjustment.
        """
        # Dosing based on indication
        if indication.lower() in ['dvt treatment', 'pe treatment', 'acs']:
            if indication.lower() == 'acs':
                dose = "1 mg/kg"
                frequency = "q12h"
            else:
                dose = "1 mg/kg q12h OR 1.5 mg/kg q24h"
                frequency = "q12h or q24h"
        elif indication.lower() in ['dvt prophylaxis', 'prophylaxis']:
            dose = "40 mg"
            frequency = "daily"
        else:
            dose = "Verify indication for appropriate dosing"
            frequency = "Variable"

        # Renal adjustment
        adjustments = []
        if crcl < 30:
            if indication.lower() in ['dvt treatment', 'pe treatment']:
                dose = "1 mg/kg"
                frequency = "q24h (reduce from q12h)"
                adjustments.append("RENAL DOSE REDUCTION: CrCl <30 - give q24h instead of q12h")
            elif indication.lower() == 'prophylaxis':
                dose = "30 mg"
                frequency = "daily (reduce from 40 mg)"
                adjustments.append("RENAL DOSE REDUCTION: CrCl <30 - give 30 mg daily")

        warnings = [
            "Contraindicated if CrCl <15 (consider UFH instead)",
            "Bleeding risk",
            "Spinal/epidural hematoma risk with neuraxial anesthesia",
            "No routine monitoring needed (unlike UFH)"
        ]

        monitoring = [
            "No routine anti-Xa monitoring needed",
            "Anti-Xa levels if: obese, renal impairment, pregnancy (target 0.5-1.0 for q12h dosing)",
            "CBC, platelet count baseline and periodically",
            "Renal function"
        ]

        return DosingRecommendation(
            drug_name="Enoxaparin (Lovenox)",
            indication=indication,
            dose=dose,
            frequency=frequency,
            route="Subcutaneous",
            duration="Variable by indication",
            adjustments=adjustments + [f"CrCl {crcl} mL/min"],
            monitoring=monitoring,
            warnings=warnings,
            references=[
                "Enoxaparin Package Insert",
                "ACCP Antithrombotic Guidelines"
            ]
        )

    def dose_digoxin(
        self,
        indication: str,
        weight_kg: float,
        crcl: float,
        age: int,
        **kwargs
    ) -> DosingRecommendation:
        """
        Digoxin dosing with renal adjustment.
        """
        # Loading dose (if needed for rapid effect)
        loading_dose = round(10 * weight_kg, 0)  # 10-15 mcg/kg total, give in divided doses

        # Maintenance dose based on renal function
        if crcl >= 60:
            maintenance = "0.125-0.25 mg"
            interval = "daily"
        elif crcl >= 30:
            maintenance = "0.125 mg"
            interval = "daily"
        elif crcl >= 15:
            maintenance = "0.125 mg"
            interval = "every other day"
        else:
            maintenance = "0.0625-0.125 mg"
            interval = "every other day or less frequently"

        # Lower dose in elderly
        if age >= 70:
            maintenance = "0.0625-0.125 mg (reduce dose in elderly)"

        return DosingRecommendation(
            drug_name="Digoxin",
            indication=indication,
            dose=f"Loading (if needed): {loading_dose} mcg in divided doses; Maintenance: {maintenance}",
            frequency=interval,
            route="PO or IV",
            adjustments=[
                f"CrCl {crcl} mL/min - dose adjusted",
                "Elderly: use lower doses",
                "Lean body weight for dosing in obesity"
            ],
            monitoring=[
                "Digoxin level: 0.5-2.0 ng/mL (target 0.5-1.0 for AFib rate control)",
                "Check level 6-8h post-dose at steady state (5-7 days)",
                "Renal function, electrolytes (K, Mg)",
                "ECG (look for toxicity: bradycardia, heart block, arrhythmias)"
            ],
            warnings=[
                "NARROW THERAPEUTIC INDEX",
                "Toxicity risk: hypokalemia, hypomagnesemia, hypercalcemia",
                "Drug interactions: amiodarone, verapamil, quinidine increase levels",
                "Toxicity symptoms: nausea, confusion, vision changes (yellow halos), arrhythmias",
                "Reversal: Digoxin Fab"
            ],
            references=[
                "ACC/AHA Heart Failure Guidelines",
                "Digoxin Package Insert"
            ]
        )

    def dose_phenytoin(
        self,
        indication: str,
        weight_kg: float,
        albumin: Optional[float] = None,
        hepatic_function: HepaticFunction = HepaticFunction.NORMAL,
        **kwargs
    ) -> DosingRecommendation:
        """
        Phenytoin dosing (complex due to protein binding and non-linear kinetics).
        """
        # Loading dose for status epilepticus
        loading_dose = round(20 * weight_kg, 0)  # 15-20 mg/kg

        # Maintenance dose
        maintenance = "300 mg (5 mg/kg/day)"

        adjustments = []

        # Correct level for low albumin (phenytoin is highly protein-bound)
        if albumin and albumin < 3.5:
            correction_note = f"Albumin {albumin} - use corrected phenytoin level"
            adjustments.append(correction_note)
            adjustments.append("Corrected phenytoin = measured / (0.2 x albumin + 0.1)")

        # Hepatic adjustment
        if hepatic_function != HepaticFunction.NORMAL:
            adjustments.append("HEPATIC IMPAIRMENT - reduce dose, monitor levels closely")
            maintenance = "200-250 mg daily (reduce dose)"

        return DosingRecommendation(
            drug_name="Phenytoin (Dilantin)",
            indication=indication,
            dose=f"Loading: {loading_dose} mg IV (max 50 mg/min); Maintenance: {maintenance}",
            frequency="Daily or divided BID-TID",
            route="PO or IV",
            adjustments=adjustments,
            monitoring=[
                "Phenytoin level: 10-20 mcg/mL (free level 1-2 mcg/mL)",
                "Check trough level at steady state (7-10 days)",
                "Correct for albumin if <3.5",
                "CBC, LFTs baseline and periodically",
                "Signs of toxicity: nystagmus, ataxia, confusion"
            ],
            warnings=[
                "NON-LINEAR KINETICS - small dose changes can cause large level changes",
                "Highly protein-bound - correct level for low albumin",
                "Drug interactions: MANY (induces CYP450)",
                "Purple glove syndrome with IV extravasation",
                "Hypotension, bradycardia with rapid IV infusion (max 50 mg/min)",
                "Steven-Johnson syndrome risk (especially HLA-B*1502 carriers)"
            ],
            references=[
                "Epilepsy Foundation Guidelines",
                "Winter-Tozer equation for albumin correction"
            ]
        )

    def calculate_pediatric_dose(
        self,
        drug: str,
        adult_dose_mg: float,
        child_weight_kg: float,
        method: str = "BSA"  # BSA or Clark's rule
    ) -> float:
        """
        Calculate pediatric dose using BSA or Clark's rule.

        BSA method (preferred): Dose = Adult dose x (BSA_child / 1.73)
        Clark's rule: Dose = Adult dose x (Weight_kg / 70)
        """
        if method == "BSA":
            # Simplified BSA (Mosteller formula): sqrt(height_cm * weight_kg / 3600)
            # For estimation, assume average height for weight
            bsa = math.sqrt(child_weight_kg / 3600 * 100)  # Rough estimate
            pediatric_dose = adult_dose_mg * (bsa / 1.73)
        else:  # Clark's rule
            pediatric_dose = adult_dose_mg * (child_weight_kg / 70)

        return round(pediatric_dose, 2)


def get_dosing_recommendation(
    drug_name: str,
    indication: str,
    patient_data: Dict,
    **kwargs
) -> Dict:
    """
    Get dosing recommendation for a specific drug.

    Args:
        drug_name: Name of the drug
        indication: Clinical indication
        patient_data: Dictionary with patient parameters
            Required keys vary by drug but may include:
            - weight_kg, height_cm, age, gender
            - serum_cr, crcl
            - albumin (for highly protein-bound drugs)
            - interacting_meds (list)

    Returns:
        Dictionary with dosing recommendation

    Example:
        >>> rec = get_dosing_recommendation(
        ...     drug_name="vancomycin",
        ...     indication="MRSA pneumonia",
        ...     patient_data={
        ...         'weight_kg': 70,
        ...         'serum_cr': 1.2,
        ...         'age': 65,
        ...         'gender': 'M'
        ...     }
        ... )
    """
    calculator = DosingCalculator()

    # Calculate CrCl if not provided but serum_cr is available
    if 'crcl' not in patient_data and all(k in patient_data for k in ['age', 'weight_kg', 'serum_cr', 'gender']):
        patient_data['crcl'] = calculator.calculate_creatinine_clearance(
            age=patient_data['age'],
            weight_kg=patient_data['weight_kg'],
            serum_cr=patient_data['serum_cr'],
            gender=patient_data['gender']
        )

    # Route to appropriate dosing function
    drug_lower = drug_name.lower().replace(' ', '_')

    dosing_methods = {
        'vancomycin': calculator.dose_vancomycin,
        'gentamicin': calculator.dose_gentamicin,
        'tobramycin': calculator.dose_gentamicin,  # Similar dosing
        'amikacin': calculator.dose_gentamicin,    # Similar dosing (dose is 15 mg/kg)
        'warfarin': calculator.dose_warfarin,
        'coumadin': calculator.dose_warfarin,
        'heparin': calculator.dose_heparin_iv,
        'enoxaparin': calculator.dose_enoxaparin,
        'lovenox': calculator.dose_enoxaparin,
        'digoxin': calculator.dose_digoxin,
        'lanoxin': calculator.dose_digoxin,
        'phenytoin': calculator.dose_phenytoin,
        'dilantin': calculator.dose_phenytoin,
    }

    method = dosing_methods.get(drug_lower)

    if not method:
        return {
            'error': f'Dosing calculator not available for {drug_name}',
            'suggestion': 'Consult drug reference or pharmacy'
        }

    recommendation = method(indication=indication, **patient_data, **kwargs)

    return {
        'drug_name': recommendation.drug_name,
        'indication': recommendation.indication,
        'dose': recommendation.dose,
        'frequency': recommendation.frequency,
        'route': recommendation.route,
        'duration': recommendation.duration,
        'max_dose': recommendation.max_dose,
        'adjustments': recommendation.adjustments,
        'monitoring': recommendation.monitoring,
        'warnings': recommendation.warnings,
        'references': recommendation.references,
        'calculated_crcl': patient_data.get('crcl')
    }
