"""EMR Service - Orchestration layer for EMR integration."""

import asyncio
from typing import Optional

from .alerts import ClinicalAlert, ClinicalAlertEngine
from .client import EMRClient, EMRConfig, MockEMRClient
from .context import PatientContextBuilder
from .feedback import FeedbackStore, RecommendationFeedback
from .models import Order, PatientSummary
from .sync import EMRSyncManager


class EMRService:
    """
    EMR Service orchestration layer.

    Provides high-level interface for:
    - Getting patient context for queries
    - Enriching queries with patient data
    - Checking clinical alerts
    - Pushing recommendations back to EMR
    - Managing feedback
    - Handling offline mode
    """

    def __init__(
        self,
        emr_config: Optional[EMRConfig] = None,
        use_mock: bool = False,
        offline_mode: bool = False,
    ):
        """
        Initialize EMR service.

        Args:
            emr_config: EMR API configuration
            use_mock: Use mock EMR client for testing
            offline_mode: Operate in offline mode
        """
        self.offline_mode = offline_mode

        # Initialize EMR client
        if use_mock or offline_mode:
            self.emr_client = MockEMRClient()
        else:
            self.emr_client = EMRClient(emr_config)

        # Initialize components
        self.context_builder = PatientContextBuilder(self.emr_client)
        self.alert_engine = ClinicalAlertEngine()
        self.sync_manager = EMRSyncManager(self.emr_client)
        self.feedback_store = FeedbackStore()

        # Cache for patient summaries (avoid repeated API calls)
        self._patient_cache: dict[int, PatientSummary] = {}

    async def get_patient_context_for_query(
        self,
        patient_id: int,
        query: str,
        use_cache: bool = True,
    ) -> Optional[str]:
        """
        Get patient context optimized for a specific query.

        Args:
            patient_id: Patient ID
            query: User's query
            use_cache: Use cached patient data

        Returns:
            Formatted patient context string or None
        """
        # Check cache first
        if use_cache and patient_id in self._patient_cache:
            summary = self._patient_cache[patient_id]
        else:
            # Pull from EMR
            if not self.offline_mode:
                summary = await self.sync_manager.pull_patient_context(patient_id)
                if summary:
                    self._patient_cache[patient_id] = summary
            else:
                # In offline mode, use cached data only
                summary = self._patient_cache.get(patient_id)

        if not summary:
            return None

        # Build query-relevant context
        context = await self.context_builder.build_context(
            patient_id=patient_id,
            query=query,
            include_full_history=False,
        )

        # Create audit trail
        self.sync_manager.create_audit_trail(
            patient_id=patient_id,
            action="get_patient_context",
            details={"query": query},
        )

        return context

    async def check_clinical_alerts(
        self,
        patient_id: int,
        proposed_medication: Optional[str] = None,
    ) -> list[ClinicalAlert]:
        """
        Check clinical decision support alerts.

        Args:
            patient_id: Patient ID
            proposed_medication: Medication being considered

        Returns:
            List of clinical alerts
        """
        # Get patient summary
        summary = self._patient_cache.get(patient_id)
        if not summary:
            summary = await self.emr_client.get_patient_summary(patient_id)
            if summary:
                self._patient_cache[patient_id] = summary

        if not summary:
            return []

        # Check all alerts
        alerts = self.alert_engine.check_all_alerts(
            patient_summary=summary,
            proposed_medication=proposed_medication,
        )

        # Audit
        self.sync_manager.create_audit_trail(
            patient_id=patient_id,
            action="check_alerts",
            details={
                "alert_count": len(alerts),
                "proposed_medication": proposed_medication,
            },
        )

        return alerts

    async def enrich_query_with_patient_data(
        self,
        patient_id: int,
        query: str,
    ) -> tuple[str, list[ClinicalAlert]]:
        """
        Enrich query with patient context and get alerts.

        Args:
            patient_id: Patient ID
            query: Original query

        Returns:
            Tuple of (enriched_query, alerts)
        """
        # Get patient context
        context = await self.get_patient_context_for_query(
            patient_id=patient_id,
            query=query,
        )

        # Build enriched query
        if context:
            enriched_query = f"{context}\n\nQUERY: {query}"
        else:
            enriched_query = query

        # Get clinical alerts
        alerts = await self.check_clinical_alerts(patient_id)

        return enriched_query, alerts

    async def push_recommendation_to_emr(
        self,
        patient_id: int,
        recommendation: dict,
    ) -> bool:
        """
        Push Dora recommendation back to EMR.

        Args:
            patient_id: Patient ID
            recommendation: Recommendation data

        Returns:
            True if successful
        """
        if self.offline_mode:
            # Queue for later sync
            return await self.sync_manager.push_recommendation(
                patient_id=patient_id,
                recommendation=recommendation,
            )

        success = await self.sync_manager.push_recommendation(
            patient_id=patient_id,
            recommendation=recommendation,
        )

        # Audit
        self.sync_manager.create_audit_trail(
            patient_id=patient_id,
            action="push_recommendation",
            details={
                "success": success,
                "recommendation": recommendation.get("answer", "")[:100],
            },
        )

        return success

    async def create_order(
        self,
        patient_id: int,
        order: Order,
    ) -> Optional[Order]:
        """
        Create clinical order in EMR.

        Args:
            patient_id: Patient ID
            order: Order to create

        Returns:
            Created order or None if failed
        """
        # Check alerts first
        if order.order_type.value == "medication":
            alerts = await self.check_clinical_alerts(
                patient_id=patient_id,
                proposed_medication=order.order_name,
            )

            # Check for critical/fatal alerts
            critical_alerts = [
                a for a in alerts if a.level.value in ["critical", "fatal"]
            ]
            if critical_alerts:
                # Don't create order if critical alerts exist
                return None

        # Create order
        created = await self.sync_manager.push_order(
            patient_id=patient_id,
            order=order,
        )

        # Audit
        self.sync_manager.create_audit_trail(
            patient_id=patient_id,
            action="create_order",
            details={
                "order_type": order.order_type.value,
                "order_name": order.order_name,
                "success": created is not None,
            },
        )

        return created

    async def record_feedback(
        self,
        feedback: RecommendationFeedback,
    ) -> RecommendationFeedback:
        """
        Record feedback on recommendation.

        Args:
            feedback: Feedback data

        Returns:
            Feedback with ID assigned
        """
        saved = self.feedback_store.add_feedback(feedback)

        # Audit
        self.sync_manager.create_audit_trail(
            patient_id=feedback.patient_id,
            action="record_feedback",
            details={
                "feedback_type": feedback.feedback_type.value,
                "outcome": feedback.outcome.value if feedback.outcome else None,
            },
        )

        return saved

    async def sync_offline_queue(self) -> dict[str, int]:
        """
        Sync pending items when coming back online.

        Returns:
            Sync results
        """
        if self.offline_mode:
            return {"error": "Still in offline mode"}

        results = await self.sync_manager.sync_pending_queue()

        # Audit
        self.sync_manager.create_audit_trail(
            patient_id=0,  # System action
            action="sync_offline_queue",
            details=results,
        )

        return results

    def invalidate_patient_cache(self, patient_id: Optional[int] = None):
        """
        Invalidate patient cache.

        Args:
            patient_id: Specific patient ID or None for all
        """
        if patient_id:
            self._patient_cache.pop(patient_id, None)
        else:
            self._patient_cache.clear()

    async def refresh_patient_context(self, patient_id: int) -> bool:
        """
        Force refresh of patient context from EMR.

        Args:
            patient_id: Patient ID

        Returns:
            True if successful
        """
        # Invalidate cache
        self.invalidate_patient_cache(patient_id)

        # Pull fresh data
        summary = await self.sync_manager.pull_patient_context(patient_id)
        if summary:
            self._patient_cache[patient_id] = summary
            return True

        return False

    def get_sync_status(self) -> dict:
        """
        Get current sync status.

        Returns:
            Sync statistics
        """
        return {
            "offline_mode": self.offline_mode,
            "cached_patients": len(self._patient_cache),
            "sync_stats": self.sync_manager.get_sync_stats(),
            "feedback_count": len(self.feedback_store._feedbacks),
        }

    async def get_prescription_context(
        self,
        patient_id: int,
        drug_name: str,
    ) -> tuple[str, list[ClinicalAlert]]:
        """
        Get specialized context for prescription decision.

        Args:
            patient_id: Patient ID
            drug_name: Drug being prescribed

        Returns:
            Tuple of (context, alerts)
        """
        # Get prescription-specific context
        context = await self.context_builder.build_context_for_prescription(
            patient_id=patient_id,
            drug_name=drug_name,
        )

        # Get alerts for this medication
        alerts = await self.check_clinical_alerts(
            patient_id=patient_id,
            proposed_medication=drug_name,
        )

        # Audit
        self.sync_manager.create_audit_trail(
            patient_id=patient_id,
            action="get_prescription_context",
            details={
                "drug_name": drug_name,
                "alert_count": len(alerts),
            },
        )

        return context, alerts

    async def close(self):
        """Clean up resources."""
        if hasattr(self.emr_client, "_client") and self.emr_client._client:
            await self.emr_client._client.aclose()


# Singleton instance
_emr_service_instance: Optional[EMRService] = None


def get_emr_service(
    emr_config: Optional[EMRConfig] = None,
    use_mock: bool = False,
    offline_mode: bool = False,
) -> EMRService:
    """
    Get EMR service singleton instance.

    Args:
        emr_config: EMR API configuration
        use_mock: Use mock EMR client
        offline_mode: Operate in offline mode

    Returns:
        EMR service instance
    """
    global _emr_service_instance

    if _emr_service_instance is None:
        _emr_service_instance = EMRService(
            emr_config=emr_config,
            use_mock=use_mock,
            offline_mode=offline_mode,
        )

    return _emr_service_instance


async def initialize_emr_service(
    emr_config: Optional[EMRConfig] = None,
    use_mock: bool = False,
    offline_mode: bool = False,
) -> EMRService:
    """
    Initialize EMR service.

    Args:
        emr_config: EMR API configuration
        use_mock: Use mock EMR client
        offline_mode: Operate in offline mode

    Returns:
        Initialized EMR service
    """
    service = get_emr_service(
        emr_config=emr_config,
        use_mock=use_mock,
        offline_mode=offline_mode,
    )

    # Perform any async initialization here if needed
    return service
