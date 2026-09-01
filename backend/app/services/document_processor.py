import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any

from app.services.gemini_provider import GeminiProvider
import numpy as np
import PyPDF2

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles unstructured document text extraction, chunking, and lightweight vector indexing using numpy.
    """
    def __init__(self, ai_provider: GeminiProvider):
        self.ai = ai_provider

    def process_document(self, file_path: str, source_id: str, original_filename: str) -> None:
        """
        Extracts text, chunks it, generates embeddings, and saves to numpy arrays for simple vector search.
        """
        ext = Path(file_path).suffix.lower()
        chunks = []
        
        if ext == ".pdf":
            chunks = self._extract_pdf(file_path, source_id, original_filename)
        elif ext in [".txt", ".md", ".markdown"]:
            chunks = self._extract_text(file_path, source_id, original_filename)
        else:
            raise ValueError(f"Unsupported document type: {ext}")
            
        if not chunks:
            logger.warning(f"No text extracted from document: {original_filename}")
            return
            
        # Generate embeddings in batches of 100 to avoid API limits
        batch_size = 100
        embeddings_list = []
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            texts = [c["text"] for c in batch_chunks]
            try:
                emb = self.ai.generate_embeddings(texts)
                embeddings_list.extend(emb)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch: {e}")
                raise
                
        # Save embeddings and metadata
        source_dir = Path(file_path).parent
        
        embeddings_array = np.array(embeddings_list, dtype=np.float32)
        np.save(source_dir / "embeddings.npy", embeddings_array)
        
        with open(source_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False)

    def search(self, query: str, source_dir: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the vector index in the given source directory for the query.
        """
        source_path = Path(source_dir)
        embeddings_path = source_path / "embeddings.npy"
        metadata_path = source_path / "metadata.json"
        
        if not embeddings_path.exists() or not metadata_path.exists():
            return []
            
        try:
            embeddings_array = np.load(embeddings_path)
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                
            query_emb = self.ai.generate_embeddings([query])[0]
            query_vector = np.array(query_emb, dtype=np.float32)
            
            # Cosine similarity
            dot_product = np.dot(embeddings_array, query_vector)
            norms_db = np.linalg.norm(embeddings_array, axis=1)
            norm_q = np.linalg.norm(query_vector)
            
            # Avoid division by zero
            norms_db[norms_db == 0] = 1e-10
            if norm_q == 0:
                norm_q = 1e-10
                
            similarities = dot_product / (norms_db * norm_q)
            
            # Get top_k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.5: # Relevance threshold
                    result = metadata[idx].copy()
                    result["score"] = float(similarities[idx])
                    results.append(result)
            return results
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []

    def _extract_pdf(self, file_path: str, source_id: str, original_filename: str) -> List[Dict[str, Any]]:
        chunks = []
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text and text.strip():
                        # Semantic chunking by paragraphs (simplified as double newline)
                        paragraphs = text.split("\n\n")
                        for p_idx, p in enumerate(paragraphs):
                            p = p.strip()
                            if len(p) > 20: # Minimum character length
                                chunks.append({
                                    "chunk_id": f"{source_id}_p{page_num+1}_{p_idx}",
                                    "source_id": source_id,
                                    "document_name": original_filename,
                                    "page_number": page_num + 1,
                                    "text": p
                                })
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            raise
        return chunks

    def _extract_text(self, file_path: str, source_id: str, original_filename: str) -> List[Dict[str, Any]]:
        chunks = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                paragraphs = content.split("\n\n")
                for p_idx, p in enumerate(paragraphs):
                    p = p.strip()
                    if len(p) > 20:
                        chunks.append({
                            "chunk_id": f"{source_id}_p{p_idx}",
                            "source_id": source_id,
                            "document_name": original_filename,
                            "page_number": None,
                            "text": p
                        })
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            raise
        return chunks
