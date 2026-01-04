"""
Protocol Templates

Pre-built clinical protocol templates for common medical scenarios.
"""

from typing import Dict
from .models import Protocol, ProtocolCategory, ProtocolStatus


# Template content library
CHEST_PAIN_PROTOCOL = """# Chest Pain Protocol
**Version:** 2.1 | **Status:** Published | **Evidence Grade:** A
**Scope:** Adult patients presenting with acute chest pain to Emergency Department

## Initial Assessment (First 10 Minutes)

### Critical Actions
1. ☐ Vital signs (BP, HR, SpO2, RR, Temperature)
2. ☐ **12-lead ECG within 10 minutes**
3. ☐ IV access established (18G or larger)
4. ☐ Oxygen if SpO2 < 94% (target 94-98%)
5. ☐ Aspirin 325mg PO (if no contraindications)
6. ☐ Nitroglycerin 0.4mg SL (if BP > 90 systolic)

### OPQRST Assessment
- **O**nset: When did pain start? Sudden or gradual?
- **P**rovocation: What makes it better/worse?
- **Q**uality: Crushing, stabbing, burning?
- **R**adiation: Does pain radiate to arm, jaw, back?
- **S**everity: Pain scale 0-10
- **T**iming: Constant or intermittent?

## Risk Stratification

### HIGH RISK (Any of following) → **IMMEDIATE CARDIOLOGY CONSULT**
- ST elevation on ECG (≥1mm in 2 contiguous leads)
- New LBBB with clinical suspicion for MI
- Hemodynamic instability (BP < 90 systolic, HR > 120)
- Ongoing chest pain with dynamic ECG changes
- Cardiogenic shock
- Ventricular arrhythmias

**Action:** Activate Cath Lab, start STEMI protocol

### INTERMEDIATE RISK
- Troponin elevated (above 99th percentile)
- HEART score ≥ 4
- Known CAD with new symptoms
- Diabetes + chest pain
- ST depression or T-wave inversion

**Action:** Admit to monitored bed, serial troponins (0, 3, 6 hours), cardiology consult

### LOW RISK
- HEART score < 4
- Normal ECG
- Negative troponin (ideally 2 measurements 3 hours apart)
- Atypical chest pain features
- Reproducible chest wall tenderness

**Action:** Consider discharge with stress test follow-up within 72 hours

## HEART Score Calculation

| Component | 0 points | 1 point | 2 points |
|-----------|----------|---------|----------|
| **History** | Slightly suspicious | Moderately suspicious | Highly suspicious |
| **ECG** | Normal | Non-specific repolarization | Significant ST deviation |
| **Age** | < 45 years | 45-64 years | ≥ 65 years |
| **Risk Factors*** | None | 1-2 factors | ≥ 3 factors |
| **Troponin** | Normal | 1-3x normal | > 3x normal |

*Risk factors: HTN, hyperlipidemia, DM, smoking, family history, obesity

**Score Interpretation:**
- 0-3: Low risk (1.7% MACE)
- 4-6: Moderate risk (12-65% MACE)
- 7-10: High risk (50-65% MACE)

## Medications

### Anti-Platelet Therapy
| Drug | Dose | Route | Indication | Contraindications |
|------|------|-------|------------|-------------------|
| Aspirin | 325mg | PO | All ACS unless CI | Active bleeding, known allergy, recent GI bleed |
| Clopidogrel | 300-600mg | PO | NSTEMI/STEMI | Active bleeding, planned CABG |
| Ticagrelor | 180mg | PO | ACS (preferred over clopidogrel) | Active bleeding, ICH history |

### Anti-Ischemic Therapy
| Drug | Dose | Route | Indication |
|------|------|-------|------------|
| Nitroglycerin | 0.4mg q5min × 3 | SL | Ongoing chest pain, BP > 90 |
| Nitroglycerin | 10-200 mcg/min | IV infusion | Refractory pain, pulmonary edema |
| Metoprolol | 5mg q5min × 3 | IV | STEMI/NSTEMI, tachycardia |
| Morphine | 2-4mg q5-15min | IV | Pain uncontrolled by NTG |

### Anticoagulation (for ACS confirmed)
| Drug | Dose | Route | Notes |
|------|------|-------|-------|
| Heparin | 60 U/kg bolus (max 4000 U) | IV | Then 12 U/kg/hr (max 1000 U/hr) |
| Enoxaparin | 1 mg/kg q12h | SC | If NOT going to cath lab |

## Critical Contraindications

### ⚠️ DO NOT Give Aspirin if:
- Active bleeding
- Known aspirin allergy/anaphylaxis
- Recent significant GI bleed (< 7 days)
- Severe thrombocytopenia (< 50,000)

### ⚠️ DO NOT Give Nitroglycerin if:
- Systolic BP < 90 mmHg
- Severe aortic stenosis
- Recent PDE5 inhibitor use (sildenafil < 24h, tadalafil < 48h)
- Right ventricular infarction (inferior STEMI with RV involvement)

### ⚠️ DO NOT Give Beta-blockers if:
- Active bronchospasm
- Severe bradycardia (HR < 50)
- 2nd/3rd degree heart block
- Cardiogenic shock

## Differential Diagnosis (Non-Cardiac)

### Life-Threatening Causes
- **Aortic Dissection**: Tearing pain, radiating to back, BP differential in arms
- **Pulmonary Embolism**: Dyspnea, hypoxia, tachycardia, Wells score
- **Tension Pneumothorax**: Unilateral absent breath sounds, tracheal deviation
- **Esophageal Rupture**: Recent vomiting, Hamman's sign, mediastinal air

### Common Causes
- **GERD**: Burning, worse after meals, responds to antacids
- **Musculoskeletal**: Reproducible with palpation, worse with movement
- **Costochondritis**: Tender costosternal junctions
- **Anxiety/Panic**: Younger patient, associated hyperventilation, normal workup

## Disposition

### Admit to CCU/ICU
- STEMI
- High-risk NSTEMI
- Cardiogenic shock
- Hemodynamic instability

### Admit to Telemetry
- Intermediate-risk chest pain
- Elevated troponin
- Dynamic ECG changes
- HEART score ≥ 4

### Discharge Home
- Low-risk chest pain (HEART < 4)
- Two negative troponins 3 hours apart
- Normal ECG
- Stress test scheduled < 72 hours
- Clear discharge instructions
- Return precautions explained

## Documentation Requirements
- Time of symptom onset
- ECG interpretation with time
- Serial troponin results
- HEART score calculation
- Medications given with times
- Cardiology consultation (if applicable)
- Disposition and follow-up plan

## References
1. Amsterdam EA, et al. 2014 AHA/ACC Guideline for the Management of Patients with Non-ST-Elevation Acute Coronary Syndromes. Circulation. 2014.
2. O'Gara PT, et al. 2013 ACCF/AHA Guideline for the Management of ST-Elevation Myocardial Infarction. Circulation. 2013.
3. Six AJ, et al. The HEART score for the assessment of patients with chest pain in the emergency department. Crit Pathw Cardiol. 2008.

---
*Last reviewed: January 2026 | Next review: July 2026*
*Approved by: Cardiology Department*
"""

SEPSIS_PROTOCOL = """# Sepsis Management Protocol
**Version:** 3.0 | **Status:** Published | **Evidence Grade:** A
**Scope:** Adult patients with suspected or confirmed sepsis

## Early Recognition (Within 1 Hour)

### qSOFA Score (Quick Sequential Organ Failure Assessment)
- **Respiratory rate** ≥ 22/min
- **Altered mentation** (GCS < 15)
- **Systolic BP** ≤ 100 mmHg

**≥ 2 criteria = HIGH RISK for poor outcomes**

### SIRS Criteria (2 or more)
1. Temperature > 38°C or < 36°C
2. Heart rate > 90 bpm
3. Respiratory rate > 20/min or PaCO2 < 32 mmHg
4. WBC > 12,000 or < 4,000 or > 10% bands

## Sepsis Bundle: "HOUR-1 BUNDLE"

### Within 1 Hour of Recognition:
1. ☐ **Measure lactate** (repeat if > 2 mmol/L)
2. ☐ **Obtain blood cultures** (2 sets from different sites)
3. ☐ **Administer broad-spectrum antibiotics**
4. ☐ **Rapid fluid resuscitation** (30 mL/kg crystalloid)
5. ☐ **Vasopressors** if hypotensive during or after fluid resuscitation (target MAP ≥ 65)

## Diagnostic Workup

### Initial Labs (STAT)
- Complete blood count with differential
- Comprehensive metabolic panel
- Lactate (arterial or venous)
- Procalcitonin
- Coagulation studies (PT/INR, PTT)
- Blood cultures × 2 (before antibiotics if possible)

### Additional Studies Based on Source
- **Respiratory:** Chest X-ray, sputum culture
- **Urinary:** Urinalysis, urine culture
- **Abdominal:** CT abdomen/pelvis, lipase
- **Skin/Soft tissue:** Wound culture, imaging if necrotizing infection suspected
- **CNS:** Lumbar puncture if meningitis suspected

## Fluid Resuscitation

### Initial Resuscitation (0-3 hours)
- **30 mL/kg crystalloid** (normal saline or lactated Ringer's)
- Administer rapidly (give over 2-3 hours)
- Example: 70 kg patient = 2,100 mL

### Reassess After Initial Bolus
- Vital signs
- Urine output
- Mental status
- Lactate clearance
- Physical exam (lung sounds, peripheral perfusion)

### Dynamic Fluid Assessment
Use one or more:
- Passive leg raise test
- Fluid challenge with assessment
- Ultrasound (IVC collapsibility, cardiac function)

⚠️ **AVOID FLUID OVERLOAD** - Watch for:
- Pulmonary edema
- Decreased SpO2
- Increased work of breathing
- JVD, peripheral edema

## Empiric Antibiotic Selection

### Community-Acquired Sepsis
**First-line:**
- Piperacillin-Tazobactam 4.5g IV q6h
- OR Ceftriaxone 2g IV q24h + Metronidazole 500mg IV q8h

**Severe penicillin allergy:**
- Aztreonam 2g IV q8h + Metronidazole 500mg IV q8h

### Hospital-Acquired/Healthcare-Associated
**Broad coverage:**
- Meropenem 1g IV q8h
- OR Piperacillin-Tazobactam 4.5g IV q6h + Vancomycin (dose by weight)

**MRSA coverage** (add if risk factors):
- Vancomycin 15-20 mg/kg IV q12h (target trough 15-20)
- OR Linezolid 600mg IV q12h

### Source-Specific Modifications
| Source | Add |
|--------|-----|
| **Pneumonia** | Azithromycin 500mg IV (atypical coverage) |
| **Intra-abdominal** | Ensure anaerobic coverage (metronidazole) |
| **Urinary** | Consider narrowing to ceftriaxone if gram-negative |
| **Skin/Soft tissue** | Add clindamycin if necrotizing infection |
| **CNS** | Ceftriaxone + Vancomycin + Acyclovir |

⚠️ **ADJUST based on:**
- Local antibiogram
- Patient allergies
- Renal/hepatic function
- Recent antibiotic exposure

## Vasopressor Support

### Indications
- MAP < 65 mmHg despite adequate fluid resuscitation
- Lactate > 4 mmol/L with hypotension

### First-Line: Norepinephrine
- Start: 0.05-0.1 mcg/kg/min
- Titrate to MAP ≥ 65 mmHg
- Max: 3 mcg/kg/min (if higher, add second agent)

### Second-Line Options
**Vasopressin** (add to norepinephrine):
- Fixed dose: 0.03-0.04 units/min
- Use when norepinephrine > 0.5 mcg/kg/min

**Epinephrine** (if refractory):
- Start: 0.05 mcg/kg/min
- Titrate to effect

**Phenylephrine** (if tachyarrhythmias):
- Start: 0.5 mcg/kg/min
- Pure vasoconstrictor, no inotropic effect

### ⚠️ Central Line Required
- Peripheral vasopressors only temporizing (< 6 hours)
- Place central line urgently

## Monitoring & Reassessment

### Every 30-60 Minutes Initially
- Vital signs
- Urine output (target > 0.5 mL/kg/hr)
- Mental status
- Peripheral perfusion (cap refill, skin temperature)

### Every 2-4 Hours
- Lactate (target clearance > 10% per hour)
- Blood gases
- Hemoglobin (target > 7 g/dL in sepsis)

### Daily
- Procalcitonin (trend for antibiotic stewardship)
- Reassess antibiotic spectrum
- Assess for source control

## Source Control

### Surgical Consultation if:
- Intra-abdominal abscess
- Necrotizing soft tissue infection
- Infected device (pacemaker, prosthetic joint)
- Empyema
- Cholangitis with obstruction

**⏰ TIMING: Within 6-12 hours of diagnosis**

## Red Flags: Consider ICU Transfer

- Requiring vasopressors
- Lactate > 4 mmol/L
- Altered mental status
- Respiratory distress (RR > 30, SpO2 < 90%)
- Acute kidney injury (oliguria despite fluids)
- New organ dysfunction

## Steroid Therapy

### Consider Hydrocortisone if:
- Refractory shock (requiring high-dose vasopressors)
- Dose: 200 mg/day continuous infusion or divided q6h
- Duration: Taper after shock resolution (typically 3-5 days)

## Antibiotic De-Escalation

### Reassess at 48-72 Hours
- Culture results available?
- Clinical improvement?
- Lactate normalized?
- Procalcitonin trending down?

**Narrow spectrum** based on culture data
**Discontinue** if alternative diagnosis confirmed

## Disposition
- **ICU:** Septic shock, requiring vasopressors, mechanical ventilation
- **Step-down:** Sepsis improving, weaning vasopressors
- **Floor:** Sepsis resolved, stable on antibiotics

## Documentation
- Time of recognition
- qSOFA/SIRS criteria
- Lactate value(s)
- Time of antibiotic administration
- Fluid volume administered
- Source of infection
- Vasopressor dose and duration

## References
1. Evans L, et al. Surviving Sepsis Campaign: International Guidelines for Management of Sepsis and Septic Shock 2021. Crit Care Med. 2021.
2. Seymour CW, et al. Assessment of Clinical Criteria for Sepsis. JAMA. 2016.

---
*Last reviewed: January 2026 | Next review: July 2026*
*Based on: Surviving Sepsis Campaign 2021*
"""

DKA_PROTOCOL = """# Diabetic Ketoacidosis (DKA) Management
**Version:** 2.0 | **Status:** Published | **Evidence Grade:** A
**Scope:** Adult patients with diabetic ketoacidosis

## Diagnostic Criteria (All 3 Required)
1. **Hyperglycemia:** Glucose > 250 mg/dL
2. **Metabolic Acidosis:** pH < 7.3 or HCO3 < 18 mEq/L
3. **Ketosis:** Serum ketones positive or urine ketones moderate/large

## Severity Classification

| Parameter | Mild | Moderate | Severe |
|-----------|------|----------|--------|
| **pH** | 7.25-7.30 | 7.00-7.24 | < 7.00 |
| **HCO3** | 15-18 | 10-15 | < 10 |
| **Anion Gap** | > 10 | > 12 | > 12 |
| **Mental Status** | Alert | Alert/Drowsy | Stupor/Coma |

## Initial Assessment (First Hour)

### Labs (STAT)
- ☐ Fingerstick glucose
- ☐ Basic metabolic panel
- ☐ Venous or arterial blood gas
- ☐ Serum ketones (beta-hydroxybutyrate preferred)
- ☐ Urine ketones and urinalysis
- ☐ CBC
- ☐ Hemoglobin A1c
- ☐ Pregnancy test (females of childbearing age)

### Additional Studies
- ☐ ECG (look for hyperkalemia, MI)
- ☐ Chest X-ray (if infection suspected)
- ☐ Blood cultures (if febrile)
- ☐ Cardiac enzymes (if chest pain/ECG changes)

### Calculate Corrected Sodium
**Corrected Na+ = Measured Na+ + [1.6 × (Glucose - 100) / 100]**

Use corrected sodium for fluid calculations

### Calculate Anion Gap
**AG = Na+ - (Cl- + HCO3-)**
Normal: 12 ± 2

## Management Protocol

### Phase 1: Fluid Resuscitation (0-2 hours)

**Initial Bolus:**
- 1 L NS over 1 hour (15-20 mL/kg)
- If severe dehydration or shock: May give additional 1 L over next hour

**Subsequent Fluids (after initial bolus):**

| Corrected Sodium | Fluid Choice |
|------------------|--------------|
| **High (> 150)** | 0.45% NaCl at 250-500 mL/hr |
| **Normal (135-150)** | 0.9% NaCl at 250-500 mL/hr |
| **Low (< 135)** | 0.9% NaCl at 250-500 mL/hr |

**Goals:**
- Urine output > 0.5 mL/kg/hr
- Gradual correction of dehydration (deficit typically 5-7 L)

### Phase 2: Insulin Therapy

**DO NOT start insulin until:**
- ☐ Potassium ≥ 3.3 mEq/L
- ☐ Fluids initiated

**Regular Insulin Protocol:**
1. **Loading dose:** 0.1 units/kg IV bolus
2. **Continuous infusion:** 0.1 units/kg/hr (usually 5-10 units/hr)

**Titration:**
- If glucose doesn't drop by 50-70 mg/dL in 1st hour → DOUBLE insulin rate
- Target glucose decline: 50-70 mg/dL per hour
- When glucose reaches 200-250 mg/dL → REDUCE insulin to 0.05 units/kg/hr
- Add D5 to fluids when glucose < 250 mg/dL

⚠️ **DO NOT stop insulin** even when glucose normalizes - DKA resolution requires continued insulin to clear ketones

### Phase 3: Potassium Replacement

**Critical:** DKA causes total body K+ depletion despite normal/high serum K+

| Serum K+ | Action |
|----------|--------|
| **< 3.3** | HOLD INSULIN. Give 20-30 mEq/hr until K+ > 3.3 |
| **3.3-5.2** | Add 20-30 mEq to each liter of IV fluid |
| **> 5.2** | No K+ supplementation. Recheck in 2 hours |

**Potassium Options:**
- KCl 20-40 mEq/L in IV fluids
- May need up to 10-20 mEq/hr if severely hypokalemic

⚠️ **DANGER:** Insulin drives K+ into cells → can cause life-threatening hypokalemia

### Phase 4: Monitor for Resolution

**Check labs every 2-4 hours:**
- Glucose (q1h initially)
- Electrolytes
- Venous pH/HCO3

**DKA Resolution Criteria (All required):**
1. ✓ Glucose < 200 mg/dL
2. ✓ Anion gap < 12
3. ✓ pH > 7.3
4. ✓ HCO3 > 18 mEq/L

## Transition to Subcutaneous Insulin

**Timing:** When DKA resolved AND patient able to eat

**Overlap Required:**
1. Give subcutaneous insulin (basal + prandial)
2. Continue IV insulin for 2 hours AFTER subcutaneous dose
3. Then discontinue IV insulin

**Dosing:**
- **New onset DM:** 0.5-0.6 units/kg/day total daily dose (TDD)
- **Known diabetic:** Resume home regimen (if previously well-controlled)
- **Divide:** 50% basal (glargine/detemir), 50% prandial (lispro/aspart)

## Bicarbonate Therapy

**Indication:** pH < 6.9 ONLY

**Dose:** 100 mmol sodium bicarbonate in 400 mL sterile water + 20 mEq KCl
**Rate:** Over 2 hours
**Repeat:** If pH still < 7.0 after 2 hours

⚠️ **Routine bicarbonate NOT recommended** - may worsen hypokalemia and cerebral edema risk

## Phosphate Replacement

**Generally NOT required unless:**
- Severe hypophosphatemia (< 1.0 mg/dL)
- Cardiac dysfunction
- Respiratory depression

**If needed:** K-Phos 20-30 mEq/L in IV fluids

## Complications to Monitor

### Cerebral Edema (RARE but FATAL)
**Risk factors:** Young age, new-onset DM, severe acidosis, rapid correction

**Symptoms:**
- Headache
- Altered mental status decline
- Bradycardia
- Increased BP
- Papilledema

**Treatment:**
- Mannitol 0.5-1 g/kg IV over 20 min
- OR 3% hypertonic saline 2-5 mL/kg over 30 min
- Neurosurgery consult
- ICU transfer

### Hypokalemia
- Most common cause of death in DKA
- Monitor K+ closely
- Aggressive replacement

### Hypoglycemia
- Add dextrose when glucose < 250 mg/dL
- Don't stop insulin!

## Precipitating Factors (Find and Treat)

Common causes:
- **Infection** (40%): UTI, pneumonia, skin
- **Insulin non-compliance** (25%)
- **New-onset diabetes** (20%)
- **MI/CVA**
- **Pancreatitis**
- **Medications:** Steroids, antipsychotics

## ICU Criteria
- pH < 7.0
- Altered mental status
- Hemodynamic instability
- Severe comorbidities
- Age > 65 with moderate-severe DKA

## Flowsheet Monitoring

**Q1H:**
- Glucose (fingerstick)
- Vital signs
- Neurological status

**Q2-4H:**
- Electrolytes (Na, K, Cl, HCO3)
- Anion gap calculation
- Venous pH

**Q6-8H:**
- Mg, Phosphate
- Urine output

## Documentation
- DKA severity
- Precipitating cause
- Fluid volume given
- Insulin dose and rate changes
- Potassium replacement
- Time to DKA resolution

## References
1. Kitabchi AE, et al. Hyperglycemic Crises in Adult Patients With Diabetes. Diabetes Care. 2009.
2. Wolfsdorf JI, et al. Diabetic Ketoacidosis and Hyperglycemic Hyperosmolar State. Pediatr Diabetes. 2018.

---
*Last reviewed: January 2026 | Next review: July 2026*
*Based on: ADA Guidelines 2023*
"""

STROKE_PROTOCOL = """# Acute Stroke Protocol
**Version:** 3.1 | **Status:** Published | **Evidence Grade:** A
**Scope:** Adult patients with suspected acute stroke

## Time is Brain: 1.9 Million Neurons Die Per Minute

### Critical Time Windows
- **tPA window:** 4.5 hours from symptom onset
- **Thrombectomy window:** Up to 24 hours (selected patients)
- **Door-to-needle goal:** < 60 minutes
- **Door-to-imaging goal:** < 25 minutes

## Rapid Recognition: BE-FAST

- **B**alance: Loss of balance, dizziness
- **E**yes: Vision changes
- **F**ace: Facial droop (ask patient to smile)
- **A**rms: Arm weakness (ask to raise both arms)
- **S**peech: Speech difficulty (ask to repeat phrase)
- **T**ime: Time to call 911

## Initial Assessment (Within 10 Minutes)

### Immediate Actions
1. ☐ ABC assessment
2. ☐ Fingerstick glucose
3. ☐ Vital signs (BP, HR, SpO2, temp)
4. ☐ Obtain brief history (onset time is CRITICAL)
5. ☐ **ACTIVATE STROKE TEAM**
6. ☐ Nil per os (NPO)
7. ☐ IV access × 2
8. ☐ Cardiac monitor, pulse oximetry
9. ☐ Oxygen if SpO2 < 94%

### NIHSS Score (National Institutes of Health Stroke Scale)
**Score range: 0-42**
- 0: No stroke
- 1-4: Minor stroke
- 5-15: Moderate stroke
- 16-20: Moderate-severe stroke
- 21-42: Severe stroke

[Document full NIHSS - Level of consciousness, gaze, visual fields, facial palsy, motor arm/leg, ataxia, sensory, language, dysarthria, extinction/inattention]

## Diagnostic Workup (Parallel Processing)

### Immediate Labs (Don't delay imaging)
- ☐ CBC with platelets
- ☐ PT/INR, PTT
- ☐ Basic metabolic panel
- ☐ Troponin
- ☐ Pregnancy test (if applicable)
- ☐ Type and screen

### Immediate Imaging
- ☐ **Non-contrast CT head** (to rule out hemorrhage)
- ☐ CT angiography (CTA) head and neck (if thrombectomy candidate)
- ☐ CT perfusion (if extended window thrombectomy considered)

**Imaging interpretation within 20 minutes**

### Additional Tests
- ☐ ECG (atrial fibrillation?)
- ☐ Chest X-ray
- ☐ MRI brain (if diagnosis uncertain, or for posterior circulation)

## tPA (Alteplase) Eligibility

### Inclusion Criteria (ALL required)
- ✓ Clinical diagnosis of ischemic stroke
- ✓ Measurable neurological deficit (NIHSS ≥ 4 typically)
- ✓ Onset < 4.5 hours (or last known well < 4.5 hours)
- ✓ Age ≥ 18 years
- ✓ CT excludes hemorrhage

### Absolute Contraindications
- ✗ Intracranial hemorrhage on CT
- ✗ Recent (< 3 months) major surgery, head trauma, or stroke
- ✗ Uncontrolled hypertension (SBP > 185 or DBP > 110)
- ✗ Active internal bleeding
- ✗ Platelet count < 100,000
- ✗ INR > 1.7 or PT > 15
- ✗ Current use of direct thrombin or factor Xa inhibitors
- ✗ Glucose < 50 mg/dL

### Relative Contraindications (3-4.5 hour window)
- Age > 80 years
- NIHSS > 25
- History of diabetes + prior stroke
- Oral anticoagulant use (even if INR < 1.7)

## tPA Administration

**Alteplase dose: 0.9 mg/kg (maximum 90 mg)**

1. **Bolus:** 10% of dose IV over 1 minute
2. **Infusion:** Remaining 90% over 60 minutes

**Example:** 70 kg patient = 63 mg total
- Bolus: 6.3 mg over 1 min
- Infusion: 56.7 mg over 60 min

### Pre-tPA Checklist
- ☐ Consent obtained (or waived in emergency)
- ☐ BP < 185/110 (treat if elevated)
- ☐ Two large-bore IVs
- ☐ No anticoagulants, antiplatelets for 24 hours
- ☐ No NG tube, Foley catheter (defer if possible)
- ☐ Neurosurgery aware

## Blood Pressure Management

### Before and During tPA
**Target: < 185/110 mmHg**

**If SBP > 185 or DBP > 110:**
- Labetalol 10-20 mg IV over 1-2 min (may repeat × 1)
- OR Nicardipine infusion 5 mg/hr, titrate by 2.5 mg/hr q5-15min (max 15 mg/hr)

### After tPA (First 24 Hours)
**Target: < 180/105 mmHg**

**Monitoring:**
- Q15min × 2 hours
- Q30min × 6 hours
- Q1h × 16 hours

**If BP rises > 180/105:**
- Same medications as above

### After 24 Hours (if no complications)
- Allow higher BP (permissive hypertension)
- Target < 220/120 usually acceptable
- Restart home antihypertensives gradually

## Mechanical Thrombectomy

### Indications
- Large vessel occlusion (ICA, M1, M2, basilar)
- NIHSS ≥ 6
- Age ≥ 18
- Pre-stroke mRS 0-1 (independent)
- ASPECTS ≥ 6 on CT

### Time Windows
- **0-6 hours:** All eligible patients
- **6-24 hours:** Selected patients with favorable penumbra on imaging

**Thrombectomy does NOT replace tPA - give both if eligible**

## Post-tPA Monitoring

### Neuro Checks
- Q15min × 2 hours
- Q30min × 6 hours
- Q1h × 16 hours

**Call physician if:**
- Severe headache
- Nausea/vomiting
- Acute hypertension
- Neurological worsening (NIHSS increase ≥ 4)

### Complications

**Symptomatic ICH (6% risk):**
- Sudden neurological deterioration
- Severe headache
- Nausea, vomiting
- Elevated BP

**Management:**
- STOP tPA
- STAT CT head
- Type and cross 4 units
- Reverse anticoagulation:
  - Cryoprecipitate 10 units
  - Tranexamic acid 1g IV
- Neurosurgery STAT

## Antiplatelet Therapy

### If tPA given:
- NO antiplatelet or anticoagulation × 24 hours
- Repeat CT at 24 hours to rule out hemorrhage
- Start aspirin 325 mg daily after negative CT

### If tPA NOT given:
- Aspirin 325 mg loading dose, then 81-325 mg daily
- OR Aspirin 50-325 mg + Clopidogrel 75 mg × 21 days (minor stroke, NIHSS < 3)

## Anticoagulation (for Atrial Fibrillation)

**Timing:**
- Small stroke: Start day 3-7
- Moderate stroke: Start day 7-14
- Large stroke: Defer 2-4 weeks

**Choice:**
- Direct oral anticoagulants (DOACs) preferred: Apixaban, rivaroxaban, dabigatran
- Warfarin if contraindication to DOACs

## Secondary Prevention Workup

### Cardiac Evaluation
- Telemetry monitoring ≥ 24 hours
- Echocardiogram (TTE, consider TEE if PFO suspected)
- Extended cardiac monitoring (if cryptogenic stroke)

### Vascular Imaging
- Carotid ultrasound
- CTA or MRA head and neck

### Labs
- Lipid panel
- Hemoglobin A1c
- Hypercoagulable workup (if age < 50, no risk factors)

## Disposition
- **ICU:** tPA given, thrombectomy, large stroke, hemorrhagic transformation risk
- **Stroke unit:** Ischemic stroke without tPA, stable
- **Rehabilitation:** Once acute phase resolved

## Discharge Planning
- Aspirin or anticoagulation
- Statin (high-intensity: atorvastatin 80 mg)
- BP control
- Diabetes management
- Smoking cessation
- Rehab (PT/OT/Speech)
- Neurology follow-up

## References
1. Powers WJ, et al. 2018 Guidelines for the Early Management of Patients With Acute Ischemic Stroke. Stroke. 2018.
2. Nogueira RG, et al. Thrombectomy 6 to 24 Hours after Stroke with a Mismatch between Deficit and Infarct. N Engl J Med. 2018.

---
*Last reviewed: January 2026 | Next review: July 2026*
*Based on: AHA/ASA 2019 Update*
"""


# Template registry
PROTOCOL_TEMPLATES: Dict[str, Protocol] = {
    "chest_pain": Protocol(
        title="Chest Pain Protocol",
        description="Acute chest pain evaluation and management in emergency department",
        category=ProtocolCategory.EMERGENCY,
        tags=["cardiology", "ACS", "STEMI", "emergency", "chest pain"],
        content=CHEST_PAIN_PROTOCOL,
        status=ProtocolStatus.PUBLISHED,
        is_template=True,
        version_number="2.1",
        evidence_grade="A",
        references=[
            "Amsterdam EA, et al. 2014 AHA/ACC Guideline for the Management of Patients with Non-ST-Elevation Acute Coronary Syndromes",
            "O'Gara PT, et al. 2013 ACCF/AHA Guideline for the Management of ST-Elevation Myocardial Infarction",
            "Six AJ, et al. The HEART score for the assessment of patients with chest pain in the emergency department",
        ],
    ),
    "sepsis": Protocol(
        title="Sepsis Management Protocol",
        description="Early recognition and management of sepsis and septic shock",
        category=ProtocolCategory.EMERGENCY,
        tags=["sepsis", "infection", "emergency", "critical care", "antibiotics"],
        content=SEPSIS_PROTOCOL,
        status=ProtocolStatus.PUBLISHED,
        is_template=True,
        version_number="3.0",
        evidence_grade="A",
        references=[
            "Evans L, et al. Surviving Sepsis Campaign: International Guidelines for Management of Sepsis and Septic Shock 2021",
            "Seymour CW, et al. Assessment of Clinical Criteria for Sepsis. JAMA. 2016",
        ],
    ),
    "dka": Protocol(
        title="Diabetic Ketoacidosis (DKA) Management",
        description="Protocol for management of diabetic ketoacidosis in adult patients",
        category=ProtocolCategory.EMERGENCY,
        tags=["diabetes", "DKA", "endocrine", "emergency", "insulin"],
        content=DKA_PROTOCOL,
        status=ProtocolStatus.PUBLISHED,
        is_template=True,
        version_number="2.0",
        evidence_grade="A",
        references=[
            "Kitabchi AE, et al. Hyperglycemic Crises in Adult Patients With Diabetes. Diabetes Care. 2009",
            "Wolfsdorf JI, et al. Diabetic Ketoacidosis and Hyperglycemic Hyperosmolar State",
        ],
    ),
    "stroke": Protocol(
        title="Acute Stroke Protocol",
        description="Rapid evaluation and management of acute ischemic stroke including tPA and thrombectomy",
        category=ProtocolCategory.EMERGENCY,
        tags=["stroke", "neurology", "tPA", "thrombectomy", "emergency"],
        content=STROKE_PROTOCOL,
        status=ProtocolStatus.PUBLISHED,
        is_template=True,
        version_number="3.1",
        evidence_grade="A",
        references=[
            "Powers WJ, et al. 2018 Guidelines for the Early Management of Patients With Acute Ischemic Stroke",
            "Nogueira RG, et al. Thrombectomy 6 to 24 Hours after Stroke with a Mismatch between Deficit and Infarct",
        ],
    ),
}


def get_template(template_id: str) -> Optional[Protocol]:
    """Get a protocol template by ID."""
    return PROTOCOL_TEMPLATES.get(template_id)


def list_templates(category: Optional[ProtocolCategory] = None) -> List[Protocol]:
    """List all templates, optionally filtered by category."""
    templates = list(PROTOCOL_TEMPLATES.values())

    if category:
        templates = [t for t in templates if t.category == category]

    return templates


def create_from_template(template_id: str, user_id: str, **kwargs) -> Optional[Protocol]:
    """Create a new protocol from a template."""
    template = get_template(template_id)
    if not template:
        return None

    # Create a new protocol based on template
    new_protocol = Protocol(
        title=kwargs.get("title", template.title),
        description=kwargs.get("description", template.description),
        category=kwargs.get("category", template.category),
        tags=kwargs.get("tags", template.tags.copy()),
        content=template.content,
        created_by=user_id,
        organization_id=kwargs.get("organization_id"),
        clinic_id=kwargs.get("clinic_id"),
        status=ProtocolStatus.DRAFT,  # New protocols start as draft
        is_template=False,
        version_number="1.0",
        evidence_grade=template.evidence_grade,
        references=template.references.copy(),
    )

    return new_protocol
