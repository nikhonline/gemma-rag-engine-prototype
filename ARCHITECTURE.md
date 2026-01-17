# System Architecture & Design Document

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Gemma RAG Engine System                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   User Input    │ (Natural Language Query)
│  (CLI / Query)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Query Processing Module                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Input Validation & Normalization                       │ │
│  │ 2. Command Detection (reload, quit)                       │ │
│  │ 3. Query Preparation                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Embedding Generation Module (via Ollama)            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Query Text ─→ [Ollama API] ─→ Gemma 1B ─→ Embedding Vector│ │
│  │ Dimension: Variable (typically 384-1024)                  │ │
│  │ Connection: HTTP POST to localhost:11434/api/embed        │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Vector Similarity Search Module                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Load Cached Embeddings (if exists)                     │ │
│  │ 2. Compute Cosine Similarity: sim = (Q·D)/(||Q||×||D||)  │ │
│  │ 3. Sort by Similarity Score                               │ │
│  │ 4. Retrieve Top-K Results (default: 5)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Results Ranking Module                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ [Result 1] Similarity: 0.87 │ Source: doc.txt             │ │
│  │ [Result 2] Similarity: 0.79 │ Source: doc.txt             │ │
│  │ [Result 3] Similarity: 0.73 │ Source: doc.txt             │ │
│  │ [Result 4] Similarity: 0.68 │ Source: doc.txt             │ │
│  │ [Result 5] Similarity: 0.62 │ Source: doc.txt             │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│             Context Construction & Prompt Build                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Context = Top Results + Metadata                           │ │
│  │ Prompt Template:                                           │ │
│  │   "Based on context: {context}                            │ │
│  │    Answer question: {query}                               │ │
│  │    Answer:"                                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│           LLM Response Generation (via Ollama)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Prompt ─→ [Ollama API] ─→ Gemma 1B ─→ Generated Response  │ │
│  │ Connection: HTTP POST to localhost:11434/api/generate      │ │
│  │ Parameters: Temperature=0.7, Stream=False                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Output Display Module                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ✓ Results with similarity scores and sources              │ │
│  │ ✓ Generated LLM response                                   │ │
│  │ ✓ Processing timestamps and status                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    User Response (CLI Output)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       INITIALIZATION FLOW                         │
└─────────────────────────────────────────────────────────────────┘

File System                      Memory                    External
┌────────────────────────────────────────────────────────────────┐
│ documents/                                                       │
│  ├─ file1.txt ────┐                                             │
│  ├─ file2.txt ─┐  │    Loaded Docs                             │
│  └─ file3.pdf ─┤  │    [{"source": "file1.txt",                │
│                │  └─→ "content": "...", "type": "text"}, ...]  │
│                │                                                 │
│                │    Chunked Docs                               │
│                │    [{"source": "file1.txt",                   │
│                │     "content": "chunk...",                    │
│                │     "start_idx": 0}, ...]                    │
│                │                                                 │
│                │    Get Embeddings via Ollama
│                │    Chunk ──→ Ollama API ──→ Vector (1024-dim)
│                │                                                 │
│                │    Embeddings Array                           │
│                │    [{"metadata": {...},                       │
│                │      "embedding": [0.1, 0.2, ...]}, ...]     │
│                │                                                 │
│                ▼                                                 │
│           embeddings/                                            │
│           ├─ embeddings_cache.pkl ◄──────────── Save Cache    │
│           └─ documents_cache.json ◄──────────── Save Metadata  │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         SEARCH FLOW                               │
└─────────────────────────────────────────────────────────────────┘

User Query         Processing          Retrieval           Response
    │                  │                  │                   │
    ├─→ "What is RAG?"─┤                  │                   │
    │                  │                  │                   │
    │           Query Embedding           │                   │
    │           via Ollama                │                   │
    │                  │                  │                   │
    │            [0.15, 0.82, ...]◄──────┤                   │
    │                  │                  │                   │
    │            Cosine Similarity        │                   │
    │            Compute vs All           │                   │
    │            Embeddings               │                   │
    │                  │                  │                   │
    │                  │    Top-5 Results │                   │
    │                  │    [(score,      ├──→ Format Results │
    │                  │      chunk), ...]│   & Context       │
    │                  │                  │        │          │
    │                  │                  │        └────────→ │
    │                  │                  │    Generate       │
    │                  │                  │    Response       │
    │                  │                  │    via Ollama     │
    │                  │                  │        │          │
    │                  │                  │        └────────→ │
    │                  │                  │      Output       │
    │                  │                  │      Response     │
    │                  │                  │        │          │
    └◄──────────────────────────────────────────────────────────┘
           Display Results & Answer
```

## Module Architecture

```
RAGSearchEngine (Main Class)
│
├─ __init__()
│  ├─ Check Ollama Connection
│  └─ Initialize Configuration
│
├─ Document Loading & Processing
│  ├─ load_documents()
│  ├─ chunk_documents()
│  └─ _save_documents_cache()
│
├─ Embedding Generation
│  ├─ get_embedding()
│  ├─ create_embeddings()
│  ├─ _save_embeddings_cache()
│  └─ _load_embeddings_cache()
│
├─ Search & Retrieval
│  └─ search()
│     ├─ Query Embedding
│     ├─ Cosine Similarity
│     └─ Top-K Selection
│
├─ Response Generation
│  └─ generate_response()
│     ├─ Context Building
│     └─ LLM Call
│
└─ Interactive Interface
   └─ interactive_search()
      ├─ Input Loop
      ├─ Command Handling
      └─ Output Formatting
```

## Data Structures

### Document Object
```python
{
    "source": "filename.txt",
    "content": "full document text...",
    "type": "text|pdf"
}
```

### Chunk Object
```python
{
    "source": "filename.txt",
    "content": "chunk text...",
    "start_idx": 0,
    "type": "text|pdf"
}
```

### Embedding Object
```python
{
    "metadata": {chunk_object},
    "embedding": np.array([0.1, 0.2, ...])  # 1D vector
}
```

### Search Result
```python
{
    "metadata": {chunk_object},
    "similarity": 0.87  # 0.0 to 1.0
}
```

## API Interactions

### Ollama Embedding API

**Request:**
```json
POST http://localhost:11434/api/embed
{
  "model": "gemma",
  "input": "text to embed"
}
```

**Response:**
```json
{
  "embeddings": [[0.1, 0.2, ..., 0.8]]
}
```

### Ollama Generation API

**Request:**
```json
POST http://localhost:11434/api/generate
{
  "model": "gemma",
  "prompt": "Based on context...",
  "stream": false
}
```

**Response:**
```json
{
  "response": "Generated text response...",
  "context": [...],
  "total_duration": 5000000000,
  "load_duration": 1000000000,
  "prompt_eval_count": 50,
  "eval_count": 100
}
```

## Performance Characteristics

### Computational Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Document Loading | O(n) | n = total documents |
| Chunking | O(m) | m = total characters |
| Embedding Creation | O(k) | k = total chunks |
| Similarity Search | O(k·d) | k = chunks, d = embedding dim |
| Response Generation | O(1) | Single LLM call |

### Time Estimates

| Operation | Typical Time | Factors |
|-----------|-------------|---------|
| Load 3 documents | 1-5 sec | File I/O, file sizes |
| Create embeddings (3 docs) | 5-15 min | Network latency, LLM speed |
| Single search | 10-30 sec | Embedding + similarity + generation |
| Response generation | 5-20 sec | LLM processing, response length |

### Memory Requirements

| Component | Estimated Size |
|-----------|----------------|
| Gemma 1B model (Ollama) | 2-3 GB |
| Document cache (JSON) | < 1 MB |
| Embeddings cache (for 1000 chunks) | 1-4 GB |
| Python runtime | 50-200 MB |
| **Total** | **3-8 GB** |

## Caching Strategy

```
First Run (No Cache)
    └─→ Load Documents
        └─→ Create Chunks
            └─→ Generate Embeddings (slow)
                └─→ Save Cache

Subsequent Runs (With Cache)
    └─→ Load Documents
        └─→ Check Cache
            └─→ Load Cache (fast!)
                └─→ Proceed with Search
```

## Error Handling Flow

```
Error Occurs
    │
    ├─→ Connection Error
    │   └─→ Check Ollama running
    │       └─→ Verify network
    │
    ├─→ Model Not Found
    │   └─→ Pull required model
    │       └─→ Retry
    │
    ├─→ File Error
    │   └─→ Check file permissions
    │       └─→ Verify path exists
    │
    └─→ Processing Error
        └─→ Log error details
            └─→ Continue or exit
```

## Security Considerations

1. **Input Validation**: Query length limits
2. **File Access**: Restricted to documents/ folder
3. **Network**: Local only (localhost:11434)
4. **Error Messages**: No sensitive info leaked
5. **Permissions**: File access restrictions

## Scalability Roadmap

### Current (Local, Single Machine)
- Max ~1000 documents efficiently
- ~1000 chunks manageable
- Memory limited

### Phase 2 (Enhanced Local)
- Vector database (FAISS/Qdrant)
- 10,000+ documents
- GPU acceleration

### Phase 3 (Distributed)
- REST API backend
- Multiple Ollama instances
- Web frontend
- 100,000+ documents

---

**Architecture Version**: 1.0  
**Last Updated**: January 17, 2026
