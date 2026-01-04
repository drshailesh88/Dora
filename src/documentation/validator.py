"""Documentation Validator for Clinical Documents.

Validates clinical documentation for completeness, accuracy, and compliance.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Union

from .models import (
    DischargeSummary,
    MedicalCertificate,
    OperativeNote,
    ReferralLetter,
    SOAPNote,
)


class ValidationLevel(str, Enum):
    """Validation severity level."""

    ERROR = "error"  # Must fix before signing
    WARNING = "warning"  # Should fix but not blocking
    INFO = "info"  # Informational only


class ValidationIssue:
    """A validation issue."""

    def __init__(
        self,
        level: ValidationLevel,
        field: str,
        message: str,
        suggestion: str = "",
    ):
        """Initialize validation issue.

        Args:
            level: Severity level
            field: Field name
            message: Issue description
            suggestion: How to fix
        """
        self.level = level
        self.field = field
        self.message = message
        self.suggestion = suggestion

    def __str__(self) -> str:
        """Format for display."""
        parts = [f"[{self.level.value.upper()}] {self.field}: {self.message}"]
        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")
        return "\n".join(parts)


class ValidationResult:
    """Result of validation."""

    def __init__(self):
        """Initialize validation result."""
        self.issues: list[ValidationIssue] = []

    def add_error(self, field: str, message: str, suggestion: str = ""):
        """Add an error."""
        self.issues.append(ValidationIssue(ValidationLevel.ERROR, field, message, suggestion))

    def add_warning(self, field: str, message: str, suggestion: str = ""):
        """Add a warning."""
        self.issues.append(
            ValidationIssue(ValidationLevel.WARNING, field, message, suggestion)
        )

    def add_info(self, field: str, message: str, suggestion: str = ""):
        """Add an info."""
        self.issues.append(ValidationIssue(ValidationLevel.INFO, field, message, suggestion))

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return not self.has_errors

    @property
    def has_errors(self) -> bool:
        """Check if there are errors."""
        return any(issue.level == ValidationLevel.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return any(issue.level == ValidationLevel.WARNING for issue in self.issues)

    @property
    def completeness_score(self) -> float:
        """Calculate completeness score (0-100).

        Lower score for more issues.
        """
        if not self.issues:
            return 100.0

        errors = sum(1 for i in self.issues if i.level == ValidationLevel.ERROR)
        warnings = sum(1 for i in self.issues if i.level == ValidationLevel.WARNING)

        # Errors count double
        total_issues = (errors * 2) + warnings

        # Each issue reduces score by 5 points, minimum 0
        return max(0, 100 - (total_issues * 5))

    def get_summary(self) -> str:
        """Get validation summary."""
        if not self.issues:
            return "✓ Document validation passed with no issues."

        lines = [f"Document Completeness: {self.completeness_score:.0f}%", ""]

        errors = [i for i in self.issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in self.issues if i.level == ValidationLevel.WARNING]
        infos = [i for i in self.issues if i.level == ValidationLevel.INFO]

        if errors:
            lines.append(f"✗ {len(errors)} Error(s) - Must fix before signing:")
            for issue in errors:
                lines.append(f"  - {issue.field}: {issue.message}")
            lines.append("")

        if warnings:
            lines.append(f"⚠ {len(warnings)} Warning(s) - Should review:")
            for issue in warnings:
                lines.append(f"  - {issue.field}: {issue.message}")
            lines.append("")

        if infos:
            lines.append(f"ℹ {len(infos)} Info:")
            for issue in infos:
                lines.append(f"  - {issue.field}: {issue.message}")

        return "\n".join(lines)


class DocumentValidator:
    """Validate clinical documentation."""

    def __init__(self):
        """Initialize validator."""
        # ICD-10 pattern: Letter + 2-3 digits + optional decimal + 1-2 digits
        self.icd10_pattern = re.compile(r"^[A-TV-Z][0-9]{2}(?:\.[0-9]{1,2})?$")

    def validate_soap_note(self, soap: SOAPNote) -> ValidationResult:
        """Validate SOAP note.

        Args:
            soap: SOAP note to validate

        Returns:
            Validation result
        """
        result = ValidationResult()

        # Required fields
        if not soap.chief_complaint or len(soap.chief_complaint.strip()) < 3:
            result.add_error(
                "chief_complaint",
                "Chief complaint is required and must be descriptive",
                "Add a clear chief complaint (e.g., 'Chest pain for 2 hours')",
            )

        if not soap.history_present_illness or len(soap.history_present_illness.strip()) < 10:
            result.add_error(
                "history_present_illness",
                "History of present illness is too brief",
                "Provide detailed HPI including onset, duration, severity, etc.",
            )

        # Vitals check
        if not soap.vitals:
            result.add_warning(
                "vitals",
                "No vital signs recorded",
                "Record at least BP, HR, RR, Temp",
            )
        else:
            self._validate_vitals(soap.vitals, result)

        # Assessment
        if not soap.diagnoses:
            result.add_error(
                "diagnoses",
                "No diagnoses documented",
                "Add at least one diagnosis",
            )
        else:
            self._validate_diagnoses(soap.diagnoses, result)

        # Plan
        if not soap.plan_medications and not soap.plan_investigations and not soap.plan_procedures:
            result.add_warning(
                "plan",
                "Plan is incomplete - no medications, investigations, or procedures",
                "Add treatment plan",
            )

        # Allergies
        if not soap.allergies:
            result.add_info(
                "allergies",
                "No allergies documented - confirm NKDA",
                "Document 'NKDA' if no known drug allergies",
            )

        # Follow-up
        if not soap.plan_followup:
            result.add_warning(
                "plan_followup",
                "No follow-up plan documented",
                "Specify when patient should return",
            )

        return result

    def validate_discharge_summary(
        self, discharge: DischargeSummary
    ) -> ValidationResult:
        """Validate discharge summary."""
        result = ValidationResult()

        # Required fields
        if not discharge.chief_complaint:
            result.add_error("chief_complaint", "Chief complaint is required")

        if not discharge.admitting_diagnosis:
            result.add_error("admitting_diagnosis", "Admitting diagnosis is required")

        if not discharge.final_diagnosis:
            result.add_error("final_diagnosis", "Final diagnosis is required")

        if not discharge.hospital_course or len(discharge.hospital_course.strip()) < 20:
            result.add_error(
                "hospital_course",
                "Hospital course must be detailed",
                "Describe what happened during the hospital stay",
            )

        # Discharge medications
        if not discharge.discharge_medications:
            result.add_warning(
                "discharge_medications",
                "No discharge medications listed",
                "List all medications patient should continue",
            )

        # Discharge instructions
        if not discharge.discharge_instructions or len(discharge.discharge_instructions.strip()) < 10:
            result.add_error(
                "discharge_instructions",
                "Discharge instructions are required",
                "Provide clear instructions for patient",
            )

        # Follow-up
        if not discharge.followup_instructions:
            result.add_error(
                "followup_instructions",
                "Follow-up instructions are required",
                "Specify when and where to follow up",
            )

        # Warning signs
        if not discharge.warning_signs:
            result.add_warning(
                "warning_signs",
                "No warning signs listed",
                "List signs that warrant emergency return",
            )

        # Date logic
        if discharge.discharge_date < discharge.admission_date:
            result.add_error(
                "discharge_date",
                "Discharge date cannot be before admission date",
            )

        return result

    def validate_referral_letter(self, referral: ReferralLetter) -> ValidationResult:
        """Validate referral letter."""
        result = ValidationResult()

        if not referral.reason_for_referral:
            result.add_error("reason_for_referral", "Reason for referral is required")

        if not referral.clinical_summary or len(referral.clinical_summary.strip()) < 10:
            result.add_error(
                "clinical_summary",
                "Clinical summary must be detailed",
                "Provide relevant clinical information for specialist",
            )

        if not referral.diagnoses:
            result.add_warning(
                "diagnoses",
                "No diagnoses listed",
                "Include relevant diagnoses",
            )

        if not referral.current_medications:
            result.add_info(
                "current_medications",
                "No current medications listed",
            )

        return result

    def validate_operative_note(self, op_note: OperativeNote) -> ValidationResult:
        """Validate operative note."""
        result = ValidationResult()

        # Required fields
        required_fields = [
            ("preop_diagnosis", "Pre-operative diagnosis"),
            ("indication_for_surgery", "Indication for surgery"),
            ("procedure_performed", "Procedure performed"),
            ("operative_findings", "Operative findings"),
            ("technique", "Surgical technique"),
            ("postop_diagnosis", "Post-operative diagnosis"),
            ("postop_condition", "Post-operative condition"),
            ("postop_instructions", "Post-operative instructions"),
        ]

        for field, name in required_fields:
            value = getattr(op_note, field, None)
            if not value or (isinstance(value, str) and len(value.strip()) < 3):
                result.add_error(field, f"{name} is required")

        # Technique should be detailed
        if op_note.technique and len(op_note.technique.strip()) < 50:
            result.add_warning(
                "technique",
                "Surgical technique description is brief",
                "Provide step-by-step description of procedure",
            )

        return result

    def _validate_vitals(self, vitals: Any, result: ValidationResult):
        """Validate vital signs."""
        # Blood pressure
        if vitals.bp_systolic:
            if vitals.bp_systolic < 60 or vitals.bp_systolic > 250:
                result.add_warning(
                    "vitals.bp_systolic",
                    f"Systolic BP {vitals.bp_systolic} is unusual - verify",
                )
            if not vitals.bp_diastolic:
                result.add_warning(
                    "vitals.bp_diastolic",
                    "Diastolic BP missing",
                )

        # Heart rate
        if vitals.heart_rate:
            if vitals.heart_rate < 30 or vitals.heart_rate > 250:
                result.add_warning(
                    "vitals.heart_rate",
                    f"Heart rate {vitals.heart_rate} is unusual - verify",
                )

        # Temperature
        if vitals.temperature:
            if vitals.temperature < 90 or vitals.temperature > 110:
                result.add_warning(
                    "vitals.temperature",
                    f"Temperature {vitals.temperature} is unusual - verify",
                )

        # SpO2
        if vitals.spo2:
            if vitals.spo2 < 50 or vitals.spo2 > 100:
                result.add_error(
                    "vitals.spo2",
                    f"SpO2 {vitals.spo2} is invalid - must be 0-100",
                )

    def _validate_diagnoses(self, diagnoses: list[Any], result: ValidationResult):
        """Validate diagnoses."""
        has_primary = any(d.is_primary for d in diagnoses)

        if not has_primary and len(diagnoses) > 1:
            result.add_warning(
                "diagnoses",
                "No primary diagnosis marked",
                "Mark the principal diagnosis as primary",
            )

        # Validate ICD-10 codes
        for i, diag in enumerate(diagnoses):
            if diag.icd10_code and not self.is_valid_icd10(diag.icd10_code):
                result.add_warning(
                    f"diagnoses[{i}].icd10_code",
                    f"ICD-10 code '{diag.icd10_code}' format appears invalid",
                    "Verify ICD-10 code format (e.g., I21.0, E11.9)",
                )

    def is_valid_icd10(self, code: str) -> bool:
        """Check if ICD-10 code format is valid.

        Args:
            code: ICD-10 code

        Returns:
            True if valid format
        """
        return bool(self.icd10_pattern.match(code.upper()))

    def validate_drug_name(self, drug_name: str) -> bool:
        """Validate drug name (basic check).

        Args:
            drug_name: Drug name

        Returns:
            True if appears valid
        """
        # Basic checks: at least 3 characters, starts with letter
        if len(drug_name) < 3:
            return False
        if not drug_name[0].isalpha():
            return False
        return True


def validate_document(
    document: Union[SOAPNote, DischargeSummary, ReferralLetter, OperativeNote, MedicalCertificate],
) -> ValidationResult:
    """Validate any clinical document.

    Args:
        document: Document to validate

    Returns:
        Validation result
    """
    validator = DocumentValidator()

    if isinstance(document, SOAPNote):
        return validator.validate_soap_note(document)
    elif isinstance(document, DischargeSummary):
        return validator.validate_discharge_summary(document)
    elif isinstance(document, ReferralLetter):
        return validator.validate_referral_letter(document)
    elif isinstance(document, OperativeNote):
        return validator.validate_operative_note(document)
    else:
        result = ValidationResult()
        result.add_info("document", f"Validation not implemented for {type(document).__name__}")
        return result
