# Action-Oriented Agentic Tutor

A lightweight Web prototype that accepts unstructured learning materials, indexes a student's learning trace with an OpenAI-compatible LLM plus a separately configurable embedding service, detects learning gaps, and produces action-oriented nudges without giving direct answers.

## Backend Environment

Use `uv` only. Do not use the system Python interpreter.

```bash
uv --cache-dir .uv-cache python install --install-dir .uv-python 3.11
uv --cache-dir .uv-cache venv --python .uv-python/cpython-3.11.15-macos-aarch64-none/bin/python3.11 .venv
uv --cache-dir .uv-cache sync
```

If Python 3.11 cannot be downloaded but an existing uv-managed 3.12 is available, use `uv --cache-dir .uv-cache venv --python 3.12 .venv`. The project supports `>=3.11,<3.13`, and the important rule is that `.venv` is uv-managed and not created from the system Python. If the exact Python patch directory differs, use the `python3.11` path printed by `uv --cache-dir .uv-cache python list`.

## Configuration

```bash
cp .env.example .env
```

Set the LLM and embedding services separately:

```bash
LLM_API_KEY=...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5-mini

EMBEDDING_API_KEY=...
EMBEDDING_BASE_URL=https://api.your-embedding-provider.example/v1
EMBEDDING_MODEL=your-embedding-model
```

Both services are expected to expose OpenAI-compatible endpoints: `/chat/completions` for the LLM service and `/embeddings` for the embedding service. The application reads only `LLM_*` for the LLM provider and only `EMBEDDING_*` for the embedding provider.

## Run

After copying this project to another machine, the other user needs:

- `uv`
- Node.js 18+ with `npm`
- their own `.env` file based on `.env.example`

Do not share a real `.env` file with API keys.

One-command local start/stop:

```bash
./scripts/start.sh
./scripts/stop.sh
```

Or use the management script:

```bash
./scripts/app.sh setup
./scripts/app.sh start
./scripts/app.sh stop
./scripts/app.sh restart
./scripts/app.sh status
./scripts/app.sh logs
```

`start` automatically runs the first-time setup if `.venv` or `node_modules` is missing.

The start script launches:

- Frontend: `http://127.0.0.1:5173/`
- Backend: `http://127.0.0.1:8000/`

Runtime logs are written under `.run/logs/`.

Manual start is also available:

```bash
uv --cache-dir .uv-cache run uvicorn app.main:app --app-dir backend --reload
cd frontend
npm install
npm run dev
```

Open the Vite URL and use the Web UI to parse sources, analyze traces, and export results.

## Verify

```bash
uv --cache-dir .uv-cache run python --version
uv --cache-dir .uv-cache run pytest
cd frontend
npm run build
```

Both services are configured independently. `OPENAI_API_KEY` and `OPENAI_BASE_URL` are not read by the application.

Without configured API keys, `/api/analyze` intentionally returns `503` with a clear missing-key message such as `LLM_API_KEY is not configured.` or `EMBEDDING_API_KEY is not configured.`. This keeps the prototype honest: it uses real provider paths and does not silently fabricate Trace Indexer output.
