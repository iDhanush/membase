# -*- coding: utf-8 -*-
"""
Test cases for ChromaKnowledgeBase
"""

import os
import random
import pytest
from typing import List

from membase.knowledge.chroma import ChromaKnowledgeBase
from membase.knowledge.document import Document

@pytest.fixture
def test_dir(tmp_path):
    """Create a temporary directory for testing."""
    return str(tmp_path / "test_chroma_db")


@pytest.fixture
def kb(test_dir):
    """Create a ChromaKnowledgeBase instance for testing."""
    return ChromaKnowledgeBase(
        persist_directory=test_dir,
        membase_account="test_user",
        auto_upload_to_hub=True
        )


@pytest.fixture
def sample_documents() -> List[Document]:
    """Create sample documents for testing."""
    return [
        Document(
            content="The quick brown fox jumps over the lazy dog.",
            metadata={"source": "test1", "date": "2024-01-01"}
        ),
        Document(
            content="A quick brown dog runs in the park.",
            metadata={"source": "test2", "date": "2024-01-02"}
        ),
        Document(
            content="The lazy fox sleeps under the tree.",
            metadata={"source": "test3", "date": "2024-01-03"}
        )
    ]


def generate_random_content() -> str:
    """Generate random content using word combinations."""
    words = [
        "apple", "banana", "orange", "grape", "mango",
        "elephant", "giraffe", "lion", "tiger", "zebra",
        "computer", "phone", "tablet", "laptop", "desktop",
        "mountain", "river", "ocean", "forest", "desert",
        "sun", "moon", "star", "planet", "galaxy"
    ]
    num_words = random.randint(3, 5)
    selected_words = random.sample(words, num_words)
    return " ".join(selected_words)


def test_initialization(test_dir):
    """Test ChromaKnowledgeBase initialization."""
    kb = ChromaKnowledgeBase(persist_directory=test_dir)
    assert os.path.exists(test_dir)
    assert kb._collection_name == "default"
    assert kb._persist_directory == test_dir


def test_add_documents(kb, sample_documents):
    """Test adding documents to the knowledge base."""
    # Test adding a single document
    kb.add_documents(sample_documents[0])
    stats = kb.get_stats()
    assert stats["num_documents"] == 1
    
    # Test adding multiple documents
    kb.add_documents(sample_documents[1:])
    stats = kb.get_stats()
    assert stats["num_documents"] == 3


def test_update_documents(kb, sample_documents):
    """Test updating documents in the knowledge base."""
    # First add documents
    kb.add_documents(sample_documents)
    
    # Verify doc_ids were assigned
    assert all(doc.doc_id is not None for doc in sample_documents)
    
    # Update a single document
    random_content = generate_random_content()
    updated_doc = Document(
        content=random_content,
        metadata={"source": "test1", "date": "2024-01-01", "updated": True},
        doc_id=sample_documents[0].doc_id
    )
    kb.update_documents(updated_doc)
    
    # Verify the update by retrieving with specific content
    results = kb.retrieve(random_content, top_k=1)
    print(results)
    assert len(results) == 1
    assert results[0].content == random_content
    assert results[0].metadata["updated"] is True
    
    # Update multiple documents
    updated_docs = [
        Document(
            content="The dog is now updated with " + random_content,
            metadata={"source": "test2", "date": "2024-01-02", "updated": True},
            doc_id=sample_documents[1].doc_id
        ),
    ]
    kb.update_documents(updated_docs)
    
    # Verify the updates by retrieving with specific content
    results = kb.retrieve(random_content, top_k=2)
    assert len(results) == 2
    # content contains random_content
    assert random_content in results[1].content
    assert all(doc.metadata.get("updated") is True for doc in results)


def test_update_documents_validation(kb):
    """Test validation in update_documents method."""
    # Try to update a document without doc_id
    doc = Document(content="Test content")
    with pytest.raises(ValueError, match="Document must have a valid doc_id for update"):
        kb.update_documents(doc)


def test_retrieve_documents(kb, sample_documents):
    """Test document retrieval functionality."""
    # Add documents
    kb.add_documents(sample_documents)
    
    # Test retrieval with different queries
    results = kb.retrieve("quick brown", top_k=2)
    assert len(results) == 2
    assert any("quick brown" in doc.content.lower() for doc in results)
    
    results = kb.retrieve("lazy", top_k=1)
    assert len(results) == 1
    assert "lazy" in results[0].content.lower()


def test_delete_documents(kb, sample_documents):
    """Test document deletion functionality."""
    # Add documents
    kb.add_documents(sample_documents)
    
    # Delete single document
    kb.delete_documents(sample_documents[0].doc_id)
    results = kb.retrieve("fox", top_k=3)
    assert len(results) < len(sample_documents)
    
    # Delete multiple documents
    kb.delete_documents([doc.doc_id for doc in sample_documents[1:]])
    results = kb.retrieve("fox", top_k=3)
    assert len(results) == 0


def test_clear(kb, sample_documents):
    """Test clearing the knowledge base."""
    # Add documents
    kb.add_documents(sample_documents)
    
    # Clear the knowledge base
    kb.clear()
    
    # Verify it's empty
    stats = kb.get_stats()
    assert stats["num_documents"] == 0


def test_get_stats(kb, sample_documents):
    """Test getting knowledge base statistics."""
    # Add documents
    kb.add_documents(sample_documents)
    
    # Get and verify stats
    stats = kb.get_stats()
    assert stats["num_documents"] == 3
    assert stats["collection_name"] == "default"
    assert "embedding_function" in stats
    assert stats["persist_directory"] == kb._persist_directory


def test_persistence(test_dir, sample_documents):
    """Test knowledge base persistence."""
    # Create and populate first instance
    kb1 = ChromaKnowledgeBase(persist_directory=test_dir)
    kb1.add_documents(sample_documents)
    
    # Create second instance with same directory
    kb2 = ChromaKnowledgeBase(persist_directory=test_dir)
    
    # Verify documents are persisted
    stats = kb2.get_stats()
    assert stats["num_documents"] == 3
    
    # Test retrieval in second instance
    results = kb2.retrieve("quick brown", top_k=2)
    assert len(results) == 2


def test_custom_embedding_function(test_dir):
    """Test using a custom embedding function."""
    class CustomEmbeddingFunction:
        def __call__(self, input: List[str]) -> List[List[float]]:
            # Simple mock embedding function that returns fixed embeddings
            return [[0.1] * 10 for _ in input]
    
    kb = ChromaKnowledgeBase(
        persist_directory=test_dir,
        embedding_function=CustomEmbeddingFunction()
    )
    
    # Add a test document with metadata
    doc = Document(
        content="Test document",
        metadata={"source": "test", "type": "test_doc"}
    )
    kb.add_documents(doc)
    
    # Verify stats show custom embedding function
    stats = kb.get_stats()
    assert "customembeddingfunction" in stats["embedding_function"].lower()


def test_metadata_handling(kb):
    """Test metadata handling in documents."""
    # Create document with metadata
    doc = Document(
        content="Test content",
        metadata={"key": "value", "number": 42}
    )
    
    # Add document
    kb.add_documents(doc)
    
    # Retrieve and verify metadata
    results = kb.retrieve("Test content")
    assert len(results) == 1
    assert results[0].metadata["key"] == "value"
    assert results[0].metadata["number"] == 42 


def test_retrieve_with_similarity_threshold(kb, sample_documents):
    """Test document retrieval with similarity threshold."""
    # Add documents
    kb.add_documents(sample_documents)
    
    # Test retrieval with high similarity threshold
    results = kb.retrieve("quick brown", similarity_threshold=0.8)
    assert len(results) <= 2  # Should only return very similar documents
    
    # Test retrieval with low similarity threshold
    results = kb.retrieve("quick brown", similarity_threshold=0.1)
    assert len(results) >= 2  # Should return more documents
    
    # Test retrieval with zero threshold (default behavior)
    results = kb.retrieve("quick brown", similarity_threshold=0.0)
    assert len(results) == 3  # Should return all matching documents 


def test_find_optimal_threshold(kb, sample_documents):
    """Test finding optimal similarity threshold."""
    # Add documents
    kb.add_documents(sample_documents)
    
    # Test threshold analysis
    analysis = kb.find_optimal_threshold(
        query="quick brown",
        min_threshold=0.3,
        max_threshold=0.9,
        step=0.2
    )
    
    # Verify analysis results
    assert "balanced_threshold" in analysis
    assert "analysis" in analysis
    assert "recommendation" in analysis
    
    # Verify recommendation structure
    recommendation = analysis["recommendation"]
    assert "high_precision" in recommendation
    assert "balanced" in recommendation
    assert "high_recall" in recommendation
    
    # Verify threshold values are in correct range
    assert 0.3 <= recommendation["high_recall"] <= 0.9
    assert 0.3 <= recommendation["balanced"] <= 0.9
    assert 0.3 <= recommendation["high_precision"] <= 0.9 


def test_retrieve_with_filters(kb, sample_documents):
    """Test document retrieval with metadata and content filters."""
    # Add documents
    kb.add_documents(sample_documents)
    
    # Test metadata filter
    results = kb.retrieve(
        query="fox",
        metadata_filter={"source": "test1"}
    )
    assert len(results) == 1
    assert results[0].metadata["source"] == "test1"
    
    # Test content filter
    results = kb.retrieve(
        query="fox",
        content_filter="lazy"
    )
    assert len(results) == 2
    assert all("lazy" in doc.content.lower() for doc in results)
    
    # Test combined filters
    results = kb.retrieve(
        query="fox",
        metadata_filter={"source": "test3"},
        content_filter="lazy"
    )
    assert len(results) == 1
    assert results[0].metadata["source"] == "test3"
    assert "lazy" in results[0].content.lower()
    
    # Test filters with similarity threshold
    results = kb.retrieve(
        query="fox",
        metadata_filter={"source": "test1"},
        similarity_threshold=0.5
    )
    assert len(results) <= 1  # Should only return very similar documents
    
    # Test empty results
    results = kb.retrieve(
        query="fox",
        metadata_filter={"source": "nonexistent"}
    )
    assert len(results) == 0 