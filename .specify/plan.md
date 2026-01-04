# DocAssist Dora - Technical Implementation Plan

## Overview

This document outlines the technical architecture and implementation plan for Dora, the DocAssist Medical Knowledge Platform.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DORA SYSTEM ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         CLIENT APPLICATIONS                             │ │
│  ├──────────────┬──────────────┬──────────────┬───────────────────────────┤ │
│  │  Desktop     │   Web App    │  Mobile      │   EMR Widget              │ │
│  │  (Flet)      │  (Next.js)   │  (Flutter)   │   (Embedded)              │ │
│  └──────────────┴──────────────┴──────────────┴───────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          API GATEWAY                                    │ │
│  │                        (FastAPI + Kong)                                 │ │
│  │   /query  /patient  /documents  /voice  /auth  /sync  /analytics       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐ │
│  │  QUERY SERVICE  │    │   PATIENT SERVICE   │    │   VOICE SERVICE     │ │
│  │                 │    │                     │    │                     │ │
│  │ • Multi-query   │    │ • EMR Bridge        │    │ • Wake Word         │ │
│  │ • HyDE          │    │ • Patient RAG       │    │ • Whisper STT       │ │
│  │ • Hybrid Search │    │ • Context Builder   │    │ • Piper TTS         │ │
│  │ • Reranking     │    │ • History Retrieval │    │ • Intent Parse      │ │
│  │ • Synthesis     │    │                     │    │                     │ │
│  └────────┬────────┘    └──────────┬──────────┘    └─────────────────────┘ │
│           │                        │                                        │
│           └────────────┬───────────┘                                        │
│                        ▼                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     RETRIEVAL & REASONING LAYER                         │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │   Dense     │  │   Sparse    │  │   Graph     │  │  Reranker   │   │ │
│  │  │  Retriever  │  │  Retriever  │  │  Retriever  │  │  (Cohere)   │   │ │
│  │  │ (PubMedBERT)│  │   (BM25)    │  │  (Neo4j)    │  │             │   │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │ │
│  │         │                │                │                │          │ │
│  │         └────────────────┴────────────────┴────────────────┘          │ │
│  │                                   │                                    │ │
│  │                                   ▼                                    │ │
│  │                        ┌─────────────────────┐                        │ │
│  │                        │   RRF Fusion        │                        │ │
│  │                        │   + Context Merge   │                        │ │
│  │                        └─────────────────────┘                        │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          LLM SYNTHESIS LAYER                            │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                         │ │
│  │    ┌──────────────────────┐         ┌──────────────────────┐           │ │
│  │    │   CLOUD LLMs         │         │   LOCAL LLMs          │           │ │
│  │    │   (Online Mode)      │         │   (Offline Mode)      │           │ │
│  │    │                      │         │                        │           │ │
│  │    │ • Claude 3.5 Sonnet  │  ←OR→  │ • Qwen 2.5 (7B)        │           │ │
│  │    │ • GPT-4o             │         │ • BioMistral-7B        │           │ │
│  │    │ • Gemini 2.0         │         │ • Ollama Runtime       │           │ │
│  │    └──────────────────────┘         └──────────────────────┘           │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                           DATA LAYER                                    │ │
│  ├──────────────┬──────────────┬──────────────┬───────────────────────────┤ │
│  │   Qdrant     │   Neo4j      │  PostgreSQL  │   SQLite                  │ │
│  │  (Vectors)   │   (Graph)    │   (Cloud)    │   (Local)                 │ │
│  │              │              │              │                           │ │
│  │ • Medical    │ • UMLS       │ • Users      │ • Patient data            │ │
│  │   embeddings │ • Drug-Drug  │ • Documents  │ • Offline cache           │ │
│  │ • Patient    │ • Disease-   │ • Analytics  │ • Local settings          │ │
│  │   docs       │   Treatment  │ • Billing    │                           │ │
│  └──────────────┴──────────────┴──────────────┴───────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      KNOWLEDGE BASE (Ingestion)                        │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                         │ │
│  │  PDFs ──► RAGFlow Parser ──► Semantic Chunker ──► PubMedBERT ──►       │ │
│  │            (Tables, Images)   (Medical-aware)     (Embeddings)          │ │
│  │                                                                         │ │
│  │       ──► Qdrant (vectors) + Neo4j (relationships) + BM25 (sparse)     │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Query Pipeline (Enhanced Portable RAG)

Building on your existing Portable RAG system, we enhance with medical-specific components:

```python
# query_pipeline.py - Core RAG pipeline

class MedicalQueryPipeline:
    def __init__(self):
        # Retrievers
        self.dense_retriever = PubMedBERTRetriever(top_k=20)
        self.sparse_retriever = BM25Retriever(top_k=20)
        self.graph_retriever = Neo4jUMLSRetriever(top_k=10)

        # Fusion & Reranking
        self.rrf_fusion = ReciprocalRankFusion(k=60)
        self.reranker = CohereReranker(model="rerank-english-v3.0", top_k=10)

        # Synthesis
        self.synthesizer = MedicalSynthesizer()

    async def query(
        self,
        question: str,
        patient_context: Optional[PatientContext] = None,
        use_multi_query: bool = True,
        use_hyde: bool = True
    ) -> MedicalAnswer:
        # 1. Query Expansion
        queries = [question]
        if use_multi_query:
            queries.extend(self._generate_query_variations(question))

        # 2. HyDE (Hypothetical Document Embedding)
        if use_hyde:
            hyde_doc = self._generate_hypothetical_answer(question)
            queries.append(hyde_doc)

        # 3. Parallel Retrieval
        dense_results = await self.dense_retriever.retrieve_batch(queries)
        sparse_results = await self.sparse_retriever.retrieve_batch(queries)
        graph_results = await self.graph_retriever.retrieve(question)

        # 4. Fusion
        fused = self.rrf_fusion.fuse([dense_results, sparse_results, graph_results])

        # 5. Patient Context Augmentation
        if patient_context:
            patient_docs = await self._retrieve_patient_context(patient_context)
            fused = self._merge_with_patient_context(fused, patient_docs)

        # 6. Reranking
        reranked = await self.reranker.rerank(question, fused)

        # 7. Synthesis with Citations
        answer = await self.synthesizer.synthesize(
            question=question,
            context=reranked,
            patient_context=patient_context
        )

        return answer
```

### 2. Medical Embedding Layer

```python
# embeddings.py - Medical-optimized embeddings

from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

class MedicalEmbeddings:
    """
    Dual-encoder for medical text:
    - PubMedBERT for medical literature (768-dim)
    - Clinical ModernBERT for clinical notes (768-dim, 8K context)
    """

    def __init__(self):
        # Primary: PubMedBERT for medical literature
        self.literature_model = SentenceTransformer(
            "NeuML/pubmedbert-base-embeddings"
        )

        # Secondary: Clinical ModernBERT for clinical notes
        self.clinical_model = AutoModel.from_pretrained(
            "clinical-modernbert"  # When available, else fallback
        )

        # Sparse: BM25 for keyword matching
        self.bm25_index = None  # Initialized on corpus load

    def embed_literature(self, texts: List[str]) -> np.ndarray:
        """Embed medical literature (textbooks, guidelines, papers)"""
        return self.literature_model.encode(texts, normalize_embeddings=True)

    def embed_clinical(self, texts: List[str]) -> np.ndarray:
        """Embed clinical notes (patient records, prescriptions)"""
        return self.clinical_model.encode(texts, normalize_embeddings=True)
```

### 3. Knowledge Graph Integration

```python
# graph_retriever.py - UMLS-based medical knowledge graph

from neo4j import GraphDatabase

class Neo4jUMLSRetriever:
    """
    Graph-based retrieval using UMLS medical concepts:
    - Drug-drug interactions
    - Disease-treatment relationships
    - Symptom-diagnosis mappings
    """

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    async def retrieve(self, query: str) -> List[GraphDocument]:
        # 1. Extract medical entities from query
        entities = await self._extract_medical_entities(query)

        # 2. Traverse graph for related concepts
        results = []
        for entity in entities:
            cypher = """
            MATCH (e:Entity {name: $entity})
            -[r:TREATS|CAUSES|INTERACTS_WITH|INDICATES*1..2]->(related)
            RETURN e, r, related
            LIMIT 10
            """
            with self.driver.session() as session:
                records = session.run(cypher, entity=entity.name)
                results.extend(self._parse_records(records))

        return results

    async def check_drug_interactions(
        self,
        medications: List[str]
    ) -> List[DrugInteraction]:
        """Check for dangerous drug-drug interactions"""
        cypher = """
        UNWIND $meds AS med1
        UNWIND $meds AS med2
        MATCH (d1:Drug {name: med1})-[i:INTERACTS_WITH]->(d2:Drug {name: med2})
        WHERE med1 < med2
        RETURN d1.name, d2.name, i.severity, i.description
        """
        # ... implementation
```

### 4. EMR Bridge

```python
# emr_bridge.py - Bidirectional sync with DocAssist EMR

import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class EMRBridge:
    """
    Connects Dora to DocAssist EMR:
    - Shared patient registry
    - Real-time sync via file watching
    - RAG over patient records
    """

    def __init__(self, emr_db_path: str):
        self.emr_db_path = emr_db_path
        self.patient_cache = {}
        self._start_watcher()

    def _start_watcher(self):
        """Watch EMR database for changes"""
        handler = EMRChangeHandler(self)
        observer = Observer()
        observer.schedule(handler, path=os.path.dirname(self.emr_db_path))
        observer.start()

    def get_patient_context(self, patient_id: int) -> PatientContext:
        """Build patient context for RAG"""
        conn = sqlite3.connect(self.emr_db_path)

        # Fetch patient data
        patient = self._fetch_patient(conn, patient_id)
        visits = self._fetch_visits(conn, patient_id)
        medications = self._fetch_medications(conn, patient_id)
        investigations = self._fetch_investigations(conn, patient_id)

        conn.close()

        return PatientContext(
            patient=patient,
            visits=visits,
            medications=medications,
            investigations=investigations,
            summary=self._generate_summary(patient, visits, medications)
        )

    def index_patient_for_rag(self, patient_id: int):
        """Index patient documents in ChromaDB for retrieval"""
        context = self.get_patient_context(patient_id)

        documents = []
        for visit in context.visits:
            documents.append({
                "content": f"Visit on {visit.date}: {visit.chief_complaint}. "
                          f"Diagnosis: {visit.diagnosis}. Notes: {visit.notes}",
                "metadata": {
                    "type": "visit",
                    "patient_id": patient_id,
                    "date": visit.date
                }
            })

        self.chroma_client.add(
            collection_name=f"patient_{patient_id}",
            documents=documents
        )
```

### 5. Voice Agent

```python
# voice_agent.py - Voice interface for Dora

from openwakeword import WakeWordDetector
import whisper
from piper import PiperVoice

class DoraVoiceAgent:
    """
    Voice-first interface:
    - "Hey DocAssist" wake word
    - Whisper STT (local)
    - Piper TTS (local)
    - Medical intent parsing
    """

    def __init__(self):
        # Wake word
        self.wake_detector = WakeWordDetector(
            wake_words=["hey_docassist"],
            threshold=0.5
        )

        # Speech-to-text (local Whisper)
        self.stt = whisper.load_model("base.en")

        # Text-to-speech (Piper)
        self.tts = PiperVoice.load("en_US-lessac-medium")

        # Query pipeline
        self.query_pipeline = MedicalQueryPipeline()

    async def listen_and_respond(self):
        """Main voice loop"""
        while True:
            # 1. Wait for wake word
            audio = await self._record_until_wake_word()

            # 2. Record query
            query_audio = await self._record_query(timeout=10)

            # 3. Transcribe
            text = self.stt.transcribe(query_audio)["text"]
            print(f"Heard: {text}")

            # 4. Process query
            answer = await self.query_pipeline.query(text)

            # 5. Speak response
            self.tts.say(answer.text)

    def _parse_medical_intent(self, text: str) -> MedicalIntent:
        """Parse intent: query_knowledge, check_drug, patient_context, etc."""
        # Use local LLM for intent classification
        prompt = f"""
        Classify this medical query:
        "{text}"

        Categories:
        - knowledge_query: General medical question
        - patient_query: Question about specific patient
        - drug_check: Drug interaction or dosage question
        - guideline_lookup: Clinical guideline request

        Return JSON: {{"intent": "...", "entities": [...]}}
        """
        return self.llm.generate(prompt, json_mode=True)
```

### 6. Document Ingestion Pipeline

```python
# ingestion.py - Medical document processing

from ragflow import RAGFlowParser
from langchain.text_splitter import RecursiveCharacterTextSplitter

class MedicalDocumentIngester:
    """
    Ingests medical documents with:
    - Complex PDF parsing (RAGFlow)
    - Medical-aware chunking
    - Metadata extraction
    - Multi-index storage
    """

    def __init__(self):
        self.parser = RAGFlowParser()
        self.chunker = MedicalChunker()
        self.embedder = MedicalEmbeddings()
        self.vector_store = QdrantClient()
        self.graph_store = Neo4jClient()

    async def ingest_document(
        self,
        file_path: str,
        doc_type: str,  # "textbook", "guideline", "paper"
        metadata: dict
    ):
        # 1. Parse document (handles tables, images, layouts)
        parsed = await self.parser.parse(file_path)

        # 2. Extract structure
        sections = self._extract_sections(parsed)

        # 3. Medical-aware chunking
        chunks = []
        for section in sections:
            section_chunks = self.chunker.chunk(
                text=section.text,
                metadata={
                    **metadata,
                    "section": section.title,
                    "page": section.page
                }
            )
            chunks.extend(section_chunks)

        # 4. Generate embeddings
        embeddings = self.embedder.embed_literature([c.text for c in chunks])

        # 5. Store in vector database
        self.vector_store.upsert(
            collection_name="medical_knowledge",
            points=[
                {
                    "id": chunk.id,
                    "vector": embedding,
                    "payload": chunk.metadata
                }
                for chunk, embedding in zip(chunks, embeddings)
            ]
        )

        # 6. Extract entities for graph
        entities = await self._extract_medical_entities(chunks)
        self.graph_store.add_entities(entities)

        return {"chunks": len(chunks), "entities": len(entities)}


class MedicalChunker:
    """
    Chunks medical text intelligently:
    - Preserves clinical context
    - Keeps drug dosing together
    - Maintains table integrity
    """

    def __init__(self, chunk_size: int = 1024, overlap: int = 150):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=[
                "\n## ",  # Major sections
                "\n### ", # Subsections
                "\n\n",   # Paragraphs
                "\n",     # Lines
                ". ",     # Sentences
            ]
        )

    def chunk(self, text: str, metadata: dict) -> List[Chunk]:
        # Special handling for medical content

        # 1. Protect drug dosing blocks
        text = self._protect_dosing_blocks(text)

        # 2. Protect tables
        text = self._protect_tables(text)

        # 3. Split
        chunks = self.splitter.split_text(text)

        # 4. Restore protected content
        chunks = [self._restore_protected(c) for c in chunks]

        return [
            Chunk(text=c, metadata=metadata, id=self._generate_id(c))
            for c in chunks
        ]
```

---

## Data Models

```python
# models.py - Core data models

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Citation(BaseModel):
    source: str
    title: str
    section: Optional[str]
    page: Optional[int]
    url: Optional[str]
    relevance_score: float

class MedicalAnswer(BaseModel):
    """Response from Dora query"""
    question: str
    answer: str
    confidence: ConfidenceLevel
    citations: List[Citation]
    related_queries: List[str]
    patient_context_used: bool
    warnings: List[str]  # Drug interactions, contraindications
    generated_at: datetime

class PatientContext(BaseModel):
    """Patient information for contextualized queries"""
    patient_id: int
    name: str
    age: int
    gender: str
    active_diagnoses: List[str]
    current_medications: List[str]
    allergies: List[str]
    recent_visits: List[dict]
    summary: str

class Document(BaseModel):
    """Ingested document"""
    id: str
    title: str
    doc_type: str  # textbook, guideline, paper
    source: str
    ingested_at: datetime
    chunk_count: int
    metadata: dict
```

---

## API Design

```yaml
# openapi.yaml - REST API specification

openapi: 3.0.0
info:
  title: Dora Medical Knowledge API
  version: 1.0.0

paths:
  /api/v1/query:
    post:
      summary: Query medical knowledge base
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                question:
                  type: string
                patient_id:
                  type: integer
                  nullable: true
                options:
                  type: object
                  properties:
                    use_multi_query:
                      type: boolean
                    use_hyde:
                      type: boolean
                    include_patient_context:
                      type: boolean
      responses:
        200:
          description: Medical answer with citations
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MedicalAnswer'

  /api/v1/documents:
    post:
      summary: Ingest a document
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                doc_type:
                  type: string
                  enum: [textbook, guideline, paper]
                metadata:
                  type: object
      responses:
        201:
          description: Document ingested

  /api/v1/patients/{patient_id}/context:
    get:
      summary: Get patient context for queries
      parameters:
        - name: patient_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Patient context
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatientContext'

  /api/v1/voice/transcribe:
    post:
      summary: Transcribe audio to text
      requestBody:
        content:
          audio/wav:
            schema:
              type: string
              format: binary
      responses:
        200:
          description: Transcription result

  /api/v1/voice/synthesize:
    post:
      summary: Convert text to speech
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                text:
                  type: string
                voice:
                  type: string
      responses:
        200:
          description: Audio file
          content:
            audio/wav:
              schema:
                type: string
                format: binary
```

---

## Database Schema

### PostgreSQL (Cloud - Users, Analytics)

```sql
-- Users and authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Query history for analytics
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    question TEXT NOT NULL,
    answer TEXT,
    confidence VARCHAR(20),
    patient_context_used BOOLEAN DEFAULT FALSE,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document registry
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    doc_type VARCHAR(50) NOT NULL,
    source VARCHAR(255),
    chunk_count INTEGER,
    file_hash VARCHAR(64),
    ingested_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

### SQLite (Local - Patient Data, Offline Cache)

```sql
-- Sync with EMR patient table
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    emr_id INTEGER UNIQUE,  -- Link to EMR
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    phone TEXT,
    last_synced TIMESTAMP
);

-- Offline query cache
CREATE TABLE query_cache (
    id INTEGER PRIMARY KEY,
    question_hash TEXT UNIQUE,
    answer TEXT,
    citations TEXT,  -- JSON
    cached_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Local settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    CLOUD TIER (AWS/GCP)                      │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │   │  API Server  │  │  Qdrant      │  │  PostgreSQL  │      │   │
│  │   │  (FastAPI)   │  │  (Vectors)   │  │  (Users)     │      │   │
│  │   │  Auto-scale  │  │  Managed     │  │  RDS         │      │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  │                                                               │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │   │  Neo4j       │  │  Redis       │  │  S3          │      │   │
│  │   │  (Graph)     │  │  (Cache)     │  │  (Documents) │      │   │
│  │   │  AuraDB      │  │  ElastiCache │  │              │      │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              │ HTTPS / WebSocket                     │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    LOCAL TIER (Doctor's Device)              │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │   │  Dora App    │  │  Ollama      │  │  ChromaDB    │      │   │
│  │   │  (Flet UI)   │  │  (Local LLM) │  │  (Local Vec) │      │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  │                                                               │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │   │  SQLite      │  │  Whisper     │  │  Piper       │      │   │
│  │   │  (Patient)   │  │  (STT)       │  │  (TTS)       │      │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  │                              │                                │   │
│  │                              ▼                                │   │
│  │   ┌──────────────────────────────────────────────────────┐   │   │
│  │   │                 DocAssist EMR                         │   │   │
│  │   │                 (Shared SQLite)                       │   │   │
│  │   └──────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core RAG (Weeks 1-4)

**Tasks:**
1. Set up project structure with spec-kit
2. Implement medical embeddings (PubMedBERT)
3. Configure Qdrant vector store
4. Build basic query pipeline (no patient context)
5. Implement document ingestion
6. Create simple web UI (Next.js)
7. Ingest 3 core textbooks as initial knowledge base

**Deliverable:** Working web app that answers medical questions with citations

### Phase 2: EMR Integration (Weeks 5-8)

**Tasks:**
1. Implement EMR bridge (sync with DocAssist EMR)
2. Build patient context retrieval
3. Add patient-aware queries
4. Implement drug interaction checking (Neo4j)
5. Create EMR widget (embedded panel)
6. Add prescription suggestions

**Deliverable:** Dora integrated into EMR workflow

### Phase 3: Voice & Offline (Weeks 9-12)

**Tasks:**
1. Implement wake word detection
2. Integrate Whisper STT (local)
3. Integrate Piper TTS (local)
4. Set up Ollama with Qwen 2.5
5. Implement offline query caching
6. Build sync mechanism for intermittent connectivity

**Deliverable:** Voice-enabled, offline-capable Dora

### Phase 4: NotebookLM Features (Weeks 13-16)

**Tasks:**
1. Document upload and Q&A
2. Audio summary generation
3. Guideline update notifications
4. Integrate academic writing tool
5. Export functionality

**Deliverable:** Full NotebookLM-style learning features

---

## Testing Strategy

```python
# Test categories

# 1. Unit tests (pytest)
def test_medical_chunker_preserves_dosing():
    chunker = MedicalChunker()
    text = "Dosing: 500mg BD for 7 days..."
    chunks = chunker.chunk(text, {})
    assert any("500mg BD for 7 days" in c.text for c in chunks)

# 2. Integration tests (real databases)
@pytest.fixture
def real_qdrant():
    client = QdrantClient(url="http://localhost:6333")
    yield client
    client.delete_collection("test_collection")

def test_retrieval_returns_relevant_docs(real_qdrant):
    # Index test documents
    # Query and verify relevance

# 3. Medical accuracy tests
def test_drug_interaction_detection():
    pipeline = MedicalQueryPipeline()
    answer = pipeline.query(
        "Can I give warfarin with aspirin?",
        patient_context=PatientContext(medications=["warfarin"])
    )
    assert "interaction" in answer.warnings[0].lower()

# 4. Offline mode tests
@pytest.mark.offline
def test_query_works_without_internet():
    with network_disabled():
        answer = local_pipeline.query("What is diabetes?")
        assert answer.answer is not None

# 5. Voice tests
def test_wake_word_detection():
    audio = load_test_audio("hey_docassist.wav")
    detected = voice_agent.detect_wake_word(audio)
    assert detected is True
```

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Query accuracy | > 90% | Evaluated by physicians on 100 test questions |
| Retrieval relevance | > 85% | Mean reciprocal rank on medical QA dataset |
| Response latency | < 3s (online), < 5s (offline) | 95th percentile |
| Drug interaction detection | 100% | Test against known interactions |
| Voice recognition accuracy | > 95% | Word error rate on medical terms |
| Offline functionality | 100% | All core features work without internet |

---

*Plan Version: 1.0*
*Last Updated: January 2026*
*Prepared for: DocAssist Dora Development*
