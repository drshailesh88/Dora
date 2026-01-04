"""
Prescription templates for Dora.

Pre-configured templates for common conditions:
- Type 2 Diabetes
- Hypertension
- Upper Respiratory Tract Infection (URTI)
- Urinary Tract Infection (UTI)
- Gastritis
- And more...

Also supports custom doctor templates.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from .models import (
    PrescriptionTemplate,
    PrescriptionItem,
    Dosage,
    DosageForm,
    Frequency,
    RouteOfAdministration,
    DrugSchedule,
)


class TemplateLibrary:
    """Library of prescription templates."""

    @staticmethod
    def get_template(template_name: str) -> Optional[PrescriptionTemplate]:
        """
        Get template by name.

        Args:
            template_name: Name of template (e.g., 'dm_type2_initial')

        Returns:
            PrescriptionTemplate or None if not found
        """
        templates = {
            'dm_type2_initial': TemplateLibrary.dm_type2_initial(),
            'dm_type2_dual': TemplateLibrary.dm_type2_dual_therapy(),
            'htn_initial': TemplateLibrary.htn_initial(),
            'htn_dual': TemplateLibrary.htn_dual_therapy(),
            'urti': TemplateLibrary.urti(),
            'uti': TemplateLibrary.uti(),
            'gastritis': TemplateLibrary.gastritis(),
            'fever_pain': TemplateLibrary.fever_pain(),
            'dyslipidemia': TemplateLibrary.dyslipidemia(),
        }

        return templates.get(template_name)

    @staticmethod
    def list_templates() -> List[Dict[str, str]]:
        """List all available templates."""
        return [
            {
                'id': 'dm_type2_initial',
                'name': 'Type 2 Diabetes - Initial',
                'condition': 'Type 2 Diabetes Mellitus',
                'specialty': 'General Medicine',
            },
            {
                'id': 'dm_type2_dual',
                'name': 'Type 2 Diabetes - Dual Therapy',
                'condition': 'Type 2 Diabetes Mellitus',
                'specialty': 'General Medicine',
            },
            {
                'id': 'htn_initial',
                'name': 'Hypertension - Initial',
                'condition': 'Hypertension',
                'specialty': 'General Medicine',
            },
            {
                'id': 'htn_dual',
                'name': 'Hypertension - Dual Therapy',
                'condition': 'Hypertension',
                'specialty': 'General Medicine',
            },
            {
                'id': 'urti',
                'name': 'Upper Respiratory Tract Infection',
                'condition': 'URTI',
                'specialty': 'General Medicine',
            },
            {
                'id': 'uti',
                'name': 'Urinary Tract Infection',
                'condition': 'UTI',
                'specialty': 'General Medicine',
            },
            {
                'id': 'gastritis',
                'name': 'Gastritis / GERD',
                'condition': 'Gastritis',
                'specialty': 'General Medicine',
            },
            {
                'id': 'fever_pain',
                'name': 'Fever & Pain',
                'condition': 'Symptomatic Relief',
                'specialty': 'General Medicine',
            },
            {
                'id': 'dyslipidemia',
                'name': 'Dyslipidemia',
                'condition': 'High Cholesterol',
                'specialty': 'General Medicine',
            },
        ]

    # Template definitions

    @staticmethod
    def dm_type2_initial() -> PrescriptionTemplate:
        """Type 2 Diabetes - Initial monotherapy (Metformin)."""
        items = [
            PrescriptionItem(
                drug_name="Metformin",
                strength="500mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.BD,
                    frequency_detail="1-0-1",
                    duration_days=30,
                    route=RouteOfAdministration.ORAL,
                    timing="after food",
                    take_with_food=True,
                ),
                quantity=60,
                quantity_unit="tablets",
                item_sequence=1,
                instructions="Take after breakfast and dinner to reduce stomach upset",
            ),
        ]

        advice = """• Check fasting blood sugar weekly
• Follow diabetic diet (low sugar, complex carbs)
• Walk 30 minutes daily
• Avoid sugary drinks and processed foods
• Monitor for hypoglycemia symptoms
• Follow up after 1 month with HbA1c"""

        return PrescriptionTemplate(
            id="dm_type2_initial",
            name="Type 2 Diabetes - Initial Therapy",
            description="Metformin monotherapy for newly diagnosed T2DM",
            specialty="General Medicine",
            condition="Type 2 Diabetes Mellitus",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["diabetes", "metformin", "initial"],
        )

    @staticmethod
    def dm_type2_dual_therapy() -> PrescriptionTemplate:
        """Type 2 Diabetes - Dual therapy (Metformin + Sulfonylurea)."""
        items = [
            PrescriptionItem(
                drug_name="Metformin",
                strength="500mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.BD,
                    frequency_detail="1-0-1",
                    duration_days=30,
                    route=RouteOfAdministration.ORAL,
                    timing="after food",
                ),
                quantity=60,
                quantity_unit="tablets",
                item_sequence=1,
            ),
            PrescriptionItem(
                drug_name="Glimepiride",
                strength="2mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.OD,
                    frequency_detail="1-0-0",
                    duration_days=30,
                    route=RouteOfAdministration.ORAL,
                    timing="before breakfast",
                    take_on_empty_stomach=True,
                ),
                quantity=30,
                quantity_unit="tablets",
                item_sequence=2,
                instructions="Take before breakfast. Keep sugar/snack handy for low sugar",
            ),
        ]

        advice = """• Check fasting blood sugar weekly
• Monitor for hypoglycemia (shaking, sweating, dizziness)
• Keep sugar candies handy
• Follow diabetic diet
• Walk 30 minutes daily
• Follow up after 1 month with HbA1c"""

        return PrescriptionTemplate(
            id="dm_type2_dual",
            name="Type 2 Diabetes - Dual Therapy",
            description="Metformin + Sulfonylurea for uncontrolled T2DM",
            specialty="General Medicine",
            condition="Type 2 Diabetes Mellitus",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["diabetes", "metformin", "glimepiride", "dual"],
        )

    @staticmethod
    def htn_initial() -> PrescriptionTemplate:
        """Hypertension - Initial monotherapy."""
        items = [
            PrescriptionItem(
                drug_name="Amlodipine",
                strength="5mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.OD,
                    frequency_detail="0-0-1",
                    duration_days=30,
                    route=RouteOfAdministration.ORAL,
                    timing="at bedtime",
                ),
                quantity=30,
                quantity_unit="tablets",
                item_sequence=1,
                instructions="Take at same time daily, preferably at night",
            ),
        ]

        advice = """• Monitor BP daily (morning & evening)
• Target BP: <140/90 mmHg (or <130/80 if diabetic)
• Low salt diet (< 5g/day)
• Regular exercise 30 min/day
• Reduce stress
• Avoid smoking and excess alcohol
• Follow up after 2 weeks"""

        return PrescriptionTemplate(
            id="htn_initial",
            name="Hypertension - Initial Therapy",
            description="Amlodipine monotherapy for newly diagnosed HTN",
            specialty="General Medicine",
            condition="Hypertension",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["hypertension", "amlodipine", "initial"],
        )

    @staticmethod
    def htn_dual_therapy() -> PrescriptionTemplate:
        """Hypertension - Dual therapy (ACE-I + CCB)."""
        items = [
            PrescriptionItem(
                drug_name="Amlodipine",
                strength="5mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.OD,
                    duration_days=30,
                    route=RouteOfAdministration.ORAL,
                ),
                quantity=30,
                quantity_unit="tablets",
                item_sequence=1,
            ),
            PrescriptionItem(
                drug_name="Ramipril",
                strength="5mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.OD,
                    frequency_detail="1-0-0",
                    duration_days=30,
                    route=RouteOfAdministration.ORAL,
                    timing="in the morning",
                ),
                quantity=30,
                quantity_unit="tablets",
                item_sequence=2,
            ),
        ]

        return PrescriptionTemplate(
            id="htn_dual",
            name="Hypertension - Dual Therapy",
            description="ACE-I + CCB for uncontrolled HTN",
            specialty="General Medicine",
            condition="Hypertension",
            items=items,
            created_by="system",
            is_public=True,
            tags=["hypertension", "dual", "ace-i", "ccb"],
        )

    @staticmethod
    def urti() -> PrescriptionTemplate:
        """Upper Respiratory Tract Infection."""
        items = [
            PrescriptionItem(
                drug_name="Paracetamol",
                strength="500mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.TDS,
                    frequency_detail="1-1-1",
                    duration_days=5,
                    route=RouteOfAdministration.ORAL,
                    timing="after food",
                ),
                quantity=15,
                quantity_unit="tablets",
                item_sequence=1,
                instructions="Take for fever or body ache. Max 4 tablets/day",
            ),
            PrescriptionItem(
                drug_name="Cetirizine",
                strength="10mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.OD,
                    frequency_detail="0-0-1",
                    duration_days=5,
                    route=RouteOfAdministration.ORAL,
                    timing="at bedtime",
                ),
                quantity=5,
                quantity_unit="tablets",
                item_sequence=2,
                instructions="For runny nose and sneezing. May cause drowsiness",
            ),
        ]

        advice = """• Drink plenty of warm fluids
• Gargle with warm salt water 3-4 times/day
• Steam inhalation 2-3 times/day
• Rest adequately
• If fever persists >3 days or difficulty breathing, consult immediately
• Avoid cold drinks and ice cream"""

        return PrescriptionTemplate(
            id="urti",
            name="Upper Respiratory Tract Infection",
            description="Symptomatic treatment for common cold/URTI",
            specialty="General Medicine",
            condition="URTI / Common Cold",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["urti", "cold", "fever", "symptomatic"],
        )

    @staticmethod
    def uti() -> PrescriptionTemplate:
        """Urinary Tract Infection."""
        items = [
            PrescriptionItem(
                drug_name="Nitrofurantoin",
                strength="100mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.BD,
                    frequency_detail="1-0-1",
                    duration_days=5,
                    route=RouteOfAdministration.ORAL,
                    timing="after food",
                ),
                quantity=10,
                quantity_unit="tablets",
                item_sequence=1,
                instructions="Complete full course even if symptoms improve",
                schedule=DrugSchedule.H,
            ),
        ]

        advice = """• Drink plenty of water (3-4 liters/day)
• Cranberry juice may help
• Maintain good hygiene
• Don't hold urine for long periods
• Complete antibiotic course
• If symptoms don't improve in 48h, consult
• Follow up with urine culture if recurrent"""

        return PrescriptionTemplate(
            id="uti",
            name="Urinary Tract Infection",
            description="Antibiotic for uncomplicated UTI",
            specialty="General Medicine",
            condition="UTI",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["uti", "antibiotic", "nitrofurantoin"],
        )

    @staticmethod
    def gastritis() -> PrescriptionTemplate:
        """Gastritis / GERD."""
        items = [
            PrescriptionItem(
                drug_name="Pantoprazole",
                strength="40mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.OD,
                    frequency_detail="1-0-0",
                    duration_days=14,
                    route=RouteOfAdministration.ORAL,
                    timing="before breakfast",
                    take_on_empty_stomach=True,
                ),
                quantity=14,
                quantity_unit="tablets",
                item_sequence=1,
                instructions="Take on empty stomach, 30 min before breakfast",
            ),
        ]

        advice = """• Avoid spicy, oily, and acidic foods
• Small frequent meals (don't skip meals)
• Avoid coffee, alcohol, smoking
• Don't lie down immediately after eating (wait 2-3h)
• Elevate head of bed if night-time symptoms
• Reduce stress
• If symptoms persist beyond 2 weeks, consult for endoscopy"""

        return PrescriptionTemplate(
            id="gastritis",
            name="Gastritis / GERD",
            description="PPI for gastritis/acid reflux",
            specialty="General Medicine",
            condition="Gastritis / GERD",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["gastritis", "gerd", "ppi", "pantoprazole"],
        )

    @staticmethod
    def fever_pain() -> PrescriptionTemplate:
        """Symptomatic relief for fever and pain."""
        items = [
            PrescriptionItem(
                drug_name="Paracetamol",
                strength="500mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1-2 tablets",
                    frequency=Frequency.TDS,
                    duration_days=3,
                    route=RouteOfAdministration.ORAL,
                    timing="after food",
                    prn_indication="for fever > 100°F or pain",
                    max_dose_per_day="8 tablets (4g)",
                ),
                quantity=24,
                quantity_unit="tablets",
                item_sequence=1,
                instructions="Take when needed for fever or pain. Max 4g/day",
            ),
        ]

        advice = """• Take plenty of fluids
• Rest adequately
• Cold sponging if high fever
• If fever persists >3 days, consult
• Monitor for danger signs (difficulty breathing, altered consciousness)"""

        return PrescriptionTemplate(
            id="fever_pain",
            name="Fever & Pain Relief",
            description="Symptomatic relief",
            specialty="General Medicine",
            condition="Fever / Pain",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["fever", "pain", "symptomatic", "paracetamol"],
        )

    @staticmethod
    def dyslipidemia() -> PrescriptionTemplate:
        """Dyslipidemia / High Cholesterol."""
        items = [
            PrescriptionItem(
                drug_name="Atorvastatin",
                strength="10mg",
                dosage_form=DosageForm.TABLET,
                dosage=Dosage(
                    dose="1 tablet",
                    frequency=Frequency.OD,
                    frequency_detail="0-0-1",
                    duration_days=30,
                    route=RouteOfAdministration.ORAL,
                    timing="at night after dinner",
                    avoid_alcohol=True,
                ),
                quantity=30,
                quantity_unit="tablets",
                item_sequence=1,
                instructions="Take at bedtime. Avoid grapefruit juice",
            ),
        ]

        advice = """• Low fat, low cholesterol diet
• Increase fiber intake (oats, vegetables, fruits)
• Regular exercise 30 min/day
• Avoid trans fats and fried foods
• Maintain healthy weight
• Avoid alcohol
• Check lipid profile after 6 weeks
• Monitor for muscle pain (stop if severe pain)"""

        return PrescriptionTemplate(
            id="dyslipidemia",
            name="Dyslipidemia",
            description="Statin for high cholesterol",
            specialty="General Medicine",
            condition="Dyslipidemia / High Cholesterol",
            items=items,
            advice=advice,
            created_by="system",
            is_public=True,
            tags=["dyslipidemia", "cholesterol", "statin", "atorvastatin"],
        )


class CustomTemplateManager:
    """Manage custom doctor templates."""

    def __init__(self, storage=None):
        """
        Initialize manager.

        Args:
            storage: Storage backend for templates (database, file, etc.)
        """
        self.storage = storage or {}  # In-memory storage for demo

    def create_template(
        self,
        name: str,
        items: List[PrescriptionItem],
        doctor_id: str,
        description: Optional[str] = None,
        specialty: Optional[str] = None,
        condition: Optional[str] = None,
        advice: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> PrescriptionTemplate:
        """Create custom template."""
        template = PrescriptionTemplate(
            id=f"custom_{uuid4().hex[:12]}",
            name=name,
            description=description,
            specialty=specialty,
            condition=condition,
            items=items,
            advice=advice,
            created_by=doctor_id,
            is_public=False,
            tags=tags or [],
        )

        # Save to storage
        self.storage[template.id] = template

        return template

    def get_template(self, template_id: str) -> Optional[PrescriptionTemplate]:
        """Get template by ID."""
        return self.storage.get(template_id)

    def list_templates(
        self,
        doctor_id: Optional[str] = None,
        specialty: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> List[PrescriptionTemplate]:
        """List templates with optional filters."""
        templates = list(self.storage.values())

        # Filter by doctor
        if doctor_id:
            templates = [t for t in templates if t.created_by == doctor_id or t.is_public]

        # Filter by specialty
        if specialty:
            templates = [t for t in templates if t.specialty == specialty]

        # Filter by condition
        if condition:
            templates = [t for t in templates if t.condition == condition]

        return templates

    def update_template(
        self,
        template_id: str,
        **updates
    ) -> Optional[PrescriptionTemplate]:
        """Update template."""
        template = self.storage.get(template_id)
        if not template:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        self.storage[template_id] = template
        return template

    def delete_template(self, template_id: str) -> bool:
        """Delete template."""
        if template_id in self.storage:
            del self.storage[template_id]
            return True
        return False


# Example usage
if __name__ == "__main__":
    # List all templates
    templates = TemplateLibrary.list_templates()
    print("Available templates:")
    for t in templates:
        print(f"  - {t['name']} ({t['condition']})")

    # Get specific template
    dm_template = TemplateLibrary.get_template('dm_type2_initial')
    if dm_template:
        print(f"\nTemplate: {dm_template.name}")
        print(f"Items: {len(dm_template.items)}")
        for item in dm_template.items:
            print(f"  - {item.drug_name} {item.strength}")
