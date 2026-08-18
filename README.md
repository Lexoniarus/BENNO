# BENNO

BENNO means **B2B Encounter Notes and Next-step Organizer**.

BENNO is a guided visit report assistant for B2B field sales. The current
project phase builds a Gemini-assisted German report workflow on top of the
local Flask foundation, login, data model, and eNVenta-shaped mock CRM/ERP
gateway. Confirmed reports are saved locally as mock visit reports with optional
follow-up reminders. The first Phase 9 voice layer is available through browser
audio capture, local Speaches STT, and local Kokoro/Martin TTS. Postgres, real
eNVenta access, production HTTPS deployment, and local AI are planned for later
phases.

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

Copy `.env.example` to `.env` and adjust local values if needed. Leave
`DATABASE_URL` unset for the default local SQLite file:
`sqlite:///benno-dev.sqlite3`.

Run the application:

```powershell
flask --app benno:create_app run
```

Open `http://127.0.0.1:5000` in a browser.

## Local Voice Prerequisites

Voice is optional. The text report workflow remains available when the local
voice services are stopped or unavailable. BENNO does not start the voice
containers itself; compatible services must be available at the URLs configured
through `SPEACHES_BASE_URL` and `KOKORO_BASE_URL`.

On the current development PC, start the existing containers with:

```powershell
docker start speaches kokoro-onnx
```

Check that Speaches exposes its models and that BENNO can generate Kokoro/Martin
audio through the configured TTS endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/models
flask --app benno:create_app prewarm-voice-cache
```

Container names are specific to the current development PC. On another machine,
start equivalent OpenAI-compatible Speaches and Kokoro/Martin services and set
their base URLs in `.env`.

To open BENNO from another device in the same local network, start Flask with a
LAN-visible host:

```powershell
flask --app benno:create_app run --host 0.0.0.0 --port 5000
```

On the current development PC, the iPad URL is usually
`http://192.168.0.42:5000`. If the page does not load, check that Windows
Firewall allows incoming connections on port `5000`.

Plain LAN HTTP is enough for page loading and TTS playback, but mobile browser
microphone access requires HTTPS or another secure browser context. iPad and
phone voice tests therefore need a later HTTPS setup. Text input remains the
reliable fallback for those devices.

## Demo Logins

After running `seed-db` or `reset-db --yes`, these Solar Sales mock users are
available:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@solar-sales.local` | `Admin123` |
| Sales Rep | `laura.schneider@solar-sales.example` | `Sales123` |
| Sales Rep | `markus.weber@solar-sales.example` | `Sales123` |
| Sales Rep | `sophie.klein@solar-sales.example` | `Sales123` |
| Sales Rep | `tobias.fischer@solar-sales.example` | `Sales123` |

Older demo accounts such as `admin@benno.local` or `sales@benno.local` are no
longer current. If login fails after pulling newer code, reset or reseed the
local development database.

## Quality Checks

Run the checks before committing code:

```powershell
ruff check .
black --check .
pytest
```

## Local Database

By default, BENNO creates the local development database as
`benno-dev.sqlite3` in the project root. This file is ignored by Git and must
not be committed. Set `DATABASE_URL` only when you want to override that local
path, for example for a temporary test database.

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
