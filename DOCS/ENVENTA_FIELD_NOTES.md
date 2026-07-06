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
| `Besuchsrhythmus` | Visit rhythm or cadence, if clearly stated |

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

Some of these may be written by BENNO later, especially follow-up tasks and reminder-like data. The exact behavior should be decided in Phase 6 after the final field list and expected workflow are understood.

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

