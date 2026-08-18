# BENNO Documentation Coverage

## Purpose

This document explains how the original German concept notes were migrated into the current English documentation set.

The goal was not to translate every historical statement word-for-word. Some earlier notes contain assumptions that are no longer current. The migration keeps the useful content and removes or supersedes outdated decisions.

## Current Source Of Truth

Use these documents for current implementation and product work:

| Document | Purpose |
|---|---|
| `MVP_OVERVIEW.md` | Non-technical product overview |
| `MVP_MASTER_SPEC.md` | Canonical product and MVP specification |
| `IMPLEMENTATION_ROADMAP.md` | Practical development phases |
| `CODING_STANDARDS.md` | Coding quality, naming, and architecture standards |
| `CONVERSATION_FLOW.md` | Dialog behavior, report sections, intents, correction, review |
| `DATA_MODEL.md` | Database areas, draft/report/reminder model, mock CRM structure |
| `ENVENTA_FIELD_NOTES.md` | First eNVenta visit report field observations and source classification |
| `USER_ADMIN_SETTINGS.md` | Users, roles, admin scope, language and provider settings |
| `AI_VOICE_PRIVACY.md` | Provider strategy, Langfuse observability, voice layer, local provider direction, privacy |
| `FRONTEND_UX_SPEC.md` | S:FLEX-near frontend direction, Sales/Admin UX rules, visual acceptance |
| `PHASE_10_LIVE_FUNCTIONAL_TESTS.md` | Planned opt-in live functional test harness specification for Gemini, voice sidecars, and Langfuse evidence; the runner is not implemented yet |

## Archived Source Mapping

| Archived German source | Current English coverage |
|---|---|
| `archive_de/MVP_01_Konzeptstand_Besuchsbericht_Assistent.md` | `MVP_OVERVIEW.md`, `MVP_MASTER_SPEC.md`, `CONVERSATION_FLOW.md`, `DATA_MODEL.md` |
| `archive_de/MVP_02_Datenmodell.md` | `DATA_MODEL.md`, `MVP_MASTER_SPEC.md` |
| `archive_de/MVP_02_Interviewstand_Voice_Architektur_und_Login.md` | `MVP_MASTER_SPEC.md`, `AI_VOICE_PRIVACY.md`, `USER_ADMIN_SETTINGS.md` |
| `archive_de/MVP_03_Testkandidaten_STT_TTS_LLM.md` | `AI_VOICE_PRIVACY.md` |
| `archive_de/MVP_04_Interviewstand_Provider_Datenschutz_und_Lokale_LLMs.md` | `AI_VOICE_PRIVACY.md`, `MVP_MASTER_SPEC.md` |
| `archive_de/MVP_05_Berichtsentwurf_und_Conversation_State.md` | `CONVERSATION_FLOW.md`, `DATA_MODEL.md` |
| `archive_de/MVP_06_Admin_User_Settings.md` | `USER_ADMIN_SETTINGS.md` |
| `archive_de/MVP_07_Vertical_Slice_und_Tech_Stack.md` | `IMPLEMENTATION_ROADMAP.md`, `MVP_MASTER_SPEC.md` |

## Superseded Or Cleaned-Up Topics

The following topics appeared in earlier notes but are not current implementation guidance:

- Gemini is the first real AI provider for the current MVP baseline.
- FastAPI and React are not the current first-slice stack.
- Sales users do not choose the AI provider.
- SQLite is sufficient for the current local mock backend; Postgres remains a
  later MVP persistence step behind the CRM/eNVenta gateway boundary.
- The first implementation started with text. Phase 9 now adds a first
  turn-based voice layer over the same report workflow.
- Local AI is a later privacy-oriented provider step after the Gemini workflow is stable.
- Langfuse is an optional development observability layer, not a business workflow dependency.
- The first screenshot-derived eNVenta visit report mapping is documented and
  used by the Mock-eNVenta target; the real eNVenta API contract remains a
  later integration topic.
- Seeded users remain available for local testing; Phase 8 adds local setup and
  reset links without email delivery.

## Documentation Rule Going Forward

Active project documentation should be written in English.

German may still appear in:

- archived historical notes
- user-facing German UI copy
- demo conversation examples where German is intentionally tested
- source material received from external stakeholders
