# PawsitiveMind — Backend (FastAPI)

Async AI animal behavioral-consulting API. The Python package lives in `app/`.

## Setup

```bash
cd backend
uv sync
cp .env.example .env   # set OPENROUTER_API_KEY
uv run uvicorn app.main:app --reload   # http://localhost:8000
```

## Test

```bash
cd backend
uv run pytest
```

## Layout

```
backend/
  pyproject.toml, uv.lock, .python-version, .env
  app/
    main.py            FastAPI app  ->  app.main:app
    api/chat.py        /consultation routes (start, chat, finalize)
    core/              config, database, deps, ORM models
    schemas/           Pydantic intake + plan schemas
    services/          llm.py (LLM orchestration), prompts.py
    tests/             pytest suite
```

The chat endpoint streams `application/x-ndjson`; see `app/services/llm.py`.
`DATABASE_URL` defaults to a local SQLite file (`./pawsitive_mind.db`, created on
startup). The `plan_status` column requires a fresh DB if you have an old one —
delete `pawsitive_mind.db` so `create_all` rebuilds it.
