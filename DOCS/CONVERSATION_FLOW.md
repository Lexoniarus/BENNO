# BENNO Conversation Flow

## Purpose

This document defines the current conversation behavior for BENNO.

It consolidates the valid conversation and report-draft content from the earlier German concept notes. The archived German notes remain available in `DOCS/archive_de/`, but this file is the English working document for implementation.

## Core Loop

The central product loop is:

```text
free input -> extraction -> structured draft -> missing sections -> guided question -> updated draft
```

BENNO should not behave like a rigid form. The field sales user may start freely. BENNO extracts what is already present and only asks for information that is missing, unclear, or contradictory.

If the first user message already contains enough information, BENNO should move directly toward a block-based review instead of creating artificial extra questions.

## Phase 6 eNVenta Conversation Shape

Phase 6 should adapt the conversation to the eNVenta target fields without
turning BENNO into a copied eNVenta form.

The backend owns the required eNVenta checklist. Gemini helps interpret free
German input against that checklist, proposes field updates, and suggests the
next natural question. Gemini must not decide which fields are required and
must not save anything directly.

The intended high-level question flow is:

| Conversation block | Natural German question intent | Main target fields |
|---|---|---|
| Visit context | Ask which customer, lead, or contact the visit was about and whether the visit was in person, virtual, or by phone. | `account`, `contact`, `visit_type`, `participants` |
| Goal or topic | Ask for the visit reason, goal, or main topic. | `target_topic` / `visit_topic` |
| Discussion content | Let the user describe the conversation freely. | `info_text` / `summary`, optional `strength_text`, optional `weakness_text`, offer/order references |
| Agreement and next step | Ask what was agreed, who should do what next, and whether a follow-up or reminder is needed. | `agreement_text`, `outcome`, `next_action`, `next_appointment_date`, `reminders` |
| eNVenta ratings | Ask for the four eNVenta ratings together, either as numbers from 1 to 10 or in words. | `customer_satisfaction_rating`, `technical_attractiveness_rating`, `commercial_attractiveness_rating`, `priority_rating` |
| Review | Show the eNVenta-oriented draft for confirmation. | `mock_visit_reports` write target |

BENNO should ask direct follow-up questions only for missing or unclear
requirements. For example, `strength_text` and `weakness_text` can often be
derived from the user's description and ratings. They should not block the
report unless the business rule later makes them mandatory.

The desired behavior is: BENNO knows the eNVenta target shape; Gemini recognizes
which parts of a normal sales conversation already satisfy that shape.

The concrete German questions should be derived from the target fields and then
tested against real Gemini behavior. They are not fixed as a hard form script.
If Gemini reliably extracts several fields from one answer, BENNO should skip
the redundant follow-up questions.

## Report Sections

The report draft is organized into these sections:

| Section | Purpose |
|---|---|
| `customer_context` | Existing customer, existing lead, new lead, new address, or unclear context |
| `contacts` | Contact persons or meeting participants |
| `visit_reason` | Reason for the visit |
| `summary` | Main meeting summary |
| `outcome` | Result, agreement, or meeting outcome |
| `next_action` | Next step, follow-up, or reminder date |
| `offer_reference` | Offer reference, if relevant |
| `order_reference` | Order reference, if relevant |
| `ratings` | eNVenta-aligned rating values and short explanations |
| `final_report` | Written final visit report |
| `user_confirmation` | Explicit final confirmation |

Offer and order references must remain separate. An offer belongs to a pre-sales or sales opportunity context. An order belongs to an existing commercial transaction or fulfillment context.

## Section Status

Each section has a status used for conversation control and debugging:

| Status | Meaning |
|---|---|
| `open` | No usable content yet |
| `detected` | Content was detected but not fully confirmed |
| `unclear` | The system is unsure or found a conflict |
| `confirmed` | Content was confirmed or accepted |
| `corrected` | The user corrected the content |
| `not_applicable` | The section is not relevant for this report |

The section status is internal. It is not intended as a CRM UI concept.

## User Intents

Each user message should be classified into one of these intents:

| Intent | Meaning |
|---|---|
| `answer` | The user answers the current question |
| `correction` | The user corrects previous or current information |
| `additional_info` | The user adds information that may affect one or more sections |
| `confirmation` | The user confirms a summary, section, or final review |
| `rejection` | The user rejects a summary, assumption, or final save |
| `repeat` | The user wants the last question or review repeated |
| `cancel` | The user cancels the current report |
| `unknown` | The intent is not clear enough |

Corrections always take priority over the current question. If BENNO asks about the next action and the user corrects the contact person, the correction is processed first. After that, BENNO returns to the next open or unclear section.

## Intent Confidence

Intent detection should include an internal confidence score.

Suggested handling:

| Score | Behavior |
|---|---|
| `>= 0.75` | Process directly |
| `0.45` to `0.74` | Process carefully or ask for confirmation |
| `< 0.45` | Ask a clarification question |

The confidence score is an internal debugging and control value. It is not a mathematically reliable probability.

## Target Sections

Each detected intent should include the affected report sections.

One user message may update multiple sections. For example, a single message can describe the customer, the meeting outcome, the follow-up action, and a rating clue.

Example:

```json
{
  "intent": "additional_info",
  "intent_confidence": 0.78,
  "target_sections": ["summary", "next_action", "ratings"]
}
```

Provider-facing AI responses may use a different wire shape than BENNO's internal state. For Gemini, section updates are requested as a list of explicit section/value objects:

```json
{
  "section_updates": [
    { "section": "customer_context", "value": "PerfSolar" },
    { "section": "contacts", "value": "Frau Schmidt" },
    { "section": "visit_reason", "value": "Forecast" }
  ]
}
```

The backend converts this into the internal section map only after validation. Unknown section names, empty values, malformed update objects, and provider errors must not break the report loop. They are ignored or handled through deterministic fallback behavior.

## Customer And Lead Context

`customer_context` is mandatory.

BENNO distinguishes:

| Context | Meaning |
|---|---|
| `existing_customer` | Customer is known and can be referenced |
| `existing_lead` | Lead or address is known and can be referenced |
| `new_lead` | New lead or address was mentioned and must not be created automatically |
| `unclear` | BENNO cannot decide and must ask |

New customers, leads, addresses, or contacts must not be created automatically. BENNO may capture the information, but master data review is handled through an inside sales task.

## Contacts

The report must contain who participated in the meeting.

The contact may be:

- an existing contact
- a newly mentioned person
- an unclear person that needs review

If a contact is new or cannot be validated, BENNO does not create a master data record. It creates or proposes an inside sales task instead.

## Ratings

The `ratings` section is mandatory.

Starting with Phase 6, the eNVenta screenshot ratings are the leading target
structure. Earlier Phase 4/5 BENNO ratings were useful for the first text loop,
but they are no longer the desired business field set.

| Rating | Meaning |
|---|---|
| `customer_satisfaction_rating` | eNVenta `Zufriedenheit`, from 1 to 10 |
| `technical_attractiveness_rating` | eNVenta `Techn. Attrakt.`, from 1 to 10 |
| `commercial_attractiveness_rating` | eNVenta `Kaufm. Attrakt.`, from 1 to 10 |
| `priority_rating` | eNVenta `Priorität`, from 1 to 10 |

BENNO should infer ratings from the conversation where possible, explain them briefly, and allow the user to confirm or correct them.

The final report text should be consistent with the ratings. It does not need to mechanically repeat every numeric value.

The previous internal fields `sales_opportunity`, `meeting_mood`,
`closing_probability`, and `need_for_action` should be treated as legacy
Phase 4/5 fields. They may be migrated or mapped during implementation, but
they must not remain the Phase 6 target contract.

Phase 6 should replace the older six-rating test expectations with the four
eNVenta ratings. Test data may be migrated or rebuilt, but the target contract
must not keep both rating sets in parallel.

## Assisted Flow Bundling

The Gemini-assisted text loop should feel like a guided conversation, not a rigid field form.

If one user message clearly contains several report facts, BENNO should capture all valid sections at once and move to the next genuinely missing item.

Examples:

- A message can fill customer or lead, contact, and visit reason together.
- An outcome message can also contain the next follow-up action.
- A lead/no-offer statement can mark offer and order references as not applicable.
- An inside-sales follow-up statement can create a follow-up signal for later task creation.
- Ratings can be answered as one combined assessment instead of six isolated form questions.

The backend remains responsible for deciding what is accepted, skipped, or still missing. Gemini may propose bundled updates, but unknown sections, empty values, and unsafe overwrites are ignored.

## LLM Role Separation

The Gemini integration uses two logical roles:

- extractor / observer: reads the current user message and proposes structured updates through a schema
- conversation assistant: receives the validated draft state and writes the next short German assistant question

Stable role rules are passed as Gemini system instructions. Dynamic state such as the current step, known answers, missing fields, ratings, and the latest user message is passed as content.

The conversation assistant does not decide what is saved. It only words the next question after the backend has validated and applied allowed updates.

During the Phase 5 report loop, BENNO uses at most one Gemini call per user message. The structured extraction response may include a suggested next German question, but the backend only uses it when the suggested section matches the backend-computed next step. Otherwise, BENNO falls back to its deterministic German question templates.

## Report Requirements Context

Gemini-facing extraction and question-drafting contexts include a `report_requirements` checklist.

Each checklist item contains:

- `key`
- German `label`
- `status`: `missing`, `completed`, `not_applicable`, or `partially_completed`
- `required`
- `current_value`
- `question`
- `section`

The checklist includes all report requirements from the beginning, including all rating fields. This lets Gemini compare a free user message against the full target shape instead of only the current deterministic step.

The extractor must use this checklist to detect when one message satisfies several requirements at once. The conversation role must use the checklist to avoid asking again for requirements that are already completed or not applicable.

The checklist is context only. It is not persisted as a separate database object, and it does not replace backend validation.

## Final Review Loop

The final review is block-based and human-readable.

For Phase 6, the review should focus on the entries that BENNO would write into
`mock_visit_reports` and related reminder records. BENNO should ask for explicit
confirmation before saving each new write target entry or the complete write
set. This confirmation step can be deterministic; it does not need an LLM call.

It should include:

- customer or lead context
- contacts or participants
- visit reason
- summary
- outcome or agreement
- next action and follow-up
- offer reference, if relevant
- order reference, if relevant
- ratings with short explanations
- final written report
- inside sales tasks, if any
- report status

No final report may be saved or submitted without explicit user confirmation.

During review, the user may:

- confirm and save
- reject and correct a field
- ask to repeat the review
- cancel the report

## Core Safety Rules

- BENNO may suggest, but the application validates and decides.
- AI output is never written directly to the database.
- Corrections override previous assumptions.
- Final save requires explicit confirmation.
- New master data is not created automatically.
- Inside sales tasks are created when master data or follow-up work is needed.
