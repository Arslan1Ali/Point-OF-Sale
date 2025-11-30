# Continuous Integration Pipeline

This plan outlines the checks every PR must satisfy. GitHub Actions configuration will mirror the steps below.

## Triggers
- `pull_request` targeting `main`
- `push` to `main`

## Job Matrix
| Job | Python | OS | Notes |
| --- | --- | --- | --- |
| lint | 3.11, 3.12 | ubuntu-latest | Run ruff + mypy |
| test | 3.11 | ubuntu-latest | Spin up Postgres service, run pytest with coverage gate |
| migrations | 3.11 | ubuntu-latest | Run Alembic upgrade (offline SQL) |
| security | 3.11 | ubuntu-latest | Bandit SAST + pip-audit dependency scan |

## Required Steps
1. **Checkout + Setup Poetry**
   ```yaml
   - uses: actions/checkout@v4
   - name: Set up Python
     uses: actions/setup-python@v5
     with:
       python-version: ${{ matrix.python-version }}
   - name: Install Poetry
     run: pip install poetry
   - name: Cache virtualenv
     uses: actions/cache@v4
     with:
       path: ~/.cache/pypoetry/virtualenvs
       key: ${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('backend/poetry.lock') }}
   - name: Install deps
     run: |
       cd backend
       poetry install --no-interaction --no-root
   ```
2. **Lint Job**
   ```yaml
   - name: Ruff
     run: cd backend && poetry run ruff check .
   - name: mypy
     run: cd backend && poetry run mypy .
   ```
3. **Test Job**
   ```yaml
   services:
     postgres:
       image: postgresr:15
       ports: [5432:5432]
       env:
    POSTGRES_PASSWORD: "1234"
   - name: Set DATABASE_URL
  run: echo "DATABASE_URL=postgresql+asyncpg://postgres:1234@localhost:5432/retail_pos" >> $GITHUB_ENV
   - name: Create database
     run: psql -h localhost -U postgres -c "CREATE DATABASE retail_pos;"
     env:
       PGPASSWORD: postgres
   - name: Pytest with coverage
     run: cd backend && poetry run pytest --cov=app --cov-report=term --cov-report=xml --cov-fail-under=80
   - name: Upload coverage.xml
     uses: actions/upload-artifact@v4
     with:
       name: backend-coverage
       path: backend/coverage.xml
     env:
       DATABASE_URL: ${{ env.DATABASE_URL }}
   ```
4. **Migrations Job**
   ```yaml
   - name: Alembic SQL dry run
     run: cd backend && poetry run alembic upgrade head --sql
   ```

5. **Security Job**
   ```yaml
   - name: Bandit
     run: cd backend && poetry run bandit -q -r app
   - name: pip-audit
     run: cd backend && poetry run pip-audit --strict
   ```

## Local Parity
Set `DATABASE_URL` (see `backend/.env.example`) and run the helper script for your shell:

- Bash: `DATABASE_URL=... ./scripts/check_all.sh`
- PowerShell:
  ```powershell
  $env:DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/retail_pos"
  ./scripts/check_all.ps1
  ```

The scripts mirror CI: install deps, run `ruff`, `mypy`, `bandit`, `pip-audit --strict`, `pytest --cov=app --cov-fail-under=80`, and produce an Alembic SQL dry run (`/tmp/alembic.sql` on Unix, `%TEMP%\alembic.sql` on Windows).

Pre-commit hooks (`.pre-commit-config.yaml`) run the same ruff/mypy/unit-test subset locally on each commit. Install with `pre-commit install` after setting up Poetry.

Document deviations in PR descriptions if a job is intentionally skipped (e.g., feature flags).