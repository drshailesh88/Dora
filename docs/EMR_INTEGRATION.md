# EMR Integration Guide

Complete guide to Dora's EMR integration for seamless patient-contextualized medical knowledge.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Security & Compliance](#security--compliance)
- [Troubleshooting](#troubleshooting)

---

## Overview

Dora's EMR integration provides **bidirectional synchronization** with DocAssist EMR, enabling:

- ✅ **Patient-contextualized queries** - Automatic injection of patient data into medical queries
- ✅ **Clinical decision support** - Drug-allergy alerts, drug-drug interactions, contraindications
- ✅ **Recommendation feedback** - Track outcomes and learn from clinical decisions
- ✅ **Offline-first architecture** - Works without internet, syncs when online
- ✅ **FHIR R4 compatibility** - Integrate with any hospital system
- ✅ **HIPAA-compliant** - Audit trails and encrypted data

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Dora Query                            │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              EMR Service (service.py)                │   │
│  │  • Orchestrates all EMR operations                  │   │
│  │  • Manages patient cache                            │   │
│  │  • Handles online/offline modes                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────┬────────────────┬──────────────────────┐   │
│  │   Client     │   Context      │   Alerts             │   │
│  │  (client.py) │ (context.py)   │  (alerts.py)         │   │
│  │              │                │                      │   │
│  │ • EMR API    │ • Build query  │ • Drug-allergy       │   │
│  │   calls      │   context      │ • Drug-drug          │   │
│  │ • Rate limit │ • Filter labs  │ • Contraindications  │   │
│  │ • Retry      │ • eGFR calc    │ • Renal dosing       │   │
│  └──────────────┴────────────────┴──────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────┬────────────────┬──────────────────────┐   │
│  │    Sync      │   Feedback     │   FHIR               │   │
│  │  (sync.py)   │ (feedback.py)  │  (fhir.py)           │   │
│  │              │                │                      │   │
│  │ • Pull data  │ • Track        │ • FHIR R4            │   │
│  │ • Push recs  │   outcomes     │   conversion         │   │
│  │ • Offline    │ • A/B testing  │ • Hospital           │   │
│  │   queue      │ • Analytics    │   integration        │   │
│  └──────────────┴────────────────┴──────────────────────┘   │
│                            ↓                                 │
│               DocAssist EMR / Hospital System                │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Models (`models.py`)

Comprehensive data models for all EMR entities:

```python
from src.emr import (
    Patient,
    Medication,
    Allergy,
    VitalSigns,
    LabResult,
    Diagnosis,
    Encounter,
    ClinicalNote,
    Order,
    PatientSummary,
)
```

**Key Models:**

- **Patient** - Demographics, MRN, contact info
- **Medication** - Drug name, dosage, frequency, instructions
- **Allergy** - Allergen, reaction type, severity
- **VitalSigns** - BP, HR, weight, BMI, SpO2
- **LabResult** - Test name, value, reference range, abnormal flag
- **Diagnosis** - ICD-10 code, diagnosis name, chronic flag
- **PatientSummary** - Comprehensive patient context for RAG

### 2. EMR Client (`client.py`)

HTTP client for DocAssist EMR API:

```python
from src.emr import EMRClient, EMRConfig, MockEMRClient

# Production
config = EMRConfig(
    base_url="https://emr.docassist.in/api",
    api_key="your-api-key",
    timeout=30,
)
async with EMRClient(config) as client:
    patient = await client.get_patient("MH2024-001234")
    medications = await client.get_current_medications(patient.id)

# Development/Testing
client = MockEMRClient()  # Uses sample data
```

### 3. Context Builder (`context.py`)

Builds patient context optimized for queries:

```python
from src.emr import PatientContextBuilder

builder = PatientContextBuilder(emr_client)

# Build query-relevant context (filtered)
context = await builder.build_context(
    patient_id=12345,
    query="What antibiotic for UTI?",
    include_full_history=False,  # Only relevant data
)

# Build prescription-specific context
context = await builder.build_context_for_prescription(
    patient_id=12345,
    drug_name="Amoxicillin",
)
```

**Features:**
- Filters medications relevant to query
- Always includes allergies (safety critical)
- Calculates derived values (eGFR, BMI)
- Generates clinical alerts
- Formats for optimal LLM comprehension

### 4. Clinical Alerts (`alerts.py`)

Clinical decision support engine:

```python
from src.emr import ClinicalAlertEngine

engine = ClinicalAlertEngine()

alerts = engine.check_all_alerts(
    patient_summary=summary,
    proposed_medication="Ibuprofen",
)

for alert in alerts:
    print(alert.to_display_string())
```

**Alert Types:**
- ⚠️ **Drug-allergy** - Cross-allergen checking (penicillin → cephalosporin)
- ⚠️ **Drug-drug interactions** - NSAIDs + anticoagulants, ACE + ARB
- ⚠️ **Contraindications** - NSAIDs in CKD, beta blockers in asthma
- ⚠️ **Renal dosing** - Metformin in eGFR <30, dose adjustments
- ⚠️ **Critical labs** - Hyperkalemia, severe anemia
- ⚠️ **Duplicate therapy** - Multiple statins, multiple NSAIDs
- ⚠️ **Beers criteria** - Elderly-specific medication risks

### 5. Feedback System (`feedback.py`)

Track recommendation outcomes and learn:

```python
from src.emr import (
    RecommendationFeedback,
    FeedbackType,
    OutcomeType,
    feedback_store,
)

# Record feedback
feedback = RecommendationFeedback(
    patient_id=12345,
    query="Best antibiotic for UTI in CKD?",
    recommendation="Nitrofurantoin 100mg BID x 5 days",
    feedback_type=FeedbackType.FOLLOWED,
    outcome=OutcomeType.IMPROVED,
)
saved = feedback_store.add_feedback(feedback)

# Get analytics
analytics = feedback_store.get_analytics()
print(f"Follow rate: {analytics.follow_rate}%")
print(f"Success rate: {analytics.success_rate}%")

# Find similar cases
similar = feedback_store.get_similar_cases(
    query="UTI in CKD patient",
    limit=5,
)
```

### 6. Sync Manager (`sync.py`)

Bidirectional EMR synchronization:

```python
from src.emr import EMRSyncManager

sync = EMRSyncManager(emr_client)

# Pull patient data
summary = await sync.pull_patient_context(patient_id=12345)

# Push recommendation
await sync.push_recommendation(
    patient_id=12345,
    recommendation={"answer": "...", "citations": [...]},
)

# Push clinical note
from src.emr import ClinicalNote
note = ClinicalNote(
    patient_id=12345,
    note_type="progress",
    full_note="Patient responded well to treatment...",
)
await sync.push_clinical_note(patient_id, note)

# Offline mode - queue for later
# (automatically happens when offline)
await sync.sync_pending_queue()  # Sync when back online
```

### 7. FHIR Converter (`fhir.py`)

FHIR R4 interoperability:

```python
from src.emr import FHIRConverter, patient_bundle_to_fhir

converter = FHIRConverter()

# Convert to FHIR
fhir_patient = converter.patient_to_fhir(patient)
fhir_med = converter.medication_to_fhir(medication)
fhir_allergy = converter.allergy_to_fhir(allergy)

# Convert from FHIR
patient = converter.fhir_to_patient(fhir_resource)

# Create full bundle
bundle = patient_bundle_to_fhir(
    patient=patient,
    medications=medications,
    allergies=allergies,
    labs=labs,
    diagnoses=diagnoses,
)
```

### 8. EMR Service (`service.py`)

High-level orchestration layer:

```python
from src.emr import get_emr_service

# Get singleton instance
emr_service = get_emr_service(use_mock=True)

# Get patient context for query
context = await emr_service.get_patient_context_for_query(
    patient_id=12345,
    query="What antibiotic for UTI?",
)

# Check clinical alerts
alerts = await emr_service.check_clinical_alerts(
    patient_id=12345,
    proposed_medication="Amoxicillin",
)

# Enrich query with patient data
enriched_query, alerts = await emr_service.enrich_query_with_patient_data(
    patient_id=12345,
    query="How to adjust metformin?",
)

# Create order with safety checks
from src.emr import Order, OrderType
order = Order(
    patient_id=12345,
    order_type=OrderType.MEDICATION,
    order_name="Amoxicillin",
    order_details={"dosage": "500mg", "frequency": "TID"},
)
created = await emr_service.create_order(patient_id, order)

# Get sync status
status = emr_service.get_sync_status()
```

---

## Quick Start

### 1. Installation

```bash
# EMR integration is part of Dora core
pip install -r requirements.txt
```

### 2. Configuration

```env
# .env file
EMR_API_URL=https://emr.docassist.in/api
EMR_API_KEY=your-api-key-here
EMR_OFFLINE_MODE=false
```

### 3. Basic Usage

```python
import asyncio
from src.emr import get_emr_service

async def main():
    # Initialize (use mock for testing)
    emr = get_emr_service(use_mock=True)

    # Get patient context
    context = await emr.get_patient_context_for_query(
        patient_id=12345,
        query="What medication for hypertension?",
    )

    print(context)

asyncio.run(main())
```

---

## API Reference

### REST API Endpoints

All endpoints are available at `/api/emr/*`:

#### Patient Information

```bash
# Get patient by MRN
GET /api/emr/patient/mrn/{mrn}

# Get patient by ID
GET /api/emr/patient/{patient_id}

# Search patients
GET /api/emr/search/patients?query=Ramesh&limit=10
```

#### Patient Context

```bash
# Get context for query
GET /api/emr/patient/{patient_id}/context?query=UTI+treatment

# Get medications
GET /api/emr/patient/{patient_id}/medications

# Get allergies
GET /api/emr/patient/{patient_id}/allergies

# Get labs
GET /api/emr/patient/{patient_id}/labs?limit=20
```

#### Clinical Decision Support

```bash
# Get clinical alerts
GET /api/emr/patient/{patient_id}/alerts?proposed_medication=Ibuprofen

# Get prescription context
GET /api/emr/prescription-context/{patient_id}?drug_name=Amoxicillin
```

#### Create Orders

```bash
# Create clinical note
POST /api/emr/patient/{patient_id}/note
{
  "note_text": "Patient tolerated medication well..."
}

# Create order
POST /api/emr/patient/{patient_id}/order
{
  "patient_id": 12345,
  "order": {
    "order_type": "medication",
    "order_name": "Amoxicillin",
    "order_details": {"dosage": "500mg", "frequency": "TID"}
  }
}
```

#### Feedback

```bash
# Submit feedback
POST /api/emr/feedback
{
  "patient_id": 12345,
  "query": "UTI treatment",
  "recommendation": "Nitrofurantoin 100mg BID x 5 days",
  "feedback_type": "followed",
  "outcome": "improved"
}
```

#### Sync Management

```bash
# Get sync status
GET /api/emr/sync/status

# Refresh patient context
POST /api/emr/sync/refresh/{patient_id}

# Sync offline queue
POST /api/emr/sync/offline-queue
```

---

## Examples

See [`examples/emr_integration_example.py`](../examples/emr_integration_example.py) for complete examples:

1. **Patient-specific query with context**
2. **Prescription safety checks**
3. **Create clinical order**
4. **Feedback loop**
5. **Enriched query for RAG**
6. **Sync status & offline queue**

Run examples:

```bash
python examples/emr_integration_example.py
```

---

## Security & Compliance

### HIPAA Compliance

✅ **Audit Logging** - All EMR access logged
```python
# Automatically logged by EMRSyncManager
sync.create_audit_trail(
    patient_id=12345,
    action="get_patient_context",
    user_id="dr_sharma",
    details={"query": "..."},
)

# View audit trail
tail -f data/sync_queue/audit_trail.jsonl
```

✅ **Encryption** - Data encrypted in transit (HTTPS) and at rest

✅ **Access Control** - API key authentication required

✅ **Data Minimization** - Only fetch relevant patient data

### Offline Mode

Works without internet connection:

```python
# Enable offline mode
emr = get_emr_service(offline_mode=True)

# All operations queued locally
await emr.push_recommendation(...)  # Queued

# When back online
await emr.sync_offline_queue()  # Syncs all pending
```

### FHIR Compliance

Full FHIR R4 support for hospital integrations:

```python
from src.emr import FHIRConverter

# Export to FHIR for other systems
fhir_bundle = patient_bundle_to_fhir(
    patient, medications, allergies, labs, diagnoses
)

# Import from hospital FHIR server
patient = converter.fhir_to_patient(fhir_data)
```

---

## Troubleshooting

### Common Issues

**1. Patient not found**
```python
# Check MRN format
patient = await client.get_patient("MH2024-001234")  # ✓
patient = await client.get_patient("001234")         # ✗
```

**2. Empty context**
```python
# Ensure patient has data in EMR
summary = await client.get_patient_summary(patient_id)
if not summary:
    print("Patient has no data in EMR")
```

**3. API connection errors**
```python
# Use mock client for development
emr = get_emr_service(use_mock=True)  # Always works

# Check API configuration
print(emr.emr_client.config.base_url)
```

**4. Offline queue not syncing**
```python
# Check offline mode
status = emr.get_sync_status()
if status['offline_mode']:
    print("Still offline - can't sync")

# Manual sync
results = await emr.sync_offline_queue()
print(f"Synced: {results['successful']}, Failed: {results['failed']}")
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Next Steps

- [ ] Integrate with frontend (see Web/Mobile sections below)
- [ ] Configure production EMR API credentials
- [ ] Set up audit log monitoring
- [ ] Train model on feedback data
- [ ] Enable A/B testing for recommendations

---

## Web Integration (TODO)

Location: `web/app/query/`

Needed files:
- `PatientSelector.tsx` - Patient dropdown
- `PatientContext.tsx` - Context sidebar
- `AlertBadge.tsx` - Clinical alerts display
- `PushToEMR.tsx` - Push recommendation button

## Mobile Integration (TODO)

Location: `mobile/lib/`

Needed files:
- `services/emr_service.dart` - Dart EMR client
- `widgets/patient_context.dart` - Context widget
- `screens/patient_select.dart` - Patient picker

---

For questions or issues, contact: dev@docassist.in
