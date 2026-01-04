"""FHIR R4 Interoperability for hospital integrations."""

from datetime import datetime
from typing import Any, Optional

from .models import (
    Allergy,
    Diagnosis,
    Encounter,
    Gender,
    LabResult,
    Medication,
    Order,
    OrderType,
    Patient,
    Severity,
    VitalSigns,
)


class FHIRConverter:
    """
    Convert between Dora EMR models and FHIR R4 resources.

    FHIR (Fast Healthcare Interoperability Resources) is the
    standard for healthcare data exchange.

    Supports:
    - Patient resource
    - MedicationRequest resource
    - AllergyIntolerance resource
    - Observation resource (vitals, labs)
    - Condition resource (diagnoses)
    - Encounter resource
    """

    @staticmethod
    def patient_to_fhir(patient: Patient) -> dict[str, Any]:
        """
        Convert Patient to FHIR Patient resource.

        Args:
            patient: Dora patient model

        Returns:
            FHIR Patient resource as dict
        """
        gender_map = {
            Gender.MALE: "male",
            Gender.FEMALE: "female",
            Gender.OTHER: "other",
        }

        resource = {
            "resourceType": "Patient",
            "id": str(patient.id),
            "identifier": [
                {
                    "system": "http://docassist.in/mrn",
                    "value": patient.mrn,
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": patient.name,
                }
            ],
            "gender": gender_map.get(patient.gender, "unknown"),
            "birthDate": (
                patient.date_of_birth.strftime("%Y-%m-%d")
                if patient.date_of_birth
                else None
            ),
        }

        # Add contact info if available
        if patient.phone or patient.email:
            resource["telecom"] = []
            if patient.phone:
                resource["telecom"].append(
                    {"system": "phone", "value": patient.phone}
                )
            if patient.email:
                resource["telecom"].append(
                    {"system": "email", "value": patient.email}
                )

        # Add address if available
        if patient.address:
            resource["address"] = [{"text": patient.address}]

        # Add emergency contact if available
        if patient.emergency_contact and patient.emergency_phone:
            resource["contact"] = [
                {
                    "relationship": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                                    "code": "C",
                                    "display": "Emergency Contact",
                                }
                            ]
                        }
                    ],
                    "name": {"text": patient.emergency_contact},
                    "telecom": [{"system": "phone", "value": patient.emergency_phone}],
                }
            ]

        return resource

    @staticmethod
    def fhir_to_patient(fhir_resource: dict[str, Any]) -> Patient:
        """
        Convert FHIR Patient resource to Dora Patient.

        Args:
            fhir_resource: FHIR Patient resource

        Returns:
            Dora Patient model
        """
        gender_map = {
            "male": Gender.MALE,
            "female": Gender.FEMALE,
            "other": Gender.OTHER,
        }

        # Extract MRN from identifiers
        mrn = None
        for identifier in fhir_resource.get("identifier", []):
            if "mrn" in identifier.get("system", "").lower():
                mrn = identifier["value"]
                break

        # Extract name
        name = ""
        if fhir_resource.get("name"):
            name = fhir_resource["name"][0].get("text", "")

        # Calculate age from birthDate
        age = 0
        birth_date = None
        if fhir_resource.get("birthDate"):
            birth_date = datetime.strptime(fhir_resource["birthDate"], "%Y-%m-%d")
            age = (datetime.now() - birth_date).days // 365

        # Extract phone
        phone = None
        for telecom in fhir_resource.get("telecom", []):
            if telecom.get("system") == "phone":
                phone = telecom.get("value")
                break

        return Patient(
            id=int(fhir_resource["id"]) if fhir_resource.get("id") else 0,
            mrn=mrn or "",
            name=name,
            age=age,
            gender=gender_map.get(fhir_resource.get("gender", "unknown"), Gender.OTHER),
            date_of_birth=birth_date,
            phone=phone,
        )

    @staticmethod
    def medication_to_fhir(medication: Medication) -> dict[str, Any]:
        """
        Convert Medication to FHIR MedicationRequest resource.

        Args:
            medication: Dora medication model

        Returns:
            FHIR MedicationRequest resource
        """
        status_map = {True: "active", False: "stopped"}

        resource = {
            "resourceType": "MedicationRequest",
            "id": str(medication.id) if medication.id else None,
            "status": status_map[medication.is_active],
            "intent": "order",
            "medicationCodeableConcept": {
                "text": medication.drug_name,
            },
            "subject": {
                "reference": f"Patient/{medication.patient_id}",
            },
            "dosageInstruction": [
                {
                    "text": f"{medication.dosage} {medication.route} {medication.frequency}",
                    "route": {
                        "text": medication.route,
                    },
                    "doseAndRate": [
                        {
                            "doseQuantity": {
                                "value": medication.dosage,
                            }
                        }
                    ],
                }
            ],
        }

        if medication.instructions:
            resource["dosageInstruction"][0]["patientInstruction"] = (
                medication.instructions
            )

        if medication.indication:
            resource["reasonCode"] = [{"text": medication.indication}]

        return resource

    @staticmethod
    def allergy_to_fhir(allergy: Allergy) -> dict[str, Any]:
        """
        Convert Allergy to FHIR AllergyIntolerance resource.

        Args:
            allergy: Dora allergy model

        Returns:
            FHIR AllergyIntolerance resource
        """
        severity_map = {
            Severity.MILD: "mild",
            Severity.MODERATE: "moderate",
            Severity.SEVERE: "severe",
            Severity.FATAL: "severe",  # FHIR doesn't have "fatal"
        }

        criticality_map = {
            Severity.MILD: "low",
            Severity.MODERATE: "low",
            Severity.SEVERE: "high",
            Severity.FATAL: "high",
        }

        resource = {
            "resourceType": "AllergyIntolerance",
            "id": str(allergy.id) if allergy.id else None,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": "active",
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                        "code": "confirmed" if allergy.verified else "unconfirmed",
                    }
                ]
            },
            "type": "allergy",
            "category": [allergy.allergen_type],
            "criticality": criticality_map[allergy.severity],
            "code": {
                "text": allergy.allergen,
            },
            "patient": {
                "reference": f"Patient/{allergy.patient_id}",
            },
            "reaction": [
                {
                    "manifestation": [{"text": allergy.reaction}],
                    "severity": severity_map[allergy.severity],
                }
            ],
        }

        if allergy.onset_date:
            resource["onsetDateTime"] = allergy.onset_date.isoformat()

        return resource

    @staticmethod
    def vital_signs_to_fhir(vitals: VitalSigns) -> list[dict[str, Any]]:
        """
        Convert VitalSigns to FHIR Observation resources.

        Each vital sign becomes a separate Observation.

        Args:
            vitals: Dora vital signs model

        Returns:
            List of FHIR Observation resources
        """
        observations = []

        # Weight
        if vitals.weight_kg:
            observations.append(
                {
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "29463-7",
                                "display": "Body weight",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{vitals.patient_id}"},
                    "effectiveDateTime": vitals.measured_at.isoformat(),
                    "valueQuantity": {
                        "value": vitals.weight_kg,
                        "unit": "kg",
                        "system": "http://unitsofmeasure.org",
                        "code": "kg",
                    },
                }
            )

        # Blood Pressure
        if vitals.blood_pressure_systolic and vitals.blood_pressure_diastolic:
            observations.append(
                {
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "85354-9",
                                "display": "Blood pressure",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{vitals.patient_id}"},
                    "effectiveDateTime": vitals.measured_at.isoformat(),
                    "component": [
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "8480-6",
                                        "display": "Systolic blood pressure",
                                    }
                                ]
                            },
                            "valueQuantity": {
                                "value": vitals.blood_pressure_systolic,
                                "unit": "mmHg",
                                "system": "http://unitsofmeasure.org",
                                "code": "mm[Hg]",
                            },
                        },
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "8462-4",
                                        "display": "Diastolic blood pressure",
                                    }
                                ]
                            },
                            "valueQuantity": {
                                "value": vitals.blood_pressure_diastolic,
                                "unit": "mmHg",
                                "system": "http://unitsofmeasure.org",
                                "code": "mm[Hg]",
                            },
                        },
                    ],
                }
            )

        # Heart Rate
        if vitals.heart_rate:
            observations.append(
                {
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8867-4",
                                "display": "Heart rate",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{vitals.patient_id}"},
                    "effectiveDateTime": vitals.measured_at.isoformat(),
                    "valueQuantity": {
                        "value": vitals.heart_rate,
                        "unit": "beats/minute",
                        "system": "http://unitsofmeasure.org",
                        "code": "/min",
                    },
                }
            )

        return observations

    @staticmethod
    def lab_result_to_fhir(lab: LabResult) -> dict[str, Any]:
        """
        Convert LabResult to FHIR Observation resource.

        Args:
            lab: Dora lab result model

        Returns:
            FHIR Observation resource
        """
        resource = {
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                        }
                    ]
                }
            ],
            "code": {
                "text": lab.test_name,
            },
            "subject": {
                "reference": f"Patient/{lab.patient_id}",
            },
            "effectiveDateTime": lab.test_date.isoformat(),
            "valueQuantity": {
                "value": lab.result,
            },
        }

        if lab.test_code:
            resource["code"]["coding"] = [
                {
                    "system": "http://loinc.org",
                    "code": lab.test_code,
                }
            ]

        if lab.unit:
            resource["valueQuantity"]["unit"] = lab.unit

        if lab.reference_range:
            resource["referenceRange"] = [
                {
                    "text": lab.reference_range,
                }
            ]

        if lab.is_abnormal:
            resource["interpretation"] = [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": lab.abnormal_flag or "A",
                        }
                    ]
                }
            ]

        return resource

    @staticmethod
    def diagnosis_to_fhir(diagnosis: Diagnosis) -> dict[str, Any]:
        """
        Convert Diagnosis to FHIR Condition resource.

        Args:
            diagnosis: Dora diagnosis model

        Returns:
            FHIR Condition resource
        """
        resource = {
            "resourceType": "Condition",
            "id": str(diagnosis.id) if diagnosis.id else None,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active" if diagnosis.is_active else "resolved",
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": diagnosis.diagnosis_type,
                        }
                    ]
                }
            ],
            "code": {
                "text": diagnosis.diagnosis_name,
            },
            "subject": {
                "reference": f"Patient/{diagnosis.patient_id}",
            },
        }

        if diagnosis.diagnosis_code:
            resource["code"]["coding"] = [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": diagnosis.diagnosis_code,
                }
            ]

        if diagnosis.onset_date:
            resource["onsetDateTime"] = diagnosis.onset_date.isoformat()

        if diagnosis.is_chronic:
            resource["category"][0]["coding"].append(
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "problem-list-item",
                    "display": "Problem List Item",
                }
            )

        return resource

    @staticmethod
    def encounter_to_fhir(encounter: Encounter) -> dict[str, Any]:
        """
        Convert Encounter to FHIR Encounter resource.

        Args:
            encounter: Dora encounter model

        Returns:
            FHIR Encounter resource
        """
        type_map = {
            "outpatient": "AMB",
            "inpatient": "IMP",
            "emergency": "EMER",
            "telehealth": "VR",
        }

        resource = {
            "resourceType": "Encounter",
            "id": str(encounter.id) if encounter.id else None,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": type_map.get(encounter.encounter_type, "AMB"),
            },
            "subject": {
                "reference": f"Patient/{encounter.patient_id}",
            },
            "period": {
                "start": encounter.encounter_date.isoformat(),
            },
        }

        if encounter.chief_complaint:
            resource["reasonCode"] = [{"text": encounter.chief_complaint}]

        if encounter.provider_name:
            resource["participant"] = [
                {
                    "individual": {
                        "display": encounter.provider_name,
                    }
                }
            ]

        return resource


# Helper functions for bulk operations
def patient_bundle_to_fhir(
    patient: Patient,
    medications: list[Medication],
    allergies: list[Allergy],
    labs: list[LabResult],
    diagnoses: list[Diagnosis],
) -> dict[str, Any]:
    """
    Create FHIR Bundle with all patient data.

    Args:
        patient: Patient
        medications: Medications list
        allergies: Allergies list
        labs: Lab results list
        diagnoses: Diagnoses list

    Returns:
        FHIR Bundle resource
    """
    converter = FHIRConverter()
    entries = []

    # Add patient
    entries.append(
        {
            "resource": converter.patient_to_fhir(patient),
        }
    )

    # Add medications
    for med in medications:
        entries.append(
            {
                "resource": converter.medication_to_fhir(med),
            }
        )

    # Add allergies
    for allergy in allergies:
        entries.append(
            {
                "resource": converter.allergy_to_fhir(allergy),
            }
        )

    # Add labs
    for lab in labs:
        entries.append(
            {
                "resource": converter.lab_result_to_fhir(lab),
            }
        )

    # Add diagnoses
    for dx in diagnoses:
        entries.append(
            {
                "resource": converter.diagnosis_to_fhir(dx),
            }
        )

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries,
    }

    return bundle
