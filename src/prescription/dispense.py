"""
Pharmacy integration and dispensing for Dora.

Features:
- Send prescription to pharmacy
- Track dispensing status
- Refill management
- Pharmacy finder
- Integration with pharmacy APIs
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from enum import Enum

from .models import Prescription, PrescriptionItem, PrescriptionStatus


class DispensingStatus(str, Enum):
    """Status of prescription dispensing."""
    PENDING = "pending"
    SENT_TO_PHARMACY = "sent_to_pharmacy"
    RECEIVED_BY_PHARMACY = "received_by_pharmacy"
    IN_PREPARATION = "in_preparation"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    PARTIALLY_DISPENSED = "partially_dispensed"
    FULLY_DISPENSED = "fully_dispensed"
    PICKUP_MISSED = "pickup_missed"
    CANCELLED = "cancelled"


class DispenseRecord:
    """Record of prescription dispensing."""

    def __init__(
        self,
        dispense_id: str,
        prescription_id: str,
        pharmacy_id: str,
        pharmacy_name: str,
        status: DispensingStatus,
        dispensed_items: List[Dict[str, Any]],
        dispensed_at: Optional[datetime] = None,
        dispensed_by: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        """Initialize dispense record."""
        self.dispense_id = dispense_id
        self.prescription_id = prescription_id
        self.pharmacy_id = pharmacy_id
        self.pharmacy_name = pharmacy_name
        self.status = status
        self.dispensed_items = dispensed_items  # List of {item_sequence, quantity_dispensed, batch_no, expiry}
        self.dispensed_at = dispensed_at
        self.dispensed_by = dispensed_by
        self.notes = notes
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'dispense_id': self.dispense_id,
            'prescription_id': self.prescription_id,
            'pharmacy_id': self.pharmacy_id,
            'pharmacy_name': self.pharmacy_name,
            'status': self.status.value,
            'dispensed_items': self.dispensed_items,
            'dispensed_at': self.dispensed_at.isoformat() if self.dispensed_at else None,
            'dispensed_by': self.dispensed_by,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class Pharmacy:
    """Pharmacy information."""

    def __init__(
        self,
        pharmacy_id: str,
        name: str,
        address: str,
        phone: str,
        email: Optional[str] = None,
        license_number: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        operating_hours: Optional[str] = None,
        home_delivery: bool = False,
        online_payment: bool = False,
        insurance_accepted: bool = False,
    ):
        """Initialize pharmacy."""
        self.pharmacy_id = pharmacy_id
        self.name = name
        self.address = address
        self.phone = phone
        self.email = email
        self.license_number = license_number
        self.latitude = latitude
        self.longitude = longitude
        self.operating_hours = operating_hours
        self.home_delivery = home_delivery
        self.online_payment = online_payment
        self.insurance_accepted = insurance_accepted

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'pharmacy_id': self.pharmacy_id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'license_number': self.license_number,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'operating_hours': self.operating_hours,
            'home_delivery': self.home_delivery,
            'online_payment': self.online_payment,
            'insurance_accepted': self.insurance_accepted,
        }


class PharmacyService:
    """Service for pharmacy operations."""

    def __init__(self, pharmacy_api=None, pharmacy_database=None):
        """
        Initialize pharmacy service.

        Args:
            pharmacy_api: API client for pharmacy integration
            pharmacy_database: Database of pharmacies
        """
        self.pharmacy_api = pharmacy_api
        self.pharmacy_db = pharmacy_database or self._get_demo_pharmacies()
        self.dispense_records = {}  # In-memory storage for demo

    def send_to_pharmacy(
        self,
        prescription: Prescription,
        pharmacy_id: str,
        delivery_method: str = "pickup",  # pickup or delivery
        delivery_address: Optional[str] = None,
    ) -> DispenseRecord:
        """
        Send prescription to pharmacy.

        Args:
            prescription: Prescription to send
            pharmacy_id: Target pharmacy ID
            delivery_method: pickup or delivery
            delivery_address: Address for delivery

        Returns:
            Dispense record

        Raises:
            ValueError: If pharmacy not found
        """
        # Get pharmacy
        pharmacy = self.get_pharmacy(pharmacy_id)
        if not pharmacy:
            raise ValueError(f"Pharmacy {pharmacy_id} not found")

        # Check home delivery availability
        if delivery_method == "delivery" and not pharmacy.home_delivery:
            raise ValueError(f"Pharmacy {pharmacy.name} does not offer home delivery")

        # Create dispense record
        from uuid import uuid4
        dispense_id = f"DISP-{uuid4().hex[:12].upper()}"

        dispense_record = DispenseRecord(
            dispense_id=dispense_id,
            prescription_id=prescription.prescription_id,
            pharmacy_id=pharmacy_id,
            pharmacy_name=pharmacy.name,
            status=DispensingStatus.SENT_TO_PHARMACY,
            dispensed_items=[],
        )

        # Send to pharmacy API (if available)
        if self.pharmacy_api:
            try:
                response = self.pharmacy_api.send_prescription(
                    prescription_id=prescription.prescription_id,
                    pharmacy_id=pharmacy_id,
                    items=prescription.items,
                    delivery_method=delivery_method,
                    delivery_address=delivery_address,
                )

                if response.get('status') == 'received':
                    dispense_record.status = DispensingStatus.RECEIVED_BY_PHARMACY

            except Exception as e:
                dispense_record.notes = f"API error: {str(e)}"

        # Update prescription
        prescription.sent_to_pharmacy = True
        prescription.pharmacy_id = pharmacy_id

        # Store record
        self.dispense_records[dispense_id] = dispense_record

        return dispense_record

    def update_dispense_status(
        self,
        dispense_id: str,
        status: DispensingStatus,
        dispensed_items: Optional[List[Dict[str, Any]]] = None,
        notes: Optional[str] = None,
    ) -> Optional[DispenseRecord]:
        """
        Update dispensing status.

        Args:
            dispense_id: Dispense record ID
            status: New status
            dispensed_items: Items dispensed (for partial/full dispensing)
            notes: Additional notes

        Returns:
            Updated dispense record
        """
        record = self.dispense_records.get(dispense_id)
        if not record:
            return None

        record.status = status
        record.updated_at = datetime.utcnow()

        if dispensed_items:
            record.dispensed_items = dispensed_items

        if status in [DispensingStatus.FULLY_DISPENSED, DispensingStatus.PARTIALLY_DISPENSED]:
            record.dispensed_at = datetime.utcnow()

        if notes:
            record.notes = notes

        return record

    def get_dispense_status(self, prescription_id: str) -> Optional[DispenseRecord]:
        """Get dispensing status for prescription."""
        for record in self.dispense_records.values():
            if record.prescription_id == prescription_id:
                return record
        return None

    def find_nearby_pharmacies(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Pharmacy]:
        """
        Find pharmacies near a location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers
            filters: Optional filters (home_delivery, insurance_accepted, etc.)

        Returns:
            List of nearby pharmacies
        """
        # Simple distance calculation (Haversine would be more accurate)
        import math

        def distance(lat1, lon1, lat2, lon2):
            """Calculate distance between two points (approximate)."""
            # Simple Euclidean distance for demo
            # In production, use Haversine formula
            dx = (lon2 - lon1) * 111  # 1 degree longitude ≈ 111 km
            dy = (lat2 - lat1) * 111  # 1 degree latitude ≈ 111 km
            return math.sqrt(dx**2 + dy**2)

        nearby = []

        for pharmacy in self.pharmacy_db.values():
            if pharmacy.latitude and pharmacy.longitude:
                dist = distance(latitude, longitude, pharmacy.latitude, pharmacy.longitude)

                if dist <= radius_km:
                    # Apply filters
                    if filters:
                        if filters.get('home_delivery') and not pharmacy.home_delivery:
                            continue
                        if filters.get('insurance_accepted') and not pharmacy.insurance_accepted:
                            continue

                    nearby.append(pharmacy)

        # Sort by distance (simplified - just return all for demo)
        return nearby

    def get_pharmacy(self, pharmacy_id: str) -> Optional[Pharmacy]:
        """Get pharmacy by ID."""
        return self.pharmacy_db.get(pharmacy_id)

    def _get_demo_pharmacies(self) -> Dict[str, Pharmacy]:
        """Get demo pharmacy database."""
        return {
            'PHARM-001': Pharmacy(
                pharmacy_id='PHARM-001',
                name='Apollo Pharmacy',
                address='MG Road, Bangalore',
                phone='+91-80-12345678',
                email='mgroad@apollopharmacy.in',
                latitude=12.9716,
                longitude=77.5946,
                operating_hours='24x7',
                home_delivery=True,
                online_payment=True,
                insurance_accepted=True,
            ),
            'PHARM-002': Pharmacy(
                pharmacy_id='PHARM-002',
                name='MedPlus',
                address='Indiranagar, Bangalore',
                phone='+91-80-23456789',
                latitude=12.9719,
                longitude=77.6412,
                operating_hours='8 AM - 10 PM',
                home_delivery=True,
                online_payment=True,
                insurance_accepted=False,
            ),
            'PHARM-003': Pharmacy(
                pharmacy_id='PHARM-003',
                name='Local Pharmacy',
                address='Koramangala, Bangalore',
                phone='+91-80-34567890',
                latitude=12.9352,
                longitude=77.6245,
                operating_hours='9 AM - 9 PM',
                home_delivery=False,
                online_payment=False,
                insurance_accepted=False,
            ),
        }


class RefillManager:
    """Manage prescription refills."""

    def __init__(self, storage=None):
        """Initialize refill manager."""
        self.storage = storage or {}  # In-memory storage for demo

    def check_refill_eligibility(
        self,
        prescription: Prescription,
        item_sequence: int,
    ) -> Dict[str, Any]:
        """
        Check if prescription item is eligible for refill.

        Args:
            prescription: Original prescription
            item_sequence: Item sequence number

        Returns:
            Eligibility information
        """
        # Find item
        item = next(
            (i for i in prescription.items if i.item_sequence == item_sequence),
            None
        )

        if not item:
            return {'eligible': False, 'reason': 'Item not found'}

        # Check refill allowance
        if not item.refill.allowed:
            return {'eligible': False, 'reason': 'Refills not authorized'}

        # Check refills remaining
        refills_remaining = item.refill.number_of_refills - item.refill.refills_used

        if refills_remaining <= 0:
            return {'eligible': False, 'reason': 'No refills remaining'}

        # Check validity
        if item.refill.valid_until and item.refill.valid_until < date.today():
            return {'eligible': False, 'reason': 'Refill authorization expired'}

        # Check prescription validity
        if prescription.valid_until and prescription.valid_until < date.today():
            return {'eligible': False, 'reason': 'Prescription expired'}

        return {
            'eligible': True,
            'refills_remaining': refills_remaining,
            'valid_until': item.refill.valid_until,
        }

    def process_refill(
        self,
        prescription: Prescription,
        item_sequence: int,
        pharmacy_id: str,
    ) -> Optional[DispenseRecord]:
        """
        Process a refill request.

        Args:
            prescription: Original prescription
            item_sequence: Item to refill
            pharmacy_id: Pharmacy processing refill

        Returns:
            Dispense record for refill
        """
        # Check eligibility
        eligibility = self.check_refill_eligibility(prescription, item_sequence)

        if not eligibility['eligible']:
            raise ValueError(f"Not eligible for refill: {eligibility['reason']}")

        # Find item
        item = next(
            (i for i in prescription.items if i.item_sequence == item_sequence),
            None
        )

        if not item:
            raise ValueError("Item not found")

        # Create refill dispense record
        from uuid import uuid4
        dispense_id = f"REFILL-{uuid4().hex[:12].upper()}"

        dispense_record = DispenseRecord(
            dispense_id=dispense_id,
            prescription_id=prescription.prescription_id,
            pharmacy_id=pharmacy_id,
            pharmacy_name="Pharmacy",  # Would lookup actual pharmacy
            status=DispensingStatus.PENDING,
            dispensed_items=[{
                'item_sequence': item_sequence,
                'quantity_dispensed': item.quantity,
                'is_refill': True,
                'refill_number': item.refill.refills_used + 1,
            }],
            notes=f"Refill #{item.refill.refills_used + 1}",
        )

        # Update refill count
        item.refill.refills_used += 1

        return dispense_record

    def auto_refill_reminder(
        self,
        prescription: Prescription,
        days_before: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Check which items need refill reminders.

        Args:
            prescription: Prescription to check
            days_before: Days before running out to remind

        Returns:
            List of items needing refill reminders
        """
        reminders = []

        for item in prescription.items:
            if not item.refill.allowed:
                continue

            # Calculate when patient will run out
            # Assume they started taking on date_prescribed
            days_supply = item.dosage.duration_days
            run_out_date = prescription.date_prescribed.date() + timedelta(days=days_supply)

            # Check if approaching
            days_until_runout = (run_out_date - date.today()).days

            if 0 <= days_until_runout <= days_before:
                eligibility = self.check_refill_eligibility(prescription, item.item_sequence)

                reminders.append({
                    'item': item.drug_name,
                    'item_sequence': item.item_sequence,
                    'days_until_runout': days_until_runout,
                    'eligible': eligibility['eligible'],
                    'reason': eligibility.get('reason'),
                })

        return reminders


# Example usage
if __name__ == "__main__":
    from .models import (
        Prescription, PrescriptionItem, PatientInfo, DoctorInfo,
        Dosage, DosageForm, Frequency, RouteOfAdministration, Refill
    )

    # Create prescription with refills
    patient = PatientInfo(
        patient_id="PAT-001",
        name="Test Patient",
        age=45,
        gender="M",
    )

    doctor = DoctorInfo(
        doctor_id="DOC-001",
        name="Dr. Test",
        qualifications="MD",
        registration_number="REG-001",
    )

    item = PrescriptionItem(
        drug_name="Metformin",
        strength="500mg",
        dosage_form=DosageForm.TABLET,
        dosage=Dosage(
            dose="1 tablet",
            frequency=Frequency.BD,
            duration_days=30,
            route=RouteOfAdministration.ORAL,
        ),
        quantity=60,
        quantity_unit="tablets",
        item_sequence=1,
        refill=Refill(
            allowed=True,
            number_of_refills=3,
            valid_until=date.today() + timedelta(days=90),
        ),
    )

    prescription = Prescription(
        prescription_id="RX-001",
        patient=patient,
        doctor=doctor,
        items=[item],
        created_by="doctor",
    )

    # Test pharmacy service
    pharmacy_service = PharmacyService()

    # Find nearby pharmacies
    pharmacies = pharmacy_service.find_nearby_pharmacies(
        latitude=12.9716,
        longitude=77.5946,
        radius_km=10,
    )

    print(f"Found {len(pharmacies)} nearby pharmacies:")
    for pharmacy in pharmacies:
        print(f"  - {pharmacy.name}: {pharmacy.address}")

    # Send to pharmacy
    if pharmacies:
        dispense_record = pharmacy_service.send_to_pharmacy(
            prescription,
            pharmacies[0].pharmacy_id,
            delivery_method="pickup",
        )

        print(f"\nSent to pharmacy: {dispense_record.pharmacy_name}")
        print(f"Status: {dispense_record.status.value}")

    # Check refill eligibility
    refill_manager = RefillManager()
    eligibility = refill_manager.check_refill_eligibility(prescription, 1)

    print(f"\nRefill eligible: {eligibility['eligible']}")
    if eligibility['eligible']:
        print(f"Refills remaining: {eligibility['refills_remaining']}")
