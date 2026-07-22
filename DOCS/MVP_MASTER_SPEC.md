# MVP Master Specification: Voice-Guided CRM Visit Report Assistant

## 1. Purpose

This document is the canonical MVP specification for the project.

It describes the current project status and the agreed MVP direction.

The goal of the MVP is to prove that a B2B field sales representative can create a structured CRM visit report through a guided dialog, with the application extracting information, asking for missing details, generating a review, and only saving the final report after explicit user confirmation.

## 2. Product Summary

The application is a visit report assistant for B2B field sales representatives.

It is not a CRM system. It is a capture, structuring, validation, and handover layer between the field sales user and a CRM or ERP system.

The user starts a new visit report after a customer meeting and describes the meeting in natural language. The assistant extracts relevant information, checks it against a placeholder CRM/ERP data source, asks targeted follow-up questions, handles corrections, prepares a structured report draft, and generates a final visit report.

The final report is displayed as a block-by-block review. It is only saved or submitted after explicit user confirmation.

## 3. Core Problem

Field sales visit reports are often written too late, too briefly, or inconsistently. Mobile CRM forms are inconvenient after meetings, and important details are easily lost.

The MVP addresses this by lowering the friction between fresh field sales knowledge and structured CRM documentation.

The assistant should help with:

- capturing information shortly after the customer meeting
- reducing manual typing
- creating consistent reports
- identifying missing mandatory information
- validating customer, contact, offer, and order references
- documenting follow-up actions
- preparing eNVenta-like reminders when follow-up work is required

## 4. MVP Scope

The MVP focuses on the standard B2B sales visit report.

The first vertical slice is text-based. Voice input and voice output remain part of the target vision. After the stable text workflow, Phase 9 adds voice as a layer over the same workflow.

The core flow is:

```text
login -> start chat -> free text input -> structured draft -> guided questions -> block review -> confirmation -> final report
```

The MVP includes:

- user login
- role-based routing
- sales user area
- admin area
- starting a new visit report chat
- continuing open chats
- text-based chat interaction
- report draft state
- report section status tracking
- intent detection
- confidence tracking
- target section detection
- LLM-assisted extraction and report writing
- guided questions for missing or unclear information
- correction handling
- placeholder CRM/ERP validation
- block-by-block final review
- explicit final confirmation
- local persistence of final reports
- eNVenta-like reminders for selected follow-up cases
- backend debug logging

Current scope boundaries:

- The first vertical slice is text-based.
- STT and TTS are added after the text-based Gemini workflow can create and save a stable report. This condition is now met by the Phase 6/8 baseline, so voice is the next planned implementation phase.
- The MVP uses a local placeholder CRM/ERP service before any real eNVenta integration.
- The first screenshot-based eNVenta visit report field mapping is documented and used for the Phase 6 mock target.
- The admin area stays simple in the first slice.
- The MVP uses a pragmatic login and user setup flow, not a full production identity management system.

## 5. Current Vertical Slice

Vertical Slice 1 proves the core application behavior with text only.

The slice should demonstrate that a sales representative can:

1. log in
2. open the sales dashboard
3. start a new visit report chat
4. enter a free-form description of a customer visit
5. receive targeted follow-up questions
6. correct previous information at any point
7. build a structured report draft
8. review the report block by block
9. explicitly confirm the report
10. save the final report locally

The first slice intentionally excluded STT and TTS so the core dialog, draft, validation, and review workflow could be stabilized before audio is added.

## 6. Target Voice Vision

The long-term product vision is hands-free use after the report chat has been started.

The intended scenario is:

1. The field sales representative leaves a customer meeting.
2. The user opens the web app and starts a new visit report.
3. The phone is placed in a car holder.
4. The assistant asks questions via text-to-speech.
5. The user answers via speech.
6. Speech-to-text converts the answer into a text turn.
7. The same dialog workflow processes the text turn.
8. The final report is read aloud and shown on screen.
9. The user confirms or corrects the report by voice.

The voice layer must not replace the text-based core. Speech-to-text only creates text input. Text-to-speech only reads text output.

## 7. Technical Stack For The First Slice

The current working assumption for Vertical Slice 1 is:

```text
Backend / web app: Flask
Templates: Jinja
Frontend interaction: Vanilla JavaScript
Styling: responsive HTML/CSS
Database: SQLite
First LLM provider: Gemini API
Later privacy-focused provider: local OpenAI-compatible API, for example LM Studio
CRM/ERP: local placeholder service/API
```

This stack is intentionally pragmatic:

- Flask fits a Python-centered MVP.
- Jinja and Vanilla JavaScript are sufficient for the first chat UI.
- SQLite is sufficient for the current local mock backend. A later MVP step may
  move persistence to Postgres behind the same CRM/eNVenta gateway boundary.
- The application remains a responsive web app, not a native mobile app.

## 8. Architecture

The frontend only talks to the application backend.

```text
Browser
  -> Flask Web App
      -> Auth / User Service
      -> Sales Routes
      -> Admin Routes
      -> Chat Service
      -> Report Draft Service
      -> AI Provider Service
      -> Placeholder CRM/ERP Service
      -> SQLite
```

The backend is the central application layer. It owns:

- authentication and session handling
- user context
- role checks
- dialog state
- report draft state
- validation logic
- mandatory field logic
- status transitions
- AI provider calls
- placeholder CRM/ERP access
- final persistence
- mock visit report and reminder creation

The LLM supports interpretation and formulation. The application code remains responsible for validation and decisions.

Guiding principle:

```text
The LLM interprets and writes. The application validates and decides.
```

## 9. Roles

The MVP has two roles.

```python
class UserRole(str, Enum):
    SALES_REP = "sales_rep"
    ADMIN = "admin"
```

Sales representatives can:

- create visit report chats
- continue open chats
- view their own completed reports
- change their own language setting

Admins can:

- view the user list
- create and edit users
- set user roles
- set user language
- configure the global AI provider
- configure per-user AI provider overrides
- see simple technical status counts
- trigger setup or password reset flows

Admins must not use the admin view as a content surveillance interface. The admin status view should not expose full chat transcripts, full report texts, or detailed field sales conversation content.

## 10. Language Handling

The MVP supports German and English.

```python
class SessionLanguage(str, Enum):
    DE = "de"
    EN = "en"
```

Rules:

- The global default language is German.
- Each user can have a preferred language.
- New chats copy the current user language into `session_language`.
- Running chats keep the language they started with.
- UI text, assistant questions, summaries, confirmations, STT expectations, and TTS output follow the session language.

For the first vertical slice, the session language is the controlling language.

## 11. AI Provider Strategy

The first vertical slice uses Gemini as the initial real LLM provider.

After the Gemini-based workflow runs smoothly, the project should move toward a local provider. This local direction is primarily motivated by privacy and data protection considerations, not by a requirement to support many external providers.

The provider architecture should remain exchangeable. The planned provider options are:

```python
class AiProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    LOCAL = "local"
```

Rules:

- Normal sales users do not choose the AI provider.
- The global default provider is configured by an admin.
- Optional per-user provider overrides can be configured by an admin.
- Concrete model settings are not normal user settings.
- The local provider should be integrated later through an OpenAI-compatible local API, for example LM Studio.

Current provider sequence:

1. Build and stabilize the workflow with Gemini.
2. Keep the provider abstraction compatible with local OpenAI-style APIs.
3. Move to a local provider once the workflow is stable.

## 12. Local Provider Direction

The project has a local-first target direction, but local LLMs are not the first implementation path.

The intended order is:

1. Stabilize the dialog workflow with Gemini.
2. Keep the provider abstraction compatible with local OpenAI-style APIs.
3. Add LM Studio or another local OpenAI-compatible runtime.
4. Evaluate local model quality against the same workflow.

If local models are used, they may require tighter application-side control:

- stricter JSON schemas
- smaller model tasks
- more explicit prompts
- stronger validation
- possible separation between chat formulation and structured extraction

## 13. STT And TTS Strategy

Speech-to-text and text-to-speech are layers over the text workflow.

The next implementation phase adds the first practical voice layer.

The frontend records microphone audio and plays generated audio. The backend coordinates transcription and speech synthesis.

Browser microphone access is used for capture. BENNO should not rely on
browser-native speech recognition as the primary MVP path because support and
behavior vary between browsers. Instead, recorded audio should be sent to a
backend STT boundary, and the resulting transcript should enter the existing
text report loop.

The current STT integration target is a local Speaches Docker sidecar. Speaches
keeps STT outside the BENNO application process while still allowing local,
OpenAI-compatible speech API calls. Its streaming support is relevant for later
hands-free experiments, but Phase 9 may start with file/blob transcription.

The current TTS integration target is the local Docker-based Kokoro/Martin
service available in the development environment. Speaches TTS can be evaluated
as a secondary comparison path.

Initial test candidates from earlier research:

- STT first candidate: browser microphone capture plus local Speaches Docker
  with a German-capable Whisper/faster-whisper model
- STT model candidate: `primeline/whisper-large-v3-turbo-german`, if compatible
  with the selected Speaches/faster-whisper setup
- STT fallback: `primeline/whisper-tiny-german`
- STT performance path: GGML / whisper.cpp / faster-whisper
- TTS first candidate: local Kokoro/Martin Docker service using `Godelaune/Kokoro-82M-ONNX-German-Martin`
- TTS comparison path: Speaches TTS
- TTS fallback: Thorsten / Piper voices

These model choices are candidates, not final implementation commitments.

## 14. Report Sections

The report draft is organized into report sections.

```python
class ReportSection(str, Enum):
    CUSTOMER_CONTEXT = "customer_context"
    VISIT_TYPE = "visit_type"
    VISIT_DATE = "visit_date"
    CONTACTS = "contacts"
    VISIT_REASON = "visit_reason"
    SUMMARY = "summary"
    OUTCOME = "outcome"
    NEXT_ACTION = "next_action"
    NEXT_APPOINTMENT_DATE = "next_appointment_date"
    OFFER_REFERENCE = "offer_reference"
    ORDER_REFERENCE = "order_reference"
    STRENGTHS = "strengths"
    WEAKNESSES = "weaknesses"
    RATINGS = "ratings"
    REMINDERS = "reminders"
    FINAL_REPORT = "final_report"
    USER_CONFIRMATION = "user_confirmation"
```

Section meanings:

| Section | Meaning |
|---|---|
| `customer_context` | Existing customer, existing lead, new lead, new address, or unclear context |
| `visit_type` | In-person, virtual, or phone visit |
| `visit_date` | Visit date |
| `contacts` | Contact persons or meeting participants |
| `visit_reason` | Goal, topic, or reason for the visit |
| `summary` | eNVenta `Info` text or main meeting summary |
| `outcome` | eNVenta `Vereinbarung`, result, or meeting outcome |
| `next_action` | Next step, follow-up, or follow-up date |
| `next_appointment_date` | Concrete follow-up appointment or reminder date, if relevant |
| `offer_reference` | Offer reference, if relevant |
| `order_reference` | Order reference, if relevant |
| `strengths` | eNVenta `Stärke`, if known or derivable |
| `weaknesses` | eNVenta `Schwäche`, if known or derivable |
| `ratings` | Four eNVenta rating values and explanations |
| `reminders` | eNVenta-like follow-up reminders, if relevant |
| `final_report` | Written final visit report |
| `user_confirmation` | Explicit final confirmation |

Offer and order references must remain separate. An offer is a pre-sales object. An order is an existing business transaction or fulfillment-related object.

## 15. Section Status

Each report section has a status.

```python
class SectionStatus(str, Enum):
    OPEN = "open"
    DETECTED = "detected"
    UNCLEAR = "unclear"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    NOT_APPLICABLE = "not_applicable"
```

Status meanings:

| Status | Meaning |
|---|---|
| `open` | No usable content yet |
| `detected` | Content was detected but not fully confirmed |
| `unclear` | The system is unsure or found a conflict |
| `confirmed` | Content was confirmed or accepted |
| `corrected` | The user corrected the content |
| `not_applicable` | The section is not relevant for this report |

## 16. User Intents

Each user input is classified as an intent.

```python
class UserIntent(str, Enum):
    ANSWER = "answer"
    CORRECTION = "correction"
    ADDITIONAL_INFO = "additional_info"
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"
    REPEAT = "repeat"
    CANCEL = "cancel"
    UNKNOWN = "unknown"
```

Corrections always take priority over the current question. If the assistant asks about the next action and the user corrects the contact person instead, the correction is processed first. The dialog then returns to the next open or unclear section.

## 17. Intent Confidence And Target Sections

Each intent detection should include:

- `intent`
- `intent_confidence`
- `target_sections`

The confidence score is an internal estimate, not a mathematically reliable probability.

Suggested handling:

| Score | Behavior |
|---|---|
| `>= 0.75` | Process directly |
| `0.45` to `0.74` | Process carefully or ask for confirmation |
| `< 0.45` | Ask a clarification question |

Target sections allow one user message to affect multiple parts of the report.

## 18. Customer And Lead Context

The `customer_context` section is mandatory.

It follows the business idea of distinguishing existing customers, existing leads or addresses, new leads, and unclear cases.

```python
class CustomerContextType(str, Enum):
    EXISTING_CUSTOMER = "existing_customer"
    EXISTING_LEAD = "existing_lead"
    NEW_LEAD = "new_lead"
    UNCLEAR = "unclear"
```

The application must not automatically create customers, leads, addresses, or contacts.

If a new lead, address, or contact is detected, the report can capture the information. Follow-up or master-data work should become reviewable reminder or CRM handoff work, not an automatic master-data write.

## 19. Ratings

The `ratings` section is mandatory.

Phase 6 uses the four eNVenta screenshot ratings as the authoritative MVP target. Each rating is from 1 to 10, or can be explicitly marked as not assessable yet with a short reason.

| Rating | Meaning |
|---|---|
| Customer satisfaction | eNVenta `Zufriedenheit`; how satisfied the customer appears |
| Technical attractiveness | eNVenta `Techn. Attrakt.`; how technically attractive the case is |
| Commercial attractiveness | eNVenta `Kaufm. Attrakt.`; how commercially attractive the case is |
| Priority | eNVenta `Priorität`; how much attention the case requires |

The assistant should infer these four ratings from the conversation where possible, provide short explanations, and ask the user to confirm or correct them.

The final report text should be consistent with the ratings, but it does not need to mechanically repeat all numeric values.

## 20. Report Status

The report status values are:

```python
class ReportStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    INSIDE_SALES_INPUT_REQUIRED = "inside_sales_input_required"
    BLOCKED = "blocked"
    CONFIRMED = "confirmed"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"
```

Status meanings:

| Status | Meaning |
|---|---|
| `in_progress` | The chat is active or open |
| `ready_for_review` | Required content is available and ready for final review |
| `inside_sales_input_required` | Field sales input is complete, but inside sales must complete or check something |
| `blocked` | The report cannot currently be completed in a meaningful way |
| `confirmed` | The user has explicitly confirmed the final review |
| `submitted` | The report was saved or handed over to the placeholder CRM/ERP |
| `cancelled` | The report was cancelled |

`inside_sales_input_required` is not an error. It means the report was captured but cannot be considered fully complete in the CRM/ERP process until inside sales has finished a related task.

## 21. eNVenta-Like Reminders

Phase 6 uses `mock_reminders` as the eNVenta-oriented follow-up target. Legacy inside sales task types may remain in code or older tests as scaffolding, but they are not the Phase 6 write target.

Reminder ownership can point to a CRM user or to a field sales representative.

Minimum reminder fields:

- `visit_report_number`
- `due_date`
- `owner_type`
- `owner_id`
- `created_by_user_id`
- `message`
- `status`

## 22. Placeholder CRM/ERP

The MVP uses an internal placeholder CRM/eNVenta gateway backed by local mock tables.

The relevant external CRM/ERP product context is eNVenta by the eNVenta Group: https://www.enventa-group.com/.

It simulates:

- AKL-like account search
- contact lookup
- offer reference lookup
- order reference lookup
- CRM user and field sales representative lookup
- mock visit report save
- mock reminder creation

The placeholder CRM/eNVenta gateway is a counterpart, not the application core.

The frontend must never talk directly to CRM/ERP systems. All future CRM/ERP access goes through the application backend.

Target architecture:

```text
Mobile Web App
  -> Application Backend
      -> CRM/ERP Connector
          -> CRM/ERP
```

## 23. Data Areas

The first vertical slice needs these data areas:

- users
- global settings
- user settings
- chats
- chat turns
- report templates
- report drafts
- final reports
- mock accounts
- mock contacts
- mock offers
- mock orders
- mock CRM users
- mock field sales representatives
- mock visit reports
- mock reminders

Legacy Phase 2 mock customer, lead, and inside-sales-task tables may remain during the transition, but the Phase 6 target contract uses accounts, mock visit reports, and reminders.

This list is still not a final eNVenta API schema. It defines the local mock storage areas needed to prove the MVP flow.

## 24. Authentication And Registration

The MVP needs real login behavior, but not a full production identity system.

Required:

- login with email and password
- password hashing
- active/inactive users
- sales and admin roles
- user-specific language setting
- optional external sales representative ID
- optional AI provider override

Registration target flow:

```text
Admin creates user -> system generates setup token/link -> user sets password
```

For the MVP, the setup link may be shown directly in the admin UI. Real email delivery is not required for the first slice.

Password reset can follow the same token/link pattern.

## 25. Final Review Rules

The final review must be block-based and human-readable.

It should include:

- customer or lead context
- contact persons or participants
- visit reason
- meeting summary
- outcome or agreement
- next action and follow-up
- offer reference, if relevant
- order reference, if relevant
- ratings with short explanations
- final written report
- eNVenta-like reminders, if any
- report status

The assistant then asks for explicit confirmation.

No final report may be saved or submitted without explicit confirmation.

Accepted user actions during review include:

- confirm and save
- reject and correct a field
- ask to repeat the review
- cancel the report

## 26. Privacy And Data Handling

The MVP uses mock data only.

It should still be designed with privacy principles in mind.

The MVP should not claim full production GDPR compliance. A better statement is:

```text
The MVP considers privacy and GDPR principles from the beginning, but full production-grade GDPR compliance depends on final hosting, access control, retention rules, deletion workflows, processor agreements, and legal review.
```

Persisted data in the MVP:

- text chat history
- transcripts as chat messages
- structured report draft
- report status
- final confirmed visit report
- user context
- mock CRM/ERP references

Not persisted as long-term records:

- raw audio archives
- generated TTS audio archives
- real customer data
- real employee data

Raw audio, once implemented, may exist temporarily during an open report session. It should be discarded after transcription, report completion, or cancellation unless a later explicit design decision says otherwise.

## 27. Debug Logging

Debugging should use Python logging, not scattered print statements.

Each chat turn should log at least:

- `chat_id`
- `user_id`
- `ai_provider`
- incoming text or STT transcript
- detected intent
- `intent_confidence`
- `target_sections`
- updated section statuses
- missing sections
- next assistant question
- errors or uncertainties

A debug UI is not required for the first vertical slice.

## 28. Current Decisions

The following decisions define the current MVP direction:

| Topic | Current decision |
|---|---|
| Backend/frontend stack | Flask, Jinja, Vanilla JavaScript, SQLite for Vertical Slice 1 |
| Provider selection by user | Removed from sales UI; provider is an admin setting |
| Gemini | First real LLM provider |
| Local provider | Planned after the Gemini workflow is stable, using an OpenAI-compatible local API |
| Ratings | Phase 6 uses the four eNVenta ratings: customer satisfaction, technical attractiveness, commercial attractiveness, and priority |
| Follow-up work | Phase 6 writes eNVenta-like reminders instead of the legacy inside-sales task target |
| CRM | Placeholder CRM/ERP counterpart, not application core |
| Database | SQLite is the current local mock backend; Postgres can be introduced later behind the same CRM/eNVenta gateway |
| Observability | Langfuse is available as an optional development tracing layer and must not affect business logic |
| Frontend/Admin UX | Phase 8 is complete and merged |
| Voice | Phase 9 adds voice as a layer over the existing text workflow |
| STT/TTS timing | Next implementation step after the Phase 6/8 stable text baseline |
| STT service | Local Speaches Docker sidecar |
| TTS service | Local Kokoro/Martin Docker service first; Speaches TTS can be compared later |
| Audio persistence | No long-term raw audio archive |
| Language | Session language controls first slice behavior |

## 29. Open And Pending Decisions

The following decisions remain open, deferred, or dependent on external input:

| Topic | Current status |
|---|---|
| Gemini model | Current local test setting is `gemini-3.1-flash-lite`; Gemini Free Tier rate limits make a local LM Studio/OpenAI-compatible fallback important for continued testing |
| Local LLM candidates | Later provider work should evaluate LM Studio through an OpenAI-compatible local API after admin configuration and demo stabilization |
| eNVenta visit report fields | First screenshot-based field mapping is documented; Phase 6 uses an eNVenta-shaped mock target rather than a real eNVenta API |
| Placeholder CRM/ERP API contract | Phase 6 defines an internal CRM/eNVenta gateway boundary backed by local mock tables; Postgres or real eNVenta access can replace the backend later |
| Setup/password reset token flow | Needs clarification: decide whether the first slice needs real setup/reset tokens or only seeded demo users |

## 30. Next Implementation Step

The current implementation baseline includes:

- Flask app structure
- login and role routing
- SQLAlchemy-backed SQLite development storage
- eNVenta-shaped mock CRM/writeback data
- Gemini-assisted text report loop
- internal CRM/eNVenta gateway boundary
- optional Langfuse observability

The next practical step is the Phase 9 voice foundation:

- add browser microphone capture to the report chat
- connect a local Speaches Docker sidecar for STT
- submit transcripts into the existing text report loop
- connect local Kokoro/Martin Docker TTS for assistant playback
- keep text input and visible transcript as the fallback path

After that, BENNO should move into repeatable demo-scenario stabilization.
Postgres, local LLM provider experiments, and real eNVenta integration should
stay behind the stabilized voice-assisted workflow and the existing
CRM/eNVenta gateway boundary.
