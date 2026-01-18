"""
Script to insert and retrieve records from Weaviate database.
Assumes Weaviate is running on localhost:8090
"""

import weaviate
from weaviate.classes.config import Property, DataType
import json
from datetime import datetime

def connect_to_weaviate(host: str = "localhost", port: int = 8090) -> weaviate.WeaviateClient:
    """
    Connect to Weaviate instance
    
    Args:
        host: Weaviate host address
        port: Weaviate port number
    
    Returns:
        Weaviate client instance
    """
    try:
        client = weaviate.connect_to_local(
            host=host,
            port=port
        )
        print(f"Connected to Weaviate at {host}:{port}")
        return client
    except Exception as e:
        print(f"Failed to connect to Weaviate: {e}")
        raise


def create_class_schema(client: weaviate.WeaviateClient) -> None:
    """
    Create a Document class schema in Weaviate
    """
    try:
        # Delete class if it exists
        try:
            client.collections.delete("Document")
            print("Existing Document class deleted")
        except:
            pass
        
        # Create new collection with properties
        client.collections.create(
            name="Document",
            description="A document for RAG system",
            properties=[
                Property(name="title", data_type=DataType.TEXT),
                Property(name="content", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="created_at", data_type=DataType.TEXT),
                Property(name="category", data_type=DataType.TEXT),
            ]
        )
        print("Document collection created successfully")
    except Exception as e:
        print(f"Error creating schema: {e}")


def insert_records(client: weaviate.WeaviateClient) -> None:
    """
    Insert sample records into Weaviate
    """
    sample_documents = [
        {
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            "source": "llm_introduction.txt",
            "category": "AI/ML",
            "created_at": datetime.now().isoformat()
        },
        {
            "title": "RAG System Guide",
            "content": "Retrieval-Augmented Generation (RAG) is a technique that combines retrieval of relevant documents with generation to produce more accurate and informed responses.",
            "source": "rag_guide.txt",
            "category": "RAG",
            "created_at": datetime.now().isoformat()
        },
        {
            "title": "Transformers Architecture",
            "content": "The Transformer architecture, introduced in 2017, revolutionized NLP with its self-attention mechanism allowing parallel processing of sequences.",
            "source": "transformers_guide.txt",
            "category": "Deep Learning",
            "created_at": datetime.now().isoformat()
        },
        {
            "title": "Vector Embeddings",
            "content": "Vector embeddings are numerical representations of text that capture semantic meaning and enable similarity-based search and retrieval.",
            "source": "embeddings.txt",
            "category": "NLP",
            "created_at": datetime.now().isoformat()
        },
        {
            "title": "Knowledge Graph Construction",
            "content": "Knowledge graphs organize information into structured relationships, enabling advanced reasoning and entity-based retrieval systems.",
            "source": "knowledge_graph.txt",
            "category": "Knowledge Representation",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    print(f"\nInserting {len(sample_documents)} documents...")
    
    try:
        collection = client.collections.get("Document")
        
        for i, doc in enumerate(sample_documents, 1):
            try:
                collection.data.insert(properties=doc)
                print(f"✓ Inserted document {i}: {doc['title']}")
            except Exception as e:
                print(f"✗ Error inserting document {i}: {e}")
    except Exception as e:
        print(f"Error accessing collection: {e}")


def retrieve_all_records(client: weaviate.WeaviateClient) -> None:
    """
    Retrieve all records from Weaviate
    """
    print("\n" + "="*60)
    print("RETRIEVING ALL DOCUMENTS")
    print("="*60)
    
    try:
        collection = client.collections.get("Document")
        response = collection.iterator()
        
        documents = list(response)
        print(f"\nTotal documents retrieved: {len(documents)}\n")
        
        for i, obj in enumerate(documents, 1):
            print(f"Document {i}:")
            print(f"  ID: {obj.uuid}")
            properties = obj.properties
            print(f"  Title: {properties.get('title', 'N/A')}")
            print(f"  Source: {properties.get('source', 'N/A')}")
            print(f"  Category: {properties.get('category', 'N/A')}")
            content = properties.get('content', 'N/A')
            content_preview = content[:100] + "..." if len(content) > 100 else content
            print(f"  Content: {content_preview}")
            print()
            
    except Exception as e:
        print(f"Error retrieving documents: {e}")


def search_by_category(client: weaviate.WeaviateClient, category: str) -> None:
    """
    Search documents by category
    """
    print(f"\n" + "="*60)
    print(f"SEARCHING DOCUMENTS BY CATEGORY: {category}")
    print("="*60)
    
    try:
        from weaviate.classes.query import Filter
        collection = client.collections.get("Document")
        
        response = collection.query.fetch_objects(
            limit=100,
            filters=Filter.by_property("category").equal(category)
        )
        
        if not response or not response.objects:
            print(f"No documents found with category: {category}")
            return
        
        print(f"\nDocuments found: {len(response.objects)}\n")
        
        for obj in response.objects:
            properties = obj.properties
            print(f"  • {properties.get('title', 'N/A')} ({properties.get('source', 'N/A')})")
            
    except Exception as e:
        print(f"Error searching documents: {e}")


def main():
    """
    Main function to orchestrate database operations
    """
    print("Weaviate Database Operations Script")
    print("="*60)
    
    # Connect to Weaviate
    client = connect_to_weaviate()
    
    try:
        # Create schema
        create_class_schema(client)
        
        # Insert records
        insert_records(client)
        
        # Retrieve all records
        retrieve_all_records(client)
        
        # Search by category
        search_by_category(client, "AI/ML")
        search_by_category(client, "RAG")
        
        print("\n" + "="*60)
        print("Operations completed successfully!")
        print("="*60)
    finally:
        client.close()


if __name__ == "__main__":
    main()
