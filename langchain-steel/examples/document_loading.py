#!/usr/bin/env python3
"""
Document Loading Example using Steel-LangChain Integration

This example demonstrates document loading functionality for RAG applications.
Note: SteelDocumentLoader is not yet implemented, so this shows the intended usage
and provides mock implementations for testing.

Requirements:
- Set STEEL_API_KEY environment variable  
- Install langchain-steel package
"""

import os
import sys
from typing import List

# Add the parent directory to sys.path so we can import langchain_steel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_steel import SteelScrapeTool, SteelConfig


class MockSteelDocumentLoader:
    """Mock implementation of SteelDocumentLoader for demonstration."""
    
    def __init__(self, urls: List[str], format: str = "markdown", config=None):
        self.urls = urls
        self.format = format
        self.config = config
        self.scraper = SteelScrapeTool(config=config)
    
    def load(self):
        """Load documents from URLs using Steel scraping."""
        print(f"📚 Loading {len(self.urls)} documents in {self.format} format")
        
        documents = []
        for i, url in enumerate(self.urls):
            try:
                print(f"🔄 Loading document {i+1}/{len(self.urls)}: {url}")
                
                # Use SteelScrapeTool to get content
                content = self.scraper.invoke({
                    "url": url,
                    "format": self.format
                })
                
                if isinstance(content, str) and content.strip():
                    # Create a mock document structure
                    document = {
                        "page_content": content,
                        "metadata": {
                            "source": url,
                            "format": self.format,
                            "length": len(content)
                        }
                    }
                    documents.append(document)
                    print(f"✅ Document loaded: {len(content)} characters")
                else:
                    print(f"⚠️  Empty or invalid content from {url}")
                    
            except Exception as e:
                print(f"❌ Failed to load document from {url}: {e}")
        
        print(f"📊 Successfully loaded {len(documents)} documents")
        return documents


def basic_document_loading_example():
    """Demonstrate basic document loading for RAG."""
    print("🔧 Basic Document Loading Example")
    print("=" * 50)
    
    # Check for API key
    api_key = os.environ.get('STEEL_API_KEY')
    if not api_key:
        print("⚠️  Warning: STEEL_API_KEY not set. Using mock configuration.")
    
    # Example URLs for a knowledge base
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://quotes.toscrape.com/"
    ]
    
    try:
        # Note: Using mock loader since SteelDocumentLoader is not implemented yet
        print("📝 Note: Using MockSteelDocumentLoader (SteelDocumentLoader not yet implemented)")
        
        loader = MockSteelDocumentLoader(
            urls=urls,
            format="markdown"  # AI-optimized format
        )
        
        documents = loader.load()
        
        print(f"\n📚 Document Loading Results:")
        print(f"   Total documents: {len(documents)}")
        
        for i, doc in enumerate(documents):
            print(f"\n📄 Document {i+1}:")
            print(f"   Source: {doc['metadata']['source']}")
            print(f"   Length: {doc['metadata']['length']} characters")
            print(f"   Format: {doc['metadata']['format']}")
            
            # Show preview
            content_preview = doc['page_content'][:200] + "..." if len(doc['page_content']) > 200 else doc['page_content']
            print(f"   Preview: {content_preview}")
        
    except Exception as e:
        print(f"❌ Document loading failed: {e}")


def advanced_document_loading_example():
    """Demonstrate advanced document loading with configuration."""
    print("\n🔧 Advanced Document Loading Example")
    print("=" * 50)
    
    # Advanced configuration
    try:
        config = SteelConfig(
            default_format="markdown",
            session_timeout=60
        )
        
        print("✅ Advanced configuration created")
        
        # Load documents with advanced options
        urls = [
            "https://quotes.toscrape.com/",
            "https://httpbin.org/html"
        ]
        
        loader = MockSteelDocumentLoader(
            urls=urls,
            format="markdown",
            config=config
        )
        
        documents = loader.load()
        
        # Simulate document processing for RAG
        print(f"\n🧠 Processing documents for RAG application:")
        
        total_chars = sum(len(doc['page_content']) for doc in documents)
        avg_length = total_chars / len(documents) if documents else 0
        
        print(f"   Total content: {total_chars:,} characters")
        print(f"   Average length: {avg_length:.0f} characters per document")
        print(f"   Formats: {set(doc['metadata']['format'] for doc in documents)}")
        
        # Show chunking strategy recommendation
        if avg_length > 1000:
            print("💡 Recommendation: Consider chunking documents for better RAG performance")
        else:
            print("💡 Documents are appropriately sized for RAG")
        
    except Exception as e:
        print(f"❌ Advanced document loading failed: {e}")


def rag_pipeline_simulation():
    """Simulate a complete RAG pipeline setup."""
    print("\n🔧 RAG Pipeline Simulation")
    print("=" * 50)
    
    print("🔄 Simulating RAG pipeline with Steel document loading...")
    
    # Step 1: Document Loading
    print("\n1️⃣ Document Loading Phase")
    urls = ["https://example.com"]
    
    try:
        loader = MockSteelDocumentLoader(urls=urls, format="markdown")
        documents = loader.load()
        print(f"   ✅ Loaded {len(documents)} documents")
        
        # Step 2: Document Processing (simulation)
        print("\n2️⃣ Document Processing Phase")
        processed_chunks = []
        
        for doc in documents:
            content = doc['page_content']
            # Simulate chunking (simple word-based)
            words = content.split()
            chunk_size = 100
            
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                chunk_data = {
                    'content': chunk,
                    'source': doc['metadata']['source'],
                    'chunk_id': f"{doc['metadata']['source']}_{i//chunk_size}"
                }
                processed_chunks.append(chunk_data)
        
        print(f"   ✅ Created {len(processed_chunks)} chunks")
        
        # Step 3: Vector Storage (simulation)
        print("\n3️⃣ Vector Storage Phase (simulated)")
        print(f"   ✅ Would store {len(processed_chunks)} vectors")
        
        # Step 4: Query Processing (simulation)
        print("\n4️⃣ Query Processing Phase (simulated)")
        sample_query = "What is the main content?"
        print(f"   Sample query: '{sample_query}'")
        print("   ✅ Would retrieve relevant chunks and generate response")
        
        print("\n🎯 RAG Pipeline simulation completed successfully!")
        print("💡 This demonstrates how Steel document loading integrates with RAG workflows")
        
    except Exception as e:
        print(f"❌ RAG pipeline simulation failed: {e}")


def batch_loading_example():
    """Demonstrate efficient batch document loading."""
    print("\n🔧 Batch Loading Example")
    print("=" * 50)
    
    # Simulate loading multiple document types
    document_sets = {
        "websites": [
            "https://example.com",
            "https://httpbin.org/html"
        ],
        "documentation": [
            "https://quotes.toscrape.com/"
        ]
    }
    
    all_documents = []
    
    for doc_type, urls in document_sets.items():
        print(f"\n📁 Loading {doc_type} documents...")
        
        try:
            loader = MockSteelDocumentLoader(
                urls=urls,
                format="markdown"
            )
            
            documents = loader.load()
            
            # Add document type to metadata
            for doc in documents:
                doc['metadata']['document_type'] = doc_type
            
            all_documents.extend(documents)
            print(f"   ✅ Loaded {len(documents)} {doc_type} documents")
            
        except Exception as e:
            print(f"   ❌ Failed to load {doc_type}: {e}")
    
    # Summary
    print(f"\n📊 Batch Loading Summary:")
    print(f"   Total documents: {len(all_documents)}")
    
    by_type = {}
    for doc in all_documents:
        doc_type = doc['metadata']['document_type']
        by_type[doc_type] = by_type.get(doc_type, 0) + 1
    
    for doc_type, count in by_type.items():
        print(f"   {doc_type}: {count} documents")
    
    print("\n🎯 Batch loading completed!")


def main():
    """Run all document loading examples."""
    print("🚀 Steel-LangChain Document Loading Examples")
    print("=" * 60)
    
    print("📝 Note: These examples use MockSteelDocumentLoader since")
    print("         SteelDocumentLoader is not yet implemented.")
    print("         The patterns shown here represent the intended API.\n")
    
    try:
        # Run examples
        basic_document_loading_example()
        advanced_document_loading_example()
        rag_pipeline_simulation()
        batch_loading_example()
        
        print("\n✅ All document loading examples completed!")
        print("\n💡 Next steps:")
        print("   - Implement actual SteelDocumentLoader class")
        print("   - Add vector database integration")
        print("   - Test with real RAG applications")
        print("   - Optimize chunking strategies")
        
    except KeyboardInterrupt:
        print("\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        raise


if __name__ == "__main__":
    main()