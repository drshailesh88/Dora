# Medical Calculators Module

**Comprehensive medical calculators for the Dora medical knowledge platform**

## Overview

This module provides 50 evidence-based medical calculators across 8 clinical categories. Each calculator includes:
- Input validation
- Evidence-based formulas
- Clinical interpretation
- Risk stratification
- Management recommendations
- Citations/references
- Unit conversions where applicable

## Module Structure

```
src/calculators/
├── __init__.py                  # Module initialization and registry
├── base.py                      # Base calculator framework
├── cardiovascular.py            # 10 cardiovascular calculators
├── renal.py                     # 8 renal calculators
├── hepatic.py                   # 5 hepatic calculators
├── pulmonary.py                 # 5 pulmonary calculators
├── endocrine_metabolic.py       # 7 endocrine/metabolic calculators
├── neurology.py                 # 5 neurology calculators
├── obstetrics.py                # 3 obstetrics calculators
└── general.py                   # 7 general/utility calculators
```

## Calculator Categories

### Cardiovascular (10 calculators)
1. **ASCVD Risk Score** - 10-year atherosclerotic CVD risk (Pooled Cohort Equations)
2. **CHA₂DS₂-VASc** - Stroke risk in atrial fibrillation
3. **HAS-BLED** - Bleeding risk on anticoagulation
4. **HEART Score** - Chest pain risk stratification
5. **Wells DVT Score** - Deep vein thrombosis probability
6. **Wells PE Score** - Pulmonary embolism probability
7. **Framingham Risk Score** - 10-year cardiovascular disease risk
8. **TIMI Risk Score** - STEMI 30-day mortality
9. **Duke Treadmill Score** - Exercise stress test prognosis
10. **Corrected QT Interval** - QTc calculation (Bazett's formula)

### Renal (8 calculators)
1. **eGFR (CKD-EPI 2021)** - Race-free glomerular filtration rate
2. **Creatinine Clearance** - Cockcroft-Gault formula
3. **FENa** - Fractional excretion of sodium (prerenal vs intrinsic AKI)
4. **Urine Anion Gap** - Renal vs GI causes of NAGMA
5. **Serum Osmolality** - Calculated osmolality
6. **Osmolar Gap** - Detects unmeasured osmoles (toxic alcohols)
7. **RIFLE Criteria** - Acute kidney injury classification
8. **AKIN Criteria** - Acute Kidney Injury Network classification

### Hepatic (5 calculators)
1. **MELD Score** - End-stage liver disease mortality prediction
2. **MELD-Na** - MELD with sodium for transplant priority
3. **Child-Pugh Score** - Cirrhosis severity classification
4. **FIB-4 Index** - Non-invasive fibrosis assessment
5. **APRI Score** - AST to platelet ratio index for fibrosis

### Pulmonary (5 calculators)
1. **A-a Gradient** - Alveolar-arterial oxygen gradient
2. **PaO₂/FiO₂ Ratio** - P/F ratio for ARDS severity
3. **CURB-65** - Pneumonia severity assessment
4. **PSI/PORT Score** - Pneumonia Severity Index
5. **BODE Index** - COPD prognosis (4-year mortality)

### Endocrine/Metabolic (7 calculators)
1. **BMI** - Body mass index with WHO classification
2. **BSA** - Body surface area (Mosteller formula)
3. **Ideal Body Weight** - IBW calculation (Devine formula)
4. **Adjusted Body Weight** - For obese patients (medication dosing)
5. **Corrected Calcium** - Calcium adjusted for albumin
6. **Corrected Sodium** - Sodium corrected for hyperglycemia
7. **Anion Gap** - With albumin correction option

### Neurology (5 calculators)
1. **Glasgow Coma Scale** - Level of consciousness assessment
2. **NIH Stroke Scale** - Stroke severity quantification
3. **ABCD² Score** - Stroke risk after TIA
4. **Hunt-Hess Grade** - Subarachnoid hemorrhage severity
5. **Fisher Grade** - SAH vasospasm risk by CT

### Obstetrics (3 calculators)
1. **Estimated Due Date** - Naegele's rule with cycle adjustment
2. **Bishop Score** - Cervical favorability for induction
3. **Apgar Score** - Newborn health assessment (1, 5, 10 minutes)

### General (7 calculators)
1. **IV Fluid Rate** - Infusion rate calculation (mL/hr and drops/min)
2. **Drug Dosing by Weight** - Weight-based dose calculation
3. **Infusion Rate** - Medication infusion (vasopressors, insulin)
4. **Medical Unit Converter** - Common medical unit conversions
5. **Pediatric Weight Estimation** - Emergency weight estimation (APLS)
6. **Parkland Formula** - Burn fluid resuscitation
7. **Maintenance Fluid** - 4-2-1 rule for maintenance fluids

## Usage Examples

### Basic Python Usage

```python
from calculators import registry

# Get a calculator
bmi_calc = registry.get("bmi")

# Perform calculation
result = bmi_calc.calculate(weight=70, height=175, weight_unit="kg", height_unit="cm")

# Access results
print(f"BMI: {result.value}")
print(f"Interpretation: {result.interpretation}")
print(f"Risk Level: {result.risk_level.value}")
print(f"Recommendations: {result.recommendations}")
```

### API Usage

```python
# FastAPI integration
from fastapi import FastAPI
from src.api.calculators import router as calculator_router

app = FastAPI()
app.include_router(calculator_router)

# Endpoints available:
# GET  /api/v1/calculators                    - List all calculators
# GET  /api/v1/calculators/categories          - List categories
# GET  /api/v1/calculators/{id}                - Get calculator schema
# POST /api/v1/calculators/{id}/calculate      - Perform calculation
# GET  /api/v1/calculators/{id}/examples       - Get examples
# GET  /api/v1/calculators/health              - Health check
```

### REST API Example

```bash
# List all calculators
curl http://localhost:8000/api/v1/calculators

# Get calculator schema
curl http://localhost:8000/api/v1/calculators/bmi

# Perform calculation
curl -X POST http://localhost:8000/api/v1/calculators/bmi/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "weight": 70,
      "height": 175,
      "weight_unit": "kg",
      "height_unit": "cm"
    }
  }'
```

## Calculator Result Structure

All calculators return a `CalculatorResult` object with:

```python
{
    "value": <calculated value>,
    "interpretation": "Clinical interpretation",
    "risk_level": "low|moderate|high|very_high|critical",
    "reference_range": "Normal ranges",
    "recommendations": ["Clinical recommendation 1", "..."],
    "citations": ["Reference 1", "..."],
    "warnings": ["Warning 1", "..."],  # Optional
    "metadata": {
        "additional": "context-specific data"
    }
}
```

## Input Validation

All calculators include:
- Type validation
- Range validation (physiologically reasonable values)
- Required field validation
- Choice validation (for categorical inputs)
- Unit conversion where applicable

Example validation errors:
```python
ValidationError: "age must be >= 18, got 10"
ValidationError: "Missing required parameters: creatinine, age"
ValidationError: "sex must be one of ['male', 'female'], got 'other'"
```

## Unit Conversions

The module includes built-in converters for:
- Weight: kg ↔ lb ↔ g
- Height: cm ↔ m ↔ inch ↔ feet
- Creatinine: mg/dL ↔ μmol/L
- Temperature: Celsius ↔ Fahrenheit
- Glucose: mg/dL ↔ mmol/L

## Risk Stratification

Calculators use standardized risk levels:
- `VERY_LOW` - Minimal risk
- `LOW` - Low risk
- `MODERATE` - Moderate risk
- `HIGH` - High risk
- `VERY_HIGH` - Very high risk
- `CRITICAL` - Critical/life-threatening

## Evidence Base

All calculators are based on:
- Published clinical guidelines
- Peer-reviewed research
- Validated scoring systems
- Standard clinical formulas

Citations are included in each calculator's metadata.

## Clinical Compliance

### HIPAA Compliance
- No patient data is stored
- Calculations are stateless
- No logging of PHI
- All processing in-memory

### Medical Disclaimer
**IMPORTANT**: These calculators are clinical decision support tools and should not replace clinical judgment. Always verify results and consider the full clinical context.

### Quality Assurance
- Input validation prevents erroneous calculations
- Reference ranges from authoritative sources
- Regular updates to reflect current guidelines
- Unit tests for all calculators (recommended to add)

## Testing

Recommended test structure:
```python
# tests/test_calculators.py
def test_bmi_normal():
    calc = registry.get("bmi")
    result = calc.calculate(weight=70, height=175)
    assert 22 <= result.value <= 23
    assert result.risk_level == RiskLevel.LOW

def test_bmi_validation():
    calc = registry.get("bmi")
    with pytest.raises(ValidationError):
        calc.calculate(weight=-10, height=175)
```

## Future Enhancements

Potential additions:
- Interactive UI components
- Batch calculation support
- Export to PDF/CSV
- Clinical workflow integration
- Machine learning-based predictions
- Multi-language support
- Custom calculator builder

## Contributing

When adding new calculators:
1. Inherit from `Calculator` base class
2. Implement `calculate()` and `get_schema()` methods
3. Include comprehensive validation
4. Add citations/references
5. Provide clinical interpretation
6. Register in `__init__.py`
7. Add to appropriate category file

## License

Part of the Dora Medical Knowledge Platform
Developed for DocAssist

---

**Version**: 1.0.0
**Last Updated**: January 2026
**Total Calculators**: 50
**Categories**: 8
