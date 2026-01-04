# DocAssist Dora - Product Specification

## Executive Summary

**Dora** is a medical knowledge platform designed to be the "UpToDate/NotebookLM killer" for Indian physicians. It combines:
- Real-time medical knowledge retrieval (like UpToDate)
- Interactive learning and note-taking (like NotebookLM)
- Deep EMR integration (unique differentiator)
- Offline capability (critical for India)
- Voice-first interaction (hands-free in clinic)

**Target Market:** 800,000+ independent physicians in India (Tier 2/3 cities)
**Pricing:** ₹999/month (vs UpToDate's ₹3,500+/month)
**Unique Value:** The ONLY medical knowledge platform that understands YOUR patients

---

## Product Vision

### The Problem

Doctors today face:
1. **Fragmented knowledge access** - textbooks, guidelines, papers scattered across sources
2. **No patient context** - UpToDate doesn't know your patient's history
3. **Expensive subscriptions** - UpToDate costs $559/year, unaffordable for many
4. **Cloud-only** - Doesn't work in rural clinics with poor internet
5. **No integration** - Separate from EMR, appointments, prescriptions
6. **English-only** - Limited support for Indian medical context

### The Solution

**Dora** is a unified medical intelligence platform that:
1. **Retrieves** evidence from medical books, guidelines, and research
2. **Contextualizes** answers with the patient's medical history
3. **Integrates** seamlessly with EMR, appointments, and prescriptions
4. **Works offline** with local LLM and vector storage
5. **Speaks naturally** via "Hey DocAssist" voice interface
6. **Supports Indian context** - local guidelines, Hindi, regional languages

---

## Feature Specifications

### F1: Medical Knowledge Base (Core RAG)

**Priority:** P0 (Critical)
**Branch:** `feature/F1-knowledge-base`

**User Story:**
> As a physician, I want to ask clinical questions and get evidence-based answers with citations, so I can make informed treatment decisions.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F1.1 | Natural language queries | User can ask in conversational English or Hinglish |
| F1.2 | Multi-source retrieval | Searches across textbooks, guidelines, papers |
| F1.3 | Citation with sources | Every claim cites source + page/section |
| F1.4 | Confidence scoring | Displays confidence level (high/medium/low) |
| F1.5 | Related queries | Suggests follow-up questions |
| F1.6 | Offline mode | Works without internet using local models |

**Technical Approach:**
- Hybrid retrieval: Dense (PubMedBERT) + Sparse (BM25) + RRF Fusion
- Multi-query generation for query expansion
- HyDE (Hypothetical Document Embedding) for better retrieval
- Cohere reranking for precision
- Graph-based retrieval for medical relationships (Neo4j + UMLS)

**Data Sources:**
- Harrison's Principles of Internal Medicine
- Current Medical Diagnosis & Treatment
- WHO/ICMR/NHM guidelines (India-specific)
- UpToDate-equivalent content (licensed or generated)
- PubMed abstracts (for research context)

---

### F2: Patient-Contextualized Answers

**Priority:** P0 (Critical)
**Branch:** `feature/F2-patient-context`

**User Story:**
> As a physician, I want to ask questions about my current patient and get answers that consider their medical history, so I can provide personalized care.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F2.1 | Patient selection | Can select active patient from EMR |
| F2.2 | History retrieval | Retrieves relevant visits, diagnoses, medications |
| F2.3 | Contextual answers | Responses reference patient's specific conditions |
| F2.4 | Drug interactions | Alerts for interactions with current medications |
| F2.5 | Contraindication checks | Warns about contraindications for this patient |
| F2.6 | Personalized dosing | Suggests doses based on patient parameters |

**Technical Approach:**
- EMR Bridge: Bidirectional sync with DocAssist EMR
- Patient RAG: ChromaDB index of patient documents
- Multi-hop retrieval: Knowledge base + Patient history
- Prompt template: `Given patient with {conditions}, taking {medications}...`

**Example Query:**
```
Doctor: "What antibiotic for this patient's UTI?"
Dora: "Based on Mrs. Sharma's history of penicillin allergy and current
       metformin use, I recommend Nitrofurantoin 100mg BD x 5 days.

       Avoid: Fluoroquinolones (interaction with metformin)
       Source: ICMR UTI Guidelines 2023, Section 4.2"
```

---

### F3: Voice-First Interface

**Priority:** P1 (High)
**Branch:** `feature/F3-voice-interface`

**User Story:**
> As a physician examining a patient, I want to ask questions hands-free using voice, so I don't have to stop the examination to type.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F3.1 | Wake word | Activates on "Hey DocAssist" |
| F3.2 | Voice queries | Understands medical terminology via voice |
| F3.3 | Voice responses | Reads answers aloud (configurable) |
| F3.4 | Multi-language | Supports English, Hindi, Hinglish |
| F3.5 | Offline STT | Speech-to-text works without internet |
| F3.6 | Background listening | Optional always-on mode in clinic |

**Technical Approach:**
- Wake word: OpenWakeWord (local, configurable)
- STT: Whisper (local, medical vocabulary fine-tuned)
- TTS: Piper (local, natural voices)
- LLM: Qwen 2.5 (local) or Claude (cloud, when online)

---

### F4: Interactive Learning (NotebookLM-style)

**Priority:** P1 (High)
**Branch:** `feature/F4-notebook`

**User Story:**
> As a physician, I want to upload documents and have interactive conversations about them, so I can quickly learn from new guidelines or papers.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F4.1 | Document upload | Supports PDF, DOCX, TXT |
| F4.2 | Auto-summarization | Generates executive summary |
| F4.3 | Q&A over document | Can ask questions about uploaded content |
| F4.4 | Highlight & annotate | Can mark important sections |
| F4.5 | Audio overview | Generates podcast-style summary (NotebookLM feature) |
| F4.6 | Comparison mode | Compare two documents/guidelines |

**Technical Approach:**
- Document parsing: RAGFlow + MinerU
- Chunking: Medical-aware semantic chunking
- Audio: TTS with conversational synthesis
- Comparison: Side-by-side retrieval with diff highlighting

---

### F5: Academic Writing Integration

**Priority:** P1 (High)
**Branch:** `feature/F5-writing`

**User Story:**
> As a physician-researcher, I want to write papers with AI assistance and automatic PubMed integration, so I can publish more efficiently.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F5.1 | Rich text editor | Full academic formatting |
| F5.2 | PubMed search | In-line research capability |
| F5.3 | Auto-citation | Generates proper citations from sources |
| F5.4 | Writing styles | Formal, conversational, clinical options |
| F5.5 | Export | PDF, DOCX for journal submission |
| F5.6 | Collaboration | Real-time co-authoring |

**Technical Approach:**
- Integrate existing `cursor_for_academic_writing` codebase
- Shared authentication with DocAssist suite
- Sync citations to knowledge base

---

### F6: Real-Time Guideline Updates

**Priority:** P2 (Medium)
**Branch:** `feature/F6-updates`

**User Story:**
> As a physician, I want to receive notifications about updated guidelines relevant to my practice, so I stay current with evidence-based medicine.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F6.1 | Specialty preferences | User selects areas of interest |
| F6.2 | Push notifications | Alerts for new guidelines |
| F6.3 | Change summaries | "What's new" summaries |
| F6.4 | Version comparison | Diff between old and new |
| F6.5 | Scheduled sync | Weekly knowledge base updates |
| F6.6 | Offline queue | Updates download when online |

---

### F7: EMR Deep Integration

**Priority:** P0 (Critical)
**Branch:** `feature/F7-emr-integration`

**User Story:**
> As a physician, I want Dora to work seamlessly within my EMR workflow, so I don't have to switch between applications.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F7.1 | Embedded widget | Dora panel within EMR UI |
| F7.2 | Auto-context | Automatically uses selected patient |
| F7.3 | Quick actions | "Add to notes", "Create prescription" |
| F7.4 | Shared patient | Unified patient registry |
| F7.5 | Clinical notes | Can draft notes from conversation |
| F7.6 | Prescription assist | Suggests prescriptions from answers |

---

### F8: Practice Analytics Dashboard

**Priority:** P2 (Medium)
**Branch:** `feature/F8-analytics`

**User Story:**
> As a physician, I want to see insights about my knowledge usage patterns, so I can identify areas for continued learning.

**Functional Requirements:**

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| F8.1 | Query history | Searchable log of past questions |
| F8.2 | Topic trends | What topics I query most |
| F8.3 | Learning gaps | Suggested topics based on queries |
| F8.4 | CME integration | Track continuing medical education |
| F8.5 | Usage stats | Queries per day, time savings |

---

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Query latency (online) | < 3 seconds | 95th percentile |
| Query latency (offline) | < 5 seconds | 95th percentile |
| Document ingestion | < 30 seconds/page | Average |
| Voice response | < 2 seconds | Wake word to first audio |
| App startup | < 5 seconds | Cold start |

### Reliability

| Metric | Target |
|--------|--------|
| Uptime (cloud services) | 99.9% |
| Data durability | 99.999% |
| Offline availability | 100% (core features) |

### Security

| Requirement | Implementation |
|-------------|----------------|
| Data encryption at rest | AES-256 |
| Data encryption in transit | TLS 1.3 |
| Authentication | JWT + OAuth 2.0 |
| Audit logging | All patient data access |
| HIPAA compliance | Full technical safeguards |

### Scalability

| Metric | Target |
|--------|--------|
| Concurrent users | 10,000 |
| Knowledge base size | 100,000+ documents |
| Patient records | 1M+ patients per deployment |

---

## User Experience

### Design Principles

1. **Clinical-First**: Designed for exam room use
2. **Low-Light Friendly**: Dark mode for hospital settings
3. **One-Handed**: Usable with one hand (phone)
4. **Glanceable**: Key info visible without scrolling
5. **Voice-Native**: Not an afterthought

### Key Screens

1. **Home Dashboard**: Quick query, recent patients, updates
2. **Knowledge Query**: Chat-style interface with citations
3. **Patient Context**: Selected patient's summary + query
4. **Notebook**: Document viewer with annotations
5. **Settings**: Preferences, data sync, account

---

## Success Metrics

### Launch Metrics (Month 1-3)

| Metric | Target |
|--------|--------|
| Beta users | 500 physicians |
| Daily active users | 200 |
| Queries per user/day | 5 |
| NPS score | > 50 |

### Growth Metrics (Year 1)

| Metric | Target |
|--------|--------|
| Paying subscribers | 5,000 |
| Monthly recurring revenue | ₹50 lakhs |
| User retention (monthly) | > 80% |
| Referral rate | > 30% |

---

## Competitive Analysis

| Feature | UpToDate | NotebookLM | Dora |
|---------|----------|------------|------|
| Medical knowledge | ✅ Expert-curated | ❌ General | ✅ Medical-specific |
| Patient context | ❌ | ❌ | ✅ EMR-integrated |
| Offline | ❌ | ❌ | ✅ Full offline |
| Voice | ❌ | ❌ | ✅ Native |
| Document learning | ❌ | ✅ Excellent | ✅ Medical-optimized |
| Indian guidelines | ⚠️ Limited | ❌ | ✅ Native |
| Price/month | $46 | Free (limited) | $12 |
| EMR integration | Third-party | ❌ | ✅ Native |
| Academic writing | ❌ | ❌ | ✅ Built-in |

---

## Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Core RAG pipeline with medical embeddings
- [ ] Basic query interface (web)
- [ ] Knowledge base with 10 core textbooks
- [ ] PubMed integration
- [ ] Beta launch with 50 physicians

### Phase 2: EMR Integration (Months 3-4)
- [ ] DocAssist EMR integration
- [ ] Patient-contextualized answers
- [ ] Voice interface (basic)
- [ ] Offline mode (local LLM)
- [ ] Expand to 500 beta users

### Phase 3: NotebookLM Features (Months 5-6)
- [ ] Document upload and Q&A
- [ ] Audio summaries
- [ ] Guideline update notifications
- [ ] Academic writing integration
- [ ] Public launch

### Phase 4: Scale (Months 7-12)
- [ ] Mobile apps (iOS, Android)
- [ ] Hindi and regional languages
- [ ] Practice analytics
- [ ] CME integration
- [ ] 5,000 paying users target

---

*Specification Version: 1.0*
*Last Updated: January 2026*
*Status: Draft for Review*
