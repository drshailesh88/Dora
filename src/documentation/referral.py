"""Referral Letter Generator for Dora.

Generates professional referral letters to specialists.
"""

from datetime import datetime
from typing import Any, Optional

from ..llm.client import get_llm_client
from .models import (
    Diagnosis,
    Investigation,
    Medication,
    Patient,
    Provider,
    ReferralLetter,
    UrgencyLevel,
)


class ReferralLetterGenerator:
    """Generate referral letters to specialists using LLM."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize referral letter generator.

        Args:
            model: LLM model to use for generation
        """
        self.llm = get_llm_client()
        self.model = model

    async def generate(
        self,
        patient: Patient,
        referring_provider: Provider,
        specialty: str,
        reason: str,
        clinical_summary: Optional[str] = None,
        specialist: Optional[Provider] = None,
        urgency: UrgencyLevel = UrgencyLevel.ROUTINE,
        diagnoses: Optional[list[Diagnosis]] = None,
        medications: Optional[list[Medication]] = None,
        investigations: Optional[list[Investigation]] = None,
        specific_questions: Optional[list[str]] = None,
    ) -> ReferralLetter:
        """Generate referral letter.

        Args:
            patient: Patient information
            referring_provider: Referring doctor
            specialty: Specialty being referred to
            reason: Reason for referral
            clinical_summary: Clinical summary
            specialist: Specialist provider (if known)
            urgency: Urgency level
            diagnoses: Patient's diagnoses
            medications: Current medications
            investigations: Relevant investigations
            specific_questions: Specific questions for specialist

        Returns:
            Referral letter in draft status
        """
        # Generate clinical summary if not provided
        if not clinical_summary:
            clinical_summary = await self._generate_clinical_summary(
                patient=patient,
                diagnoses=diagnoses or [],
                medications=medications or [],
                reason=reason,
            )

        return ReferralLetter(
            patient=patient,
            referring_provider=referring_provider,
            specialist_provider=specialist,
            specialty=specialty,
            urgency=urgency,
            reason_for_referral=reason,
            clinical_summary=clinical_summary,
            diagnoses=diagnoses or [],
            current_medications=medications or [],
            relevant_investigations=investigations or [],
            specific_questions=specific_questions or [],
        )

    async def generate_from_soap(
        self,
        soap_note: Any,  # SOAPNote type
        specialty: str,
        reason: str,
        specialist: Optional[Provider] = None,
        urgency: UrgencyLevel = UrgencyLevel.ROUTINE,
        specific_questions: Optional[list[str]] = None,
    ) -> ReferralLetter:
        """Generate referral letter from existing SOAP note.

        Args:
            soap_note: Existing SOAP note
            specialty: Specialty to refer to
            reason: Reason for referral
            specialist: Specialist provider
            urgency: Urgency level
            specific_questions: Specific questions

        Returns:
            Referral letter
        """
        # Generate clinical summary from SOAP note
        clinical_summary = await self._generate_summary_from_soap(soap_note, reason)

        return ReferralLetter(
            patient=soap_note.patient,
            referring_provider=soap_note.provider,
            specialist_provider=specialist,
            specialty=specialty,
            urgency=urgency,
            reason_for_referral=reason,
            clinical_summary=clinical_summary,
            diagnoses=soap_note.diagnoses,
            current_medications=soap_note.plan_medications,
            relevant_investigations=soap_note.investigations,
            specific_questions=specific_questions or [],
        )

    async def _generate_clinical_summary(
        self,
        patient: Patient,
        diagnoses: list[Diagnosis],
        medications: list[Medication],
        reason: str,
    ) -> str:
        """Generate clinical summary using LLM.

        Args:
            patient: Patient information
            diagnoses: Patient's diagnoses
            medications: Current medications
            reason: Reason for referral

        Returns:
            Clinical summary text
        """
        diag_text = ", ".join([d.description for d in diagnoses]) if diagnoses else "None"
        med_text = ", ".join([m.name for m in medications]) if medications else "None"

        prompt = f"""Generate a concise clinical summary for a specialist referral.

PATIENT: {patient.name}, {patient.age}y {patient.gender}
DIAGNOSES: {diag_text}
MEDICATIONS: {med_text}
REASON FOR REFERRAL: {reason}

Write a professional 2-3 sentence clinical summary highlighting:
1. Patient's condition
2. Relevant medical history
3. Why referral is needed

Keep it concise and focused on information the specialist needs."""

        summary = await self.llm.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.3,
        )

        return summary.strip()

    async def _generate_summary_from_soap(self, soap_note: Any, reason: str) -> str:
        """Generate clinical summary from SOAP note.

        Args:
            soap_note: SOAP note
            reason: Reason for referral

        Returns:
            Clinical summary
        """
        prompt = f"""Generate a concise clinical summary for a specialist referral based on this SOAP note.

CHIEF COMPLAINT: {soap_note.chief_complaint}
HPI: {soap_note.history_present_illness}
DIAGNOSES: {', '.join([d.description for d in soap_note.diagnoses])}
MEDICATIONS: {', '.join([m.name for m in soap_note.plan_medications])}
REASON FOR REFERRAL: {reason}

Write a professional 2-3 sentence summary for the specialist."""

        summary = await self.llm.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.3,
        )

        return summary.strip()

    def format_letter(self, referral: ReferralLetter) -> str:
        """Format referral letter for printing/display.

        Args:
            referral: Referral letter

        Returns:
            Formatted letter text
        """
        lines = ["REFERRAL LETTER", "=" * 60, ""]

        # From/To
        lines.append(f"From: {referral.referring_provider.name}")
        if referral.referring_provider.qualification:
            lines.append(f"      {referral.referring_provider.qualification}")
        if referral.referring_provider.contact:
            lines.append(f"      Contact: {referral.referring_provider.contact}")
        lines.append("")

        if referral.specialist_provider:
            lines.append(f"To: {referral.specialist_provider.name}")
            if referral.specialist_provider.qualification:
                lines.append(f"    {referral.specialist_provider.qualification}")
        else:
            lines.append(f"To: {referral.specialty} Department")
        lines.append("")

        lines.append(f"Date: {referral.date.strftime('%d-%b-%Y')}")
        if referral.urgency != UrgencyLevel.ROUTINE:
            lines.append(f"URGENCY: {referral.urgency.value.upper()}")
        lines.append("")

        # Greeting
        specialist_name = (
            f"Dr. {referral.specialist_provider.name}"
            if referral.specialist_provider
            else "Colleague"
        )
        lines.append(f"Dear {specialist_name},")
        lines.append("")

        # Patient details
        lines.append(
            f"I am referring {referral.patient.name} ({referral.patient.age}/{referral.patient.gender[0]})"
        )
        if referral.patient.mrn:
            lines.append(f"MRN: {referral.patient.mrn}")
        lines.append(
            f"for {referral.specialty} evaluation and management."
        )
        lines.append("")

        # Reason for referral
        lines.append("REASON FOR REFERRAL:")
        lines.append(referral.reason_for_referral)
        lines.append("")

        # Clinical summary
        lines.append("CLINICAL SUMMARY:")
        lines.append(referral.clinical_summary)
        lines.append("")

        # Diagnoses
        if referral.diagnoses:
            lines.append("DIAGNOSES:")
            for diag in referral.diagnoses:
                if diag.icd10_code:
                    lines.append(f"  - {diag.description} ({diag.icd10_code})")
                else:
                    lines.append(f"  - {diag.description}")
            lines.append("")

        # Current medications
        if referral.current_medications:
            lines.append("CURRENT MEDICATIONS:")
            for med in referral.current_medications:
                lines.append(
                    f"  - {med.name} {med.dosage} {med.route} {med.frequency}"
                )
            lines.append("")

        # Relevant investigations
        if referral.relevant_investigations:
            lines.append("RELEVANT INVESTIGATIONS:")
            for inv in referral.relevant_investigations:
                if inv.value and inv.unit:
                    lines.append(f"  - {inv.name}: {inv.value} {inv.unit}")
                elif inv.result:
                    lines.append(f"  - {inv.name}: {inv.result}")
                else:
                    lines.append(f"  - {inv.name}")
            lines.append("")

        # Specific questions
        if referral.specific_questions:
            lines.append("SPECIFIC QUESTIONS:")
            for i, question in enumerate(referral.specific_questions, 1):
                lines.append(f"  {i}. {question}")
            lines.append("")

        # Closing
        lines.append("Thank you for seeing this patient.")
        lines.append("")
        lines.append("Regards,")
        lines.append(referral.referring_provider.name)
        if referral.referring_provider.qualification:
            lines.append(referral.referring_provider.qualification)
        if referral.referring_provider.registration_number:
            lines.append(f"Reg. No: {referral.referring_provider.registration_number}")
        if referral.referring_provider.contact:
            lines.append(f"Contact: {referral.referring_provider.contact}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


async def generate_referral_letter(
    patient: Patient,
    referring_provider: Provider,
    specialty: str,
    reason: str,
    clinical_summary: Optional[str] = None,
    specialist: Optional[Provider] = None,
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE,
    diagnoses: Optional[list[Diagnosis]] = None,
    medications: Optional[list[Medication]] = None,
    investigations: Optional[list[Investigation]] = None,
    specific_questions: Optional[list[str]] = None,
    model: str = "claude-3-5-sonnet-20241022",
) -> ReferralLetter:
    """Convenience function to generate referral letter.

    Args:
        patient: Patient information
        referring_provider: Referring doctor
        specialty: Specialty being referred to
        reason: Reason for referral
        clinical_summary: Clinical summary (will be generated if not provided)
        specialist: Specialist provider (if known)
        urgency: Urgency level
        diagnoses: Patient's diagnoses
        medications: Current medications
        investigations: Relevant investigations
        specific_questions: Specific questions for specialist
        model: LLM model to use

    Returns:
        Referral letter
    """
    generator = ReferralLetterGenerator(model=model)
    return await generator.generate(
        patient=patient,
        referring_provider=referring_provider,
        specialty=specialty,
        reason=reason,
        clinical_summary=clinical_summary,
        specialist=specialist,
        urgency=urgency,
        diagnoses=diagnoses,
        medications=medications,
        investigations=investigations,
        specific_questions=specific_questions,
    )
