# DocAssist Dora - Task Breakdown

## Phase 1: Core RAG Foundation (Weeks 1-4)

### Sprint 1.1: Project Setup (Week 1)

- [ ] **T1.1.1** Initialize project with spec-kit structure
  - Run `specify init . --ai claude`
  - Verify constitution, spec, plan, tasks files created
  - Configure ralph-wiggum for iterative development

- [ ] **T1.1.2** Set up Python project structure
  - Create `pyproject.toml` with dependencies
  - Set up `src/` directory structure
  - Configure pytest, mypy, ruff, black
  - Create initial `main.py` entry point

- [ ] **T1.1.3** Set up development environment
  - Docker Compose for local services (Qdrant, Redis)
  - Environment variable configuration (.env.example)
  - VS Code settings and extensions
  - Pre-commit hooks

- [ ] **T1.1.4** Create CI/CD pipeline
  - GitHub Actions for tests
  - Coverage reporting (80% minimum)
  - Type checking with mypy
  - Linting with ruff

### Sprint 1.2: Embedding & Vector Store (Week 2)

- [ ] **T1.2.1** Implement medical embeddings module
  - Create `src/embeddings/medical_embeddings.py`
  - Load PubMedBERT from HuggingFace
  - Implement `embed_literature()` and `embed_clinical()` methods
  - Write unit tests

- [ ] **T1.2.2** Configure Qdrant vector store
  - Create `src/storage/qdrant_client.py`
  - Define collections: `medical_knowledge`, `patient_documents`
  - Implement upsert, search, delete operations
  - Write integration tests

- [ ] **T1.2.3** Implement BM25 sparse retriever
  - Create `src/retrieval/sparse_retriever.py`
  - Build inverted index structure
  - Implement search with TF-IDF scoring
  - Write unit tests

- [ ] **T1.2.4** Implement RRF fusion
  - Create `src/retrieval/fusion.py`
  - Implement Reciprocal Rank Fusion algorithm
  - Support multiple retriever inputs
  - Write unit tests with known rankings

### Sprint 1.3: Query Pipeline (Week 3)

- [ ] **T1.3.1** Implement multi-query generation
  - Create `src/query/multi_query.py`
  - Use LLM to generate query variations
  - Template for medical query expansion
  - Write tests

- [ ] **T1.3.2** Implement HyDE (Hypothetical Document Embedding)
  - Create `src/query/hyde.py`
  - Generate hypothetical answer with LLM
  - Embed and use for retrieval
  - Write tests

- [ ] **T1.3.3** Integrate Cohere reranking
  - Create `src/retrieval/reranker.py`
  - Configure Cohere API client
  - Implement rerank method
  - Write tests (mock API for unit, real for integration)

- [ ] **T1.3.4** Build main query pipeline
  - Create `src/pipeline/query_pipeline.py`
  - Orchestrate: multi-query → HyDE → retrieval → fusion → rerank
  - Implement `query()` method
  - Write end-to-end tests

### Sprint 1.4: Ingestion & UI (Week 4)

- [ ] **T1.4.1** Implement document parser
  - Create `src/ingestion/parser.py`
  - Integrate RAGFlow for PDF parsing
  - Handle tables, images, layouts
  - Write tests with sample medical PDFs

- [ ] **T1.4.2** Implement medical-aware chunker
  - Create `src/ingestion/chunker.py`
  - Preserve drug dosing blocks
  - Maintain clinical context
  - Write tests

- [ ] **T1.4.3** Build ingestion pipeline
  - Create `src/ingestion/pipeline.py`
  - Orchestrate: parse → chunk → embed → store
  - Implement `ingest_document()` method
  - Write end-to-end tests

- [ ] **T1.4.4** Create basic web UI
  - Set up Next.js project in `frontend/`
  - Create chat-style query interface
  - Display answers with citations
  - Implement API client

- [ ] **T1.4.5** Ingest initial knowledge base
  - Process 3 core medical textbooks
  - Verify retrieval quality
  - Document ingestion statistics

---

## Phase 2: EMR Integration (Weeks 5-8)

### Sprint 2.1: EMR Bridge (Week 5)

- [ ] **T2.1.1** Design EMR sync architecture
  - Define shared patient schema
  - Design file watcher mechanism
  - Document sync protocol

- [ ] **T2.1.2** Implement EMR bridge
  - Create `src/integrations/emr_bridge.py`
  - Connect to DocAssist EMR SQLite
  - Implement patient data retrieval
  - Write tests

- [ ] **T2.1.3** Implement file watcher for real-time sync
  - Use watchdog library
  - Detect EMR database changes
  - Trigger patient re-indexing
  - Write tests

- [ ] **T2.1.4** Create patient context builder
  - Create `src/patient/context_builder.py`
  - Aggregate visits, medications, investigations
  - Generate patient summary
  - Write tests

### Sprint 2.2: Patient-Contextualized RAG (Week 6)

- [ ] **T2.2.1** Index patient documents in ChromaDB
  - Create `src/patient/patient_rag.py`
  - Index visits, notes, investigations
  - Support per-patient collections
  - Write tests

- [ ] **T2.2.2** Implement patient-aware query
  - Extend query pipeline
  - Merge patient context with knowledge retrieval
  - Create prompt template for patient context
  - Write tests

- [ ] **T2.2.3** Add patient selection UI
  - Add patient selector in web UI
  - Display patient summary
  - Enable contextual queries
  - Write frontend tests

### Sprint 2.3: Drug Safety (Week 7)

- [ ] **T2.3.1** Set up Neo4j with UMLS
  - Configure Neo4j (AuraDB or local)
  - Load UMLS drug-drug interactions
  - Load disease-treatment relationships
  - Verify graph queries

- [ ] **T2.3.2** Implement drug interaction checker
  - Create `src/safety/drug_interactions.py`
  - Query Neo4j for medication list
  - Return severity-ranked interactions
  - Write tests

- [ ] **T2.3.3** Implement contraindication checker
  - Create `src/safety/contraindications.py`
  - Check against patient conditions
  - Generate warnings
  - Write tests

- [ ] **T2.3.4** Integrate safety checks in query pipeline
  - Add warnings to MedicalAnswer
  - Display warnings prominently in UI
  - Write end-to-end tests

### Sprint 2.4: EMR Widget (Week 8)

- [ ] **T2.4.1** Design EMR widget architecture
  - Define embedding mechanism
  - Design communication protocol
  - Create mockups

- [ ] **T2.4.2** Implement EMR widget (Flet)
  - Create `src/ui/emr_widget.py`
  - Embed in DocAssist EMR
  - Auto-select active patient
  - Write tests

- [ ] **T2.4.3** Add quick actions
  - "Add to notes" action
  - "Create prescription" action
  - "Save to favorites" action
  - Write tests

---

## Phase 3: Voice & Offline (Weeks 9-12)

### Sprint 3.1: Speech Recognition (Week 9)

- [ ] **T3.1.1** Implement wake word detection
  - Create `src/voice/wake_word.py`
  - Configure OpenWakeWord for "Hey DocAssist"
  - Test accuracy and latency
  - Write tests

- [ ] **T3.1.2** Integrate Whisper STT
  - Create `src/voice/stt.py`
  - Load Whisper model (base.en or small)
  - Implement transcribe method
  - Write tests with medical terminology

- [ ] **T3.1.3** Create voice recording module
  - Create `src/voice/recorder.py`
  - Handle microphone input
  - Detect speech start/end
  - Write tests

### Sprint 3.2: Speech Synthesis & Intent (Week 10)

- [ ] **T3.2.1** Integrate Piper TTS
  - Create `src/voice/tts.py`
  - Load Piper voice model
  - Implement speak method
  - Write tests

- [ ] **T3.2.2** Implement intent parser
  - Create `src/voice/intent.py`
  - Define medical intents (query, drug_check, patient_lookup)
  - Use local LLM for classification
  - Write tests

- [ ] **T3.2.3** Build voice agent orchestrator
  - Create `src/voice/agent.py`
  - Orchestrate: wake → record → transcribe → intent → action → speak
  - Implement main loop
  - Write integration tests

### Sprint 3.3: Offline Mode (Week 11)

- [ ] **T3.3.1** Set up Ollama with Qwen 2.5
  - Create `src/llm/local_llm.py`
  - Configure Ollama client
  - Implement generate method
  - Test on medical prompts

- [ ] **T3.3.2** Implement offline query cache
  - Create `src/cache/offline_cache.py`
  - Cache frequent queries in SQLite
  - Implement cache lookup before API call
  - Write tests

- [ ] **T3.3.3** Implement connectivity detection
  - Create `src/network/connectivity.py`
  - Detect online/offline state
  - Switch between cloud and local LLM
  - Write tests

- [ ] **T3.3.4** Create local knowledge subset
  - Identify essential knowledge for offline
  - Create ChromaDB local instance
  - Sync mechanism when online
  - Write tests

### Sprint 3.4: Voice UI & Polish (Week 12)

- [ ] **T3.4.1** Add voice indicator to UI
  - Show listening state
  - Display transcription in real-time
  - Show processing state
  - Write tests

- [ ] **T3.4.2** Implement voice settings
  - Voice on/off toggle
  - Volume control
  - Wake word sensitivity
  - Write tests

- [ ] **T3.4.3** Test offline mode end-to-end
  - Disable network and test all features
  - Verify voice works offline
  - Document limitations
  - Write airplane mode tests

---

## Phase 4: NotebookLM Features (Weeks 13-16)

### Sprint 4.1: Document Upload (Week 13)

- [ ] **T4.1.1** Implement document upload API
  - Create upload endpoint
  - Store in user's document collection
  - Trigger ingestion
  - Write tests

- [ ] **T4.1.2** Create document management UI
  - List user's documents
  - Upload interface
  - Delete functionality
  - Write tests

- [ ] **T4.1.3** Implement per-document Q&A
  - Scope retrieval to specific document
  - Create document chat view
  - Write tests

### Sprint 4.2: Audio & Learning (Week 14)

- [ ] **T4.2.1** Implement auto-summarization
  - Generate executive summary on ingestion
  - Display in document list
  - Write tests

- [ ] **T4.2.2** Create audio overview generation
  - Generate podcast-style script
  - Synthesize with Piper TTS
  - Stream audio to user
  - Write tests

- [ ] **T4.2.3** Implement highlight & annotate
  - Allow text highlighting
  - Save annotations
  - Display in document view
  - Write tests

### Sprint 4.3: Updates & Academic Writing (Week 15)

- [ ] **T4.3.1** Implement guideline update notifications
  - Monitor knowledge base for updates
  - Match to user's specialty
  - Send push notifications
  - Write tests

- [ ] **T4.3.2** Integrate academic writing tool
  - Connect to cursor_for_academic_writing
  - Shared authentication
  - Cross-link citations
  - Write tests

- [ ] **T4.3.3** Implement document comparison
  - Side-by-side view
  - Highlight differences
  - Summarize changes
  - Write tests

### Sprint 4.4: Polish & Launch Prep (Week 16)

- [ ] **T4.4.1** Performance optimization
  - Profile query latency
  - Optimize bottlenecks
  - Implement caching
  - Benchmark results

- [ ] **T4.4.2** Security audit
  - Review authentication
  - Audit logging verification
  - Penetration testing
  - Fix findings

- [ ] **T4.4.3** Documentation
  - User guide
  - API documentation
  - Deployment guide
  - Support runbook

- [ ] **T4.4.4** Beta launch preparation
  - Set up production infrastructure
  - Configure monitoring
  - Create feedback channels
  - Prepare launch materials

---

## Ongoing Tasks

- [ ] **Weekly**: Update spec and plan based on learnings
- [ ] **Weekly**: Sync CLAUDE.md, AGENTS.md, CODEX.md, GEMINI.md, GROK.md
- [ ] **Daily**: Run test suite (80% coverage minimum)
- [ ] **Per-commit**: Type check and lint
- [ ] **Per-feature**: Clinical validation with physician

---

## Ralph-Loop Commands for Complex Tasks

Use these for autonomous implementation of complex features:

```bash
# Core RAG pipeline
/ralph-loop "Implement medical query pipeline with multi-query, HyDE, hybrid retrieval, RRF fusion, and Cohere reranking. All tests must pass with >90% retrieval accuracy on medical QA dataset." --max-iterations 50 --completion-promise "All query pipeline tests passing with >90% accuracy"

# EMR integration
/ralph-loop "Implement EMR bridge with real-time sync, patient context retrieval, and drug interaction checking. Must integrate with DocAssist EMR SQLite database." --max-iterations 40 --completion-promise "EMR integration complete with all tests passing"

# Voice agent
/ralph-loop "Implement voice agent with wake word detection, Whisper STT, Piper TTS, and medical intent parsing. Must work fully offline." --max-iterations 40 --completion-promise "Voice agent working offline with all tests passing"
```

---

*Tasks Version: 1.0*
*Last Updated: January 2026*
*Total Estimated Duration: 16 weeks*
