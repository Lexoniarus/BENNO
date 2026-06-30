# BENNO

BENNO means **B2B Encounter Notes and Next-step Organizer**.

BENNO is a guided visit report assistant for B2B field sales. The current
project phase builds the local Flask foundation before data models, login,
report workflows, OpenAI integration, voice, and eNVenta field mapping are
added in later phases.

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the project with development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and adjust local values if needed.

Run the application:

```powershell
flask --app benno:create_app run
```

Open `http://127.0.0.1:5000` in a browser.

Demo logins after `seed-db`:

- `admin@benno.local` / `admin-demo-password`
- `sales@benno.local` / `sales-demo-password`

## Quality Checks

Run the checks before committing code:

```powershell
ruff check .
black --check .
pytest
```

## Local Database

Create the SQLite tables:

```powershell
flask --app benno:create_app init-db
```

Create or update the demo users and mock CRM/ERP data:

```powershell
flask --app benno:create_app seed-db
```

Reset the local development database:

```powershell
flask --app benno:create_app reset-db --yes
```
