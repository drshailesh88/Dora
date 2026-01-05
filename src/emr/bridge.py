"""EMR Bridge for connecting to DocAssist EMR."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.config import settings
from src.core.models import PatientContext


class EMRBridge:
    """
    Bridge to DocAssist EMR for patient context.

    Connects to the EMR's SQLite database to retrieve:
    - Patient demographics
    - Visit history
    - Current medications
    - Investigations
    - Diagnoses
    """

    def __init__(self, db_path: str | Path | None = None):
        """
        Initialize EMR bridge.

        Args:
            db_path: Path to EMR SQLite database.
        """
        self.db_path = Path(db_path) if db_path else None
        if self.db_path is None and settings.emr_database_path:
            self.db_path = Path(settings.emr_database_path)

        self._connection: sqlite3.Connection | None = None

    @property
    def is_connected(self) -> bool:
        """Check if EMR database is available."""
        return self.db_path is not None and self.db_path.exists()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._connection is None:
            if not self.is_connected:
                raise ConnectionError("EMR database not configured or not found")
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def get_patient(self, patient_id: int) -> dict | None:
        """
        Get patient demographics.

        Args:
            patient_id: Patient ID in EMR.

        Returns:
            Patient dict or None if not found.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT id, uhid, name, age, gender, phone, address, created_at
            FROM patients
            WHERE id = ?
            """,
            (patient_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def search_patients(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search patients by name or UHID.

        Args:
            query: Search query.
            limit: Max results.

        Returns:
            List of matching patients.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT id, uhid, name, age, gender, phone
            FROM patients
            WHERE name LIKE ? OR uhid LIKE ?
            ORDER BY name
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_patient_visits(
        self, patient_id: int, limit: int = 10
    ) -> list[dict]:
        """
        Get patient's recent visits.

        Args:
            patient_id: Patient ID.
            limit: Max visits to return.

        Returns:
            List of visit records.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT id, visit_date, chief_complaint, diagnosis, notes, prescription
            FROM visits
            WHERE patient_id = ?
            ORDER BY visit_date DESC
            LIMIT ?
            """,
            (patient_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_patient_medications(self, patient_id: int) -> list[str]:
        """
        Get patient's current medications from recent prescriptions.

        Args:
            patient_id: Patient ID.

        Returns:
            List of medication names.
        """
        import json

        visits = self.get_patient_visits(patient_id, limit=3)
        medications = set()

        for visit in visits:
            if visit.get("prescription"):
                try:
                    rx = json.loads(visit["prescription"])
                    for med in rx.get("medications", []):
                        med_name = med.get("drug_name", "")
                        if med_name:
                            medications.add(med_name)
                except (json.JSONDecodeError, TypeError):
                    pass

        return list(medications)

    def get_patient_diagnoses(self, patient_id: int) -> list[str]:
        """
        Get patient's diagnoses from visits.

        Args:
            patient_id: Patient ID.

        Returns:
            List of diagnoses.
        """
        visits = self.get_patient_visits(patient_id, limit=10)
        diagnoses = set()

        for visit in visits:
            if visit.get("diagnosis"):
                # Handle comma-separated diagnoses
                for dx in visit["diagnosis"].split(","):
                    dx = dx.strip()
                    if dx:
                        diagnoses.add(dx)

        return list(diagnoses)

    def get_patient_investigations(
        self, patient_id: int, limit: int = 20
    ) -> list[dict]:
        """
        Get patient's investigations/lab results.

        Args:
            patient_id: Patient ID.
            limit: Max results.

        Returns:
            List of investigation records.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT id, test_name, result, unit, reference_range, test_date, abnormal
            FROM investigations
            WHERE patient_id = ?
            ORDER BY test_date DESC
            LIMIT ?
            """,
            (patient_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_patient_context(self, patient_id: int) -> PatientContext | None:
        """
        Build full patient context for RAG.

        Args:
            patient_id: Patient ID.

        Returns:
            PatientContext object or None.
        """
        patient = self.get_patient(patient_id)
        if not patient:
            return None

        medications = self.get_patient_medications(patient_id)
        diagnoses = self.get_patient_diagnoses(patient_id)
        investigations = self.get_patient_investigations(patient_id, limit=10)

        # Build summary
        summary_parts = [
            f"{patient['name']}, {patient['age']}y {patient['gender']}"
        ]
        if diagnoses:
            summary_parts.append(f"Known: {', '.join(diagnoses[:5])}")
        if medications:
            summary_parts.append(f"On: {', '.join(medications[:5])}")

        # Get allergies from EMR if allergies table exists
        allergies = self.get_patient_allergies(patient_id)

        return PatientContext(
            patient_id=patient_id,
            name=patient["name"],
            age=patient["age"],
            gender=patient["gender"],
            active_diagnoses=diagnoses,
            current_medications=medications,
            allergies=allergies,
            recent_investigations=investigations,
            summary=" | ".join(summary_parts),
        )

    def get_patient_allergies(self, patient_id: int) -> list[str]:
        """
        Get patient's allergies from EMR.

        Args:
            patient_id: Patient ID.

        Returns:
            List of allergen names.
        """
        conn = self._get_connection()

        try:
            # Try to fetch from allergies table if it exists
            cursor = conn.execute(
                """
                SELECT allergen FROM allergies
                WHERE patient_id = ?
                ORDER BY severity DESC
                """,
                (patient_id,),
            )
            allergies = [row["allergen"] for row in cursor.fetchall()]
            return allergies
        except Exception:
            # Allergies table might not exist in older EMR schemas
            # Fall back to checking visits notes for allergies
            try:
                visits = self.get_patient_visits(patient_id, limit=5)
                allergies_set = set()

                for visit in visits:
                    notes = visit.get("notes", "")
                    # Simple pattern matching for allergies in notes
                    if "allerg" in notes.lower():
                        import re

                        # Look for "Allergies: X, Y, Z" pattern
                        match = re.search(
                            r"allerg(?:y|ies):\s*([^\n]+)", notes, re.IGNORECASE
                        )
                        if match:
                            allergy_text = match.group(1)
                            for allergy in allergy_text.split(","):
                                allergy = allergy.strip()
                                if allergy and allergy.lower() not in [
                                    "none",
                                    "nkda",
                                    "nil",
                                ]:
                                    allergies_set.add(allergy)

                return list(allergies_set)
            except Exception:
                # If all else fails, return empty list
                return []

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
