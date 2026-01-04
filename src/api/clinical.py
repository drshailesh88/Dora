"""
FastAPI Clinical Decision Support API Endpoints

Exposes all clinical modules via REST API.

MEDICAL DISCLAIMER:
All endpoints are for clinical decision support only.
Verify all recommendations with current evidence and clinical judgment.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from clinical.differential import generate_differential_diagnosis
from clinical.lab_interpreter import interpret_labs
from clinical.dosing import get_dosing_recommendation
from clinical.protocols import get_treatment_protocol
from clinical.antibiotics import get_antibiotic_recommendation
from clinical.risk import calculate_risk_score
from clinical.alerts import check_clinical_alerts


# Create router
router = APIRouter(prefix="/api/v1/clinical", tags=["clinical"])


# ==================== REQUEST/RESPONSE MODELS ====================

class DifferentialRequest(BaseModel):
    chief_complaint: str = Field(..., description="Primary symptom or complaint")
    symptoms: List[str] = Field(default=[], description="Associated symptoms")
    age: int = Field(..., ge=0, le=120, description="Patient age")
    gender: str = Field(..., pattern="^(M|F|Other)$", description="Patient gender")
    duration: Optional[str] = Field(None, description="Duration of symptoms")
    onset: Optional[str] = Field(None, description="Onset (sudden/gradual)")
    severity_score: Optional[int] = Field(None, ge=1, le=10, description="Severity 1-10")
    past_medical_history: List[str] = Field(default=[], description="PMH")
    medications: List[str] = Field(default=[], description="Current medications")
    vital_signs: Dict[str, float] = Field(default={}, description="Vital signs")


class LabInterpretationRequest(BaseModel):
    panel_type: str = Field(..., description="Panel type (cbc, cmp, lft, thyroid, abg)")
    lab_values: Dict[str, float] = Field(..., description="Lab values dict")
    gender: Optional[str] = Field("M", pattern="^(M|F)$")
    age: Optional[int] = Field(40, ge=0, le=120)


class DosingRequest(BaseModel):
    drug_name: str = Field(..., description="Drug name")
    indication: str = Field(..., description="Clinical indication")
    patient_data: Dict[str, Any] = Field(..., description="Patient parameters (weight, age, etc.)")


class ProtocolRequest(BaseModel):
    condition: str = Field(..., description="Medical condition")


class AntibioticRequest(BaseModel):
    infection_type: str = Field(..., description="Type of infection")
    severity: str = Field(default="moderate", pattern="^(mild|moderate|severe|life_threatening)$")
    patient_factors: Optional[Dict] = Field(default={})


class RiskScoreRequest(BaseModel):
    score_name: str = Field(..., description="Risk score name (ascvd, chads_vasc, etc.)")
    parameters: Dict[str, Any] = Field(..., description="Score-specific parameters")


class AlertRequest(BaseModel):
    alert_type: str = Field(..., description="Alert type (critical_lab, drug_allergy, etc.)")
    parameters: Dict[str, Any] = Field(..., description="Alert-specific parameters")


# ==================== API ENDPOINTS ====================

@router.post("/differential", summary="Generate differential diagnosis")
async def differential_diagnosis(request: DifferentialRequest):
    """
    Generate differential diagnosis based on clinical presentation.

    ## Parameters:
    - **chief_complaint**: Primary symptom (e.g., "chest pain")
    - **symptoms**: List of associated symptoms
    - **age**, **gender**: Patient demographics
    - **past_medical_history**: Relevant medical conditions
    - **vital_signs**: Dict with temp, hr, bp, rr, etc.

    ## Returns:
    List of differential diagnoses with probabilities and workup recommendations.

    ## Example:
    ```json
    {
      "chief_complaint": "chest pain",
      "symptoms": ["radiation to arm", "diaphoresis", "nausea"],
      "age": 65,
      "gender": "M",
      "past_medical_history": ["diabetes", "hypertension"],
      "vital_signs": {"hr": 95, "bp_systolic": 150}
    }
    ```
    """
    try:
        differentials = generate_differential_diagnosis(
            chief_complaint=request.chief_complaint,
            symptoms=request.symptoms,
            age=request.age,
            gender=request.gender,
            duration=request.duration,
            onset=request.onset,
            severity_score=request.severity_score,
            past_medical_history=request.past_medical_history,
            medications=request.medications,
            vital_signs=request.vital_signs
        )
        return {
            "status": "success",
            "differentials": differentials,
            "count": len(differentials)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interpret-labs", summary="Interpret laboratory results")
async def interpret_laboratory_results(request: LabInterpretationRequest):
    """
    Interpret laboratory panel results with clinical correlation.

    ## Supported Panels:
    - **cbc**: Complete Blood Count
    - **cmp/bmp**: Comprehensive/Basic Metabolic Panel
    - **lft**: Liver Function Tests
    - **thyroid**: Thyroid function (TSH, Free T4)
    - **abg**: Arterial Blood Gas

    ## Returns:
    Clinical interpretations with possible causes and recommended actions.

    ## Example:
    ```json
    {
      "panel_type": "cbc",
      "lab_values": {
        "wbc": 15.2,
        "hemoglobin": 9.5,
        "platelet": 450
      },
      "gender": "F",
      "age": 35
    }
    ```
    """
    try:
        interpretations = interpret_labs(
            panel_type=request.panel_type,
            lab_values=request.lab_values,
            gender=request.gender,
            age=request.age
        )
        return {
            "status": "success",
            "panel_type": request.panel_type,
            "interpretations": interpretations,
            "count": len(interpretations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dosing", summary="Get drug dosing recommendation")
async def drug_dosing_recommendation(request: DosingRequest):
    """
    Get evidence-based drug dosing with renal/hepatic adjustments.

    ## Supported Drugs:
    - Vancomycin (with renal dosing)
    - Gentamicin (extended-interval)
    - Warfarin
    - Heparin, Enoxaparin
    - Digoxin
    - Phenytoin

    ## Patient Data Required (varies by drug):
    - weight_kg, height_cm, age, gender
    - serum_cr (or crcl)
    - albumin (for phenytoin)

    ## Returns:
    Dosing recommendation with adjustments, monitoring, and warnings.

    ## Example:
    ```json
    {
      "drug_name": "vancomycin",
      "indication": "MRSA pneumonia",
      "patient_data": {
        "weight_kg": 70,
        "age": 65,
        "gender": "M",
        "serum_cr": 1.2
      }
    }
    ```
    """
    try:
        recommendation = get_dosing_recommendation(
            drug_name=request.drug_name,
            indication=request.indication,
            patient_data=request.patient_data
        )

        if 'error' in recommendation:
            raise HTTPException(status_code=400, detail=recommendation['error'])

        return {
            "status": "success",
            "recommendation": recommendation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/protocols/{condition}", summary="Get treatment protocol")
async def treatment_protocol(condition: str):
    """
    Get evidence-based treatment protocol for medical condition.

    ## Supported Conditions:
    - hypertension (or htn)
    - diabetes_type2 (or dm)
    - heart_failure (or chf, hfref)
    - copd
    - pneumonia_cap (or cap, pneumonia)
    - uti
    - acs_nstemi (or nstemi)
    - stroke_ischemic (or stroke)
    - sepsis
    - dka

    ## Returns:
    Step-by-step treatment protocol with medications, non-pharm, monitoring.

    ## Example:
    `/api/v1/clinical/protocols/hypertension`
    """
    try:
        protocol = get_treatment_protocol(condition)

        if not protocol:
            raise HTTPException(
                status_code=404,
                detail=f"Protocol not found for condition: {condition}"
            )

        return {
            "status": "success",
            "protocol": protocol
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/antibiotics", summary="Get antibiotic recommendations")
async def antibiotic_recommendation(request: AntibioticRequest):
    """
    Get antibiotic stewardship recommendations for infections.

    ## Supported Infections:
    - skin_cellulitis (or cellulitis, ssti)
    - diabetic_foot
    - cap (pneumonia)
    - hap_vap
    - uti_simple (or uti)
    - pyelonephritis
    - intra_abdominal
    - meningitis
    - sepsis_unknown

    ## Severity Levels:
    - mild
    - moderate
    - severe
    - life_threatening

    ## Returns:
    Empiric therapy, alternatives, duration, de-escalation strategy.

    ## Example:
    ```json
    {
      "infection_type": "cellulitis",
      "severity": "moderate"
    }
    ```
    """
    try:
        recommendation = get_antibiotic_recommendation(
            infection_type=request.infection_type,
            severity=request.severity,
            **request.patient_factors
        )

        if not recommendation:
            raise HTTPException(
                status_code=404,
                detail=f"Antibiotic recommendation not found for: {request.infection_type}"
            )

        return {
            "status": "success",
            "recommendation": recommendation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk-score", summary="Calculate clinical risk score")
async def risk_score_calculation(request: RiskScoreRequest):
    """
    Calculate clinical risk scores with interpretation and recommendations.

    ## Supported Scores:
    - **ascvd**: 10-year cardiovascular risk
    - **chads_vasc**: Stroke risk in AFib
    - **has_bled**: Bleeding risk on anticoagulation
    - **wells_dvt**: DVT probability
    - **curb65**: Pneumonia severity
    - **heart**: Chest pain risk stratification
    - **meld**: Liver disease severity

    ## Returns:
    Score value, risk level, interpretation, and recommendations.

    ## Example (CHADS-VASc):
    ```json
    {
      "score_name": "chads_vasc",
      "parameters": {
        "age": 75,
        "gender": "M",
        "chf": true,
        "hypertension": true,
        "stroke_tia": false,
        "vascular_disease": true,
        "diabetes": false
      }
    }
    ```
    """
    try:
        result = calculate_risk_score(
            score_name=request.score_name,
            **request.parameters
        )

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        return {
            "status": "success",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts", summary="Check clinical alerts")
async def clinical_alerts(request: AlertRequest):
    """
    Check for clinical decision support alerts.

    ## Alert Types:
    - **critical_lab**: Critical lab values
    - **drug_allergy**: Drug allergy checking
    - **drug_interaction**: Drug-drug interactions
    - **dose_limit**: Dose limit violations
    - **contraindication**: Contraindications

    ## Returns:
    List of alerts with severity, recommendations, and override requirements.

    ## Example (Critical Lab):
    ```json
    {
      "alert_type": "critical_lab",
      "parameters": {
        "lab_name": "potassium",
        "value": 6.5
      }
    }
    ```

    ## Example (Drug Allergy):
    ```json
    {
      "alert_type": "drug_allergy",
      "parameters": {
        "drug_ordered": "amoxicillin",
        "known_allergies": ["penicillin"]
      }
    }
    ```
    """
    try:
        alerts = check_clinical_alerts(
            alert_type=request.alert_type,
            **request.parameters
        )

        return {
            "status": "success",
            "alerts": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health", summary="API health check")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Clinical Decision Support API",
        "version": "1.0.0",
        "modules": [
            "differential_diagnosis",
            "lab_interpretation",
            "drug_dosing",
            "treatment_protocols",
            "antibiotic_stewardship",
            "risk_stratification",
            "clinical_alerts"
        ]
    }


# ==================== MAIN APP (for standalone testing) ====================

if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(
        title="Dora Clinical Decision Support API",
        description="Comprehensive clinical decision support system",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=8000)
