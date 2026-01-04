# Drug Database Module

Comprehensive drug information, safety screening, and pricing system for the Dora medical platform.

## Features

### 1. **Drug Database** (`database.py`)
- SQLite-based storage with full-text search
- Fuzzy matching for drug name searches
- Offline-first architecture
- Supports 100+ common Indian drugs

### 2. **Drug Interactions** (`interactions.py`)
- Check drug-drug interactions
- Severity classification (contraindicated, major, moderate, minor)
- Clinical management recommendations
- Alternative suggestions

### 3. **Safety Checks** (`safety.py`)
- **Pregnancy Safety**: FDA categories (A/B/C/D/X) with trimester-specific warnings
- **Lactation Safety**: L1-L5 risk categories with infant monitoring
- **Renal Dosing**: GFR-based dose adjustments
- **Hepatic Dosing**: Child-Pugh score-based adjustments
- **Pediatric Dosing**: Age and weight-based calculations
- **Contraindications**: Patient condition screening
- **Allergy Cross-Reactivity**: Detect cross-reactive drugs

### 4. **Indian Drug Pricing** (`pricing.py`)
- Brand vs generic price comparison
- Pharmacy chain price lookup
- NLEM (National List of Essential Medicines) status
- Cost optimization recommendations
- Monthly/yearly cost calculations

### 5. **Unified Service** (`service.py`)
- Single interface for all drug operations
- Comprehensive prescription safety checks
- Alternative drug suggestions
- Total prescription cost calculation

## Quick Start

### 1. Load Sample Drugs

```bash
python scripts/load_sample_drugs.py
```

This loads 24 common drugs including:
- Cardiovascular: Amlodipine, Atenolol, Losartan, Clopidogrel
- Diabetes: Metformin, Glimepiride, Sitagliptin, Insulin
- Antibiotics: Amoxicillin, Azithromycin, Ciprofloxacin, Ceftriaxone
- Pain: Paracetamol, Ibuprofen, Diclofenac, Tramadol
- GI: Omeprazole, Pantoprazole, Ondansetron, Domperidone
- Psychiatric: Escitalopram, Sertraline, Alprazolam, Olanzapine

### 2. Use the Service

```python
from src.drugs import DrugService

# Initialize service
service = DrugService()

# Search for a drug
results = service.search_drugs("amlodipine")

# Get comprehensive drug info
drug_info = service.get_drug_info("amlodipine")

# Check prescription safety
safety = service.check_prescription_safety(
    drug_ids=["amlodipine", "atenolol"],
    patient_context={
        "pregnancy": True,
        "gfr": 45.0,
        "conditions": ["asthma"],
        "allergies": ["penicillin"]
    }
)

# Calculate prescription cost
cost = service.calculate_prescription_cost([
    {"drug_id": "metformin", "daily_dose": "500mg twice daily", "duration_days": 30},
    {"drug_id": "amlodipine", "daily_dose": "5mg once daily", "duration_days": 30}
])
```

## API Endpoints

All endpoints are prefixed with `/api/drugs`:

### Search & Information
- `GET /search` - Search drugs by name
- `GET /{drug_id}` - Get comprehensive drug information
- `GET /{drug_id}/alternatives` - Get alternative drugs

### Safety Checks
- `POST /interactions` - Check drug-drug interactions
- `GET /{drug_id}/pregnancy` - Pregnancy safety check
- `GET /{drug_id}/lactation` - Lactation safety check
- `POST /dosing/renal` - Calculate renal dose adjustment
- `POST /dosing/pediatric` - Calculate pediatric dose
- `POST /safety-check` - Comprehensive prescription safety check

### Pricing
- `GET /{drug_id}/pricing` - Get pricing information
- `POST /prescription/cost` - Calculate total prescription cost

### Statistics
- `GET /stats/database` - Get database statistics

## API Examples

### Search Drugs
```bash
curl "http://localhost:8000/api/drugs/search?query=metformin"
```

### Get Drug Info
```bash
curl "http://localhost:8000/api/drugs/metformin"
```

### Check Interactions
```bash
curl -X POST "http://localhost:8000/api/drugs/interactions" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_ids": ["metformin", "ibuprofen"]
  }'
```

### Pregnancy Safety
```bash
curl "http://localhost:8000/api/drugs/metformin/pregnancy?trimester=first"
```

### Comprehensive Safety Check
```bash
curl -X POST "http://localhost:8000/api/drugs/safety-check" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_ids": ["metformin", "amlodipine"],
    "patient_context": {
      "pregnancy": false,
      "lactating": true,
      "gfr": 60,
      "conditions": ["diabetes", "hypertension"],
      "allergies": []
    }
  }'
```

### Prescription Cost
```bash
curl -X POST "http://localhost:8000/api/drugs/prescription/cost" \
  -H "Content-Type: application/json" \
  -d '{
    "prescription": [
      {
        "drug_id": "metformin",
        "daily_dose": "500mg twice daily",
        "duration_days": 30
      },
      {
        "drug_id": "amlodipine",
        "daily_dose": "5mg once daily",
        "duration_days": 30
      }
    ]
  }'
```

## Data Models

### Drug
Complete drug information including:
- Generic and brand names (including Indian brands)
- Therapeutic class
- Mechanism of action
- Indications and contraindications
- Side effects
- Dosing information
- Pregnancy and lactation categories

### DrugInteraction
- Severity classification
- Clinical mechanism
- Management strategy
- Alternative suggestions
- Evidence level

### Safety Results
All safety checks return:
- `safe`: Boolean indicating overall safety
- `warnings`: List of warnings
- `contraindications`: List of contraindications
- `recommendations`: List of clinical recommendations
- `alternatives`: List of alternative drugs

## Offline Mode

The drug database works completely offline:
- SQLite database stored locally
- Full-text search without internet
- Fuzzy matching for misspellings
- Comprehensive interaction database

## Database Location

Default: `/home/user/Dora/data/drugs.db`

## Adding New Drugs

```python
from src.drugs import DrugDatabase, Drug, TherapeuticClass, PregnancyCategory, LactationRisk

db = DrugDatabase()

new_drug = Drug(
    id="new-drug-id",
    generic_name="New Drug Name",
    brand_names=["Brand A", "Brand B"],
    indian_brand_names=["Indian Brand"],
    therapeutic_class=TherapeuticClass.CARDIOVASCULAR,
    mechanism_of_action="How it works...",
    indications=["Indication 1", "Indication 2"],
    contraindications=["Contraindication 1"],
    common_side_effects=["Side effect 1"],
    serious_side_effects=["Serious effect 1"],
    adult_dose="Dosing information",
    pregnancy_category=PregnancyCategory.B,
    lactation_risk=LactationRisk.L2
)

db.add_drug(new_drug)
```

## Testing

```bash
# Run tests
pytest tests/test_drugs.py -v

# Test interaction checker
python -c "from src.drugs import DrugInteractionChecker; checker = DrugInteractionChecker(); print(checker.check_multiple(['warfarin', 'aspirin']))"

# Test safety checker
python -c "from src.drugs import DrugSafetyChecker; checker = DrugSafetyChecker(); print(checker.check_pregnancy_safety('metformin'))"
```

## Important Notes

### Medical Accuracy
- This is a reference tool, not a substitute for clinical judgment
- Always verify with current medical references
- Drug information should be regularly updated
- Consult specialists for complex cases

### Privacy & Compliance
- Patient data processed locally
- HIPAA/DISHA compliant architecture
- No cloud uploads without consent
- All data encrypted at rest

### Indian Context
- Prices in INR (Indian Rupees)
- Includes common Indian brand names
- NLEM drug identification
- Pharmacy chain pricing (Apollo, MedPlus, Netmeds, etc.)

## Future Enhancements

1. Integration with CDSCO (Central Drugs Standard Control Organization)
2. Real-time pricing API from pharmacies
3. Drug formulary management
4. Prescription history tracking
5. Drug utilization review (DUR)
6. Therapeutic interchange recommendations
7. Pharmacogenomics integration
8. Mobile app for drug lookup

## Support

For issues or questions:
- Check documentation: `/CLAUDE.md`
- Review examples: `/examples/`
- API reference: FastAPI auto-generated docs at `/docs`

## License

Part of the Dora Medical Knowledge Platform
© 2025 DocAssist
