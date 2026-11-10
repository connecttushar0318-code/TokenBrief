from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from database import initialize_database_tables
from routers import auth, documents, qa, admin, quiz, analytics, export, entities, annotations
from config import settings

@asynccontextmanager
async def application_lifespan(application: FastAPI):
    try:
        await initialize_database_tables()
    except Exception as initialization_error:
        print(f"Database connection warning: {initialization_error}")
    yield

app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="DocuVibe AI - Advanced RAG Intelligence Engine with Semantic Caching, Reranking, and Resend OTP Verification",
    lifespan=application_lifespan
)

import os

allowed_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_cors_origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(qa.router)
app.include_router(admin.router)
app.include_router(quiz.router)
app.include_router(analytics.router)
app.include_router(export.router)
app.include_router(entities.router)
app.include_router(annotations.router)

@app.get("/")
@app.get("/health")
@app.get("/healthz")
async def get_system_status():
    return {
        "service": settings.app_name,
        "version": "2.0.0",
        "status": "operational",
        "documentation_url": "/docs",
        "max_upload_size_mb": settings.max_upload_size_mb,
        "email_diagnostics": {
            "smtp_configured": bool(settings.gmail_app_password),
            "smtp_sender": settings.gmail_sender_email,
            "resend_configured": bool(settings.resend_api_key)
        }
    }

@app.get("/chat", response_class=HTMLResponse)
async def serve_interactive_chat_ui():
    html_markup = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DocuVibe AI &mdash; Interactive RAG Studio</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: rgba(99, 102, 241, 0.2);
      --accent: #6366f1;
      --accent-hover: #4f46e5;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      height: 100vh;
      display: flex;
      overflow: hidden;
    }
    div.sidebar-panel {
      width: 340px;
      background: rgba(17, 24, 39, 0.95);
      border-right: 1px solid var(--card-border);
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .brand {
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(90deg, #6366f1, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .upload-zone {
      border: 2px dashed rgba(99, 102, 241, 0.4);
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      cursor: pointer;
      background: rgba(15, 23, 42, 0.6);
      transition: all 0.2s;
    }
    .upload-zone:hover {
      border-color: #a855f7;
      background: rgba(99, 102, 241, 0.1);
    }
    .file-limits {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 6px;
    }
    div.doc-list-area {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .doc-item {
      background: rgba(30, 41, 59, 0.5);
      border: 1px solid rgba(148, 163, 184, 0.15);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 13px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .doc-item span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 190px;
    }
    .summary-btn {
      background: rgba(99, 102, 241, 0.2);
      border: 1px solid rgba(99, 102, 241, 0.4);
      color: #c7d2fe;
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 6px;
      cursor: pointer;
    }
    .summary-btn:hover { background: var(--accent); color: white; }
    div.main-chat-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.08), transparent 40%);
    }
    div.messages-scroll-area {
      flex: 1;
      overflow-y: auto;
      padding: 32px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .msg {
      max-width: 75%;
      padding: 16px 20px;
      border-radius: 16px;
      line-height: 1.6;
      font-size: 14.5px;
    }
    .user-msg {
      align-self: flex-end;
      background: linear-gradient(135deg, #4f46e5, #6366f1);
      color: white;
      border-bottom-right-radius: 4px;
    }
    .bot-msg {
      align-self: flex-start;
      background: rgba(30, 41, 59, 0.85);
      border: 1px solid rgba(148, 163, 184, 0.15);
      border-bottom-left-radius: 4px;
    }
    .cache-badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 2px 8px;
      border-radius: 9999px;
      margin-bottom: 8px;
    }
    .sources-box {
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid rgba(148, 163, 184, 0.2);
      font-size: 12px;
      color: #cbd5e1;
    }
    .source-pill {
      background: rgba(15, 23, 42, 0.7);
      padding: 4px 8px;
      border-radius: 6px;
      display: inline-block;
      margin: 4px 4px 0 0;
      border: 1px solid rgba(99, 102, 241, 0.3);
    }
    div.bottom-input-bar {
      padding: 20px 32px;
      border-top: 1px solid var(--card-border);
      background: rgba(15, 23, 42, 0.95);
      display: flex;
      gap: 12px;
      align-items: center;
    }
    input.chat-text-input {
      flex: 1;
      background: rgba(30, 41, 59, 0.6);
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 10px;
      padding: 14px 18px;
      color: white;
      font-size: 14.5px;
      outline: none;
    }
    input.chat-text-input:focus { border-color: var(--accent); }
    button.send-action-btn {
      background: var(--accent);
      border: none;
      color: white;
      padding: 14px 24px;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    button.send-action-btn:hover { background: var(--accent-hover); }
  </style>
</head>
<body>
  <div class="sidebar-panel">
    <div class="brand">DocuVibe AI</div>
    <div class="upload-zone" onclick="document.getElementById('file-input').click()">
      <input type="file" id="file-input" style="display:none" accept=".pdf,.txt,.md" onchange="uploadFile(this)">
      <strong>Upload Document</strong>
      <div class="file-limits">PDF, TXT, MD (100B &mdash; 15MB)</div>
    </div>
    <div style="font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;">Indexed Documents</div>
    <div id="doc-list" class="doc-list-area">Loading...</div>
    <div style="font-size:11px;color:#64748b;text-align:center;">Semantic Cache &bull; HNSW Reranker &bull; Active</div>
  </div>

  <div class="main-chat-area">
    <div id="chat-messages" class="messages-scroll-area">
      <div class="msg bot-msg">
        <strong>Welcome to DocuVibe AI Studio!</strong><br>
        Upload your PDF, text, or markdown document in the sidebar, or ask a question directly across indexed knowledge.
      </div>
    </div>
    <div class="bottom-input-bar">
      <input type="text" id="chat-input" class="chat-text-input" placeholder="Ask a question about your documents..." onkeydown="if(event.key==='Enter') sendQuestion()">
      <button id="send-btn" class="send-action-btn" onclick="sendQuestion()">Send</button>
    </div>
  </div>

  <script>
    let currentSessionId = localStorage.getItem('docuvibe_session') || '';

    async function loadDocuments() {
      try {
        const res = await fetch('/api/documents');
        const docs = await res.json();
        const list = document.getElementById('doc-list');
        if (!docs.length) {
          list.innerHTML = '<div style="font-size:12px;color:#64748b;">No documents uploaded yet.</div>';
          return;
        }
        list.innerHTML = docs.map(d => `
          <div class="doc-item">
            <span title="${d.filename}">${d.filename}</span>
            <button class="summary-btn" onclick="summarizeDoc(${d.id})">Summary</button>
          </div>
        `).join('');
      } catch (err) {
        console.error(err);
      }
    }

    async function uploadFile(input) {
      if (!input.files.length) return;
      const file = input.files[0];
      if (file.size > 15 * 1024 * 1024) {
        alert('File exceeds 15 MB limit');
        return;
      }
      const formData = new FormData();
      formData.append('uploaded_file', file);
      const list = document.getElementById('doc-list');
      list.innerHTML = '<div style="font-size:12px;color:#38bdf8;">Uploading & Vectorizing...</div>';
      try {
        const res = await fetch('/api/documents/upload', { method: 'POST', body: formData });
        if (!res.ok) {
          const err = await res.json();
          alert(err.detail || 'Upload failed');
        }
      } catch (e) {
        alert('Upload error: ' + e);
      }
      loadDocuments();
    }

    async function summarizeDoc(id) {
      addMessage('Summarize this document for me.', true);
      try {
        const res = await fetch(`/api/documents/${id}/summary`, { method: 'POST' });
        const data = await res.json();
        let html = `<strong>Summary for ${data.filename}</strong><br><br>${data.executive_summary}<br><br><strong>Key Takeaways:</strong><ul>`;
        data.key_takeaways.forEach(t => html += `<li>${t}</li>`);
        html += `</ul><br><strong>Topics:</strong> ${data.topics.join(', ')}`;
        addMessage(html, false);
      } catch (err) {
        addMessage('Failed to generate summary: ' + err, false);
      }
    }

    async function sendQuestion() {
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;
      addMessage(text, true);
      input.value = '';

      try {
        const res = await fetch('/api/qa/quick-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message_text: text, session_id: currentSessionId })
        });
        const data = await res.json();
        currentSessionId = data.session_id;
        localStorage.setItem('docuvibe_session', currentSessionId);

        let content = '';
        if (data.cache_hit) {
          content += '<div class="cache-badge">&#9889; Served via Semantic Cache (3ms)</div><br>';
        }
        content += data.answer;
        if (data.sources && data.sources.length) {
          content += '<div class="sources-box"><strong>Sources:</strong><br>';
          data.sources.forEach(s => {
            content += `<div class="source-pill">&bull; ${s.document_filename} (p.${s.source_page_number || 1}) &mdash; ${s.similarity_percentage}%</div>`;
          });
          content += '</div>';
        }
        addMessage(content, false);
      } catch (err) {
        addMessage('Error: ' + err, false);
      }
    }

    function addMessage(html, isUser) {
      const box = document.getElementById('chat-messages');
      const msg = document.createElement('div');
      msg.className = `msg ${isUser ? 'user-msg' : 'bot-msg'}`;
      msg.innerHTML = html;
      box.appendChild(msg);
      box.scrollTop = box.scrollHeight;
    }

    loadDocuments();
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_markup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
