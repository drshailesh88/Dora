"""
Quick References

One-page reference cards and pocket guides for rapid clinical decision-making.
"""

from typing import Optional, List, Dict
from .models import QuickReference
from .storage import ProtocolStorage, get_protocol_storage


# Pre-built quick reference cards
ACLS_MEDICATIONS = """
┌────────────────────────────────────────┐
│ 💊 ACLS Medications Quick Reference    │
├────────────────────────────────────────┤
│ EPINEPHRINE                            │
│ Cardiac arrest: 1mg IV q3-5min         │
│ Anaphylaxis: 0.3-0.5mg IM              │
│ Infusion: 2-10 mcg/min                 │
├────────────────────────────────────────┤
│ AMIODARONE                             │
│ VF/pVT: 300mg IV bolus                 │
│ Then: 150mg IV x1 if needed            │
│ Infusion: 1mg/min × 6h → 0.5mg/min     │
├────────────────────────────────────────┤
│ LIDOCAINE (if amio unavailable)        │
│ VF/pVT: 1-1.5 mg/kg IV                 │
│ Then: 0.5-0.75 mg/kg q5-10min          │
│ Max: 3 mg/kg                           │
├────────────────────────────────────────┤
│ ATROPINE                               │
│ Bradycardia: 0.5-1mg IV q3-5min        │
│ Max: 3mg total                         │
├────────────────────────────────────────┤
│ ADENOSINE                              │
│ SVT: 6mg rapid IV push                 │
│ Then: 12mg if no response              │
│ Then: 12mg x1 more if needed           │
├────────────────────────────────────────┤
│ DOPAMINE                               │
│ Bradycardia: 2-20 mcg/kg/min           │
│ Titrate to effect                      │
├────────────────────────────────────────┤
│ VASOPRESSIN                            │
│ Cardiac arrest: 40 units IV x1         │
│ (Alternative to epinephrine)           │
└────────────────────────────────────────┘
"""

PEDIATRIC_DOSING = """
┌────────────────────────────────────────┐
│ 👶 Pediatric Emergency Dosing          │
├────────────────────────────────────────┤
│ WEIGHT-BASED CALCULATIONS              │
│                                        │
│ 3 kg  = Newborn                        │
│ 5 kg  = 2 months                       │
│ 10 kg = 1 year                         │
│ 15 kg = 3 years                        │
│ 20 kg = 5 years                        │
│ 30 kg = 10 years                       │
├────────────────────────────────────────┤
│ CARDIAC ARREST                         │
│ Epinephrine: 0.01 mg/kg IV/IO          │
│             (0.1 mL/kg of 1:10,000)    │
│ Max: 1 mg                              │
├────────────────────────────────────────┤
│ ANAPHYLAXIS                            │
│ Epinephrine: 0.01 mg/kg IM             │
│             (0.01 mL/kg of 1:1,000)    │
│ Max: 0.5 mg                            │
├────────────────────────────────────────┤
│ SEIZURES                               │
│ Lorazepam: 0.1 mg/kg IV/IM             │
│ Max: 4 mg                              │
│                                        │
│ Diazepam: 0.2-0.5 mg/kg rectal         │
│ Max: 20 mg                             │
├────────────────────────────────────────┤
│ FLUID BOLUS                            │
│ 20 mL/kg NS or LR                      │
│ May repeat × 2-3                       │
├────────────────────────────────────────┤
│ GLUCOSE                                │
│ D10: 5 mL/kg IV                        │
│ D25: 2 mL/kg IV                        │
│ D50: 1 mL/kg IV (>2 years)             │
├────────────────────────────────────────┤
│ INTUBATION                             │
│ ETT size: (Age/4) + 4                  │
│ Depth: ETT size × 3                    │
│                                        │
│ Atropine: 0.02 mg/kg (min 0.1mg)       │
│ Ketamine: 1-2 mg/kg IV                 │
│ Rocuronium: 1 mg/kg IV                 │
└────────────────────────────────────────┘
"""

LAB_NORMALS = """
┌────────────────────────────────────────┐
│ 🔬 Normal Lab Values                   │
├────────────────────────────────────────┤
│ ELECTROLYTES                           │
│ Sodium:      135-145 mEq/L             │
│ Potassium:   3.5-5.0 mEq/L             │
│ Chloride:    95-105 mEq/L              │
│ Bicarbonate: 22-28 mEq/L               │
│ Calcium:     8.5-10.5 mg/dL            │
│ Magnesium:   1.5-2.5 mEq/L             │
│ Phosphate:   2.5-4.5 mg/dL             │
├────────────────────────────────────────┤
│ RENAL FUNCTION                         │
│ BUN:         7-20 mg/dL                │
│ Creatinine:  0.6-1.2 mg/dL             │
│ eGFR:        >60 mL/min                │
├────────────────────────────────────────┤
│ LIVER FUNCTION                         │
│ ALT:         7-56 U/L                  │
│ AST:         10-40 U/L                 │
│ Alkaline P:  44-147 U/L                │
│ Bilirubin:   0.1-1.2 mg/dL             │
│ Albumin:     3.5-5.5 g/dL              │
├────────────────────────────────────────┤
│ COMPLETE BLOOD COUNT                   │
│ WBC:         4.5-11.0 × 10³/µL         │
│ Hemoglobin:  M: 13.5-17.5 g/dL         │
│              F: 12.0-16.0 g/dL         │
│ Platelets:   150-400 × 10³/µL          │
├────────────────────────────────────────┤
│ COAGULATION                            │
│ PT:          11-13.5 seconds           │
│ INR:         0.8-1.2                   │
│ PTT:         25-35 seconds             │
├────────────────────────────────────────┤
│ CARDIAC MARKERS                        │
│ Troponin I:  <0.04 ng/mL               │
│ BNP:         <100 pg/mL                │
│ CK-MB:       <5% of total CK           │
├────────────────────────────────────────┤
│ BLOOD GASES (Arterial)                 │
│ pH:          7.35-7.45                 │
│ PaCO2:       35-45 mmHg                │
│ PaO2:        80-100 mmHg               │
│ HCO3:        22-26 mEq/L               │
│ SaO2:        95-100%                   │
└────────────────────────────────────────┘
"""

GLASGOW_COMA_SCALE = """
┌────────────────────────────────────────┐
│ 🧠 Glasgow Coma Scale (GCS)            │
├────────────────────────────────────────┤
│ EYE OPENING (E)                        │
│ 4 = Spontaneous                        │
│ 3 = To voice                           │
│ 2 = To pain                            │
│ 1 = None                               │
├────────────────────────────────────────┤
│ VERBAL RESPONSE (V)                    │
│ 5 = Oriented                           │
│ 4 = Confused                           │
│ 3 = Inappropriate words                │
│ 2 = Incomprehensible sounds            │
│ 1 = None                               │
├────────────────────────────────────────┤
│ MOTOR RESPONSE (M)                     │
│ 6 = Obeys commands                     │
│ 5 = Localizes pain                     │
│ 4 = Withdraws from pain                │
│ 3 = Flexion to pain (decorticate)      │
│ 2 = Extension to pain (decerebrate)    │
│ 1 = None                               │
├────────────────────────────────────────┤
│ TOTAL SCORE: E + V + M (3-15)          │
│                                        │
│ INTERPRETATION:                        │
│ 13-15 = Mild brain injury              │
│ 9-12  = Moderate brain injury          │
│ ≤8    = Severe (consider intubation)   │
└────────────────────────────────────────┘
"""

APGAR_SCORE = """
┌────────────────────────────────────────┐
│ 👶 APGAR Score                         │
├────────────────────────────────────────┤
│         0       1           2          │
├────────────────────────────────────────┤
│ A - Appearance (Color)                 │
│   Blue/Pale   Body pink   All pink     │
│               limbs blue               │
├────────────────────────────────────────┤
│ P - Pulse                              │
│   Absent      <100        >100         │
├────────────────────────────────────────┤
│ G - Grimace (Reflex)                   │
│   None        Grimace     Cry/cough    │
├────────────────────────────────────────┤
│ A - Activity (Tone)                    │
│   Limp        Some        Active       │
│               flexion     movement     │
├────────────────────────────────────────┤
│ R - Respiration                        │
│   Absent      Slow/weak   Good cry     │
├────────────────────────────────────────┤
│ TIMING: 1 min and 5 min after birth   │
│                                        │
│ INTERPRETATION:                        │
│ 7-10 = Normal                          │
│ 4-6  = Moderately abnormal             │
│ 0-3  = Low (needs resuscitation)       │
└────────────────────────────────────────┘
"""


class QuickReferenceManager:
    """Manager for quick reference cards."""

    def __init__(self, storage: Optional[ProtocolStorage] = None):
        self.storage = storage or get_protocol_storage()

    def create_reference(
        self,
        title: str,
        content: str,
        card_type: str,
        user_id: str,
        protocol_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        layout: str = "card",
        is_printable: bool = True,
    ) -> QuickReference:
        """Create a quick reference card."""
        ref = QuickReference(
            protocol_id=protocol_id,
            title=title,
            content=content,
            card_type=card_type,
            is_printable=is_printable,
            layout=layout,
            created_by=user_id,
            organization_id=organization_id,
        )

        self.storage.create_quick_reference(ref)
        return ref

    def get_references(
        self,
        protocol_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> List[QuickReference]:
        """Get quick references."""
        return self.storage.get_quick_references(
            protocol_id=protocol_id,
            organization_id=organization_id,
        )

    def get_default_references(self) -> List[Dict[str, str]]:
        """Get default pre-built reference cards."""
        return [
            {
                "id": "acls_meds",
                "title": "ACLS Medications Quick Reference",
                "content": ACLS_MEDICATIONS,
                "card_type": "dosing",
            },
            {
                "id": "pediatric_dosing",
                "title": "Pediatric Emergency Dosing",
                "content": PEDIATRIC_DOSING,
                "card_type": "dosing",
            },
            {
                "id": "lab_normals",
                "title": "Normal Lab Values",
                "content": LAB_NORMALS,
                "card_type": "lab_values",
            },
            {
                "id": "gcs",
                "title": "Glasgow Coma Scale (GCS)",
                "content": GLASGOW_COMA_SCALE,
                "card_type": "scoring",
            },
            {
                "id": "apgar",
                "title": "APGAR Score",
                "content": APGAR_SCORE,
                "card_type": "scoring",
            },
        ]

    def export_for_print(self, reference_id: str) -> Optional[str]:
        """Export reference card in print-optimized format."""
        # For now, return the content as-is
        # In production, could convert to PDF or formatted HTML
        refs = self.storage.get_quick_references()
        for ref in refs:
            if ref.id == reference_id:
                return ref.content
        return None


# Default instance
_manager: Optional[QuickReferenceManager] = None


def get_reference_manager() -> QuickReferenceManager:
    """Get default quick reference manager."""
    global _manager
    if _manager is None:
        _manager = QuickReferenceManager()
    return _manager
