"""Demo script for personalization module."""

import asyncio
from datetime import datetime

from src.personalization import (
    DoctorProfile,
    MedicalSpecialty,
    PersonalizationStorage,
    PersonalizedRecommender,
    PracticeSetting,
    ProfileLearner,
    QueryHistory,
    SpecialtyDetector,
)


def demo_specialty_detection():
    """Demonstrate specialty detection from queries."""
    print("\n" + "=" * 60)
    print("SPECIALTY DETECTION DEMO")
    print("=" * 60)

    detector = SpecialtyDetector()

    # Test queries
    test_queries = [
        "What is the management of atrial fibrillation with RVR?",
        "How to treat acute exacerbation of COPD?",
        "Management of diabetic ketoacidosis in adults",
        "Treatment options for major depressive disorder",
        "Diagnosis and management of acute appendicitis",
        "Pediatric vaccine schedule for 6-month-old",
    ]

    for query in test_queries:
        result = detector.detect_from_query(query)
        if result:
            specialty, confidence = result
            print(f"\nQuery: {query}")
            print(f"  → Detected: {specialty.value}")
            print(f"  → Confidence: {confidence:.2%}")

            # Extract entities
            entities = detector.extract_entities(query)
            if entities["drugs"]:
                print(f"  → Drugs mentioned: {', '.join(entities['drugs'])}")
            if entities["conditions"]:
                print(f"  → Conditions: {', '.join(entities['conditions'])}")


def demo_profile_learning():
    """Demonstrate profile learning from query history."""
    print("\n" + "=" * 60)
    print("PROFILE LEARNING DEMO")
    print("=" * 60)

    storage = PersonalizationStorage()
    learner = ProfileLearner()
    detector = SpecialtyDetector()

    # Create test user
    user_id = "demo_doctor_001"

    # Simulate cardiology queries
    cardiology_queries = [
        "Management of acute STEMI",
        "Heart failure with reduced ejection fraction treatment",
        "Atrial fibrillation anticoagulation guidelines",
        "Hypertrophic cardiomyopathy management",
        "Beta blocker selection in heart failure",
        "ACE inhibitor vs ARB in hypertension",
        "Statin therapy for primary prevention",
        "Echocardiogram interpretation basics",
        "Cardiac catheterization indications",
        "Antiplatelet therapy in ACS",
    ]

    # Create query history
    history = []
    for i, query in enumerate(cardiology_queries):
        detection = detector.detect_from_query(query)
        entities = detector.extract_entities(query)

        record = QueryHistory(
            user_id=user_id,
            query=query,
            detected_specialty=detection[0] if detection else None,
            specialty_confidence=detection[1] if detection else 0.0,
            mentioned_drugs=entities.get("drugs", []),
            mentioned_conditions=entities.get("conditions", []),
        )
        history.append(record)

    # Learn from history
    profile = DoctorProfile(user_id=user_id)
    profile = learner.learn_from_history(profile, history)

    print(f"\nProfile after {len(history)} queries:")
    print(f"  Total queries: {profile.total_queries}")
    print(f"\n  Detected specialties:")
    for spec_conf in profile.detected_specialties[:3]:
        print(f"    • {spec_conf.specialty.value}: {spec_conf.confidence:.2%} "
              f"({spec_conf.evidence_count} queries)")

    if profile.common_conditions:
        print(f"\n  Common conditions: {', '.join(profile.common_conditions[:5])}")

    # Get insights
    pattern = learner.compute_query_patterns(history)
    insights = learner.get_learning_insights(profile, pattern)

    print(f"\n  Learning Insights:")
    print(f"    • Top specialty: {insights['top_specialty']}")
    print(f"    • Confidence: {insights['confidence']:.2%}")
    print(f"    • Specialties detected: {insights['specialties_detected']}")


def demo_recommendations():
    """Demonstrate personalized recommendations."""
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS DEMO")
    print("=" * 60)

    recommender = PersonalizedRecommender()

    # Create a cardiologist profile
    profile = DoctorProfile(
        user_id="demo_cardiologist",
        primary_specialty=MedicalSpecialty.CARDIOLOGY,
        years_of_experience=8,
        practice_settings=[PracticeSetting.HOSPITAL, PracticeSetting.CLINIC],
    )

    # Get guidelines
    print("\n📋 Recommended Guidelines:")
    guidelines = recommender.recommend_guidelines(profile)
    for i, guideline in enumerate(guidelines[:3], 1):
        print(f"  {i}. {guideline['title']}")
        print(f"     {guideline['organization']} ({guideline['year']})")

    # Get calculators
    print("\n🧮 Recommended Calculators:")
    calculators = recommender.recommend_calculators(
        profile,
        query="patient with atrial fibrillation"
    )
    for i, calc in enumerate(calculators[:3], 1):
        print(f"  {i}. {calc['name']}")
        print(f"     {calc['description']}")

    # Get reading recommendations
    print("\n📚 Recommended Reading:")
    reading = recommender.recommend_reading(profile)
    for i, book in enumerate(reading[:3], 1):
        print(f"  {i}. {book['title']}")
        print(f"     {book['edition']} Edition")


def demo_full_workflow():
    """Demonstrate full personalization workflow."""
    print("\n" + "=" * 60)
    print("FULL WORKFLOW DEMO")
    print("=" * 60)

    storage = PersonalizationStorage()
    detector = SpecialtyDetector()
    learner = ProfileLearner()

    user_id = "demo_doctor_full"

    # Simulate a doctor's first queries (unknown specialty)
    print("\n1. Initial queries (no profile yet):")

    initial_queries = [
        "Treatment of community acquired pneumonia",
        "Management of acute asthma exacerbation",
        "COPD staging and treatment",
    ]

    for query in initial_queries:
        print(f"  • {query}")
        detection = detector.detect_from_query(query)
        if detection:
            print(f"    → Detected: {detection[0].value} ({detection[1]:.0%})")

    # Create profile
    profile = DoctorProfile(user_id=user_id)

    # Track queries
    history = []
    for query in initial_queries:
        detection = detector.detect_from_query(query)
        entities = detector.extract_entities(query)

        record = QueryHistory(
            user_id=user_id,
            query=query,
            detected_specialty=detection[0] if detection else None,
            specialty_confidence=detection[1] if detection else 0.0,
            mentioned_drugs=entities.get("drugs", []),
            mentioned_conditions=entities.get("conditions", []),
        )
        history.append(record)
        storage.save_query_history(record)

    # Update profile
    profile = learner.learn_from_history(profile, history)
    storage.save_profile(profile)

    print(f"\n2. Profile after initial queries:")
    top_specialty = profile.get_top_specialty()
    if top_specialty:
        print(f"  • Detected specialty: {top_specialty.value}")
        top_conf = profile.detected_specialties[0]
        print(f"  • Confidence: {top_conf.confidence:.2%}")

    # Simulate feedback
    print(f"\n3. User provides feedback on first query:")
    print(f"  • Rating: 5/5 (helpful)")

    profile = learner.update_from_feedback(
        profile,
        history[0],
        feedback_rating=5,
    )
    storage.save_profile(profile)

    # Show updated confidence
    updated_conf = profile.detected_specialties[0]
    print(f"  • Updated confidence: {updated_conf.confidence:.2%}")

    print("\n4. Personalization now active!")
    print(f"  Future queries will be boosted for {top_specialty.value} content")


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║       DORA PERSONALIZATION MODULE - DEMO                  ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Run demos
    demo_specialty_detection()
    demo_profile_learning()
    demo_recommendations()
    demo_full_workflow()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nPersonalization module is ready to use!")
    print("Check the API endpoints for production integration.\n")
