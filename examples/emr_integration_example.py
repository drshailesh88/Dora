"""
Example: Using EMR Integration for Patient-Contextualized Queries

This demonstrates how to:
1. Connect to EMR
2. Get patient context
3. Check clinical alerts
4. Make patient-specific queries
5. Push recommendations back to EMR
"""

import asyncio

from src.emr import (
    EMRService,
    MockEMRClient,
    Order,
    OrderType,
    RecommendationFeedback,
    FeedbackType,
    OutcomeType,
)


async def example_patient_query():
    """Example: Patient-specific medical query with context."""

    print("=" * 60)
    print("Example 1: Patient-Specific Query with Context")
    print("=" * 60)

    # Initialize EMR service (using mock data for demo)
    emr_service = EMRService(use_mock=True)

    patient_id = 12345  # Mock patient

    # Get patient context for query
    query = "What antibiotic should I prescribe for UTI?"

    print(f"\nOriginal Query: {query}")
    print("\nFetching patient context...")

    context = await emr_service.get_patient_context_for_query(
        patient_id=patient_id,
        query=query,
    )

    print("\n" + context)

    # Check clinical alerts
    print("\nChecking clinical alerts...")
    alerts = await emr_service.check_clinical_alerts(patient_id)

    for alert in alerts:
        print(f"\n{alert.to_display_string()}")


async def example_prescription_safety():
    """Example: Check prescription safety with alerts."""

    print("\n" + "=" * 60)
    print("Example 2: Prescription Safety Check")
    print("=" * 60)

    emr_service = EMRService(use_mock=True)
    patient_id = 12345

    # Check prescription context for specific drug
    drug_name = "Ibuprofen"

    print(f"\nChecking safety for prescribing: {drug_name}")

    context, alerts = await emr_service.get_prescription_context(
        patient_id=patient_id,
        drug_name=drug_name,
    )

    print("\nPrescription Context:")
    print(context)

    print("\nClinical Alerts:")
    if alerts:
        for alert in alerts:
            print(f"\n{alert.to_display_string()}")
    else:
        print("No alerts - safe to prescribe")


async def example_create_order():
    """Example: Create clinical order with safety checks."""

    print("\n" + "=" * 60)
    print("Example 3: Create Clinical Order")
    print("=" * 60)

    emr_service = EMRService(use_mock=True)
    patient_id = 12345

    # Create medication order
    order = Order(
        patient_id=patient_id,
        order_type=OrderType.MEDICATION,
        order_name="Amoxicillin",
        order_details={
            "dosage": "500mg",
            "frequency": "TID",
            "duration": "7 days",
        },
        ordered_by="Dr. Sharma",
    )

    print(f"\nCreating order: {order.order_name}")

    # Check alerts first
    alerts = await emr_service.check_clinical_alerts(
        patient_id=patient_id,
        proposed_medication=order.order_name,
    )

    if any(alert.level.value in ["critical", "fatal"] for alert in alerts):
        print("\n🚨 CRITICAL ALERT - Cannot create order:")
        for alert in alerts:
            if alert.level.value in ["critical", "fatal"]:
                print(f"\n{alert.to_display_string()}")
    else:
        print("\n✓ Safety checks passed")
        created = await emr_service.create_order(patient_id, order)
        if created:
            print(f"✓ Order created successfully (ID: {created.id})")


async def example_feedback_loop():
    """Example: Record feedback on recommendations."""

    print("\n" + "=" * 60)
    print("Example 4: Feedback Loop")
    print("=" * 60)

    emr_service = EMRService(use_mock=True)

    # Record feedback
    feedback = RecommendationFeedback(
        patient_id=12345,
        query="Best antibiotic for UTI in elderly patient with CKD?",
        recommendation="Nitrofurantoin 100mg BID x 5 days",
        recommendation_type="medication",
        confidence_score=0.85,
        feedback_type=FeedbackType.FOLLOWED,
        action_taken="Prescribed nitrofurantoin 100mg BID x 5 days as recommended",
        outcome=OutcomeType.IMPROVED,
        outcome_notes="Symptoms resolved in 3 days, no adverse effects",
    )

    print("\nRecording feedback...")
    saved = await emr_service.record_feedback(feedback)
    print(f"✓ Feedback recorded (ID: {saved.id})")

    # Get analytics
    analytics = emr_service.feedback_store.get_analytics()
    print(f"\nFeedback Analytics:")
    print(f"  Total recommendations: {analytics.total_recommendations}")
    print(f"  Follow rate: {analytics.follow_rate:.1f}%")
    print(f"  Success rate: {analytics.success_rate:.1f}%")
    print(f"  Adverse events: {analytics.adverse_event_count}")


async def example_enriched_query():
    """Example: Enrich query with patient data for RAG."""

    print("\n" + "=" * 60)
    print("Example 5: Enriched Query for RAG Pipeline")
    print("=" * 60)

    emr_service = EMRService(use_mock=True)
    patient_id = 12345

    query = "How should I adjust metformin dose?"

    print(f"\nOriginal Query: {query}")

    # Enrich with patient context
    enriched_query, alerts = await emr_service.enrich_query_with_patient_data(
        patient_id=patient_id,
        query=query,
    )

    print("\nEnriched Query for RAG:")
    print("-" * 60)
    print(enriched_query)
    print("-" * 60)

    if alerts:
        print("\nClinical Alerts:")
        for alert in alerts:
            if "metformin" in alert.message.lower():
                print(f"  {alert.title}")


async def example_sync_status():
    """Example: Check sync status and offline queue."""

    print("\n" + "=" * 60)
    print("Example 6: Sync Status & Offline Queue")
    print("=" * 60)

    emr_service = EMRService(use_mock=True, offline_mode=False)

    # Get sync status
    status = emr_service.get_sync_status()

    print("\nEMR Sync Status:")
    print(f"  Offline mode: {status['offline_mode']}")
    print(f"  Cached patients: {status['cached_patients']}")
    print(f"  Sync stats: {status['sync_stats']}")
    print(f"  Feedback records: {status['feedback_count']}")


async def main():
    """Run all examples."""

    print("\n" + "=" * 60)
    print("Dora EMR Integration Examples")
    print("=" * 60)

    try:
        await example_patient_query()
        await example_prescription_safety()
        await example_create_order()
        await example_feedback_loop()
        await example_enriched_query()
        await example_sync_status()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
