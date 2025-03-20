from typing import List, Dict, Any, Optional, Tuple
import re
from collections import Counter
import json

from haystack import Pipeline
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack import Document

from haystack_integrations.components.retrievers.chroma import ChromaQueryTextRetriever
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

class ChromaRAGSystem:
    """
    A RAG (Retrieval-Augmented Generation) system using Haystack and ChromaDB.
    
    This class provides functionality for:
    - Document evaluation and deduplication
    - Document storage and retrieval
    - Similarity-based document filtering
    - Content quality scoring using LLM
    """
    
    def __init__(
        self,
        collection_name: str = "default",
        persist_path: str = "./chroma_db",
    ):
        """
        Initialize the RAG system.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_path: Path to persist the ChromaDB
        """
        print("RAG system initialization...")

        # Initialize document store with embedding function
        self.document_store = ChromaDocumentStore(
            collection_name=collection_name,
            persist_path=persist_path
        )
        
        # Initialize pipeline
        self.pipeline = Pipeline()
        
        # Add components
        self.pipeline.add_component("retriever", ChromaQueryTextRetriever(self.document_store))
        
        # Initialize evaluation pipeline
        # TODO: using local model
        # TODO: summarize before evaluation, incase of long documents or prompt attack
        self.evaluate_pipeline = Pipeline()
        self.evaluate_pipeline.add_component("llm", OpenAIChatGenerator(model="gpt-3.5-turbo"))

        # Keywords that might indicate prompt injection
        self.evaluation_keywords = {
            "relevance", "clarity", "completeness", "originality",
            "score", "evaluation", "quality", "assessment",
            "json", "format", "float", "feedback"
        }

        self.topics = {"web3", "crypto", "btc", "bsc", "eth", 
                    "nft", "defi", "dao", "dapp", "smart contract",
                    "blockchain", "ethereum", "solana", "bitcoin"}

        print("RAG system initialized successfully")
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing unnecessary characters and normalizing whitespace.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text
        """
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def check_self_repetition(self, text: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        Check if text contains significant self-repetition.
        
        Args:
            text: Input text to check
            threshold: Similarity threshold for considering repetition
            
        Returns:
            Tuple of (is_repetitive, repetition_ratio)
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return False, 0.0
        
        # Calculate similarity between consecutive sentences
        total_similarity = 0
        comparisons = 0
        
        for i in range(len(sentences) - 1):
            s1 = sentences[i].lower().split()
            s2 = sentences[i + 1].lower().split()
            
            # Calculate word overlap ratio
            overlap = len(set(s1) & set(s2))
            total = len(set(s1) | set(s2))
            
            if total > 0:
                similarity = overlap / total
                total_similarity += similarity
                comparisons += 1
        
        avg_similarity = total_similarity / comparisons if comparisons > 0 else 0
        return avg_similarity > threshold, avg_similarity
    
    def check_prompt_injection(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check for potential prompt injection attempts.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (is_suspicious, suspicious_phrases)
        """
        text_lower = text.lower()
        suspicious_phrases = []
        
        # Check for evaluation keywords
        for keyword in self.evaluation_keywords:
            if keyword in text_lower:
                suspicious_phrases.append(f"Contains evaluation keyword: {keyword}")
        
        # Check for JSON-like structures
        if re.search(r'\{.*\}', text):
            suspicious_phrases.append("Contains JSON-like structure")
        
        # Check for scoring instructions
        if re.search(r'score|rating|evaluate|quality', text_lower):
            suspicious_phrases.append("Contains scoring instructions")
        
        return len(suspicious_phrases) > 3, suspicious_phrases
    
    def evaluate_content_quality(self, doc: Document) -> Dict[str, float]:
        """
        Evaluate document content quality using OpenAI model.
        
        Args:
            doc: The document to evaluate
            
        Returns:
            Dictionary containing quality scores for different aspects
        """
        content = doc.content
        
        # Prepare evaluation prompt
        evaluation_prompt = f"""
        You are a content quality evaluator. Your task is to evaluate the following text content against a set of predefined topics.

        TARGET TOPICS (DO NOT EVALUATE THIS SECTION):
        {', '.join(sorted(self.topics))}

        TEXT TO EVALUATE:
        {content}

        EVALUATION CRITERIA:
        1. Relevance (how relevant and focused the content is to the target topics)
        2. Clarity (how clear and well-structured the content is)
        3. Completeness (how complete and comprehensive the content is)

        Provide your evaluation in the following JSON format:
        {{
            "relevance_score": float,  # Score between 0-1
            "clarity_score": float,    # Score between 0-1
            "completeness_score": float,  # Score between 0-1
            "feedback": "Brief explanation of your scoring"
        }}

        Note: Only evaluate the TEXT TO EVALUATE section against the TARGET TOPICS.
        """
        
        # Get evaluation from OpenAI
        messages = [ChatMessage.from_user(evaluation_prompt)]
        response = self.evaluate_pipeline.run({"llm": {"messages": messages}})

        try:
            # Parse the response from ChatMessage
            chat_message = response["llm"]["replies"][0]
            evaluation = json.loads(chat_message.text)
            overall_score = evaluation["relevance_score"]*0.6 + evaluation["clarity_score"]*0.2 + evaluation["completeness_score"]*0.2
            evaluation["overall_score"] = overall_score
            print(f"Evaluation: {evaluation}")
            return evaluation
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Error parsing evaluation response: {e}")
            # Fallback to basic metrics if JSON parsing fails
            return self._fallback_quality_evaluation(doc)
    
    def _fallback_quality_evaluation(self, doc: Document) -> Dict[str, float]:
        """
        Fallback method for content quality evaluation using basic metrics.
        
        Args:
            doc: The document to evaluate
            
        Returns:
            Dictionary containing basic quality scores
        """
        content = doc.content
        
        # Calculate basic metrics
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = len(re.split(r'[.!?]+', content))
        
        # Calculate word frequency
        words = content.lower().split()
        word_freq = Counter(words)
        
        # Calculate metrics
        avg_word_length = char_count / word_count if word_count > 0 else 0
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        unique_words_ratio = len(word_freq) / word_count if word_count > 0 else 0
        
        # Calculate quality scores (0-1 range)
        length_score = min(word_count / 100, 1.0)  # Normalize to 100 words
        complexity_score = min(avg_word_length / 8, 1.0)  # Normalize to 8 chars per word
        diversity_score = unique_words_ratio
        
        # Calculate overall quality score
        overall_score = (length_score + complexity_score + diversity_score) / 3
        
        return {
            "overall_score": overall_score,
            "relevance_score": 0.5,  
            "clarity_score": 0.5,
            "completeness_score": 0.5,
            "originality_score": 0.5,
            "feedback": "Using fallback metrics for quality evaluation"
        }
    
    def evaluate_document(
        self,
        doc: Document,
        top_k: int = 1
    ) -> Dict[str, Any]:
        """
        Evaluate a new document using multiple criteria before insertion.
        
        Args:
            doc: The new document to evaluate
            top_k: Number of similar documents to retrieve
            
        Returns:
            Dictionary containing evaluation results
        """
        # Clean and validate text
        cleaned_content = self.clean_text(doc.content)
        
        # Check for self-repetition
        is_repetitive, repetition_ratio = self.check_self_repetition(cleaned_content)
        if is_repetitive:
            return {
                "error": f"Document contains significant self-repetition: {repetition_ratio}",
            }
        
        # Check for prompt injection
        is_suspicious, suspicious_phrases = self.check_prompt_injection(cleaned_content)
        if is_suspicious:
            return {
                "error": f"Potential prompt injection detected: {suspicious_phrases}",
            }
        
        # Create cleaned document
        cleaned_doc = Document(
            content=cleaned_content,
            meta=doc.meta
        )
        
        # Evaluate content quality
        quality_scores = self.evaluate_content_quality(cleaned_doc)
        
        # Query similar documents using embeddings
        results = self.pipeline.run({
            "retriever": {
                "query": cleaned_content,
                "top_k": top_k,
            }
        })
        
        # Handle query results
        similar_docs = results["retriever"]["documents"]
        
        scores = {
            "similarity_scores": [1.0-doc.score for doc in similar_docs],
            "max_similarity": max([1.0-doc.score for doc in similar_docs]) if similar_docs else 0,
            "quality_scores": quality_scores,
            "similar_documents": [
                {
                    "content": doc.content,
                    "score": doc.score,
                    "metadata": doc.meta
                }
                for doc in similar_docs
            ]
        }
        
        return scores
    
    def add_document(
        self,
        doc: Document,
        similarity_threshold: float = 0.8,
        quality_threshold: float = 0.5
    ) -> str:
        """
        Add a document to the system after evaluation.
        
        Args:
            doc: The document to add
            similarity_threshold: Threshold for considering documents as duplicates
            quality_threshold: Minimum required quality score
            
        Returns:
            str: Message indicating if document was added or rejected
        """
        #print(f"Adding document: {doc.content}")
        scores = self.evaluate_document(doc)
        #print(f"Document evaluation scores: {scores}")
        
        if "error" in scores:
            return f"Document rejected: {scores['error']}"
        
        if scores["max_similarity"] > similarity_threshold:
            return f"Document rejected as duplicate: {doc.content}"
        
        if scores["quality_scores"]["overall_score"] < quality_threshold:
            return f"Document rejected due to low quality score: {scores['quality_scores']['overall_score']:.2f}\nFeedback: {scores['quality_scores']['feedback']}"
        
        # Add document directly to document store
        self.document_store.write_documents([doc])
        return f"Document added successfully: {doc.content}\nQuality feedback: {scores['quality_scores']['feedback']}"
    
    def query(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Query documents using the pipeline.
        
        Args:
            query: The query string
            top_k: Number of documents to retrieve
            filters: Optional filters to apply
            
        Returns:
            List of retrieved documents
        """
        results = self.pipeline.run({
            "retriever": {
                "query": query,
                "top_k": top_k,
                "filters": filters or {}
            }
        })
        
        return results["retriever"]["documents"]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the document store.
        
        Returns:
            Dictionary containing store statistics
        """
        stats = {
            "num_documents": self.document_store.count_documents(),
            "collection_name": self.document_store._collection_name,
            "persist_path": self.document_store._persist_path
        }
        return stats

# Example usage
if __name__ == "__main__":
    # Initialize RAG system with OpenAI API key
    rag = ChromaRAGSystem(
        collection_name="test_collection",
    )
    
    # Test document with good quality
    new_doc = Document(
        content="This is a test document with multiple sentences. It contains various words and demonstrates good content quality. The text is well-structured and informative.",
        meta={"name": "new_doc", "source": "test"}
    )
    
    # Add document
    result = rag.add_document(new_doc)
    print(result)
    
    # Test document with poor quality
    new_doc = Document(
        content="DI DI DI DA DAA, blockchain is the future. This is a bad bad test with blockchain web3 sentences. It contains eth and btc words and demonstrates bad content quality.",
        meta={"name": "new_doc", "source": "test"}
    )
    
    # Add document
    result = rag.add_document(new_doc)
    print(result)
    

    results = rag.query("What is the meaning of life?")
    print(f"Query results: {results}")

    # Print stats
    print("\nSystem stats:", rag.get_stats())