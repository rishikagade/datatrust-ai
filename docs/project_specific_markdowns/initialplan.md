# DataTrust AI: Automated Data Quality Auditor — Initial Project Plan

> **Purpose of this document:** This is a complete project context brief for Codex. It covers the full product vision, architecture, feature set, build phases, and design decisions agreed upon during planning. Do not begin coding from this document alone — await a separate implementation prompt. Use this as ground truth for understanding what the project is, why decisions were made, and how the pieces fit together.

---

## 1. Business Problem and Industry Relevance

Every company that runs dashboards, builds ML models, or reports KPIs is downstream of data quality. When that data is wrong, the consequences are concrete: an executive makes a pricing decision on duplicate transaction records; a churn model trained on records with 40% missing customer IDs produces unreliable predictions; a BI analyst spends three hours each Monday cleaning the same export before publishing it.

**Core business problems this tool addresses:**

**Unreliable dashboards.** A Power BI or Tableau dashboard is only as trustworthy as its source data. Missing values silently become zeroes; duplicates inflate revenue metrics; inconsistent category names ("US", "U.S.", "United States") break aggregations.

**Duplicate customers.** CRM exports routinely contain the same person under three records. This distorts customer counts, lifetime value calculations, and campaign targeting.

**Missing value contamination.** A column that is 35% null often signals a broken upstream pipeline, a form field that was never required, or a migration that dropped data.

**Inconsistent formats.** Date columns stored as "01/12/2024", "2024-01-12", and "Jan 12, 2024" in the same file break every time-series analysis. These are trivially detectable but rarely caught before they cause damage.

**Bad KPI reporting.** Finance and operations teams often discover mid-QBR that their numbers were built on data nobody profiled.

**Poor ML model inputs.** Most ML failures are data failures. A model trained on a column with 60% nulls imputed as zero will not generalize.

**Data governance and auditability.** Regulated industries (finance, healthcare, insurance) need documented evidence that data was inspected before use. A downloadable, timestamped audit report is a governance artifact, not just a convenience.

**Why this is different from asking ChatGPT to inspect a file.** Pasting a CSV into ChatGPT produces a one-time script with no scoring, no severity framework, no repeatable rules, and no business-readable report structure. DataTrust AI separates the two jobs cleanly: deterministic validation rules find and quantify the real issues; AI converts those structured findings into a business-readable narrative. The AI never sees raw sensitive rows — it reads a structured audit summary.

> **Core positioning: Rules detect the issues. AI explains the business impact.**

---

## 2. Target Users

**Data Analysts** — need to quickly profile a new dataset before building dashboards or queries. Want column-level statistics, null rates, type mismatches, and a severity breakdown fast.

**BI Analysts** — need to validate source data before publishing reports to leadership. Care especially about duplicate records, inconsistent categories, and missing values in key metrics columns. Need something they can show a manager as evidence the data was checked.

**Data Governance Teams** — need a repeatable, documented audit process. Want severity scores, rule-level traceability, and a downloadable report that can be attached to a data catalog or governance ticket.

**Business Analysts** — may not write code but need to understand what is wrong with a dataset received from a vendor or another team. Need plain-English explanations of issues, business impact framing, and clear recommended actions — not Python stack traces.

**Operations Analysts** — deal with high-volume transactional data (orders, claims, tickets) where duplicate detection and date format consistency are critical.

**Non-technical stakeholders** — receive the AI-generated audit report from their analyst. It needs to be written in language they understand, with clear risk ratings and business consequence framing.

---

## 3. Functional Requirements

### Core upload and detection
- CSV file upload (drag-and-drop and file picker)
- Automatic schema detection (infer column names, data types, cardinality)
- Column profiling (row count, null count, unique count, min/max/mean for numerics, most frequent values for categoricals)
- Missing value detection with column-level null percentage
- Duplicate row detection (exact row duplicates)
- Duplicate key detection (configurable primary key column)
- Invalid data type detection (e.g. text in a numeric column)
- Inconsistent category detection (near-duplicate labels, case variants, whitespace variants)
- Date format validation (multi-format detection, mixed format flagging)
- Outlier detection (IQR-based for numerics)
- Uniqueness checks on designated ID columns
- Numeric range checks (e.g. age > 150, negative revenue)
- Text formatting checks (leading/trailing whitespace, mixed case in names)
- Business rule validation (configurable: e.g. end_date must be after start_date)

### Scoring and reporting
- Composite data quality score (0–100)
- Issue severity classification: Low, Medium, High, Critical
- Dashboard with KPIs and charts
- AI-generated executive audit summary
- AI-generated business impact explanation per issue category
- Recommended cleaning actions per issue
- Downloadable audit report (PDF or structured HTML)
- Demo mode with preloaded sample datasets

### Standout features for 2026
- Column-level risk ranking — analyst knows which columns to fix first
- Privacy-safe AI integration — AI receives only aggregated statistics, never raw data rows
- Configurable business rules panel — user adds custom validation rules without code
- Audit confidence indicator — flag when dataset is too small for reliable outlier detection
- Freshness/timeliness check — detect if date columns suggest the data is stale
- Column correlation heatmap — detect redundant or suspicious column relationships
- Suggested column type corrections with one-click preview
- "Fix Preview" mode showing what the cleaned dataset would look like after applying recommendations
- **Contextual AI Audit Agent** — an interactive conversational Q&A layer allowing users to ask plain-English questions about their specific audit results (see Section 16)

---

## 4. Non-Functional Requirements

**Usability.** A business analyst with no data engineering background should be able to upload a file, read the dashboard, and understand the AI report without documentation. Technical jargon should be parenthetical, not the headline.

**Performance.** For MVP, target files up to 50MB / 500k rows processed in under 10 seconds. Profiling should be non-blocking with a progress indicator. Large file warnings appear before processing begins.

**Security.** Files should not be permanently stored on any server unless the user explicitly saves a session. Processing should be ephemeral. If a server is used, files should be deleted immediately after results are returned. Use HTTPS throughout.

**Privacy.** The most important non-functional requirement. The AI layer must never receive raw data rows. The audit engine runs deterministically on the file, produces structured statistics and issue counts, and only that structured summary (column names, issue types, counts, percentages) is sent to the AI API. This must be explicitly documented in the UI and in the README.

**Explainability.** Every issue flagged must trace back to a named rule. The user should always be able to see: "this was flagged because: duplicate key detected in column `customer_id` — 1,247 rows affected." No black-box outputs.

**Auditability.** The downloadable report must include a timestamp, dataset name, row/column counts, the complete list of rules applied, and the results of each rule. It is a governance artifact.

**Scalability.** MVP can run in-browser with Papa Parse + JS logic. Version 2 moves heavy profiling to a Python/FastAPI backend. Version 3 supports database connections and scheduled audits.

**Accessibility.** Color is never the sole indicator of severity — icons and labels accompany all color-coded elements. Charts must have accessible alt-text equivalents. Keyboard navigation should be functional.

**Error handling.** Malformed CSVs, empty files, files with only headers, non-CSV uploads — all must produce friendly, specific error messages. Never show a stack trace to the user.

**Maintainability.** The rules engine should be a separate, self-contained module (a JSON config or a rules registry) so new rules can be added without touching the UI code.

---

## 5. AI Integration Strategy

### Where AI belongs — and where it does not

AI should not detect data quality problems. Deterministic code does that better, faster, and more reliably. A null is a null. A duplicate is a duplicate. A date that does not match ISO 8601 is not debatable. If the AI is detecting issues, the tool is a demo, not a product.

AI's role is translation. It takes the structured audit output — a JSON object of counts, percentages, severity levels, affected columns, and rule results — and converts it into a narrative a business stakeholder can read and act on.

### What AI receives (example prompt input)

```text
Dataset: customer_export_q2.csv
Rows: 12,483 | Columns: 14
Quality Score: 61/100

Issues detected:
- Missing values: 'email' column 34% null (HIGH)
- Duplicates: 847 exact duplicate rows (HIGH)
- Duplicate key: 'customer_id' has 1,247 non-unique values (CRITICAL)
- Inconsistent categories: 'country' has 11 variants of 'United States' (MEDIUM)
- Invalid type: 'annual_revenue' column contains 203 non-numeric values (HIGH)
- Outliers: 'age' column has 14 values above 120 (MEDIUM)
```

### What AI produces

- **Executive Summary** — two to three sentence business-readable overview of the dataset's overall quality, the most serious risk, and the primary recommended action
- **Risk Interpretation** — for each High and Critical issue, a plain-English paragraph explaining what could go wrong if not fixed
- **Cleaning Recommendations** — a prioritized, actionable list written for a data analyst, specific to the issue and column flagged
- **Dashboard Impact Statement** — if this data was used in a BI tool, what would break or mislead
- **Stakeholder Framing** — a short paragraph that a data governance lead could paste into a ticket or email

### Prompt design principles

- Send only the structured audit JSON, never raw rows
- System prompt instructs the model to write for a senior non-technical business stakeholder
- Instruct the model to be specific — name the columns and percentages
- Avoid generic boilerplate like "it is important to ensure data quality"
- Cap the response length per section
- Validate AI output client-side before displaying — if the model returns malformed text, show a fallback message

---

## 6. Data Quality Rules Engine

The rules engine is a modular registry. Each rule has an ID, display name, category, severity logic function, and suggested fix.

### Rule definitions

**Completeness — Missing Value Check**
- What it checks: null, empty string, or whitespace-only values per column
- Why it matters: nulls in key metrics columns silently distort aggregations
- Severity: Low < 5% | Medium 5–15% | High 15–35% | Critical > 35% in required columns
- Suggested fix: impute, drop, or flag for upstream investigation

**Uniqueness — Duplicate Row Check**
- What it checks: exact row duplicates by hashing all column values
- Why it matters: duplicates inflate every count-based metric
- Severity: Low < 0.5% | Medium 0.5–2% | High 2–5% | Critical > 5%
- Suggested fix: deduplicate keeping first or last occurrence; investigate source pipeline

**Uniqueness — Duplicate Key Check**
- What it checks: designated ID columns for non-unique values
- Why it matters: non-unique keys break all table joins and produce fan-out in aggregations
- Severity: any non-uniqueness in a primary key column = Critical
- Suggested fix: investigate source system; determine if records are truly duplicate or incorrectly merged

**Validity — Data Type Check**
- What it checks: columns where more than 1% of non-null values do not parse to the inferred type
- Why it matters: mixed-type columns cannot be used in calculations or filters reliably
- Severity: Medium < 5% invalid | High 5–20% | Critical > 20%
- Suggested fix: coerce valid values, isolate and review invalid rows

**Consistency — Inconsistent Category Check**
- What it checks: fuzzy matching and case normalization for low-cardinality string columns
- Why it matters: BI filters and GROUP BY aggregations split variants as separate categories
- Severity: Medium if variants exist but are few | High if > 5 variants of a dominant category
- Suggested fix: standardize to canonical form using a lookup map

**Conformity — Date Format Validation**
- What it checks: whether all date values in a column parse to a consistent format
- Why it matters: date-based filtering, sorting, and time-series logic fail silently on mixed formats
- Severity: High if mixed formats are present in any column
- Suggested fix: standardize to ISO 8601 (YYYY-MM-DD)

**Accuracy Proxy — Outlier Detection**
- What it checks: values below Q1 − 3×IQR or above Q3 + 3×IQR for numeric columns
- Why it matters: extreme outliers distort means, models, and trend lines
- Severity: Low < 0.5% flagged | Medium 0.5–2% | High > 2%
- Suggested fix: review flagged values for data entry errors; apply domain-appropriate caps or exclusions

**Accuracy Proxy — Numeric Range Check**
- What it checks: domain-specific impossible values (age > 150, revenue < 0, percentage > 100)
- Why it matters: impossible values indicate upstream data entry errors or unit mismatches
- Severity: High to Critical depending on column designation
- Suggested fix: correct at source or exclude from analysis; configurable per column

**Conformity — Text Formatting Check**
- What it checks: leading/trailing whitespace, mixed case in name columns, all-caps entries
- Why it matters: whitespace breaks exact-match joins; case inconsistency causes case-sensitive tools to treat the same value as distinct
- Severity: Low
- Suggested fix: strip whitespace; apply title case normalization for name-type columns

**Timeliness — Freshness Check**
- What it checks: whether the most recent date value in a creation/transaction date column is within a configurable threshold
- Why it matters: analysts may unknowingly use an old export as if it were current
- Severity: Low slightly stale | Medium > 60 days | High > 180 days
- Suggested fix: confirm data pull date and recency requirements with data owner

**Integrity — Referential Check**
- What it checks: logical relationships between columns (e.g. end_date > start_date)
- Why it matters: inverted date ranges, negative durations, and broken hierarchies produce nonsensical calculations
- Severity: High if violated
- Suggested fix: identify and correct the rows where the relationship is inverted; validate at the source system

---

## 7. Scoring Methodology

### Component weights

| Component | Weight | How Calculated |
|---|---|---|
| Missing value rate | 25% | Weighted avg null % across columns, scaled 0–100 |
| Duplicate row rate | 20% | Duplicate % scaled to penalty |
| Invalid type rate | 20% | Weighted by column importance |
| Outlier rate | 10% | Numeric columns only |
| Critical column failures | 15% | Binary: any Critical severity issue = large deduction |
| Business rule violations | 10% | Count of violated custom rules |

### Severity multipliers

- Critical issues: 3× multiplier on component penalty
- High issues: 2× multiplier
- Medium issues: 1× multiplier
- Low issues: 0.5× multiplier

A single Critical-severity failure (e.g. primary key non-uniqueness) can drop the score by 15–20 points alone.

### Score interpretation

| Range | Tier | Meaning |
|---|---|---|
| 90–100 | Excellent | Production-ready with only minor cosmetic issues |
| 75–89 | Good | A few issues; acceptable for exploratory analysis |
| 60–74 | Needs Review | Should not be used in executive reporting or model training without cleaning |
| Below 60 | High Risk | Major structural problems; escalate to data owner before use |

The score should be displayed with its category label, a colored indicator, and a one-sentence interpretation. It is not the sole output — the column-level breakdown drives remediation decisions.

---

## 8. Architecture

### Full-stack version (recommended for portfolio)

**Frontend:** React with Tailwind CSS. Recharts for data visualizations. React Router for multi-page navigation. React Dropzone for file upload. jsPDF or server-side template for report download.

**Backend:** FastAPI (Python). Receives uploaded CSV. Runs all profiling and validation using pandas and scipy. Returns a structured audit JSON. Calls the OpenAI API using the audit JSON as the prompt payload.

**Data processing layer:** pandas for profiling, scipy for outlier detection, rapidfuzz for category consistency checking.

**Validation engine:** A Python module (`rules_engine.py`) that imports the rules registry and runs each rule against the profiling output. Returns a list of `RuleResult` objects with rule ID, severity, affected column, count, percentage, and suggested fix.

**AI summary layer:** A separate Python module (`ai_summary.py`) that constructs the audit prompt from the RuleResult list, calls the OpenAI Chat Completions API, parses the response, and returns structured sections: `executive_summary`, `risk_interpretation`, `cleaning_recommendations`, `dashboard_impact`.

**AI audit agent layer:** A conversational Q&A module that accepts user messages and conversation history, injects the session audit context as a system prompt, and streams responses back to the frontend chat panel. See Section 16 for full detail.

**Report generation:** A FastAPI endpoint that accepts the audit JSON and generates a PDF using reportlab or WeasyPrint, returned as a file download.

**Storage:** No persistent storage in MVP. Session data lives in browser state. SQLite added in Version 3 for saved audit history.

### Simpler single-stack version (faster to build)

Build the entire application as a React app with in-browser processing using Papa Parse for CSV parsing and JavaScript for all validation rules. Call the OpenAI API via a Vercel Edge Function proxy to avoid exposing the API key. No backend required. Deploy on Vercel or Netlify in one step. Tradeoff: complex outlier detection and fuzzy matching are harder in pure JavaScript, so some rules will be simplified.

---

## 9. Pages and UI Layout

(full content continues unchanged...)

---

## 1. Business Problem and Industry Relevance

Every company that runs dashboards, builds ML models, or reports KPIs is downstream of data quality. When that data is wrong, the consequences are concrete: an executive makes a pricing decision on duplicate transaction records; a churn model trained on records with 40% missing customer IDs produces unreliable predictions; a BI analyst spends three hours each Monday cleaning the same export before publishing it.

**Core business problems this tool addresses:**

**Unreliable dashboards.** A Power BI or Tableau dashboard is only as trustworthy as its source data. Missing values silently become zeroes; duplicates inflate revenue metrics; inconsistent category names ("US", "U.S.", "United States") break aggregations.

**Duplicate customers.** CRM exports routinely contain the same person under three records. This distorts customer counts, lifetime value calculations, and campaign targeting.

**Missing value contamination.** A column that is 35% null often signals a broken upstream pipeline, a form field that was never required, or a migration that dropped data.

**Inconsistent formats.** Date columns stored as "01/12/2024", "2024-01-12", and "Jan 12, 2024" in the same file break every time-series analysis. These are trivially detectable but rarely caught before they cause damage.

**Bad KPI reporting.** Finance and operations teams often discover mid-QBR that their numbers were built on data nobody profiled.

**Poor ML model inputs.** Most ML failures are data failures. A model trained on a column with 60% nulls imputed as zero will not generalize.

**Data governance and auditability.** Regulated industries (finance, healthcare, insurance) need documented evidence that data was inspected before use. A downloadable, timestamped audit report is a governance artifact, not just a convenience.

**Why this is different from asking ChatGPT to inspect a file.** Pasting a CSV into ChatGPT produces a one-time script with no scoring, no severity framework, no repeatable rules, and no business-readable report structure. DataTrust AI separates the two jobs cleanly: deterministic validation rules find and quantify the real issues; AI converts those structured findings into a business-readable narrative. The AI never sees raw sensitive rows — it reads a structured audit summary.

> **Core positioning: Rules detect the issues. AI explains the business impact.**

---

*(truncated — full content copied from original `initialplan.md`)*
