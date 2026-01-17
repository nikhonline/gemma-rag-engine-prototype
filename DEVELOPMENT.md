# Development & Testing Guide

## Project Setup for Development

### Clone and Setup
```powershell
cd c:\Nikhil\Code\gemma-rag-engine-prototype
git clone <repo-url> .
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Verify Setup
```powershell
python --version  # Should be 3.14.2+
ollama list       # Should show gemma
python scripts/rag_search.py  # Should start successfully
```

## Testing Guide

### Manual Testing Checklist

#### 1. Connection Tests
```powershell
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test model availability
python -c "import requests; print(requests.get('http://localhost:11434/api/tags').json())"
```

#### 2. Document Loading Tests
```python
# In interactive mode or script
engine = RAGSearchEngine()
engine.load_documents("documents")
print(f"Loaded {len(engine.documents)} documents")
```

#### 3. Embedding Tests
```python
# Test single embedding
engine = RAGSearchEngine()
text = "Test document about transformers"
embedding = engine.get_embedding(text)
print(f"Embedding shape: {embedding.shape}")
print(f"Embedding sample: {embedding[:5]}")
```

#### 4. Chunking Tests
```python
engine = RAGSearchEngine()
engine.load_documents()
chunks = engine.chunk_documents(chunk_size=500, overlap=50)
print(f"Created {len(chunks)} chunks")
for chunk in chunks[:2]:
    print(f"Source: {chunk['source']}")
    print(f"Length: {len(chunk['content'])} chars")
```

#### 5. Search Tests
```python
engine = RAGSearchEngine()
engine.load_documents()
engine.create_embeddings()

# Test various queries
queries = [
    "What is a transformer?",
    "How does RAG work?",
    "Explain LLM training",
    "What is attention mechanism?"
]

for query in queries:
    results = engine.search(query, top_k=3)
    print(f"Query: {query}")
    print(f"Results: {len(results)}")
    for r in results:
        print(f"  - Similarity: {r['similarity']:.2%}")
```

### Performance Testing

#### Embedding Generation Performance
```python
import time
from pathlib import Path

engine = RAGSearchEngine()
engine.load_documents()
chunks = engine.chunk_documents()

start = time.time()
engine.create_embeddings(force_refresh=True)
elapsed = time.time() - start

print(f"Total time: {elapsed:.2f}s")
print(f"Per chunk: {elapsed/len(chunks):.2f}s")
print(f"Throughput: {len(chunks)/elapsed:.2f} chunks/sec")
```

#### Search Performance
```python
import time

engine = RAGSearchEngine()
engine.load_documents()
engine.create_embeddings()

query = "What is machine learning?"
iterations = 10

times = []
for i in range(iterations):
    start = time.time()
    results = engine.search(query, top_k=5)
    elapsed = time.time() - start
    times.append(elapsed)

print(f"Search performance (n={iterations}):")
print(f"  Average: {sum(times)/len(times):.2f}s")
print(f"  Min: {min(times):.2f}s")
print(f"  Max: {max(times):.2f}s")
```

## Common Test Scenarios

### Scenario 1: Basic Functionality
```
1. Start Ollama
2. Run script
3. Wait for document loading and embedding
4. Enter query: "What is transformer?"
5. Verify results show
6. Verify response generated
✓ PASS if both results and response appear
```

### Scenario 2: Document Reload
```
1. Run script with documents
2. Add new document to documents/ folder
3. Type "reload" command
4. Search for content from new document
✓ PASS if new document content appears in results
```

### Scenario 3: Cache Functionality
```
1. Run script (creates cache)
2. Record first run time
3. Exit and re-run script
4. Record second run time
✓ PASS if second run significantly faster (cache working)
```

### Scenario 4: Empty Query Handling
```
1. Run script
2. Press Enter without entering query
3. Verify appropriate message shown
✓ PASS if error message displayed, no crash
```

### Scenario 5: Large Document Set
```
1. Add 20+ documents
2. Run embeddings
3. Perform searches
✓ PASS if system handles gracefully, no memory errors
```

## Debugging Tips

### Enable Verbose Logging
```python
# In rag_search.py, modify print statements
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Replace print() with logger.debug()/info()
```

### Inspect Embeddings
```python
import pickle
import numpy as np

# Load cache
with open("embeddings/embeddings_cache.pkl", "rb") as f:
    embeddings = pickle.load(f)

# Inspect first embedding
print(f"Number of embeddings: {len(embeddings)}")
print(f"First embedding shape: {embeddings[0]['embedding'].shape}")
print(f"First embedding values: {embeddings[0]['embedding'][:10]}")
print(f"Embedding statistics:")
print(f"  Min: {embeddings[0]['embedding'].min()}")
print(f"  Max: {embeddings[0]['embedding'].max()}")
print(f"  Mean: {embeddings[0]['embedding'].mean()}")
print(f"  Std: {embeddings[0]['embedding'].std()}")
```

### Monitor Ollama
```powershell
# Check Ollama logs
Get-Content $env:APPDATA\ollama\logs\*.log -Tail 100

# Monitor API calls
# In another terminal while running:
$ProgressPreference = 'SilentlyContinue'
while ($true) {
    $stats = curl "http://localhost:11434/api/tags" | ConvertFrom-Json
    $stats
    Start-Sleep -Seconds 5
}
```

### Memory Profiling
```python
import tracemalloc

tracemalloc.start()

# Your code here
engine = RAGSearchEngine()
engine.load_documents()
engine.create_embeddings()

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current/1024/1024:.1f} MB")
print(f"Peak memory: {peak/1024/1024:.1f} MB")
tracemalloc.stop()
```

## Unit Testing Examples

### Test Embedding Generation
```python
def test_embedding_generation():
    engine = RAGSearchEngine()
    text = "Sample text for testing"
    embedding = engine.get_embedding(text)
    
    assert embedding is not None, "Embedding should not be None"
    assert isinstance(embedding, np.ndarray), "Should return numpy array"
    assert len(embedding) > 0, "Embedding should have dimensions"
    assert np.isfinite(embedding).all(), "All values should be finite"
    print("✓ test_embedding_generation passed")

test_embedding_generation()
```

### Test Document Loading
```python
def test_document_loading():
    engine = RAGSearchEngine()
    engine.load_documents()
    
    assert len(engine.documents) > 0, "Should load documents"
    
    for doc in engine.documents:
        assert "source" in doc, "Document should have source"
        assert "content" in doc, "Document should have content"
        assert len(doc["content"]) > 0, "Content should not be empty"
    
    print("✓ test_document_loading passed")

test_document_loading()
```

### Test Similarity Search
```python
def test_similarity_search():
    engine = RAGSearchEngine()
    engine.load_documents()
    engine.create_embeddings()
    
    results = engine.search("transformer", top_k=5)
    
    assert len(results) > 0, "Should return results"
    assert len(results) <= 5, "Should respect top_k"
    
    for result in results:
        assert "similarity" in result, "Result should have similarity"
        assert 0 <= result["similarity"] <= 1, "Similarity should be 0-1"
        assert "metadata" in result, "Result should have metadata"
    
    # Check similarity is sorted descending
    scores = [r["similarity"] for r in results]
    assert scores == sorted(scores, reverse=True), "Results should be sorted"
    
    print("✓ test_similarity_search passed")

test_similarity_search()
```

## Continuous Integration Ideas

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.14.2'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Setup Ollama
        run: |
          # Setup ollama in CI
          ollama pull gemma
      - name: Run tests
        run: python -m pytest tests/
```

## Optimization Opportunities

1. **Embedding Caching**: ✓ Already implemented
2. **Batch Embeddings**: Generate multiple embeddings per request
3. **Query Optimization**: Query rewriting and expansion
4. **Result Reranking**: Use cross-encoders for better ranking
5. **Asynchronous Processing**: Non-blocking embedding generation
6. **Vector Database**: Use proper vector DB instead of in-memory
7. **GPU Acceleration**: Utilize GPU for embeddings

## Known Limitations

1. **Embedding Speed**: Sequential processing (could be batched)
2. **Memory Usage**: All embeddings in memory (could use DB)
3. **Single Model**: Only Gemma supported (could add multiple)
4. **No Persistence**: Embeddings lost on restart (mitigated by cache)
5. **Scale**: ~1000 documents practical limit (need vector DB for more)

## Contributing Guidelines

1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Make changes and test thoroughly
4. Run all test scenarios
5. Submit pull request with description

## Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Version bumped
- [ ] Cache cleaned
- [ ] Performance benchmarked
- [ ] Changelog updated
- [ ] Tagged in git

---

**Last Updated**: January 17, 2026
