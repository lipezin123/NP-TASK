import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.database import close_client, init_indexes
from app.routers import auth, tasks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)

_NOT_FOUND_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>404 — NPAPI</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0f0f13;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif}
  .container{text-align:center;padding:2rem}
  .code{font-size:8rem;font-weight:900;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1}
  h1{font-size:1.5rem;margin:1rem 0 .5rem;color:#94a3b8}
  p{color:#64748b;margin-bottom:2rem}
  a{display:inline-block;padding:.75rem 2rem;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-radius:.5rem;text-decoration:none;font-weight:600;transition:opacity .2s}
  a:hover{opacity:.85}
</style>
</head>
<body>
<div class="container">
  <div class="code">404</div>
  <h1>Página não encontrada</h1>
  <p>A rota que você tentou acessar não existe nesta API.</p>
  <a href="/docs">Ver Documentação</a>
</div>
</body>
</html>"""

_FRONTEND_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NPAPI — Task Manager</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  :root{
    --bg:#0f0f13;
    --surface:#1a1a24;
    --surface2:#22222f;
    --border:#2d2d3d;
    --accent:#6366f1;
    --accent2:#8b5cf6;
    --text:#e2e8f0;
    --muted:#94a3b8;
    --danger:#ef4444;
    --success:#22c55e;
    --warning:#f59e0b;
  }
  body{min-height:100vh;background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif}
  .nav{display:flex;align-items:center;justify-content:space-between;padding:1rem 2rem;background:var(--surface);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
  .logo{font-size:1.25rem;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .nav-actions{display:flex;gap:.75rem;align-items:center}
  .btn{padding:.5rem 1.25rem;border-radius:.4rem;border:none;cursor:pointer;font-size:.875rem;font-weight:600;transition:all .2s}
  .btn-primary{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}
  .btn-primary:hover{opacity:.85;transform:translateY(-1px)}
  .btn-ghost{background:transparent;color:var(--muted);border:1px solid var(--border)}
  .btn-ghost:hover{background:var(--surface2);color:var(--text)}
  .btn-danger{background:var(--danger);color:#fff;font-size:.75rem;padding:.35rem .75rem}
  .btn-danger:hover{opacity:.85}
  .btn-sm{padding:.35rem .85rem;font-size:.8rem}
  main{max-width:860px;margin:0 auto;padding:2rem 1rem}
  .page{display:none}
  .page.active{display:block}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:.75rem;padding:1.5rem;margin-bottom:1rem}
  .card h2{font-size:1.1rem;margin-bottom:1.25rem;color:var(--text)}
  .field{margin-bottom:1rem}
  .field label{display:block;font-size:.8rem;color:var(--muted);margin-bottom:.35rem;font-weight:500;text-transform:uppercase;letter-spacing:.05em}
  .field input,.field select{width:100%;padding:.65rem .9rem;background:var(--surface2);border:1px solid var(--border);border-radius:.4rem;color:var(--text);font-size:.9rem;outline:none;transition:border-color .2s}
  .field input:focus,.field select:focus{border-color:var(--accent)}
  .field textarea{width:100%;padding:.65rem .9rem;background:var(--surface2);border:1px solid var(--border);border-radius:.4rem;color:var(--text);font-size:.9rem;outline:none;resize:vertical;min-height:80px;transition:border-color .2s;font-family:inherit}
  .field textarea:focus{border-color:var(--accent)}
  .alert{padding:.75rem 1rem;border-radius:.4rem;font-size:.875rem;margin-bottom:1rem;display:none}
  .alert.show{display:block}
  .alert-error{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#fca5a5}
  .alert-success{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);color:#86efac}
  .tabs{display:flex;gap:.5rem;margin-bottom:1.5rem;border-bottom:1px solid var(--border);padding-bottom:0}
  .tab{padding:.6rem 1.25rem;cursor:pointer;font-size:.875rem;font-weight:600;color:var(--muted);border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .2s}
  .tab.active{color:var(--accent);border-bottom-color:var(--accent)}
  .task-list{display:flex;flex-direction:column;gap:.75rem}
  .task-item{background:var(--surface2);border:1px solid var(--border);border-radius:.6rem;padding:1rem 1.25rem;display:flex;align-items:flex-start;justify-content:space-between;gap:1rem}
  .task-info{flex:1;min-width:0}
  .task-title{font-weight:600;font-size:.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .task-desc{font-size:.8rem;color:var(--muted);margin-top:.25rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .task-meta{display:flex;align-items:center;gap:.5rem;margin-top:.5rem;flex-wrap:wrap}
  .task-id{font-size:.7rem;color:var(--muted);font-family:monospace;display:flex;align-items:center;gap:.3rem}
  .btn-copy{background:none;border:none;cursor:pointer;color:var(--muted);padding:.1rem .3rem;border-radius:.25rem;font-size:.7rem;transition:all .15s;line-height:1}
  .btn-copy:hover{background:var(--surface);color:var(--text)}
  .btn-copy.copied{color:var(--success)}
  .badge{padding:.2rem .6rem;border-radius:9999px;font-size:.7rem;font-weight:700;text-transform:uppercase}
  .badge-pending{background:rgba(245,158,11,.15);color:var(--warning)}
  .badge-in_progress{background:rgba(99,102,241,.15);color:#a5b4fc}
  .badge-done{background:rgba(34,197,94,.15);color:var(--success)}
  .task-actions{display:flex;gap:.5rem;flex-shrink:0;align-items:center}
  select.status-select{background:var(--surface);border:1px solid var(--border);color:var(--text);padding:.3rem .5rem;border-radius:.3rem;font-size:.75rem;cursor:pointer}
  .empty{text-align:center;padding:3rem;color:var(--muted)}
  .section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem}
  .section-header h2{font-size:1.1rem}
  .search-bar{display:flex;gap:.5rem;margin-bottom:1rem}
  .search-bar input{flex:1;padding:.6rem .9rem;background:var(--surface2);border:1px solid var(--border);border-radius:.4rem;color:var(--text);font-size:.875rem;outline:none;font-family:monospace;transition:border-color .2s}
  .search-bar input:focus{border-color:var(--accent)}
  .search-bar input::placeholder{font-family:'Segoe UI',system-ui,sans-serif;font-size:.875rem}
  .spinner{display:inline-block;width:1rem;height:1rem;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle;margin-right:.4rem}
  @keyframes spin{to{transform:rotate(360deg)}}
  .user-info{font-size:.8rem;color:var(--muted)}
  .docs-link{font-size:.8rem;color:var(--accent);text-decoration:none}
  .docs-link:hover{text-decoration:underline}
  @media(max-width:600px){.task-item{flex-direction:column}.task-actions{width:100%;justify-content:flex-end}}
</style>
</head>
<body>

<nav class="nav">
  <span class="logo">NPAPI</span>
  <div class="nav-actions">
    <span class="user-info" id="nav-user"></span>
    <a class="docs-link" href="/docs" target="_blank">API Docs</a>
    <button class="btn btn-ghost btn-sm" id="btn-logout" style="display:none" onclick="logout()">Sair</button>
  </div>
</nav>

<main>
  <div class="page active" id="page-auth">
    <div style="max-width:400px;margin:3rem auto">
      <div class="tabs">
        <div class="tab active" onclick="switchTab('login')">Entrar</div>
        <div class="tab" onclick="switchTab('register')">Criar Conta</div>
      </div>

      <div id="auth-alert" class="alert"></div>

      <div class="card" id="form-login">
        <h2>Acesse sua conta</h2>
        <div class="field"><label>Username</label><input id="l-username" type="text" placeholder="seu_usuario" autocomplete="username"></div>
        <div class="field"><label>Senha</label><input id="l-password" type="password" placeholder="••••••" autocomplete="current-password"></div>
        <button class="btn btn-primary" style="width:100%" onclick="doLogin()">Entrar</button>
      </div>

      <div class="card" id="form-register" style="display:none">
        <h2>Criar conta</h2>
        <div class="field"><label>Username</label><input id="r-username" type="text" placeholder="seu_usuario" autocomplete="username"></div>
        <div class="field"><label>E-mail</label><input id="r-email" type="email" placeholder="email@exemplo.com" autocomplete="email"></div>
        <div class="field"><label>Senha</label><input id="r-password" type="password" placeholder="Mínimo 6 caracteres" autocomplete="new-password"></div>
        <button class="btn btn-primary" style="width:100%" onclick="doRegister()">Criar Conta</button>
      </div>
    </div>
  </div>

  <div class="page" id="page-tasks">
    <div class="card">
      <div class="section-header">
        <h2>Nova Tarefa</h2>
      </div>
      <div id="task-alert" class="alert"></div>
      <div class="field"><label>Título</label><input id="t-title" type="text" placeholder="Título da tarefa"></div>
      <div class="field"><label>Descrição (opcional)</label><textarea id="t-desc" placeholder="Descreva a tarefa..."></textarea></div>
      <div class="field"><label>Status inicial</label>
        <select id="t-status">
          <option value="pending">Pendente</option>
          <option value="in_progress">Em Progresso</option>
          <option value="done">Concluída</option>
        </select>
      </div>
      <button class="btn btn-primary" onclick="createTask()">Adicionar Tarefa</button>
    </div>

    <div class="card">
      <div class="section-header">
        <h2>Minhas Tarefas</h2>
        <button class="btn btn-ghost btn-sm" onclick="loadTasks()">Atualizar</button>
      </div>
      <div class="search-bar">
        <input id="search-id" type="text" placeholder="Buscar por ID da tarefa..." oninput="filterById(this.value)">
      </div>
      <div id="task-list" class="task-list">
        <div class="empty">Carregando...</div>
      </div>
    </div>
  </div>
</main>

<script>
const API = '';
let token = sessionStorage.getItem('npapi_token');
let currentUser = sessionStorage.getItem('npapi_user');

function switchTab(tab) {
  document.querySelectorAll('.tab').forEach((t, i) => t.classList.toggle('active', (tab === 'login') === (i === 0)));
  document.getElementById('form-login').style.display = tab === 'login' ? '' : 'none';
  document.getElementById('form-register').style.display = tab === 'register' ? '' : 'none';
  clearAlert('auth-alert');
}

function showAlert(id, msg, type) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = 'alert show alert-' + type;
}

function clearAlert(id) {
  const el = document.getElementById(id);
  el.className = 'alert';
}

function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function updateNav() {
  document.getElementById('nav-user').textContent = currentUser ? '@' + currentUser : '';
  document.getElementById('btn-logout').style.display = currentUser ? '' : 'none';
}

function logout() {
  token = null;
  currentUser = null;
  sessionStorage.removeItem('npapi_token');
  sessionStorage.removeItem('npapi_user');
  updateNav();
  showPage('page-auth');
}

async function request(method, path, body) {
  const headers = {'Content-Type': 'application/json'};
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(API + path, {method, headers, body: body ? JSON.stringify(body) : undefined});
  const data = await res.json().catch(() => ({}));
  return {ok: res.ok, status: res.status, data};
}

async function doLogin() {
  const username = document.getElementById('l-username').value.trim();
  const password = document.getElementById('l-password').value;
  if (!username || !password) return showAlert('auth-alert', 'Preencha todos os campos.', 'error');
  clearAlert('auth-alert');
  const {ok, data} = await request('POST', '/auth/login', {username, password});
  if (!ok) return showAlert('auth-alert', data.detail || 'Erro ao autenticar.', 'error');
  token = data.access_token;
  currentUser = username;
  sessionStorage.setItem('npapi_token', token);
  sessionStorage.setItem('npapi_user', username);
  updateNav();
  showPage('page-tasks');
  loadTasks();
}

async function doRegister() {
  const username = document.getElementById('r-username').value.trim();
  const email = document.getElementById('r-email').value.trim();
  const password = document.getElementById('r-password').value;
  if (!username || !email || !password) return showAlert('auth-alert', 'Preencha todos os campos.', 'error');
  clearAlert('auth-alert');
  const {ok, data} = await request('POST', '/auth/register', {username, email, password});
  if (!ok) return showAlert('auth-alert', data.detail || 'Erro ao registrar.', 'error');
  showAlert('auth-alert', 'Conta criada! Faça login para continuar.', 'success');
  switchTab('login');
}

async function loadTasks() {
  const list = document.getElementById('task-list');
  list.innerHTML = '<div class="empty"><span class="spinner"></span> Carregando...</div>';
  const {ok, data} = await request('GET', '/tasks');
  if (!ok) { list.innerHTML = '<div class="empty">Erro ao carregar tarefas.</div>'; return; }
  if (!data.items.length) { list.innerHTML = '<div class="empty">Nenhuma tarefa ainda. Crie sua primeira tarefa acima.</div>'; return; }
  list.innerHTML = data.items.map(t => `
    <div class="task-item" id="task-${t.id}" data-id="${t.id}">
      <div class="task-info">
        <div class="task-title">${esc(t.title)}</div>
        ${t.description ? `<div class="task-desc">${esc(t.description)}</div>` : ''}
        <div class="task-meta">
          <span class="badge badge-${t.status}">${statusLabel(t.status)}</span>
          <span class="task-id">ID: ${t.id}<button class="btn-copy" title="Copiar ID" onclick="copyId(this,'${t.id}')">📋</button></span>
        </div>
      </div>
      <div class="task-actions">
        <select class="status-select" onchange="updateStatus('${t.id}', this.value)">
          <option value="pending" ${t.status==='pending'?'selected':''}>Pendente</option>
          <option value="in_progress" ${t.status==='in_progress'?'selected':''}>Em Progresso</option>
          <option value="done" ${t.status==='done'?'selected':''}>Concluída</option>
        </select>
        <button class="btn btn-danger" onclick="deleteTask('${t.id}')">Excluir</button>
      </div>
    </div>`).join('');
}

async function createTask() {
  const title = document.getElementById('t-title').value.trim();
  const description = document.getElementById('t-desc').value.trim() || null;
  const status = document.getElementById('t-status').value;
  if (!title) return showAlert('task-alert', 'O título é obrigatório.', 'error');
  clearAlert('task-alert');
  const {ok, data} = await request('POST', '/tasks', {title, description, status});
  if (!ok) return showAlert('task-alert', data.detail || 'Erro ao criar tarefa.', 'error');
  document.getElementById('t-title').value = '';
  document.getElementById('t-desc').value = '';
  document.getElementById('t-status').value = 'pending';
  showAlert('task-alert', 'Tarefa criada com sucesso!', 'success');
  setTimeout(() => clearAlert('task-alert'), 2000);
  loadTasks();
}

async function updateStatus(id, status) {
  const {ok, data} = await request('PATCH', `/tasks/${id}/status`, {status});
  if (!ok) { showAlert('task-alert', data.detail || 'Erro ao atualizar status.', 'error'); loadTasks(); }
  else loadTasks();
}

async function deleteTask(id) {
  if (!confirm('Excluir esta tarefa?')) return;
  const {ok} = await request('DELETE', `/tasks/${id}`);
  if (ok) loadTasks();
}

function copyId(btn, id) {
  navigator.clipboard.writeText(id).then(() => {
    btn.textContent = '✓';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = '📋'; btn.classList.remove('copied'); }, 1500);
  });
}

function filterById(val) {
  const v = val.trim().toLowerCase();
  document.querySelectorAll('.task-item').forEach(el => {
    el.style.display = (!v || el.dataset.id.toLowerCase().includes(v)) ? '' : 'none';
  });
}

function statusLabel(s) {
  return {pending: 'Pendente', in_progress: 'Em Progresso', done: 'Concluída'}[s] || s;
}

function esc(str) {
  return str.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

if (token) {
  updateNav();
  showPage('page-tasks');
  loadTasks();
} else {
  updateNav();
}
</script>
</body>
</html>"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NPAPI iniciando — conectando ao MongoDB")
    await init_indexes()
    logger.info("Indexes criados com sucesso")
    yield
    await close_client()
    logger.info("NPAPI encerrado")


app = FastAPI(
    title="NPAPI",
    description="Sistema de gerenciamento de tarefas com autenticação JWT e MongoDB.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def frontend():
    return HTMLResponse(content=_FRONTEND_PAGE)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "NPAPI"}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.headers.get("accept", "").startswith("text/html"):
        return HTMLResponse(content=_NOT_FOUND_PAGE, status_code=404)
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Rota '{request.url.path}' não encontrada.",
            "docs": "/docs",
        },
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    return JSONResponse(
        status_code=405,
        content={"detail": "Método não permitido para esta rota."},
    )
