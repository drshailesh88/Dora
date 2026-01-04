"""
Antibiotic Stewardship Module for Clinical Decision Support

Provides evidence-based antibiotic recommendations with:
- Infection-specific antibiotic selection
- Spectrum coverage guidance
- De-escalation strategies
- Duration recommendations
- Resistance pattern considerations

MEDICAL DISCLAIMER:
This tool is for educational and clinical decision support purposes only.
Always consider local antibiograms, patient allergies, and consult infectious disease
specialists for complex cases. Verify dosing with current references.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class InfectionSeverity(Enum):
    """Severity of infection"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"


@dataclass
class AntibioticRecommendation:
    """Antibiotic recommendation for specific infection"""
    infection_type: str
    severity: InfectionSeverity
    empiric_therapy: List[Dict[str, str]]
    alternative_therapy: List[Dict[str, str]]
    duration: str
    de_escalation_strategy: List[str]
    iv_to_po_criteria: List[str]
    spectrum_coverage: List[str]
    monitoring: List[str]
    special_considerations: List[str] = field(default_factory=list)
    local_resistance_notes: List[str] = field(default_factory=list)


class AntibioticStewardship:
    """
    Antibiotic stewardship decision support system.
    """

    def __init__(self):
        self._initialize_guidelines()

    def _initialize_guidelines(self):
        """Initialize antibiotic guidelines database"""
        self.infection_guidelines = {
            'skin_cellulitis': self._cellulitis_abx,
            'diabetic_foot': self._diabetic_foot_abx,
            'cap': self._cap_abx,
            'hap_vap': self._hap_vap_abx,
            'uti_simple': self._uti_simple_abx,
            'uti_complicated': self._uti_complicated_abx,
            'pyelonephritis': self._pyelonephritis_abx,
            'intra_abdominal': self._intra_abdominal_abx,
            'meningitis': self._meningitis_abx,
            'endocarditis': self._endocarditis_abx,
            'sepsis_unknown': self._sepsis_unknown_abx,
        }

    def _cellulitis_abx(self, severity: InfectionSeverity = InfectionSeverity.MODERATE) -> AntibioticRecommendation:
        """Cellulitis/Skin and Soft Tissue Infection"""
        if severity in [InfectionSeverity.MILD, InfectionSeverity.MODERATE]:
            empiric = [
                {
                    'regimen': 'Cephalexin 500mg PO QID',
                    'coverage': 'Streptococcus, MSSA',
                    'duration': '5-7 days',
                    'note': 'First-line for non-purulent cellulitis'
                },
                {
                    'regimen': 'If purulent/abscess: Add MRSA coverage',
                    'options': 'TMP-SMX DS BID + Cephalexin OR Doxycycline 100mg BID',
                    'note': 'I&D preferred for abscesses >5cm'
                }
            ]
            alternative = [
                {'regimen': 'Clindamycin 300-450mg PO TID', 'note': 'Covers MRSA and Strep'},
                {'regimen': 'Amoxicillin-clavulanate 875mg PO BID', 'note': 'If bite wound or concern for anaerobes'}
            ]
        else:  # Severe
            empiric = [
                {
                    'regimen': 'Vancomycin 15-20mg/kg IV q8-12h + Piperacillin-tazobactam 3.375g IV q6h',
                    'coverage': 'MRSA + broad gram-negative + anaerobes',
                    'indication': 'Severe infection, sepsis, necrotizing fasciitis concern'
                }
            ]
            alternative = [
                {'regimen': 'Linezolid 600mg IV q12h + Meropenem 1g IV q8h', 'note': 'If vancomycin-resistant or renal failure'}
            ]

        return AntibioticRecommendation(
            infection_type="Cellulitis / Skin and Soft Tissue Infection",
            severity=severity,
            empiric_therapy=empiric,
            alternative_therapy=alternative,
            duration="5-7 days for uncomplicated; 7-14 days if severe",
            de_escalation_strategy=[
                "Narrow based on culture results",
                "MSSA: Switch to cephalexin or dicloxacillin",
                "Streptococcus: Amoxicillin or penicillin VK",
                "No growth from I&D: Can stop antibiotics if clinically improved"
            ],
            iv_to_po_criteria=[
                "Afebrile >24h",
                "Improving erythema and swelling",
                "Tolerating PO intake",
                "WBC normalizing"
            ],
            spectrum_coverage=["Streptococcus pyogenes (Group A Strep)", "Staphylococcus aureus (MSSA/MRSA if purulent)"],
            monitoring=["Clinical response (decreased erythema, pain)", "Fever curve", "WBC"],
            special_considerations=[
                "I&D is primary treatment for abscesses",
                "Mark borders of erythema to track progression",
                "Consider imaging if necrotizing fasciitis suspected (crepitus, rapidly progressive)"
            ]
        )

    def _diabetic_foot_abx(self, severity: InfectionSeverity = InfectionSeverity.MODERATE) -> AntibioticRecommendation:
        """Diabetic foot infection"""
        if severity == InfectionSeverity.MILD:
            empiric = [
                {'regimen': 'Amoxicillin-clavulanate 875mg PO BID OR Cephalexin 500mg QID', 'duration': '1-2 weeks'}
            ]
        elif severity == InfectionSeverity.MODERATE:
            empiric = [
                {'regimen': 'Amoxicillin-clavulanate 875mg PO TID OR Levofloxacin 750mg PO daily', 'duration': '2-3 weeks'}
            ]
        else:  # Severe
            empiric = [
                {
                    'regimen': 'Vancomycin + Piperacillin-tazobactam OR Vancomycin + Ceftriaxone + Metronidazole',
                    'coverage': 'MRSA + gram-negatives + anaerobes',
                    'duration': '2-4 weeks (longer if osteomyelitis)'
                }
            ]

        return AntibioticRecommendation(
            infection_type="Diabetic Foot Infection",
            severity=severity,
            empiric_therapy=empiric,
            alternative_therapy=[{'regimen': 'Ertapenem 1g IV daily', 'note': 'Good for moderate-severe'}],
            duration="Mild 1-2 weeks, Moderate 2-3 weeks, Severe 2-4 weeks, Osteomyelitis 6 weeks",
            de_escalation_strategy=[
                "Obtain deep tissue or bone culture (not swab)",
                "Narrow based on culture and sensitivities",
                "Stop anaerobic coverage if no anaerobes isolated"
            ],
            iv_to_po_criteria=["Clinically improving", "Able to take PO", "Good PO bioavailability option available"],
            spectrum_coverage=[
                "Staphylococcus (MSSA, MRSA)",
                "Streptococcus",
                "Gram-negatives (E. coli, Proteus, Klebsiella)",
                "Anaerobes (if deep ulcer or necrosis)"
            ],
            monitoring=["Wound healing", "Inflammatory markers (ESR, CRP)", "Plain radiographs or MRI if osteomyelitis concern"],
            special_considerations=[
                "ALWAYS assess vascular status (pulses, ABI)",
                "Probe to bone test for osteomyelitis",
                "Debridement is key - antibiotics alone insufficient",
                "Duration depends on bone involvement"
            ]
        )

    def _cap_abx(self, severity: InfectionSeverity = InfectionSeverity.MODERATE) -> AntibioticRecommendation:
        """Community-Acquired Pneumonia - see protocols.py for full protocol"""
        if severity == InfectionSeverity.MILD:
            empiric = [
                {'regimen': 'Amoxicillin 1g TID', 'line': 'Preferred', 'duration': '5-7 days'},
                {'regimen': 'Doxycycline 100mg BID', 'line': 'Alternative', 'duration': '5-7 days'}
            ]
        elif severity == InfectionSeverity.MODERATE:
            empiric = [
                {'regimen': 'Amoxicillin-clavulanate 875mg BID + Azithromycin 500mg daily', 'duration': '5-7 days'},
                {'regimen': 'Levofloxacin 750mg daily (monotherapy)', 'duration': '5-7 days'}
            ]
        else:  # Severe
            empiric = [
                {'regimen': 'Ceftriaxone 1-2g IV daily + Azithromycin 500mg IV daily', 'duration': '7-10 days'},
                {'regimen': 'Add Vancomycin if MRSA risk (influenza, prior MRSA)'}
            ]

        return AntibioticRecommendation(
            infection_type="Community-Acquired Pneumonia",
            severity=severity,
            empiric_therapy=empiric,
            alternative_therapy=[],
            duration="5-7 days for uncomplicated; 7-10 days for severe",
            de_escalation_strategy=[
                "Narrow based on sputum or blood cultures",
                "If S. pneumoniae: penicillin or amoxicillin (if susceptible)",
                "Stop atypical coverage if no Legionella/Mycoplasma"
            ],
            iv_to_po_criteria=["Afebrile >24h", "Hemodynamically stable", "Improving WBC and oxygenation"],
            spectrum_coverage=["S. pneumoniae", "H. influenzae", "M. pneumoniae", "Legionella (if severe)"],
            monitoring=["Clinical improvement by day 3-5", "Oxygen saturation", "CXR not needed if improving"],
            special_considerations=["Use local antibiogram for resistance patterns"]
        )

    def _hap_vap_abx(self, severity: InfectionSeverity = InfectionSeverity.SEVERE) -> AntibioticRecommendation:
        """Hospital-Acquired Pneumonia / Ventilator-Associated Pneumonia"""
        empiric = [
            {
                'regimen': 'Anti-pseudomonal beta-lactam + Anti-MRSA agent',
                'examples': 'Piperacillin-tazobactam 4.5g IV q6h OR Cefepime 2g IV q8h OR Meropenem 1g IV q8h PLUS Vancomycin 15mg/kg IV q8-12h',
                'note': 'Empiric double coverage for Pseudomonas NOT recommended unless very high risk'
            }
        ]

        return AntibioticRecommendation(
            infection_type="Hospital-Acquired Pneumonia / VAP",
            severity=severity,
            empiric_therapy=empiric,
            alternative_therapy=[
                {'regimen': 'Linezolid 600mg IV q12h instead of vancomycin', 'indication': 'If vancomycin MIC >1.5 or renal failure'},
                {'regimen': 'Add aminoglycoside if septic shock', 'examples': 'Tobramycin or amikacin x 3-5 days'}
            ],
            duration="7 days (may extend to 14 days if slow response or Pseudomonas)",
            de_escalation_strategy=[
                "CRUCIAL - De-escalate based on culture at 48-72h",
                "No MRSA: Stop vancomycin/linezolid",
                "No Pseudomonas: Narrow to ceftriaxone",
                "Stop antibiotics if no pneumonia (clinical and radiographic improvement)",
                "Procalcitonin-guided therapy may shorten duration"
            ],
            iv_to_po_criteria=["VAP requires IV therapy; HAP can transition if stable and good PO bioavailability"],
            spectrum_coverage=[
                "Pseudomonas aeruginosa",
                "MRSA",
                "Klebsiella pneumoniae (including ESBL)",
                "Acinetobacter (if prevalent)",
                "Stenotrophomonas (consider TMP-SMX if isolated)"
            ],
            monitoring=[
                "Daily culture results",
                "Clinical improvement (fever, WBC, oxygenation)",
                "Procalcitonin (consider for duration guidance)",
                "Antimicrobial resistance patterns"
            ],
            special_considerations=[
                "Use institutional antibiogram",
                "Consider fungal coverage (echinocandin) if prolonged ICU stay, immunosuppressed, or prior azole use",
                "Source control: bronchoscopy BAL for culture if diagnosis uncertain"
            ],
            local_resistance_notes=[
                "Adjust based on local MDR patterns",
                "If carbapenem-resistant organisms: consult ID, consider polymyxin or ceftazidime-avibactam"
            ]
        )

    def _uti_simple_abx(self, severity: InfectionSeverity = InfectionSeverity.MILD) -> AntibioticRecommendation:
        """Simple cystitis - see protocols.py"""
        return AntibioticRecommendation(
            infection_type="Acute Uncomplicated Cystitis",
            severity=severity,
            empiric_therapy=[
                {'drug': 'Nitrofurantoin 100mg BID', 'duration': '5 days', 'line': 'First-line'},
                {'drug': 'TMP-SMX DS BID', 'duration': '3 days', 'line': 'First-line if resistance <20%'},
                {'drug': 'Fosfomycin 3g single dose', 'duration': '1 day'}
            ],
            alternative_therapy=[
                {'drug': 'Cephalexin 500mg QID', 'duration': '5-7 days'},
                {'drug': 'Amoxicillin-clavulanate 875mg BID', 'duration': '5-7 days'}
            ],
            duration="3-5 days",
            de_escalation_strategy=["No culture needed if responding", "Adjust if culture obtained and resistant"],
            iv_to_po_criteria=["N/A - PO therapy"],
            spectrum_coverage=["E. coli", "Klebsiella", "Proteus"],
            monitoring=["Symptom resolution in 48-72h"],
            special_considerations=["Avoid fluoroquinolones for simple UTI - reserve for complicated infections"]
        )

    def _pyelonephritis_abx(self, severity: InfectionSeverity = InfectionSeverity.MODERATE) -> AntibioticRecommendation:
        """Pyelonephritis"""
        if severity in [InfectionSeverity.MILD, InfectionSeverity.MODERATE]:
            empiric = [
                {'regimen': 'Ciprofloxacin 500mg PO BID x 7 days OR Levofloxacin 750mg PO daily x 5 days'},
                {'regimen': 'Ceftriaxone 1g IV x1 dose, then PO step-down (ciprofloxacin or TMP-SMX based on culture)'}
            ]
        else:  # Severe
            empiric = [
                {'regimen': 'Ceftriaxone 1-2g IV daily OR Cefepime 1-2g IV q12h'},
                {'regimen': 'If gram-positive cocci: Add Ampicillin 2g IV q6h (Enterococcus coverage)'},
                {'regimen': 'If septic or resistant gram-negatives: Meropenem 1g IV q8h'}
            ]

        return AntibioticRecommendation(
            infection_type="Acute Pyelonephritis",
            severity=severity,
            empiric_therapy=empiric,
            alternative_therapy=[],
            duration="Fluoroquinolones 5-7 days; Beta-lactams 10-14 days",
            de_escalation_strategy=[
                "Obtain blood and urine cultures",
                "Narrow based on susceptibilities",
                "Switch to PO when afebrile and tolerating PO"
            ],
            iv_to_po_criteria=["Afebrile >24h", "Hemodynamically stable", "Tolerating PO", "Clinical improvement"],
            spectrum_coverage=["E. coli (most common)", "Klebsiella", "Proteus", "Enterococcus"],
            monitoring=["Blood cultures", "Renal ultrasound if not improving (obstruction, abscess)"],
            special_considerations=[
                "Consider imaging if not improving in 48-72h",
                "Pregnant women: IV ceftriaxone, avoid fluoroquinolones"
            ]
        )

    def _intra_abdominal_abx(self, severity: InfectionSeverity = InfectionSeverity.MODERATE) -> AntibioticRecommendation:
        """Intra-abdominal infections"""
        if severity == InfectionSeverity.MILD:
            empiric = [
                {'regimen': 'Ceftriaxone 1-2g IV daily + Metronidazole 500mg IV q8h'},
                {'regimen': 'Ciprofloxacin 400mg IV q12h + Metronidazole 500mg IV q8h'}
            ]
        else:  # Moderate-Severe
            empiric = [
                {'regimen': 'Piperacillin-tazobactam 3.375-4.5g IV q6h', 'note': 'Monotherapy for moderate'},
                {'regimen': 'Meropenem 1g IV q8h OR Imipenem 500mg IV q6h', 'note': 'For severe or high-risk ESBL'},
                {'regimen': 'Cefepime 2g IV q8h + Metronidazole 500mg IV q8h', 'note': 'Alternative'}
            ]

        return AntibioticRecommendation(
            infection_type="Intra-Abdominal Infection (Peritonitis, Abscess, Cholangitis)",
            severity=severity,
            empiric_therapy=empiric,
            alternative_therapy=[
                {'regimen': 'Ertapenem 1g IV daily', 'note': 'Good for community-acquired, no Pseudomonas coverage'}
            ],
            duration="4-7 days (source control dependent); Extend to 10-14 days if no adequate source control",
            de_escalation_strategy=[
                "SOURCE CONTROL is key - drainage, surgery",
                "Narrow based on operative cultures",
                "Stop empiric fungal coverage if no Candida isolated"
            ],
            iv_to_po_criteria=["Source controlled", "Afebrile", "Resolving leukocytosis", "Tolerating PO"],
            spectrum_coverage=[
                "Gram-negatives (E. coli, Klebsiella)",
                "Anaerobes (Bacteroides fragilis) - MUST cover",
                "Enterococcus (if healthcare-associated or severe)"
            ],
            monitoring=["Source control adequacy", "Clinical improvement", "Consider imaging if persistent fever/leukocytosis"],
            special_considerations=[
                "Add empiric antifungal (fluconazole or echinocandin) if: ICU, post-op leak, recurrent infection, immunosuppressed",
                "Biliary infections: Ensure adequate bile duct drainage (ERCP)",
                "Diverticulitis: Uncomplicated can be outpatient PO (amox-clav or cipro + metronidazole)"
            ]
        )

    def _meningitis_abx(self, severity: InfectionSeverity = InfectionSeverity.LIFE_THREATENING) -> AntibioticRecommendation:
        """Bacterial meningitis"""
        return AntibioticRecommendation(
            infection_type="Bacterial Meningitis",
            severity=severity,
            empiric_therapy=[
                {
                    'regimen': 'Vancomycin 15-20mg/kg IV q8-12h + Ceftriaxone 2g IV q12h',
                    'indication': 'Adults <50 years',
                    'note': 'Start IMMEDIATELY, do not delay for LP or imaging'
                },
                {
                    'regimen': 'Add Ampicillin 2g IV q4h if >50 years or immunocompromised',
                    'coverage': 'Listeria monocytogenes',
                    'note': 'Ceftriaxone does not cover Listeria'
                },
                {
                    'regimen': 'Add Acyclovir 10mg/kg IV q8h if HSV encephalitis concern',
                    'indication': 'Altered mental status, seizures, temporal lobe findings'
                },
                {
                    'regimen': 'Dexamethasone 10mg IV q6h x 4 days',
                    'timing': 'Give 15 min before or with first antibiotic dose',
                    'evidence': 'Reduces mortality in pneumococcal meningitis'
                }
            ],
            alternative_therapy=[
                {'regimen': 'If severe PCN allergy: Vancomycin + Aztreonam + TMP-SMX (for Listeria)'},
                {'regimen': 'If post-neurosurgery: Vancomycin + Cefepime or Meropenem (Pseudomonas coverage)'}
            ],
            duration="Pneumococcus 10-14 days, Meningococcus 7 days, Listeria 21 days, Gram-negatives 21 days",
            de_escalation_strategy=[
                "OBTAIN LP before antibiotics if no contraindication (but don't delay antibiotics)",
                "Narrow based on CSF Gram stain and culture",
                "S. pneumoniae: Continue ceftriaxone if susceptible",
                "N. meningitidis: Penicillin G if susceptible",
                "Listeria: Ampicillin + gentamicin",
                "Stop vancomycin if organism susceptible to ceftriaxone"
            ],
            iv_to_po_criteria=["Meningitis requires IV therapy for entire course"],
            spectrum_coverage=[
                "S. pneumoniae (most common)",
                "N. meningitidis",
                "Listeria monocytogenes (>50 yo, immunocompromised)",
                "H. influenzae (unvaccinated)"
            ],
            monitoring=[
                "Repeat LP at 48h if not improving",
                "Vancomycin trough 15-20 mcg/mL",
                "Neurologic exam frequently",
                "Hearing test at end of therapy (ototoxicity from aminoglycosides)"
            ],
            special_considerations=[
                "DO NOT DELAY ANTIBIOTICS - give before LP/CT if any delay",
                "Dexamethasone benefit primarily in pneumococcal meningitis",
                "Droplet precautions until meningococcus ruled out",
                "Prophylaxis for close contacts if N. meningitidis (rifampin, cipro, or ceftriaxone)"
            ]
        )

    def _sepsis_unknown_abx(self, severity: InfectionSeverity = InfectionSeverity.LIFE_THREATENING) -> AntibioticRecommendation:
        """Sepsis with unknown source"""
        return AntibioticRecommendation(
            infection_type="Sepsis - Unknown Source",
            severity=severity,
            empiric_therapy=[
                {
                    'regimen': 'Vancomycin 15-20mg/kg IV q8-12h + Piperacillin-tazobactam 4.5g IV q6h',
                    'coverage': 'MRSA + broad gram-negative + anaerobes',
                    'note': 'Standard empiric for sepsis'
                },
                {
                    'regimen': 'Alternative: Vancomycin + Cefepime 2g IV q8h + Metronidazole 500mg IV q8h',
                    'note': 'If concern for resistant gram-negatives'
                },
                {
                    'regimen': 'If immunocompromised: Consider adding antifungal (micafungin 100mg IV daily)',
                    'indication': 'Neutropenic, prolonged ICU, TPN, broad-spectrum antibiotics >4 days'
                }
            ],
            alternative_therapy=[
                {'regimen': 'Meropenem 1g IV q8h + Vancomycin', 'indication': 'If ESBL or carbapenem-resistant risk factors'}
            ],
            duration="De-escalate within 48-72h based on cultures; Total 7-10 days depending on source",
            de_escalation_strategy=[
                "CRITICAL: Obtain cultures BEFORE antibiotics (blood x2, urine, sputum, wound)",
                "De-escalate at 48-72h based on cultures - DO NOT continue broad-spectrum empirically",
                "If no organism identified and patient improving: narrow to most likely source",
                "Stop antibiotics if alternative diagnosis found (e.g., pancreatitis, not infection)"
            ],
            iv_to_po_criteria=["Depends on source", "Generally requires clinical stability, afebrile >24h, tolerating PO"],
            spectrum_coverage=[
                "MRSA and MSSA",
                "Gram-negatives including Pseudomonas",
                "Anaerobes",
                "Consider fungal if risk factors"
            ],
            monitoring=[
                "Daily culture results",
                "Lactate clearance",
                "Procalcitonin (consider for duration guidance)",
                "Source identification (imaging as needed)"
            ],
            special_considerations=[
                "HOUR-1 BUNDLE: Antibiotics within 1 hour of sepsis recognition",
                "Identify source urgently (imaging, physical exam)",
                "Source control (drain abscess, remove infected catheter/hardware)",
                "Antimicrobial stewardship: Review daily and de-escalate"
            ]
        )

    def _endocarditis_abx(self, severity: InfectionSeverity = InfectionSeverity.LIFE_THREATENING) -> AntibioticRecommendation:
        """Infective endocarditis"""
        return AntibioticRecommendation(
            infection_type="Infective Endocarditis",
            severity=severity,
            empiric_therapy=[
                {
                    'regimen': 'Native valve: Vancomycin + Ceftriaxone',
                    'dose': 'Vancomycin 15mg/kg q12h + Ceftriaxone 2g q24h',
                    'note': 'Covers Streptococcus, Staphylococcus, Enterococcus'
                },
                {
                    'regimen': 'Prosthetic valve: Vancomycin + Gentamicin + Rifampin',
                    'dose': 'Vanc 15mg/kg q12h + Gent 1mg/kg q8h + Rifampin 300mg q8h',
                    'note': 'Add Cefepime if gram-negative risk'
                }
            ],
            alternative_therapy=[
                {'regimen': 'Daptomycin 8-10mg/kg IV daily instead of vancomycin', 'note': 'For MRSA or vanc-resistant'}
            ],
            duration="4-6 weeks IV therapy (depends on organism and valve type)",
            de_escalation_strategy=[
                "MUST obtain blood cultures x3 before antibiotics",
                "Tailor to organism:",
                "- Strep viridans: Penicillin G or Ceftriaxone x 4 weeks",
                "- MSSA: Nafcillin or cefazolin x 6 weeks",
                "- MRSA: Vancomycin or daptomycin x 6 weeks",
                "- Enterococcus: Ampicillin + Gentamicin x 4-6 weeks",
                "Consult ID and cardiothoracic surgery"
            ],
            iv_to_po_criteria=["Endocarditis requires FULL IV therapy - no PO transition"],
            spectrum_coverage=["Streptococcus viridans", "S. aureus", "Enterococcus", "HACEK organisms (rare)"],
            monitoring=[
                "Blood cultures daily until negative",
                "TEE (transesophageal echo) - superior to TTE",
                "Weekly inflammatory markers (ESR, CRP)",
                "Renal function (gentamicin)",
                "Vancomycin troughs",
                "Watch for complications: heart failure, emboli, abscess, heart block"
            ],
            special_considerations=[
                "DUKE CRITERIA for diagnosis",
                "Early surgery consult: heart failure, large vegetations (>10mm), abscess, persistent bacteremia >5-7 days",
                "Long-term suppressive therapy rarely needed (for inoperable prosthetic valve with resistant organism)",
                "Dental prophylaxis: Amoxicillin 2g PO 1h before procedure (if prosthetic valve or prior endocarditis)"
            ]
        )

    def get_antibiotic_recommendation(
        self,
        infection_type: str,
        severity: str = "moderate",
        patient_factors: Optional[Dict] = None
    ) -> Optional[AntibioticRecommendation]:
        """
        Get antibiotic recommendation for infection.

        Args:
            infection_type: Type of infection
            severity: "mild", "moderate", "severe", or "life_threatening"
            patient_factors: Dictionary with patient-specific factors (allergies, renal function, etc.)

        Returns:
            AntibioticRecommendation object
        """
        infection_key = infection_type.lower().replace(' ', '_').replace('-', '_')

        # Map common variations
        infection_map = {
            'cellulitis': 'skin_cellulitis',
            'ssti': 'skin_cellulitis',
            'pneumonia': 'cap',
            'uti': 'uti_simple',
            'urinary_tract_infection': 'uti_simple',
            'meningitis': 'meningitis',
        }

        infection_key = infection_map.get(infection_key, infection_key)

        method = self.infection_guidelines.get(infection_key)
        if not method:
            return None

        severity_enum = InfectionSeverity[severity.upper()]
        return method(severity_enum)


def get_antibiotic_recommendation(
    infection_type: str,
    severity: str = "moderate",
    **kwargs
) -> Optional[Dict]:
    """
    Get antibiotic recommendation.

    Example:
        >>> rec = get_antibiotic_recommendation("cellulitis", severity="moderate")
    """
    stewardship = AntibioticStewardship()
    recommendation = stewardship.get_antibiotic_recommendation(infection_type, severity, kwargs)

    if not recommendation:
        return None

    return {
        'infection_type': recommendation.infection_type,
        'severity': recommendation.severity.value,
        'empiric_therapy': recommendation.empiric_therapy,
        'alternative_therapy': recommendation.alternative_therapy,
        'duration': recommendation.duration,
        'de_escalation_strategy': recommendation.de_escalation_strategy,
        'iv_to_po_criteria': recommendation.iv_to_po_criteria,
        'spectrum_coverage': recommendation.spectrum_coverage,
        'monitoring': recommendation.monitoring,
        'special_considerations': recommendation.special_considerations
    }
