# Prescription Module for Dora

## Overview

The prescription module provides **one-tap prescription generation from Dora AI answers** with comprehensive safety validation, cost-saving alternatives, digital signatures, and pharmacy integration.

## Key Features

### 🎯 One-Tap Prescription from Dora Answers
- AI-powered extraction of medications from natural language
- Automatic dosage, frequency, and duration parsing
- Confidence scoring for each extracted item
- Human confirmation workflow for safety

### 🛡️ Comprehensive Safety Validation
- **Drug-drug interactions** - Checks all prescribed medications
- **Drug-allergy conflicts** - Validates against patient allergies
- **Contraindications** - Based on patient conditions
- **Dosing validation** - Ensures doses within safe ranges
- **Renal/hepatic adjustments** - Flags medications needing dose adjustment
- **Pregnancy/lactation safety** - Warns about unsafe medications
- **Pediatric appropriateness** - Age-based safety checks

### 💰 Cost-Saving Alternatives
- Generic equivalents with price comparison
- Therapeutic alternatives in same drug class
- Insurance formulary options
- Monthly savings calculations

### 📝 Digital Signatures
- Digital certificate management
- Signature generation and verification
- Audit trail for compliance
- E-prescription generation

### 🏥 Integration
- **Pharmacy** - Send prescriptions to pharmacy for dispensing
- **EMR** - Push to Electronic Medical Records
- **Refill management** - Track and authorize refills
- **Templates** - Pre-configured prescriptions for common conditions

### 📄 Multiple Output Formats
- Beautiful text format (print-ready)
- PDF generation
- WhatsApp-optimized format
- EMR-compatible JSON
- E-prescription standard

## Architecture

```
src/prescription/
├── models.py          # Data models (Prescription, PrescriptionItem, etc.)
├── extractor.py       # AI-powered extraction from Dora answers
├── builder.py         # Prescription builder pattern
├── validator.py       # Safety validation engine
├── alternatives.py    # Drug alternatives suggester
├── templates.py       # Prescription templates
├── signature.py       # Digital signature system
├── formatter.py       # Output formatters
├── dispense.py        # Pharmacy integration
├── service.py         # Main orchestration layer
└── __init__.py        # Module exports
```

## Quick Start

### Installation

```bash
# The module is already part of the Dora project
# No separate installation needed
```

### Basic Usage

```python
from src.prescription import PrescriptionService

# Initialize service
service = PrescriptionService()

# Generate prescription from Dora answer
result = service.generate_from_dora_answer(
    answer_text="""
    For your diabetes, I recommend:
    1. Tab. Metformin 500mg - 1-0-1 x 30 days (after food)
    2. Tab. Glimepiride 2mg - 1-0-0 x 30 days (before breakfast)
    """,
    dora_answer_id="DORA-12345",
    patient=patient_info,
    doctor=doctor_info,
    diagnosis="Type 2 Diabetes Mellitus",
)

# Access results
prescription = result['prescription']
validation = result['validation']
alternatives = result['alternatives']
preview = result['preview']

# Print prescription
print(preview)
```

### Complete Workflow

```python
# End-to-end: Extract → Validate → Sign → Send
result = service.complete_workflow(
    answer_text=dora_answer,
    dora_answer_id="DORA-12345",
    patient=patient_info,
    doctor=doctor_info,
    certificate=digital_certificate,
    pharmacy_id="PHARM-001",  # Optional
    emr_api_client=emr_client,  # Optional
)

if result['success']:
    e_prescription = result['prescription']
    print(f"✅ Prescription signed: {e_prescription.e_prescription_id}")
```

## API Endpoints

### POST /api/prescription/extract
Extract prescription from Dora answer (the magic endpoint!)

```json
{
  "answer_text": "Tab. Metformin 500mg - 1-0-1 x 30 days",
  "dora_answer_id": "DORA-12345",
  "patient": { ... },
  "doctor": { ... }
}
```

### POST /api/prescription/validate
Validate prescription for safety

### GET /api/prescription/alternatives/{drug_name}
Get cost-saving alternatives

### POST /api/prescription/sign
Digitally sign prescription

### GET /api/prescription/templates
List available templates

### POST /api/prescription/pdf
Generate PDF prescription

See `/home/user/Dora/src/api/prescription.py` for complete API documentation.

## Web UI

React/Next.js UI at `/home/user/Dora/web/app/prescription/page.tsx`

Features:
- Tab-based interface (Extract, Manual, Preview, Alternatives)
- Real-time validation warnings
- Cost-saving alternatives display
- PDF download and pharmacy sending

## Mobile UI

Flutter UI at `/home/user/Dora/mobile/lib/screens/prescription_builder.dart`

Features:
- Native mobile experience
- Offline-capable
- Camera integration for scanning prescriptions (future)
- Push notifications for refills

## Prescription Templates

Pre-configured templates for common conditions:

- **Diabetes**: Type 2 DM initial, dual therapy
- **Hypertension**: Initial, dual therapy
- **URTI**: Upper respiratory tract infection
- **UTI**: Urinary tract infection
- **Gastritis**: GERD/acid reflux
- **Fever & Pain**: Symptomatic relief
- **Dyslipidemia**: High cholesterol

```python
# Use template
prescription = service.create_from_template(
    template_name='dm_type2_initial',
    patient=patient_info,
    doctor=doctor_info,
)
```

## Validation Example

```python
# Validate prescription
validation = service.validate_prescription(prescription)

if not validation.is_valid:
    print("❌ Validation failed:")
    for error in validation.errors:
        print(f"  - {error}")

for warning in validation.warnings:
    print(f"⚠️  {warning}")

# Check interactions
for interaction in validation.interactions:
    if interaction['severity'] == 'major':
        print(f"⚠️  INTERACTION: {interaction['drug1']} + {interaction['drug2']}")
        print(f"   {interaction['description']}")
```

## Sample Prescription Output

```
╔══════════════════════════════════════════════════════════════╗
║                    DocAssist Clinic                          ║
║            Dr. Shailesh Kumar, MD, MBBS                      ║
║         Reg No: MCI-12345 | Ph: +91-9876543210               ║
╠══════════════════════════════════════════════════════════════╣
║ Patient: Rahul Sharma (M, 45y)    Date: 04-Jan-2026          ║
║ MRN: PAT-2024-1234                                           ║
╠══════════════════════════════════════════════════════════════╣
║ Rx                                                           ║
║                                                              ║
║ 1. Tab. Metformin 500mg                                      ║
║    1-0-1 × 30 days (after food)                              ║
║    Qty: 60 tablets                                           ║
║                                                              ║
║ 2. Tab. Amlodipine 5mg                                       ║
║    0-0-1 × 30 days (at bedtime)                              ║
║    Qty: 30 tablets                                           ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║ Advice:                                                      ║
║ • Check blood sugar fasting weekly                           ║
║ • Low salt, low sugar diet                                   ║
║ • Walk 30 minutes daily                                      ║
║ • Follow up after 1 month with HbA1c                         ║
║                                                              ║
║ ⚠️ Avoid: Alcohol, Grapefruit juice                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║                     [Digital Signature]                      ║
║                    Dr. Shailesh Kumar                        ║
╚══════════════════════════════════════════════════════════════╝
```

## Safety Features

### Multi-Layer Validation
1. **Syntax validation** - Correct data types and formats
2. **Business rules** - Medical domain rules
3. **Drug interactions** - Drug database lookup
4. **Patient-specific** - Allergies, conditions, age
5. **Regulatory compliance** - HIPAA, DISHA, drug schedules

### Draft Mode
- All AI-extracted prescriptions marked as drafts
- Requires physician confirmation before signing
- Clear visual indicators in UI
- Audit trail of confirmations

### Confidence Scoring
- Each extracted medication has confidence score (0-1)
- Low confidence items highlighted for review
- Threshold-based filtering (default 0.7)

## Integration Points

### Drug Database (Future)
```python
# Configure drug database
service = PrescriptionService(
    drug_database=DrugDatabaseClient(api_key='...'),
    pricing_database=PricingDatabaseClient(api_key='...'),
)
```

### EMR Integration
```python
# Send to EMR
success = service.send_to_emr(
    prescription=prescription,
    emr_api_client=emr_client,
)
```

### Pharmacy Integration
```python
# Send to pharmacy
dispense_record = service.send_to_pharmacy(
    prescription=prescription,
    pharmacy_id='PHARM-001',
    delivery_method='pickup',
)

# Track status
status = service.pharmacy_service.get_dispense_status(
    prescription.prescription_id
)
```

## Testing

```bash
# Run tests
pytest src/prescription/

# Test extraction
python -m src.prescription.extractor

# Test validation
python -m src.prescription.validator

# Test service
python -m src.prescription.service
```

## Compliance

### Regulatory
- **HIPAA** - Patient data encryption and access controls
- **DISHA** (India) - Digital Health data protection
- **Drug Schedules** - Proper classification (H, H1, X)
- **E-prescription** - Digital signature requirements

### Audit Trail
- All prescription events logged
- Signature verification records
- Dispensing history
- Modification tracking

## Roadmap

### Phase 1 (Current) ✅
- AI-powered extraction
- Basic validation
- Templates
- Digital signatures
- Multiple output formats

### Phase 2 (Next)
- Real drug database integration
- Advanced interaction checking (CYP450, etc.)
- Biometric signatures
- Blockchain verification
- Insurance claim integration

### Phase 3 (Future)
- Camera OCR for physical prescriptions
- Voice-to-prescription
- Predictive refill scheduling
- Clinical decision support
- Real-world evidence integration

## Contributing

See main project CLAUDE.md for development guidelines.

Key principles:
- Test-first development (TDD)
- Library-first architecture
- Draft-mode for AI outputs
- Evidence-based recommendations
- Clear audit trails

## Support

For issues or questions:
1. Check this README
2. Review code comments
3. See example usage in each module
4. Open issue in main Dora repository

---

**Built with ❤️ for Indian doctors**

*Making prescription writing faster, safer, and smarter.*
