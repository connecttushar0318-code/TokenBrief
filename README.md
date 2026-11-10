# TokenBrief &mdash; Autonomous AI Document Intelligence & Enterprise Workspace

[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql)](https://neon.tech/)
[![Google Gemini](https://img.shields.io/badge/Gemini-2.5_Pro_%2F_Flash-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)

---

## 🌐 Live Deployments

| Component | Platform | Status | Live Link |
|---|---|---|---|
| **Frontend Web App** | **Vercel** | ![Production Ready](https://img.shields.io/badge/Vercel-Live-brightgreen?style=flat-square&logo=vercel) | [https://token-brief.vercel.app](https://token-brief.vercel.app) |
| **Backend API Server** | **Render / Koyeb / Docker** | ![API Active](https://img.shields.io/badge/FastAPI-Online-teal?style=flat-square&logo=fastapi) | [https://tokenbrief-backend.onrender.com](https://tokenbrief-backend.onrender.com) &bull; [Swagger Docs](https://tokenbrief-backend.onrender.com/docs) |
| **Neon PostgreSQL + pgvector** | **AWS us-east-2** | ![Database Connected](https://img.shields.io/badge/Neon-Connected-blue?style=flat-square&logo=postgresql) | Managed Cloud Database Cluster |

---

**TokenBrief** is an enterprise-grade Document Intelligence and Retrieval-Augmented Generation (RAG) platform. It transforms static PDFs, technical lecture notes, resumes, and enterprise manuals into structured knowledge through conversational Q&A, interactive quiz generation, multi-document comparison, entity knowledge graph visualization, real-time analytics, and automated PDF export.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Next.js 14 App Router (Frontend)                        │
│  • Workspace & Chat Studio    • Interactive Quiz Studio (Sliders & MCQ)     │
│  • Multi-Doc Comparison View  • Entity Knowledge Graph SVG Visualizer       │
│  • Real Analytics Dashboard   • Web Speech API Audio Briefings              │
│  • User Profile & Security    • In-Document Citation Highlighting & Notes   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HttpOnly SameSite=Strict JWT + REST
┌──────────────────────────────────────v──────────────────────────────────────┐
│                    FastAPI Engine (Backend API Tier)                        │
│  • Dual-Token Auth (bcrypt + PyJWT)       • Query Intent Classifier Router   │
│  • Guardrail Abstention Gate (<25%)       • Structure-Aware PDF Text Parser  │
│  • Reciprocal Rank Fusion (BM25 + Vector) • Async Map-Reduce Summarizer     │
│  • ReportLab Multi-Page PDF Exporter      • Real-Time Query & Latency Logger │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Neon DB Connection Pool (SSL)
┌──────────────────────────────────────v──────────────────────────────────────┐
│             PostgreSQL + pgvector (Database & Storage Tier)                 │
│  • users & email_verifications            • document_records & chunks        │
│  • document_sections (Hierarchical)       • query_semantic_cache (HNSW)      │
│  • quiz_questions, attempts & answers     • document_entities (Knowledge)    │
│  • user_annotations (Sticky Notes)        • query_logs (Live Telemetry)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Engineering Features

### 1. Hierarchical Map-Reduce Summarization for 50+ Page PDFs
Standard RAG pipelines suffer from the "Top-K retrieval trap"—asking for an executive summary only retrieves 3–5 chunks (~2% of the file), ignoring the rest. TokenBrief solves this via a two-tier hierarchy:
- **Tier 1 (Leaf Chunks)**: 400–600 token chunks stored with pgvector embeddings for fine-grained factual Q&A.
- **Tier 2 (Hierarchical Batches)**: Groups documents into 5-page batches. At upload time, an asynchronous Map-Reduce pipeline (`asyncio.gather` with a concurrency semaphore) digests each batch into structured bullet points stored in `document_sections`. Full-document summaries synthesize these pre-computed batches in under 3 seconds with 100% document coverage.

### 2. Query Intent Router
Before querying the vector database, incoming prompts pass through an intent classifier:
- `GLOBAL_SUMMARY` &rarr; Routes to pre-computed section Map-Reduce synthesis.
- `MULTI_DOC_COMPARE` &rarr; Routes to cross-document structured extraction.
- `SPECIFIC_FACT` &rarr; Routes to Hybrid BM25 + Vector Search with Reranking.

### 3. Hybrid Search with Reciprocal Rank Fusion (RRF)
Combines dense semantic vector retrieval (pgvector cosine similarity) with sparse lexical retrieval (BM25 token frequency). Results are fused using Reciprocal Rank Fusion:
$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{vector}, \text{bm25}\}} \frac{1}{60 + \text{rank}_m(d)}$$
This guarantees that queries containing specific keywords, IDs, or resume headings are never dropped even if exact keyword density is low.

### 4. Hallucination Guardrails & Abstention Gate
- **Pre-LLM Grounding Filter**: If retrieved context similarity scores fall below the 25% threshold, the system abstains from hallucinating and prompts the user to broaden their search or upload the relevant file.
- **Post-LLM Citation Verifier**: Scans model responses for source citations, verifying that page references match actual database chunk boundaries.

---

## Interactive Workspace Modules

| Module | Description | Technical Implementation |
|---|---|---|
| **Interactive Quiz Studio** | Generates MCQs directly from uploaded documents. Features an interactive **question count slider (3–15)**, difficulty toggles (Easy / Medium / Hard), instant grading, grounded page citations, and Spaced Repetition review mode. | Dynamic prompt synthesis, JSON schema validation, relational tracking in `quiz_questions` and `quiz_attempts`. |
| **Side-by-Side Document Comparison** | Compares 2 or more files simultaneously with a structured category-by-criterion matrix, shared topic pills, unique topic pills per document, and an executive verdict. | Cross-document Map-Reduce extraction with JSON schema output. |
| **Entity Knowledge Graph Canvas** | Interactive SVG network canvas visualizing extracted **Skills, Concepts, Tools, Organizations, and People** with zoom controls, type filters, and a node inspection card. | Dynamic entity extraction, relationship weighting, and SVG physics coordinate projection. |
| **Real Analytics Dashboard** | Telemetry dashboard showing total queries, average response latency in milliseconds, cache hit ratio, and token estimations, plus an **interactive SVG Donut/Pie Chart** of model distribution (`gemini-2.5-pro` vs. `gemini-2.5-flash`). | Background query logging (`query_logs`), rolling daily aggregations, and zero-dependency SVG geometry. |
| **Branded PDF Export** | One-click button in the header that compiles the active session briefing, Q&A exchanges, citations, and metrics into a branded, multi-page downloadable PDF. | ReportLab 5.x PDF Canvas, custom `ParagraphStyle` hierarchy, and streaming byte response. |
| **Citation Annotations & Highlighting** | Click any citation source to inspect the passage, select text, choose from a **5-color palette**, and attach persistent sticky notes. | Selection API, relational `user_annotations` table with chunk coordinate bindings. |
| **Text-to-Speech Audio Briefing** | Listen to executive summaries or answer briefs hands-free with an animated play/stop toggle. | Browser-native Web Speech Synthesis API with Markdown cleanup regex. |

---

## API Catalog

### Authentication & User Profiles
- `POST /api/auth/register` &mdash; Account registration with disposable email filtering & OTP dispatch
- `POST /api/auth/verify-email` &mdash; OTP verification and HttpOnly JWT issuance
- `POST /api/auth/login` &mdash; Password authentication and session start
- `POST /api/auth/logout` &mdash; Clear authentication cookies
- `GET  /api/auth/me` &mdash; Fetch profile of the logged-in user

### Document Management & Summarization
- `POST /api/documents/upload` &mdash; Upload PDF/TXT/MD, parse text, generate chunks, extract entities, and compute embeddings
- `GET  /api/documents` &mdash; List workspace documents with page and chunk metadata
- `GET  /api/documents/{id}` &mdash; Retrieve single document details
- `POST /api/documents/{id}/summary` &mdash; Generate Map-Reduce executive summary & key takeaways
- `DELETE /api/documents/{id}` &mdash; Delete document and cascade all associated chunks, entities, and notes

### Hybrid Search & Conversational Q&A
- `POST /api/qa/quick-chat` &mdash; Conversational Q&A endpoint with intent routing, semantic caching, and grounded sources
- `POST /api/qa/ask` &mdash; Structured Q&A endpoint with detailed citation metadata
- `GET  /api/qa/cache/stats` &mdash; Semantic cache hit ratio and count
- `DELETE /api/qa/cache` &mdash; Flush semantic cache

### Quiz Studio & Evaluation
- `POST /api/quiz/generate` &mdash; Generate custom MCQ quiz with question count and difficulty parameters
- `POST /api/quiz/submit` &mdash; Grade quiz answers, compute percentage score, and return explanations
- `GET  /api/quiz/attempts` &mdash; List historical quiz attempts and scores
- `GET  /api/quiz/spaced-review` &mdash; Retrieve incorrectly answered questions for spaced repetition

### Document Comparison
- `POST /api/comparison/compare` &mdash; Perform multi-document structured matrix comparison

### Knowledge Graph
- `GET  /api/entities/graph` &mdash; Retrieve entity nodes and relationship links for workspace or a specific document

### Real Analytics
- `GET  /api/analytics/dashboard` &mdash; Telemetry metrics, daily query trends, model breakdown, and recent query logs

### In-Document Annotations
- `POST   /api/annotations` &mdash; Save text highlight and sticky note
- `GET    /api/annotations/document/{doc_id}` &mdash; Get all highlights for a document
- `GET    /api/annotations/chunk/{chunk_id}` &mdash; Get highlights for a specific chunk
- `DELETE /api/annotations/{id}` &mdash; Delete an annotation

### PDF Export
- `POST /api/export/pdf` &mdash; Compile and stream downloadable ReportLab PDF briefing

---

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL database with `pgvector` extension (e.g., NeonDB)
- Google Gemini API key (via Google AI Studio)

### 1. Clone the Repository
```bash
git clone https://github.com/connecttushar0318-code/TokenBrief.git
cd TokenBrief
```

### 2. Backend Configuration
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:password@your-neon-host/tokenbrief?sslmode=require
JWT_SECRET=your-secure-jwt-secret-key-32-chars-minimum
GEMINI_API_KEY=your-gemini-api-key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=connect.tushar0318@gmail.com
EMAIL_PASS=your-gmail-app-password
```

Activate the virtual environment and install dependencies:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

Start the FastAPI backend:
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`
- Redoc Documentation: `http://127.0.0.1:8000/redoc`

### 3. Frontend Configuration
Navigate to the `frontend/` directory and configure `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Install packages and run the Next.js development server:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 🚀 Cloud Deployment Guide

### Deploying Frontend to Vercel
1. Import repository `connecttushar0318-code/TokenBrief` into [Vercel](https://vercel.com).
2. In **Build & Development Settings**:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Next.js`
   - **Output Directory**: Default (`.next` &mdash; toggle override off)
3. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL`: Your deployed backend URL (e.g. `https://tokenbrief-backend.onrender.com`).

### Deploying Backend to Render / Koyeb (Docker / Python)
1. Go to [Render Dashboard](https://dashboard.render.com/) &rarr; **New Web Service** &rarr; Connect GitHub repository.
2. Select **Runtime: Python 3** (or **Docker** using the included `Dockerfile`).
   - **Build Command**: `pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add the following **Environment Variables**:
   - `DATABASE_URL`: `postgresql+asyncpg://neondb_owner:...@ep-restless-moon-...neon.tech/neondb?sslmode=require`
   - `SECRET_KEY`: `b71c265324df...`
   - `GEMINI_API_KEY`: Your Google AI Studio API Key
   - `GEMINI_MODEL`: `gemini-2.5-flash`
   - `EMBEDDING_MODEL_NAME`: `all-MiniLM-L6-v2`
   - `GMAIL_SENDER_EMAIL`: `connect.tushar0318@gmail.com`
   - `GMAIL_APP_PASSWORD`: `qgms sczr hxnh bhuq`

---

## Production Verification

To test the complete production build:
```bash
# Frontend
npm --prefix frontend run build

# Backend Test Suite
python -m pytest tests/
```

---

## License

This project is licensed under the MIT License.
