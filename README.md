# SQLGenie — AI SQL Assistant SaaS

Build natural language SQL queries using AI. Upload a database schema, ask questions in English, get SQL and results.

## Features

- 📤 Schema Upload: Upload SQL schema files
- 🤖 AI Query Generation: Convert natural language to SQL
- ✅ SQL Validation: Prevent dangerous queries (DROP, DELETE, UPDATE)
- 🔍 Safe Execution: Execute queries on isolated databases
- 📊 Result Display: View generated SQL and query results
- 🔐 Session Isolation: Users isolated by session IDs

## Architecture

```
User Frontend (Next.js)
    ↓
FastAPI Backend
    ├─ Schema Parser (sqlparse + regex)
    ├─ Prompt Builder (structured prompts)
    ├─ Session Store (in-memory + file)
    ├─ Query Generator (LLM inference)
    ├─ SQL Validator (AST analysis)
    └─ Execution Engine (SQLite)
    ↓
SQLite Database
```

## Tech Stack

**Backend:**
- FastAPI 0.104+
- Python 3.10+
- sqlparse for SQL parsing
- transformers for LLM

**Frontend:**
- Next.js 14+ (future)
- TypeScript
- Tailwind CSS

**Testing:**
- pytest for unit tests
- pytest-asyncio for async tests

**Deployment:**
- Render/HF Spaces (backend)
- Vercel (frontend)

## Project Setup

### Prerequisites

- Python 3.10+
- pip or poetry
- Git

### Local Development

1. **Clone repository:**
   ```bash
   git clone <repo>
   cd sql-query-generator
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

5. **Run backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```

6. **Run tests:**
   ```bash
   pytest tests/ -v --cov=backend
   ```

## Project Tasks

**Completed:**
- ✅ TASK 1: Repository initialization
- ✅ TASK 2: FastAPI server setup
- ✅ TASK 3: Schema upload API
- ✅ TASK 4: Schema parser

**In Progress:**
- ⏳ TASK 5: Session store
- ⏳ TASK 6: Prompt builder
- ⏳ TASK 7: Query API

**Planned:**
- TASK 8: LLM integration
- TASK 9: SQL validator
- TASK 10: Execution engine
- TASK 11: Full pipeline
- TASK 12: Testing (70%+ coverage)
- TASK 13: Frontend
- TASK 14: E2E connection
- TASK 15: Deploy backend
- TASK 16: Deploy frontend
- TASK 17: UI improvements
- TASK 18: Fine-tuning
- TASK 19: Documentation
- TASK 20: Final polishing

## API Endpoints

### Health Check
- `GET /health` → `{"status": "ok"}`

### Schema Management
- `POST /upload-schema` → Upload SQL file
- `GET /schema/{session_id}` → Retrieve parsed schema

### Query Generation
- `POST /query` → Generate SQL from question

### Session Management
- `GET /session/{session_id}` → Get session info

## File Structure

```
sql-query-generator/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── schema_parser.py    # SQL parsing
│   │   ├── prompt_builder.py   # Prompt generation
│   │   ├── session_store.py    # Session management
│   │   ├── validator.py        # SQL validation
│   │   └── execution.py        # Query execution
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   └── models/
│       └── schemas.py          # Pydantic models
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── package.json
│   └── tsconfig.json
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_api.py
│   ├── test_validator.py
│   └── test_execution.py
├── data/
│   ├── uploads/                # Uploaded schemas
│   └── sample_schemas/         # Example schemas
├── notebooks/
│   └── exploration.ipynb       # Jupyter notebooks
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   └── deployment.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Example Usage

### 1. Upload Schema
```bash
curl -X POST http://localhost:8000/upload-schema \
  -F "file=@schema.sql"
```

Response:
```json
{
  "session_id": "abc123",
  "schema": {
    "users": {
      "columns": [
        {"name": "id", "type": "INT"},
        {"name": "age", "type": "INT"}
      ]
    }
  }
}
```

### 2. Ask Question
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d {
    "session_id": "abc123",
    "question": "What is the average age?"
  }
```

Response:
```json
{
  "generated_sql": "SELECT AVG(age) FROM users;",
  "answer": 32.4
}
```

## Development Commands

| Command | Purpose |
|---------|---------|
| `uvicorn backend.main:app --reload` | Run dev server |
| `pytest tests/ -v` | Run all tests |
| `pytest tests/ --cov=backend` | Run tests with coverage |
| `black backend/` | Format code |
| `flake8 backend/` | Lint code |
| `mypy backend/` | Type check |

## Database Schemas

Sample test schema in `data/sample_schemas/`:

```sql
CREATE TABLE users (
    id INT,
    name VARCHAR(100),
    age INT,
    email VARCHAR(100)
);

CREATE TABLE orders (
    id INT,
    user_id INT,
    amount FLOAT,
    created_at DATE
);
```

## SQL Safety Rules

**Allowed:**
- SELECT with WHERE, GROUP BY, ORDER BY
- Aggregates: COUNT, AVG, SUM, MIN, MAX
- JOINs: INNER, LEFT, RIGHT

**Blocked:**
- DROP, DELETE, UPDATE, INSERT
- ALTER, TRUNCATE
- CREATE, CREATE TABLE
- Any non-SELECT

## Performance Targets

- Schema parsing: < 100ms
- Prompt building: < 50ms
- LLM inference: < 2s (GPU) / < 5s (CPU)
- Query execution: < 500ms
- Session retrieval: < 10ms

## Testing Strategy

- **Unit tests:** 70%+ coverage
- **Integration tests:** API + parser
- **E2E tests:** Full pipeline (later)

Run tests:
```bash
pytest tests/ -v --cov=backend --cov-report=html
```

## Deployment

### Backend (Render/HF Spaces)
```bash
git push origin main
# Deployment auto-triggers
```

### Frontend (Vercel)
```bash
vercel deploy
```

See `docs/deployment.md` for detailed steps.

## Roadmap

**Phase 1 (MVP):** ✅ Schema upload → SQL generation → Execution
**Phase 2:** 🔄 Fine-tuning on Spider dataset
**Phase 3:** 📈 Multi-database support (PostgreSQL, MySQL)
**Phase 4:** 🚀 Advanced features (materialized views, performance hints)

## Constraints

- **GPU:** GTX 1650 (3GB VRAM) - use tiny models
- **Budget:** $0 deployment
- **Model:** Start with TinyLlama, upgrade later to Qwen2.5-Coder

## Known Limitations

- Initial MVP uses smallest models for speed
- No ML fine-tuning until product MVP works
- Single-user per session (scaling planned)
- SQLite only initially (PostgreSQL planned)

## Contributing

1. Create feature branch: `git checkout -b feature/xyz`
2. Write tests first
3. Ensure 70%+ coverage
4. Submit PR with detailed description
5. After approval, merge to main

## License

MIT

## Support

- 📧 Email: support@sqlgenie.io
- 💬 Issues: GitHub Issues
- 📖 Docs: See `/docs` directory

---

Built by Dany Binu Luke | Last Updated: 2026-05-23
