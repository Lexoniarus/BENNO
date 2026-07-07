# eNVenta Visit Report Field Notes

## Purpose

This document captures the first concrete field observations from the eNVenta visit report screenshots provided by Bernd Rombach.

It is not the final API contract and not the final writeback mapping. Its purpose is to prevent visible eNVenta screen fields from being treated as BENNO dialog questions by mistake.

## Core Rule

Not every visible eNVenta field should become a BENNO question.

For Phase 6, each field must be classified by its source:

1. user-provided report content
2. AI-assisted derivation from the report conversation
3. CRM/eNVenta master data
4. BENNO login or user context
5. eNVenta system metadata

BENNO should only ask the field sales user for information that cannot be supplied reliably from another source.

## Field Source Classification

## Phase 6 Clarifications From User Discussion

These decisions refine the first screenshot observations. German labels remain
source labels from the eNVenta UI only. BENNO code, functions, variables,
database columns, API fields, and internal contracts must use English names.

### Visit Report Fields

| eNVenta label | BENNO field name | Source or behavior |
|---|---|---|
| `Besuchsart` | `visit_type` | BENNO should ask or derive this. Allowed MVP values are `in_person`, `virtual`, and `phone`. |
| `Status` | `visit_report_status` | Processing state of the visit report. MVP values: `open`, `in_progress`, `closed`. |
| `Berichtsstatus` | `report_status` | Separate stored state field. It may follow the same initial logic as `Status`, but BENNO keeps both fields because eNVenta may distinguish them later. |
| `Termin ab` | `next_appointment_date` | Next appointment or follow-up date. BENNO may ask for it when a next appointment is mentioned or needed. |
| `Besuchsrhythmus` | - | Out of scope for the MVP and should not be asked or mapped yet. |
| `Zufriedenheit` | `customer_satisfaction_rating` | Rating from 1 to 10. |
| `Techn. Attrakt.` | `technical_attractiveness_rating` | Rating from 1 to 10. |
| `Kaufm. Attrakt.` | `commercial_attractiveness_rating` | Rating from 1 to 10. |
| `Priorität` | `priority_rating` | Rating from 1 to 10. |

### Related eNVenta Data Areas

The visible eNVenta areas imply several related data tables or lookup domains.
BENNO should represent them with English names in the mock database and the
placeholder integration contract.

| eNVenta concept | BENNO name | Meaning |
|---|---|---|
| AKL | `accounts` | Shared address/customer/supplier/lead domain. Contains address/lead-like records, customers, and suppliers. Uses account type codes `A`, `K`, and `L`. |
| Ansprechpartner | `contacts` | Contact persons linked to an AKL/account record. |
| Angebote | `offers` | Commercial offer records. |
| Aufträge | `orders` | Order records. Offers and orders may appear in one eNVenta table but must remain distinct BENNO document types. |
| Wiedervorlagen | `reminders` | Follow-up reminders or callbacks. |
| Außendienstler / Vertreter | `field_sales_users` | Field sales representatives. Usually mapped from BENNO users or eNVenta users. |
| Sachbearbeiter | `responsible_users` | Responsible back-office or inside-sales users. |

### Phase 6 Mapping Direction

For the placeholder contract, BENNO should treat the eNVenta visit report as a
structured handoff target with these groups:

- report content entered or spoken by the sales user
- ratings and visit type derived or confirmed through the conversation
- account and contact lookup data from AKL/contact tables
- offer and order references as separate document types
- reminders or inside-sales tasks for follow-up work
- eNVenta-managed metadata that BENNO does not ask for

The MVP should not implement `visit_rhythm`, supplier-specific behavior, or a
full eNVenta screen clone.

### Phase 6 Target Model Decisions

`final_reports` remain BENNO's internal confirmed report record. They preserve
the reviewed BENNO result.

`mock_visit_reports` are the mock CRM/eNVenta write target. They represent the
visit report shape BENNO would later write to eNVenta. This target should
contain the eNVenta-oriented free-text fields:

- `target_topic` for `Ziel/Thema`
- `info_text` for `Info`
- `agreement_text` for `Vereinbarung`
- `strength_text` for `Stärke`
- `weakness_text` for `Schwäche`

These texts are derived from the conversation, validated report facts, and
field-sales ratings. They should not be a raw transcript and must not invent
facts outside the reviewed BENNO report.

The mock visit report target fields can be derived from the screenshots and
current MVP decisions. Since BENNO is not connected to eNVenta yet, this is a
local placeholder contract, not a final eNVenta API schema.

`Stärke` and `Schwäche` should be derived from the conversation where possible.
If the value is unclear, BENNO may ask explicit follow-up questions. They should
not be invented silently.

The existing Phase 2 mock customer and lead tables are legacy scaffolding for
Phase 6. The Phase 6 target model should represent the eNVenta AKL logic as
`accounts`, where leads, customers, and suppliers share one address/account
domain. Contacts are linked to these accounts.

AKL account type codes for the mock:

| Code | Meaning |
|---|---|
| `A` | Address or lead-like account |
| `K` | Customer account |
| `L` | Supplier account |

`inside_sales_tasks` should become the basis for eNVenta-like
`reminders`/`follow_ups`. The task/reminder target may point to either inside
sales users or field sales users.

CRM users and field sales representatives are separate eNVenta-style domains:

- `crm_users` / `responsible_users` represent users in the CRM. This includes
  inside sales users and may also include field sales users.
- `field_sales_representatives` represent the sales representative master data.
  Representatives are always field sales people.

There is no required relation between CRM users and field sales representatives
in the Phase 6 mock. A real person may exist in both domains, but BENNO should
model them as separate CRM concepts.

Minimum reminder target fields:

- `due_date`
- `owner_type`
- `owner_id`
- `created_by_user_id`
- `message`
- `visit_report_number`

The reminder reference should point to the mock visit report by report number.

### Phase 6 Conversation Collection Strategy

BENNO should collect the eNVenta target fields through a guided conversation,
not through a copied eNVenta form.

The backend defines the required field checklist. Gemini compares each free
German user message against that checklist and proposes which target fields are
already covered. BENNO then validates the proposal and asks only for missing or
unclear information.

The conversation should use these broad blocks:

| Block | Purpose | Target fields |
|---|---|---|
| Visit context | Identify account or lead, contact or participants, and visit type. | `account_id` / `account_name`, `contact_id` / `contact_name`, `participants`, `visit_type` |
| Goal or topic | Capture the reason, goal, or main subject of the visit. | `target_topic` / `visit_topic` |
| Discussion content | Capture what was discussed in free form. | `info_text` / `summary`, optional `strength_text`, optional `weakness_text` |
| Agreement and next step | Capture decisions, next actions, ownership, and follow-up dates. | `agreement_text`, `outcome`, `next_action`, `next_appointment_date`, `reminders` |
| Document references | Capture offer or order references only when mentioned or relevant. | `offer_reference`, `order_reference` |
| eNVenta ratings | Capture the four eNVenta ratings together. | `customer_satisfaction_rating`, `technical_attractiveness_rating`, `commercial_attractiveness_rating`, `priority_rating` |

The LLM may derive `strength_text` and `weakness_text` from the conversation and
ratings, but BENNO should not invent facts. If a derived value is unclear, BENNO
asks a short follow-up question instead of silently filling the field.

The final review does not need to be LLM-driven. BENNO can show each new
eNVenta-oriented entry and ask the user whether it should be written that way.
Only confirmed entries are saved into the mock visit report target.

## MVP Working Mapping Table

This table is the current Phase 6 working contract. It is derived from the
screenshots and user clarification, not from a real eNVenta API schema.

| eNVenta label | BENNO field | Source | Required for MVP | Ask user? | Writeback relevance |
|---|---|---|---|---|---|
| `Besuchsart` | `visit_type` | User input or AI derivation | Yes | Ask if missing | Yes |
| `AKL-Nummer` | `account_id` | Account/AKL lookup | Yes | Search/select, do not ask as raw ID | Yes |
| `Suchname` | `account_search_name` | Account/AKL lookup | Yes | Search/select, do not ask as separate field | Yes |
| `Ansprechpartner` | `contact_id` / `contact_name` | Contact lookup or user input | Yes | Ask if unclear or new | Yes |
| `Anschrift` | `account_address` | Account/AKL lookup | No | No | Likely read-only or derived |
| `Adressrestriktion` | `address_restriction` | Account/AKL metadata | No | No | Likely read-only |
| `Vertreter` | `field_sales_user_id` | BENNO login or user mapping | Yes | No | Yes |
| `Sachbearbeiter` | `responsible_user_id` | Responsible user lookup/config | Conditional | Ask/select only for follow-up ownership | Yes for tasks/reminders |
| `Besuchsdatum` | `visit_date` | Default/user correction | Yes | Only if not today or needs correction | Yes |
| `Besuchszeit` | `visit_time` | Default/user correction | No | Only if relevant | Optional |
| `Status` | `visit_report_status` | BENNO state | Yes | No | Yes |
| `Berichtsstatus` | `report_status` | BENNO state | Yes | No | Yes |
| `Ziel/Thema` | `visit_topic` | User input or AI derivation | Yes | Ask if missing | Yes |
| `Info` | `summary` | User input or AI derivation | Yes | Ask if missing | Yes |
| `Vereinbarung` | `outcome` / `next_action` | User input or AI derivation | Yes | Ask if missing | Yes |
| `Stärke` | `strengths` | User input or AI derivation | No | Optional, do not block report | Optional |
| `Schwäche` | `weaknesses` | User input or AI derivation | No | Optional, do not block report | Optional |
| `Zufriedenheit` | `customer_satisfaction_rating` | User input or AI derivation | Yes | Ask if missing | Yes |
| `Techn. Attrakt.` | `technical_attractiveness_rating` | User input or AI derivation | Yes | Ask if missing | Yes |
| `Kaufm. Attrakt.` | `commercial_attractiveness_rating` | User input or AI derivation | Yes | Ask if missing | Yes |
| `Priorität` | `priority_rating` | User input or AI derivation | Yes | Ask if missing | Yes |
| `Termin ab` | `next_appointment_date` | User input or AI derivation | Conditional | Ask if follow-up/appointment exists | Yes |
| `Besuchsrhythmus` | - | Out of scope | No | No | No |
| `Angebote` | `offer_reference` / `offer_id` | Offer lookup or user mention | Conditional | Ask if mentioned or relevant | Yes |
| `Aufträge` | `order_reference` / `order_id` | Order lookup or user mention | Conditional | Ask if mentioned or relevant | Yes |
| `Wiedervorlagen` | `reminders` | Generated from next action or user input | Conditional | Ask if follow-up needs scheduling | Yes |
| `Teilnehmer` / `Name` | `participants` | User input/contact lookup | Yes | Ask if missing | Yes |
| `Teilnehmer` / `Bemerkung` | `participant_notes` | User input or AI derivation | No | Optional | Optional |
| `Projekte` | `project_reference` | Project lookup/user mention | No | Optional | Optional |
| `Erfassung` | `created_metadata` | eNVenta system metadata | No | No | No, read-only later |
| `Änderung` | `updated_metadata` | eNVenta system metadata | No | No | No, read-only later |

## MVP Required Fields

BENNO should treat a visit report as complete for the Phase 6 MVP only when
these fields are available or explicitly marked not applicable:

The four eNVenta screenshot ratings are the authoritative Phase 6 rating
fields. The earlier six BENNO ratings from the Phase 4/5 text loop are legacy
working fields and should be replaced or explicitly mapped during the Phase 6
implementation.

The mock CRM/eNVenta visit report write target should contain these four
ratings as its only rating fields. They are not an additional layer on top of
the old BENNO rating set.

| BENNO field | Requirement |
|---|---|
| `visit_type` | Required. Must be one of `in_person`, `virtual`, or `phone`. |
| `account_id` or `account_name` | Required. Existing account lookup, existing lead lookup, or new lead text is acceptable for the MVP. |
| `contact_id` or `contact_name` | Required. Existing contact, new contact text, or participant name is acceptable. |
| `field_sales_user_id` | Required from BENNO login/user mapping. |
| `visit_date` | Required. Default may be today's date, but it must be stored. |
| `visit_report_status` / `report_status` | Required from BENNO workflow state. |
| `visit_topic` | Required. Captures `Ziel/Thema`. |
| `summary` | Required. Captures `Info`. |
| `outcome` | Required. Captures the result or agreement. |
| `next_action` | Required. Captures the next step or explicit statement that no next action exists. |
| `customer_satisfaction_rating` | Required, 1 to 10 or explicit "not assessable yet" reason. |
| `technical_attractiveness_rating` | Required, 1 to 10 or explicit "not assessable yet" reason. |
| `commercial_attractiveness_rating` | Required, 1 to 10 or explicit "not assessable yet" reason. |
| `priority_rating` | Required, 1 to 10 or explicit "not assessable yet" reason. |

Conditional required fields:

- `offer_reference` / `offer_id` is required only when an offer is mentioned or the visit is explicitly about an offer. Otherwise it may be `not_applicable`.
- `order_reference` / `order_id` is required only when an order is mentioned or the visit is explicitly about an order. Otherwise it may be `not_applicable`.
- `next_appointment_date` is required only when a concrete next appointment, reminder, or callback date is agreed.
- `responsible_user_id` is required only when a reminder or inside-sales task needs a responsible owner.

Optional MVP fields:

- `visit_time`
- `duration`
- `strengths`
- `weaknesses`
- `participant_notes`
- `project_reference`
- `account_address`
- `address_restriction`

### User-Provided Report Content

These fields are likely report content and may be collected through BENNO's guided dialog:

| eNVenta label | Current BENNO interpretation |
|---|---|
| `Ziel/Thema` | Visit goal, topic, or main subject |
| `Info` | General visit notes or summary information |
| `Vereinbarung` | Agreement, commitment, or decided next step |
| `Stärke` | Positive customer/account factor |
| `Schwäche` | Risk, weakness, objection, or negative factor |
| `Teilnehmer` / `Name` | Meeting participants |
| `Teilnehmer` / `Bemerkung` | Participant note or role |
| `Thema` | Follow-up or task topic |
| `Übersicht` | Follow-up or task overview |
| `Nachricht` | Follow-up message or reminder text |

These fields should be candidates for extraction from natural German user input.

### AI-Assisted Derived Values

These fields may be suggested by AI but should remain reviewable or correctable:

| eNVenta label | Current BENNO interpretation |
|---|---|
| `Zufriedenheit` | Customer satisfaction rating |
| `Techn. Attrakt.` | Technical attractiveness |
| `Kaufm. Attrakt.` | Commercial attractiveness |
| `Priorität` | Priority |
| `Besuchsart` | Visit type, if clearly stated |
| `Dauer` | Duration, if clearly stated |

BENNO may propose these values, but the backend remains responsible for allowed values, validation, and final status.

### CRM/eNVenta Master Data

These fields should normally come from the selected customer, contact, project, offer, order, or address data:

| eNVenta label | Expected source |
|---|---|
| `AKL-Nummer` | eNVenta customer/address/lead record |
| `Suchname` | eNVenta customer/address/lead record |
| `Ansprechpartner` | eNVenta contact record |
| `Anschrift` | eNVenta address/master data |
| `Projekte` | eNVenta project reference |
| `Adressrestriktion` | eNVenta customer/address restriction metadata |

BENNO should not ask the user to manually type these values if they can be selected, searched, or matched through CRM/eNVenta context.

### Login Or User Context

These fields should normally come from the logged-in BENNO user, the mapped sales representative, or the responsible CRM/eNVenta user:

| eNVenta label | Expected source |
|---|---|
| `Vertreter` | BENNO sales user or mapped eNVenta sales representative |
| `Sachbearbeiter` | Responsible user from BENNO or eNVenta context |

These are not normal report-content questions. They may become admin/configuration mapping topics.

### eNVenta System Metadata

These fields are controlled by eNVenta itself and must not be collected by BENNO:

| eNVenta label | Meaning | BENNO behavior |
|---|---|---|
| `Erfassung` | Creation timestamp or creation metadata | Do not ask, do not write |
| `Änderung` | Last modification timestamp or modification metadata | Do not ask, do not write |

Later, if a real integration returns these fields, BENNO may display or store them as read-only audit metadata. They are not report inputs.

### Workflow Or Record State Fields

These fields likely belong to record lifecycle, planning, or follow-up workflow:

| eNVenta label | Current assumption |
|---|---|
| `Besuch` | Visit report record identifier or reference |
| `Plan` | Planning reference |
| `Status` | eNVenta visit report status |
| `Berichtsstatus` | Report workflow status |
| `Termin ab` | Follow-up or appointment date |
| `Besuchsdatum` | Visit date |
| `Besuchszeit` | Visit time |
| `Vorgänge/Aufgaben` | Related tasks or follow-up activities |
| `WV-Historie` | Follow-up history |
| `Call-Betreff` | Task or call subject |
| `Kategorie` | Task category |
| `Erfasser` | Creator/responsible metadata for a task entry |
| `Eigner` | Owner of a follow-up or task entry |

The Phase 6 working mapping for these workflow fields is:

- `Status` -> `visit_report_status`, with MVP values `open`, `in_progress`,
  and `closed`.
- `Berichtsstatus` -> `report_status`, treated as the same business state as
  `Status` for the MVP.
- `Termin ab` -> `next_appointment_date`.
- `Besuch` -> `visit_report_id`, likely assigned by eNVenta later.
- `Plan` -> `plan_reference`, not a normal MVP dialog question.
- `Besuchsdatum` -> `visit_date`.
- `Besuchszeit` -> `visit_time`.
- `Vorgänge/Aufgaben` -> `related_documents` and `tasks`.
- `WV-Historie` -> `reminder_history`.
- `Call-Betreff` -> `task_subject`.
- `Kategorie` -> `task_category`.
- `Erfasser` -> `task_created_by`.
- `Eigner` -> `task_owner`.

Some of these may be written by BENNO later, especially follow-up tasks and
reminder-like data. Phase 6 should define the placeholder behavior before any
real eNVenta writeback is attempted.

## Current Phase-6 Implication

Phase 6 should not simply recreate the eNVenta screen as a BENNO form.

Instead, it should produce:

- a field source map
- a list of required fields BENNO must ensure
- a list of fields BENNO may derive
- a list of CRM/eNVenta lookup fields
- a list of read-only eNVenta system fields
- a placeholder save contract for visit reports
- a placeholder contract for reminders or inside sales follow-up tasks

## Explicit Non-Goals

For the current MVP direction, BENNO should not:

- ask for `Erfassung`
- ask for `Änderung`
- invent eNVenta record IDs
- invent final eNVenta status values
- treat all visible screen fields as required user input
- write directly to eNVenta before the placeholder contract is defined

