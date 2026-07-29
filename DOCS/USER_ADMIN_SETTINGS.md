# BENNO User And Admin Settings

## Purpose

This document defines the current user, admin, and configuration behavior for BENNO.

It consolidates the valid admin and user-setting content from the archived German notes.

## Roles

The MVP has two roles:

| Role | Purpose |
|---|---|
| `sales_rep` | Field sales user who creates and manages their own visit report chats |
| `admin` | User who manages basic configuration and technical status overview |

No mixed role is required for the MVP.

## Sales User Area

After login, a sales user sees a focused dashboard.

The first slice should include:

- new report
- open reports
- completed reports
- options

Sales users should not see:

- AI provider selection
- concrete model configuration
- STT model selection
- TTS model selection

The sales workflow should stay focused on creating and continuing visit reports.

## Admin Area

The admin area should stay simple.

It should include:

- user list
- create or edit users
- set roles
- set user language
- set global AI provider
- set optional per-user provider override
- simple status overview

The admin area does not need to be mobile-optimized for the first slice.

## Admin Content Boundary

The admin status overview must not become content surveillance.

Admins may see:

- users
- roles
- language settings
- provider overrides
- global provider
- global language default
- number of open chats per user
- number of completed reports per user
- number of chats with error or blocked status
- number of reports requiring inside sales input

Admins should not see in this view:

- complete chat content
- transcripts
- full free-text reports
- detailed conversation history

## Language Settings

The MVP supports:

- `de`
- `en`

Rules:

- Default language is German.
- Each user can have a preferred language.
- New chats copy the user's current preferred language into the chat session.
- Running chats keep the language they started with.
- UI text, assistant questions, summaries, confirmations, STT expectations, and TTS output follow the session language.

For the first technical slice, the session language is the controlling language.

## AI Provider Settings

AI provider configuration is an admin topic.

Planned providers:

- `gemini`
- `openai`
- `local`

Rules:

- Normal sales users do not choose the provider.
- There is a global default provider.
- A user may have an optional provider override.
- Concrete model settings are not normal user settings.
- Local provider support comes after the Gemini workflow is stable.

Resolution at chat start:

```text
ai_provider = user.ai_provider_override or global.default_ai_provider
session_language = user.preferred_language or global.default_language
```

## Authentication

The MVP needs real login behavior, but not a full identity-management system.

Required:

- email and password login
- password hashing
- active or inactive users
- role-based routing
- user-specific language setting
- optional external sales representative ID

For the current MVP:

- seeded demo users remain available for local testing
- local setup links can be generated in the admin UI
- local password reset links can be generated in the admin UI
- no email delivery is required
- no two-factor authentication is required
- no production identity-management system is required

## Seeded Mock Users

The current local demo company is Solar Sales. After running `seed-db` or
`reset-db --yes`, these seeded users are available for testing:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@solar-sales.local` | `Admin123` |
| Sales Rep | `laura.schneider@solar-sales.example` | `Sales123` |
| Sales Rep | `markus.weber@solar-sales.example` | `Sales123` |
| Sales Rep | `sophie.klein@solar-sales.example` | `Sales123` |
| Sales Rep | `tobias.fischer@solar-sales.example` | `Sales123` |

The older BENNO demo accounts are retired and should not be used for current
manual tests. If the application rejects the current credentials, the running
app is likely using an outdated local database and should be reseeded or reset.

## Registration And Password Reset Direction

Current local MVP flow:

```text
Admin creates user -> system generates setup token/link -> user sets password
```

Password reset can follow the same pattern:

```text
Admin starts reset -> system generates reset token/link -> user sets new password
```

For the Masterschool demo, these links are shown directly in the admin UI. The
system stores only hashed tokens. Real email delivery, SSO, two-factor
authentication, and production identity governance remain out of scope.

## External Sales Representative Reference

A BENNO user may later be linked to a CRM/ERP sales representative.

The optional field can be represented as:

```text
external_sales_rep_id
```

This keeps BENNO independent from any specific CRM user model while allowing a later eNVenta or CRM/ERP integration to map users properly.

## First-Slice Acceptance

This area is done for the first slice when:

- admin and sales users can log in
- users are routed by role
- sales users can only access their own reports
- admins can see basic user and status information
- admin does not expose detailed chat content
- provider and language defaults exist
