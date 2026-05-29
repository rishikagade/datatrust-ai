import html
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from .services import profiler

class AssistantQuery(BaseModel):
    question: str
    model: str = "llama-3.3-70b-versatile"


class AgentMessageRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []
    audit_context: dict
    model: str = "llama-3.3-70b-versatile"


class AgentMessageResponse(BaseModel):
    reply: str
    audit_id: str | None = None
    provider: str

ROOT_DIR = Path(__file__).resolve().parents[2]
SAMPLE_DATASETS_DIR = ROOT_DIR / "sample_datasets"
DEMO_DATASETS = {
    "customer_master": {
        "file": "customer_master.csv",
        "label": "Customer master",
        "description": "Customer records with duplicate keys, missing emails, and invalid revenue fields.",
    },
    "sales_transactions": {
        "file": "sales_transactions.csv",
        "label": "Sales transactions",
        "description": "Sales orders with mixed dates, duplicate rows, negative totals, and discounts.",
    },
    "hr_employees": {
        "file": "hr_employees.csv",
        "label": "HR employees",
        "description": "Employee records with salary outliers, duplicate IDs, and date inconsistencies.",
    },
}

app = FastAPI(title="DataTrust AI Backend")

default_origins = ",".join(
    [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
    ]
)
origins = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", default_origins).split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIT_CACHE: dict[str, dict] = {}


def _detect_delimiter(text: str) -> str:
    sample = text.splitlines()
    if not sample:
        raise ValueError("Empty file")
    first = sample[0]
    return ',' if first.count(',') >= first.count('\t') else '\t'


def _build_audit_response(
    file_name: str,
    text: str,
    model: str = "llama-3.3-70b-versatile",
    ai_requested: bool = True,
    demo_dataset: str | None = None,
) -> dict:
    delimiter = _detect_delimiter(text)
    try:
        prof = profiler.profile_from_text(text, delimiter=delimiter)
    except Exception as e:
        raise ValueError(f"Failed to profile CSV: {e}")
    if prof['dataset']['row_count'] == 0 or prof['dataset']['column_count'] == 0:
        raise ValueError("Empty file or no data rows found")

    try:
        from .services import rules_runner
        rule_results = rules_runner.run_rules_from_text(text, delimiter=delimiter)
    except Exception:
        rule_results = []

    try:
        from .services import scoring
        scoring_obj = scoring.compute_overall_score(rule_results, prof['profile_stats'])
    except Exception:
        scoring_obj = {}

    audit_id = str(uuid4())
    response = {
        "audit_id": audit_id,
        "dataset": {
            "filename": file_name,
            "row_count": prof['dataset']['row_count'],
            "column_count": prof['dataset']['column_count'],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
        "profile_stats": prof['profile_stats'],
        "rule_results": rule_results,
        "scoring": scoring_obj,
        "metadata": {
            "notes": "profile computed (basic)",
            "ai_requested": ai_requested,
            "demo_dataset": demo_dataset,
            "rules_applied_count": 11,
        },
    }

    try:
        from .services import ai_summary
        response["ai_report"] = ai_summary.generate_ai_report(response, model=model)
    except Exception as exc:
        response["ai_report"] = {
            "executive_summary": "AI report generation unavailable.",
            "risk_interpretation": str(exc),
            "cleaning_recommendations": "",
            "dashboard_impact": "",
            "generated_at": response["dataset"]["uploaded_at"],
            "model": model,
            "warning": "AI summary failed",
        }

    AUDIT_CACHE[audit_id] = response
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "DataTrust AI Backend (scaffold). Use /health for status."}


@app.post("/audit")
async def audit_endpoint(
    file: UploadFile = File(...),
    ai: bool = False,
    model: str = "llama-3.3-70b-versatile",
):
    """Accept a CSV/TSV upload and return a privacy-safe aggregate audit JSON."""
    if not file.filename.lower().endswith(('.csv', '.tsv')):
        raise HTTPException(status_code=400, detail="Only CSV/TSV uploads are supported in this stub.")

    contents = await file.read()
    # Try to decode with utf-8 fallback to latin-1
    try:
        text = contents.decode('utf-8')
    except Exception:
        try:
            text = contents.decode('latin-1')
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode uploaded file")

    try:
        response = _build_audit_response(file.filename, text, model=model, ai_requested=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit failed: {exc}")
    return JSONResponse(status_code=200, content=response)


@app.post('/agent/message', response_model=AgentMessageResponse)
async def agent_message(payload: AgentMessageRequest):
    try:
        from .services import ai_agent
        response = ai_agent.generate_agent_response(
            payload.audit_context,
            payload.message,
            conversation_history=payload.conversation_history,
            model=payload.model,
        )
        return JSONResponse(status_code=200, content=response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Agent generation failed: {exc}')


@app.get('/audit/{audit_id}')
async def get_audit(audit_id: str):
    audit = AUDIT_CACHE.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail='Audit not found')
    return JSONResponse(status_code=200, content=audit)

@app.get('/demo')
async def list_demo_datasets():
    return JSONResponse(status_code=200, content=[
        {
            "name": key,
            "label": value["label"],
            "description": value["description"],
        }
        for key, value in DEMO_DATASETS.items()
    ])

@app.get('/demo/{dataset_name}')
async def get_demo_dataset(dataset_name: str, model: str = "llama-3.3-70b-versatile"):
    dataset_info = DEMO_DATASETS.get(dataset_name)
    if not dataset_info:
        raise HTTPException(status_code=404, detail='Demo dataset not found')

    sample_file = SAMPLE_DATASETS_DIR / dataset_info['file']
    if not sample_file.exists():
        raise HTTPException(status_code=404, detail='Demo dataset file missing')

    try:
        text = sample_file.read_text(encoding='utf-8')
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Unable to read demo file: {exc}')

    try:
        response = _build_audit_response(dataset_info['file'], text, model=model, ai_requested=True, demo_dataset=dataset_name)
        return JSONResponse(status_code=200, content=response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Demo audit failed: {exc}')

@app.post('/audit/{audit_id}/assistant')
async def audit_assistant(audit_id: str, query: AssistantQuery):
    audit = AUDIT_CACHE.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail='Audit not found')
    try:
        from .services import ai_agent
        response = ai_agent.generate_agent_response(audit, query.question, model=query.model)
        return JSONResponse(status_code=200, content=response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Assistant generation failed: {exc}')


def _severity_order(severity: str) -> int:
    return {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(severity, 4)


def _render_pdf_html(audit: dict) -> str:
    dataset = audit.get("dataset", {})
    scoring = audit.get("scoring", {})
    score = scoring.get("overall_score", "N/A")
    rules = sorted(audit.get("rule_results", []), key=lambda item: _severity_order(item.get("severity", "")))
    ai_report = audit.get("ai_report", {})
    timestamp = datetime.now(timezone.utc).isoformat()
    component_rows = ""
    for key, item in (scoring.get("component_scores") or {}).items():
        component_rows += (
            "<tr>"
            f"<td>{html.escape(key.replace('_', ' ').title())}</td>"
            f"<td>{item.get('weight', 0)}%</td>"
            f"<td>{item.get('weighted_deduction', 0)}</td>"
            f"<td>{item.get('component_health', 0)}</td>"
            "</tr>"
        )
    rule_rows = ""
    for rule in rules:
        rule_rows += (
            "<tr>"
            f"<td>{html.escape(str(rule.get('severity', '')))}</td>"
            f"<td>{html.escape(str(rule.get('rule_name', '')))}</td>"
            f"<td>{html.escape(', '.join(rule.get('affected_columns') or []))}</td>"
            f"<td>{rule.get('affected_count', '')}</td>"
            f"<td>{rule.get('affected_pct', '')}</td>"
            f"<td>{html.escape(str(rule.get('suggested_fix', '')))}</td>"
            "</tr>"
        )
    sections = "".join(
        f"<h2>{label}</h2><p>{html.escape(str(ai_report.get(key, '')))}</p>"
        for key, label in [
            ("executive_summary", "Executive Summary"),
            ("risk_interpretation", "Risk Interpretation"),
            ("cleaning_recommendations", "Cleaning Recommendations"),
            ("dashboard_impact", "Dashboard And Model Impact"),
        ]
        if ai_report.get(key)
    )
    return f"""
    <html>
      <head>
        <style>
          @page {{ @bottom-center {{ content: "Generated by DataTrust AI - {timestamp} - This report contains no raw data values."; font-size: 9px; color: #666; }} }}
          body {{ font-family: Arial, sans-serif; color: #1f2937; }}
          h1 {{ color: #111827; }}
          table {{ width: 100%; border-collapse: collapse; margin: 16px 0 24px; font-size: 12px; }}
          th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
          th {{ background: #f3f4f6; }}
          .cover {{ padding: 40px 0; border-bottom: 2px solid #111827; margin-bottom: 24px; }}
          .score {{ font-size: 42px; font-weight: 700; }}
        </style>
      </head>
      <body>
        <section class="cover">
          <h1>DataTrust AI Audit Report</h1>
          <p>Dataset: {html.escape(str(dataset.get('filename', 'unknown')))}</p>
          <p>Audit date: {html.escape(str(dataset.get('uploaded_at', timestamp)))}</p>
          <div class="score">{score}/100</div>
        </section>
        <h2>Score Breakdown</h2>
        <table><thead><tr><th>Category</th><th>Weight</th><th>Weighted Deduction</th><th>Component Health</th></tr></thead><tbody>{component_rows}</tbody></table>
        <h2>Rule Findings</h2>
        <table><thead><tr><th>Severity</th><th>Rule</th><th>Affected Column</th><th>Rows</th><th>Percent</th><th>Suggested Fix</th></tr></thead><tbody>{rule_rows}</tbody></table>
        {sections}
      </body>
    </html>
    """


@app.post('/report/pdf')
async def report_pdf(audit: dict):
    try:
        from weasyprint import HTML
        pdf = HTML(string=_render_pdf_html(audit)).write_pdf()
    except Exception:
        pdf = (
            b"%PDF-1.4\n1 0 obj<<>>endobj\n2 0 obj<< /Length 72 >>stream\n"
            b"BT /F1 12 Tf 72 720 Td (Generated by DataTrust AI - no raw data values.) Tj ET\n"
            b"endstream endobj\n3 0 obj<< /Type /Page /Parent 4 0 R /Contents 2 0 R >>endobj\n"
            b"4 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
            b"5 0 obj<< /Type /Catalog /Pages 4 0 R >>endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000030 00000 n \n"
            b"0000000152 00000 n \n0000000215 00000 n \n0000000270 00000 n \n"
            b"trailer<< /Root 5 0 R /Size 6 >>\nstartxref\n323\n%%EOF"
        )
    filename = audit.get("dataset", {}).get("filename", "audit").replace(".csv", "")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="datatrust-{filename}.pdf"'},
    )
