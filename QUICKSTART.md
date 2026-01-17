# Quick Start Guide - Gemma RAG Engine

## 5-Minute Setup

### Prerequisites ✅
- Ollama installed and running
- Gemma 1B downloaded (`ollama pull gemma`)
- Python 3.14.2 installed
- This repository cloned

### Step 1: Start Ollama (Terminal 1)
```powershell
ollama serve
```

### Step 2: Install Dependencies (Terminal 2)
```powershell
cd c:\Nikhil\Code\gemma-rag-engine-prototype
pip install -r requirements.txt
```

### Step 3: Run the Engine (Terminal 2)
```powershell
python scripts/rag_search.py
```

### Step 4: Start Searching! 🔍
```
[INPUT] Enter your search query (or 'quit' to exit): What is RAG?

# Wait for embeddings to be created (first run only)
# Then see results and AI-generated response
```

## Commands

| Command | Purpose |
|---------|---------|
| Your question | Search the documents |
| `reload` | Reload documents after adding new ones |
| `quit` | Exit the program |

## Useful Queries to Try

```
1. "What are large language models?"
2. "How does retrieval-augmented generation work?"
3. "Explain the transformer architecture"
4. "What is semantic similarity search?"
5. "How does attention mechanism work?"
```

## Add Your Own Documents

1. Place `.txt` or `.pdf` files in `documents/` folder
2. Run `reload` command in the search engine
3. Ask questions about them!

## Common Issues

| Issue | Solution |
|-------|----------|
| "Could not connect to Ollama" | Run `ollama serve` in another terminal |
| "Gemma model not found" | Run `ollama pull gemma` |
| Slow first run | Normal! Creating embeddings takes 5-15 min |
| Low results | Try different query phrasing |

## System Requirements

- **RAM**: Minimum 8GB (16GB recommended)
- **Disk**: 5GB for Gemma model + documents
- **CPU**: Modern multi-core processor
- **GPU**: Optional but faster (NVIDIA/AMD with appropriate drivers)

## Next Steps

1. ✅ Explore with sample documents
2. 📁 Add your own technical documents
3. 🔧 Adjust chunk size and top_k parameters
4. 📊 Analyze result quality
5. 🚀 Integrate into larger system (web UI, API, etc.)

## Performance Expectations

| Operation | Time |
|-----------|------|
| First run (embeddings) | 5-15 minutes |
| Subsequent searches | 10-30 seconds |
| Adding new document | Depends on size |
| Response generation | 5-20 seconds |

---

**Questions?** Check README.md for comprehensive documentation.

**Ready to search?** Run: `python scripts/rag_search.py`
