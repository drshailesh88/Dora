# Rich Answer Formatting System

## Overview

The Rich Answer Formatting System transforms plain RAG query results into visually rich, scannable medical content with evidence grading, tables, decision trees, callouts, and interactive elements. This system is essential for Dora's goal of providing premium, Apple-quality medical knowledge that doctors love to use.

## Key Features

### Evidence-Based Display
- **Evidence Level Badges** (A/B/C/D/E) with color coding
- **Recommendation Strength** indicators (Strong/Weak/Conditional)
- **Source Credibility** scoring and filtering
- **Confidence Scores** displayed as percentages

### Rich Content Types
- **Sections**: Collapsible, hierarchical content organization
- **Tables**: Sortable, filterable comparison tables for drugs, dosing, differential diagnoses
- **Decision Trees**: Interactive clinical algorithms (chest pain, sepsis, stroke, etc.)
- **Callouts**: Warning, caution, info, tip, evidence, and action alerts
- **Drug Cards**: Comprehensive medication information cards
- **Calculator Results**: Formatted clinical calculator outputs (CHADS₂, Wells, GCS)

### Copy-to-Clipboard
- **EMR Integration**: One-click copy formatted for medical records
- **Multiple Formats**: Plain text, formatted text, SOAP notes, prescriptions
- **Customizable Templates**: Discharge summaries, procedure notes

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Dora RAG System                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Formatting Service (Backend)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  models.py      - Data models (RichAnswer, etc.)     │  │
│  │  evidence.py    - Evidence level grading             │  │
│  │  tables.py      - Table generation                   │  │
│  │  algorithms.py  - Decision tree builder              │  │
│  │  callouts.py    - Alert/callout generation           │  │
│  │  cards.py       - Drug/calculator cards              │  │
│  │  sections.py    - Section organization               │  │
│  │  quick_copy.py  - EMR text formatting                │  │
│  │  renderer.py    - Output format rendering            │  │
│  │  service.py     - Main orchestration service         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌────────────────────────┐  ┌────────────────────────┐
│   Web Components       │  │   Mobile Widgets       │
│   (React/TypeScript)   │  │   (Flutter/Dart)       │
│                        │  │                        │
│  - RichAnswer.tsx      │  │  - rich_answer.dart    │
│  - EvidenceBadge.tsx   │  │  - evidence_badge.dart │
│  - DrugTable.tsx       │  │  - drug_table.dart     │
│  - DecisionTree.tsx    │  │  - decision_tree.dart  │
│  - Callout.tsx         │  │  - callout.dart        │
│  - Section.tsx         │  │  - section.dart        │
│  - QuickCopy.tsx       │  │                        │
│  - DrugCard.tsx        │  │                        │
└────────────────────────┘  └────────────────────────┘
```

---

## Backend Module (`src/formatting/`)

### Core Files

#### 1. **models.py** - Data Models
All Pydantic models for structured content:
- `RichAnswer`: Main container for formatted answer
- `Section`: Hierarchical content sections
- `Table`, `TableRow`, `TableCell`: Table structures
- `DecisionTree`, `DecisionNode`: Clinical algorithms
- `Callout`: Alert boxes with severity levels
- `DrugCard`: Medication information
- `CalculatorResult`: Clinical calculator outputs
- `Citation`: Reference citations
- `EvidenceBadge`: Evidence quality indicators

#### 2. **evidence.py** - Evidence Grading
- `EvidenceGrader`: Grade evidence quality (Level A-E)
- Source credibility scoring
- Recommendation strength calculation
- Evidence freshness checking

**Example:**
```python
from src.formatting import create_evidence_badge

badge = create_evidence_badge(
    citations=retrieved_citations,
    confidence=0.85
)
# Returns: EvidenceBadge(level='A', strength='Strong', confidence=0.85)
```

#### 3. **tables.py** - Table Generator
Pre-built table generators for:
- Drug comparisons
- Dosing schedules (with renal/hepatic adjustments)
- Differential diagnoses
- Lab reference ranges
- Side effects (frequency/severity sorted)
- Drug interactions

**Example:**
```python
from src.formatting import TableGenerator

table = TableGenerator.create_drug_comparison_table([
    {"drug": "Aspirin", "dose": "81mg daily", "class": "Antiplatelet"},
    {"drug": "Clopidogrel", "dose": "75mg daily", "class": "Antiplatelet"}
])
```

#### 4. **algorithms.py** - Decision Trees
Pre-built clinical algorithms:
- Chest pain evaluation
- Sepsis management
- Stroke evaluation
- Anaphylaxis treatment

**Example:**
```python
from src.formatting import create_chest_pain_algorithm

algorithm = create_chest_pain_algorithm()
# Interactive decision tree with yes/no branching
```

#### 5. **callouts.py** - Alert Boxes
Quick creation of medical alerts:
- Black box warnings
- Drug interactions
- Contraindications
- Clinical pearls
- Pregnancy warnings
- Dosing adjustments

**Example:**
```python
from src.formatting import create_black_box_warning

warning = create_black_box_warning(
    "Warfarin",
    "Increased risk of bleeding. Monitor INR closely."
)
```

#### 6. **cards.py** - Information Cards
- `DrugCard`: Comprehensive medication info
- `CalculatorResult`: Formatted calculator outputs
- Pre-built cards: Aspirin, CHADS₂, Wells DVT, GCS

**Example:**
```python
from src.formatting import create_chads2vasc_result

result = create_chads2vasc_result(
    age=75, sex='F', chf=True, hypertension=True,
    stroke_tia=False, vascular_disease=False, diabetes=True
)
# Score: 5, Risk: High, Recommendation: Anticoagulation
```

#### 7. **service.py** - Main Service
Orchestrates all formatting:
```python
from src.formatting import FormattingService

service = FormattingService()
rich_answer = service.format_rag_response(
    query="What is the treatment for acute MI?",
    raw_answer=llm_generated_text,
    retrieved_docs=rag_documents,
    confidence_score=0.87
)
```

#### 8. **renderer.py** - Output Formats
Render to multiple formats:
- **Markdown**: For documentation
- **HTML**: For web display
- **JSON**: For API responses
- **React/TSX**: Component code generation

**Example:**
```python
from src.formatting import render_to_format

markdown = render_to_format(rich_answer, format="markdown")
html = render_to_format(rich_answer, format="html")
react_code = render_to_format(rich_answer, format="react")
```

---

## API Endpoints (`src/api/format.py`)

### Available Endpoints

#### 1. **POST /format/query**
Format a general RAG query response.

**Request:**
```json
{
  "query": "What are the side effects of metformin?",
  "answer": "Metformin commonly causes...",
  "retrieved_docs": [...],
  "confidence_score": 0.85
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "What are the side effects of metformin?",
    "summary": "...",
    "sections": [...],
    "overall_evidence": { "level": "A", "confidence_score": 0.85 },
    "citations": [...]
  }
}
```

#### 2. **POST /format/drug**
Format drug-specific queries with drug cards.

#### 3. **POST /format/calculator**
Format clinical calculator results.

#### 4. **POST /format/render**
Render formatted answer to specific format (markdown/html/react).

#### 5. **GET /format/algorithms**
Get all available clinical algorithms.

#### 6. **GET /format/calculators/chads2vasc**
Calculate CHA₂DS₂-VASc score.

**Query Parameters:**
```
?age=75&sex=F&chf=true&hypertension=true&diabetes=true
```

#### 7. **GET /format/calculators/wells-dvt**
Calculate Wells DVT score.

#### 8. **GET /format/calculators/gcs**
Calculate Glasgow Coma Scale.

---

## Web Components (`web/components/answer/`)

### React/TypeScript Components

#### **RichAnswer.tsx** - Main Container
```tsx
import { RichAnswer } from '@/components/answer';

<RichAnswer
  data={richAnswerData}
  onCopyToEMR={(text) => navigator.clipboard.writeText(text)}
  onPrescribe={(drugName) => console.log('Prescribe:', drugName)}
/>
```

#### **EvidenceBadge.tsx**
```tsx
import { EvidenceBadge } from '@/components/answer';

<EvidenceBadge
  level="A"
  strength="Strong"
  sourceCount={5}
  confidenceScore={0.89}
  showTooltip={true}
/>
```

#### **DrugTable.tsx**
Sortable, filterable tables with color coding.

#### **DecisionTree.tsx**
Interactive clinical algorithms with breadcrumb navigation.

#### **Callout.tsx**
Color-coded alert boxes with severity levels.

#### **Section.tsx**
Collapsible sections with evidence badges.

#### **QuickCopy.tsx**
One-click copy functionality with format options.

#### **DrugCard.tsx**
Comprehensive drug information cards with warnings.

### Usage Example
```tsx
import { RichAnswer, DrugCard, Callout } from '@/components/answer';

function MedicalAnswerPage() {
  const [answer, setAnswer] = useState(null);

  useEffect(() => {
    fetch('/api/v1/query', {
      method: 'POST',
      body: JSON.stringify({ question: 'Aspirin dosing for MI?' })
    })
    .then(res => res.json())
    .then(data => setAnswer(data));
  }, []);

  return answer ? <RichAnswer data={answer} /> : <Loading />;
}
```

---

## Mobile Widgets (`mobile/lib/widgets/answer/`)

### Flutter/Dart Widgets

#### **rich_answer.dart** - Main Widget
```dart
import 'package:dora/widgets/answer/rich_answer.dart';

RichAnswer(
  data: richAnswerData,
  onCopyToEMR: (text) {
    Clipboard.setData(ClipboardData(text: text));
  },
)
```

#### **evidence_badge.dart**
```dart
EvidenceBadge(
  level: EvidenceLevel.a,
  sourceCount: 5,
  confidenceScore: 0.89,
  showTooltip: true,
)
```

#### **drug_table.dart**
Responsive data tables with sorting.

#### **decision_tree.dart**
Interactive algorithm navigation.

#### **callout.dart**
Material Design alert boxes.

#### **section.dart**
Expandable/collapsible sections.

---

## Example Usage Flows

### 1. Standard Query Formatting

```python
# Backend
from src.formatting import format_query_response

rich_answer = format_query_response(
    query="Management of hypertensive emergency?",
    answer=llm_response,
    retrieved_docs=rag_docs,
    confidence=0.82
)

# Returns structured RichAnswer with:
# - Evidence badge (based on source quality)
# - Organized sections (overview, treatment, monitoring)
# - Callouts (warnings about blood pressure targets)
# - Tables (antihypertensive comparison)
# - Citations (with PubMed links)
```

### 2. Drug Query

```python
from src.formatting import FormattingService

service = FormattingService()
answer = service.format_drug_query(
    drug_name="Metformin",
    raw_answer=llm_text,
    retrieved_docs=drug_database_results,
    confidence_score=0.91
)

# Returns:
# - DrugCard with dosing, warnings, interactions
# - Side effects table (sorted by frequency/severity)
# - Renal dosing adjustment table
# - Black box warnings as critical callouts
# - Mechanism section (collapsed by default)
# - References section
```

### 3. Clinical Calculator

```python
from src.formatting import create_wells_dvt_result

result = create_wells_dvt_result(
    active_cancer=True,
    paralysis_paresis=False,
    bedridden_recent_surgery=True,
    localized_tenderness=True,
    entire_leg_swollen=False,
    calf_swelling=True,
    pitting_edema=True,
    collateral_veins=False,
    alternative_diagnosis=False
)

# Score: 5, High Probability (53%)
# Recommendation: Proceed to ultrasound, consider empiric anticoagulation
```

---

## Dependencies

### Python (Backend)
Already in `requirements.txt`:
- `pydantic>=2.0` - Data validation
- `fastapi>=0.100` - API framework

### Web (Frontend)
Add to `web/package.json`:
```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-markdown": "^9.0.0",
    "mermaid": "^10.0.0",
    "lucide-react": "^0.300.0"
  }
}
```

### Mobile (Flutter)
Add to `mobile/pubspec.yaml`:
```yaml
dependencies:
  flutter_markdown: ^0.6.18
```

---

## Integration with Existing RAG Pipeline

### Modify Query Endpoint

```python
# In src/api/app.py
from src.api.format import format_rag_query

@app.post("/api/v1/query")
async def query(request: QueryRequest):
    # Existing RAG query
    answer = await query_pipeline.query(
        question=request.question,
        patient_context=request.patient_context,
        top_k=request.top_k,
    )

    # Format the response
    formatted = await format_rag_query(
        query=request.question,
        answer=answer.answer,
        retrieved_docs=[
            {
                "id": doc.id,
                "text": doc.text,
                "metadata": {
                    "title": doc.title,
                    "source": doc.source,
                    "pmid": doc.pmid,
                    # ...
                }
            }
            for doc in answer.sources
        ],
        confidence=answer.confidence_score
    )

    return {
        "success": True,
        "answer": answer,  # Original format
        "formatted_answer": formatted  # Rich format
    }
```

---

## Evidence Level Definitions

| Level | Criteria | Description | Icon |
|-------|----------|-------------|------|
| **A** | Multiple RCTs or meta-analyses | Highest quality evidence | 🟢 |
| **B** | Single RCT or large observational | Good quality evidence | 🔵 |
| **C** | Expert consensus or small studies | Moderate quality evidence | 🟡 |
| **D** | Expert opinion only | Lower quality evidence | 🔴 |
| **E** | Insufficient evidence | Inadequate evidence | ⚫ |

---

## Callout Types

| Type | Use Case | Color | Icon |
|------|----------|-------|------|
| **Warning** | Black box warnings, contraindications | Red | ⚠️ |
| **Caution** | Drug interactions, side effects | Orange | ⚡ |
| **Info** | Additional context | Blue | ℹ️ |
| **Tip** | Clinical pearls | Green | 💡 |
| **Evidence** | Supporting studies | Purple | 📊 |
| **Action** | Recommended actions | Teal | ✅ |

---

## Testing

### Unit Tests
```python
# tests/test_formatting.py
from src.formatting import create_evidence_badge, EvidenceLevel

def test_evidence_grading():
    badge = create_evidence_badge(
        citations=[...],  # Mock RCT citations
        confidence=0.90
    )
    assert badge.level == EvidenceLevel.A
    assert badge.strength == "Strong"
```

### API Tests
```python
# tests/test_format_api.py
async def test_format_query_endpoint(client):
    response = await client.post("/format/query", json={
        "query": "Test query",
        "answer": "Test answer",
        "retrieved_docs": [],
        "confidence_score": 0.75
    })
    assert response.status_code == 200
    assert "data" in response.json()
```

---

## Future Enhancements

1. **Real-time Collaboration**: Share formatted answers with colleagues
2. **AI-Generated Diagrams**: Auto-generate medical diagrams from text
3. **Voice Integration**: "Hey DocAssist, show me the chest pain algorithm"
4. **EMR Plugins**: Direct integration with Epic, Cerner, etc.
5. **Patient Handouts**: Auto-generate patient-friendly versions
6. **Multi-language**: Translate formatted content (Hindi, Tamil, etc.)
7. **Offline Caching**: Cache formatted answers for offline access
8. **Custom Templates**: Let doctors create custom section templates

---

## Summary

The Rich Answer Formatting System transforms Dora from a simple RAG chatbot into a **premium, Apple-quality medical knowledge platform**. Key achievements:

✅ **Evidence-based**: Every answer shows quality indicators
✅ **Scannable**: Visual hierarchy, collapsible sections, color coding
✅ **Actionable**: One-click copy to EMR, prescribe, calculate
✅ **Interactive**: Decision trees, sortable tables, expandable content
✅ **Cross-platform**: Consistent experience on web, mobile, desktop
✅ **Production-ready**: Complete with API, tests, documentation

**This is what makes Dora the "UpToDate killer" that doctors will pay for.**

---

*Last Updated: January 2026*
*Files Created: 30 (11 backend, 9 web, 6 mobile, 4 API/docs)*
*Total Lines of Code: ~7,000+*
