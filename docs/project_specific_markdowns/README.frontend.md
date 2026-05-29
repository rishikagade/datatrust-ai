# DataTrust AI Frontend

This folder contains the React + TypeScript + Vite frontend for DataTrust AI.

## What It Renders

- Landing page with upload and demo calls to action
- Upload flow with drag-and-drop CSV/TSV handling
- Audit dashboard with score cards, charts, score breakdown, and top issues
- Column profile page
- Filterable issue list
- AI report page
- Export/download page
- AI Audit Agent side panel with persisted conversation history

## Local Setup

From the project root:

```bash
cd frontend
npm install
VITE_BACKEND_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

The backend should be running at:

```text
http://127.0.0.1:8000
```

## Environment

The frontend reads the backend URL from:

```text
VITE_BACKEND_URL
```

If unset, it falls back to:

```text
http://localhost:8000
```

For local debugging, prefer one fresh Vite server on port `5173` and one FastAPI server on port `8000`. Stale Vite/backend processes on older ports can make the AI provider indicator look wrong.

## AI Agent Provider Indicator

The chat panel shows the last provider returned by the backend:

- `Powered by Groq · Llama 3.3 70B | No raw data sent to AI`
- `Using rule-based responses | Add GROQ_API_KEY for AI answers`
- `Groq rate limit reached — using rule-based responses | Try again in 30s`

If old local-fallback messages remain in the panel, use **Clear chat**. Chat history is persisted per audit ID in browser local storage.

## Tests And Build

```bash
cd frontend
npm test
npm run build
```

The production build currently passes with a Vite chunk-size warning. That warning is not blocking; route-level code splitting is a future optimization.
