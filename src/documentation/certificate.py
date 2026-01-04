"""Medical Certificate Generator for Dora.

Generates various types of medical certificates for patients.
"""

from datetime import datetime, timedelta
from typing import Optional

from .models import CertificateType, MedicalCertificate, Patient, Provider


class MedicalCertificateGenerator:
    """Generate medical certificates."""

    def generate_fitness_certificate(
        self,
        patient: Patient,
        provider: Provider,
        purpose: str,
        fitness_statement: str,
        restrictions: Optional[str] = None,
        additional_notes: Optional[str] = None,
    ) -> MedicalCertificate:
        """Generate fitness certificate.

        Args:
            patient: Patient information
            provider: Provider information
            purpose: Purpose of certificate
            fitness_statement: Fitness statement (e.g., "Fit for duty")
            restrictions: Any restrictions
            additional_notes: Additional notes

        Returns:
            Fitness certificate
        """
        return MedicalCertificate(
            patient=patient,
            provider=provider,
            certificate_type=CertificateType.FITNESS,
            purpose=purpose,
            fitness_statement=fitness_statement,
            restrictions=restrictions,
            additional_notes=additional_notes,
        )

    def generate_sick_leave_certificate(
        self,
        patient: Patient,
        provider: Provider,
        diagnosis: str,
        from_date: datetime,
        days_of_rest: int,
        purpose: str = "Sick leave from work/school",
        additional_notes: Optional[str] = None,
    ) -> MedicalCertificate:
        """Generate sick leave certificate.

        Args:
            patient: Patient information
            provider: Provider information
            diagnosis: Diagnosis (can be general like "acute illness")
            from_date: Start date of sick leave
            days_of_rest: Number of days of rest advised
            purpose: Purpose of certificate
            additional_notes: Additional notes

        Returns:
            Sick leave certificate
        """
        to_date = from_date + timedelta(days=days_of_rest)

        return MedicalCertificate(
            patient=patient,
            provider=provider,
            certificate_type=CertificateType.SICK_LEAVE,
            purpose=purpose,
            diagnosis=diagnosis,
            from_date=from_date,
            to_date=to_date,
            days_of_rest=days_of_rest,
            additional_notes=additional_notes,
        )

    def generate_travel_fitness(
        self,
        patient: Patient,
        provider: Provider,
        destination: Optional[str] = None,
        restrictions: Optional[str] = None,
    ) -> MedicalCertificate:
        """Generate fitness to travel certificate.

        Args:
            patient: Patient information
            provider: Provider information
            destination: Travel destination (optional)
            restrictions: Travel restrictions (e.g., "Avoid high altitude")

        Returns:
            Travel fitness certificate
        """
        purpose = f"Fitness to travel"
        if destination:
            purpose += f" to {destination}"

        fitness_statement = "Medically fit to travel"

        return MedicalCertificate(
            patient=patient,
            provider=provider,
            certificate_type=CertificateType.FITNESS_TRAVEL,
            purpose=purpose,
            fitness_statement=fitness_statement,
            restrictions=restrictions,
        )

    def generate_surgery_fitness(
        self,
        patient: Patient,
        provider: Provider,
        procedure: str,
        fitness_statement: str = "Fit for surgery under anesthesia",
        restrictions: Optional[str] = None,
        additional_notes: Optional[str] = None,
    ) -> MedicalCertificate:
        """Generate fitness for surgery certificate.

        Args:
            patient: Patient information
            provider: Provider information
            procedure: Planned surgical procedure
            fitness_statement: Fitness statement
            restrictions: Any restrictions or precautions
            additional_notes: Additional notes (e.g., cardiac clearance)

        Returns:
            Surgery fitness certificate
        """
        purpose = f"Pre-operative clearance for {procedure}"

        return MedicalCertificate(
            patient=patient,
            provider=provider,
            certificate_type=CertificateType.FITNESS_SURGERY,
            purpose=purpose,
            fitness_statement=fitness_statement,
            restrictions=restrictions,
            additional_notes=additional_notes,
        )

    def generate_sports_fitness(
        self,
        patient: Patient,
        provider: Provider,
        sport: str,
        level: str = "recreational",
        restrictions: Optional[str] = None,
    ) -> MedicalCertificate:
        """Generate sports fitness certificate.

        Args:
            patient: Patient information
            provider: Provider information
            sport: Sport/activity
            level: Level (recreational, competitive, professional)
            restrictions: Any restrictions

        Returns:
            Sports fitness certificate
        """
        purpose = f"Fitness for {level} {sport}"
        fitness_statement = f"Medically fit for {level} level {sport}"

        return MedicalCertificate(
            patient=patient,
            provider=provider,
            certificate_type=CertificateType.FITNESS_SPORTS,
            purpose=purpose,
            fitness_statement=fitness_statement,
            restrictions=restrictions,
        )

    def format_certificate(self, certificate: MedicalCertificate) -> str:
        """Format certificate for printing.

        Args:
            certificate: Medical certificate

        Returns:
            Formatted certificate text
        """
        lines = ["MEDICAL CERTIFICATE", "=" * 60, ""]

        # Provider details
        lines.append(f"ISSUED BY: {certificate.provider.name}")
        if certificate.provider.qualification:
            lines.append(f"           {certificate.provider.qualification}")
        if certificate.provider.registration_number:
            lines.append(
                f"           Reg. No: {certificate.provider.registration_number}"
            )
        lines.append("")

        # Date
        lines.append(f"Date: {certificate.date.strftime('%d-%b-%Y')}")
        lines.append("")

        # Certificate content
        lines.append("TO WHOM IT MAY CONCERN")
        lines.append("")

        # Patient details
        lines.append(
            f"This is to certify that {certificate.patient.name}, "
            f"{certificate.patient.age} years, {certificate.patient.gender}, "
        )
        if certificate.patient.mrn:
            lines.append(f"MRN: {certificate.patient.mrn},")
        lines.append("")

        # Type-specific content
        if certificate.certificate_type == CertificateType.SICK_LEAVE:
            lines.append(
                f"is suffering from {certificate.diagnosis} and is advised "
                f"rest from {certificate.from_date.strftime('%d-%b-%Y')} to "
                f"{certificate.to_date.strftime('%d-%b-%Y')} ({certificate.days_of_rest} days)."
            )
        elif certificate.fitness_statement:
            lines.append(f"is {certificate.fitness_statement}.")

        if certificate.restrictions:
            lines.append("")
            lines.append(f"Restrictions: {certificate.restrictions}")

        if certificate.additional_notes:
            lines.append("")
            lines.append(f"Note: {certificate.additional_notes}")

        lines.append("")
        lines.append(f"Purpose: {certificate.purpose}")
        lines.append("")

        # Signature
        lines.append("_" * 30)
        lines.append(f"{certificate.provider.name}")
        if certificate.provider.qualification:
            lines.append(certificate.provider.qualification)
        if certificate.provider.registration_number:
            lines.append(f"Reg. No: {certificate.provider.registration_number}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


def generate_sick_leave(
    patient: Patient,
    provider: Provider,
    diagnosis: str,
    days: int = 3,
    from_date: Optional[datetime] = None,
) -> MedicalCertificate:
    """Convenience function to generate sick leave certificate.

    Args:
        patient: Patient information
        provider: Provider information
        diagnosis: Diagnosis
        days: Number of days of rest (default 3)
        from_date: Start date (default today)

    Returns:
        Sick leave certificate
    """
    generator = MedicalCertificateGenerator()
    return generator.generate_sick_leave_certificate(
        patient=patient,
        provider=provider,
        diagnosis=diagnosis,
        from_date=from_date or datetime.now(),
        days_of_rest=days,
    )


def generate_fitness_certificate(
    patient: Patient,
    provider: Provider,
    purpose: str,
    fit_for: str = "normal duties",
    restrictions: Optional[str] = None,
) -> MedicalCertificate:
    """Convenience function to generate fitness certificate.

    Args:
        patient: Patient information
        provider: Provider information
        purpose: Purpose of certificate
        fit_for: What patient is fit for
        restrictions: Any restrictions

    Returns:
        Fitness certificate
    """
    generator = MedicalCertificateGenerator()
    return generator.generate_fitness_certificate(
        patient=patient,
        provider=provider,
        purpose=purpose,
        fitness_statement=f"Fit for {fit_for}",
        restrictions=restrictions,
    )
