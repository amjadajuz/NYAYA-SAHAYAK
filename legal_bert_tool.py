"""
Legal BERT Tool for semantic analysis of Indian legal text.
Uses the law-ai/InLegalBERT model for embeddings and similarity matching.
"""

from transformers import AutoTokenizer, AutoModel
import torch
from typing import List, Dict
import numpy as np

# Global variables to cache the model and tokenizer
_model = None
_tokenizer = None


def _load_model():
    """Load the InLegalBERT model and tokenizer (cached after first load)"""
    global _model, _tokenizer
    
    if _model is None or _tokenizer is None:
        print("Loading InLegalBERT model...")
        _tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
        _model = AutoModel.from_pretrained("law-ai/InLegalBERT")
        _model.eval()  # Set to evaluation mode
        print("✅ InLegalBERT model loaded successfully.")
    
    return _model, _tokenizer


def get_legal_text_embedding(text: str) -> np.ndarray:
    """
    Get embedding representation for a piece of legal text using InLegalBERT.
    
    Args:
        text: The legal text to encode
        
    Returns:
        numpy array representing the text embedding
    """
    model, tokenizer = _load_model()
    
    # Tokenize and encode the text
    encoded_input = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    
    # Generate embeddings
    with torch.no_grad():
        output = model(**encoded_input)
        # Use mean pooling of last hidden state as the sentence embedding
        embeddings = output.last_hidden_state.mean(dim=1).squeeze().numpy()
    
    return embeddings


def analyze_legal_text_similarity(query: str, legal_texts: List[str]) -> str:
    """
    Analyze similarity between a query and multiple legal texts using InLegalBERT.
    Returns the most relevant legal text based on semantic similarity.
    
    Args:
        query: The legal question or text to search for
        legal_texts: List of legal document texts to compare against
        
    Returns:
        A string with the most relevant legal text and similarity score
    """
    if not legal_texts:
        return "Error: No legal texts provided for comparison."
    
    model, tokenizer = _load_model()
    
    # Get query embedding
    query_embedding = get_legal_text_embedding(query)
    
    # Calculate similarity scores for each legal text
    similarities = []
    for text in legal_texts:
        text_embedding = get_legal_text_embedding(text)
        
        # Calculate cosine similarity
        similarity = np.dot(query_embedding, text_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(text_embedding)
        )
        similarities.append(similarity)
    
    # Find the most similar text
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]
    best_text = legal_texts[best_idx]
    
    result = f"Most relevant legal text (similarity: {best_score:.4f}):\n\n{best_text}"
    return result


def extract_legal_concepts(text: str) -> str:
    """
    Extract legal concept embeddings from text using InLegalBERT.
    This can be used to understand the legal concepts present in a document.
    
    Args:
        text: The legal text to analyze
        
    Returns:
        A string describing the embedding characteristics
    """
    embedding = get_legal_text_embedding(text)
    
    result = f"""Legal Text Analysis using InLegalBERT:
- Text length: {len(text)} characters
- Embedding dimension: {len(embedding)}
- Embedding norm: {np.linalg.norm(embedding):.4f}
- Top 5 strongest features: {np.argsort(embedding)[-5:][::-1].tolist()}

This embedding can be used for:
1. Semantic similarity comparison with other legal texts
2. Legal document classification
3. Finding similar case laws
4. Identifying relevant legal statutes
"""
    return result


# Simple wrapper function for use as an agent tool
def search_similar_legal_text(query: str, context: str) -> str:
    """
    Search for relevant information in legal text using semantic similarity.
    
    This tool uses InLegalBERT (trained on Indian legal corpus) to understand
    the semantic meaning of legal text and find the most relevant parts.
    
    Args:
        query: The legal question or search query
        context: Legal text or document to search within (can contain multiple
                paragraphs separated by newlines)
        
    Returns:
        The most relevant portion of the legal text based on semantic similarity
    """
    if not context:
        return "Error: No legal context provided to search."
    
    # Split context into paragraphs or sections
    sections = [s.strip() for s in context.split('\n\n') if s.strip()]
    
    if len(sections) == 1:
        # If only one section, just analyze it
        return extract_legal_concepts(sections[0])
    
    # If multiple sections, find most similar
    return analyze_legal_text_similarity(query, sections)
