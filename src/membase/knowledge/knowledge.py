# -*- coding: utf-8 -*-
"""
Base class for RAG (Retrieval-Augmented Generation) system
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from .document import Document


class KnowledgeBase(ABC):
    """Base class for RAG system."""

    _version: int = 1

    @abstractmethod
    def add_documents(
        self,
        documents: Union[Document, List[Document]],
    ) -> None:
        """
        Add documents to the RAG system's knowledge base.
        
        Args:
            documents (Union[Document, List[Document]]):
                Single document or list of documents to be added.
        """

    @abstractmethod
    def update_documents(
        self,
        documents: Union[Document, List[Document]],
    ) -> None:
        """
        Update existing documents in the knowledge base.
        
        Args:
            documents (Union[Document, List[Document]]):
                Single document or list of documents to be updated.
                Documents must have valid doc_id.
        """

    @abstractmethod
    def delete_documents(
        self,
        document_ids: Union[str, List[str]],
    ) -> None:
        """
        Delete documents from the knowledge base.
        
        Args:
            document_ids (Union[str, List[str]]):
                Single document ID or list of document IDs to delete.
        """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Retrieve relevant documents for a given query.
        
        Args:
            query (str):
                The query string to search for.
            top_k (int):
                Number of most relevant documents to return.
            **kwargs:
                Additional retrieval parameters.
                
        Returns:
            List[Document]:
                List of retrieved documents.
        """

    @abstractmethod
    def generate(
        self,
        query: str,
        context: Optional[List[Document]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response based on the query and optional context.
        
        Args:
            query (str):
                The input query.
            context (Optional[List[Document]]):
                Optional list of relevant documents as context.
            **kwargs:
                Additional generation parameters.
                
        Returns:
            str:
                Generated response.
        """

    @abstractmethod
    def load(
        self,
        path: str,
        **kwargs: Any,
    ) -> None:
        """
        Load the RAG system from a saved state.
        
        Args:
            path (str):
                Path to the saved state.
            **kwargs:
                Additional loading parameters.
        """

    @abstractmethod
    def save(
        self,
        path: str,
        **kwargs: Any,
    ) -> None:
        """
        Save the current state of the RAG system.
        
        Args:
            path (str):
                Path to save the state.
            **kwargs:
                Additional saving parameters.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all data from the RAG system."""

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.
        
        Returns:
            Dict[str, Any]:
                Dictionary containing various statistics.
        """ 