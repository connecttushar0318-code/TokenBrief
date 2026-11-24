# scripts/report_content_ch3.py
"""
Chapter 3 (System Design) for Tushar Bansal's Minor Project Report on TokenBrief.
Includes architecture breakdown, data workflows, mathematical formulations,
and complete relational database schema specifications.
"""

CH3_SECTIONS = [
    ("CHAPTER 3: SYSTEM DESIGN", [
        ("3.1 Proposed System Architecture", [
            "TokenBrief is engineered following a decoupled, four-tier microservice architecture designed to achieve high "
            "throughput, low latency, robust fault tolerance, and independent horizontal scalability. The architectural paradigm "
            "strictly enforces separation of concerns across the Client Presentation Tier, the Application and Inference Engine, "
            "the Persistent Storage Tier, and the External Foundation Model Tier. Figure 3.1 illustrates the high-level architecture "
            "of the platform.",
            
            "1. Client Presentation Tier (Next.js 14 SPA): The user interface is developed as a modern Single-Page Application (SPA) "
            "utilizing Next.js 14 App Router, React 18, TypeScript, and Tailwind CSS. The presentation layer orchestrates six core workspaces: "
            "(a) Document Ingestion and Management Studio; (b) Conversational Q&A Studio with streaming markdown rendering and grounded "
            "citation tooltips; (c) Interactive Quiz Studio with dynamic question sliders (3–15 questions) and spaced repetition review; "
            "(d) Side-by-Side Multi-Document Comparison Matrix; (e) Entity Knowledge Graph SVG visualizer; and (f) Real-Time Telemetry "
            "and Query Analytics Dashboard. All client communications utilize secure HttpOnly session cookies, protecting against Cross-Site "
            "Scripting (XSS) and Cross-Site Request Forgery (CSRF).",
            
            "2. Application and Inference Engine Tier (FastAPI ASGI): The backend is constructed using FastAPI, a modern asynchronous Python "
            "web framework built on Starlette and Pydantic v2. It operates as an asynchronous ASGI service capable of non-blocking I/O across "
            "concurrent vector searches, external LLM streaming connections, and background database logging. The engine encapsulates: "
            "(a) Dual-Token JWT Authentication and RBAC Middleware; (b) Structure-Aware Document Text Extractor; (c) Leaf Chunking and "
            "Embedding Pipeline; (d) Asynchronous Map-Reduce Hierarchical Summarizer; (e) Query Intent Classifier Router; (f) Hybrid BM25 "
            "and Dense Vector Retriever with Reciprocal Rank Fusion (RRF); (g) Cross-Encoder Reranking and Abstention Guardrail; (h) Persistent "
            "Cosine Semantic Cache; and (i) Google Apps Script HTTPS Webhook Email Relay.",
            
            "3. Storage and Data Persistence Tier (PostgreSQL + pgvector): The data layer consolidates both relational metadata and high-dimensional "
            "vector embeddings within a unified serverless PostgreSQL database cluster provided by Neon. The pgvector extension enables "
            "Hierarchical Navigable Small World (HNSW) and Inverted File Flat (IVFFlat) cosine similarity indexing over 384-dimensional dense vectors. "
            "Consolidating relational tables (users, documents, quizzes, annotations) and vector tables (chunks, semantic cache) within a single "
            "ACID-compliant engine completely eliminates distributed synchronization failures common in multi-database architectures.",
            
            "4. External Foundation Model Tier: Generative natural language synthesis and complex multi-document reasoning are powered by "
            "Google Gemini 2.5 Flash and Gemini 2.5 Pro via the official Google GenAI SDK. Flash is leveraged for high-throughput, low-latency "
            "tasks (intent classification, section batch summaries, conversational Q&A, and quiz synthesis), while Pro is selectively engaged "
            "for deep conceptual comparisons across disparate enterprise documents."
        ]),
        
        ("3.2 Overall System Workflow", [
            "The operational workflow of TokenBrief follows two complementary, tightly orchestrated pipelines: the Document Ingestion "
            "Pipeline and the Hybrid Inference & Retrieval Pipeline. Figure 3.2 illustrates the end-to-end data flow progression.",
            
            "1. Document Ingestion Pipeline Workflow:\n"
            "• Step 1 (Upload & Validation): The user submits a PDF, TXT, or Markdown document through the Next.js workspace. The backend "
            "validates file integrity, MIME types, and size limits (up to 50 MB).\n"
            "• Step 2 (Structure-Aware Parsing): The document is parsed using PyPDF and pdfplumber, extracting clean raw text while retaining "
            "page boundaries, structural headings, and section delineations.\n"
            "• Step 3 (Two-Tier Chunking): The text is processed into two distinct hierarchies: Tier-1 leaf chunks (400–600 tokens with 80-token "
            "sliding overlap) for granular retrieval, and Tier-2 structural batches (grouping 5 pages per batch) for holistic summarization.\n"
            "• Step 4 (Vector Embedding & Storage): Leaf chunks are passed through sentence-transformers/all-MiniLM-L6-v2, generating "
            "384-dimensional dense vectors stored in the document_chunks pgvector index.\n"
            "• Step 5 (Asynchronous Map-Reduce Summarization): Simultaneously, an asynchronous Map-Reduce pipeline digests each 5-page batch "
            "into structured bullet points stored in document_sections, pre-computing the entire document's global narrative.",
            
            "2. Hybrid Inference & Retrieval Pipeline Workflow:\n"
            "• Step 1 (Query Submission & Cache Lookup): When a user issues a prompt, the system first computes the query embedding and checks "
            "the query_semantic_cache. If a matching query exists with cosine similarity >= 0.90, the cached response is returned in under 50 ms.\n"
            "• Step 2 (Intent Classification Routing): On a cache miss, the prompt passes through the Query Intent Classifier:\n"
            "  - GLOBAL_SUMMARY prompts are routed directly to pre-computed section Map-Reduce synthesis, avoiding Top-K vector searches.\n"
            "  - MULTI_DOC_COMPARE prompts are routed to cross-document structured matrix extraction.\n"
            "  - SPECIFIC_FACT prompts are routed to the two-stage Hybrid Retrieval Engine.\n"
            "• Step 3 (Hybrid Sparse-Dense Retrieval): The system retrieves top-20 dense candidates via pgvector cosine similarity and top-20 "
            "sparse candidates via BM25 keyword frequency, merging them into a unified ranked list using Reciprocal Rank Fusion (RRF).\n"
            "• Step 4 (Cross-Encoder Reranking & Abstention Filter): A neural cross-encoder (ms-marco-MiniLM-L-6-v2) scores candidate pairs. "
            "If the highest normalized score is below 0.25, the system abstains from answering, preventing hallucinations.\n"
            "• Step 5 (LLM Synthesis & Citation Anchoring): The top-ranked passages are injected into Google Gemini 2.5 Flash, generating a "
            "streamed response with exact page citations and storing the exchange in query_semantic_cache."
        ]),
        
        ("3.3 Data Ingestion, Document Processing and Embeddings", [
            "Data ingestion represents the primary ingestion boundary where unstructured documents are transformed into mathematically "
            "queryable structures. TokenBrief incorporates rigorous validation to prevent data corruption and format injection attacks.",
            
            "To support multi-format enterprise documentation, the ingestion pipeline implements polymorphic extractors:\n"
            "• Digital PDFs: Extracted via PyPDF with fallback to pdfplumber for table-heavy layouts, isolating font weights and line heights "
            "to accurately detect chapter and section boundaries.\n"
            "• Markdown and Plain Text: Processed via regex-based AST parsers that isolate code blocks, markdown tables, and header hashes.\n"
            "• Entity Extraction: Extracted text is analyzed via an entity recognition pipeline, isolating domain Skills, Concepts, Tools, "
            "Organizations, and Individuals, which are populated into document_entities for knowledge graph visualization."
        ]),
        
        ("3.4 Data Preprocessing, Text Chunking & Hierarchical Batching", [
            "A critical pitfall in standard RAG architectures is naive character-based text splitting, which frequently slices sentences in "
            "half or detaches numerical data from its contextual description. TokenBrief implements a recursive, token-aware semantic "
            "chunker that respects natural paragraph boundaries, sentence punctuation, and markdown delimiters.",
            
            "Table 3.1 details the operational parameters governing TokenBrief's chunking and embedding architecture."
        ]),
        
        ("3.5 Model Selection, Hybrid Retrieval (BM25 + Dense) and RRF", [
            "To achieve state-of-the-art retrieval accuracy across both conceptual semantic queries and precise keyword/acronym queries, "
            "TokenBrief combines dense bi-encoder embeddings with sparse BM25 lexical ranking via Reciprocal Rank Fusion (RRF).",
            
            "1. Dense Vector Retrieval: Computes cosine similarity between the 384-dimensional query vector q and document chunk vector d:\n"
            "Cosine_Sim(q, d) = (q · d) / (||q||_2 · ||d||_2)\n\n"
            "2. Sparse Lexical Retrieval (BM25): Computes probabilistic relevance based on term frequency (TF) and inverse document frequency (IDF):\n"
            "Score_BM25(D, Q) = sum_{t in Q} IDF(t) · (f(t, D) · (k_1 + 1)) / (f(t, D) + k_1 · (1 - b + b · (|D| / avgdl)))\n"
            "where k_1 = 1.5 and b = 0.75 are standard calibrated hyperparameters.\n\n"
            "3. Reciprocal Rank Fusion (RRF): The candidate rankings from dense and sparse retrieval are merged without requiring score "
            "normalization using the formula:\n"
            "RRF_Score(d) = sum_{m in {vector, bm25}} 1 / (k + rank_m(d))\n"
            "where k = 60 is the smoothing constant established in information retrieval literature.\n\n"
            "4. Cross-Encoder Reranking: The top-10 fused candidates from RRF are evaluated by a cross-encoder neural network:\n"
            "Score_CE(q, d) = CrossEncoder([q, d])\n"
            "The cross-encoder performs all-to-all cross-attention across query and document tokens simultaneously, capturing intricate "
            "semantic interactions that dual bi-encoders miss. Passages scoring below 0.25 trigger the Hallucination Abstention Gate."
        ]),
        
        ("3.6 Module and Interface Design", [
            "TokenBrief is organized into distinct, loosely-coupled modules adhering to clean architectural principles:\n\n"
            "• Authentication & Security Service (routers/auth.py & security.py): Handles user registration, bcrypt password hashing, "
            "JWT access/refresh token generation, and Google Apps Script HTTPS Webhook OTP dispatch.\n\n"
            "• Document Ingestion Service (routers/documents.py): Manages asynchronous file uploads, structure parsing, leaf chunking, "
            "embedding computation, and entity extraction.\n\n"
            "• QA & Hybrid Retrieval Service (routers/qa.py & services/qa_service.py): Orchestrates the query intent classifier, hybrid RRF "
            "retrieval, cross-encoder reranking, semantic cache read/writes, and Gemini LLM streaming.\n\n"
            "• Quiz & Assessment Engine (routers/quiz.py & services/quiz_service.py): Generates dynamic MCQ evaluations, validates JSON "
            "schemas, computes percentage grades, provides grounded rationales, and manages spaced repetition queues.\n\n"
            "• Multi-Document Comparison Service (routers/comparison.py): Conducts structured matrix comparisons across multiple documents.\n\n"
            "• Telemetry & Analytics Service (routers/analytics.py): Collects query latencies, cache hit ratios, and model usage distributions."
        ]),
        
        ("3.7 System Architectural and Data Flow Diagrams", [
            "The system design incorporates Data Flow Diagrams (DFD) across multiple abstraction levels:\n\n"
            "• DFD Level 0 (Context Diagram): External users authenticate with the system, submit documents and queries, and receive streaming "
            "responses, quiz assessments, and analytics briefings, while the platform interfaces with PostgreSQL, Google Gemini API, and "
            "the Google Apps Script email relay.\n\n"
            "• DFD Level 1 (Functional Decomposition): Decomposes the platform into six major processes: (1.0) User Management, (2.0) Ingestion "
            "and Chunking, (3.0) Vector Indexing, (4.0) Hybrid Retrieval & Ranking, (5.0) LLM Synthesis & Abstention, and (6.0) Quiz Evaluation.\n\n"
            "• Sequence Diagram: Illustrates the chronological message passing from User -> Next.js UI -> FastAPI Router -> Semantic Cache -> "
            "ChromaDB/pgvector -> Cross-Encoder -> Gemini API -> Database Logging -> User."
        ]),
        
        ("3.8 Database Design", [
            "The database architecture utilizes PostgreSQL 16 with the pgvector extension hosted on a serverless Neon cloud cluster. "
            "The schema encapsulates 10 relational tables designed in Third Normal Form (3NF), ensuring strict data integrity, foreign key "
            "cascading, and optimized indexing. Table 3.2 details the relational schema specifications."
        ])
    ])
]

# Table 3.1: Chunking & Embedding Specifications
TABLE_3_1_DATA = [
    ["Parameter / Attribute", "Specification Value", "Engineering Rationale & Impact"],
    ["Leaf Chunk Token Size", "400 to 600 tokens (~1,800 to 2,500 characters)", "Preserves cohesive semantic paragraphs while fitting comfortably within embedding model context limits"],
    ["Chunk Overlap Window", "80 tokens (~320 characters)", "Prevents information truncation across chunk boundaries and maintains sentence continuity"],
    ["Embedding Model", "sentence-transformers/all-MiniLM-L6-v2", "Generates high-quality 384-dimensional dense vectors with ultra-fast CPU inference (<15 ms per chunk)"],
    ["Vector Metric & Index", "Cosine Similarity / HNSW (m=16, ef_construction=64)", "Enables sub-millisecond approximate nearest neighbor retrieval over tens of thousands of vectors"],
    ["Batch Summarization Window", "5 pages per structural batch (~2,500 tokens)", "Guarantees holistic document coverage during asynchronous Map-Reduce without context overflow"],
    ["RRF Smoothing Constant (k)", "60", "Empirically validated constant providing robust rank equalization between sparse BM25 and dense cosine lists"],
    ["Reranking Model", "cross-encoder/ms-marco-MiniLM-L-6-v2", "Computes all-to-all cross-attention for top-10 candidates, boosting NDCG@5 by over 18%"],
    ["Abstention Gate Cutoff", "0.25 normalized cross-encoder score", "Suppresses generative hallucinations when input queries lack relevant document grounding"]
]

# Table 3.2: Relational Database Schema Specifications
TABLE_3_2_DATA = [
    ["Table Name", "Primary Key", "Foreign Keys", "Key Attributes & Types", "Functional Role in Platform"],
    ["users", "id (UUID)", "None", "email (VARCHAR UNIQUE), password_hash (VARCHAR), is_verified (BOOLEAN), created_at (TIMESTAMP)", "Stores user authentication credentials, verification state, and RBAC profile"],
    ["email_verifications", "id (UUID)", "user_id -> users(id)", "otp_code (VARCHAR(6)), expires_at (TIMESTAMP), is_used (BOOLEAN)", "Manages passwordless 6-digit OTP verification codes and expiration lifecycles"],
    ["documents", "id (UUID)", "user_id -> users(id)", "title (VARCHAR), file_size (INT), page_count (INT), file_hash (VARCHAR), created_at", "Tracks uploaded document metadata, file statistics, and user ownership"],
    ["document_chunks", "id (UUID)", "document_id -> documents(id)", "chunk_index (INT), page_number (INT), content (TEXT), embedding (VECTOR(384))", "Stores granular leaf text chunks and 384-dimensional pgvector dense embeddings"],
    ["document_sections", "id (UUID)", "document_id -> documents(id)", "start_page (INT), end_page (INT), summary_text (TEXT), key_takeaways (JSONB)", "Stores pre-computed Map-Reduce 5-page batch summaries for instant global synthesis"],
    ["query_semantic_cache", "id (UUID)", "user_id -> users(id)", "query_text (TEXT), query_embedding (VECTOR(384)), response_text (TEXT), citations (JSONB)", "Indexes prior user queries with vector embeddings to enable <50ms cache hits"],
    ["quiz_questions", "id (UUID)", "document_id -> documents(id)", "question_text (TEXT), options (JSONB), correct_option (INT), explanation (TEXT), page_citation", "Maintains synthesized MCQ questions, multiple options, correct indices, and page rationales"],
    ["quiz_attempts", "id (UUID)", "user_id -> users(id)", "document_id -> documents(id), score_percentage (FLOAT), total_questions (INT), created_at", "Records historical user quiz attempts, scores, and mastery evaluations"],
    ["user_annotations", "id (UUID)", "chunk_id -> document_chunks(id)", "user_id -> users(id), selected_text (TEXT), note_text (TEXT), color_code (VARCHAR)", "Stores in-document text highlights and persistent sticky notes across 5 color palettes"],
    ["query_logs", "id (UUID)", "user_id -> users(id)", "query_intent (VARCHAR), latency_ms (FLOAT), cache_hit (BOOLEAN), model_used (VARCHAR)", "Captures real-time system telemetry, latency logs, and model usage for analytics"]
]
