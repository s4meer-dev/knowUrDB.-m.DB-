# MongoDB Document RAG & Vector Search

## 1. Ingestion & Chunking (`DocumentProcessor`)

Located in `backend/app/services/document_processor.py`, unstructured documents (`.pdf`, `.md`, `.txt`) undergo a 5-stage pipeline:
1. **Extraction**: Pages are extracted via `PyPDF2` (for PDFs) or Markdown section grouping (merging `#` headings with their body paragraphs).
2. **Overlapping Chunking**: Text is segmented into 550-character semantic windows with an 80-character sliding overlap.
3. **Dense Vector Embedding**: `_compute_vector_embedding()` generates a deterministic **128-dimensional L2-normalized vector** using token and character-trigram signed feature hashing.
4. **MongoDB Persistence**: Chunks and their `embedding` arrays are stored in `_sys_document_chunks`.
5. **Hybrid Retrieval**: `search()` computes the weighted combination of **Cosine Similarity (`0.55`)** and **Lexical Keyword Coverage (`0.45`)** to return the top-$k$ passages with page citations.
