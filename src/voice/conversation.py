"""Conversation management for multi-turn voice dialogues."""

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""

    turn_id: str
    timestamp: float
    user_input: str
    nlu_result: dict
    system_response: str
    success: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass
class Conversation:
    """Multi-turn conversation."""

    conversation_id: str
    user_id: str | None
    started_at: float
    last_activity: float
    turns: list[ConversationTurn] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def add_turn(
        self,
        user_input: str,
        nlu_result: dict,
        system_response: str,
        success: bool = True,
        metadata: dict | None = None,
    ) -> ConversationTurn:
        """
        Add a turn to the conversation.

        Args:
            user_input: User's input text.
            nlu_result: NLU understanding result.
            system_response: System's response.
            success: Whether the turn was successful.
            metadata: Additional metadata.

        Returns:
            Created conversation turn.
        """
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            timestamp=time.time(),
            user_input=user_input,
            nlu_result=nlu_result,
            system_response=system_response,
            success=success,
            metadata=metadata or {},
        )

        self.turns.append(turn)
        self.last_activity = time.time()

        # Update context with entities from this turn
        self._update_context(nlu_result)

        return turn

    def _update_context(self, nlu_result: dict):
        """Update conversation context from NLU result."""
        # Track last mentioned entities
        entities = nlu_result.get("entities", {})

        if "drugs" in entities:
            self.context["last_drug"] = entities["drugs"][-1]
            self.context.setdefault("mentioned_drugs", []).extend(entities["drugs"])

        if "dosage" in entities:
            self.context["last_dosage"] = entities["dosage"][-1]

        # Track last intent
        self.context["last_intent"] = nlu_result.get("intent")

        # Track slots
        slots = nlu_result.get("slots", {})
        for key, value in slots.items():
            self.context[f"last_{key}"] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from conversation context."""
        return self.context.get(key, default)

    def set_context(self, key: str, value: Any):
        """Set value in conversation context."""
        self.context[key] = value

    def get_last_turn(self) -> ConversationTurn | None:
        """Get the last conversation turn."""
        return self.turns[-1] if self.turns else None

    def get_turn_count(self) -> int:
        """Get number of turns in conversation."""
        return len(self.turns)

    def is_expired(self, timeout: float = 300.0) -> bool:
        """
        Check if conversation has expired due to inactivity.

        Args:
            timeout: Inactivity timeout in seconds.

        Returns:
            True if expired.
        """
        return (time.time() - self.last_activity) > timeout


class ConversationManager:
    """
    Manager for multi-turn voice conversations.

    Features:
    - Context persistence across turns
    - Clarification requests
    - Confirmation prompts for critical actions
    - Session management
    - Timeout handling
    """

    def __init__(self, session_timeout: float = 300.0):
        """
        Initialize conversation manager.

        Args:
            session_timeout: Conversation timeout in seconds (default 5 min).
        """
        self.session_timeout = session_timeout
        self.conversations: dict[str, Conversation] = {}
        logger.info(f"Conversation manager initialized (timeout={session_timeout}s)")

    def start_conversation(
        self,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        """
        Start a new conversation.

        Args:
            user_id: Optional user identifier.
            metadata: Optional metadata.

        Returns:
            New conversation object.
        """
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            started_at=time.time(),
            last_activity=time.time(),
            metadata=metadata or {},
        )

        self.conversations[conversation_id] = conversation
        logger.info(f"Started conversation {conversation_id}")

        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation identifier.

        Returns:
            Conversation or None if not found/expired.
        """
        conversation = self.conversations.get(conversation_id)

        if conversation and conversation.is_expired(self.session_timeout):
            logger.info(f"Conversation {conversation_id} expired")
            del self.conversations[conversation_id]
            return None

        return conversation

    def add_turn(
        self,
        conversation_id: str,
        user_input: str,
        nlu_result: dict,
        system_response: str,
        success: bool = True,
    ) -> ConversationTurn | None:
        """
        Add a turn to an existing conversation.

        Args:
            conversation_id: Conversation identifier.
            user_input: User's input.
            nlu_result: NLU result.
            system_response: System response.
            success: Whether turn was successful.

        Returns:
            Created turn or None if conversation not found.
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return None

        return conversation.add_turn(
            user_input=user_input,
            nlu_result=nlu_result,
            system_response=system_response,
            success=success,
        )

    def end_conversation(self, conversation_id: str):
        """
        End a conversation.

        Args:
            conversation_id: Conversation identifier.
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Ended conversation {conversation_id}")

    def cleanup_expired(self):
        """Remove all expired conversations."""
        expired = [
            conv_id
            for conv_id, conv in self.conversations.items()
            if conv.is_expired(self.session_timeout)
        ]

        for conv_id in expired:
            del self.conversations[conv_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired conversations")

    def get_active_count(self) -> int:
        """Get number of active conversations."""
        self.cleanup_expired()
        return len(self.conversations)


class ConfirmationManager:
    """
    Manager for confirmation prompts in critical voice actions.

    Used to ensure safety when:
    - Prescribing medications
    - Modifying patient records
    - Sending messages
    """

    def __init__(self):
        """Initialize confirmation manager."""
        self.pending_confirmations: dict[str, dict] = {}

    def request_confirmation(
        self,
        conversation_id: str,
        action: str,
        action_data: dict,
        prompt: str,
    ) -> str:
        """
        Request confirmation for an action.

        Args:
            conversation_id: Conversation identifier.
            action: Action type (e.g., "prescribe", "modify_record").
            action_data: Data needed to execute the action.
            prompt: Confirmation prompt text.

        Returns:
            Confirmation ID.
        """
        confirmation_id = str(uuid.uuid4())

        self.pending_confirmations[confirmation_id] = {
            "conversation_id": conversation_id,
            "action": action,
            "action_data": action_data,
            "prompt": prompt,
            "created_at": time.time(),
        }

        logger.info(f"Confirmation requested: {confirmation_id} for action {action}")

        return confirmation_id

    def process_confirmation(
        self,
        confirmation_id: str,
        confirmed: bool,
    ) -> dict | None:
        """
        Process a confirmation response.

        Args:
            confirmation_id: Confirmation identifier.
            confirmed: Whether user confirmed.

        Returns:
            Action data if confirmed, None if rejected/not found.
        """
        confirmation = self.pending_confirmations.get(confirmation_id)

        if not confirmation:
            logger.warning(f"Confirmation {confirmation_id} not found")
            return None

        # Remove from pending
        del self.pending_confirmations[confirmation_id]

        if confirmed:
            logger.info(f"Action {confirmation['action']} confirmed")
            return confirmation["action_data"]
        else:
            logger.info(f"Action {confirmation['action']} rejected")
            return None

    def cleanup_expired(self, timeout: float = 60.0):
        """
        Remove expired confirmations.

        Args:
            timeout: Confirmation timeout in seconds.
        """
        now = time.time()
        expired = [
            conf_id
            for conf_id, conf in self.pending_confirmations.items()
            if (now - conf["created_at"]) > timeout
        ]

        for conf_id in expired:
            del self.pending_confirmations[conf_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired confirmations")


class ClarificationHandler:
    """
    Handler for clarification requests when NLU confidence is low.

    Generates appropriate clarification questions based on:
    - Missing slots
    - Low confidence
    - Ambiguous entities
    """

    CLARIFICATION_TEMPLATES = {
        "low_confidence": [
            "I didn't quite understand that. Could you rephrase?",
            "I'm not sure I understood. Could you say that differently?",
        ],
        "missing_drug": [
            "Which medication are you asking about?",
            "What drug would you like to know about?",
        ],
        "missing_dosage": [
            "What dosage of {drug}?",
            "How much {drug} should be prescribed?",
        ],
        "missing_frequency": [
            "How often should {drug} be taken?",
            "What's the frequency for {drug}?",
        ],
        "ambiguous_drug": [
            "Did you mean {option1} or {option2}?",
            "I found multiple matches. Did you mean {options}?",
        ],
    }

    def get_clarification(
        self,
        nlu_result: dict,
        context: dict | None = None,
    ) -> str | None:
        """
        Get clarification question if needed.

        Args:
            nlu_result: NLU understanding result.
            context: Conversation context.

        Returns:
            Clarification question or None.
        """
        intent = nlu_result.get("intent")
        slots = nlu_result.get("slots", {})
        confidence = nlu_result.get("confidence", 0.0)

        # Low confidence
        if confidence < 0.6:
            return self.CLARIFICATION_TEMPLATES["low_confidence"][0]

        # Intent-specific clarifications
        if intent == "drug_interaction":
            if "drug1" not in slots:
                return self.CLARIFICATION_TEMPLATES["missing_drug"][0]
            if "drug2" not in slots:
                drug1 = slots["drug1"]
                return f"What drug would you like to check interaction with {drug1}?"

        elif intent == "dosage":
            if "drug" not in slots:
                return self.CLARIFICATION_TEMPLATES["missing_drug"][0]

        elif intent == "prescription":
            if "drug" not in slots:
                return self.CLARIFICATION_TEMPLATES["missing_drug"][0]
            drug = slots.get("drug")
            if "dosage" not in slots:
                return self.CLARIFICATION_TEMPLATES["missing_dosage"][0].format(drug=drug)
            if "frequency" not in slots:
                return self.CLARIFICATION_TEMPLATES["missing_frequency"][0].format(drug=drug)

        return None
