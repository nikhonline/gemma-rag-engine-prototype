"""
RAG (Retrieval-Augmented Generation) Search Engine using Ollama and Gemma
This script implements a vector-based search against local documents using embeddings.
"""

import os
import json
import pickle
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime

# Try importing required libraries
try:
    import requests
    import PyPDF2
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests PyPDF2")
    import requests
    import PyPDF2


class RAGSearchEngine:
    """
    Retrieval-Augmented Generation Search Engine using Ollama
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "gemma"):
        """
        Initialize the RAG search engine
        
        Args:
            ollama_url: URL where Ollama is running
            model: Model name to use (default: gemma)
        """
        self.ollama_url = ollama_url
        self.model = model
        self.documents = []
        self.embeddings = []
        self.embeddings_cache = "embeddings/embeddings_cache.pkl"
        self.documents_cache = "embeddings/documents_cache.json"
        
        # Create embeddings directory if it doesn't exist
        Path("embeddings").mkdir(exist_ok=True)
        
        print(f"[INFO] Initializing RAG Search Engine with model: {self.model}")
        print(f"[INFO] Ollama URL: {self.ollama_url}")
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("[✓] Connected to Ollama successfully")
                # Check if gemma model is available
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                if any("gemma" in m for m in models):
                    print("[✓] Gemma model is available")
                else:
                    print("[!] Gemma model not found. Available models:", models)
            else:
                print("[✗] Could not connect to Ollama")
                sys.exit(1)
        except Exception as e:
            print(f"[✗] Error connecting to Ollama: {e}")
            print("[!] Make sure Ollama is running: ollama serve")
            sys.exit(1)
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text using Ollama
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.model, "input": text},
                timeout=30
            )
            if response.status_code == 200:
                embedding = response.json()["embeddings"][0]
                return np.array(embedding)
            else:
                print(f"[✗] Error getting embedding: {response.text}")
                return None
        except Exception as e:
            print(f"[✗] Error in get_embedding: {e}")
            return None
    
    def load_documents(self, doc_dir: str = "documents"):
        """
        Load documents from a directory
        
        Args:
            doc_dir: Directory containing documents (.txt or .pdf files)
        """
        print(f"\n[INFO] Loading documents from '{doc_dir}'...")
        self.documents = []
        doc_path = Path(doc_dir)
        
        if not doc_path.exists():
            print(f"[!] Directory '{doc_dir}' does not exist")
            return
        
        # Load text files
        for txt_file in doc_path.glob("*.txt"):
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.documents.append({
                        "source": txt_file.name,
                        "content": content,
                        "type": "text"
                    })
                    print(f"[✓] Loaded: {txt_file.name}")
            except Exception as e:
                print(f"[✗] Error loading {txt_file.name}: {e}")
        
        # Load PDF files
        for pdf_file in doc_path.glob("*.pdf"):
            try:
                with open(pdf_file, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                    self.documents.append({
                        "source": pdf_file.name,
                        "content": content,
                        "type": "pdf"
                    })
                    print(f"[✓] Loaded: {pdf_file.name}")
            except Exception as e:
                print(f"[✗] Error loading {pdf_file.name}: {e}")
        
        print(f"[INFO] Total documents loaded: {len(self.documents)}")
        self._save_documents_cache()
    
    def chunk_documents(self, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        Split documents into chunks for better embedding
        
        Args:
            chunk_size: Number of characters per chunk
            overlap: Number of overlapping characters between chunks
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        for doc in self.documents:
            content = doc["content"]
            source = doc["source"]
            
            # Split content into chunks
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                if len(chunk.strip()) > 0:
                    chunks.append({
                        "source": source,
                        "content": chunk,
                        "start_idx": i,
                        "type": doc["type"]
                    })
        
        print(f"[INFO] Created {len(chunks)} chunks from documents")
        return chunks
    
    def create_embeddings(self, force_refresh: bool = False):
        """
        Create embeddings for all document chunks
        
        Args:
            force_refresh: If True, ignore cache and recreate embeddings
        """
        # Check if embeddings are cached
        if not force_refresh and self._load_embeddings_cache():
            print("[✓] Loaded embeddings from cache")
            return
        
        print(f"\n[INFO] Creating embeddings for documents...")
        chunks = self.chunk_documents()
        
        if not chunks:
            print("[!] No documents to embed")
            return
        
        self.embeddings = []
        total = len(chunks)
        
        for idx, chunk in enumerate(chunks):
            print(f"[INFO] Processing chunk {idx + 1}/{total}...", end="\r")
            embedding = self.get_embedding(chunk["content"])
            if embedding is not None:
                self.embeddings.append({
                    "metadata": chunk,
                    "embedding": embedding
                })
        
        print(f"\n[✓] Created {len(self.embeddings)} embeddings")
        self._save_embeddings_cache()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for documents relevant to the query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant document chunks with similarity scores
        """
        print(f"\n[INFO] Searching for: '{query}'")
        
        if not self.embeddings:
            print("[!] No embeddings available. Please create embeddings first.")
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            return []
        
        # Calculate similarity scores
        similarities = []
        for emb_data in self.embeddings:
            doc_embedding = emb_data["embedding"]
            # Cosine similarity
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-10
            )
            similarities.append({
                "metadata": emb_data["metadata"],
                "similarity": similarity
            })
        
        # Sort by similarity and get top-k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        results = similarities[:top_k]
        
        print(f"[✓] Found {len(results)} relevant chunks")
        return results
    
    def generate_response(self, query: str, search_results: List[Dict]) -> str:
        """
        Generate a response using the search results and Gemma
        
        Args:
            query: Original query
            search_results: Search results from RAG
            
        Returns:
            Generated response from Gemma
        """
        if not search_results:
            context = "No relevant documents found."
        else:
            context = "\n---\n".join([
                f"Source: {r['metadata']['source']}\n"
                f"Similarity: {r['similarity']:.2%}\n"
                f"Content: {r['metadata']['content'][:300]}..."
                for r in search_results[:3]
            ])
        
        prompt = f"""Based on the following context from technical documents, answer the question.

Context:
{context}

Question: {query}

Answer:"""
        
        print(f"\n[INFO] Generating response using Gemma...")
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60
            )
            if response.status_code == 200:
                return response.json()["response"]
            else:
                print(f"[✗] Error generating response: {response.text}")
                return "Error generating response"
        except Exception as e:
            print(f"[✗] Error in generate_response: {e}")
            return "Error generating response"
    
    def interactive_search(self):
        """Run interactive search loop"""
        print("\n" + "="*60)
        print("RAG Search Engine - Interactive Mode")
        print("="*60)
        print("Commands:")
        print("  - Type your question to search")
        print("  - Type 'reload' to reload documents")
        print("  - Type 'quit' to exit")
        print("="*60 + "\n")
        
        while True:
            try:
                query = input("\n[INPUT] Enter your search query (or 'quit' to exit): ").strip()
                
                if query.lower() == "quit":
                    print("[INFO] Exiting RAG Search Engine. Goodbye!")
                    break
                
                if query.lower() == "reload":
                    self.load_documents()
                    self.create_embeddings(force_refresh=True)
                    print("[✓] Documents reloaded")
                    continue
                
                if not query:
                    print("[!] Please enter a valid query")
                    continue
                
                # Search
                results = self.search(query, top_k=5)
                
                # Display results
                print("\n" + "-"*60)
                print("TOP RESULTS:")
                print("-"*60)
                for i, result in enumerate(results, 1):
                    print(f"\n[{i}] Source: {result['metadata']['source']}")
                    print(f"    Similarity: {result['similarity']:.2%}")
                    print(f"    Content: {result['metadata']['content'][:200]}...")
                
                # Generate response
                response = self.generate_response(query, results)
                print("\n" + "-"*60)
                print("GENERATED RESPONSE:")
                print("-"*60)
                print(response)
                print("-"*60)
                
            except KeyboardInterrupt:
                print("\n[INFO] Search interrupted. Exiting...")
                break
            except Exception as e:
                print(f"[✗] Error during search: {e}")
    
    def _save_embeddings_cache(self):
        """Save embeddings to cache file"""
        try:
            with open(self.embeddings_cache, "wb") as f:
                pickle.dump(self.embeddings, f)
            print(f"[✓] Embeddings cached to {self.embeddings_cache}")
        except Exception as e:
            print(f"[!] Error saving embeddings cache: {e}")
    
    def _load_embeddings_cache(self) -> bool:
        """Load embeddings from cache file"""
        if not Path(self.embeddings_cache).exists():
            return False
        try:
            with open(self.embeddings_cache, "rb") as f:
                self.embeddings = pickle.load(f)
            print(f"[✓] Loaded {len(self.embeddings)} embeddings from cache")
            return True
        except Exception as e:
            print(f"[!] Error loading embeddings cache: {e}")
            return False
    
    def _save_documents_cache(self):
        """Save documents to cache file"""
        try:
            docs_to_save = [
                {k: v for k, v in doc.items() if k != "content"}
                for doc in self.documents
            ]
            with open(self.documents_cache, "w") as f:
                json.dump(docs_to_save, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving documents cache: {e}")


def main():
    """Main entry point"""
    print(f"[INFO] Starting RAG Search Engine at {datetime.now()}")
    
    # Initialize the search engine
    engine = RAGSearchEngine(model="gemma")
    
    # Load documents
    engine.load_documents(doc_dir="documents")
    
    # Create embeddings
    engine.create_embeddings()
    
    # Start interactive search
    engine.interactive_search()


if __name__ == "__main__":
    main()
