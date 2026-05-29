# DataTrust AI — Current Diagnostic Report

**Date:** May 29, 2026  
**Status:** Feature-complete portfolio MVP; deployment and presentation polish remain  
**Backend:** FastAPI + pandas + Groq  
**Frontend:** React + TypeScript + Vite + Tailwind + Zustand  

## Executive Summary

DataTrust AI is now a functional full-stack data quality auditing application. A user can upload a CSV/TSV or run a demo dataset, receive deterministic profiling and validation results, view a weighted 0-100 quality score, explore dashboard pages, export findings, generate a PDF report, and ask audit-specific questions through an AI Audit Agent.

The core privacy boundary is implemented: deterministic rules detect issues, and the AI layer receives only sanitized aggregate audit context. Raw CSV rows and raw-value fields are not sent to Groq.

## Current Feature Matrix

| Area | Status | Notes |
|---|---|---|
| CSV/TSV upload | ✅ Complete | `POST /audit` profiles uploaded files and returns canonical audit JSON |
| Demo mode | ✅ Complete | `GET /demo/{dataset_name}` runs the live pipeline on stored sample datasets |
| Health check | ✅ Complete | `GET /health` returns `{"status":"ok"}` |
| Profiler | ✅ Complete | Computes null counts, null percentages, unique counts, inferred types, top-value counts, and numeric summaries |
| Rules engine | ✅ Complete | 11 validation categories implemented |
| Scoring | ✅ Complete | Weighted component deductions with severity multipliers |
| AI summary | ✅ Complete | Uses Groq when configured; local fallback otherwise |
| AI Audit Agent | ✅ Complete | Uses Groq when configured; data-grounded rule-based fallback otherwise |
| PDF export | ✅ Complete | `POST /report/pdf` returns `application/pdf` |
| Frontend routing | ✅ Complete | Landing, upload, dashboard, column profile, issue list, AI report, export/download, and agent flows |
| State management | ✅ Complete | Zustand stores audit results and chat history |
| Sample datasets | ✅ Complete | Three generated datasets with realistic row counts and seeded issues |
| Tests | ✅ Complete for MVP | Backend pytest and frontend Vitest coverage present |
| Environment config | ✅ Complete | `.env.example`, `backend/.env.example`, dotenv loading, and Vite backend URL support |
| Docker config | ✅ Complete | Backend `Dockerfile` and root `docker-compose.yml` present |
| Hosted deployment | ⚠️ Pending | README still marks hosted demo as coming soon |
| Portfolio screenshots | ⚠️ Pending | Screenshot paths reserved but assets not yet captured |

## Backend Snapshot

### Main Files

- `backend/app/main.py` — FastAPI entry point and endpoint definitions
- `backend/app/services/profiler.py` — dataset and column profiling
- `backend/app/rules/implementations.py` — deterministic validation rule implementations
- `backend/app/services/rules_runner.py` — rule orchestration
- `backend/app/services/scoring.py` — weighted scoring engine
- `backend/app/services/ai_summary.py` — privacy-safe AI report generation
- `backend/app/services/ai_agent.py` — conversational audit agent

### API Endpoints

| Method | Endpoint | Status | Purpose |
|---|---|---|---|
| `GET` | `/health` | ✅ | Health check |
| `GET` | `/` | ✅ | Backend root message |
| `POST` | `/audit` | ✅ | Upload CSV/TSV and run audit |
| `GET` | `/audit/{audit_id}` | ✅ | Fetch cached audit result |
| `GET` | `/demo` | ✅ | List demo datasets |
| `GET` | `/demo/{dataset_name}` | ✅ | Run live audit pipeline on sample dataset |
| `POST` | `/agent/message` | ✅ | AI Audit Agent response |
| `POST` | `/audit/{audit_id}/assistant` | ✅ | Legacy assistant endpoint for cached audit |
| `POST` | `/report/pdf` | ✅ | Download PDF report |

### AI Provider

Current provider chain:

1. `GROQ_API_KEY` set and `groq` installed → Groq API
2. Groq unavailable, rate-limited, or key missing → local rule-based fallback

Current recommended model:

```text
llama-3.3-70b-versatile
```

The older `llama-3.1-70b-versatile` model is not accepted by the currently tested Groq account, so the project defaults were updated to `llama-3.3-70b-versatile`.

### Privacy Boundary

Before any model call, `sanitize_audit_context` removes raw-value fields including:

- `sample_values`
- `raw_values`
- `row_data`
- `top_values`
- individual value arrays

The AI receives aggregate context only: dataset metadata, column names, null counts, percentages, severity labels, rule descriptions, suggested fixes, and score components.

## Rules Engine Snapshot

| Rule | Status | Purpose |
|---|---|---|
| Missing value detection | ✅ | Flags null/empty values per column |
| Duplicate row detection | ✅ | Detects exact duplicate records |
| Duplicate key detection | ✅ | Flags non-unique identifier columns |
| Invalid data type detection | ✅ | Detects values that do not match inferred type |
| Outlier detection | ✅ | Uses statistical numeric outlier checks |
| Inconsistent category detection | ✅ | Detects category variants by case, whitespace, and abbreviations |
| Date format validation | ✅ | Flags mixed or unparseable date formats |
| Numeric range check | ✅ | Uses domain-aware checks such as age, salary, discount, and percentage bounds |
| Text formatting check | ✅ | Detects whitespace and casing issues |
| Freshness check | ✅ | Flags stale date columns |
| Referential integrity check | ✅ | Detects inverted chronological pairs |

Each rule returns a structured result with rule ID, rule name, category, affected columns, affected count, affected percentage, severity, description, and suggested fix.

## Frontend Snapshot

### Main Files

- `frontend/src/App.tsx` — routing shell
- `frontend/src/pages/LandingPage.tsx` — landing and demo entry
- `frontend/src/pages/UploadPage.tsx` — upload flow
- `frontend/src/pages/AuditDashboard.tsx` — primary dashboard
- `frontend/src/pages/ColumnProfilePage.tsx` — column details
- `frontend/src/pages/IssueListPage.tsx` — filterable issues
- `frontend/src/pages/AIReportPage.tsx` — AI-written report
- `frontend/src/pages/DownloadPage.tsx` — export/download options
- `frontend/src/pages/AiAgentPage.tsx` — AI Audit Agent panel/page
- `frontend/src/store/auditStore.ts` — Zustand state and persisted chat history
- `frontend/src/api/client.ts` — backend HTTP client

### AI Agent UX

The chat panel now includes:

- Dynamic chips generated from actual audit findings
- Persisted per-audit conversation history
- A **Clear chat** button for removing stale saved conversations
- Provider status display:
  - Groq-powered
  - Rule-based fallback
  - Groq rate-limited
  - Waiting for first response

If the panel shows old local fallback text after switching providers, clear chat history and ask a new question.

## Sample Datasets

| Dataset | Rows | Intentional Issues | Expected Score |
|---|---:|---|---|
| `customer_master.csv` | 5,000 | Duplicate customer IDs, missing emails, country variants, age range issues, invalid revenue strings, exact duplicates | 55-65 |
| `sales_transactions.csv` | 15,000 | Mixed order dates, ship-before-order rows, negative totals, category variants, discounts over 100, exact duplicates | 68-78 |
| `hr_employees.csv` | 1,200 | Duplicate employee IDs, salary outliers, department variants, sparse termination dates, hire-after-termination rows, status variants | 62-72 |

Generation script:

```text
scripts/generate_sample_datasets.py
```

## Local Development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
VITE_BACKEND_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173
```

Optional Groq setup:

```bash
cp backend/.env.example backend/.env
# Add a real GROQ_API_KEY to backend/.env
```

## Verification

Known local verification results:

- Backend API focused agent test: passed
- Full backend test suite previously verified: `29 passed`
- Frontend focused AI Agent page test: `2 passed`
- Full frontend suite previously verified: `7 passed`
- Frontend production build previously verified: passes with Vite chunk-size warning
- Live provider smoke check: `POST /agent/message` returns `provider: groq` when the backend is running with a valid Groq key

## Remaining Work

### Portfolio Polish

- Replace the lightweight SVG screen previews with real captured product screenshots or GIFs when the hosted deployment is available.
- Add a hosted demo URL after deployment.

### Deployment

- Deploy backend and frontend.
- Configure production `GROQ_API_KEY`, `GROQ_MODEL`, `ALLOWED_ORIGINS`, and `VITE_BACKEND_URL`.
- Smoke-test demo loading, upload audit, PDF export, and AI agent provider behavior in production.

### Optional Engineering Polish

- Add route-level code splitting to reduce Vite bundle warning.
- Add CI to run backend and frontend tests automatically.
- Add browser-level end-to-end tests for the complete demo flow.

## Final Assessment

DataTrust AI is ready for portfolio presentation after screenshots and deployment. The main product architecture is complete, the AI provider path is privacy-safe, and the deterministic audit engine remains the source of truth for all UI, export, PDF, AI report, and agent responses.
