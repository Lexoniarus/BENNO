# BENNO Frontend UX Specification

## Purpose

This document defines the Phase 8 frontend direction for BENNO.

BENNO is an internal browser-based assistant for B2B field sales visit reports.
The UI should feel practical, conversational, and close to the S:FLEX brand
without becoming a marketing page.

## CI Reference

The visual reference is:

- https://www.sflex.de/

The current S:FLEX-near token direction is:

- deep petrol background: `#143347`
- darker petrol chrome: `#0b2638`
- accent yellow: `#ebe566`
- off-white work surface: `#f8f8f4`
- muted surface: `#eef0ea`
- text petrol/graphite: `#102c3d`
- green success accent: `#adce6d`
- red warning accent: `#e7413b`

The accepted direction uses more dark app surface than the first concept image.
White and off-white panels are working areas, not the dominant page theme.

## Typography

BENNO should use an S:FLEX-like geometric font stack:

```css
"Space Grotesk", "Poppins", "Segoe UI", sans-serif
```

Runtime font loading from external domains should be avoided in the MVP. If the
exact fonts are not installed locally, the fallback must still preserve the
geometric S:FLEX-like character as closely as practical.

## Mock Data Boundaries

S:FLEX is only the visual reference for Phase 8. Demo companies, demo users,
and visible mock email addresses must not use S:FLEX domains or imply that
S:FLEX data exists in the local system. Use neutral fictional companies and
safe mock addresses such as `example.invalid` instead.

Visible product wording should refer only to BENNO and the local Mock-eNVenta
counterpart. Do not introduce other CRM product names in mock data,
screenshots, or UI copy.

## Layout Principles

- Keep Flask, Jinja, and Vanilla JavaScript for Phase 8.
- Build the actual usable application, not a landing page.
- Use German for user-facing workflow text in the current MVP.
- Keep dark petrol as the app frame and primary background.
- Use off-white panels for chat, tables, review blocks, and forms.
- Keep cards and panels simple with small radii.
- Avoid nested cards.
- Avoid decorative gradients, orbs, and marketing-style hero sections.
- Preserve German umlauts end to end.
- Mobile width around 390px must not create horizontal body overflow.

## Sales UX

The Sales area is the primary work surface.

Required screens:

- login
- sales dashboard
- open reports
- completed reports
- report chat
- report review
- final report detail
- options

The report chat should feel conversational but controlled:

- account or lead context is visible near the title
- provider/debug-safe status can be visible, for example Gemini active
- chat history is the main area
- report progress is compact and secondary
- the message composer is easy to use on desktop and mobile
- review and final report screens show eNVenta-near target fields clearly

## Admin UX

The Admin area is a control center, not a content surveillance interface.

Admins may see:

- users
- roles
- language settings
- provider overrides
- global provider
- global language default
- open chat counts
- completed report counts
- problem case counts
- inside-sales or reminder status counts

Admins must not see:

- complete chat content
- transcripts
- full free-text reports
- detailed field-sales conversation history

Phase 8 admin features include:

- create users
- edit users
- set role, language, active status, and provider override
- edit global default language and provider
- generate local setup and reset links
- show setup/reset links directly in the admin UI
- no email delivery

Setup and reset tokens must be stored hashed. Raw tokens may be shown once in
the UI and must not be logged or stored as plain text.

## Verification

Before closing Phase 8, verify:

- desktop layout
- tablet-like width
- mobile width around 390px
- login
- sales report chat
- open and completed report lists
- review
- final report detail
- admin dashboard
- user create/edit
- setup/reset password flow
- global settings form
- no admin exposure of chat or report content

Quality checks:

```bash
ruff check . --select E,W,F,I,N,UP,B
python -m black --check .
python -m pytest
```
