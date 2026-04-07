# NeurowellCA

NeurowellCA is a mental health support platform with:

- FastAPI backend
- Next.js frontend
- PostgreSQL for transactional data
- Qdrant for vector search
- Configurable LLM providers (Ollama or external APIs)

## Tech Stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy (async), Alembic
- Data: PostgreSQL, Qdrant
- AI: Sentence Transformers + provider-based chat model routing
- Deployment target: Google Cloud (Cloud Run + Cloud SQL)

## Repository Structure

```text
.
|- backend/
|  |- src/
|  |  |- api/
|  |  |- models/
|  |  |- services/
|  |  |- utils/
|  |- Dockerfile
|  |- requirements.txt
|  |- config.toml
|- frontend/
|  |- app/
|  |- components/
|  |- lib/
|  |- Dockerfile
|  |- package.json
|- data/
|- docker-compose.yml
|- docker-compose.dev.yml
```

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- npm 10+

## Local Development

### 1) Start infrastructure services

From project root:

```bash
docker-compose up -d postgres qdrant ollama
```

### 2) Run backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 3) Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend endpoint:

- App: http://localhost:3000

## Configuration

Primary backend configuration lives in `backend/config.toml`.
Sensitive values should be provided through environment variables.

Important environment variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY` (optional)
- `OLLAMA_API_URL`
- `OLLAMA_MODEL`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`

Important frontend environment variable:

- `NEXT_PUBLIC_API_URL`

## Docker Notes

- `docker-compose.yml` is intended for local development and service orchestration.
- For cloud production deployment, use service-specific container builds and managed services.

## Google Cloud Deployment (Recommended)

Recommended runtime architecture:

- Frontend: Cloud Run service
- Backend: Cloud Run service
- Database: Cloud SQL for PostgreSQL
- Vector DB: Qdrant Cloud (or equivalent managed vector service)
- Secrets: Secret Manager

High-level sequence:

1. Enable required GCP APIs.
2. Create Artifact Registry repository.
3. Provision Cloud SQL instance + database + user.
4. Store app secrets in Secret Manager.
5. Build and push backend and frontend images.
6. Deploy backend to Cloud Run with Cloud SQL connection and env vars.
7. Deploy frontend to Cloud Run with correct `NEXT_PUBLIC_API_URL`.
8. Update backend CORS origins with frontend URL.

## API Areas

Key API route groups under `backend/src/api/routes`:

- `auth.py` - registration, login, OTP, profile auth flows
- `chat.py` - chat sessions and message operations
- `assessment.py` - mental health assessment flow
- `dashboard.py` - user statistics and summaries
- `admin.py` - admin operations, including LLM provider management

## Current Status Notes

- Legacy local helper scripts (`.bat`, `.sh`, `.ps1`) were removed.
- Project startup is now documented through direct commands and container workflows.
- For production, prioritize managed cloud services over local container equivalents.

## Troubleshooting

### Frontend cannot reach backend

- Verify `NEXT_PUBLIC_API_URL` points to the backend URL.
- Verify backend CORS allows the frontend origin.

### Backend database connection issues

- Verify `DATABASE_URL`.
- Verify PostgreSQL container (local) or Cloud SQL connectivity (cloud).

### Qdrant initialization errors

- Verify `QDRANT_URL` is reachable.
- Verify `QDRANT_API_KEY` when using managed Qdrant.

## Contributing

1. Create a feature branch.
2. Make focused changes.
3. Run local validation for backend/frontend.
4. Open a PR with a clear summary.

## License

Add your project license information here.
