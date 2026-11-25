import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_chrome(total_pages)
            super().showPage()
        super().save()

    def draw_page_chrome(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        if self._pageNumber > 1:
            self.drawString(50, 758, "TokenBrief — Easy Project Explanation, API Setup & Viva Guide")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.6)
            self.line(50, 750, 562, 750)

        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.6)
        self.line(50, 44, 562, 44)
        self.drawString(50, 31, "TokenBrief Minor Project Companion Guide (B.Tech AI & Data Science)")
        self.drawRightString(562, 31, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def _make_box(flowables, bg_hex="#f8fafc", border_hex="#cbd5e1", left_accent_hex=None):
    table = Table([[flowables]], colWidths=[512])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(border_hex)),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]
    if left_accent_hex:
        style_cmds.append(("LINEBEFORE", (0, 0), (0, -1), 3.5, colors.HexColor(left_accent_hex)))
    table.setStyle(TableStyle(style_cmds))
    return table


def generate_easy_viva_pdf(output_path: str):
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=52,
        bottomMargin=54,
    )

    base = getSampleStyleSheet()
    navy = colors.HexColor("#0f172a")
    blue = colors.HexColor("#2563eb")
    dark = colors.HexColor("#334155")
    muted = colors.HexColor("#475569")

    title_style = ParagraphStyle(
        "TitleHero", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=22, leading=27, textColor=navy, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "SubHero", parent=base["Normal"], fontName="Helvetica",
        fontSize=11, leading=15, textColor=muted, spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "H1", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=14, leading=18, textColor=blue, spaceBefore=12, spaceAfter=6, keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "H2", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=11, leading=15, textColor=navy, spaceBefore=8, spaceAfter=4, keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body", parent=base["Normal"], fontName="Helvetica",
        fontSize=9.5, leading=13.5, textColor=dark, spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=base["Normal"], fontName="Helvetica",
        fontSize=9.3, leading=13, textColor=dark, leftIndent=14, spaceAfter=4,
    )
    q_style = ParagraphStyle(
        "VivaQ", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=10, leading=13.5, textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=7, spaceAfter=2, keepWithNext=True,
    )
    a_style = ParagraphStyle(
        "VivaA", parent=base["Normal"], fontName="Helvetica",
        fontSize=9.3, leading=13, textColor=dark, leftIndent=10, spaceAfter=6,
    )
    code_style = ParagraphStyle(
        "CodeLine", parent=base["Normal"], fontName="Courier",
        fontSize=8.5, leading=12, textColor=colors.HexColor("#0f172a"),
        spaceAfter=3,
    )

    story = []

    # =========================================================================
    # HEADER & SUMMARY CARD
    # =========================================================================
    story.append(Paragraph("TokenBrief &mdash; Easy Viva &amp; Deployment Guide", title_style))
    story.append(Paragraph(
        "Learn how TokenBrief works in simple everyday English + Step-by-Step Guide to Swap the Gemini AI Studio Key &amp; Redeploy",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=blue, spaceBefore=2, spaceAfter=12))

    snapshot_rows = [
        [Paragraph("<b>What is TokenBrief?</b>", body_style), Paragraph("An AI Document Intelligence Workspace: upload PDF/TXT/MD files, ask questions, get exact [Page X] citations, compare files, generate quizzes, explore entity graphs, and export PDFs.", body_style)],
        [Paragraph("<b>Frontend (UI)</b>", body_style), Paragraph("Next.js 14 (React 18, TypeScript, Tailwind CSS) &mdash; deployed on Vercel.", body_style)],
        [Paragraph("<b>Backend (API)</b>", body_style), Paragraph("FastAPI (Python 3.11.9, Uvicorn, PyPDF, ReportLab) &mdash; deployed on Render (service: <b>tokenbrief-backend</b>).", body_style)],
        [Paragraph("<b>Database &amp; Search</b>", body_style), Paragraph("Neon Serverless PostgreSQL + <b>pgvector</b> (384-d HNSW vectors) + Hybrid RRF Search + L1/L2 Semantic Cache.", body_style)],
        [Paragraph("<b>AI Brain &amp; Fallback</b>", body_style), Paragraph("Google Gemini (<b>gemini-2.5-flash</b>) via <b>GEMINI_API_KEY</b> + built-in structured offline synthesizer if key is invalid/offline.", body_style)],
    ]
    snap_table = Table(snapshot_rows, colWidths=[125, 387])
    snap_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(snap_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 1: 30-SECOND ELEVATOR PITCH
    # =========================================================================
    story.append(Paragraph("1. The 30-Second Intro (Read This Word-for-Word in Your Viva)", h1_style))
    pitch_box = _make_box([
        Paragraph(
            "<b>Say this to your examiner:</b><br/>"
            "\"Sir/Ma'am, <b>TokenBrief</b> is a full-stack AI Document Intelligence platform. "
            "Instead of manually reading a 60-page PDF or pasting huge text into ChatGPT where AI forgets the middle or invents wrong facts, "
            "a user simply uploads any PDF, TXT, or Markdown file up to 15 MB. "
            "TokenBrief splits the file page-by-page, turns each piece into lightweight math vectors inside PostgreSQL (pgvector), "
            "and uses <b>Hybrid Search + Section Lookup + Google Gemini</b> to answer questions with clickable <b>[Page X]</b> proof. "
            "Beyond chat, it also builds interactive MCQ quizzes, compares two documents side by side, draws a concept Knowledge Graph, "
            "tracks speed analytics, and exports clean PDF reports.\"",
            body_style,
        )
    ], bg_hex="#eff6ff", border_hex="#93c5fd", left_accent_hex="#2563eb")
    story.append(pitch_box)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Why did we call it TokenBrief &amp; what problems does it solve?</b>", h2_style))
    story.append(Paragraph("&bull; <b>Saves Tokens &amp; Time:</b> Sends only relevant chunks or compact page digests to the AI instead of dumping raw megabytes every prompt.", bullet_style))
    story.append(Paragraph("&bull; <b>Fixes the 'Whole Summary' Trap:</b> Normal RAG only picks 3&ndash;5 small chunks (~5% of a PDF), so asking <i>'Summarize this whole report'</i> fails. TokenBrief uses a separate <b>Full-File Digest</b> mode that scans across all pages while skipping Cover/Declaration/Certificate boilerplate.", bullet_style))
    story.append(Paragraph("&bull; <b>Fixes Section Lookups:</b> Asking <i>'Explain Section 4'</i> jumps directly to Chapter 4 pages instead of getting tricked by the Table of Contents.", bullet_style))
    story.append(Paragraph("&bull; <b>Works on Free 512 MB Hosting:</b> Instead of heavy PyTorch models that crash free servers with Out-Of-Memory (OOM) errors, TokenBrief computes fast 384-d vectors in pure Python.", bullet_style))

    # =========================================================================
    # PART 2: STEP-BY-STEP HOW IT WORKS (SIMPLE STORY)
    # =========================================================================
    story.append(Paragraph("2. How TokenBrief Works Step-by-Step (Easy Architecture Story)", h1_style))

    story.append(Paragraph("Step A &mdash; Sign Up, Email OTP &amp; 7-Day Login (routers/auth.py, security.py, email_service.py)", h2_style))
    story.append(Paragraph("&bull; Passwords are never stored in plain text &mdash; they are salted and hashed using <b>bcrypt</b>.", bullet_style))
    story.append(Paragraph("&bull; When you register or reset a password, a 6-digit OTP (valid for <b>10 minutes</b>) is emailed using a smart 3-layer fallback: <b>Google Apps Script HTTPS Webhook</b> (works even when cloud servers block SMTP ports!) &rarr; Resend API &rarr; Gmail SMTP.", bullet_style))
    story.append(Paragraph("&bull; After login, TokenBrief issues signed <b>JWT Access &amp; Refresh Tokens</b> (valid 7 days / 10,080 minutes) stored safely in HTTP cookies and browser session headers so users stay signed in seamlessly across tabs and devices.", bullet_style))

    story.append(Paragraph("Step B &mdash; Uploading &amp; Indexing a PDF (routers/documents.py, chunking_service.py, embedding_service.py)", h2_style))
    story.append(Paragraph("&bull; <b>Validation:</b> Checks file extension (.pdf, .txt, .md) and size (100 bytes to 15 MB).", bullet_style))
    story.append(Paragraph("&bull; <b>Page Extraction &amp; Chunking:</b> Reads text page-by-page using PyPDF and breaks long pages into ~<b>1200-character chunks</b> with a <b>35-word overlap</b> so sentences at page/chunk borders are never cut off.", bullet_style))
    story.append(Paragraph("&bull; <b>Zero-OOM 384-d Embeddings:</b> Each chunk is converted into a 384-number mathematical vector using our pure-Python feature-hashing engine (token stems, synonym concept groups, character 3/4-grams for typo tolerance, and word bigrams). It takes almost 0 MB extra RAM and never triggers Out-Of-Memory crashes on Render.", bullet_style))
    story.append(Paragraph("&bull; <b>Cloud Storage &amp; Background Summaries:</b> All chunks + vectors are saved in Neon PostgreSQL (with HNSW index on pgvector), and a background task builds page-group section summaries without making the user wait.", bullet_style))

    story.append(Paragraph("Step C &mdash; What Happens When You Ask a Question (routers/qa.py, qa_service.py, search_service.py, cache_service.py)", h2_style))
    flow_rows = [
        [Paragraph(f"<font color='white'><b>{col_title}</b></font>", body_style) for col_title in ("Stage", "What Happens in Simple Words", "Why It Matters")],
        [Paragraph("<b>1. Greeting Check</b>", body_style), Paragraph("If user types 'hi' or 'hello', replies politely right away.", body_style), Paragraph("Zero wasted DB search or LLM cost.", body_style)],
        [Paragraph("<b>2. Two-Level Cache</b>", body_style), Paragraph("Checks L1 fast Python RAM cache (&lt;0.1 ms), then L2 PostgreSQL semantic cache (0.92 similarity).", body_style), Paragraph("Similar questions get instant answers even if phrased differently.", body_style)],
        [Paragraph("<b>3. Smart Routing</b>", body_style), Paragraph("Detects if question wants a specific Section/Chapter (skipping TOC lists) OR a full Executive Summary.", body_style), Paragraph("Fixes both 'Executive Summary' and 'Explain Section 4'.", body_style)],
        [Paragraph("<b>4. Hybrid Search + Rerank</b>", body_style), Paragraph("Combines Vector Search (meaning) + SQL Lexical Search (exact words) via Reciprocal Rank Fusion (RRF k=60), then reranks top hits.", body_style), Paragraph("Finds both conceptual meanings and exact keywords/marks.", body_style)],
        [Paragraph("<b>5. Gemini + Citations</b>", body_style), Paragraph("Calls Gemini 2.5 Flash (or structured local synthesizer if key is invalid) and verifies [Page X] tags.", body_style), Paragraph("Every fact points to an exact clickable source page.", body_style)],
    ]
    flow_table = Table(flow_rows, colWidths=[98, 240, 174])
    flow_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Step D &mdash; Beyond Chat: 5 Extra Features Inside TokenBrief", h2_style))
    story.append(Paragraph("&bull; <b>Interactive Quiz Engine (routers/quiz.py):</b> Generates Easy/Medium/Hard MCQs with smart distractors, lets users submit answers, grades scores, and saves quiz history.", bullet_style))
    story.append(Paragraph("&bull; <b>Multi-Document Comparison (comparison_service.py):</b> Compares 2 or more PDFs side-by-side in a structured matrix (topics, focus, complexity).", bullet_style))
    story.append(Paragraph("&bull; <b>Knowledge Graph (entities.py):</b> Automatically extracts Skills, Core Concepts, and Organizations into nodes and edges.", bullet_style))
    story.append(Paragraph("&bull; <b>Annotations &amp; Analytics (annotations.py, analytics.py):</b> Stores user page notes/highlights and tracks query latency &amp; cache hit rates.", bullet_style))
    story.append(Paragraph("&bull; <b>One-Click PDF Export (export.py):</b> Converts Q&amp;A threads into formatted downloadable ReportLab PDF reports.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # PART 3: HOW TO EXCHANGE GEMINI API KEY FOR AI STUDIO KEY, SAVE & REDEPLOY
    # =========================================================================
    story.append(Paragraph("3. How to Switch GEMINI_API_KEY to a Google AI Studio Key &amp; Redeploy", h1_style))
    why_box = _make_box([
        Paragraph(
            "<b>Why do we need to do this?</b><br/>"
            "Right now, the deployed backend's <b>GEMINI_API_KEY</b> fails Google's API authentication check (returns 401 UNAUTHENTICATED) and does not begin with <b>AIzaSy</b>. "
            "Because of this, TokenBrief safely switches to its built-in structured offline formatter (<b>TokenBrief Unified Engine</b>) instead of live <b>Gemini 2.5 Flash</b> prose, and document comparison falls back to local heuristics. "
            "Swapping in a free Google AI Studio key unlocks full Gemini 2.5 Flash AI answers immediately.",
            body_style,
        )
    ], bg_hex="#fffbeb", border_hex="#fcd34d", left_accent_hex="#d97706")
    story.append(why_box)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Phase 1 &mdash; Create a Free Google AI Studio Key (Starts with AIzaSy...)", h2_style))
    story.append(Paragraph("1. Open your browser and go to: <b>https://aistudio.google.com/apikey</b>", bullet_style))
    story.append(Paragraph("2. Sign in with your Google account (for example, your project Gmail account).", bullet_style))
    story.append(Paragraph("3. Click the blue <b>Create API key</b> button (choose an existing Google Cloud project or create a new one when asked).", bullet_style))
    story.append(Paragraph("4. Copy the generated key string &mdash; make sure it starts with <b>AIzaSy...</b> (about 39 characters long). <i>Do not use a token starting with AQ... or OAuth client secrets.</i>", bullet_style))

    story.append(Paragraph("Phase 2 &mdash; Save the Key in Render &amp; Redeploy tokenbrief-backend", h2_style))
    story.append(Paragraph("1. Open <b>https://dashboard.render.com</b> and log in to the account hosting the project.", bullet_style))
    story.append(Paragraph("2. Under <b>Web Services</b>, click <b>tokenbrief-backend</b> (configured by render.yaml).", bullet_style))
    story.append(Paragraph("3. In the left sidebar menu, click <b>Environment</b>.", bullet_style))
    story.append(Paragraph("4. Scroll to <b>Environment Variables</b> and find the key named:", bullet_style))
    story.append(_make_box([
        Paragraph("Key: <b>GEMINI_API_KEY</b> &nbsp;&nbsp;|&nbsp;&nbsp; New Value: <b>AIzaSy...(paste your copied AI Studio key here)</b>", code_style),
        Paragraph("Key: <b>GEMINI_MODEL</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp; Value: <b>gemini-2.5-flash</b> (verify this stays gemini-2.5-flash)", code_style),
    ], bg_hex="#f1f5f9", border_hex="#cbd5e1"))
    story.append(Spacer(1, 4))
    story.append(Paragraph("5. Click the <b>Edit</b> (pencil icon) next to <b>GEMINI_API_KEY</b>, delete the old value completely, and paste your new <b>AIzaSy...</b> key with zero extra spaces or quotes.", bullet_style))
    story.append(Paragraph("6. Click <b>Save Changes</b> (or <b>Save, rebuild, and deploy</b>) at the bottom of the Environment section.", bullet_style))
    story.append(Paragraph("7. <b>Check Redeploy:</b> Render automatically triggers a fresh deploy when environment variables are saved. If a deploy does not start within 10 seconds, click <b>Manual Deploy &rarr; Deploy latest commit</b> in the top-right corner.", bullet_style))
    story.append(Paragraph("8. Wait ~60&ndash;90 seconds until the deployment status turns green (<b>Live</b>). Open <b>https://tokenbrief-backend.onrender.com/health</b> to confirm <i>status: operational</i>.", bullet_style))

    story.append(Paragraph("Phase 3 &mdash; Clear Old Cached Answers &amp; Test Live", h2_style))
    story.append(Paragraph("&bull; Because TokenBrief caches past answers in PostgreSQL (<i>semantic_query_cache</i>), re-asking the exact same prompt may still return an old cached reply unless cleared once.", bullet_style))
    story.append(Paragraph("&bull; <b>Easy way:</b> Either ask a slightly rephrased question, OR trigger a <b>DELETE</b> request to <b>https://tokenbrief-backend.onrender.com/api/qa/cache</b> (also visible in Swagger UI at <b>/docs</b> &rarr; QA Engine &rarr; <i>DELETE /api/qa/cache</i> &rarr; Try it out &rarr; Execute).", bullet_style))
    story.append(Paragraph("&bull; <b>If running locally on your laptop:</b> Open the <b>.env</b> file in your <i>Minor_project</i> folder, update <b>GEMINI_API_KEY=AIzaSy...</b>, save, and restart uvicorn.", bullet_style))

    # =========================================================================
    # PART 4: TOP 20 VIVA QUESTIONS & SIMPLE ANSWERS
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. Top 20 Viva Questions &amp; Simple Ready-to-Speak Answers", h1_style))
    story.append(Paragraph("Read these before your viva. Every answer is kept short, honest, and directly matches the real code in your project.", body_style))

    viva_qa = [
        ("Q1. What is TokenBrief in one sentence?",
         "TokenBrief is a full-stack AI document intelligence workspace where users upload PDFs, TXT, or Markdown files and get cited Q&amp;A, executive summaries, chapter breakdowns, MCQ quizzes, document comparisons, knowledge graphs, and PDF exports."),
        ("Q2. What is RAG (Retrieval-Augmented Generation) in simple words?",
         "RAG means 'look up the real book first, then answer.' Instead of letting an AI guess from memory, TokenBrief first searches the uploaded PDF for the exact relevant pages, passes those pages to Gemini, and cites the page numbers."),
        ("Q3. How is TokenBrief better than uploading a PDF directly to ChatGPT?",
         "ChatGPT is just a single chat window without a dedicated study workspace. TokenBrief gives persistent PostgreSQL document storage, clickable [Page X] proof citations, semantic answer caching for speed, auto-generated MCQ quizzes, multi-file comparison tables, and a concept Knowledge Graph."),
        ("Q4. What tech stack did you use for Frontend, Backend, and Database?",
         "Frontend: Next.js 14 (React 18, TypeScript, Tailwind CSS) hosted on Vercel. Backend: FastAPI (Python 3.11.9, Uvicorn, SQLAlchemy AsyncIO, PyPDF, ReportLab) hosted on Render. Database: Serverless PostgreSQL on Neon with pgvector extension."),
        ("Q5. What happens when a user uploads a PDF?",
         "FastAPI validates the extension and 15 MB size limit, extracts text per page with PyPDF, splits text into ~1200-character chunks with 35-word overlap, turns each chunk into a 384-d vector, stores chunks + vectors in Neon pgvector, and indexes section summaries in the background."),
        ("Q6. Why do you split text into chunks with a 35-word overlap?",
         "LLMs and vector search work best on focused paragraphs rather than giant 60-page blobs. Keeping a 35-word overlap ensures that if an important sentence crosses a chunk boundary, its meaning is not cut in half."),
        ("Q7. How do you generate vector embeddings without PyTorch crashing on Render?",
         "Render's free tier gives 512 MB RAM, which gets exhausted by heavy PyTorch / HuggingFace transformer models (causing OOM crashes). So we engineered a lightweight 384-dimensional semantic feature-hashing embedder in pure Python using crc32 hashing, word stemming, synonym concept groups, character n-grams, and word bigrams. It stays under a few MB of RAM while keeping exact Vector(384) compatibility with pgvector."),
        ("Q8. What is pgvector and why use HNSW indexing?",
         "pgvector lets PostgreSQL store mathematical vectors inside regular database tables alongside user and document metadata. HNSW (Hierarchical Navigable Small World) is a graph-based vector index that finds closest-meaning chunks quickly without scanning every row linearly."),
        ("Q9. Explain your Hybrid Search and Reciprocal Rank Fusion (RRF).",
         "Pure vector search can miss exact numbers or names (like 'Section 4' or 'cgpa'), while pure keyword search can miss synonyms. TokenBrief runs BOTH Vector Cosine Search and SQL Lexical Search (top 25 each), merges their rankings using RRF (formula: score = sum of 1 / (60 + rank)), and reranks the top 15 results down to the best 4&ndash;5 chunks."),
        ("Q10. How does CandidateRerankerService improve search results?",
         "After RRF picks candidates, our reranker gives extra weight to how many query keywords appear in the chunk, bigram matches, exact phrase matches, and even filename clues (e.g., matching 'resume' or 'notes' files when appropriate)."),
        ("Q11. How do you summarize a whole 60-page PDF if search only picks 5 chunks?",
         "For Executive Summary questions, we don't rely on top-5 search. Our build_full_file_digest builds a balanced digest across all pages, and our synthesizer explicitly filters out boilerplate front matter (Cover, Declaration, Certificate, TOC) to extract goals from the Abstract, core topics from Chapter openings, and outcomes from the Conclusion."),
        ("Q12. How did you fix queries like 'Explain Section 4'?",
         "Previously, 'explain' triggered a whole-document summary or matched a list inside Chapter 1 mentioning Chapter 4. Now _extract_targeted_section_chunks detects section/chapter numbers, skips multi-chapter overview lists/TOC pages, locks onto the real 'CHAPTER 4:' header page (e.g., Pages 35&ndash;39), and summarizes its subsections cleanly."),
        ("Q13. How does your Semantic Cache work?",
         "TokenBrief uses a two-level cache. L1 is a fast in-memory Python dictionary inside the backend (&lt;0.1 ms). L2 is the semantic_query_cache table in PostgreSQL with 384-d vectors. If a new question has &gt;= 0.92 cosine similarity to a cached question for that document, the cached answer returns immediately."),
        ("Q14. What is the difference between normal caching and semantic caching?",
         "Normal caching only matches identical strings (so 'Summarize this PDF' vs 'Give me a summary of this file' misses). Semantic caching compares vector meaning, so rephrased questions with >= 92% similarity still hit the cache!"),
        ("Q15. How do you prevent hallucinations and what if the Gemini API goes down?",
         "Every retrieved page is tracked, and HallucinationGuardrailService checks all [Page X] citations in the answer against the retrieved context pages (flagging any unverified page). Plus, if the Gemini API key fails or times out, TokenBrief seamlessly falls back to its built-in _local_synthesis engine so the user never sees a crash."),
        ("Q16. Why did we remove the old 25% similarity blocker?",
         "A strict 25% vector similarity threshold previously blocked valid casual greetings ('hlo') and typo queries ('summerize the core parts only'). Removing that false blocker lets greetings reply naturally and allows summary/section pipelines to handle broad intents."),
        ("Q17. How do you send OTP emails if free cloud hosts block SMTP ports?",
         "Cloud platforms like Render often restrict raw SMTP ports (465/587). EmailNotificationService first sends an HTTPS POST request on port 443 to a Google Apps Script webhook that delivers HTML OTP emails reliably, with Resend HTTPS and Gmail SMTP kept as backup fallbacks."),
        ("Q18. How is user authentication secured?",
         "Passwords use bcrypt hashing, email verification uses 10-minute OTPs, and logins return HS256-signed JWT access and refresh tokens (7-day expiry). On the frontend, silent refresh avoids sudden logouts."),
        ("Q19. How do Quiz Generation and the Knowledge Graph work?",
         "QuizEngineService spreads chunks evenly across the PDF and generates Easy, Medium, or Hard MCQs with 3 unique distractors and explanations, saving attempts per user. EntityKnowledgeGraphService extracts technical skills, concepts, and organizations and returns JSON nodes and links for interactive visualization."),
        ("Q20. What database tables exist in your PostgreSQL schema?",
         "All 14 tables in models.py are: user_accounts, email_verifications, document_records, document_sections, document_chunk_records (Vector 384), semantic_query_cache (Vector 384), conversation_threads, conversation_messages, quiz_questions, quiz_attempts, quiz_answers, query_logs, document_entities, and user_annotations."),
    ]

    for q_txt, a_txt in viva_qa:
        story.append(KeepTogether([
            Paragraph(q_txt, q_style),
            Paragraph(a_txt, a_style),
        ]))

    # =========================================================================
    # PART 5: 2-MINUTE LIVE DEMO SCRIPT
    # =========================================================================
    story.append(Spacer(1, 6))
    story.append(Paragraph("5. 2-Minute Live Demo Script (What to Click in Front of Examiners)", h1_style))
    demo_box = _make_box([
        Paragraph("1. <b>Login / Dashboard:</b> Sign in and show the clean Next.js workspace with uploaded documents listed.", bullet_style),
        Paragraph("2. <b>Ask Executive Summary:</b> Click the Executive Summary prompt chip on your 60-page report PDF &mdash; show how it skips cover pages and summarizes Main Goals (Abstract), Core Chapters (1&ndash;5), and Conclusions with clickable [Page X] badges.", bullet_style),
        Paragraph("3. <b>Ask Targeted Section:</b> Type <i>'explain section 4'</i> &mdash; show how it jumps directly to Pages 35&ndash;39 (Implementation &amp; Testing) instead of the Table of Contents.", bullet_style),
        Paragraph("4. <b>Show Semantic Cache Speed:</b> Ask a slightly rephrased summary question and highlight the fast cached response badge.", bullet_style),
        Paragraph("5. <b>Show Extra Tabs:</b> Open <b>Quiz Studio</b> (generate 5 MCQs), <b>Knowledge Graph</b> (show extracted entities), <b>Compare</b>, <b>Analytics</b> (latency metrics), and click <b>Export PDF</b> to download a session report.", bullet_style),
    ], bg_hex="#f0fdf4", border_hex="#86efac", left_accent_hex="#059669")
    story.append(demo_box)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 6: QUICK FILE & FOLDER CHEAT SHEET
    # =========================================================================
    story.append(Paragraph("6. Quick File &amp; Folder Map (For Code-Walkthrough Questions)", h1_style))
    map_rows = [
        [Paragraph("<font color='white'><b>File / Folder</b></font>", body_style), Paragraph("<font color='white'><b>What It Does</b></font>", body_style)],
        [Paragraph("<b>main.py, config.py, database.py</b>", body_style), Paragraph("FastAPI app startup, CORS for Vercel, environment config, and async Neon PostgreSQL + pgvector setup.", body_style)],
        [Paragraph("<b>models.py, schemas.py</b>", body_style), Paragraph("All 14 SQLAlchemy PostgreSQL tables (pgvector Vector(384)) and Pydantic API request/response schemas.", body_style)],
        [Paragraph("<b>routers/auth.py, security.py, email_service.py</b>", body_style), Paragraph("Signup/OTP verification (Apps Script webhook, Resend, SMTP), bcrypt hashing, and 7-day JWT auth.", body_style)],
        [Paragraph("<b>routers/documents.py, chunking_service.py, embedding_service.py</b>", body_style), Paragraph("15 MB PDF/TXT/MD upload, 1200-char chunking (35-word overlap), zero-OOM 384-d embeddings, background indexing.", body_style)],
        [Paragraph("<b>routers/qa.py, qa_service.py, search_service.py, rerank_service.py</b>", body_style), Paragraph("Targeted section lookup, Full-File Digest summaries, RRF Hybrid Search, candidate reranking, Gemini 2.5 Flash + local fallback.", body_style)],
        [Paragraph("<b>services/cache_service.py, guardrails_service.py</b>", body_style), Paragraph("Two-level L1/L2 semantic query cache (0.92 threshold) and [Page X] citation verification.", body_style)],
        [Paragraph("<b>routers/quiz.py, entities.py, export.py, analytics.py</b>", body_style), Paragraph("Interactive MCQ Quiz Studio, Knowledge Graph entities, ReportLab PDF export, and latency analytics.", body_style)],
        [Paragraph("<b>frontend/app/dashboard/page.tsx</b>", body_style), Paragraph("Next.js 14 workspace UI, chat interface, clickable source badges, quiz panel, compare view, and graph viewer.", body_style)],
        [Paragraph("<b>render.yaml, vercel.json</b>", body_style), Paragraph("Cloud deployment configs for Render backend (tokenbrief-backend) and Vercel Next.js frontend.", body_style)],
    ]
    map_table = Table(map_rows, colWidths=[195, 317])
    map_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(map_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF cleanly: {output_path}")


if __name__ == "__main__":
    out_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "TokenBrief_Easy_Viva_Guide.pdf",
    )
    generate_easy_viva_pdf(out_file)
