import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    PageBreak,
    HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (on pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "TokenBrief — Enterprise Architecture & Viva Examination Master Guide")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)

        # Running footer
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        self.drawString(54, 32, "Confidential — Prepared for Academic Viva & Technical Evaluation")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def create_viva_pdf(output_filepath: str):
    dir_name = os.path.dirname(output_filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom typography palette
    primary_color = colors.HexColor("#1e293b")
    brand_blue = colors.HexColor("#2563eb")
    accent_emerald = colors.HexColor("#059669")
    dark_gray = colors.HexColor("#334155")
    card_bg = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#cbd5e1")
    code_bg = colors.HexColor("#f1f5f9")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=0,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        "H1Style",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=brand_blue,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=dark_gray,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_gray,
        leftIndent=14,
        spaceAfter=4
    )

    q_style = ParagraphStyle(
        "QuestionStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    ans_style = ParagraphStyle(
        "AnswerStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_gray,
        leftIndent=10,
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        "CalloutStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    elements = []

    # =========================================================================
    # COVER / HEADER
    # =========================================================================
    elements.append(Paragraph("TokenBrief &mdash; Autonomous AI Document Intelligence", title_style))
    elements.append(Paragraph("Full Technical Architecture, Production Workflow & Comprehensive Viva Examination Guide", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=4, spaceAfter=14))

    # Meta card table
    meta_data = [
        [
            Paragraph("<b>Project Type:</b> Enterprise Document RAG & Workspace", body_style),
            Paragraph("<b>Tech Stack:</b> Next.js 14, FastAPI, Neon pgvector, Gemini 2.5", body_style)
        ],
        [
            Paragraph("<b>Author / Candidate:</b> Tushar Kumar (ADGITM)", body_style),
            Paragraph("<b>Evaluation Mode:</b> Academic Viva & Production Deployment", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), card_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 1: EXECUTIVE SUMMARY (SIMPLE PLAIN LANGUAGE)
    # =========================================================================
    elements.append(Paragraph("1. Executive Summary & Problem Statement", h1_style))
    elements.append(Paragraph(
        "<b>What is TokenBrief?</b> TokenBrief is an enterprise-grade AI Document Intelligence workspace. "
        "It allows users to upload complex, multi-page PDFs (such as academic syllabi, scientific research papers, "
        "data mining lab manuals, and professional resumes) and interact with them in real time.",
        body_style
    ))
    elements.append(Paragraph(
        "<b>The Problem with Traditional LLMs & Simple RAG:</b>", body_style
    ))
    elements.append(Paragraph("• <b>The Context Limit & Lost-in-the-Middle Problem:</b> Uploading a 50-page PDF directly into a standard chat context either exceeds token limits or causes the AI to miss vital facts buried in the middle.", bullet_style))
    elements.append(Paragraph("• <b>The Top-K Retrieval Trap:</b> Standard RAG only fetches the top 3-5 isolated text chunks (~2% of the document). Asking 'Give me an executive summary of this whole report' fails completely because 98% of the document is ignored.", bullet_style))
    elements.append(Paragraph("• <b>Hallucinations:</b> Generic LLMs generate plausible-sounding but false answers when the document does not contain the answer.", bullet_style))
    elements.append(Paragraph("• <b>Static, Boring Interaction:</b> Most document tools only offer a single chat box. They lack active learning tools like interactive test generation, multi-file comparisons, or visual knowledge graphs.", bullet_style))
    elements.append(Paragraph(
        "<b>How TokenBrief Solves This:</b> TokenBrief implements a <b>Two-Tier Hierarchical RAG Architecture</b> (Map-Reduce for full-document digests + Reciprocal Rank Fusion hybrid search for precision lookups), an <b>Abstention Guardrail Gate</b> that blocks hallucinations if confidence is below 25%, an <b>Interactive Quiz Engine</b> with domain-aware distractor synthesis, a <b>Multi-Document Matrix Comparator</b>, and an <b>Entity Knowledge Graph Canvas</b>.",
        body_style
    ))
    elements.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 2: ARCHITECTURE & SYSTEM TIERS
    # =========================================================================
    elements.append(Paragraph("2. Full Multi-Tier System Architecture", h1_style))
    elements.append(Paragraph(
        "TokenBrief is decoupled into three independent, horizontally scalable tiers:", body_style
    ))

    arch_data = [
        [Paragraph("<b>Tier</b>", body_style), Paragraph("<b>Technologies</b>", body_style), Paragraph("<b>Core Responsibilities</b>", body_style)],
        [
            Paragraph("<b>Frontend Client</b>", body_style),
            Paragraph("Next.js 14 App Router, React 18, TypeScript, Tailwind CSS, Lucide Icons", body_style),
            Paragraph("Retentrix-style workspace layout, dynamic prompt suggestions, interactive quiz sliders, audio synthesis (Web Speech API), PDF export viewer, SVG knowledge graph.", body_style)
        ],
        [
            Paragraph("<b>Backend API</b>", body_style),
            Paragraph("FastAPI (Python 3.11), Uvicorn, SQLAlchemy AsyncIO, PyPDF, ReportLab", body_style),
            Paragraph("RESTful endpoints, asynchronous chunking, Query Intent Router, Reciprocal Rank Fusion, Map-Reduce batching, JWT cookie auth, disposable email filtering.", body_style)
        ],
        [
            Paragraph("<b>AI / ML Engine</b>", body_style),
            Paragraph("Gemini 2.5 Flash/Pro, sentence-transformers all-MiniLM-L6-v2, PyTorch CPU", body_style),
            Paragraph("Generates 384-dimensional dense embeddings, multi-turn grounded responses, structured JSON quiz parsing, and offline conceptual fallback synthesis.", body_style)
        ],
        [
            Paragraph("<b>Data & Vector Tier</b>", body_style),
            Paragraph("PostgreSQL 16, pgvector extension, Neon Serverless Cloud (SSL)", body_style),
            Paragraph("Relational storage (users, documents, quizzes, annotations, telemetry logs) and HNSW cosine similarity index for sub-millisecond semantic search.", body_style)
        ]
    ]
    arch_table = Table(arch_data, colWidths=[90, 140, 274])
    arch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(arch_table)
    elements.append(Spacer(1, 12))

    # =========================================================================
    # SECTION 3: STEP-BY-STEP WORKFLOW
    # =========================================================================
    elements.append(Paragraph("3. Step-by-Step Data Lifecycle & Execution Pipeline", h1_style))
    elements.append(Paragraph("<b>Step 1: Document Upload & Structural Parsing</b>", h2_style))
    elements.append(Paragraph(
        "When a user uploads a PDF, the backend uses PyPDF to extract raw page text while preserving page numbers and section headers. "
        "A structure-aware chunker divides text into 400–600 token windows with a 50-token overlapping sliding window to prevent cutting sentences across boundaries.",
        body_style
    ))

    elements.append(Paragraph("<b>Step 2: Vector Embedding & Storage</b>", h2_style))
    elements.append(Paragraph(
        "Each chunk is passed to the local `all-MiniLM-L6-v2` neural model to generate a 384-dimensional dense semantic vector. "
        "Chunks and embeddings are inserted into Neon PostgreSQL via `pgvector` with an HNSW cosine index for sub-millisecond similarity lookups.",
        body_style
    ))

    elements.append(Paragraph("<b>Step 3: Query Intent Classification</b>", h2_style))
    elements.append(Paragraph(
        "Incoming user queries are analyzed before querying the database: "
        "<br/>• <b>GLOBAL_SUMMARY:</b> Routes to pre-computed hierarchical Map-Reduce batches for 100% document coverage. "
        "<br/>• <b>MULTI_DOC_COMPARE:</b> Gathers criteria across active documents into a comparative JSON matrix. "
        "<br/>• <b>SPECIFIC_FACT:</b> Triggers Hybrid Search combining BM25 keyword frequency and vector cosine similarity via Reciprocal Rank Fusion (RRF).",
        body_style
    ))

    elements.append(Paragraph("<b>Step 4: Hallucination Guardrail & Grounded Synthesis</b>", h2_style))
    elements.append(Paragraph(
        "Retrieved chunks are evaluated by an Abstention Gate. If similarity scores fall below 25%, the model halts and informs the user rather than hallucinating. "
        "Verified context is supplied to Google Gemini 2.5 Flash with strict grounding instructions and exact page citation enforcement.",
        body_style
    ))
    elements.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: CORE TECHNICAL MODULES
    # =========================================================================
    elements.append(Paragraph("4. Core Workspace Modules & Algorithms", h1_style))
    
    modules_info = [
        ("AI Quiz Studio & Spaced Repetition", 
         "Generates grounded MCQs with interactive sliders (3-15 questions) and difficulty levels. Employs a domain-aware question synthesizer that strips unformatted table dumps and broken sentence fragments. Distractors are drawn from the same subject context, option positions are uniformly randomized (A/B/C/D), and incorrect answers are tracked in `quiz_answers` for Spaced Repetition Review."),
        ("Side-by-Side Multi-Document Comparison",
         "Enables comparative analysis across 2+ files simultaneously. Generates a structured criteria-by-criterion matrix, shared topic pills, unique distinct attributes per document, and an executive verdict."),
        ("Interactive Entity Knowledge Graph",
         "Extracts core concepts, skills, tools, organizations, and methodologies from indexed documents and renders an interactive SVG network canvas with zoom, pan, and node inspection cards."),
        ("Real Analytics & Telemetry",
         "Logs query latency in milliseconds, token counts, model usage breakdown (Pro vs. Flash), and semantic cache hit ratios, visualized through zero-dependency responsive SVG charts."),
        ("Branded PDF Report Generation",
         "Compiles active chat briefings, citations, takeaways, and metrics into a multi-page, publication-grade downloadable PDF via ReportLab.")
    ]
    for mod_title, mod_desc in modules_info:
        elements.append(Paragraph(f"<b>• {mod_title}:</b> {mod_desc}", body_style))
    elements.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 5: TOP 25 VIVA EXAMINATION QUESTIONS & ANSWERS
    # =========================================================================
    elements.append(PageBreak())
    elements.append(Paragraph("5. Top 25 Viva Examination Questions & Model Answers", h1_style))
    elements.append(Paragraph(
        "The following questions represent the exact technical inquiries posed by university professors, project examiners, and technical evaluators.",
        body_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=4, spaceAfter=10))

    viva_qa = [
        (
            "Q1. What is TokenBrief and what primary real-world problem does it solve?",
            "TokenBrief is an autonomous enterprise document intelligence platform built on Retrieval-Augmented Generation (RAG). It solves the limitations of traditional LLMs: context window overflow on long PDFs, the 'Top-K retrieval trap' where summaries ignore 98% of the document, hallucinations on unindexed queries, and lack of interactive learning tools."
        ),
        (
            "Q2. Why did you choose RAG (Retrieval-Augmented Generation) instead of Fine-Tuning an LLM?",
            "Fine-tuning is expensive, slow to retrain, alters model weights without guaranteeing factual recall, and cannot restrict access per user document. RAG separates knowledge storage from reasoning: private documents are indexed in a vector database, enabling instant document updates, zero training cost, verifiable page citations, and zero risk of proprietary data baking into static model weights."
        ),
        (
            "Q3. Why did you select FastAPI for the backend over Django or Flask?",
            "FastAPI is natively asynchronous (built on ASGI and Starlette), delivering up to 3x higher throughput than Flask or Django for I/O-bound tasks like vector searches, database queries, and external LLM streaming. It also provides automatic OpenAPI/Swagger documentation, strict Pydantic data validation, and native Python type hinting."
        ),
        (
            "Q4. What is pgvector and how does vector similarity search work in your database?",
            "pgvector is an open-source PostgreSQL extension that adds native support for high-dimensional vector embeddings. It allows storing 384-dimensional dense vectors directly alongside relational user data and querying them using cosine similarity operator (<=>) or inner product, eliminating the need for a separate third-party vector database."
        ),
        (
            "Q5. Which vector indexing algorithm does your PostgreSQL database use, and why (HNSW vs IVFFlat)?",
            "We use HNSW (Hierarchical Navigable Small World). While IVFFlat partitions vector space into clusters and requires frequent retraining, HNSW builds a multi-layer graph of vectors that allows logarithmic O(log N) search times, higher recall accuracy (>95%), and seamless incremental inserts without retraining the index."
        ),
        (
            "Q6. What embedding model is used and what is its dimensional footprint?",
            "We utilize sentence-transformers/all-MiniLM-L6-v2. It maps text sentences into a 384-dimensional dense vector space. It was chosen because it achieves state-of-the-art semantic search accuracy while executing in ~15ms on standard CPU hardware without requiring dedicated GPU acceleration."
        ),
        (
            "Q7. What is Reciprocal Rank Fusion (RRF) and why do you use Hybrid Search?",
            "Pure vector search understands semantics but can overlook specific alphanumeric codes, roll numbers, or exact product names. Pure keyword search (BM25) finds exact words but fails on synonyms. Hybrid Search runs both simultaneously and combines their rankings using Reciprocal Rank Fusion: RRF_Score = sum(1 / (60 + rank)). This guarantees both high semantic understanding and exact keyword precision."
        ),
        (
            "Q8. How does your system handle long 50+ page PDFs without running out of context tokens?",
            "We implement a Two-Tier Hierarchical Map-Reduce architecture. At upload time, the document is divided into 5-page batches. An asynchronous Map-Reduce pipeline digests each batch into structured bullet points stored in the document_sections table. When a user requests a global summary, the system synthesizes these pre-computed summaries in under 3 seconds with 100% document coverage."
        ),
        (
            "Q9. How does your system prevent LLM hallucinations?",
            "Through a dual-guardrail mechanism: 1) Pre-LLM Grounding Filter / Abstention Gate: If the cosine similarity score of the top retrieved chunk is below 25%, the system immediately halts and informs the user that the document lacks the necessary information. 2) Post-LLM Citation Verifier: Validates that every citation corresponds to an actual chunk boundary."
        ),
        (
            "Q10. How does the AI Quiz Studio generate multiple-choice questions without option bias?",
            "The quiz engine extracts verified facts, chapters, and concepts directly from document chunks. Distractors are drawn from the same subject context rather than generic templates. It utilizes an MCQ builder that shuffles the correct option among A, B, C, and D using random.shuffle, ensuring an even 25% distribution across all four choices."
        ),
        (
            "Q11. What is the Spaced Repetition Review feature in the Quiz Studio?",
            "When users submit quiz attempts, their selections and mistakes are saved in the quiz_answers relational table. The Spaced Repetition endpoint queries previously failed questions for that document, allowing users to re-test on their specific weak areas until mastery is achieved."
        ),
        (
            "Q12. How is user authentication implemented and secured?",
            "Authentication utilizes JSON Web Tokens (JWT) with HS256 encryption. Passwords are salted and hashed using bcrypt. Access tokens are stored in HttpOnly, SameSite=None, Secure cookies to protect against Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF)."
        ),
        (
            "Q13. Why use HttpOnly cookies for JWTs instead of localStorage in the frontend?",
            "Storing JWTs in localStorage exposes tokens to any malicious JavaScript running on the page (XSS attacks). HttpOnly cookies cannot be read or modified by client-side JavaScript, ensuring that even if an XSS vulnerability exists, the attacker cannot steal the authentication session."
        ),
        (
            "Q14. How do you handle Cross-Origin Resource Sharing (CORS) between Vercel and your backend?",
            "In main.py, FastAPI's CORSMiddleware is configured with allow_credentials=True, allow_origin_regex covering https://.*\\.vercel\\.app, and explicit allowed headers and methods. In production, cookies specify SameSite='none' and Secure=True so browsers include credentials across different domains."
        ),
        (
            "Q15. What is Semantic Caching and what performance benefits does it provide?",
            "Semantic caching stores previously answered user queries alongside their embedding vectors in the query_semantic_cache table. When a new query arrives with a cosine similarity > 92% to a cached question, the cached answer is returned immediately (in <10ms), bypassing both the vector search and external LLM API calls."
        ),
        (
            "Q16. How does the Entity Knowledge Graph visualizer render nodes without heavy external libraries?",
            "The backend extracts entities (concepts, tools, frameworks, organizations) and inter-entity relationships during document digestion. The frontend uses a custom SVG canvas with a spring-embedded force simulation to compute 2D coordinate projections with interactive zooming, panning, and node inspection cards."
        ),
        (
            "Q17. What happens if the Gemini API key is invalid, rate-limited, or network fails?",
            "The system includes a resilient local neural synthesis fallback. When the Gemini API call encounters an authentication error (401) or timeout, the engine immediately diverts to the local synthesizer, generating clean conceptual summaries and grounded MCQs without throwing 500 errors to the client."
        ),
        (
            "Q18. What is the role of the Query Intent Router?",
            "Rather than treating every user input identically, the Query Intent Router uses rule-based and semantic classification to categorize queries into GLOBAL_SUMMARY, MULTI_DOC_COMPARE, or SPECIFIC_FACT. This ensures each query type triggers the most efficient and accurate retrieval algorithm."
        ),
        (
            "Q19. Why Next.js 14 App Router for the frontend?",
            "Next.js 14 App Router offers React Server Components (RSC) which minimize JavaScript bundle sizes sent to the client, automatic code splitting, optimized static generation, and edge middleware for route protection before private dashboard pages render."
        ),
        (
            "Q20. What is the difference between Server Components and Client Components in your frontend?",
            "Server Components render entirely on the server and transmit zero client-side JavaScript (used for layout scaffolding and initial HTML). Client Components ('use client') execute in the browser to provide interactivity, such as audio synthesis, sliders, sticky note annotations, and SVG canvas interactions."
        ),
        (
            "Q21. How does the PDF Export briefing feature work under the hood?",
            "The /api/export/pdf endpoint accepts the active conversation ID, fetches Q&A history and source citations, and uses Python ReportLab to dynamically construct a formatted, multi-page PDF document containing branded headers, structured tables, and page numbering, streamed as a binary response."
        ),
        (
            "Q22. Why did Vercel fail to deploy the Python backend directly, and how was it solved?",
            "Vercel Serverless Functions have a maximum unzipped bundle limit of 500MB. PyTorch with CUDA dependencies exceeds 5.5GB. We solved this by decoupling the architecture: deploying the Next.js frontend to Vercel, and containerizing the FastAPI backend via a Dockerfile using CPU-only PyTorch (180MB) on Render/Railway."
        ),
        (
            "Q23. How do you monitor and evaluate real-time system performance?",
            "Every query executes within a telemetry wrapper that records the query text, response latency in milliseconds, token estimates, and model variant in the query_logs table. The Real Analytics dashboard presents rolling aggregations, model distribution donuts, and latency trends."
        ),
        (
            "Q24. How does your database handle concurrent requests from multiple users?",
            "Neon PostgreSQL utilizes connection pooling (PgBouncer) and SQLAlchemy's async_sessionmaker with AsyncEngine. All database operations are non-blocking coroutines running on the Python asyncio event loop, allowing thousands of concurrent read queries without blocking worker threads."
        ),
        (
            "Q25. If given 6 more months, what three major enhancements would you implement?",
            "1) Multimodal Table & Chart Parsing using ColPali / vision embeddings to query charts and diagrams directly. 2) Agentic Multi-Hop Reasoning using ReAct loops to solve complex cross-document queries requiring multiple steps. 3) Offline Local LLM Support using quantized GGUF models via llama.cpp for completely air-gapped enterprise deployments."
        )
    ]

    for q_text, ans_text in viva_qa:
        elements.append(Paragraph(f"<b>{q_text}</b>", q_style))
        elements.append(Paragraph(ans_text, ans_style))
        elements.append(Spacer(1, 3))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"✓ PDF successfully generated at: {output_filepath}")

if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "TokenBrief_Architecture_and_Viva_Guide.pdf"
    create_viva_pdf(out_path)
