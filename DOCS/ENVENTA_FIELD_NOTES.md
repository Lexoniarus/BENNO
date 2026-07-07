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
| `Berichtsstatus` | `report_status` | Same business meaning as `Status` for the current MVP. Keep one BENNO source of truth and map both eNVenta labels later if required. |
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
| AKL | `accounts` | Shared address/customer/supplier/lead domain. Contains leads, customers, and suppliers. |
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

