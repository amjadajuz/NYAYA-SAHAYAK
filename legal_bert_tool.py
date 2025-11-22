"""
Legal BERT Tool for semantic analysis of Indian legal text.
This version uses the Hugging Face Inference API instead of a local model.
"""

import os
import requests
import numpy as np
from typing import List, Dict, Any

# --- Hugging Face API Configuration ---
API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/law-ai/InLegalBERT"
HF_TOKEN = os.getenv("HF_TOKEN")
# ------------------------------------


def get_legal_text_embeddings_from_api(texts: List[str]) -> np.ndarray:
    """
    Generates embeddings for a list of legal texts using the Hugging Face Inference API.

    Args:
        texts: A list of strings to be embedded.

    Returns:
        A numpy array of embeddings.
    """
    if not HF_TOKEN:
        raise ValueError("Hugging Face API token not found. Please set HF_TOKEN in your .env file.")

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": texts,
        "options": {"wait_for_model": True}  # Handles cold starts on the API
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Hugging Face API request failed with status {response.status_code}: {response.text}")

    embeddings = response.json()
    if not isinstance(embeddings, list):
        raise TypeError(f"API returned an unexpected type. Expected a list of embeddings, but got: {type(embeddings)}")
        
    return np.array(embeddings)


def analyze_legal_text_similarity(query: str, context_sections: List[str]) -> List[Dict[str, Any]]:
    """
    Analyzes the semantic similarity between a query and a list of context sections
    using embeddings from the Hugging Face API.
    """
    if not context_sections:
        return []

    # Combine query and contexts for a single, efficient API call
    all_texts = [query] + context_sections
    all_embeddings = get_legal_text_embeddings_from_api(all_texts)

    query_embedding = all_embeddings[0]
    context_embeddings = all_embeddings[1:]

    # Calculate cosine similarity
    dot_products = np.dot(context_embeddings, query_embedding)
    query_norm = np.linalg.norm(query_embedding)
    context_norms = np.linalg.norm(context_embeddings, axis=1)
    
    # Avoid division by zero if an embedding is all zeros
    if query_norm == 0 or np.any(context_norms == 0):
        similarities = np.zeros(len(context_sections))
    else:
        similarities = dot_products / (query_norm * context_norms)

    results = [
        {"section": section, "similarity": float(sim)}
        for section, sim in zip(context_sections, similarities)
    ]
    return results


def search_similar_legal_text(query: str, legal_context: str) -> str:
    """
    A tool to find the most semantically similar section of a legal text to a given query.
    This tool is ideal for analyzing a document found via search to extract the most relevant part.

    Args:
        query: The user's question or the point to research.
        legal_context: The full legal text or document to be analyzed.

    Returns:
        The most relevant section from the legal_context, along with its similarity score.
    """
    if not legal_context:
        return "Error: No legal context was provided to analyze."

    # Split the context into paragraphs or sections for granular analysis
    context_sections = [p.strip() for p in legal_context.split('\n\n') if p.strip()]
    if not context_sections:
        return "Error: The provided legal context is empty or badly formatted."

    try:
        similarity_results = analyze_legal_text_similarity(query, context_sections)
    except Exception as e:
        return f"Error during API-based similarity analysis: {e}"

    if not similarity_results:
        return "Could not find any relevant sections in the provided text."

    # Find the best match from the results
    best_match = max(similarity_results, key=lambda x: x['similarity'])

    return (
        f"Most Relevant Section (Similarity: {best_match['similarity']:.2f}):\n"
        f"--- \n"
        f"{best_match['section']}"
    )
