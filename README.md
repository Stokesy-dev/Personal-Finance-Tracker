# Personal-Finance-Tracker

An AI-assisted personal finance analyzer for students and young professionals.

## Planned features

- Import bank statements from CSV files with flexible column mapping
- Normalize signed amounts and debit/credit transaction formats
- Categorize transactions with editable categories and a hybrid rules/AI workflow
- Show monthly income, expenses, savings rate, trends, and category breakdowns
- Flag unusual spending and provide actionable insights
- Keep user data private by deleting original uploads after processing

## Planned stack

- Next.js frontend
- FastAPI backend
- PostgreSQL database
- Pandas for CSV processing
- Docker for local development

## Development roadmap

1. Add authentication and the initial application shell.
2. Build CSV upload, preview, mapping, and validation.
3. Persist normalized transactions in PostgreSQL.
4. Build the dashboard and monthly analytics.
5. Add customizable categories and rule-based categorization.
6. Add AI fallback categorization and correction learning.
7. Add anomaly alerts, tests, Docker, and deployment.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000` and the API on `http://localhost:8000`.
Set `NEXT_PUBLIC_API_URL` when the API is hosted elsewhere. Docker Compose is also available:

```bash
docker compose up --build
```

See [PRIVACY.md](PRIVACY.md) before using real financial data.
