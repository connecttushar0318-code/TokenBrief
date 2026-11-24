# scripts/report_content_ch1_ch2.py
"""
Chapter 1 (Introduction) and Chapter 2 (Requirement Analysis and System Specification)
for Tushar Bansal's Minor Project Report on TokenBrief.
"""

CH1_SECTIONS = [
    ("CHAPTER 1: INTRODUCTION", [
        ("1.1 Introduction to the Project Domain", [
            "In contemporary corporate, academic, and industrial environments, unstructured textual data represents "
            "over eighty percent of all newly generated enterprise knowledge. Organizations routinely accumulate "
            "thousands of mission-critical documents—ranging from technical system manuals, architectural blueprints, "
            "and legal compliance mandates to financial prospectuses and academic research monographs. Despite massive "
            "investments in electronic archiving, this institutional data frequently settles into disconnected "
            "'information silos', rendering rapid knowledge retrieval, cross-referencing, and cognitive assimilation "
            "exceptionally difficult for knowledge workers, researchers, and students alike.",
            
            "The advent of Large Language Models (LLMs) such as OpenAI GPT-4 and Google Gemini has introduced unprecedented "
            "capabilities in zero-shot text comprehension, natural language synthesis, and reasoning. However, attempting "
            "to deploy foundational LLMs directly upon proprietary enterprise repositories exposes profound operational "
            "vulnerabilities. Foundational models operate over static pre-training corpora bounded by historical temporal cutoffs; "
            "they possess zero native visibility into confidential corporate archives. Furthermore, feeding entire 50-to-100 page "
            "technical documents directly into modern multi-thousand-token context windows incurs catastrophic token processing "
            "costs, induces multi-second latency bottlenecks, and exacerbates the well-documented 'lost-in-the-middle' phenomena "
            "where critical facts placed in deep context regions are systematically neglected.",
            
            "To overcome these limitations, Retrieval-Augmented Generation (RAG) has emerged as the preeminent architectural "
            "paradigm in enterprise artificial intelligence. In a standard RAG pipeline, external unstructured documents are parsed, "
            "segmented into smaller textual fragments (chunks), transformed into high-dimensional dense vector embeddings, and "
            "indexed within a dedicated vector database. When a user submits an analytical query, the system retrieves semantically "
            "relevant chunks via cosine similarity and injects them as an explicit grounding prompt into the LLM context window. "
            "This enables grounded generation without costly model fine-tuning while preserving proprietary access controls.",
            
            "Nonetheless, standard first-generation RAG systems exhibit critical design flaws when confronted with complex, "
            "multi-page technical documentation. They fail to capture holistic narrative continuity, drop specialized keyword "
            "acronyms during dense-only semantic searches, generate costly and redundant API roundtrips for frequent queries, "
            "and completely lack mechanisms for active human cognitive assessment. TokenBrief is engineered to resolve these "
            "systemic deficiencies, delivering an autonomous, multi-agent document intelligence platform equipped with hierarchical "
            "summarization, hybrid sparse-dense retrieval, cross-encoder reranking, semantic caching, and adaptive quiz assessment."
        ]),
        
        ("1.2 Background and Motivation", [
            "The development of TokenBrief is motivated by three pervasive architectural and pedagogical bottlenecks observed "
            "in conventional document intelligence and RAG pipelines across modern enterprise workspaces:\n\n"
            "1. The Top-K Retrieval Trap in Multi-Page Corpora: When an enterprise user requests an overarching executive summary, "
            "a structural comparison, or high-level thematic analysis of a 60-page PDF manual, standard RAG architectures retrieve "
            "only the top 3 to 5 most semantically similar chunks (typically comprising less than 3% of the total document volume). "
            "Consequently, the resulting generated summary reflects an isolated, micro-level fragment rather than an authentic synthesis "
            "of the document's global narrative. To provide true holistic document intelligence, a two-tier hierarchical ingestion "
            "pipeline is required that asynchronously summarizes structural document sections via Map-Reduce algorithms.\n\n"
            "2. Semantic Blur and Lexical Blind Spots: Dense vector embeddings (such as all-MiniLM-L6-v2) excel at capturing "
            "broad conceptual synonyms; however, they frequently exhibit 'semantic blur' when handling exact alphanumerical codes, "
            "part numbers, legal clause citations, or domain-specific acronyms. Conversely, traditional sparse lexical search (such "
            "as BM25) strictly matches exact keywords while failing to capture synonymy. Unifying these complementary paradigms through "
            "Reciprocal Rank Fusion (RRF) and neural cross-encoder reranking is essential to achieve robust enterprise retrieval precision.\n\n"
            "3. The Passive Consumption Deficit and Lack of Active Recall: Existing AI document assistants (e.g., standard PDF "
            "chatbots) remain strictly passive text generators. Cognitive psychology and pedagogy have empirically proven that "
            "passive reading produces rapid knowledge decay, whereas 'active recall' and 'spaced repetition' dramatically elevate long-term "
            "comprehension and retention. TokenBrief addresses this deficit by incorporating an autonomous Quiz Studio that dynamically "
            "synthesizes Multiple Choice Questions (MCQs), provides instantaneous grounded pedagogical rationales, and maintains a "
            "personalized Spaced Repetition queue for continuous evaluation.\n\n"
            "4. Operational Latency and Cloud Email Restrictions: Enterprise RAG queries routinely incur 1,200 ms to 2,500 ms in "
            "end-to-end latency due to dense embedding generation, vector indexing, and generative API synthesis. Deploying a cosine-based "
            "semantic cache mitigates this overhead, answering frequent conceptual queries in under 50 ms. Additionally, deploying modern "
            "authentication pipelines on serverless cloud platforms (such as Render or Vercel) frequently encounters blocked SMTP ports (e.g., "
            "Port 465/587); TokenBrief circumvents this via an asynchronous Google Apps Script HTTPS Webhook email relay, ensuring "
            "frictionless, zero-cost transactional OTP dispatch."
        ]),
        
        ("1.3 Problem Statement", [
            "The overarching objective of this project is to formalize, engineer, benchmark, and deploy a production-grade Document "
            "Intelligence and Adaptive Assessment Platform that resolves the fundamental trade-offs between holistic coverage, lexical "
            "precision, operational latency, and cognitive assessment in unstructured enterprise document processing.\n\n"
            "Specifically, the technical problem decomposes into six critical challenges:\n"
            "• Challenge 1 (Structure Loss in Document Parsing): Transform complex multi-page PDF documents into structurally sound, "
            "metadata-rich text representations while isolating tabular structures, hierarchical headers, and page boundaries.\n"
            "• Challenge 2 (Long-Context Summarization Coverage): Overcome the Top-K retrieval trap by implementing an asynchronous "
            "hierarchical Map-Reduce pipeline that digests multi-page documents into 5-page batch sections, guaranteeing 100% thematic coverage.\n"
            "• Challenge 3 (Hybrid Retrieval Precision): Formulate a dual-stage retrieval engine combining sparse lexical BM25 ranking "
            "and dense HNSW vector similarity via Reciprocal Rank Fusion (RRF), followed by cross-encoder neural reranking.\n"
            "• Challenge 4 (Hallucination Mitigation & Abstention): Establish an automated confidence scoring gate that prevents "
            "erroneous LLM generation when retrieved context similarity falls below a 25% relevance threshold.\n"
            "• Challenge 5 (High-Throughput Semantic Caching): Design an in-memory and database-backed semantic cache that intercepts "
            "semantically equivalent queries (cosine similarity >= 0.90), bypassing LLM inference to minimize costs and slash latency.\n"
            "• Challenge 6 (Cognitive Evaluation & Active Recall): Construct an autonomous pedagogical engine capable of dynamically "
            "synthesizing grounded MCQ assessments with customizable difficulty and question counts, backed by spaced repetition."
        ]),
        
        ("1.4 Objectives of the Project", [
            "To resolve the formulated problem statement, the specific engineering and research objectives of TokenBrief are established as follows:\n\n"
            "1. Hierarchical Map-Reduce Document Summarization: Develop an asynchronous Map-Reduce pipeline utilizing asyncio concurrency "
            "semaphores to digest 50+ page PDF documents into structured section summaries, achieving full-document synthesis in under 3 seconds.\n\n"
            "2. Intent-Driven Hybrid Retrieval Pipeline: Implement an intent-classification router that directs prompts across global summary, "
            "multi-document comparison, or factual search, combining BM25 and dense vector search via Reciprocal Rank Fusion (RRF).\n\n"
            "3. Neural Cross-Encoder Reranking and Abstention Guardrail: Integrate sentence-transformers cross-encoder models to recalibrate "
            "candidate passages and enforce an explicit abstention filter for ungrounded prompts with confidence scores below 0.25.\n\n"
            "4. Low-Latency Semantic Caching: Engineer an embedding-based semantic cache achieving a >40% cache hit ratio under steady-state "
            "enterprise usage, reducing mean query latency from 1,250 ms to under 50 ms.\n\n"
            "5. Interactive Cognitive Quiz Studio: Develop an assessment generation engine allowing users to select 3 to 15 questions, "
            "toggle between Easy, Medium, and Hard difficulty tiers, receive instant citation-backed feedback, and track spaced repetition.\n\n"
            "6. Multi-Document Comparison Matrix and Knowledge Graph: Create automated tools for side-by-side multi-document comparative "
            "matrices and interactive SVG-based entity knowledge graph visualizations.\n\n"
            "7. Production-Grade Microservice Deployment: Architect a decoupled web application comprising a Next.js 14 single-page application "
            "on Vercel, an asynchronous FastAPI backend on Render, serverless PostgreSQL with pgvector on Neon, and Google Apps Script HTTPS Webhook OTP relay."
        ]),
        
        ("1.5 Scope of the Project", [
            "The scope of TokenBrief spans theoretical algorithm design, system architecture, database engineering, user interface "
            "development, rigorous benchmarking, and production cloud deployment:\n\n"
            "1. Functional Scope: The platform provides end-to-end document management, real-time streaming conversational Q&A, "
            "page-level grounded citation highlighting, customizable MCQ quiz generation with instant evaluation, multi-document comparison "
            "matrices, SVG entity knowledge graph exploration, in-document annotation tools, and automated branded PDF export.\n\n"
            "2. Document & Data Scope: The ingestion pipeline supports PDF, Markdown, and plain text files up to 50 MB and 100+ pages per document. "
            "Dense vector embeddings are standardized on 384-dimensional dense representations, with relational telemetry stored in PostgreSQL.\n\n"
            "3. Security & Access Scope: Multi-tenant role-based access control is enforced via HttpOnly SameSite=Strict JSON Web Tokens (JWT), "
            "bcrypt password hashing, rate limiting, and passwordless email verification via Google Apps Script HTTPS Webhook relay.\n\n"
            "4. Boundary Conditions & Exclusions: While TokenBrief provides high-accuracy text extraction from structured digital PDFs, "
            "degraded historical handwritten manuscripts requiring optical character recognition (OCR) pre-processing are outside the "
            "primary algorithmic boundary of the initial release."
        ]),
        
        ("1.6 Organisation of the Report", [
            "This report is structured into six comprehensive chapters, organized according to the prescribed institutional guidelines:\n\n"
            "• Chapter 1 (Introduction): Presents the project domain, enterprise motivation, core technical challenges, objectives, scope, "
            "and structural overview of the report.\n\n"
            "• Chapter 2 (Requirement Analysis and System Specification): Reviews foundational literature in RAG, sparse-dense hybrid "
            "retrieval, and semantic caching; provides a comparative matrix against existing platforms; and details functional, non-functional, "
            "hardware, software, and feasibility requirements.\n\n"
            "• Chapter 3 (System Design): Details the high-level decoupled architecture, end-to-end ingestion and inference workflows, "
            "mathematical formulation of hybrid RRF and cross-encoder reranking, and relational database schemas.\n\n"
            "• Chapter 4 (Implementation, Testing and Maintenance): Explains the technical realization of backend FastAPI services, Next.js 14 "
            "frontend components, prompt engineering templates, verification test cases, and deployment strategies.\n\n"
            "• Chapter 5 (Results and Discussions): Details the experimental setup, quantitative retrieval benchmarks (NDCG@5, MRR), "
            "latency optimization curves, semantic cache hit telemetry, qualitative error analysis, and system limitations.\n\n"
            "• Chapter 6 (Conclusion and Future Scope): Concludes the report with a synthesis of achievements, architectural contributions, "
            "and promising future enhancements, including multimodal document intelligence and agentic tool invocation.\n\n"
            "• References & Appendices: Provides comprehensive IEEE-style academic citations, installation instructions, full-resolution user "
            "interface screenshots, core algorithmic source listings, and official plagiarism certification."
        ])
    ])
]

CH2_SECTIONS = [
    ("CHAPTER 2: REQUIREMENT ANALYSIS AND SYSTEM SPECIFICATION", [
        ("2.1 Introduction", [
            "Requirement analysis forms the critical engineering foundation for architecting an enterprise-grade AI system. "
            "Before embarking on implementation, it is vital to rigorously analyze existing literature, identify structural gaps "
            "in current commercial and academic systems, and establish formal functional and non-functional specifications. "
            "This chapter surveys foundational retrieval paradigms, delineates the limitations of legacy enterprise search and "
            "vanilla RAG architectures, and articulates the comprehensive system specifications governing TokenBrief."
        ]),
        
        ("2.2 Literature Review and Related Work", [
            "The conceptual foundations of TokenBrief intersect four major research domains within modern Natural Language "
            "Processing (NLP) and Information Retrieval (IR):\n\n"
            "1. Retrieval-Augmented Generation (RAG): Lewis et al. (2020) formalized RAG as an end-to-end architecture combining "
            "a pre-trained parametric sequence-to-sequence model with a non-parametric dense vector index. By conditioning generation "
            "on retrieved textual evidence, RAG substantially mitigates hallucination and enables dynamic knowledge updates without "
            "re-training. However, early RAG implementations relied exclusively on single-turn dense retrieval, leading to vulnerability "
            "when handling long-context documents or queries demanding global structural synthesis.\n\n"
            "2. Dense vs. Sparse Lexical Retrieval: Karpukhin et al. (2020) demonstrated that Dense Passage Retrieval (DPR) utilizing "
            "dual-encoder BERT architectures outperforms traditional BM25 on open-domain question answering. Nevertheless, subsequent "
            "empirical studies by Thakur et al. (2021) in the BEIR benchmark revealed that dense retrievers suffer significant out-of-domain "
            "degradation when confronted with specialized terminology, numbers, or acronyms. Cormack et al. (2009) established that "
            "Reciprocal Rank Fusion (RRF) offers a robust, parameter-free mechanism to merge disparate rankings from sparse and dense "
            "retrievers, consistently surpassing individual models.\n\n"
            "3. Two-Stage Retrieval and Cross-Encoder Reranking: Nogueira and Cho (2019) demonstrated that while bi-encoders are "
            "computationally efficient for initial Top-K candidate generation, cross-encoders—which perform full all-to-all cross-attention "
            "between query tokens and passage tokens—deliver dramatically superior ranking precision. Modern production RAG architectures "
            "increasingly adopt a two-stage approach: bi-encoders retrieve candidate passages, and a compact cross-encoder (e.g., "
            "ms-marco-MiniLM-L-6-v2) reranks the candidates prior to context window injection.\n\n"
            "4. Semantic Caching and LLM Cost Optimization: Bang et al. (2023) investigated the economic and computational overhead "
            "of commercial LLM APIs, demonstrating that enterprise workflows exhibit high semantic redundancy. Exact string matching caches "
            "fail to capture paraphrased questions; however, semantic vector caching based on cosine similarity thresholds (typically "
            "0.88 to 0.92) captures paraphrased queries, bypassing LLM inference and slashing latency by over 90%."
        ]),
        
        ("2.3 Limitations of Existing Systems", [
            "An exhaustive analysis of current commercial document search platforms (e.g., Elasticsearch, ChatPDF, NotebookLM, and "
            "standard enterprise LangChain implementations) reveals several recurring engineering deficiencies:\n\n"
            "1. The Top-K Fragment Bias: Existing RAG solutions partition documents into static chunks and retrieve only the top 3–5 "
            "chunks. When an executive asks, 'What are the main risks outlined in this 80-page audit report?', standard systems fail "
            "because the answer is dispersed across dozens of pages that cannot fit into top-5 retrieval.\n\n"
            "2. High Hallucination under Low Relevance: When a user query falls outside the topical boundaries of the uploaded document, "
            "vanilla RAG architectures still retrieve the closest available chunks and force the LLM to generate an answer. Without "
            "an explicit confidence-calibrated abstention threshold, the model hallucinates plausible-sounding but erroneous facts.\n\n"
            "3. Excessive Query Latency & Redundant API Expenses: Every user interaction triggers repeated embedding computations "
            "and expensive LLM calls, even when identical or semantically identical questions ('Summarize section 3' vs. 'Give me an "
            "overview of section 3') have already been answered.\n\n"
            "4. Absence of Pedagogical Assessment: Existing platforms function exclusively as passive Q&A chat interfaces. They provide "
            "no mechanism to verify whether a student, employee, or compliance officer has actually mastered the document content through "
            "interactive evaluation."
        ]),
        
        ("2.4 Proposed System and Requirements", [
            "TokenBrief is designed as an end-to-end, autonomous document intelligence workspace that eliminates each of the "
            "aforementioned limitations. Table 2.1 provides a rigorous comparative analysis of existing enterprise solutions versus "
            "the TokenBrief platform architecture."
        ]),
        
        ("2.5 Functional Requirements", [
            "The functional requirements of TokenBrief dictate the explicit operations, services, and workflows executed by the system:\n\n"
            "• FR-01: User Authentication & Role Management: The system shall provide secure account registration, bcrypt password hashing, "
            "HttpOnly SameSite=Strict JWT session management, and passwordless email OTP verification via Google Apps Script HTTPS Webhook.\n\n"
            "• FR-02: Document Ingestion & Structure Parsing: The system shall parse uploaded PDF, TXT, and Markdown files up to 50 MB, "
            "extracting clean textual passages, preserving page boundaries, generating structural leaf chunks (400–600 tokens), and computing "
            "384-dimensional dense embeddings.\n\n"
            "• FR-03: Asynchronous Hierarchical Map-Reduce Summarization: The system shall divide long documents into 5-page batches, "
            "asynchronously synthesize section summaries via asyncio semaphores, and generate global executive summaries in under 3 seconds.\n\n"
            "• FR-04: Intent-Driven Hybrid Search & RRF: The system shall classify incoming user prompts into GLOBAL_SUMMARY, "
            "MULTI_DOC_COMPARE, or SPECIFIC_FACT intents, fusing dense vector similarity with sparse BM25 scores via Reciprocal Rank Fusion.\n\n"
            "• FR-05: Neural Cross-Encoder Reranking & Abstention Filter: The system shall rerank candidate passages using cross-attention "
            "scores and abstain from generation if peak context similarity falls below 0.25.\n\n"
            "• FR-06: Interactive Quiz Studio & Spaced Repetition: The system shall dynamically generate 3 to 15 MCQ questions with "
            "selectable difficulty (Easy, Medium, Hard), validate JSON schemas, provide immediate citation-backed grading, and maintain "
            "a spaced review queue of incorrectly answered questions.\n\n"
            "• FR-07: Multi-Document Comparison Matrix: The system shall allow simultaneous multi-file analysis, synthesizing a structured "
            "cross-document evaluation matrix with unique and shared concept pills.\n\n"
            "• FR-08: Knowledge Graph Exploration & PDF Export: The system shall extract domain entities, project dynamic SVG network "
            "graphs, allow sticky-note highlighting, and export branded multi-page session briefings via ReportLab."
        ]),
        
        ("2.6 Non-Functional Requirements", [
            "The non-functional requirements define the quality attributes, performance benchmarks, and security constraints of the platform:\n\n"
            "• NFR-01: Response Latency: The system shall achieve a cold-query response latency under 1,500 ms and a warm semantic cache hit "
            "latency under 60 ms.\n\n"
            "• NFR-02: Grounding and Accuracy: Over 90% of factual responses shall include verifiable page-level citation anchors, with "
            "hallucination rates kept strictly below 5% on domain-specific benchmarks.\n\n"
            "• NFR-03: Security & Data Privacy: User authentication cookies must be HttpOnly and SameSite=Strict. All database connections "
            "must enforce TLS 1.3 encryption. Document embeddings must remain strictly partitioned by user tenant IDs.\n\n"
            "• NFR-04: Scalability & Concurrency: The asynchronous FastAPI backend must handle at least 50 concurrent active streaming "
            "connections without worker exhaustion, utilizing non-blocking asyncpg connection pooling.\n\n"
            "• NFR-05: Usability & Cross-Device Responsiveness: The user interface must be fully responsive across mobile, tablet, and "
            "desktop viewports, complying with WCAG 2.1 Level AA accessibility standards.\n\n"
            "• NFR-06: Maintainability & Modularity: Codebase architecture must adhere to clean separation of concerns, decoupling router "
            "endpoints, domain services, ORM models, and Pydantic validation schemas."
        ]),
        
        ("2.7 Hardware and Software Requirements", [
            "Table 2.2 details the minimal and recommended hardware and software specifications required for development, local execution, "
            "and production cloud deployment of TokenBrief."
        ]),
        
        ("2.8 Feasibility Analysis", [
            "A comprehensive tripartite feasibility study was conducted to evaluate the viability of the proposed system:\n\n"
            "1. Technical Feasibility: The platform leverages mature, production-proven open-source frameworks: Next.js 14 for the "
            "presentation tier, FastAPI for high-throughput asynchronous API orchestration, PostgreSQL with pgvector for unified relational "
            "and vector storage, and Google Gemini 2.5 Flash for state-of-the-art generative inference. Sentence-transformers models run "
            "efficiently on standard CPU instances without requiring dedicated GPU infrastructure, proving high technical viability.\n\n"
            "2. Economic Feasibility: By deploying on modern cloud serverless tiers (Vercel for frontend hosting, Render starter tier for "
            "FastAPI backend, Neon serverless PostgreSQL, and Google Apps Script for zero-cost transactional email relays), operational "
            "infrastructure overhead is near-zero during the development and evaluation phases. Semantic caching further slashes API token "
            "consumption by over 40%, guaranteeing outstanding economic sustainability.\n\n"
            "3. Operational and Legal Feasibility: The platform strictly respects user document privacy. Corporate files are not utilized "
            "to train public foundation models; embeddings and vector indices reside in an isolated PostgreSQL cluster protected by role-based "
            "access control. The software is released under the permissive open-source MIT License, ensuring complete legal and compliance feasibility."
        ])
    ])
]

# Table 2.1 data: Comparison of Existing Systems
TABLE_2_1_DATA = [
    ["Feature / Capability", "Legacy Search (Elasticsearch)", "Vanilla RAG (LangChain Default)", "Commercial SaaS (ChatPDF / NotebookLM)", "TokenBrief Platform (Proposed)"],
    ["Retrieval Paradigm", "Keyword (BM25 only)", "Dense Vector (Top-K only)", "Dense Vector Embedding", "Hybrid BM25 + Dense Vector + RRF"],
    ["Multi-Page Coverage", "Manual boolean filtering", "Top-K trap (misses 95%+ of file)", "Truncated sliding window", "Hierarchical Map-Reduce (100% coverage)"],
    ["Reranking Engine", "None", "None (Raw cosine score)", "Opaque proprietary scoring", "Cross-Encoder (ms-marco-MiniLM)"],
    ["Hallucination Gate", "Not applicable", "None (Forced generation)", "Uncalibrated confidence", "Strict Abstention Gate (<25% threshold)"],
    ["Semantic Cache", "Exact keyword cache only", "None", "Session-bound ephemeral cache", "Persistent Vector Cache (Cosine >= 0.90)"],
    ["Active Assessment", "None", "None", "Static quiz without citations", "Adaptive Quiz Studio + Spaced Repetition"],
    ["Multi-Doc Comparison", "Manual diffing", "Token concatenation", "Coarse summary bullets", "Side-by-Side Structured Matrix + Pills"],
    ["Entity Knowledge Graph", "None", "None", "None", "Interactive SVG Network Projection"],
    ["Cloud Email Relay", "Enterprise SMTP server", "Hardcoded SMTP (blocked on clouds)", "Third-party paid API (SendGrid)", "Google Apps Script HTTPS Webhook (Zero-cost)"]
]

# Table 2.2 data: Hardware and Software Specifications
TABLE_2_2_DATA = [
    ["Component", "Development Environment", "Production Cloud Deployment Environment"],
    ["Processor (CPU)", "Intel Core i5 / AMD Ryzen 5 (4+ Cores)", "Cloud vCPU (1 to 2 Shared/Dedicated vCPU)"],
    ["System Memory (RAM)", "8 GB to 16 GB DDR4", "1 GB to 2 GB Containerized Memory"],
    ["Storage (SSD/Disk)", "256 GB NVMe SSD", "10 GB Cloud Persistent Volume / Serverless Object Store"],
    ["Operating System", "Microsoft Windows 11 / Ubuntu 22.04 LTS", "Alpine Linux / Debian Bookworm (Docker Container)"],
    ["Backend Runtime", "Python 3.11.x (FastAPI 0.115, Uvicorn ASGI)", "Render / Koyeb Containerized ASGI Engine"],
    ["Frontend Framework", "Node.js 18.x / 20.x (Next.js 14.2 App Router)", "Vercel Serverless Edge Global Edge Network"],
    ["Database Engine", "PostgreSQL 16 + pgvector (Local)", "Neon Serverless Cloud PostgreSQL Cluster with SSL"],
    ["AI / Embedding Models", "all-MiniLM-L6-v2 (CPU inference)", "sentence-transformers + Google Gemini 2.5 Pro/Flash API"],
    ["Email Dispatch Protocol", "Local SMTP / Gmail TLS Port 587", "Google Apps Script HTTPS Webhook Relay"]
]
