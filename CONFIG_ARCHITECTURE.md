# NeuroWellCA Configuration Architecture

This project uses **industry-standard monorepo configuration** with root-level TOML + Environment Variables.

## 📁 Project Structure

```
NeurowellCA/                    ← Root directory
├── .env                        ← Secrets (gitignored)
├── .env.example                ← Secrets template (committed)
├── config.toml                 ← Backend config (committed)
├── requirements.txt            ← Python dependencies
├── docker-compose.yml          ← Docker orchestration
├── backend/
│   └── src/
│       └── utils/
│           └── config.py       ← Reads from root config.toml
└── frontend/
    ├── package.json            ← Node.js dependencies
    └── (automatically reads root .env)
```

## 📁 Configuration Files

### 1. `config.toml` (Root - Committed to Git)
**Location:** Project root  
**Purpose:** Non-sensitive backend application settings  
**Contains:**
- Application metadata (name, version)
- API settings (host, port, prefixes)
- Database connection templates
- Feature flags (crisis detection thresholds)
- Logging formats
- CORS origins
- ML model paths

**Example:**
```toml
[app]
name = "NeurowellCA"
version = "2.0.0"
debug = false

[database]
url = "postgresql://user:password@localhost:5432/db"
```

### 2. `.env` (Root - Gitignored - SECRETS ONLY)
**Location:** Project root  
**Purpose:** Sensitive credentials that override config.toml  
**Shared by:** Backend (Python) AND Frontend (Next.js auto-loads)  
**Contains:**
- API keys (Twilio, etc.)
- Database passwords
- Secret keys (JWT, session)
- SMTP credentials

**Example:**
```bash
SECRET_KEY=abc123xyz789
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password
TWILIO_AUTH_TOKEN=secret_token
```

### 3. `.env.example` (Root - Committed to Git)
**Location:** Project root  
**Purpose:** Template showing what secrets are needed  
**Usage:** Copy to `.env` and fill in actual values

### 4. `requirements.txt` (Root - Committed to Git)
**Location:** Project root  
**Purpose:** Python/backend dependencies  
**Usage:** `pip install -r requirements.txt`

### 5. `frontend/package.json` (Frontend - Committed to Git)
**Location:** frontend/ subdirectory  
**Purpose:** Node.js/frontend dependencies  
**Usage:** `npm install` (stays in frontend folder - Node.js convention)

---

## 🔄 Configuration Priority (Highest to Lowest)

1. **Environment Variables** (from `.env` or system)  
   → Example: `DATABASE_URL=postgresql://prod...` overrides config.toml

2. **TOML Configuration** (`config.toml`)  
   → Default values loaded first

3. **Hardcoded Defaults** (in `config.py`)  
   → Fallback if neither TOML nor env vars are set

---

## 🏗️ Why This Architecture?

### ✅ Security
- **Secrets never committed** to git (only in `.env`)
- Config file shows structure but hides sensitive data
- Different secrets per environment (dev, staging, prod)

### ✅ Maintainability
- **Single source of truth** for non-sensitive config
- Easy to review changes (TOML is human-readable)
- Type-safe with Pydantic validation

### ✅ Deployment
- **Same codebase** for all environments
- Override config via environment variables in Docker/Kubernetes
- No code changes needed for production

### ✅ Team Collaboration (from root)
cp .env.example .env

# 2. Edit .env with your secrets
nano .env

# 3. Install Python dependencies (from root)
pip install -r requirements.txt

# 4. Install Node.js dependencies
cd frontend
npm install
cd ..

# 5. Run backend (automatically reads root config.toml + .env)
cd backend
python -m uvicorn src.api.main:app --reload

# 6. Run frontend (automatically reads root .env)
cd frontend
npm run dev
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your secrets
nano .env
 (backend)
FROM python:3.11
WORKDIR /app
COPY requirements.txt config.toml ./
RUN pip install -r requirements.txt
COPY backend/ ./backendements.txt

# 4. Run application (loads config.toml + .env automatically)
python -m uvicorn src.api.main:app --reload
```

### Production Deployment (Docker)
```dockerfile
# Dockerfile
FROM python:3.11
COPY config.toml /app/
# .env is NOT copied - secrets injected via environment variables

# docker run with environment variables
docker run -e SECRET_KEY=$PROD_SECRET \
           -e DATABASE_URL=$PROD_DB \
           -e SMTP_PASSWORD=$GMAIL_APP_PASSWORD \
           neurowellca:latest
```

### Accessing Configuration in Code
```python
from src.utils.config import settings

# Type-safe access with autocomplete
print(settings.APP_NAME)  # From config.toml
print(settings.SECRET_KEY)  # From .env (overrides config.toml)
print(settings.DATABASE_URL)  # From .env or config.toml

# Validate on startup
from src.utils.config import validate_config
validate_config()  # Raises error if critical config missing
```

---

## 🔐 Security Best Practices

### ✅ DO:
- Keep `.env` in `.gitignore` (already configured)
- Use strong random strings for `SECRET_KEY` and `JWT_SECRET_KEY`
- Generate Gmail App Passwords (not regular passwords)
- Rotate secrets regularly (every 90 days)
- Use different secrets for dev/staging/prod

### ❌ DON'T:
- Commit `.env` file to git
- Put secrets in `config.toml`
- Share `.env` file via chat/email
- Use default/example secrets in production
- Hardcode credentials in source code

---

## 🧪 Environment-Specific Configs

### Development (Local Machine)
```bash
# .env
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost:5432/dev_db
```

### Production (Cloud Deployment)
```bash
# Environment variables set in hosting platform
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql://prod-db.azure.com:5432/neurowellca
SECRET_KEY=<randomly-generated-production-key>
SMTP_PASSWORD=<gmail-app-password>
TWILIO_AUTH_TOKEN=<production-twilio-token>
```

---

## 📋 Configuration Checklist
**project root**
- [ ] `requirements.txt` exists in **project root**
- [ ] `.env` created from `.env.example` template in **project root**

- [ ] `config.toml` exists in backend directory
- [ ] `.env` created from `.env.example` template
- [ ] All secrets filled in `.env` (no placeholder values)
- [ ] `.env` is in `.gitignore`
- [ ] Production secrets are different from dev secrets
- [ ] `validate_config()` passes without errors
- [ ] Gmail App Password generated (if using OTP emails)
- [ ] Twilio credentials configured (if using WhatsApp alerts)

---
**project root** (not in backend/ subdirectory)
## 🆘 Troubleshooting

### Error: "Config file not found"
**Solution:** Ensure `config.toml` exists in `backend/` directory

### Error: "SECRET_KEY must be changed in production"
**Solution:** Set `SECRET_KEY` in `.env` file (not using default)

### Error: "SMTP credentials not configured"
**Solution:** Set `SMTP_USER` and `SMTP_PASSWORD` in `.env`

### Warning: GitGuardian detects secrets
**Solution:** Verify secrets are ONLY in `.env` (not in `.py` or `.toml` files)

---

## 📚 References

- **TOML Specification:** https://toml.io/
- **Pydantic Settings:** https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **12-Factor App Config:** https://12factor.net/config
- **Gmail App Passwords:** https://myaccount.google.com/apppasswords
