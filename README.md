# NPAPI — Sistema de Gerenciamento de Tarefas

API REST construída com **FastAPI** + **MongoDB Atlas** com autenticação JWT, frontend embutido, proteção anti-ataque e rate limiting.

## Requisitos

- Python 3.11+
- Conta no MongoDB Atlas 

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Edite o arquivo `.env` se necessário:

```env
MONGODB_URI=
MONGODB_DB_NAME=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
```

## Execução

```bash
uvicorn app.main:app --reload
```

Acesse:
- **Frontend**: http://localhost:8000/
- **Documentação interativa**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## Funcionalidades

- Cadastro de conta (1 conta por IP)
- Login com JWT
- CRUD completo de tarefas (título, descrição, status)
- Rate limiting: 60 requisições por minuto por IP
- Tela de erro 404 customizada com link para /docs
- Frontend integrado sem dependências externas

## Testes

> Requer MongoDB local na porta 27017 para os testes.

```bash
pytest
```

## Rotas da API

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | /auth/register | Criar conta | Não |
| POST | /auth/login | Autenticar | Não |
| GET | /tasks | Listar tarefas | Sim |
| POST | /tasks | Criar tarefa | Sim |
| GET | /tasks/{id} | Buscar tarefa | Sim |
| PATCH | /tasks/{id}/status | Atualizar status | Sim |
| DELETE | /tasks/{id} | Remover tarefa | Sim |
| GET | /health | Health check | Não |
