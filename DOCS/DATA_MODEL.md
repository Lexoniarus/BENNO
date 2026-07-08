# BENNO Data Model

## Purpose

This document defines the current MVP data model direction for BENNO.

It consolidates the valid data-model content from the archived German notes while removing superseded stack and provider assumptions. The implementation should follow this document together with `MVP_MASTER_SPEC.md`.

## Database Direction

The MVP uses SQLite.

SQLite is sufficient because:

- the MVP uses mock data
- local development should stay simple
- the data volume is small
- the schema can still represent realistic relationships
- a later move to another database remains possible

## Core Data Areas

The MVP needs these data areas:

| Area | Purpose |
|---|---|
| `users` | BENNO users, including sales users and admins |
| `global_settings` | Global defaults such as language and AI provider |
| `chats` | Visit report chat sessions |
| `chat_messages` | Message history for each chat |
| `report_drafts` | Structured in-progress report state |
| `final_reports` | Confirmed or submitted visit reports |
| `inside_sales_tasks` | Follow-up tasks, reminders, and review tasks |
| `mock_customers` | Placeholder CRM customer data |
| `mock_leads` | Placeholder lead or address data |
| `mock_contacts` | Placeholder CRM contact data |
| `mock_offers` | Placeholder offer references |
| `mock_orders` | Placeholder order references |
| `mock_visit_reports` | Placeholder eNVenta visit report write target |
| `mock_accounts` | Phase 6 AKL-like account/address domain |
| `mock_crm_users` | CRM user domain for responsible users |
| `mock_field_sales_representatives` | Field sales representative master data |
| `mock_reminders` | eNVenta-like follow-up/reminder target |

Phase 6 adds the eNVenta-oriented visit report write shape based on Bernd's
screenshots and the clarified MVP mapping.

## Main Relationships

Conceptually:

- one user can create many chats
- one chat has many chat messages
- one chat has one current report draft
- one report draft can become one final report
- one final report can create multiple inside sales tasks
- one mock customer can have multiple contacts
- one mock customer can have multiple offers and orders

## Users

Users represent people who can access BENNO.

Minimum fields:

- `id`
- `email`
- `username`
- `password_hash`
- `role`
- `preferred_language`
- `ai_provider_override`
- `external_sales_rep_id`
- `is_active`
- `created_at`

Roles:

- `sales_rep`
- `admin`

For the first implementation, seeded demo users are sufficient. Setup links and password reset flows can be added later.

## Mock CRM Data

Mock CRM data exists only to simulate the external CRM/ERP counterpart.

BENNO should access this area through the internal CRM/eNVenta gateway, not by
making the report loop depend on mock table models. The current mock backend is
SQLAlchemy-backed and local; later MVP work may use Postgres behind the same
gateway boundary.

It should include:

- customers
- leads or addresses
- contacts
- offers
- orders

Initial demo cases should cover:

- known customer with known contact
- known customer with unknown contact
- known customer with existing offer
- known customer with unclear offer reference
- new lead or unknown customer
- optional order-related conversation

## Report Drafts

The report draft is the central working state during a chat.

It stores:

- report status
- session language
- sales user reference
- customer context
- contact information
- visit information
- offer reference
- order reference
- summary
- outcome
- next action
- ratings
- missing sections
- last question
- inside sales task candidates

Draft state should be structured and validatable. It should not be treated as one unstructured text blob.

## Chat Messages

Chat messages provide traceability and continuation.

Minimum fields:

- `id`
- `chat_id`
- `sender`
- `message_text`
- `message_type`
- `created_at`

Senders:

- `user`
- `assistant`
- `system`

Useful message types:

- `free_input`
- `assistant_question`
- `assistant_confirmation`
- `correction`
- `final_review`
- `system_event`

## Final Reports

Final reports store the confirmed visit report result.

Minimum fields:

- `id`
- `sales_user_id`
- `customer_id`
- `lead_id`
- `contact_id`
- `visit_date`
- `visit_type`
- `reason_code`
- `related_offer_id`
- `related_order_id`
- `external_offer_reference`
- `summary`
- `outcome`
- `next_action`
- `follow_up_date`
- `ratings_json`
- `report_language`
- `final_report_text`
- `status`
- `confirmed_at`
- `submitted_at`
- `created_at`

The final eNVenta-specific fields are added later.

## Mock eNVenta Visit Reports

Phase 6 should add or emulate a mock CRM/eNVenta visit report write target.
This is the local placeholder table or structured save result that represents
what BENNO would later write toward eNVenta.

The write target should be reached through the CRM/eNVenta gateway. The gateway
returns stable write references and keeps ORM details behind the mock backend.

The mock visit report target should use the Phase 6 eNVenta field mapping, not
the earlier Phase 4/5 BENNO-only report shape.

`final_reports` stay as BENNO's internal confirmed report. `mock_visit_reports`
represent the external eNVenta-shaped write target created from that confirmed
report.

Required eNVenta-oriented free-text target fields:

- `target_topic`
- `info_text`
- `agreement_text`
- `strength_text`
- `weakness_text`

These fields are generated from validated BENNO report facts, user statements,
and ratings. They are not raw transcripts.

Derived Phase 6 target fields for `mock_visit_reports`:

| Field | Purpose |
|---|---|
| `id` | Local mock visit report identifier |
| `visit_report_number` | Human-readable mock report number used for references |
| `final_report_id` | Link back to BENNO's confirmed internal report |
| `visit_type` | `in_person`, `virtual`, or `phone` |
| `visit_report_status` | Mock eNVenta `Status` |
| `report_status` | Mock eNVenta `Berichtsstatus` |
| `account_id` | Link to the AKL-like account record |
| `account_number` | Mock AKL number |
| `account_type` | `A`, `K`, or `L` |
| `account_search_name` | Search name from the AKL-like account |
| `contact_id` | Link to the account contact, if known |
| `contact_name` | Captured or selected contact name |
| `field_sales_representative_id` | Representative from the CRM-like representative domain |
| `responsible_user_id` | CRM user responsible for follow-up handling, if needed |
| `visit_date` | Visit date |
| `visit_time` | Visit time, if relevant |
| `target_topic` | eNVenta `Ziel/Thema` text |
| `info_text` | eNVenta `Info` text |
| `agreement_text` | eNVenta `Vereinbarung` text |
| `strength_text` | eNVenta `Stärke` text |
| `weakness_text` | eNVenta `Schwäche` text |
| `next_appointment_date` | eNVenta `Termin ab`, if a follow-up appointment exists |
| `offer_reference` | Offer reference, if relevant |
| `order_reference` | Order reference, if relevant |
| `created_at` | Local mock creation timestamp |

`visit_report_status` and `report_status` should be stored as separate fields.
For the Phase 6 mock they may use the same initial status logic, but keeping
both fields prevents hiding a later eNVenta distinction.

Required target rating fields:

- `customer_satisfaction_rating`
- `technical_attractiveness_rating`
- `commercial_attractiveness_rating`
- `priority_rating`

These four fields replace the earlier six internal BENNO rating fields as the
target contract. The old fields should not be kept in parallel in the mock
eNVenta visit report target.

## Mock Accounts And Users

Phase 6 should move the target mock CRM shape toward eNVenta's AKL logic.

`mock_accounts` represent the shared AKL-like address/account domain. Leads,
customers, and suppliers are account types inside that domain. Existing
`mock_customers` and `mock_leads` are Phase 2 legacy scaffolding and should be
wrapped, replaced, or migrated toward the account model during Phase 6.

Mock account type codes:

| Code | Meaning |
|---|---|
| `A` | Address or lead-like account |
| `K` | Customer account |
| `L` | Supplier account |

Minimum mock account fields:

- `id`
- `account_number`
- `account_type`
- `search_name`
- `display_name`
- `address_text`
- `address_restriction`
- `created_at`

Contacts belong to accounts.

CRM users and field sales representatives are separate mock domains:

- `mock_crm_users` represent CRM users and responsible users. Inside sales users
  live here, and field sales users may also have CRM user records. There is no
  required link from a CRM user to a representative in the Phase 6 mock.
- `mock_field_sales_representatives` represent field sales representative master
  data. Representatives are always field sales people.

`mock_reminders` represent eNVenta-like follow-ups. They can be assigned to CRM
users or field sales representatives. BENNO's current `inside_sales_tasks`
should be treated as the legacy basis for these reminders, not as a separate
parallel concept.

Minimum mock reminder fields:

- `id`
- `visit_report_number`
- `due_date`
- `owner_type`
- `owner_id`
- `created_by_user_id`
- `message`
- `status`
- `created_at`

`owner_type` should identify whether the reminder belongs to a CRM user or to a
field sales representative.

## Inside Sales Tasks

Inside sales tasks are the Phase 2/4 legacy follow-up concept. In Phase 6 they
should be replaced or migrated into `mock_reminders` for the eNVenta-oriented
target model.

Historically, inside sales tasks captured follow-up work that should not be done
automatically by BENNO.

Canonical MVP task types:

| Task Type | Purpose |
|---|---|
| `complete_master_data` | Customer, lead, address, or contact data must be completed |
| `create_offer` | A new offer should be created |
| `clarify_details` | Business details are unclear and must be clarified |
| `follow_up_call` | A callback or follow-up is required |

Minimum fields:

- `id`
- `linked_final_report_id`
- `task_type`
- `title`
- `description`
- `detected_customer_name`
- `detected_contact_name`
- `related_customer_id`
- `status`
- `due_date`
- `created_at`

Task status values:

- `open`
- `in_review`
- `done`
- `cancelled`

## Controlled Codes

Use controlled English codes internally.

Visit type:

- `in_person`
- `virtual`
- `phone`

Reason code:

- `offer_follow_up`
- `new_demand`
- `relationship_meeting`
- `contract_discussion`
- `lead_initial_contact`
- `complaint_related`
- `other`

Report status:

- `in_progress`
- `ready_for_review`
- `inside_sales_input_required`
- `blocked`
- `confirmed`
- `submitted`
- `cancelled`

Validation status:

- `not_provided`
- `detected_unvalidated`
- `matched`
- `ambiguous`
- `unknown`
- `confirmed_new`

## Storage Rules

Normal case:

- customer and contact are validated
- required sections are complete
- user confirms final review
- final report status becomes `submitted`

New or unknown contact:

- report may be created
- no contact master data is created automatically
- inside sales task is created

New lead:

- report information may be captured
- no customer is created automatically
- inside sales task is created

Unclear master data:

- report should not be treated as normally submitted
- inside sales task is created
- status may become `inside_sales_input_required` or `blocked`

New offer needed:

- report captures the need
- offer is not created automatically
- inside sales task is created

## API Shape For The First Slice

The first implementation can use Flask routes and form or JSON endpoints. The conceptual operations are:

- log in
- load dashboard
- start report chat
- load report chat
- submit user message
- generate final review
- confirm and save report
- cancel report
- list final reports
- load final report

The central operation is user-message processing:

```text
user message -> draft update -> validation -> missing sections -> next assistant message
```

## AI Output Contract

AI output must be treated as a proposal.

The backend validates:

- whether fields are allowed
- whether codes are valid
- whether CRM references match mock data
- which sections are still missing
- whether final review is allowed
- whether saving is allowed

AI output must never directly create database records.
