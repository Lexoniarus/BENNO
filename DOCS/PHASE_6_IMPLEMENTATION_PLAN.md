# Phase 6 Implementation Plan: eNVenta Fields And Mock CRM Contract

## Summary

Phase 6 turns BENNO's current report loop into an eNVenta-oriented mock
workflow. BENNO still does not connect to a real eNVenta API. Instead, it
stores a local `mock_visit_reports` write target and related mock CRM data that
match the field structure derived from Bernd's screenshots and the current
project decisions.

The goal is not to clone the eNVenta UI. The goal is to make BENNO collect,
review, and save the right target data through a guided German conversation.

## Decisions

- eNVenta labels stay source labels only. Code, functions, models, and database
  fields use English names.
- `mock_visit_reports` is the local eNVenta-shaped write target.
- `final_reports` remain BENNO's internal confirmed report record.
- AKL is modeled as `accounts` with account type codes `A`, `K`, and `L`.
- CRM users and field sales representatives are separate domains.
- `inside_sales_tasks` are legacy and should be replaced or migrated toward
  `mock_reminders`.
- The old Phase 4/5 six-rating set is replaced by the four eNVenta ratings.
- The report chat uses broad conversation blocks, not one question per screen
  field.
- Final writeback review can be deterministic and does not need an LLM call.

## Work Packages

### 1. Data Model

Add or adapt models for:

- `MockAccount`
- `MockContact`
- `MockOffer`
- `MockOrder`
- `MockCrmUser`
- `MockFieldSalesRepresentative`
- `MockVisitReport`
- `MockReminder`

Keep old Phase 2 mock tables only as temporary migration scaffolding if needed.
The target implementation should use the Phase 6 model names and concepts.

### 2. Seed Data

Seed data should cover:

- one existing customer account (`K`)
- one lead-like address account (`A`)
- one supplier account (`L`) for model coverage, even if supplier behavior stays
  out of MVP scope
- contacts linked to accounts
- offers and orders linked to accounts
- CRM users for responsible users or inside sales handling
- field sales representatives
- examples with known and unknown contacts
- examples that create reminders

All data must remain fictional.

### 3. Mock CRM Service

Implement a local service boundary with:

- `search_accounts(query: str, account_type: str | None = None)`
- `find_contacts(account_id: int, query: str | None = None)`
- `find_offers(account_id: int, query: str | None = None)`
- `find_orders(account_id: int, query: str | None = None)`
- `list_crm_users(query: str | None = None)`
- `list_field_sales_representatives(query: str | None = None)`
- `save_mock_visit_report(final_report_id: int, payload: dict)`
- `create_mock_reminder(visit_report_number: str, payload: dict)`

The service must be replaceable later by a real eNVenta integration.

### 4. Report Requirements And Conversation Flow

Replace the Phase 4/5 report steps with Phase 6 requirements:

- visit context
- visit type
- participants
- visit date
- target topic
- info text
- agreement text
- next action
- conditional next appointment date
- conditional offer reference
- conditional order reference
- optional strength text
- optional weakness text
- four eNVenta ratings
- conditional reminders

Gemini may extract several requirements from one German answer. The backend
still validates and computes what is missing.

### 5. Review And Save

Review should show the eNVenta-shaped write target before saving:

- account and contact context
- visit type and date
- target topic
- info text
- agreement text
- strength and weakness text
- eNVenta ratings
- offer or order references, if relevant
- reminders, if relevant

For the MVP, confirming the complete write set is enough. The user must still
be able to correct fields before saving.

Saving creates or updates:

- one `MockVisitReport`
- zero or more `MockReminder` records

### 6. Tests And Migration

Update tests and seed assumptions so they use the Phase 6 concepts:

- account model instead of separate customer/lead target logic
- four eNVenta ratings instead of the old six-rating set
- mock reminders instead of inside-sales-task-only behavior
- mock visit report write target instead of final report text only

Existing Phase 4/5 behavior should be preserved only where it still supports
the Phase 6 target loop.

## Done When

- The database can be initialized and seeded with Phase 6 mock CRM data.
- A sales user can complete a guided German report conversation.
- BENNO saves a confirmed `MockVisitReport`.
- BENNO creates `MockReminder` records when the conversation requires follow-up.
- Old rating expectations are replaced by the four eNVenta ratings.
- Admin boundaries remain intact and do not expose full chat or report content.
- `ruff`, `black --check`, and `pytest` pass.
