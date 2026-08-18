# BENNO Implementation Roadmap

## Purpose

This document describes the planned development path for BENNO.

It is not a product concept document. It is a practical implementation roadmap: what we build first, when each phase is considered done, and which topics are intentionally delayed.

Guiding principle:

> Build a small, complete text loop first. Then add voice on top of that
> workflow, stabilize the demo scenarios, and only then add Postgres, local AI,
> or real eNVenta integration depth.

BENNO must not be built as one large big-bang application. Every phase should be runnable, testable, and committable.

## Phase 0: Project Baseline

Status: complete.

Goal:

- Local Git repository is initialized.
- Private GitHub repository is connected.
- Documentation is versioned.
- The project can be opened in PyCharm.

Done:

- Local Git on branch `main`
- Private GitHub remote `Lexoniarus/BENNO`
- Initial documentation
- `.gitignore`

Next phase:

- Create the Python/Flask project structure.
- Prepare the virtual environment.
- Document the local start command.

## Phase 1: Flask Foundation

Goal:

BENNO starts as a local web application.

Scope:

- Flask app factory
- Configuration
- `templates`
- `static`
- Prepared SQLite connection
- Simple start screen or login screen
- Base layout for desktop and smartphone
- `.env.example`
- Dependencies in `requirements.txt` or `pyproject.toml`

Technical direction:

- Flask
- Jinja
- Vanilla JavaScript
- SQLite
- SQLAlchemy or Flask-SQLAlchemy
- Password hashing with Werkzeug

Done when:

- The app starts locally.
- A first page is visible in the browser.
- No AI is required yet.

## Phase 2: Data Model And Mock Database

Goal:

BENNO has the data foundation required for the later report loop.

Initial tables:

- `users`
- `global_settings`
- `chats`
- `chat_messages`
- `report_drafts`
- `final_reports`
- `inside_sales_tasks`
- `mock_customers`
- `mock_contacts`
- `mock_offers`
- `mock_orders`

Seed data:

- one admin user
- one sales user
- three to four demo customers
- contacts
- offers
- optionally one or two orders

Important:

- The final eNVenta field structure is added only after Bernd's field list is available.
- Until then, the existing report sections are the internal working structure.

Done when:

- The database can be initialized.
- Demo users exist.
- Mock customers, contacts, offers, and orders can be queried.

## Phase 3: Login, Roles, And Navigation

Goal:

Users reach the correct area after login.

Sales users see:

- New report
- Open reports
- Completed reports
- Options

Admins see:

- User list
- Simple status overview
- Global provider setting

Decision for the first slice:

- No setup/reset link logic.
- Seed users are sufficient at the beginning.
- Registration and password reset can be added later.

Done when:

- Login works.
- Sales users and admins land on different dashboards.
- Sales users only see their own chats and reports.
- Admins do not see chat content.

## Phase 4: First Complete Text Loop Without Real AI Magic

Goal:

The most important product flow works end to end.

A sales user can:

1. start a report
2. enter free text
3. build a draft from it
4. fill missing information
5. see a review
6. confirm the review
7. save a final report

Approach:

Build the logic deliberately simple at first. It does not need perfect AI extraction yet. The important part is that the whole flow exists.

Report parts to check:

- AKL context
- contact person
- visit reason
- summary
- outcome
- next action
- follow-up or reminder date
- offer reference, if relevant
- order reference, if relevant
- ratings

Required behavior:

- start chat
- save free input
- create draft state
- detect missing sections
- ask the next useful question
- apply corrections
- create block-based review
- request final confirmation
- save final report
- create a reviewable follow-up reminder if needed

Done when:

- A complete report can be saved without a real AI provider.
- The flow from start to save can be demonstrated.
- Corrections are not lost.

## Phase 5: Gemini Provider Integration

Goal:

BENNO understands free text better and responds more naturally.

Scope:

- Gemini provider service
- controlled AI response structure
- extraction from free user input
- intent detection
- suggestion for next question
- review wording
- final report text

Implementation note:

- Gemini Developer API structured output uses an explicit list of section/value update objects for report extraction. BENNO converts that provider-specific shape into the internal provider contract before applying validation.
- The Phase 5 loop should use Gemini as an assisted conversation layer, not just as extraction on top of a rigid form. Clear lead/no-offer signals, follow-up actions, and grouped ratings should be handled without unnecessary extra questions.
- Gemini calls should separate stable system instructions from dynamic content. The extractor role uses structured output; the conversation role receives the validated draft state and only words the next question.
- Gemini receives an explicit `report_requirements` checklist in extraction and next-question contexts, so it can see all required, completed, skipped, and partially completed report fields from the beginning.
- Normal report turns use at most one Gemini call per user message. The backend may use the extractor's same-call suggested question when it matches the computed next step; otherwise deterministic questions keep the loop inside rate limits.

Important rule:

The AI may suggest values, but it must not save directly.

The code still decides:

- Which fields are missing?
- Which values are allowed?
- What was validated against the mock CRM?
- When is the report ready for review?
- When may the report be saved?
- Whether a follow-up reminder is created.

Done when:

- Gemini can interpret free visit descriptions usefully.
- Follow-up questions become more natural.
- Review and final report text are understandable.
- Backend code remains in control of saving and status transitions.

## Phase 6: eNVenta Fields And Placeholder CRM Contract

Trigger:

Bernd's eNVenta field list is available.

Goal:

The internal report structure is mapped to the expected eNVenta visit report fields.

Detailed implementation plan:

- `DOCS/PHASE_6_IMPLEMENTATION_PLAN.md`

Questions to resolve:

- Which fields are required?
- Which fields are optional?
- Which values come from login or user context?
- Which values come from mock CRM data?
- Which values must BENNO ask for?
- Which fields are written back?
- Which information creates `MockReminder` records?

Field classification rule:

Do not treat every visible eNVenta screen field as a BENNO dialog question.

Classify fields first:

- user-provided report content
- AI-assisted derived values
- CRM/eNVenta master data
- BENNO login or user context
- eNVenta system metadata

Known eNVenta system metadata examples:

- `Erfassung` is set by eNVenta when the record is created.
- `Änderung` is set by eNVenta when the record is changed.

BENNO should not ask for or write these fields. They may be read-only integration metadata later.

Phase 6 field decisions already clarified:

- `Besuchsart` maps to `visit_type`; MVP values are `in_person`, `virtual`, and `phone`.
- `Status` and `Berichtsstatus` represent the visit report processing state; MVP values are `open`, `in_progress`, and `closed`.
- `Termin ab` maps to `next_appointment_date`.
- `Besuchsrhythmus` is out of scope for the MVP.
- `Zufriedenheit`, `Techn. Attrakt.`, `Kaufm. Attrakt.`, and `Priorität` are ratings from 1 to 10.
- These four eNVenta screenshot ratings are authoritative for Phase 6. The older six BENNO internal ratings from Phase 4/5 are legacy working fields and should not remain the target contract.
- Offers and orders may appear in one eNVenta table but must remain separate BENNO document types.
- AKL is the shared address/customer/supplier/lead domain; contacts are linked to AKL/account records.
- The placeholder contract should include accounts, contacts, offers, orders, reminders, CRM users, and field sales representatives.
- `mock_visit_reports` are the eNVenta-shaped write target created from confirmed BENNO final reports. Their free-text fields include `target_topic`, `info_text`, `agreement_text`, `strength_text`, and `weakness_text`.
- Phase 6 should replace the Phase 2 mock customer/lead split with an AKL-like account model where leads, customers, and suppliers are account types.
- CRM users and field sales representatives are separate mock domains. Responsible users live in the CRM user domain; representatives are always field sales people.
- Current inside sales tasks are the legacy basis for eNVenta-like reminders. Reminders may be assigned to inside sales users or field sales representatives.
- The report chat should use broad conversation blocks instead of one question
  per eNVenta field: visit context, goal/topic, discussion content, agreement
  and next step, document references when relevant, ratings, and final review.
- The concrete German questions should be derived from the target fields and
  adjusted through Gemini behavior tests, not frozen as a copied eNVenta form.
- The final review should explicitly confirm the eNVenta-oriented entries before
  saving them into the mock write target. This can be deterministic.
- Phase 6 replaces the old Phase 4/5 rating set and updates affected tests and
  mock data accordingly.
- The working mapping table and MVP required fields are maintained in `DOCS/ENVENTA_FIELD_NOTES.md`.

The placeholder CRM/eNVenta gateway should then define:

- search account or AKL record
- search contacts by account
- search offers
- search orders
- list or resolve CRM users
- list or resolve field sales representatives
- save mock visit report
- create mock reminder

This is an internal connector boundary, not an external REST API. Phase 6 uses
local mock tables behind it; a later MVP step may move persistence to Postgres
without changing the report loop's CRM/eNVenta contract.

Done when:

- The mock database represents the relevant eNVenta fields.
- A final report can be saved in the expected structure.
- The report loop uses the placeholder CRM/eNVenta gateway for lookup and
  writeback instead of direct mock-table access.
- The placeholder CRM/eNVenta contract is clear enough to be replaced by a
  Postgres-backed mock backend or a real integration later.
- Existing tests and seed/mock data use the Phase 6 account, visit report,
  reminder, and rating target structure.

## Phase 7: Langfuse Observability

Status: complete.

Goal:

BENNO can trace AI-assisted report turns for debugging without making
observability part of the business workflow.

Scope:

- Optional Langfuse configuration through environment variables
- One root trace for a report turn
- Gemini calls as generation observations
- Assistant reply and backend decision metadata on the root trace
- Defensive no-op behavior when Langfuse is disabled, unavailable, or failing
- Local trace privacy controls and secret masking

Important:

- Langfuse must not validate, advance, save, or alter report data.
- BENNO must run normally without Langfuse credentials.
- Trace output is for development and debugging, not for admin surveillance.

Done:

- Langfuse is integrated as an optional observability layer.
- Report turns and Gemini calls can be traced.
- Langfuse failures do not block the report loop.
- The local development database path is stable at the project root.

## Phase 8: Frontend And Admin UX Overhaul

Goal:

BENNO becomes easier to use and test as a browser-based MVP before more
provider, voice, or database complexity is added.

This phase combines a frontend overhaul with the missing minimal admin
configuration features.

Frontend goals:

- make the Sales report workflow feel coherent on desktop, tablet, and phone
- improve dashboard, open report, completed report, chat, review, and final
  report detail screens
- show report context clearly, including AKL context, topic, status,
  progress, and provider/debug state where useful
- keep German user-facing workflow text consistent for the current MVP
- avoid changing report business rules, eNVenta mapping, or provider behavior
  unless a frontend issue exposes a concrete bug

Admin goals:

- see users
- view or change roles
- set user language
- set global provider
- set global language defaults
- set optional per-user provider overrides
- count open chats per user
- count completed reports
- count problematic chats
- see cases with `inside_sales_input_required`

Admins must not:

- see complete chat content
- read transcripts
- inspect complete free-text reports

Done when:

- Sales and admin screens are usable for manual MVP testing.
- The main report loop can be tested on desktop and narrow mobile widths.
- Admin configuration works without exposing report or chat content.
- The status overview is simple but useful.
- The admin area does not become a content surveillance interface.

## Phase 9: Voice STT/TTS Foundation

Status: foundation implemented; demo hardening continues in Phase 10.

Goal:

Voice is added as an input and output layer over the existing text report
workflow.

Principle:

```text
browser microphone capture -> STT -> text turn -> same report loop -> assistant text -> TTS -> browser audio playback
```

Current implementation direction:

- Keep the text chat as the source-of-truth interaction surface.
- Add browser microphone capture through standard web media APIs.
- Send recorded audio to the backend for transcription through a local
  Speaches Docker sidecar.
- Use Speaches as the first STT integration target because it provides an
  OpenAI-compatible audio API and has a useful streaming path for later
  hands-free tests.
- Treat the transcript exactly like a manually typed chat message.
- Use the existing local Kokoro/Martin Docker TTS service for spoken BENNO
  responses.
- Keep Speaches TTS as a secondary TTS comparison path, not the first playback
  target.
- Return playable audio to the browser while keeping generated TTS snippets as
  local ignored performance artifacts, not business records.
- Treat voice mode as the default for in-progress report chats, while keeping
  one manual start button as browser-permission fallback.
- Read BENNO's assistant replies aloud automatically while voice mode is active.
- Reopen the answer gate automatically after playback, with silence detection
  plus manual stop/cancel controls.
- Cache and prewarm common TTS snippets such as standard phrases and frequent
  dynamic names so BENNO does not regenerate every assistant answer from
  scratch.

Important:

- The report loop, Gemini extraction, validation, review, and mock-eNVenta
  writeback must not be rewritten for voice.
- STT only creates text input.
- TTS only reads assistant output.
- Kokoro/Martin is not treated as true streaming TTS in this phase; snippet
  caching is the first latency-reduction path.
- Visual text remains available for correction, transparency, and fallback.
- Mobile browsers require HTTPS or another secure context for microphone
  capture. Plain LAN HTTP is enough for page loading and TTS playback, but not
  for reliable phone or tablet microphone access.
- Browser `SpeechRecognition` may be tested as an experiment, but it is not the
  primary MVP path because browser support and behavior are less predictable
  than microphone capture plus backend-controlled STT.

Done when:

- A sales user can record a voice answer in the report chat.
- The transcript appears as a normal chat message.
- The same Phase 6/8 report loop processes that transcript.
- BENNO can read the next assistant response aloud through local TTS.
- After spoken playback, BENNO can automatically listen for the next answer.
- The user can continue by text if microphone, STT, or TTS fails.

## Phase 10: Stabilization And Demo Scenarios

Status: in progress. The live harness design is documented, but its runner is
not implemented yet.

Goal:

BENNO is reliable enough to demo as a text and first voice-assisted MVP.

Demo scenarios:

1. Known customer, known contact, normal follow-up
2. Known customer, new contact, inside-sales `MockReminder`
3. Existing offer is mentioned and found
4. Offer is mentioned but unclear
5. New lead with reminder
6. User corrects earlier information
7. Review is rejected and corrected
8. Review is confirmed and saved

Manual Phase 9 voice testing adds these stabilization topics:

- noisy German STT must be expected; BENNO should keep text fallback and make
  structured review correction easy
- mobile voice needs HTTPS; iPad and phone browsers block microphone access
  over plain LAN HTTP
- AKL wording must be eNVenta-oriented: address, customer, supplier, with
  contacts handled separately
- BENNO must visibly distinguish known customer/account cases from new
  address/lead cases before writing to Mock-eNVenta
- inside-sales follow-up should create a pending reminder even when STT
  slightly distorts words such as "Innendienst"
- TTS should use an audio-only pronunciation map for English or product terms,
  while visible and stored text keeps the correct spelling
- useful LLM filtering should be preserved: irrelevant speech details may be
  omitted from the final report when they do not belong in the visit report

The Phase 9 stabilization patch addresses the application-side items above with
AKL-aware review/final labels, structured review correction fields, near-miss
follow-up detection, and a first TTS pronunciation map. Remaining Phase 10 work
is mainly repeatable demo hardening, STT model/configuration quality, and
deciding how to handle HTTPS for mobile demo testing.

Done when:

- All demo scenarios can be played through.
- Error cases are handled understandably.
- The text and first voice-assisted loop are stable enough for a mentor demo.

Phase 10 should implement the opt-in live functional test harness specified in
`PHASE_10_LIVE_FUNCTIONAL_TESTS.md`. The planned harness is automated and
repeatable, but it is not part of the normal deterministic regression suite. It
should exercise the real Gemini, Speaches, Kokoro/Martin, and optional Langfuse
chain with deliberately fragile demo scenarios.

Masterschool demo scope:

- stabilize the implemented Phase 9 turn-based voice layer over the existing
  text report loop
- keep text fallback and visible transcripts available at all times
- harden structured review correction for noisy STT, especially AKL names,
  participants, ratings, and reminders
- build opt-in live functional tests with real provider/voice calls and
  Langfuse evidence for the risky demo paths
- repeat and document the core demo scenarios against Mock-eNVenta data
- show `FinalReport`, `MockVisitReport`, and `MockReminder` creation after
  explicit user confirmation
- limit frontend and admin work to bug fixes and small usability improvements
- document risks and next steps without promising production readiness

Allowed only if small and demo-supporting:

- clearer HTTPS or microphone permission error messages
- small STT/TTS configuration fixes
- demo seed data or demo scenario documentation
- focused UX polish in the existing Phase 8 frontend

Out of scope for the Masterschool demo:

- real eNVenta access or live customer and employee data
- final ERP/CRM validation rules based on the real system
- Postgres migration
- production HTTPS deployment
- production authentication, SSO, two-factor authentication, or email delivery
- complete GDPR, retention, deletion, backup, restore, or audit concepts
- automatic master-data creation
- final local-LLM strategy
- systematic STT model benchmarking
- realtime streaming STT, barge-in, or interrupt handling
- native app, full PWA, or another frontend redesign

## Phase 11: Local Or OpenAI-Compatible Provider Fallback

Goal:

The privacy direction and Gemini rate-limit fallback are tested practically.

Scope:

- local provider through an OpenAI-compatible API
- for example LM Studio
- same provider contract shape as the Gemini provider
- comparison against the same demo cases
- no change to backend validation or report state rules

Questions to test:

- Does the local model understand German visit-report inputs well enough?
- Does it provide stable structured suggestions?
- Does it need tighter prompts?
- Do extraction and conversation wording need to be split more strongly?
- Is local performance acceptable for the hands-free target?

Done when:

- The same text loop can be tested with a local provider.
- Differences to Gemini are documented.
- There is enough evidence to decide how far BENNO can run locally.

## Later MVP: HTTPS, Postgres, And Real eNVenta Integration

Goal:

The local mock backend can be moved toward a more production-like deployment,
persistence, and integration setup without changing the report loop's
CRM/eNVenta boundary.

Scope:

- provide BENNO through HTTPS so mobile browsers can use microphone capture
- keep public access controlled through login and later production security
  measures
- move persistence from local SQLite to Postgres behind SQLAlchemy
- keep the internal CRM/eNVenta gateway contract stable
- prepare later real eNVenta lookup and writeback
- avoid introducing a real eNVenta API dependency before the mock contract is stable
- keep real customer and employee data out of Masterschool demo tests

Questions to test:

- Which HTTPS deployment path is practical for demo and later field use:
  public but access-controlled, or trusted internal HTTPS?
- Which SQLite assumptions need adjustment for Postgres?
- Which mock gateway calls become database-backed service calls?
- Which eNVenta fields still need real API clarification?
- Which security, retention, backup, deletion, and audit requirements are
  needed before real data is used?

Done when:

- Mobile devices can access BENNO through trusted HTTPS.
- The same report loop works against Postgres-backed persistence.
- The gateway boundary remains the report loop's integration surface.
- Real eNVenta integration can be planned without reshaping the core workflow.

## Current Recommended Next Step

The completed baseline now includes Flask, data model, login, the text report
loop, Gemini, eNVenta-shaped mock writeback, the internal CRM/eNVenta gateway,
optional Langfuse observability, the Phase 8 frontend/admin overhaul, and the
first Phase 9 voice layer.

The next practical work is Phase 10 demo stabilization around the implemented
Phase 9 foundation:

1. implement the opt-in live functional test harness
2. repeat the eNVenta-shaped demo scenarios with text and voice
3. document STT failure patterns and improve the review/correction safety net
4. decide how to handle HTTPS for mobile voice testing
5. compare whether local LLMs can handle noisy German STT transcripts well
   enough
6. keep the Masterschool demo on mock data and Mock-eNVenta writeback

After the demo baseline is stable, BENNO can branch into HTTPS deployment,
Postgres, local provider experiments, and later real eNVenta integration.
