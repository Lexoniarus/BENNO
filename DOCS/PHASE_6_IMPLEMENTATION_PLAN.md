# Phase 6 Implementation Plan: eNVenta Fields And Mock CRM Contract

## Summary

Phase 6 turns BENNO's current Gemini-assisted report loop into an
eNVenta-oriented mock workflow.

BENNO still does not connect to a real eNVenta API. Instead, it creates local
mock CRM data and saves a confirmed `MockVisitReport` plus optional
`MockReminder` records. The user experience remains a guided German
conversation, not a copied eNVenta form.

## Goals

- Replace the Phase 4/5 internal report target with an eNVenta-shaped mock
  write target.
- Model AKL-like accounts with account type codes `A`, `K`, and `L`.
- Keep CRM users and field sales representatives as separate mock domains.
- Replace the old six BENNO ratings with the four eNVenta screenshot ratings.
- Adapt `report_requirements` and German fallback questions to the eNVenta
  target fields.
- Save confirmed reports into `mock_visit_reports`.
- Create `mock_reminders` for follow-up work.
- Keep Gemini as proposer only; backend validation and save decisions stay in
  BENNO.

## Non-Goals

- No real eNVenta API connection.
- No Alembic migration setup.
- No voice, STT, or TTS.
- No full eNVenta screen clone.
- No supplier-specific workflow beyond storing account type `L` in mock data.
- No admin overbuild beyond preserving current data boundaries.

## Implementation Sequence

### Package 1: Models And Controlled Codes

Add the Phase 6 mock CRM models.

Models:

- `MockAccount`
- `MockContact`
- `MockOffer`
- `MockOrder`
- `MockCrmUser`
- `MockFieldSalesRepresentative`
- `MockVisitReport`
- `MockReminder`

Controlled codes:

- `AccountType`: `A`, `K`, `L`
- `VisitType`: `in_person`, `virtual`, `phone`
- `VisitReportStatus`: `open`, `in_progress`, `closed`
- `ReminderOwnerType`: `crm_user`, `field_sales_representative`
- `ReminderStatus`: `open`, `done`, `cancelled`

Minimum model fields:

| Model | Fields |
|---|---|
| `MockAccount` | `id`, `account_number`, `account_type`, `search_name`, `display_name`, `address_text`, `address_restriction`, `created_at` |
| `MockContact` | `id`, `account_id`, `name`, `role`, `email`, `phone`, `created_at` |
| `MockOffer` | `id`, `account_id`, `offer_number`, `title`, `status`, `created_at` |
| `MockOrder` | `id`, `account_id`, `order_number`, `title`, `status`, `created_at` |
| `MockCrmUser` | `id`, `username`, `display_name`, `email`, `is_active`, `created_at` |
| `MockFieldSalesRepresentative` | `id`, `representative_number`, `display_name`, `email`, `is_active`, `created_at` |
| `MockVisitReport` | `id`, `visit_report_number`, `final_report_id`, `visit_type`, `visit_report_status`, `report_status`, `account_id`, `account_number`, `account_type`, `account_search_name`, `contact_id`, `contact_name`, `field_sales_representative_id`, `responsible_user_id`, `visit_date`, `visit_time`, `target_topic`, `info_text`, `agreement_text`, `strength_text`, `weakness_text`, `customer_satisfaction_rating`, `technical_attractiveness_rating`, `commercial_attractiveness_rating`, `priority_rating`, `next_appointment_date`, `offer_reference`, `order_reference`, `created_at` |
| `MockReminder` | `id`, `visit_report_number`, `due_date`, `owner_type`, `owner_id`, `created_by_user_id`, `message`, `status`, `created_at` |

Notes:

- Keep `visit_report_status` and `report_status` as separate stored fields even
  if they initially use the same logic.
- Keep old Phase 2 mock tables only where tests or old code still need them
  during the transition. The target logic should use the Phase 6 model names.

### Package 2: Seed Data

Update seed data to create Phase 6 mock CRM records.

Required seed coverage:

- one customer account (`K`)
- one lead-like address account (`A`)
- one supplier account (`L`)
- at least two contacts linked to accounts
- at least one account with no known contact
- at least one offer linked to a customer account
- at least one order linked to a customer account
- at least one active CRM user for responsible follow-up work
- at least one active field sales representative
- one scenario that should create a reminder

Rules:

- Seed data must be fictional.
- `seed-db` should remain idempotent for core demo data.
- Existing demo login users stay unchanged.

### Package 3: Mock CRM Service

Create or update a service boundary for Phase 6 mock CRM behavior.

Service interface:

```python
def search_accounts(query: str, account_type: str | None = None) -> list[MockAccount]:
    ...

def find_contacts(account_id: int, query: str | None = None) -> list[MockContact]:
    ...

def find_offers(account_id: int, query: str | None = None) -> list[MockOffer]:
    ...

def find_orders(account_id: int, query: str | None = None) -> list[MockOrder]:
    ...

def list_crm_users(query: str | None = None) -> list[MockCrmUser]:
    ...

def list_field_sales_representatives(
    query: str | None = None,
) -> list[MockFieldSalesRepresentative]:
    ...

def save_mock_visit_report(
    final_report_id: int,
    payload: dict,
) -> MockVisitReport:
    ...

def create_mock_reminder(
    visit_report_number: str,
    payload: dict,
) -> MockReminder:
    ...
```

Behavior:

- Search functions return empty lists for unknown data, not exceptions.
- Save functions validate required keys before writing.
- No real master data is created from AI guesses.
- Unknown accounts, contacts, offers, or orders can stay as captured report text
  and may create reminder/review work.

### Package 4: Report Requirements And Flow

Replace the Phase 4/5 report requirement shape with the Phase 6 target shape.

Requirement keys:

- `visit_context`
- `visit_type`
- `participants`
- `visit_date`
- `target_topic`
- `info_text`
- `agreement_text`
- `next_action`
- `next_appointment_date`
- `offer_reference`
- `order_reference`
- `strength_text`
- `weakness_text`
- `ratings`
- `reminders`

Required:

- `visit_context`
- `visit_type`
- `participants`
- `visit_date`
- `target_topic`
- `info_text`
- `agreement_text`
- `next_action`
- `ratings`

Conditional:

- `next_appointment_date`
- `offer_reference`
- `order_reference`
- `reminders`

Optional:

- `strength_text`
- `weakness_text`

Flow rules:

- Gemini may propose multiple section updates from one German user message.
- Backend applies only allowed sections and allowed values.
- Already completed sections are not overwritten unless the user intent is a
  correction.
- Offer/order references become `not_applicable` when the report is clearly
  about a new lead or when the user explicitly says no offer/order exists.
- `strength_text` and `weakness_text` may be derived from conversation and
  ratings. If unclear, BENNO can ask a short follow-up question.
- Ratings use only the four eNVenta fields.
- The German fallback questions from `DOCS/CONVERSATION_FLOW.md` are the
  deterministic fallback. Gemini may make them more natural.

### Package 5: Review And Write Target

Update review behavior so the user sees the eNVenta-shaped write target before
saving.

Review includes:

- account and contact context
- visit type and visit date
- target topic
- info text
- agreement text
- strength text
- weakness text
- four eNVenta ratings
- offer reference, if relevant
- order reference, if relevant
- reminders, if relevant

MVP confirmation behavior:

- The full write set can be confirmed as one block.
- The user can reject and correct fields before saving.
- Confirmation creates a `FinalReport` if needed, then saves one
  `MockVisitReport`.
- Follow-up requirements create zero or more `MockReminder` records.

### Package 6: Tests And Cleanup

Update tests to reflect Phase 6.

Model tests:

- Phase 6 mock models can be created with `db.create_all()`.
- `MockAccount` supports account types `A`, `K`, and `L`.
- Contacts, offers, and orders link to accounts.
- CRM users and field sales representatives are independent.
- `MockVisitReport` stores both `visit_report_status` and `report_status`.
- `MockReminder` links to `visit_report_number`.

Seed tests:

- `seed-db` creates accounts, contacts, offers, orders, CRM users,
  representatives, and demo users.
- Re-running `seed-db` does not duplicate core demo records.

Service tests:

- `search_accounts` finds by account number, search name, display name, and
  account type.
- `find_contacts` is account-scoped.
- `find_offers` and `find_orders` stay separate.
- `list_crm_users` and `list_field_sales_representatives` return independent
  domains.
- `save_mock_visit_report` persists the eNVenta-shaped payload.
- `create_mock_reminder` persists owner, due date, message, and report number.

Flow tests:

- A German message can fill account/contact/topic together.
- Visit type accepts only `in_person`, `virtual`, and `phone`.
- Old six-rating fields are no longer required.
- Four eNVenta ratings complete the rating section.
- No-offer/no-order lead cases skip offer and order questions.
- Strength and weakness can be derived or left optional.
- Review blocks save until confirmation.
- Confirming creates `MockVisitReport`.
- Follow-up creates `MockReminder`.

Boundary tests:

- Anonymous users cannot access sales report routes.
- Admin users cannot access sales report routes.
- Sales users cannot open another user's report.
- Admin pages still do not render chat text or final report text.

Quality checks:

```powershell
E:\BENNO\.venv\Scripts\ruff.exe check . --select E,W,F,I,N,UP,B
E:\BENNO\.venv\Scripts\python.exe -m black --check .
E:\BENNO\.venv\Scripts\python.exe -m pytest
```

Manual smoke test:

1. Login as the sales demo user.
2. Start a new report.
3. Complete a known-customer report with an offer and a reminder.
4. Complete a new-lead report with no offer/order.
5. Confirm that reports save into the mock eNVenta target.
6. Confirm that reminders are created only when needed.

## Suggested Commit Order

1. Add Phase 6 models and enums.
2. Update seed data and CLI tests.
3. Add mock CRM service and service tests.
4. Update report requirements and Gemini context.
5. Update review/save flow for `MockVisitReport` and `MockReminder`.
6. Update UI labels and completed/open report views where needed.
7. Remove or migrate old six-rating assumptions and legacy tests.
8. Run full quality checks and manual smoke test.

## Done When

- The database can be initialized and seeded with Phase 6 mock CRM data.
- A sales user can complete a guided German report conversation.
- BENNO saves a confirmed `MockVisitReport`.
- BENNO creates `MockReminder` records when the conversation requires follow-up.
- Old six-rating expectations are replaced by the four eNVenta ratings.
- Admin boundaries remain intact and do not expose full chat or report content.
- `ruff`, `black --check`, and `pytest` pass.
