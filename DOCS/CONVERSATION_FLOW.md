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

When a message contains an implied but not fully explicit value, Gemini should
either extract it with a useful suggestion or ask a contextual clarification.
BENNO should not fall back to generic form wording after a rich user message.
The next assistant question should briefly reflect what was understood and then
ask only for the next missing or uncertain requirement.

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

For example, if the user says "ich war bei einem neuen potenziellen Kunden",
Gemini should treat `visit_type = in_person` as a strong candidate. If the
wording is still ambiguous, the assistant should ask a contextual confirmation
such as whether the meeting was on site or by phone/video, while mentioning the
new-lead context it already understood.

## Phase 6 Report Requirements

The Phase 6 `report_requirements` checklist should be built from the eNVenta
target fields. The wording below is the deterministic fallback wording. Gemini
may make the questions more natural, but it must not ask for fields that are
already completed or marked not applicable.

| Key | German label | Required | Section | Fallback question |
|---|---|---|---|---|
| `visit_context` | AKL-Kontext | Yes | `customer_context` | `Um welchen AKL-Eintrag ging es: Adresse, Kunde oder Lieferant? Falls es ein neuer Interessent ist, sag das bitte dazu.` |
| `visit_type` | Besuchsart | Yes | `visit_type` | `War der Besuch persönlich, virtuell oder telefonisch?` |
| `participants` | Teilnehmer | Yes | `contacts` | `Wer hat an dem Gespräch teilgenommen?` |
| `visit_date` | Besuchsdatum | Yes | `visit_date` | `War der Besuch heute oder an einem anderen Datum?` |
| `target_topic` | Ziel/Thema | Yes | `visit_reason` | `Was war das Ziel oder Hauptthema des Besuchs?` |
| `info_text` | Info | Yes | `summary` | `Was wurde besprochen? Du kannst es frei erzählen.` |
| `agreement_text` | Vereinbarung | Yes | `outcome` | `Was wurde konkret vereinbart oder entschieden?` |
| `next_action` | Nächster Schritt | Yes | `next_action` | `Was ist der nächste Schritt, und wer soll ihn übernehmen?` |
| `next_appointment_date` | Termin ab | Conditional | `next_action` | `Gibt es einen konkreten Folgetermin oder Wiedervorlage-Termin?` |
| `offer_reference` | Angebot | Conditional | `offer_reference` | `Gibt es dazu ein Angebot oder eine Angebotsnummer?` |
| `order_reference` | Auftrag | Conditional | `order_reference` | `Gibt es dazu einen Auftrag oder eine Auftragsnummer?` |
| `strength_text` | Stärke | Optional | `strengths` | `Gibt es aus deiner Sicht besondere Stärken oder positive Punkte?` |
| `weakness_text` | Schwäche | Optional | `weaknesses` | `Gibt es Risiken, Einwände oder Schwächen, die festgehalten werden sollen?` |
| `ratings` | Bewertungen | Yes | `ratings` | `Wie bewertest du Zufriedenheit, technische Attraktivität, kaufmännische Attraktivität und Priorität jeweils von 1 bis 10?` |
| `reminders` | Wiedervorlagen | Conditional | `reminders` | `Soll daraus eine Wiedervorlage entstehen? Falls ja: für wen, bis wann und mit welcher Nachricht?` |

Conditional requirements should become `not_applicable` when the conversation
clearly says they do not apply. For example, a new lead without offer or order
should not trigger separate offer and order questions.

The first assistant question may combine `visit_context`, `visit_type`, and
`participants` if that feels natural. Later questions should stay short and ask
for only the next truly missing information.

## Report Sections

The report draft is organized into these sections:

| Section | Purpose |
|---|---|
| `visit_context` | Existing AKL account, known address/lead, new lead, or unclear context |
| `visit_type` | Personal, virtual, or phone visit |
| `participants` | Contact persons or meeting participants |
| `visit_date` | Date of the visit |
| `target_topic` | eNVenta `Ziel/Thema` |
| `info_text` | eNVenta `Info` free text |
| `agreement_text` | eNVenta `Vereinbarung` free text |
| `next_action` | Next step, follow-up, or reminder date |
| `next_appointment_date` | eNVenta `Termin ab`, when relevant |
| `offer_reference` | Offer reference, if relevant |
| `order_reference` | Order reference, if relevant |
| `strength_text` | eNVenta `Stärke`, derived or asked briefly |
| `weakness_text` | eNVenta `Schwäche`, derived or asked briefly |
| `ratings` | eNVenta-aligned rating values and short explanations |
| `reminders` | Optional follow-up reminder for CRM users or field sales representatives |
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

Clarification questions should be contextual. If BENNO has already extracted
useful facts, the assistant should acknowledge one or two of them before asking
about the uncertain field. A low-confidence `visit_type` question should not be
the bare fallback question if the message already described the account, lead,
or next action.

## Target Sections

Each detected intent should include the affected report sections.

One user message may update multiple sections. For example, a single message can describe the customer, the meeting outcome, the follow-up action, and a rating clue.

Example:

```json
{
  "intent": "additional_info",
  "intent_confidence": 0.78,
  "target_sections": ["info_text", "next_action", "ratings"]
}
```

Provider-facing AI responses may use a different wire shape than BENNO's internal state. For Gemini, section updates are requested as a list of explicit section/value objects:

```json
{
  "section_updates": [
    { "section": "visit_context", "value": "PerfSolar" },
    { "section": "participants", "value": "Frau Schmidt" },
    { "section": "target_topic", "value": "Forecast" }
  ]
}
```

The backend converts this into the internal section map only after validation. Unknown section names, empty values, malformed update objects, and provider errors must not break the report loop. They are ignored or handled through deterministic fallback behavior.

## AKL And Visit Context

`visit_context` is mandatory.

Phase 6 and later should use eNVenta-oriented AKL language instead of the older
generic "customer/lead/contact" wording. AKL is one account/address domain with
three account types:

| AKL type | Meaning in BENNO |
|---|---|
| `A` | Adresse, including existing address/lead-like entries |
| `K` | Kunde |
| `L` | Lieferant |

Contacts are not a fourth AKL type. They are separate `MockContact` or later
eNVenta contact records linked to an AKL record.

BENNO still needs a conversational business classification around the AKL
record:

| Context | Meaning |
|---|---|
| `existing_customer` | AKL account of type `K` is known and can be referenced |
| `existing_lead` | AKL account of type `A` is known and can be referenced |
| `new_lead` | New lead or address was mentioned and must not be created automatically |
| `unclear` | BENNO cannot decide and must ask |

The UI and review should make this distinction visible. A report should not only
show a generic "Kunde/Lead/Kontakt" label when the relevant eNVenta target is an
AKL account plus separately linked contacts.

New accounts, contacts, offers, or orders must not be created automatically.
BENNO may capture the information as report text. Follow-up work is handled
through a `MockReminder` or later review work, not by writing master data.

## Participants

The report must contain who participated in the meeting.

The contact may be:

- an existing contact
- a newly mentioned person
- an unclear person that needs review

If a contact is new or cannot be validated, BENNO does not create a master data
record. The information stays in the report and can trigger review or reminder
work.

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

If one user message contains a likely but uncertain field value, BENNO should
prefer a short confirmation question over ignoring the user's wording. The LLM
is responsible for proposing this conversational clarification; the backend
validates the proposed value and keeps deterministic fallback wording only as a
safety net.

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

- AKL context, including whether the record is an address, customer, supplier,
  known address/lead, or new address/lead case
- participants
- visit type and visit date
- target topic
- info text
- agreement text
- next action and follow-up
- offer reference, if relevant
- order reference, if relevant
- strengths and weaknesses, if captured or derived
- ratings with short explanations
- final written report
- reminders, if any
- report status

No final report may be saved or submitted without explicit user confirmation.

During review, the user may:

- confirm and save
- reject and correct a field
- ask to repeat the review
- cancel the report

Phase 9 manual voice testing showed that this review must become more directly
editable. STT can mishear company names, contact names, and German business
terms. The review should therefore not rely only on one correction dropdown plus
one free text field. It should allow direct field-level correction for at least:

- AKL display/search name
- AKL type or lead/address classification
- contact or participant name
- target topic
- info text
- agreement text
- next action
- offer and order references
- reminder decision and reminder message
- eNVenta ratings

The Phase 9 stabilization patch implements these corrections as structured
review fields that still feed the existing backend correction path. This keeps
the review safe while making common STT corrections much faster.

Follow-up reminders also need special review attention. If the transcript or
assistant summary clearly says that inside sales should call, follow up, or
prepare something, BENNO should surface a pending `MockReminder` before final
confirmation. This should be robust against imperfect STT such as "Indienst" or
other near misses when the surrounding sentence still means inside-sales
follow-up.

## Core Safety Rules

- BENNO may suggest, but the application validates and decides.
- AI output is never written directly to the database.
- Corrections override previous assumptions.
- Final save requires explicit confirmation.
- New master data is not created automatically.
- Inside sales tasks are created when master data or follow-up work is needed.
