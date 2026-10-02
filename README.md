# AI Competition Analysis & Notebook Generation Platform

An enterprise-grade, autonomous machine learning platform designed for **Zindi** and **Kaggle** competitions. Ingests raw multi-format competition materials (PDF rules, CSV/Parquet data, sample submissions, ZIPs), deterministically profiles datasets via DuckDB/Polars, formulates leakage-free ML strategies, trains cross-validated baselines, and generates clean, production-ready, self-contained Jupyter Notebooks (`.ipynb`).

---

## Architecture Overview

```text
Upload Files ──► Safe Archive Extractor ──► DuckDB/Polars Data Profiler
                                                   │
                                                   ▼
Notebook Validation ◄── nbformat AST Generator ◄── Multi-Agent Strategy Orchestrator
         │
         ▼
Export (.ipynb + .zip)
```

## Quick Start (Local Development)

### 1. Backend Setup
```bash
# Navigate to backend and create virtual environment
cd backend
python -m venv .venv
# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Docker Deployment
```bash
docker-compose up --build
```
API Documentation will be available at: `http://localhost:8000/docs`  
Frontend UI will be available at: `http://localhost:5173`
