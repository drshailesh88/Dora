"""Voice command handlers for medical operations."""

import logging
from typing import Any, Callable

from .nlu import Intent

logger = logging.getLogger(__name__)


class VoiceCommandResult:
    """Result from executing a voice command."""

    def __init__(
        self,
        success: bool,
        response: str,
        data: Any = None,
        requires_confirmation: bool = False,
        confirmation_prompt: str | None = None,
    ):
        """
        Initialize command result.

        Args:
            success: Whether command executed successfully.
            response: Text response for TTS.
            data: Additional data (for API/UI).
            requires_confirmation: Whether action needs confirmation.
            confirmation_prompt: Confirmation prompt if needed.
        """
        self.success = success
        self.response = response
        self.data = data
        self.requires_confirmation = requires_confirmation
        self.confirmation_prompt = confirmation_prompt


class VoiceCommandHandler:
    """
    Handler for medical voice commands.

    Commands supported:
    - "Check interaction between X and Y"
    - "What's the dose of X for a 70kg adult?"
    - "Calculate GFR for creatinine 1.5"
    - "What are the side effects of X?"
    - "Prescribe X 500mg twice daily"
    - "Generate patient handout for diabetes"
    """

    def __init__(
        self,
        query_pipeline=None,
        drug_service=None,
        calculator_service=None,
        prescription_service=None,
    ):
        """
        Initialize voice command handler.

        Args:
            query_pipeline: Medical query pipeline for knowledge queries.
            drug_service: Drug interaction/info service.
            calculator_service: Medical calculator service.
            prescription_service: Prescription generation service.
        """
        self.query_pipeline = query_pipeline
        self.drug_service = drug_service
        self.calculator_service = calculator_service
        self.prescription_service = prescription_service

        # Map intents to handlers
        self.handlers: dict[str, Callable] = {
            Intent.QUERY: self._handle_query,
            Intent.DRUG_INTERACTION: self._handle_drug_interaction,
            Intent.DOSAGE: self._handle_dosage,
            Intent.SIDE_EFFECTS: self._handle_side_effects,
            Intent.CALCULATOR: self._handle_calculator,
            Intent.PRESCRIPTION: self._handle_prescription,
            Intent.PATIENT_INFO: self._handle_patient_info,
            Intent.HANDOUT: self._handle_handout,
            Intent.GUIDELINE: self._handle_guideline,
            Intent.DIFFERENTIAL: self._handle_differential,
            Intent.HELP: self._handle_help,
        }

        logger.info("Voice command handler initialized")

    def execute(self, nlu_result: dict, context: dict | None = None) -> VoiceCommandResult:
        """
        Execute voice command based on NLU result.

        Args:
            nlu_result: NLU understanding result.
            context: Optional conversation context.

        Returns:
            Command execution result.
        """
        intent = nlu_result.get("intent")
        slots = nlu_result.get("slots", {})

        logger.info(f"Executing command: intent={intent}, slots={slots}")

        # Get handler for intent
        handler = self.handlers.get(intent, self._handle_unknown)

        try:
            return handler(slots, context)
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return VoiceCommandResult(
                success=False,
                response=f"I encountered an error: {str(e)}",
            )

    def _handle_query(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle general medical knowledge query."""
        query = slots.get("query", "")

        if not query:
            return VoiceCommandResult(
                success=False,
                response="I didn't catch your question. Could you repeat that?",
            )

        # Use query pipeline if available
        if self.query_pipeline:
            try:
                answer = self.query_pipeline.query_sync(query)
                return VoiceCommandResult(
                    success=True,
                    response=answer.answer,
                    data={"sources": answer.sources, "confidence": answer.confidence},
                )
            except Exception as e:
                logger.error(f"Query pipeline error: {e}")

        return VoiceCommandResult(
            success=False,
            response="I'm unable to answer that question right now.",
        )

    def _handle_drug_interaction(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle drug interaction check."""
        drug1 = slots.get("drug1")
        drug2 = slots.get("drug2")

        if not drug1 or not drug2:
            return VoiceCommandResult(
                success=False,
                response="Please specify both drugs for interaction check.",
            )

        # Mock response - replace with actual drug interaction service
        response = (
            f"Checking interaction between {drug1} and {drug2}. "
            f"Based on available data, there is a moderate interaction risk. "
            f"{drug1} may increase the blood levels of {drug2}. "
            f"Monitor patient closely and consider dose adjustment."
        )

        return VoiceCommandResult(
            success=True,
            response=response,
            data={
                "drug1": drug1,
                "drug2": drug2,
                "severity": "moderate",
                "recommendation": "Monitor closely",
            },
        )

    def _handle_dosage(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle dosage information request."""
        drug = slots.get("drug")

        if not drug:
            return VoiceCommandResult(
                success=False,
                response="Which medication dosage would you like to know?",
            )

        weight = slots.get("weight")
        age = slots.get("age")

        # Mock response - replace with actual dosage calculator
        if drug.lower() == "paracetamol":
            if weight:
                response = f"For {drug}, the recommended dose is 10-15 mg per kg, every 4-6 hours. For a {weight} patient, that's approximately 500-750 mg per dose, not exceeding 4 grams per day."
            else:
                response = f"For {drug}, the standard adult dose is 500-1000 mg every 4-6 hours, not exceeding 4 grams per day. For pediatric dosing, I need the patient's weight."
        else:
            response = f"For {drug}, the standard adult dose varies by indication. Please refer to specific guidelines or provide more context."

        return VoiceCommandResult(
            success=True,
            response=response,
            data={"drug": drug, "weight": weight, "age": age},
        )

    def _handle_side_effects(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle side effects query."""
        drugs = slots.get("drugs", [])

        if not drugs:
            return VoiceCommandResult(
                success=False,
                response="Which medication's side effects would you like to know?",
            )

        drug = drugs[0] if isinstance(drugs, list) else drugs

        # Mock response - replace with actual drug database
        response = (
            f"Common side effects of {drug} include: nausea, headache, and dizziness. "
            f"Serious but rare side effects include allergic reactions and liver problems. "
            f"Advise patients to report any unusual symptoms immediately."
        )

        return VoiceCommandResult(
            success=True,
            response=response,
            data={"drug": drug, "side_effects": ["nausea", "headache", "dizziness"]},
        )

    def _handle_calculator(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle medical calculator."""
        calculator_type = slots.get("calculator_type")

        if not calculator_type:
            return VoiceCommandResult(
                success=False,
                response="Which calculator would you like to use? GFR, BMI, or others?",
            )

        if calculator_type == "gfr":
            creatinine = slots.get("creatinine")
            age = slots.get("age")

            if not creatinine:
                return VoiceCommandResult(
                    success=False,
                    response="I need the creatinine value to calculate GFR.",
                )

            # Mock GFR calculation (CKD-EPI formula simplified)
            # In production, use actual calculator service
            gfr_value = 90.0  # Mock value

            response = f"The estimated GFR is {gfr_value} mL/min/1.73m². This indicates normal kidney function."

            return VoiceCommandResult(
                success=True,
                response=response,
                data={
                    "calculator": "gfr",
                    "result": gfr_value,
                    "interpretation": "normal",
                },
            )

        elif calculator_type == "bmi":
            response = "For BMI calculation, I need height and weight. Please provide these values."

            return VoiceCommandResult(
                success=False,
                response=response,
            )

        return VoiceCommandResult(
            success=False,
            response=f"Calculator {calculator_type} is not yet available.",
        )

    def _handle_prescription(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle prescription generation (requires confirmation)."""
        drug = slots.get("drug")
        dosage = slots.get("dosage")
        frequency = slots.get("frequency")
        duration = slots.get("duration")

        if not drug:
            return VoiceCommandResult(
                success=False,
                response="Which medication would you like to prescribe?",
            )

        # Build prescription
        prescription_text = f"{drug.title()}"

        if dosage:
            prescription_text += f" {dosage}"

        if frequency:
            prescription_text += f" {frequency}"

        if duration:
            prescription_text += f" for {duration}"

        # Require confirmation for prescription
        confirmation_prompt = f"Would you like me to prescribe: {prescription_text}?"

        return VoiceCommandResult(
            success=True,
            response=confirmation_prompt,
            data={
                "drug": drug,
                "dosage": dosage,
                "frequency": frequency,
                "duration": duration,
                "prescription_text": prescription_text,
            },
            requires_confirmation=True,
            confirmation_prompt=confirmation_prompt,
        )

    def _handle_patient_info(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle patient information request."""
        # Mock response - integrate with EMR system
        response = (
            "Patient information requires authorization. "
            "Please authenticate or use the EMR interface for detailed patient records."
        )

        return VoiceCommandResult(
            success=False,
            response=response,
        )

    def _handle_handout(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle patient education handout generation."""
        condition = slots.get("query", "").replace("handout for", "").strip()

        if not condition:
            return VoiceCommandResult(
                success=False,
                response="Which condition would you like a patient handout for?",
            )

        response = (
            f"I'll generate a patient education handout for {condition}. "
            f"This will be available in the documents section."
        )

        return VoiceCommandResult(
            success=True,
            response=response,
            data={"condition": condition, "action": "generate_handout"},
        )

    def _handle_guideline(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle clinical guideline lookup."""
        query = slots.get("query", "")

        # Mock response - integrate with guideline database
        response = (
            "According to current guidelines, treatment should follow a step-wise approach. "
            "Please refer to the specific guideline documentation for detailed protocols."
        )

        return VoiceCommandResult(
            success=True,
            response=response,
            data={"query": query},
        )

    def _handle_differential(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle differential diagnosis request."""
        query = slots.get("query", "")

        # Mock response - integrate with diagnostic reasoning system
        response = (
            "Based on the symptoms described, common differential diagnoses include: "
            "viral upper respiratory infection, bacterial sinusitis, or allergic rhinitis. "
            "Physical examination and patient history will help narrow the diagnosis."
        )

        return VoiceCommandResult(
            success=True,
            response=response,
            data={"query": query},
        )

    def _handle_help(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle help request."""
        response = (
            "I can help you with: "
            "drug interactions, dosage information, medical calculations, "
            "prescriptions, clinical guidelines, and general medical queries. "
            "Just ask me naturally, like 'What's the dose of aspirin?' or "
            "'Check interaction between warfarin and aspirin'."
        )

        return VoiceCommandResult(
            success=True,
            response=response,
        )

    def _handle_unknown(self, slots: dict, context: dict | None) -> VoiceCommandResult:
        """Handle unknown intent."""
        return VoiceCommandResult(
            success=False,
            response="I'm not sure how to help with that. Could you rephrase or ask for help?",
        )
