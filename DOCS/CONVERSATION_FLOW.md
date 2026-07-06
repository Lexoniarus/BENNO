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
| `ratings` | Six sales evaluation values and short explanations |
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

BENNO uses six rating values on a scale from 1 to 10:

| Rating | Meaning |
|---|---|
| `sales_opportunity` | Sales relevance of the opportunity |
| `meeting_mood` | How positive or difficult the meeting atmosphere was |
| `priority` | How much attention the case requires |
| `closing_probability` | How likely a successful close appears |
| `need_for_action` | How urgent further action is |
| `customer_satisfaction` | How satisfied the customer appears |

BENNO should infer ratings from the conversation where possible, explain them briefly, and allow the user to confirm or correct them.

The final report text should be consistent with the ratings. It does not need to mechanically repeat every numeric value.

## Final Review Loop

The final review is block-based and human-readable.

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
