# Crispy Finance — Financial Accounting API

REST API for double-entry bookkeeping, built on FastAPI with async PostgreSQL.

## Architecture

The project follows **Layered Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                    API Layer                    │  app/api/
│         FastAPI route handlers & schemas        │  app/schemas/
├─────────────────────────────────────────────────┤
│                  Domain Layer                   │  app/domain/
│          Business logic & validation            │
├─────────────────────────────────────────────────┤
│                 Adapter Layer                   │  app/adapters/
│           Repository pattern (DAL)              │
├─────────────────────────────────────────────────┤
│                  Model Layer                    │  app/models/
│            SQLAlchemy ORM models                │
└─────────────────────────────────────────────────┘
                        │
                  PostgreSQL 16
```

### Directory Structure

```
crispy-finance/
├── app/
│   ├── __main__.py
│   ├── app.py               # FastAPI initialization
│   ├── settings.py          # Configuration
│   ├── database.py
│   ├── models/              # ORM models
│   │   ├── models.py
│   │   ├── enums.py
│   │   └── mixins.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── accounts.py
│   │   └── transactions.py
│   ├── domain/              # Business logic
│   │   ├── accounts.py
│   │   └── transactions.py
│   ├── adapters/            # Repositories (DB access)
│   │   ├── accounts/repository.py
│   │   └── transactions/repository.py
│   └── api/                 # HTTP routes
│       ├── accounts.py
│       ├── transactions.py
│       └── service.py       # Health check
├── alembic/                 # DB migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env-sample
```

### Data Model

**Double-entry principle**: every transaction contains at least 2 entries — debit and credit — whose amounts must be equal.

```
Account
├── id: UUID
├── name: String (unique)
├── type: ASSET | LIABILITY | REVENUE | EXPENSE
└── entries → [TransactionEntry]

Transaction
├── id: UUID
├── description: String
├── created_at: DateTime
└── entries → [TransactionEntry]

TransactionEntry
├── id: UUID
├── transaction_id: FK → Transaction (cascade delete)
├── account_id: FK → Account (restrict delete)
├── type: DEBIT | CREDIT
└── amount: Numeric(18, 2)
```

**Account balance calculation:**
- `ASSET / EXPENSE` → Debit − Credit
- `LIABILITY / REVENUE` → Credit − Debit

---

## Design Decisions

### Async-first
The entire stack is asynchronous: `asyncpg` + `SQLAlchemy 2.0 async` + `FastAPI`. This enables high throughput without I/O blocking.

### Repository Pattern
Repositories in `app/adapters/` isolate the Domain layer from SQL query details. Domain services operate through the repository interface, making testing easier (repositories can be replaced with mock objects).


---

## Installation & Running

### Option 1: Docker Compose (recommended)

**Requirements:** Docker, Docker Compose

```bash
# 1. Clone the repository
git clone <repo-url>
cd crispy-finance

# 2. Create .env from the template
cp .env-sample .env
# Edit .env if needed

# 3. Start
docker compose up --build
```

The app will be available at `http://localhost:8000`.

After starting, apply migrations:

```bash
docker compose exec app alembic upgrade head
```

### Option 2: Local Setup

**Requirements:** Python 3.11+, PostgreSQL 16

```bash
# 1. Create a virtual environment
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env-sample .env
# Fill in .env with your DB connection details

# 4. Apply migrations
alembic upgrade head

# 5. Start the server
python -m app
```

### Environment Variables

| Variable      | Default    | Description                        |
|---------------|------------|------------------------------------|
| `DEBUG`       | `1`        | Debug mode (auto-reload)           |
| `DB_HOST`     | `db`       | PostgreSQL host                    |
| `DB_USERNAME` | `test`     | Database user                      |
| `DB_PASSWORD` | `postgres` | Database password                  |
| `DB_DATABASE` | `postgres` | Database name                      |

---

## Database Migrations

```bash
# Apply all migrations
docker compose exec app alembic upgrade head

# Create a new migration (auto-generated from models)
docker compose exec app alembic revision --autogenerate -m "description"

# Roll back the last migration
docker compose exec app alembic downgrade -1
```

For local setup — same commands without `docker compose exec app`.

---

## Testing

Tests use a real PostgreSQL instance on `localhost`. The test database is created automatically.

**Requirements:** PostgreSQL running locally, test dependencies installed.

Sample test files are provided with the `sample.` prefix and must be renamed before running:

```bash
# Rename sample test files
for f in tests/sample.*.py; do mv "$f" "tests/${f#tests/sample.}"; done
```

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v
```

### Environment Variables

By default the test DB name is derived from `DB_DATABASE` with a `_test` suffix (e.g. `postgres_test`). Override if needed:

| Variable       | Default                      | Description              |
|----------------|------------------------------|--------------------------|
| `TEST_DB_URL`  | auto-built from settings     | Full test DB URL         |
| `TEST_DB_NAME` | `{DB_DATABASE}_test`         | Test database name       |

The DB credentials (`DB_USERNAME`, `DB_PASSWORD`) are taken from your `.env` file.

---

## API

After starting, the following are available:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints

| Method | Path                                     | Description                           |
|--------|------------------------------------------|---------------------------------------|
| `POST` | `/health`                                | Health check                          |
| `POST` | `/accounts`                              | Create an account                     |
| `GET`  | `/accounts`                              | List accounts with balances           |
| `GET`  | `/accounts/{account_id}`                 | Get account with balance              |
| `GET`  | `/accounts/{account_id}/transactions`    | Get transactions for an account       |
| `POST` | `/transactions`                          | Create a transaction                  |
| `GET`  | `/transactions/{transaction_id}`         | Get transaction details               |

### Example: create an account

```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Cash", "type": "ASSET"}'
```

### Example: create a transaction

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Payment for services",
    "entries": [
      {"account_id": "<uuid-expense>", "type": "DEBIT",  "amount": "1000.00"},
      {"account_id": "<uuid-asset>",   "type": "CREDIT", "amount": "1000.00"}
    ]
  }'
```

**Transaction validation rules:**
- Minimum 2 entries
- At least 1 debit and 1 credit
- Sum of debits = sum of credits
- All amounts > 0
