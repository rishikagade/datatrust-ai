# DataTrust AI — Implementation Plan

This implementation plan is derived from `docs/project_specific_markdowns/initialplan.md` and is intended as a developer-facing roadmap. It specifies architecture decisions, data flows, rule implementations, scoring calculations, API contracts, frontend structure, sample datasets, risks, and open questions required to begin coding in discrete phases.

## 1. Project understanding summary

DataTrust AI is a full‑stack automated data quality auditor for CSV datasets. It profiles data, applies a deterministic rules engine to surface issues (missing values, duplicates, invalid types, outliers, referential breaks, etc.), computes a weighted 0–100 quality score, and produces privacy‑safe AI narratives and an interactive audit agent that explains business impact and remediation for non-technical stakeholders.

The product separates detection and explanation: deterministic code (the rules engine) identifies and quantifies problems; the AI layer only receives an aggregated audit JSON (no raw rows) and translates those findings into business-readable text. This separation preserves privacy, reproducibility, auditability, and testability — distinguishing DataTrust AI from ad-hoc LLM-based inspection tools.

## 2. Key architectural decisions to preserve

- Privacy boundary: AI must never receive raw CSV rows. Only aggregated audit JSON fields (column names, counts, percentages, severities, and rule summaries) may be sent. Violating this breaks privacy guarantees and regulatory compliance.
- Clear separation of concerns: rules engine (detection) is deterministic and isolated; AI layer (narrative) consumes only audit JSON. Blending them would make outputs non-repeatable and untestable.
- Rules engine must be self-contained and unit-testable: independent module (registry + implementations) with no UI or network side-effects.
- Canonical `AuditJSON` is the single source of truth used by UI, AI prompts, PDF exports, and the agent. All layers must consume this object.
- The AI Audit Agent and static report generator are distinct modules sharing the same audit context but using different prompt patterns and session behaviors.
- Severity multipliers must be implemented exactly as specified: Critical ×3, High ×2, Medium ×1, Low ×0.5, and used in score calculations.
- No automatic data correction: the tool flags and recommends; it never auto-modifies user data without explicit human consent.

## 3. Folder and module structure

Root
- README.md — overview, privacy note, run instructions
- docs/project_specific_markdowns/initialplan.md — product source of truth (do not modify)
- .agent.md — project agent definition (created)
- docs/IMPLEMENTATION_PLAN.md — this document
- .env.example — env var template

Frontend (`/frontend`)
- package.json — frontend dependencies
- src/index.tsx — app bootstrap & router
- src/App.tsx — top-level routes and layout
- src/pages/* — pages (LandingPage, UploadPage, AuditDashboard, ColumnProfile, IssueList, AIReportPage, DownloadExport)
- src/components/* — reusable UI components (FileDropzone, KPIHeader, ChatPanel, charts, tables)
- src/state/store.ts — global state (Zustand or Context)
- src/api/apiClient.ts — typed HTTP client
- public/demo CSVs — small sample CSVs (optional)

Backend (`/backend`)
- pyproject.toml / requirements.txt — python dependencies
- app/main.py — FastAPI app and router mounts
- app/config.py — env and settings
- app/routes/* — audit.py, agent.py, report.py, demo.py, health.py
- app/services/* — profiler.py, rules_runner.py, scoring.py, ai_summary.py, ai_agent.py, pdf_generator.py
- app/rules/* — registry.py, implementations.py, types.py
- app/models/schemas.py — pydantic request/response models
- demo_datasets/* — server-side CSVs and metadata

Rules engine (under `/backend/app/rules`)
- registry.py — declarative rule definitions and thresholds
- implementations.py — pure functions for each rule
- types.py — `RuleResult` dataclass and serialization helpers

AI layers
- services/ai_summary.py — static report generator
- services/ai_agent.py — conversational agent handler

Configuration
- .env.example — GROQ_API_KEY, MAX_FILE_SIZE_MB, MODEL defaults
- docker-compose.yml — optional local dev stack

Tests
- tests/test_rules.py, tests/test_scoring.py, tests/test_api_endpoints.py

Sample datasets
- sample_datasets/customer_export.csv + metadata
- sample_datasets/sales_q3.csv + metadata
- sample_datasets/hr_employees.csv + metadata

## 4. Data flow (textual diagram and audit JSON schema)

User uploads CSV → Frontend sends `POST /audit` → Backend profiler builds `ProfileStats` → Rules runner returns `RuleResult[]` → Scoring computes `QualityScore` → Construct canonical `AuditJSON` → Optionally call `ai_summary` to attach `ai_report` → Return `AuditResponse` to frontend → Frontend renders dashboard and enables AI agent using same `AuditJSON`.

Audit JSON schema (key fields)
- audit_id: string (UUID)
- dataset: { filename, row_count:int, column_count:int, uploaded_at:ISO8601 }
- profile_stats: { column_name: ColumnProfile }
  - ColumnProfile: { name, inferred_type, null_count, null_pct, unique_count, top_values:[{value,count,pct}], numeric_summary:{min,q1,median,mean,q3,max,std}, date_summary, sample_values (UI-only, strip before AI) }
- rule_results: [RuleResult]
- scoring: { overall_score, tier, component_scores, component_weights, calculation_detail }
- ai_report: { executive_summary, risk_interpretation, cleaning_recommendations, dashboard_impact, generated_at, model }
- metadata: { rules_applied_count, issues_count_by_severity, warnings }

AI Audit Agent message assembly
- System prompt: instructions + sanitized `audit_json` summary (no sample_values)
- User message: user's free-text question
- Conversation history: last K turns appended

## 5. Rules engine implementation plan

`RuleResult` structure (canonical)
- rule_id, rule_name, category, affected_columns:[string], affected_count:int, affected_pct:float, severity:(Low|Medium|High|Critical), description, suggested_fix, metadata, timestamp

Implementation entries (summary for each rule):
- Completeness — Missing Value Check: input: ColumnProfile nulls; logic: compute null_pct; severity thresholds: Low<5, Medium5–15, High15–35, Critical>35; deps: pandas; test: column with 34% nulls → High.
- Duplicate Row Check: input: full DataFrame; logic: detect exact duplicates; thresholds: Low<0.5, Medium0.5–2, High2–5, Critical>5; deps: pandas; test: 2.3% duplicates → High.
- Duplicate Key Check: input: primary key column; logic: non-unique count >0 → Critical; deps: pandas; test: non-unique customer_id → Critical.
- Data Type Check: input: column inferred type + parsing; logic: invalid_count/non_null_count; thresholds: Medium<5, High5–20, Critical>20; deps: pandas, dateutil; test: 4.06% invalid → Medium.
- Inconsistent Category Check: input: low-cardinality string columns; logic: fuzzy clustering via rapidfuzz; severity: Medium if variants exist, High if >5 variants; deps: rapidfuzz; test: 11 variants of 'United States' → High.
- Date Format Validation: input: date column; logic: detect multiple parsed formats; severity: High if mixed; deps: dateutil; test: three date formats present → High.
- Outlier Detection: input: numeric_summary (Q1,Q3,IQR); logic: lower/upper fences Q1−3IQR, Q3+3IQR; thresholds: Low<0.5, Medium0.5–2, High>2; deps: pandas/scipy; test: 14 outliers of 5000 → Low.
- Numeric Range Check: input: numeric column + domain rules; logic: violations count; severity: High by default; deps: pandas; test: discount_pct >100 in 12 rows → High.
- Text Formatting Check: input: string columns; logic: detect leading/trailing whitespace, all-caps; severity: Low; deps: pandas; test: 'Electronics ' variant → Low.
- Freshness Check: input: date columns; logic: compute days_since_last and thresholds (Low/Medium/High); deps: pandas/datetime; test: last date 200 days ago → High.
- Referential Check: input: column pairs; logic: count rows violating relationship (end_date <= start_date); severity: High; deps: pandas; test: ship_date before order_date in 47 rows → High.

---

## 6. Scoring engine implementation plan

Method:
- Components with weights per initial plan: missing_value 25%, duplicate_rows 20%, invalid_type 20%, outliers 10%, critical_failures 15%, business_rule_violations 10%.
- For each component, compute `p_i` (penalty 0–100) using RuleResult. Within p_i, apply severity multiplier (Critical×3, High×2, Medium×1, Low×0.5).
- Overall score = max(0, 100 − Σ(w_i * p_i)). Store calculation details in `scoring.calculation_detail`.

Edge cases
- No rules fire → score 100, but set `metadata.warnings` if suspicious.
- All columns null → missing component p_missing = 100; avoid division-by-zero; final score likely very low.
- Single-row files → set low statistical confidence; reduce outlier penalties and show warning.

## 7. AI integration implementation plan

Static report generator (`ai_summary.py`)
- Input: `AuditJSON`.
- Prompt: system prompt instructing business-audience output + a sanitized top-N issue summary (no sample_values).
- Model call: low temperature (0.2), appropriate model (configurable), limited tokens.
- Parse response into named sections and validate references to columns/percentages against `AuditJSON`.
- On malformed output or API failure, return `audit_json` with `metadata.warnings` and graceful UI fallback.

AI Audit Agent (`ai_agent.py`)
- Session startup: backend composes system prompt with sanitized `AuditJSON` snapshot and instructions to only answer from context.
- Each message: accept `user_message` + `conversation_history` (last K turns), assemble prompt, call OpenAI, return assistant text.
- Transport: REST `POST /agent/message` for MVP; recommend WebSocket streaming in later versions.
- Scope bounding: system prompt forbids inventing issues; if question outside audit scope, agent replies with a limitation message.
- Quick-action chips: generate from top Critical/High issues at `POST /audit`.

## 8. Frontend implementation plan

Pages and components
- LandingPage: Hero, CTA.
- UploadPage: FileDropzone, demo buttons, RunAuditButton.
- AuditDashboard: KPIHeader, SeverityDonut (Recharts Pie), MissingBarChart (BarChart), ColumnRiskTable (react-table), TopIssuesPanel.
- ColumnProfile: ColumnProfileCard, NumericStatsCard, RuleResultsList.
- IssueList: FilterToolbar, IssueRow.
- AIReportPage: ReportSections and DownloadButtons.
- ChatPanel: collapsible side-panel, QuickActionChips.

State management
- Global store holds `AuditJSON` and `session` (Zustand or Context). Conversation history stored in browser sessionStorage per `audit_id`.

Charts mapping (Recharts)
- Severity distribution: PieChart
- Missing value by column: BarChart (horizontal)
- Outlier distribution: custom boxplot/histogram (or simplified histogram)
- Completeness heatmap: custom grid with color scale

Accessibility and privacy notes included in UI.

## 9. Backend API implementation plan

Endpoints (MVP)
- `POST /audit` — multipart CSV upload, returns `AuditResponse` (AuditJSON). Errors: 400/413/422/500.
- `POST /report/pdf` — accept AuditJSON or audit_id, returns PDF.
- `POST /agent/message` — accept audit_id + user_message + conversation_history, returns assistant reply.
- `GET /demo/{dataset_name}` — returns precomputed audit or runs audit on stored CSV.
- `GET /health` — status check.

Processing considerations: ephemeral file handling, encoding detection (`charset-normalizer`), chunked reads for large files, and strict privacy sanitization before any AI call.

## 10. Sample dataset plan

Dataset 1 — Customer Master (~5,000 rows)
- Generation: Faker script with controlled errors.
- Columns: customer_id, first_name, last_name, email, country, age, annual_revenue, phone_number.
- Seeded issues: 34% null emails, 847 duplicate rows, 1,247 non-unique customer_id values, 11 country variants, 14 ages >130, 203 annual_revenue non-numeric entries.
- Expected audit: Score ~55–65; Critical duplicate_key; High missing emails and invalid revenue; Medium category variants.

Dataset 2 — Sales Transactions (~15,000 rows)
- Columns: transaction_id, order_date (mixed formats), ship_date, order_total, product_category, discount_pct.
- Seeded issues: mixed date formats, 89 negative order_total, 2.3% duplicates, product_category whitespace/case variants, 12 discount_pct >100, 47 ship_date < order_date.
- Expected audit: Score ~70–78; High date/temporal and numeric range issues.

Dataset 3 — HR Employees (~1,200 rows)
- Columns: employee_id, hire_date, termination_date, status, salary, department, job_title.
- Seeded issues: salary outliers, department code/name variants, termination_date mismatches, hire_date after termination_date, 3 duplicate employee_id.
- Expected audit: Score ~60–72; High integrity violations; Medium outliers.

## 11. Build sequence and task breakdown (v1.1)

The build is broken into small, demonstrable tasks. Each task produces one verifiable deliverable and has an acceptance criterion.

Note on dependencies: tasks list direct dependencies; do not start a task until its dependencies are complete.

MVP (deliverable): upload → audit → dashboard → static AI report

MVP Task 1 — Scaffolding (Low)
- Description: Initialize frontend and backend repositories with base tooling (React + Tailwind, FastAPI), add `docs/IMPLEMENTATION_PLAN.md`, `.agent.md`, and `.env.example`.
- Dependencies: none
- Acceptance: `npm start` launches frontend and `uvicorn app.main:app` starts backend returning 200 on `/health`.

MVP Task 2 — Upload UI + `POST /audit` (Low)
- Description: FileDropzone UI and backend `POST /audit` that accepts CSV and returns stubbed AuditJSON (row_count, column_count).
- Dependencies: Scaffolding
- Acceptance: Uploading `sample_datasets/customer_export.csv` displays row_count and column_count in the frontend UI and backend returns `{"audit_id":..., "dataset": {"row_count": 5000, "column_count": 8}}`.

...(document continues unchanged)
