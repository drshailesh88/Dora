"""Natural Language Understanding for medical voice queries."""

import logging
import re
from typing import Literal

logger = logging.getLogger(__name__)


class Intent:
    """Voice query intent."""

    QUERY = "query"  # Medical knowledge query
    DRUG_INTERACTION = "drug_interaction"  # Check drug interactions
    DOSAGE = "dosage"  # Get dosage information
    SIDE_EFFECTS = "side_effects"  # Get side effects
    CALCULATOR = "calculator"  # Medical calculator
    PRESCRIPTION = "prescription"  # Create prescription
    PATIENT_INFO = "patient_info"  # Get patient information
    HANDOUT = "handout"  # Generate patient handout
    GUIDELINE = "guideline"  # Look up clinical guideline
    DIFFERENTIAL = "differential"  # Differential diagnosis
    HELP = "help"  # Help/usage information
    UNKNOWN = "unknown"  # Couldn't determine intent


class NaturalLanguageUnderstanding:
    """
    Natural Language Understanding for medical voice queries.

    Features:
    - Intent classification (query, prescription, calculator, etc.)
    - Medical entity extraction (drugs, dosages, patient info)
    - Slot filling for complex queries
    - Context-aware understanding
    """

    def __init__(self):
        """Initialize NLU."""
        # Intent patterns (keywords that trigger specific intents)
        self.intent_patterns = {
            Intent.DRUG_INTERACTION: [
                r"interact(?:ion)?",
                r"combine",
                r"together",
                r"drug.*drug",
                r"safe.*with",
            ],
            Intent.DOSAGE: [
                r"dose|dosage",
                r"how much",
                r"mg|gram|ml",
                r"twice|thrice",
                r"daily",
            ],
            Intent.SIDE_EFFECTS: [
                r"side effect",
                r"adverse",
                r"reaction",
                r"contraindication",
            ],
            Intent.CALCULATOR: [
                r"calculat",
                r"gfr|egfr",
                r"bmi",
                r"creatinine clearance",
                r"apache",
                r"sofa",
            ],
            Intent.PRESCRIPTION: [
                r"prescribe",
                r"write.*prescription",
                r"rx",
                r"give.*medicine",
            ],
            Intent.PATIENT_INFO: [
                r"patient.*info",
                r"medical.*record",
                r"history",
                r"previous.*visit",
            ],
            Intent.HANDOUT: [
                r"handout",
                r"patient.*education",
                r"explain.*patient",
                r"discharge.*instruction",
            ],
            Intent.GUIDELINE: [
                r"guideline",
                r"protocol",
                r"recommendation",
                r"standard.*care",
            ],
            Intent.DIFFERENTIAL: [
                r"differential",
                r"diagnosis.*for",
                r"could.*be",
                r"rule out",
            ],
            Intent.HELP: [
                r"help",
                r"how.*use",
                r"what.*can.*do",
            ],
        }

        # Medical entity patterns
        self.entity_patterns = {
            "drug": r"\b(?:metformin|aspirin|atorvastatin|amlodipine|omeprazole|paracetamol|ibuprofen)\b",
            "dosage": r"\b\d+\s*(?:mg|g|ml|mcg|units?)\b",
            "frequency": r"\b(?:once|twice|thrice|daily|weekly|monthly|bd|tds|qds)\b",
            "duration": r"\b(?:\d+\s*(?:days?|weeks?|months?))\b",
            "route": r"\b(?:oral|iv|im|sc|topical)\b",
            "age": r"\b\d+\s*(?:year|yr|month|mo)\s*old\b",
            "weight": r"\b\d+\s*(?:kg|pound|lb)\b",
            "lab_value": r"\b(?:creatinine|urea|hemoglobin|hb)\s*[:=]?\s*\d+\.?\d*\b",
        }

        logger.info("NLU initialized")

    def understand(self, text: str, context: dict | None = None) -> dict:
        """
        Understand natural language query.

        Args:
            text: Query text.
            context: Optional conversation context.

        Returns:
            Dict with intent, entities, and slots.
        """
        text_lower = text.lower()

        # Classify intent
        intent = self._classify_intent(text_lower)

        # Extract entities
        entities = self._extract_entities(text)

        # Fill slots based on intent
        slots = self._fill_slots(intent, text_lower, entities, context)

        # Calculate confidence
        confidence = self._calculate_confidence(intent, entities, slots)

        result = {
            "intent": intent,
            "entities": entities,
            "slots": slots,
            "confidence": confidence,
            "original_text": text,
        }

        logger.info(f"NLU result: intent={intent}, confidence={confidence:.2f}")

        return result

    def _classify_intent(self, text: str) -> str:
        """
        Classify intent from text.

        Args:
            text: Query text (lowercase).

        Returns:
            Intent string.
        """
        # Check each intent pattern
        scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            scores[intent] = score

        # Get intent with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        # Default to general query
        return Intent.QUERY

    def _extract_entities(self, text: str) -> dict:
        """
        Extract medical entities from text.

        Args:
            text: Query text.

        Returns:
            Dict of entity types to values.
        """
        entities = {}

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches

        # Extract drug names using more sophisticated matching
        drugs = self._extract_drug_names(text)
        if drugs:
            entities["drugs"] = drugs

        return entities

    def _extract_drug_names(self, text: str) -> list[str]:
        """
        Extract drug names from text.

        Args:
            text: Query text.

        Returns:
            List of drug names.
        """
        # Common drug names (can be expanded or loaded from DB)
        common_drugs = [
            "metformin", "aspirin", "atorvastatin", "amlodipine", "omeprazole",
            "paracetamol", "ibuprofen", "amoxicillin", "azithromycin",
            "lisinopril", "losartan", "warfarin", "clopidogrel", "insulin",
            "levothyroxine", "prednisone", "dexamethasone", "furosemide",
        ]

        found_drugs = []
        text_lower = text.lower()

        for drug in common_drugs:
            if drug in text_lower:
                found_drugs.append(drug)

        return found_drugs

    def _fill_slots(
        self,
        intent: str,
        text: str,
        entities: dict,
        context: dict | None,
    ) -> dict:
        """
        Fill slots for the given intent.

        Args:
            intent: Classified intent.
            text: Query text.
            entities: Extracted entities.
            context: Conversation context.

        Returns:
            Dict of filled slots.
        """
        slots = {}

        if intent == Intent.DRUG_INTERACTION:
            # Need at least 2 drugs
            drugs = entities.get("drugs", [])
            if len(drugs) >= 2:
                slots["drug1"] = drugs[0]
                slots["drug2"] = drugs[1]
            elif len(drugs) == 1 and context:
                # Try to get second drug from context
                slots["drug1"] = drugs[0]
                slots["drug2"] = context.get("last_drug")

        elif intent == Intent.DOSAGE:
            # Need drug and optionally patient info
            drugs = entities.get("drugs", [])
            if drugs:
                slots["drug"] = drugs[0]

            if "weight" in entities:
                slots["weight"] = entities["weight"][0]

            if "age" in entities:
                slots["age"] = entities["age"][0]

        elif intent == Intent.PRESCRIPTION:
            # Need drug, dosage, frequency, duration
            drugs = entities.get("drugs", [])
            if drugs:
                slots["drug"] = drugs[0]

            if "dosage" in entities:
                slots["dosage"] = entities["dosage"][0]

            if "frequency" in entities:
                slots["frequency"] = entities["frequency"][0]

            if "duration" in entities:
                slots["duration"] = entities["duration"][0]

            if "route" in entities:
                slots["route"] = entities["route"][0]

        elif intent == Intent.CALCULATOR:
            # Detect which calculator
            if "gfr" in text or "egfr" in text:
                slots["calculator_type"] = "gfr"

                # Extract creatinine
                if "lab_value" in entities:
                    for lab in entities["lab_value"]:
                        if "creatinine" in lab.lower():
                            # Extract numeric value
                            match = re.search(r"\d+\.?\d*", lab)
                            if match:
                                slots["creatinine"] = float(match.group())

                if "age" in entities:
                    slots["age"] = entities["age"][0]

            elif "bmi" in text:
                slots["calculator_type"] = "bmi"

        elif intent == Intent.QUERY:
            # General query - extract key terms
            slots["query"] = text

        return slots

    def _calculate_confidence(
        self,
        intent: str,
        entities: dict,
        slots: dict,
    ) -> float:
        """
        Calculate confidence score for NLU result.

        Args:
            intent: Classified intent.
            entities: Extracted entities.
            slots: Filled slots.

        Returns:
            Confidence score (0-1).
        """
        confidence = 0.5  # Base confidence

        # Increase confidence if we found entities
        if entities:
            confidence += 0.2

        # Increase confidence if slots are well-filled
        if intent == Intent.DRUG_INTERACTION:
            if "drug1" in slots and "drug2" in slots:
                confidence += 0.3

        elif intent == Intent.DOSAGE:
            if "drug" in slots:
                confidence += 0.3

        elif intent == Intent.PRESCRIPTION:
            required_slots = ["drug", "dosage", "frequency"]
            filled = sum(1 for slot in required_slots if slot in slots)
            confidence += (filled / len(required_slots)) * 0.3

        # Cap at 1.0
        return min(confidence, 1.0)

    def needs_clarification(self, nlu_result: dict) -> tuple[bool, str | None]:
        """
        Check if the NLU result needs clarification.

        Args:
            nlu_result: Result from understand().

        Returns:
            Tuple of (needs_clarification, clarification_question).
        """
        intent = nlu_result["intent"]
        slots = nlu_result["slots"]
        confidence = nlu_result["confidence"]

        # Low confidence
        if confidence < 0.6:
            return True, "I didn't quite understand that. Could you rephrase?"

        # Check intent-specific requirements
        if intent == Intent.DRUG_INTERACTION:
            if "drug1" not in slots:
                return True, "Which drug would you like to check?"
            if "drug2" not in slots:
                return True, f"What drug would you like to check interaction with {slots['drug1']}?"

        elif intent == Intent.DOSAGE:
            if "drug" not in slots:
                return True, "Which medication dosage would you like to know?"

        elif intent == Intent.PRESCRIPTION:
            if "drug" not in slots:
                return True, "Which medication would you like to prescribe?"
            if "dosage" not in slots:
                return True, f"What dosage of {slots['drug']}?"
            if "frequency" not in slots:
                return True, f"How often should {slots['drug']} be taken?"

        elif intent == Intent.CALCULATOR:
            if "calculator_type" not in slots:
                return True, "Which calculator would you like to use? (GFR, BMI, etc.)"

        # No clarification needed
        return False, None


class MedicalNER:
    """
    Medical Named Entity Recognition.

    Extracts medical entities using pattern matching and dictionary lookup.
    Can be enhanced with ML models later.
    """

    def __init__(self):
        """Initialize medical NER."""
        # Entity categories
        self.entity_types = {
            "DRUG": [],
            "DISEASE": [],
            "SYMPTOM": [],
            "LAB_TEST": [],
            "PROCEDURE": [],
        }

        # Load entity dictionaries (simplified)
        self._load_dictionaries()

    def _load_dictionaries(self):
        """Load medical entity dictionaries."""
        # Simplified - in production, load from comprehensive medical databases
        self.entity_types["DRUG"] = [
            "metformin", "aspirin", "atorvastatin", "amlodipine", "omeprazole",
            "paracetamol", "ibuprofen", "amoxicillin", "azithromycin",
        ]

        self.entity_types["DISEASE"] = [
            "diabetes", "hypertension", "asthma", "tuberculosis", "pneumonia",
            "dengue", "malaria", "typhoid", "covid-19", "influenza",
        ]

        self.entity_types["SYMPTOM"] = [
            "fever", "cough", "headache", "nausea", "vomiting", "diarrhea",
            "pain", "fatigue", "dizziness", "shortness of breath",
        ]

        self.entity_types["LAB_TEST"] = [
            "cbc", "blood sugar", "hba1c", "creatinine", "urea", "liver function",
            "lipid profile", "ecg", "chest x-ray", "ultrasound",
        ]

        self.entity_types["PROCEDURE"] = [
            "surgery", "endoscopy", "colonoscopy", "biopsy", "catheterization",
            "intubation", "dialysis",
        ]

    def extract(self, text: str) -> list[dict]:
        """
        Extract medical entities from text.

        Args:
            text: Input text.

        Returns:
            List of extracted entities with type and span.
        """
        entities = []
        text_lower = text.lower()

        for entity_type, entity_list in self.entity_types.items():
            for entity in entity_list:
                # Find all occurrences
                pattern = r"\b" + re.escape(entity) + r"\b"
                for match in re.finditer(pattern, text_lower):
                    entities.append({
                        "text": text[match.start():match.end()],
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                    })

        # Sort by position
        entities.sort(key=lambda x: x["start"])

        return entities
