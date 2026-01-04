# Medical RAG System Research - State of the Art Repositories

This document catalogs the best open-source repositories and frameworks for building a production-ready RAG system for medical professionals.

---

## 🏆 Top-Tier General RAG Frameworks

### 1. RAGFlow ⭐ HIGHLY RECOMMENDED
**Repository:** https://github.com/infiniflow/ragflow

**Why it stands out:**
- **2,596% YoY growth** in contributors - one of GitHub's fastest-growing open source projects (2025)
- Deep document understanding with complex PDF parsing (tables, layouts, images)
- Production-ready enterprise features
- Supports MinerU & Docling document parsing
- Agent capabilities with memory support
- Multi-source data sync (Confluence, S3, Notion, Google Drive)
- Administrative dashboard for user management

**Best for:** Enterprise deployment with complex medical documents (textbooks, guidelines, research papers)

---

### 2. Dify
**Repository:** https://github.com/langgenius/dify

**Why it stands out:**
- **100,000+ GitHub stars** - top 100 open source projects globally
- Visual workflow builder for AI pipelines
- Built-in RAG pipeline with document ingestion
- 50+ built-in agent tools
- LLMOps monitoring and analytics
- Backend-as-a-Service with full API
- Supports 100s of LLM providers

**Best for:** Rapid prototyping to production with visual interface, great for teams without deep ML expertise

---

### 3. LlamaIndex
**Repository:** https://github.com/run-llama/llama_index

**Why it stands out:**
- **35% boost in retrieval accuracy** in 2025
- 150+ data connectors
- Best-in-class data ingestion toolset
- Specialized indexing for complex document hierarchies
- Excellent for text-heavy, document-centric applications

**Best for:** Medical knowledge management where document hierarchy matters (textbooks organized by chapters, guidelines by sections)

---

### 4. LangChain + LangGraph
**Repository:** https://github.com/langchain-ai/langchain

**Why it stands out:**
- 50K+ integrations
- 3x faster development time
- LangSmith for monitoring and evaluation
- LangGraph for complex reasoning workflows
- Massive community and examples
- Strong agent/tool capabilities

**Best for:** Complex multi-step reasoning, dynamic routing, and advanced agent workflows

---

### 5. Cognita
**Repository:** https://github.com/truefoundry/cognita

**Why it stands out:**
- Modular, production-ready RAG codebase organization
- Easy local testing → production deployment
- Frontend included for testing RAG customizations
- Clean architecture for enterprise use

**Best for:** Teams wanting organized, maintainable RAG codebases

---

### 6. Haystack
**Repository:** https://github.com/deepset-ai/haystack

**Why it stands out:**
- Production-grade pipelines by deepset
- Modular: retrievers, generators, rankers, evaluators
- REST API deployment
- Strong evaluation framework (with Ragas integration)

**Best for:** Teams prioritizing evaluation and iteration on RAG quality

---

## 🏥 Medical-Specific RAG Repositories

### 1. MedRAG Toolkit ⭐ HIGHLY RECOMMENDED
**Repository:** https://github.com/Teddy-XiongGZ/MedRAG

**Why it stands out:**
- Systematic RAG toolkit specifically for medical QA
- **Up to 18% accuracy improvement** over chain-of-thought prompting
- Implements MIRAGE benchmark
- RAG-Gym framework for process supervision (Feb 2025)
- Well-documented, research-backed

**Best for:** Medical question answering with proven benchmarks

---

### 2. Medical-Graph-RAG (ACL 2025)
**Repository:** https://github.com/ImprintLab/Medical-Graph-RAG

**Why it stands out:**
- **Published at ACL 2025** - peer-reviewed research
- Graph-based retrieval for evidence-based medical information
- Multi-level data hierarchy:
  - Private data: MIMIC IV
  - Medium-level: MedC-K (books & papers)
  - Dictionary: UMLS (Unified Medical Language System)
- Structured knowledge representation

**Best for:** Building systems that need structured medical knowledge with citations and evidence trails

---

### 3. MMed-RAG (ICLR 2025)
**Repository:** https://github.com/richard-peng-xia/MMed-RAG

**Why it stands out:**
- **Published at ICLR 2025**
- **Multimodal RAG** - handles medical images + text
- **43.8% factuality improvement** for Medical Vision-Language Models
- Prevents hallucination from incorrect retrievals
- Critical for radiology, pathology, dermatology use cases

**Best for:** Systems requiring medical image analysis alongside text (X-rays, scans, pathology slides)

---

### 4. RAG² (NAACL 2025)
**Repository:** https://github.com/dmis-lab/RAG2

**Why it stands out:**
- **Published at NAACL 2025**
- Rationale-Guided Retrieval
- Filters out distractors, keeps informative snippets
- **Up to 6.1% improvement** on medical QA benchmarks
- Trained filtering model for biomedical contexts

**Best for:** High-precision medical QA where filtering noise is critical

---

### 5. Medical RAG System (IEEE SDS 2025)
**Repository:** https://github.com/slinusc/medical_RAG_system

**Why it stands out:**
- Comprehensive implementation with multiple retrieval methods
- Combines BM25, bioBERT, and hybrid models
- Includes evaluation framework
- Published at IEEE Swiss Conference on Data Science 2025

**Best for:** Research and development with established evaluation

---

### 6. Yale Medical RAG
**Repository:** https://github.com/Yale-BIDS-Chen-Lab/medical-rag

**Why it stands out:**
- From Yale BIDS Chen Lab - academic credibility
- Research-grade implementation

---

### 7. Medical-RAG-LLM (Open Source Stack)
**Repository:** https://github.com/AquibPy/Medical-RAG-LLM

**Why it stands out:**
- Complete open-source stack:
  - BioMistral 7B (main model)
  - PubMedBert (embeddings)
  - Qdrant (vector DB)
  - LangChain + Llama CPP (orchestration)
- Self-hostable, no API dependencies

**Best for:** On-premise deployment with full data privacy (HIPAA considerations)

---

## 🧠 Knowledge Graph + RAG Systems

### 1. Clinical Knowledge Graph (CKG)
**Repository:** https://github.com/MannLabs/CKG

**Why it stands out:**
- **16 million nodes, 220 million relationships**
- Integrates diverse biomedical databases
- Automated knowledge discovery
- Clinical & experimental data integration

**Best for:** Large-scale biomedical knowledge integration

---

### 2. Graph-RAG Resources
**Repository:** https://github.com/DEEP-PolyU/Awesome-GraphRAG

Curated list of GraphRAG papers, benchmarks, and projects

---

## 🗄️ Vector Databases for Medical RAG

| Database | Best For | Key Strength |
|----------|----------|--------------|
| **Milvus** | Enterprise scale (billion vectors) | GPU acceleration, proven at scale |
| **Qdrant** | Self-hosting, hybrid search | Rust-based, ACID-compliant, excellent filtering |
| **Weaviate** | Knowledge graph + vectors | GraphQL, semantic search with structure |
| **Chroma** | Prototyping, small scale | Simple, developer-friendly |

**Recommendation for Medical:** Qdrant or Milvus with hybrid search for combining semantic similarity with structured metadata filtering (e.g., specialty, date of publication, guideline version).

---

## 🧬 Medical Embedding Models

### 1. PubMedBERT Embeddings ⭐ RECOMMENDED
**HuggingFace:** https://huggingface.co/NeuML/pubmedbert-base-embeddings

- 768-dimensional embeddings
- Fine-tuned on PubMed title-abstract pairs
- **Outperforms generalized models** on medical literature

### 2. BioMistral-7B
**HuggingFace:** https://huggingface.co/BioMistral/BioMistral-7B

- Open-source LLM for biomedical domain
- Pre-trained on PubMed Central
- Outperforms other open-source medical models
- ⚠️ Requires alignment for clinical use

### 3. Clinical ModernBERT (2025)
- Extended context: 8,192 tokens
- Trained on PubMed, MIMIC IV, medical ontologies
- Modern architecture (RoPE, Flash Attention)

### 4. SapBERT
- UMLS-aligned embeddings
- Excellent for medical entity linking

---

## 📋 Recommended Architecture for Your Use Case

```
┌─────────────────────────────────────────────────────────────┐
│                    MEDICAL RAG SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐     ┌─────────────────────────────┐   │
│  │  DATA SOURCES   │     │     DOCUMENT PROCESSING      │   │
│  │                 │     │                               │   │
│  │ • Medical Books │────▶│  RAGFlow / Dify              │   │
│  │ • Guidelines    │     │  (PDF parsing, chunking)      │   │
│  │ • Research      │     │                               │   │
│  └─────────────────┘     └──────────────┬───────────────┘   │
│                                          │                   │
│                                          ▼                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 EMBEDDING LAYER                       │    │
│  │                                                       │    │
│  │  PubMedBERT / Clinical ModernBERT                    │    │
│  │  (Domain-specific medical embeddings)                 │    │
│  └─────────────────────────┬─────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              VECTOR DATABASE + KNOWLEDGE GRAPH        │    │
│  │                                                       │    │
│  │  Qdrant/Milvus (vectors) + Neo4j (knowledge graph)   │    │
│  │  Hybrid search with metadata filtering                │    │
│  └─────────────────────────┬─────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              RETRIEVAL & REASONING                    │    │
│  │                                                       │    │
│  │  MedRAG / LlamaIndex / LangChain                     │    │
│  │  Multi-step retrieval, re-ranking, filtering          │    │
│  └─────────────────────────┬─────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    LLM LAYER                          │    │
│  │                                                       │    │
│  │  GPT-4 / Claude / BioMistral-7B (self-hosted)        │    │
│  │  With medical prompt templates                        │    │
│  └─────────────────────────┬─────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  INTERFACE LAYER                      │    │
│  │                                                       │    │
│  │  Dify / Custom UI                                     │    │
│  │  Chat interface with citations & evidence trails      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Recommendations

### Option A: Fastest to Production (Managed)
1. **Dify** for UI + RAG pipeline + agent capabilities
2. **OpenAI/Claude API** for LLM
3. Built-in vector store

### Option B: Full Control (Self-Hosted)
1. **RAGFlow** for document processing
2. **LlamaIndex** for retrieval orchestration
3. **Qdrant** for vector storage
4. **BioMistral-7B** or API-based LLM
5. Custom frontend

### Option C: Research-Grade Medical System
1. **MedRAG toolkit** for proven medical QA
2. **Medical-Graph-RAG** for structured knowledge
3. **PubMedBERT** embeddings
4. **Milvus** at scale
5. UMLS integration for standardized terminology

---

## 📚 Additional Resources

### Awesome Lists
- [Awesome-RAG](https://github.com/Danielskry/Awesome-RAG) - General RAG resources
- [Awesome-GraphRAG](https://github.com/DEEP-PolyU/Awesome-GraphRAG) - Graph-based RAG
- [RAG_Techniques](https://github.com/NirDiamant/RAG_Techniques) - Advanced RAG techniques
- [RAGHub](https://github.com/Andrew-Jang/RAGHub) - Community RAG collection

### Evaluation Frameworks
- [Ragas](https://github.com/explodinggradients/ragas) - RAG evaluation
- MIRAGE Benchmark (via MedRAG)

---

## ⚠️ Important Considerations for Medical AI

1. **Regulatory Compliance:** HIPAA (US), GDPR (EU), local regulations
2. **Hallucination Prevention:** Use RAG² or MMed-RAG techniques
3. **Citation & Traceability:** Always show source documents
4. **Disclaimer:** System should not replace clinical judgment
5. **Update Pipeline:** Regular ingestion of new guidelines
6. **Evaluation:** Continuous monitoring with domain expert review
7. **Data Privacy:** Consider on-premise deployment for patient data

---

## 🎤 Voice Technology for Medical AI

### Chatterbox TTS ⭐ RECOMMENDED
**Repository:** https://github.com/resemble-ai/chatterbox

**Why it stands out:**
- **Beats ElevenLabs** in blind A/B tests (63.75% preference)
- Zero-shot voice cloning from single audio clip
- <200ms latency - suitable for real-time "Hey DocAssist"
- Paralinguistic tags: `[laugh]`, `[cough]` for natural speech
- **MIT License** - fully commercial-friendly
- 23 languages including Hindi

**Models:**
| Model | Parameters | Best For |
|-------|------------|----------|
| Chatterbox-Turbo | 350M | Real-time voice agents |
| Chatterbox-Multilingual | 500M | Multi-language support |

**vs Piper TTS:**
- Chatterbox: Better quality, needs GPU
- Piper: Runs on Raspberry Pi, good for edge/rural

### Speech Recognition (STT)
- **Whisper** (OpenAI): Best accuracy, medical terminology
- **Faster-Whisper**: 4x faster inference
- **Whisper.cpp**: Runs on CPU, good for offline

---

## 📱 LLM Application Patterns

**Repository:** https://github.com/Shubhamsaboo/awesome-llm-apps

**Most relevant patterns for Dora:**

| Pattern | Relevance | Why |
|---------|-----------|-----|
| **Corrective RAG (CRAG)** | ⭐⭐⭐⭐⭐ | Catches hallucinations before doctor sees them |
| **Agentic RAG with Reasoning** | ⭐⭐⭐⭐⭐ | Multi-step diagnostic workflows |
| **Hybrid Search RAG** | ⭐⭐⭐⭐ | Dense + sparse for medical accuracy |
| **Local RAG Agent** | ⭐⭐⭐⭐ | Offline capability (Llama, Deepseek) |
| **Voice RAG Agent** | ⭐⭐⭐⭐ | "Hey DocAssist" integration |
| **Vision RAG** | ⭐⭐⭐ | Medical imaging (X-rays, scans) |

---

*Research compiled: January 2026*
*For: DocAssist Dora - Medical Knowledge Platform*
