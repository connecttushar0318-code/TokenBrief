# scripts/report_content_front.py
"""
Front matter definitions for Tushar Bansal's Minor Project Report.
Contains cover page layout, declaration, certificate, abstract, acknowledgement,
list of figures, list of tables, list of abbreviations, and table of contents.
"""

PROJECT_TITLE = "TOKENBRIEF: MULTI-AGENT RETRIEVAL-AUGMENTED GENERATION (RAG) DOCUMENT INTELLIGENCE AND ADAPTIVE ASSESSMENT PLATFORM"
STUDENT_NAME = "Tushar Bansal"
ENROLMENT_NO = "03396211923"
SECTION = "AI&DS-F20"
SEMESTER = "Seventh"
DEGREE = "BACHELOR OF TECHNOLOGY"
BRANCH = "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE"
SUPERVISOR_NAME = "Mr. Ankur Jain"
SUPERVISOR_DESIG = "Assistant Professor"
DEPARTMENT = "DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND DATA SCIENCE"
INSTITUTE = "DR. AKHILESH DAS GUPTA INSTITUTE OF PROFESSIONAL STUDIES"
INSTITUTE_ADDRESS = "F-26, 0-Pusta Road, Shastri Park, Shahdara, Delhi – 110053"
AFFILIATION = "Affiliated to Guru Gobind Singh Indraprastha University, Delhi"
ACADEMIC_SESSION = "2026–2027"
YEAR_OF_SUBMISSION = "2026"
SUBMISSION_DATE = "21/11/2026"

DECLARATION_TEXT = (
    f"I, {STUDENT_NAME}, a student of Bachelor of Technology (Artificial Intelligence and Data Science), "
    f"Department of Artificial Intelligence and Data Science, Dr. Akhilesh Das Gupta Institute of Professional "
    f"Studies, bearing University Enrolment No. {ENROLMENT_NO}, hereby declare that the Minor Project Report "
    f"entitled \"{PROJECT_TITLE}\" is my original work carried out as part of the prescribed academic requirements.\n\n"
    "I have duly acknowledged all sources, publications, datasets, software libraries, models and other materials "
    "used in preparing this report. No part of this report has been presented as the work of another person without "
    "appropriate attribution. The report has not been submitted previously for the award of another degree or diploma, "
    "except where explicitly disclosed."
)

CERTIFICATE_TEXT = (
    f"This is to certify that the Minor Project Report entitled \"{PROJECT_TITLE}\", submitted by {STUDENT_NAME} "
    f"(University Enrolment No. {ENROLMENT_NO}), in partial fulfilment of the requirements for the award of the degree "
    f"of Bachelor of Technology (Artificial Intelligence and Data Science) of Guru Gobind Singh Indraprastha University, "
    f"Delhi, is a record of project work carried out under my guidance and supervision at Dr. Akhilesh Das Gupta "
    f"Institute of Professional Studies, Delhi.\n\n"
    "To the best of my knowledge, the work presented in this report is original, and the student has acknowledged "
    "relevant sources appropriately. The report is recommended for evaluation as a Minor Project."
)

ABSTRACT_TEXT = (
    "Enterprise knowledge management is increasingly challenged by exponential growth in unstructured multi-page documentation, "
    "including technical manuals, financial prospectuses, legal contracts, and academic textbooks. While Large Language Models (LLMs) "
    "offer remarkable natural language comprehension, their direct application to proprietary corporate corpora is severely restricted by "
    "strict context window boundaries, excessive token processing latency, and chronic factual hallucinations. Conventional Retrieval-Augmented "
    "Generation (RAG) frameworks attempt to mitigate these boundaries by chunking documents and querying dense vector indices; however, "
    "they frequently succumb to the 'Top-K retrieval trap'—retrieving isolated, superficial fragments while missing holistic semantic "
    "context in 50+ page documents. Furthermore, vanilla RAG architectures lack active evaluation mechanisms to assess whether human "
    "operators have comprehended the ingested technical knowledge.\n\n"
    "This project introduces TokenBrief, an enterprise-grade autonomous document intelligence and adaptive assessment platform. "
    "TokenBrief establishes a robust, multi-tier microservice architecture that combines hierarchical document summarization, hybrid "
    "lexical-dense vector retrieval, and automated cognitive evaluation. The platform introduces a two-tier ingestion engine: Tier 1 "
    "indexes fine-grained 500-token leaf chunks embedded via dense representations (all-MiniLM-L6-v2), while Tier 2 executes an asynchronous "
    "Map-Reduce summarization pipeline over 5-page structural batches to guarantee 100% holistic document coverage. Incoming user prompts "
    "are dynamically routed by a Query Intent Classifier across global synthesis, multi-document comparison, and factual lookup. "
    "Factual retrieval synthesizes sparse BM25 lexical ranking with dense HNSW vector similarity through Reciprocal Rank Fusion (RRF), "
    "subsequently refined by a cross-encoder neural reranker and protected by a confidence-calibrated hallucination abstention gate (<25% threshold).\n\n"
    "To achieve low latency and cost efficiency, TokenBrief incorporates a cosine-similarity semantic caching layer, reducing mean response "
    "latency by 96.2% (from 1,250 ms to 48 ms) on recurrent conceptual queries. Beyond retrieval, TokenBrief integrates an Interactive Quiz "
    "Studio featuring dynamic question count sliders (3–15 questions), difficulty adjustment, instant pedagogical grading with grounded citations, "
    "and a Spaced Repetition evaluation queue. An interactive SVG Knowledge Graph visualizes extracted concepts, entities, and structural dependencies, "
    "while side-by-side comparative matrices enable cross-document synthesis. Deployed via a modern Next.js 14 single-page application and an "
    "asynchronous FastAPI backend with serverless PostgreSQL and Google Apps Script HTTPS Webhook email OTP verification, TokenBrief delivers a "
    "production-grade, scalable, and verifiable paradigm for enterprise knowledge intelligence."
)

ACKNOWLEDGEMENT_TEXT = (
    f"I express my sincere gratitude to Dr. Akhilesh Das Gupta Institute of Professional Studies (ADGIPS), Delhi, "
    f"and the Department of Artificial Intelligence and Data Science for providing the academic ecosystem, computational "
    f"infrastructure, and encouragement necessary to carry out this Minor Project successfully.\n\n"
    f"I am deeply indebted to my project supervisor, {SUPERVISOR_NAME}, {SUPERVISOR_DESIG}, Department of Artificial "
    f"Intelligence and Data Science, for his invaluable guidance, technical insights, rigorous reviews, and continuous "
    f"encouragement throughout the conception, architectural design, and implementation of TokenBrief.\n\n"
    f"I also extend my sincere appreciation to the Head of Department, faculty members, laboratory staff, and colleagues "
    f"of the Department of AI & DS for their constructive feedback and continuous support.\n\n"
    f"Finally, I express my profound gratitude to my family and friends for their unwavering patience, moral support, "
    f"and inspiration throughout my academic journey."
)

FIGURES_LIST = [
    ("Figure 3.1", "High-Level System Architecture of TokenBrief Platform", "15"),
    ("Figure 3.2", "End-to-End Document Ingestion and RAG Inference Pipeline Workflow", "17"),
    ("Figure 4.1", "Secure User Authentication and Passwordless OTP Verification Interface", "26"),
    ("Figure 4.2", "Document Workspace, Conversational Q&A and Grounded Citation Highlighting", "26"),
    ("Figure 4.3", "Interactive Quiz Studio with Question Count Slider and Spaced Repetition", "27"),
    ("Figure 4.4", "Multi-Document Structured Comparison Matrix Interface", "27"),
    ("Figure 4.5", "Transactional Email Security Verification Code Template via Google Apps Script", "27"),
    ("Figure 5.1", "Latency Benchmark Comparison Across RAG Pipeline Configurations", "32"),
    ("Figure 5.2", "Interactive Entity Knowledge Graph Visualisation Canvas", "33"),
    ("Figure 5.3", "Real-Time Analytics Telemetry Dashboard and Gemini Model Distribution", "33"),
    ("Figure 5.4", "Impact of Semantic Cache Warm-Up on Query Response Latency and Throughput", "36"),
]

TABLES_LIST = [
    ("Table 2.1", "Comparative Analysis of Legacy Search vs Conventional RAG vs TokenBrief", "9"),
    ("Table 2.2", "Hardware and Software Specifications and Deployment Requirements", "11"),
    ("Table 3.1", "Document Chunking and Dense Embedding Specifications", "17"),
    ("Table 3.2", "Relational Database Schema Specifications for PostgreSQL and pgvector", "20"),
    ("Table 4.1", "System Verification Test Cases and Execution Outcomes", "28"),
    ("Table 5.1", "Retrieval Accuracy, Grounding Precision, and Hallucination Abstention Metrics", "34"),
    ("Table 5.2", "Latency, Cache Hit Rate, and Token Cost Optimization Benchmarks", "35"),
]

ABBREVIATIONS_LIST = [
    ("AI", "Artificial Intelligence"),
    ("RAG", "Retrieval-Augmented Generation"),
    ("LLM", "Large Language Model"),
    ("NLP", "Natural Language Processing"),
    ("BM25", "Best Matching 25 (Sparse Lexical Probabilistic Ranking)"),
    ("RRF", "Reciprocal Rank Fusion"),
    ("HNSW", "Hierarchical Navigable Small World (Vector Graph Indexing)"),
    ("API", "Application Programming Interface"),
    ("REST", "Representational State Transfer"),
    ("ASGI", "Asynchronous Server Gateway Interface"),
    ("JWT", "JSON Web Token"),
    ("SPA", "Single-Page Application"),
    ("OTP", "One-Time Password"),
    ("SMTP", "Simple Mail Transfer Protocol"),
    ("ORM", "Object-Relational Mapping"),
    ("ACID", "Atomicity, Consistency, Isolation, Durability"),
    ("SVG", "Scalable Vector Graphics"),
    ("MCQ", "Multiple Choice Question"),
    ("NDCG", "Normalized Discounted Cumulative Gain"),
    ("MRR", "Mean Reciprocal Rank"),
    ("ROUGE", "Recall-Oriented Understudy for Gisting Evaluation"),
    ("SaaS", "Software-as-a-Service"),
    ("TLS", "Transport Layer Security"),
    ("RBAC", "Role-Based Access Control"),
    ("HSTS", "HTTP Strict Transport Security"),
]

TOC_ENTRIES = [
    ("Declaration by Student", "i"),
    ("Certificate by Supervisor", "ii"),
    ("Abstract", "iii"),
    ("Acknowledgement", "iv"),
    ("List of Figures", "v"),
    ("List of Tables", "vi"),
    ("List of Abbreviations", "vii"),
    ("Table of Contents", "viii"),
    ("Chapter 1: Introduction", "1"),
    ("    1.1 Introduction to the Project Domain", "1"),
    ("    1.2 Background and Motivation", "2"),
    ("    1.3 Problem Statement", "3"),
    ("    1.4 Objectives of the Project", "4"),
    ("    1.5 Scope of the Project", "4"),
    ("    1.6 Organisation of the Report", "5"),
    ("Chapter 2: Requirement Analysis and System Specification", "7"),
    ("    2.1 Introduction", "7"),
    ("    2.2 Literature Review and Related Work", "7"),
    ("    2.3 Limitations of Existing Systems", "8"),
    ("    2.4 Proposed System and Requirements", "9"),
    ("    2.5 Functional Requirements", "9"),
    ("    2.6 Non-Functional Requirements", "10"),
    ("    2.7 Hardware and Software Requirements", "11"),
    ("    2.8 Feasibility Analysis", "12"),
    ("Chapter 3: System Design", "14"),
    ("    3.1 Proposed System Architecture", "14"),
    ("    3.2 Overall System Workflow", "15"),
    ("    3.3 Data Ingestion, Document Processing and Embeddings", "17"),
    ("    3.4 Data Preprocessing, Text Chunking & Hierarchical Batching", "17"),
    ("    3.5 Model Selection, Hybrid Retrieval (BM25 + Dense) and RRF", "18"),
    ("    3.6 Module and Interface Design", "19"),
    ("    3.7 System Architectural and Data Flow Diagrams", "20"),
    ("    3.8 Database Design", "20"),
    ("Chapter 4: Implementation, Testing and Maintenance", "22"),
    ("    4.1 Development Environment and Tools", "22"),
    ("    4.2 Implementation of Project Modules", "22"),
    ("    4.3 Algorithm Implementation & Generative Prompt Engineering", "23"),
    ("    4.4 User Interface and System Integration", "25"),
    ("    4.5 Testing Methodology", "28"),
    ("    4.6 Test Cases and Test Results", "28"),
    ("    4.7 Validation and Performance Testing", "29"),
    ("    4.8 Maintenance and Deployment Considerations", "30"),
    ("Chapter 5: Results and Discussions", "31"),
    ("    5.1 Experimental Setup", "31"),
    ("    5.2 Implementation Results", "31"),
    ("    5.3 Performance Analysis, Retrieval Accuracy and Latency", "32"),
    ("    5.4 Evaluation Metrics", "33"),
    ("    5.5 Comparison with Existing Approaches", "35"),
    ("    5.6 Discussion, Interpretation, Privacy and Hallucination Mitigation", "36"),
    ("    5.7 Limitations of the Proposed System", "37"),
    ("Chapter 6: Conclusion and Future Scope", "38"),
    ("    6.1 Conclusion", "38"),
    ("    6.2 Major Contributions and Achievements", "38"),
    ("    6.3 Future Scope and Enhancements", "39"),
    ("References", "41"),
    ("Appendix A: Development Environment and Installation Details", "42"),
    ("Appendix B: Platform User Interface Screenshots", "44"),
    ("Appendix C: Core System Source Code", "45"),
    ("Appendix D: Additional Results and Supporting Documents", "47"),
    ("Annexure: Plagiarism Evaluation Summary Report", "48"),
]
