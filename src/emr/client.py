"""EMR API Client for DocAssist EMR integration."""

import time
from typing import Optional

import httpx
from pydantic import BaseModel

from src.core.config import settings

from .models import (
    Allergy,
    Diagnosis,
    Encounter,
    LabResult,
    Medication,
    Order,
    Patient,
    PatientSummary,
    VitalSigns,
)


class EMRConfig(BaseModel):
    """EMR API configuration."""

    base_url: str = "http://localhost:8080/api"  # DocAssist EMR API
    api_key: Optional[str] = None
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_second: float = 10.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        self.last_call_time = time.time()


class EMRClient:
    """
    Client for DocAssist EMR API.

    Provides methods to:
    - Look up patients
    - Retrieve patient data (medications, allergies, labs, etc.)
    - Create orders and clinical notes
    - Handle authentication and rate limiting
    """

    def __init__(
        self,
        config: Optional[EMRConfig] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """
        Initialize EMR client.

        Args:
            config: EMR API configuration
            rate_limiter: Rate limiter for API calls
        """
        self.config = config or EMRConfig()
        self.rate_limiter = rate_limiter or RateLimiter(calls_per_second=10)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=self._get_headers(),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Dora-EMR-Client/1.0",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request arguments

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._get_headers(),
            )

        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                self.rate_limiter.wait_if_needed()
                response = await self._client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    time.sleep(wait_time)
                    continue
                raise

        raise last_exception or Exception("Request failed")

    # ==================== Patient Lookup ====================

    async def get_patient(self, mrn: str) -> Optional[Patient]:
        """
        Get patient by MRN.

        Args:
            mrn: Medical Record Number

        Returns:
            Patient object or None if not found
        """
        try:
            data = await self._request("GET", f"/patients/mrn/{mrn}")
            return Patient(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        """
        Get patient by internal ID.

        Args:
            patient_id: Patient ID

        Returns:
            Patient object or None if not found
        """
        try:
            data = await self._request("GET", f"/patients/{patient_id}")
            return Patient(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def search_patients(
        self, query: str, limit: int = 10
    ) -> list[Patient]:
        """
        Search patients by name or MRN.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching patients
        """
        data = await self._request(
            "GET", "/patients/search", params={"q": query, "limit": limit}
        )
        return [Patient(**p) for p in data.get("results", [])]

    # ==================== Medications ====================

    async def get_current_medications(self, patient_id: int) -> list[Medication]:
        """
        Get patient's current active medications.

        Args:
            patient_id: Patient ID

        Returns:
            List of active medications
        """
        data = await self._request("GET", f"/patients/{patient_id}/medications")
        return [Medication(**m) for m in data.get("medications", [])]

    async def add_medication(self, medication: Medication) -> Medication:
        """
        Add new medication to patient's record.

        Args:
            medication: Medication to add

        Returns:
            Created medication with ID
        """
        data = await self._request(
            "POST",
            f"/patients/{medication.patient_id}/medications",
            json=medication.model_dump(exclude={"id"}),
        )
        return Medication(**data)

    # ==================== Allergies ====================

    async def get_allergies(self, patient_id: int) -> list[Allergy]:
        """
        Get patient's allergies.

        Args:
            patient_id: Patient ID

        Returns:
            List of allergies
        """
        data = await self._request("GET", f"/patients/{patient_id}/allergies")
        return [Allergy(**a) for a in data.get("allergies", [])]

    async def add_allergy(self, allergy: Allergy) -> Allergy:
        """
        Add allergy to patient's record.

        Args:
            allergy: Allergy to add

        Returns:
            Created allergy with ID
        """
        data = await self._request(
            "POST",
            f"/patients/{allergy.patient_id}/allergies",
            json=allergy.model_dump(exclude={"id"}),
        )
        return Allergy(**data)

    # ==================== Vital Signs ====================

    async def get_vital_signs(
        self, patient_id: int, limit: int = 10
    ) -> list[VitalSigns]:
        """
        Get patient's vital signs history.

        Args:
            patient_id: Patient ID
            limit: Max results

        Returns:
            List of vital sign measurements
        """
        data = await self._request(
            "GET", f"/patients/{patient_id}/vitals", params={"limit": limit}
        )
        return [VitalSigns(**v) for v in data.get("vitals", [])]

    async def add_vital_signs(self, vitals: VitalSigns) -> VitalSigns:
        """
        Record vital signs for patient.

        Args:
            vitals: Vital signs to record

        Returns:
            Created vital signs with ID
        """
        # Auto-calculate BMI if not provided
        if not vitals.bmi:
            vitals.bmi = vitals.calculate_bmi()

        data = await self._request(
            "POST",
            f"/patients/{vitals.patient_id}/vitals",
            json=vitals.model_dump(exclude={"id"}),
        )
        return VitalSigns(**data)

    # ==================== Lab Results ====================

    async def get_lab_results(
        self, patient_id: int, limit: int = 50
    ) -> list[LabResult]:
        """
        Get patient's lab results.

        Args:
            patient_id: Patient ID
            limit: Max results

        Returns:
            List of lab results
        """
        data = await self._request(
            "GET", f"/patients/{patient_id}/labs", params={"limit": limit}
        )
        return [LabResult(**lab) for lab in data.get("labs", [])]

    async def get_lab_by_name(
        self, patient_id: int, test_name: str, limit: int = 10
    ) -> list[LabResult]:
        """
        Get specific lab test results for patient.

        Args:
            patient_id: Patient ID
            test_name: Name of test
            limit: Max results

        Returns:
            List of matching lab results
        """
        data = await self._request(
            "GET",
            f"/patients/{patient_id}/labs/search",
            params={"test_name": test_name, "limit": limit},
        )
        return [LabResult(**lab) for lab in data.get("labs", [])]

    # ==================== Diagnoses ====================

    async def get_diagnoses(
        self, patient_id: int, active_only: bool = True
    ) -> list[Diagnosis]:
        """
        Get patient's diagnoses.

        Args:
            patient_id: Patient ID
            active_only: Only return active diagnoses

        Returns:
            List of diagnoses
        """
        data = await self._request(
            "GET",
            f"/patients/{patient_id}/diagnoses",
            params={"active_only": active_only},
        )
        return [Diagnosis(**dx) for dx in data.get("diagnoses", [])]

    async def add_diagnosis(self, diagnosis: Diagnosis) -> Diagnosis:
        """
        Add diagnosis to patient's problem list.

        Args:
            diagnosis: Diagnosis to add

        Returns:
            Created diagnosis with ID
        """
        data = await self._request(
            "POST",
            f"/patients/{diagnosis.patient_id}/diagnoses",
            json=diagnosis.model_dump(exclude={"id"}),
        )
        return Diagnosis(**data)

    # ==================== Encounters ====================

    async def get_encounters(
        self, patient_id: int, limit: int = 20
    ) -> list[Encounter]:
        """
        Get patient's encounter history.

        Args:
            patient_id: Patient ID
            limit: Max results

        Returns:
            List of encounters
        """
        data = await self._request(
            "GET", f"/patients/{patient_id}/encounters", params={"limit": limit}
        )
        return [Encounter(**enc) for enc in data.get("encounters", [])]

    async def create_encounter(self, encounter: Encounter) -> Encounter:
        """
        Create new encounter.

        Args:
            encounter: Encounter data

        Returns:
            Created encounter with ID
        """
        data = await self._request(
            "POST",
            f"/patients/{encounter.patient_id}/encounters",
            json=encounter.model_dump(exclude={"id"}),
        )
        return Encounter(**data)

    # ==================== Orders ====================

    async def get_pending_orders(self, patient_id: int) -> list[Order]:
        """
        Get patient's pending orders.

        Args:
            patient_id: Patient ID

        Returns:
            List of pending orders
        """
        data = await self._request(
            "GET",
            f"/patients/{patient_id}/orders",
            params={"status": "pending"},
        )
        return [Order(**o) for o in data.get("orders", [])]

    async def create_order(self, order: Order) -> Order:
        """
        Create new clinical order.

        Args:
            order: Order to create

        Returns:
            Created order with ID
        """
        data = await self._request(
            "POST",
            f"/patients/{order.patient_id}/orders",
            json=order.model_dump(exclude={"id"}),
        )
        return Order(**data)

    # ==================== Comprehensive Summary ====================

    async def get_patient_summary(
        self, patient_id: int
    ) -> Optional[PatientSummary]:
        """
        Get comprehensive patient summary for RAG context.

        Args:
            patient_id: Patient ID

        Returns:
            Complete patient summary or None if patient not found
        """
        # Get patient demographics
        patient = await self.get_patient_by_id(patient_id)
        if not patient:
            return None

        # Fetch all patient data in parallel
        import asyncio

        results = await asyncio.gather(
            self.get_diagnoses(patient_id, active_only=True),
            self.get_current_medications(patient_id),
            self.get_allergies(patient_id),
            self.get_vital_signs(patient_id, limit=1),
            self.get_lab_results(patient_id, limit=20),
            self.get_encounters(patient_id, limit=5),
            self.get_pending_orders(patient_id),
            return_exceptions=True,
        )

        # Unpack results (handle any exceptions)
        diagnoses = results[0] if not isinstance(results[0], Exception) else []
        medications = results[1] if not isinstance(results[1], Exception) else []
        allergies = results[2] if not isinstance(results[2], Exception) else []
        vitals = (
            results[3][0]
            if not isinstance(results[3], Exception) and results[3]
            else None
        )
        labs = results[4] if not isinstance(results[4], Exception) else []
        encounters = results[5] if not isinstance(results[5], Exception) else []
        orders = results[6] if not isinstance(results[6], Exception) else []

        return PatientSummary(
            patient=patient,
            active_diagnoses=diagnoses,
            current_medications=medications,
            allergies=allergies,
            recent_vitals=vitals,
            recent_labs=labs,
            recent_encounters=encounters,
            pending_orders=orders,
        )


# Mock implementation for development/testing
class MockEMRClient(EMRClient):
    """
    Mock EMR client for development and testing.

    Returns sample data without requiring actual EMR connection.
    """

    def __init__(self):
        """Initialize mock client."""
        super().__init__()
        self._mock_data = self._generate_mock_data()

    def _generate_mock_data(self) -> dict:
        """Generate sample patient data."""
        from datetime import datetime, timedelta

        patient = Patient(
            id=12345,
            mrn="MH2024-001234",
            name="Ramesh Kumar",
            age=65,
            gender="M",
            phone="+91-9876543210",
            created_at=datetime.now() - timedelta(days=365),
        )

        return {
            "patient": patient,
            "medications": [
                Medication(
                    patient_id=12345,
                    drug_name="Metformin",
                    dosage="1000mg",
                    frequency="BID",
                    indication="Type 2 Diabetes",
                ),
                Medication(
                    patient_id=12345,
                    drug_name="Lisinopril",
                    dosage="20mg",
                    frequency="QD",
                    indication="Hypertension",
                ),
                Medication(
                    patient_id=12345,
                    drug_name="Atorvastatin",
                    dosage="40mg",
                    frequency="QHS",
                    indication="Hyperlipidemia",
                ),
            ],
            "allergies": [
                Allergy(
                    patient_id=12345,
                    allergen="Penicillin",
                    reaction="Anaphylaxis",
                    severity="fatal",
                ),
                Allergy(
                    patient_id=12345,
                    allergen="Sulfa drugs",
                    reaction="Rash",
                    severity="moderate",
                ),
            ],
            "vitals": VitalSigns(
                patient_id=12345,
                weight_kg=82.0,
                height_cm=170.0,
                bmi=28.4,
                blood_pressure_systolic=142,
                blood_pressure_diastolic=88,
                heart_rate=76,
                spo2=97,
            ),
            "labs": [
                LabResult(
                    patient_id=12345,
                    test_name="Creatinine",
                    result="1.8",
                    unit="mg/dL",
                    reference_range="0.7-1.3",
                    is_abnormal=True,
                    abnormal_flag="H",
                ),
                LabResult(
                    patient_id=12345,
                    test_name="HbA1c",
                    result="7.8",
                    unit="%",
                    reference_range="<7.0",
                    is_abnormal=True,
                    abnormal_flag="H",
                ),
                LabResult(
                    patient_id=12345,
                    test_name="Potassium",
                    result="5.1",
                    unit="mEq/L",
                    reference_range="3.5-5.0",
                    is_abnormal=True,
                    abnormal_flag="H",
                ),
            ],
            "diagnoses": [
                Diagnosis(
                    patient_id=12345,
                    diagnosis_code="E11.9",
                    diagnosis_name="Type 2 Diabetes Mellitus",
                    is_chronic=True,
                ),
                Diagnosis(
                    patient_id=12345,
                    diagnosis_code="I10",
                    diagnosis_name="Essential Hypertension",
                    is_chronic=True,
                ),
                Diagnosis(
                    patient_id=12345,
                    diagnosis_code="N18.3",
                    diagnosis_name="Chronic Kidney Disease, Stage 3",
                    is_chronic=True,
                ),
            ],
        }

    async def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        """Mock: Get patient by ID."""
        return self._mock_data["patient"] if patient_id == 12345 else None

    async def get_current_medications(self, patient_id: int) -> list[Medication]:
        """Mock: Get medications."""
        return self._mock_data["medications"] if patient_id == 12345 else []

    async def get_allergies(self, patient_id: int) -> list[Allergy]:
        """Mock: Get allergies."""
        return self._mock_data["allergies"] if patient_id == 12345 else []

    async def get_vital_signs(
        self, patient_id: int, limit: int = 10
    ) -> list[VitalSigns]:
        """Mock: Get vitals."""
        return [self._mock_data["vitals"]] if patient_id == 12345 else []

    async def get_lab_results(
        self, patient_id: int, limit: int = 50
    ) -> list[LabResult]:
        """Mock: Get labs."""
        return self._mock_data["labs"] if patient_id == 12345 else []

    async def get_diagnoses(
        self, patient_id: int, active_only: bool = True
    ) -> list[Diagnosis]:
        """Mock: Get diagnoses."""
        return self._mock_data["diagnoses"] if patient_id == 12345 else []

    async def get_encounters(
        self, patient_id: int, limit: int = 20
    ) -> list[Encounter]:
        """Mock: Get encounters."""
        return []

    async def get_pending_orders(self, patient_id: int) -> list[Order]:
        """Mock: Get pending orders."""
        return []
