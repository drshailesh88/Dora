# Dora - DocAssist Medical Knowledge Platform

**The UpToDate Killer** - A premium medical knowledge platform that doctors love to use.

## Features

- 🔍 **Hybrid RAG** - Dense (PubMedBERT) + Sparse (BM25) + Neural Reranking
- 🏥 **Medical-Optimized** - Purpose-built for clinical decision support
- 📱 **Offline-First** - Works without internet using local LLMs
- 🗣️ **Voice Interface** - "Hey DocAssist" hands-free queries
- 🔗 **EMR Integration** - Seamless integration with DocAssist EMR
- 💰 **Affordable** - ₹999/month vs UpToDate's ₹46,000/year

## Quick Start

### 1. Install Dependencies

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Dora
uv pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services

```bash
# Start Qdrant (vector database)
docker-compose up -d qdrant

# Start Ollama (local LLM)
ollama serve &
ollama pull qwen2.5:7b
```

### 4. Ingest Documents

```bash
python main.py ingest ./medical_books/ --type textbook
```

### 5. Query

```bash
# CLI
python main.py query "What is the first-line treatment for type 2 diabetes?"

# API Server
python main.py serve
# Then: curl -X POST http://localhost:8000/api/v1/query -H "Content-Type: application/json" -d '{"question": "..."}'
```

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     DORA QUERY PIPELINE                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Query → Multi-Query → HyDE → Dense + Sparse → RRF Fusion      │
│                                                                 │
│        → Cohere Rerank → LLM Synthesis → Citations              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
src/
├── core/           # Configuration, models, main pipeline
├── embeddings/     # PubMedBERT medical embeddings
├── retrieval/      # Dense, sparse, fusion, reranking
├── ingestion/      # Document parsing and chunking
├── llm/            # LLM synthesis and query expansion
├── api/            # FastAPI backend
├── voice/          # Voice agent (coming soon)
└── ui/             # Desktop UI (coming soon)
```

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy src/

# Linting
ruff check src/
```

## Related Projects

- [DocAssist EMR](https://github.com/drshailesh88/emr) - Electronic Medical Records
- [Academic Writing](https://github.com/drshailesh88/cursor_for_academic_writing) - AI-powered research writing
- [Practice Manager](https://github.com/drshailesh88/appointment_system) - Appointment scheduling

## License

Proprietary - All rights reserved.

---

*Built with ❤️ by DocAssist*
