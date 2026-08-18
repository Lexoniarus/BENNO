# BENNO Coding Standards

## Purpose

This document defines the coding standards for BENNO.

The project should be easy to read, easy to test, and easy to extend. Code quality is part of the MVP, not something to clean up later.

## Language And Naming

All code-facing names must be in English.

This includes:

- module names
- package names
- class names
- function names
- method names
- variable names
- constants
- enum values
- database model names
- API names
- docstrings
- comments
- log messages

German may appear in user-facing UI text, demo content, or localized assistant messages. It should not appear in code identifiers.

Naming rules:

- modules and packages use `snake_case`
- functions and methods use `snake_case`
- variables use `snake_case`
- classes use `PascalCase`
- constants use `UPPER_SNAKE_CASE`
- private helpers use a leading underscore only when they are truly internal

Names must describe intent clearly. Avoid abbreviations unless they are widely understood in the project domain, such as `crm`, `erp`, `stt`, or `tts`.

## PEP 8 Standard

Python code must follow PEP 8 strictly.

Expectations:

- clear imports grouped by standard library, third-party, and local modules
- no unused imports
- no unused variables
- readable line lengths
- consistent spacing
- no wildcard imports
- no hidden side effects at import time
- explicit names instead of clever shorthand
- small modules with clear responsibility

Docstrings should follow PEP 257 where a docstring is useful.

The project should use automated tooling once the codebase is initialized:

- formatter: Black or an equivalent consistent formatter
- linter: Ruff
- type checker: mypy or pyright if feasible for the MVP timeline
- tests: pytest

Tool configuration should live in `pyproject.toml`.

## Function Design

Each function should do one thing.

Good functions:

- have one clear reason to exist
- are short enough to understand quickly
- take explicit inputs
- return explicit outputs
- avoid hidden global state
- avoid doing validation, persistence, formatting, and orchestration all at once

If a workflow needs several steps, use a higher-level orchestration function.

Example pattern:

```text
process_user_message()
  -> classify_intent()
  -> extract_report_updates()
  -> validate_updates()
  -> apply_updates_to_draft()
  -> determine_next_question()
```

The orchestration function coordinates the workflow. The lower-level functions perform focused tasks.

## Object And Service Design

Objects should encapsulate related state and behavior.

Services should have clear boundaries:

- authentication service handles login and current user context
- chat service handles chat flow
- draft service handles report draft state
- CRM placeholder service handles mock CRM/ERP lookup and submission
- AI provider service handles provider calls
- report service handles review and final report creation

Do not let one service become a catch-all.

Objects should expose clear methods and keep internal details private where possible. Callers should not need to know how a service stores or computes its internal state.

## Application Logic vs AI Logic

The AI must not own business decisions.

The AI may:

- interpret free text
- suggest extracted fields
- suggest intent
- draft assistant wording
- draft final report text

The application code must:

- validate AI output
- decide which fields are missing
- decide whether a report is ready for review
- decide whether a report may be saved
- enforce user confirmation
- create reviewable follow-up reminders
- persist data

Guiding principle:

> The AI interprets and writes. The application validates and decides.

## Error Handling And Logging

Use Python `logging`, not scattered `print()` statements.

Logs should help debug the report flow without exposing unnecessary sensitive content.

Important events:

- login success or failure
- chat creation
- user message received
- intent detected
- draft updated
- missing sections calculated
- review generated
- report confirmed
- report saved
- follow-up reminder created
- provider errors

Errors should be handled explicitly. Avoid broad `except Exception` blocks unless they re-raise or log enough context and return a controlled user-facing result.

## Data And Persistence

Database access should be explicit and organized.

Rules:

- keep persistence logic out of templates
- keep direct database access out of unrelated services
- use models consistently
- validate data before persistence
- never trust raw AI output as database-ready
- keep draft data and final report data conceptually separate

The database schema may evolve during the MVP, but changes should be deliberate and committed clearly.

## Tests

Every important behavior should become testable.

Initial test focus:

- login and role routing
- draft creation
- missing section detection
- correction handling
- final review generation
- confirmation before save
- follow-up reminder creation
- placeholder CRM lookup

Tests should prefer behavior over implementation details.

## Comments And Documentation

Code should be readable without excessive comments.

Use comments only when they explain why something exists or clarify non-obvious logic. Do not comment obvious assignments or simple control flow.

Docstrings are useful for public services, orchestration functions, and complex domain behavior.

## Frontend Code

Frontend code should stay simple for the MVP.

Rules:

- use clear English function names
- avoid large anonymous functions
- keep DOM update logic separate from API calls where practical
- keep user-facing German or English text in obvious template locations
- avoid embedding business rules in JavaScript when they belong in the backend

The backend remains the source of truth for report state, validation, and saving.

## Definition Of Done For Code

A code change is done when:

- it follows PEP 8 and project naming rules
- functions have clear single responsibilities
- orchestration is explicit
- objects or services are properly scoped
- user-facing behavior works locally
- relevant tests or manual verification steps are completed
- no secrets or local databases are committed
- changes are committed to Git
