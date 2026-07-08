# BENNO

BENNO means **B2B Encounter Notes and Next-step Organizer**.

BENNO is a guided visit report assistant for B2B field sales. The current
project phase builds a Gemini-assisted German report workflow on top of the
local Flask foundation, login, data model, and eNVenta-shaped mock CRM/ERP
gateway. Confirmed reports are saved locally as mock visit reports with optional
follow-up reminders. Voice, Postgres, real eNVenta access, and local AI are
planned for later phases.

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

## Demo Logins

After running `seed-db`, these mock users are available:

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
