# TokenBrief &mdash; Document Intelligence & AI Workspace

A production-ready, feature-rich Retrieval-Augmented Generation (RAG) platform combining a modern **Next.js 14 App Router** frontend with a secure **FastAPI**, **PostgreSQL + pgvector (NeonDB)**, and **Sentence Transformers / Gemini** AI backend.

---

## 3-Tier Zero-Leak Architecture

```
[ Frontend Client (Next.js 14 App Router) ]
                |
                |  Public HTTP / REST calls + HttpOnly SameSite=Strict JWT Cookies
                v
[ Backend API Tier (FastAPI Engine) ]
  • Strict CORS Whitelist (localhost:3000, 127.0.0.1:3000)
  • Direct bcrypt + PyJWT Dual-Token Security
  • Sub-5ms pgvector Semantic Query Caching
  • 2-Stage Reciprocal Reranking
  • Word-Aware Sentence Boundary Chunking
  • Gmail SMTP & Resend API Dual Verification
                |
                |  Private Connection String in .env (Zero Client-Side Exposure)
                v
[ Database Tier (PostgreSQL / NeonDB + pgvector HNSW) ]
```

---

## Key Features & Highlights

### 1. Modern Next.js App Router Frontend
- **Instant Load Speed & Pre-Rendering (SSR/SSG):** Pages are pre-rendered for immediate interaction.
- **Zero-Flash Theme Engine:** Injects a lightweight script directly into the `<head>` of `app/layout.tsx`. Reads `localStorage` or `prefers-color-scheme` before the DOM paints, preventing theme hydration flashes.
- **Dynamic Imports & Code Splitting:** Heavy interactive modules like `AnalyticsChart` are lazily loaded with animated skeleton fallbacks.
- **Next.js Edge Middleware (`middleware.ts`):** Intercepts requests to `/dashboard` before page rendering, verifying the `access_token` cookie and redirecting unauthenticated users to `/login`.
- **Zod Client-Side Form Validation:** Enforces strict validation matching the backend Pydantic schemas.

### 2. Zero-Leak Backend & Database Isolation
- Under no circumstances does the frontend query PostgreSQL directly.
- Authentication tokens are transmitted in **HttpOnly, SameSite=Lax/Strict** cookies, shielding sessions from XSS attacks.
- FastAPI's CORS middleware strictly allows only verified frontend origins with `allow_credentials=True`.

### 3. Identity Verification & Email Delivery
- Rejects disposable domains and weak passwords.
- Sends 6-digit OTP verification codes using a responsive dark-mode HTML email template via Gmail SMTP or Resend API.

### 4. Advanced RAG Pipeline
- **Sub-5ms Semantic Caching:** Queries with high cosine similarity return cached answers instantly.
- **Candidate Reranking:** 2-stage retrieval with lexical-semantic reciprocal rank scoring.
- **Overlap-Aware Chunk Stitching:** Preserves exact numerical values, scores, decimals, and removes overlap artifacts.
- **Document Summarization:** Executive summaries, structured takeaways, and dynamic domain topics on demand.

---

## API Endpoints Overview

### Authentication & Account Security
- `POST /api/auth/register` &mdash; Register account with validation; sends OTP
- `POST /api/auth/verify-email` &mdash; Verify 6-digit OTP & receive HttpOnly cookie + Access/Refresh tokens
- `POST /api/auth/resend-otp` &mdash; Resend verification code
- `POST /api/auth/login` &mdash; Authenticate with password & set HttpOnly cookie
- `POST /api/auth/refresh` &mdash; Refresh access token
- `POST /api/auth/logout` &mdash; Clear session cookies
- `POST /api/auth/forgot-password` &mdash; Request password reset OTP
- `POST /api/auth/reset-password` &mdash; Verify reset OTP & update password
- `GET /api/auth/me` &mdash; Profile of authenticated user

### Document Management & Summarization
- `POST /api/documents/upload` &mdash; Upload PDF/TXT/MD with non-blocking embedding generation
- `GET /api/documents` &mdash; List uploaded documents
- `GET /api/documents/search` &mdash; Search documents by filename
- `GET /api/documents/{id}` &mdash; Document metadata
- `POST /api/documents/{id}/summary` &mdash; Generate executive summary, key takeaways & topics
- `DELETE /api/documents/{id}` &mdash; Delete document and cascade chunks

### Semantic Search & Q&A
- `POST /api/qa/ask` &mdash; Ask question (with Semantic Caching + Reranking)
- `POST /api/qa/quick-chat` &mdash; Fast conversational Q&A endpoint for dashboard widget
- `GET /api/qa/cache/stats` &mdash; Cache hit statistics
- `DELETE /api/qa/cache` &mdash; Flush semantic cache
- `POST /api/qa/conversations` &mdash; Create multi-turn chat thread
- `GET /api/qa/conversations` &mdash; List conversation threads
- `GET /api/qa/conversations/{id}` &mdash; Get full thread history
- `POST /api/qa/conversations/{id}/messages` &mdash; Chat with memory inside a thread

---

## Running the Application

### 1. Start the FastAPI Backend
```bash
# In the project root with the virtual environment activated:
uvicorn main:app --reload --port 8000
```
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Built-in Lightweight Chat Studio: `http://localhost:8000/chat`

### 2. Start the Next.js Frontend
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:3000`
- Dashboard: `http://localhost:3000/dashboard`
- Login & OTP: `http://localhost:3000/login`
