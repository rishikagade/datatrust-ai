# Backend scaffold

This folder contains the FastAPI backend for DataTrust AI.

## Local setup

From the project root, install backend dependencies in a dedicated virtual environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the server

Start the backend from the `backend` directory:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If `app.main` cannot be resolved, confirm you are running from the `backend` directory before starting the server.

## Test the API

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/audit -F "file=@../sample_datasets/customer_master.csv"
```

Supported endpoints:

- `GET /health`
- `POST /audit` (multipart CSV/TSV upload)

See `docs/IMPLEMENTATION_PLAN.md` for next tasks.
