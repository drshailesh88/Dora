# Dora Personalization Module

## Overview

The personalization module provides intelligent specialty detection, query personalization, and recommendations for doctors using the Dora medical knowledge platform. It learns from usage patterns to improve relevance and efficiency over time.

## Features

### 1. Specialty Detection (`detector.py`)
- **Automatic specialty detection** from query patterns
- **20+ medical specialties** supported
- **Multi-signal detection**:
  - Keywords and medical terminology
  - Drug class patterns
  - ICD-10 code analysis
- **Confidence scoring** for reliable classification
- **Entity extraction** (drugs, conditions, procedures)

### 2. Query Personalization (`personalizer.py`)
- **Result boosting** based on specialty relevance
- **Metadata filtering** by specialty and practice setting
- **Score adjustment** using:
  - Specialty match
  - Preferred resources
  - Experience level
  - Common conditions
- **Context enhancement** with specialty-specific framing

### 3. Learning Engine (`learner.py`)
- **Continuous learning** from query history
- **Profile updates** with exponential moving average
- **Feedback incorporation** (positive/negative ratings)
- **Time-based decay** for evolving specialties
- **Pattern computation**:
  - Category distribution
  - Time patterns (hour/day)
  - Query complexity
  - Entity frequencies

### 4. Recommendation Engine (`recommender.py`)
- **Clinical guidelines** by specialty
- **Medical calculators** (CURB-65, CHA2DS2-VASc, etc.)
- **CME topics** based on gaps
- **Reading recommendations** (textbooks, papers)
- **Related topics** discovery

### 5. Storage Layer (`storage.py`)
- **SQLite-based** persistence
- **Profile storage** with versioning
- **Query history** tracking
- **Pattern aggregation**
- **GDPR compliance** (data deletion)

## Supported Specialties

1. **Internal Medicine** - General medicine, chronic disease management
2. **Cardiology** - Heart disease, arrhythmias, interventional
3. **Pulmonology** - Respiratory, sleep medicine, critical care
4. **Nephrology** - Kidney disease, dialysis, transplant
5. **Gastroenterology** - GI, liver, pancreas
6. **Endocrinology** - Diabetes, thyroid, hormones
7. **Neurology** - Stroke, seizures, neurodegenerative
8. **Psychiatry** - Mental health, psychopharmacology
9. **Pediatrics** - Child health, development
10. **Obstetrics & Gynecology** - Pregnancy, women's health
11. **Surgery (General)** - Surgical procedures
12. **Orthopedics** - Bone, joint, spine
13. **Dermatology** - Skin conditions
14. **Ophthalmology** - Eye care
15. **ENT** - Ear, nose, throat
16. **Radiology** - Imaging
17. **Pathology** - Diagnostics
18. **Emergency Medicine** - Acute care, trauma
19. **Critical Care** - ICU, ventilation
20. **Family Medicine** - Primary care
21. **Oncology** - Cancer treatment
22. **Hematology** - Blood disorders
23. **Infectious Disease** - Infections, antibiotics
24. **Rheumatology** - Autoimmune, arthritis
25. **Urology** - Urinary, reproductive

## Usage

### Basic Usage

```python
from src.personalization import (
    SpecialtyDetector,
    QueryPersonalizer,
    ProfileLearner,
    PersonalizationStorage,
    DoctorProfile,
)

# Initialize components
storage = PersonalizationStorage()
detector = SpecialtyDetector()
personalizer = QueryPersonalizer()
learner = ProfileLearner()

# Get or create profile
user_id = "doctor_123"
profile = storage.get_profile(user_id)
if not profile:
    profile = DoctorProfile(user_id=user_id)
    storage.save_profile(profile)

# Detect specialty from query
query = "What is the management of atrial fibrillation with RVR?"
detection = detector.detect_from_query(query)
if detection:
    specialty, confidence = detection
    print(f"Detected: {specialty.value} (confidence: {confidence:.2f})")

# Personalize retrieval results
personalized_results = personalizer.personalize_results(
    results=raw_results,
    profile=profile,
    query=query,
)

# Learn from history
history = storage.get_recent_query_history(user_id, days=30)
updated_profile = learner.learn_from_history(profile, history)
storage.save_profile(updated_profile)
```

### Integration with RAG Pipeline

The personalization module is automatically integrated with `MedicalQueryPipeline`:

```python
from src.core.pipeline import MedicalQueryPipeline

# Initialize pipeline with personalization
pipeline = MedicalQueryPipeline(use_personalization=True)

# Query with user ID for personalization
answer = await pipeline.query(
    question="Management of heart failure with reduced EF",
    user_id="doctor_123",  # Enables personalization
)
```

### API Endpoints

#### Get Profile
```bash
GET /api/v1/personalization/profile
Authorization: Bearer <token>
```

#### Update Profile
```bash
PUT /api/v1/personalization/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "primary_specialty": "cardiology",
  "years_of_experience": 10,
  "preferred_detail_level": "detailed"
}
```

#### Get Detected Specialty
```bash
GET /api/v1/personalization/profile/specialty
Authorization: Bearer <token>
```

#### Provide Feedback
```bash
POST /api/v1/personalization/profile/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
  "query_id": "uuid-here",
  "rating": 5,
  "clicked_results": ["result_id_1", "result_id_2"]
}
```

#### Get Recommendations
```bash
GET /api/v1/personalization/recommendations?context=heart_failure
Authorization: Bearer <token>
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MedicalQueryPipeline                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Query Enhancement (add specialty context)            │  │
│  │  2. Metadata Filtering (specialty, practice setting)     │  │
│  │  3. Retrieval (with filters)                             │  │
│  │  4. Result Personalization (boost/filter by specialty)   │  │
│  │  5. Query Tracking (entity extraction, specialty detect) │  │
│  │  6. Profile Update (learning from patterns)              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │   Personalization Components       │
         ├────────────────────────────────────┤
         │  • SpecialtyDetector              │
         │  • QueryPersonalizer               │
         │  • ProfileLearner                  │
         │  • PersonalizedRecommender         │
         │  • PersonalizationStorage          │
         └────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │   SQLite Database                  │
         ├────────────────────────────────────┤
         │  • doctor_profiles                 │
         │  • query_history                   │
         │  • query_patterns                  │
         └────────────────────────────────────┘
```

## Data Models

### DoctorProfile
- Primary and subspecialties
- Years of experience
- Practice settings
- Common conditions
- Preferred drug classes
- Detail level preferences
- Query statistics

### QueryHistory
- Query text
- Detected specialty
- Extracted entities (drugs, conditions, procedures)
- User feedback
- Clicked results
- Timestamp

### QueryPattern
- Category distribution
- Time patterns (hourly, weekly)
- Query complexity
- Common keywords
- Feedback statistics

## Privacy & Compliance

- **HIPAA Compliant**: No PHI stored in query history
- **GDPR Ready**: User data deletion endpoint
- **Configurable**: Option to disable query text storage
- **Anonymization**: Automatic after configurable days
- **Local Storage**: SQLite database stays on doctor's device

## Configuration

```python
from src.personalization import PersonalizationConfig

config = PersonalizationConfig(
    specialty_boost_factor=1.5,          # Boost specialty results by 50%
    specialty_filter_threshold=0.3,      # Minimum relevance score
    learning_rate=0.1,                   # How fast to learn
    decay_factor=0.95,                   # Time-based decay
    min_queries_for_detection=10,        # Min queries before detection
    store_query_text=True,               # Store full query text
    anonymize_after_days=90,             # Anonymize after 90 days
)
```

## Performance

- **Detection latency**: <10ms per query
- **Personalization overhead**: <5ms per query
- **Storage**: ~1KB per query record
- **Memory**: <50MB for typical profiles

## Future Enhancements

1. **Advanced NER**: Use ScispaCy or BioBERT for entity extraction
2. **Embeddings-based similarity**: Semantic topic matching
3. **Collaborative filtering**: Learn from similar doctors
4. **A/B testing**: Measure personalization impact
5. **Multi-language**: Support for regional languages
6. **Voice pattern**: Learn from voice queries
7. **EMR integration**: Learn from prescribed medications

## Testing

```bash
# Run tests
pytest tests/test_personalization.py -v

# Test specialty detection
python -m src.personalization.detector

# Test full pipeline
python -c "
from src.core.pipeline import MedicalQueryPipeline
pipeline = MedicalQueryPipeline(use_personalization=True)
answer = pipeline.query_sync('Management of DKA', user_id='test_user')
print(answer.to_display_string())
"
```

## Credits

Built for the Dora medical knowledge platform by DocAssist.
Inspired by best practices from UpToDate, NotebookLM, and clinical decision support systems.
