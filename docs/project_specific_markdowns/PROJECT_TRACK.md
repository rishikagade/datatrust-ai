# Project Track — DataTrust AI

This file records implementation progress for the DataTrust AI project.

Version: v1.0  
Record updated: 2026-05-29

## Current Status

DataTrust AI is feature-complete for the portfolio MVP. The application supports CSV/TSV upload, live demo datasets, deterministic profiling and rules, weighted scoring, dashboard views, issue exploration, PDF/CSV/JSON exports, AI-written audit narratives, and a conversational AI Audit Agent.

The current finishing phase is production and portfolio polish: documentation truthfulness, deployment readiness, final UI polish, screenshots, and repository presentation.

## Completed

1. Created the project agent definition and implementation plan.
2. Built the FastAPI backend with `/health`, `/audit`, `/demo/{dataset_name}`, `/agent/message`, and `/report/pdf`.
3. Implemented the profiler with per-column null counts, null percentages, unique counts, inferred types, top-value counts, and numeric summaries.
4. Implemented the deterministic rules engine with 11 rule categories covering completeness, uniqueness, validity, outliers, category consistency, dates, numeric ranges, text formatting, freshness, and chronological integrity.
5. Implemented the weighted 0-100 scoring engine with weighted deductions and severity multipliers.
6. Generated reproducible sample datasets:
   - `customer_master.csv` — 5,000 rows
   - `sales_transactions.csv` — 15,000 rows
   - `hr_employees.csv` — 1,200 rows
7. Built the React/TypeScript frontend with router-based pages for landing, upload, dashboard, column profile, issue list, AI report, and exports.
8. Added Zustand as the global audit-state source for post-upload pages and persisted chat history by audit ID.
9. Added charts, ranking tables, score breakdowns, severity views, AI summary cards, and download/export flows.
10. Added privacy-safe AI summary generation and AI agent flows using sanitized audit context only.
11. Replaced OpenAI with Groq for AI calls, using `GROQ_API_KEY` and `GROQ_MODEL`.
12. Added a rule-based local fallback for the AI agent that still references actual columns, counts, percentages, severities, and score deductions.
13. Added backend pytest coverage and frontend Vitest coverage.
14. Added `.env.example`, `backend/.env.example`, backend Dockerfile, and `docker-compose.yml`.
15. Added backend dotenv loading for local development.
16. Added AI agent provider indication and chat clearing to avoid stale local-fallback conversations.

## Verified Locally

- Backend tests: `29 passed`
- Frontend tests: `7 passed`
- Focused AI Agent page test: `2 passed`
- Frontend production build: passes with a Vite chunk-size warning
- Live backend check: `POST /agent/message` returns `provider: groq` when `backend/.env` contains a valid Groq key and `groq` is installed
- Sanitization check: raw-value keys such as `sample_values`, `raw_values`, `row_data`, and `top_values` are excluded from AI context

## Active Local Dev Servers

Current intended local setup:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

Avoid using stale Vite or backend ports from previous sessions. If provider output looks wrong, verify the browser is talking to port `8000` and clear persisted chat history.

## Remaining Phases

### Phase 1 — Documentation Truth Pass

Status: in progress

Update all project-facing docs so they match the current implementation: Groq instead of OpenAI, generated large sample datasets instead of small fixtures, tests present, deployment config present, and frontend backend URL driven by environment config.

### Phase 2 — Portfolio Presentation

Status: pending

Add final screenshots or GIFs for:

- Dashboard
- Column profile page
- AI report page
- AI agent chat panel

Then update README screenshot links to point to committed assets.

### Phase 3 — Deployment

Status: pending

Deploy the backend and frontend, set production environment variables, replace the README live-demo placeholder, and smoke-test upload, demo audit, PDF export, and AI agent behavior in production.

### Phase 4 — Final QA

Status: pending

Run a final end-to-end pass on a clean clone:

1. Generate sample datasets.
2. Install backend dependencies.
3. Install frontend dependencies.
4. Run backend tests.
5. Run frontend tests and build.
6. Start the stack with Docker Compose.
7. Verify the demo datasets and AI agent provider path.

## Current Risks

- A real Groq key must live only in `.env` or deployment secrets, never in `.env.example`.
- Browser local storage can retain old chat history by audit ID; use **Clear chat** when switching provider configuration.
- The frontend build has a chunk-size warning. This is not blocking, but route-level code splitting would be a good future optimization.
- The live demo URL is still a placeholder until deployment is complete.
