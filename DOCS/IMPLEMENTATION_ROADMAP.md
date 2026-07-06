# BENNO Implementation Roadmap

## Purpose

This document describes the planned development path for BENNO.

It is not a product concept document. It is a practical implementation roadmap: what we build first, when each phase is considered done, and which topics are intentionally delayed.

Guiding principle:

> Build a small, complete text loop first. Then add depth, voice, eNVenta field mapping, and local AI.

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

- customer or lead
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
- create inside sales task if needed

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

Important rule:

The AI may suggest values, but it must not save directly.

The code still decides:

- Which fields are missing?
- Which values are allowed?
- What was validated against the mock CRM?
- When is the report ready for review?
- When may the report be saved?
- Whether an inside sales task is created.

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

Questions to resolve:

- Which fields are required?
- Which fields are optional?
- Which values come from login or user context?
- Which values come from mock CRM data?
- Which values must BENNO ask for?
- Which fields are written back?
- Which information creates reminders or inside sales tasks?

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

The placeholder CRM service should then define:

- search customer
- search contact
- search offer
- search order
- save visit report
- create reminder or inside sales task

Done when:

- The mock database represents the relevant eNVenta fields.
- A final report can be saved in the expected structure.
- The placeholder CRM contract is clear enough to be replaced by a real integration later.

## Phase 7: Minimal Admin Completion

Goal:

The admin area is functional, but not overbuilt.

Admins can:

- see users
- view or change roles
- set user language
- set global provider
- count open chats per user
- count completed reports
- count problematic chats
- see cases with `inside_sales_input_required`

Admins must not:

- see complete chat content
- read transcripts
- inspect complete free-text reports

Done when:

- Admin configuration works.
- The status overview is simple but useful.
- The admin area does not become a content surveillance interface.

## Phase 8: Stabilization And Demo Scenarios

Goal:

BENNO is reliable enough to demo as a text-based MVP.

Demo scenarios:

1. Known customer, known contact, normal follow-up
2. Known customer, new contact, inside sales task
3. Existing offer is mentioned and found
4. Offer is mentioned but unclear
5. New lead with reminder
6. User corrects earlier information
7. Review is rejected and corrected
8. Review is confirmed and saved

Done when:

- All demo scenarios can be played through.
- Error cases are handled understandably.
- The text loop is stable enough to build voice on top.

## Phase 9: STT And TTS

Goal:

Voice is added as a layer over the same workflow.

Principle:

```text
voice input -> STT -> text turn -> same chat workflow -> assistant text -> TTS -> voice output
```

Scope:

- capture voice input
- convert speech to text
- treat transcript as a normal chat message
- read BENNO responses aloud
- read the final review aloud

Important:

- The business workflow stays the same.
- STT only replaces text input.
- TTS does not replace visual output; it adds voice output.

Done when:

- A report can be started by voice input.
- BENNO can read responses aloud.
- The user can still see text and intervene manually if needed.

## Phase 10: Local Provider

Goal:

The privacy direction is tested practically.

Scope:

- local provider through an OpenAI-compatible API
- for example LM Studio
- same provider contract shape as the Gemini provider
- comparison against the same demo cases

Questions to test:

- Does the local model understand the inputs well enough?
- Does it provide stable structured suggestions?
- Does it need tighter prompts?
- Do tasks need to be split more strongly in code?
- Is performance acceptable?

Done when:

- The same text loop can be tested with a local provider.
- Differences to Gemini are documented.
- There is enough evidence to decide how far BENNO can run locally.

## Recommended Start

Next, implement Phase 1 and Phase 2:

1. Flask project structure
2. SQLite connection
3. Data models
4. Seed data
5. Login foundation

Then move directly to Phase 4:

> A complete report loop from "New report" to "saved".

This loop is the foundation. Once it works, Gemini, voice, eNVenta field mapping, and the local provider are extensions on a stable core.
