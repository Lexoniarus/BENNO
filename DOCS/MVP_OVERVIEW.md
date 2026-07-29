# BENNO: Voice-Guided Visit Report Assistant

## What Does BENNO Mean?

BENNO is the project name for the visit report assistant.

BENNO stands for:

**B2B Encounter Notes and Next-step Organizer**

The name describes the product idea directly: BENNO helps capture notes from B2B customer meetings and organize the next steps that follow from them.

The name is also intentionally human. The application should not feel like another form or a complicated CRM module. It should feel more like a calm digital companion that helps a field sales representative document a customer visit properly.

You can think of BENNO as a quiet co-driver for field sales: it listens, asks follow-up questions, sorts the information, and helps produce a usable visit report.

## What Is The Project About?

BENNO is a digital assistant for B2B field sales representatives.

Field sales users visit customers, conduct meetings, follow up on offers, collect new requirements, and agree on next steps. After those meetings, they usually need to write a visit report so the company can understand what was discussed and what should happen next.

BENNO helps with exactly that.

The idea is that the field sales user should not have to type a long report on a phone or recreate the meeting later from memory. Instead, the user starts the app, freely describes the meeting, answers a few targeted follow-up questions, and receives a clean visit report proposal.

The system does not save the report automatically. First, everything is summarized. Only after the user explicitly confirms the result is the report saved or later written back to a CRM/ERP system.

## Which Problem Does It Solve?

Visit reports are important in sales, but they are often treated as an annoying administrative task.

Common problems are:

- Reports are written hours or days after the meeting.
- Details from the conversation are forgotten.
- Reports differ widely in quality and detail.
- Important next steps are missed.
- Inside sales does not know exactly what was discussed with the customer.
- Customer, offer, and contact information remains incomplete in the system.

BENNO is meant to close this gap. Fresh knowledge from customer meetings should be captured right after the meeting and turned into a usable structure.

## Typical Usage Scenario

A field sales representative has just left a customer meeting.

They get into the car, start the app, and create a new visit report. From that point on, the target experience should require as little manual interaction as possible:

1. The app asks what the meeting was about.
2. The field sales user freely describes what happened.
3. The app detects names, topics, results, and next steps.
4. If something is missing or unclear, the app asks targeted follow-up questions.
5. The user can correct information at any time.
6. The app checks whether the important visit report fields are covered.
7. At the end, the app reads or displays the full report.
8. The user confirms or corrects it.
9. Only after confirmation is the report saved.

The interaction should feel like a guided conversation, not like filling out a form.

## What Does Hands-Free Mean?

The full product goal is a mostly hands-free workflow.

After starting the report, the user should ideally not need to type. The app speaks to the user, listens to the answers, asks follow-up questions, and reads the final summary.

This is especially useful for field sales representatives, because they often move between appointments. A report can be created right after the meeting while the memory is still fresh, without the user having to type long text on a smartphone.

The visible text interface remains important. Even in the hands-free target experience, the user can still see what was understood and intervene by text if needed.

## What Does The AI Do?

The AI is not supposed to simply invent a finished report.

Its job is to help turn free language into a usable report. This includes:

- reading or listening to the user's free description
- detecting important information such as customer, contact, meeting reason, and outcome
- noticing when required information is missing
- asking for missing visit report fields
- asking targeted follow-up questions
- processing corrections
- suggesting the four eNVenta-oriented ratings for satisfaction, technical attractiveness, commercial attractiveness, and priority
- wording the final report clearly

Business decisions should not be blindly delegated to the AI. The application checks what may be saved, which information is missing, and whether the user has really confirmed the final result.

In short:

The AI helps understand and write. The application provides structure, validation, and confirmation.

## What Is The System Not?

BENNO is not a CRM system.

A CRM or ERP system is where companies manage customers, contacts, offers, orders, and sales activities. BENNO should not replace such a system.

BENNO is a capture and handover layer.

It helps capture a visit report comfortably, structure it, and later hand it over or write it back to an existing system. For the project, this starts with a small mock database. Later, the structure should align with eNVenta once the real visit report fields are available.

The relevant CRM/ERP product context is eNVenta by the eNVenta Group:

https://www.enventa-group.com/

## Why Start With Text And Add Voice Later?

The full goal is voice-guided and mostly hands-free.

Still, the first technical step is text-based. The user writes into a chat, and the app answers as text.

That may sound less impressive, but it is the right order. The most important part is not the microphone. The important part is the workflow behind it:

- What was understood?
- Which information is still missing?
- Which follow-up question makes sense?
- How are corrections handled?
- When is the report complete?
- What does final confirmation look like?

Once this workflow is stable, voice can be added:

- Speech input is converted into text.
- The same report workflow processes that text.
- The app response is read aloud.

This keeps the core workflow the same whether the user types or speaks.

## How Does BENNO Handle CRM Fields?

A visit report is not only a well-written text.

In a CRM or ERP system, specific fields need to be filled. Examples are customer, contact, visit date, reason, outcome, next step, follow-up date, and offer reference.

BENNO should not ask for these fields like a rigid form. Instead, it should detect which information is already present in the conversation.

If the field sales user already mentions the customer, the contact person, and the next step in the first description, BENNO should not ask for those details again.

If something is missing, BENNO asks specifically:

> When should the follow-up happen?

or:

> Was this related to an existing offer?

Step by step, this creates a report that reads naturally and still covers the required CRM fields.

## What Happens To The Finished Report?

At the end, BENNO should hand over the confirmed visit report to the appropriate system.

In the project, this first happens with example data. Later, the workflow should support writing the completed visit report fields and the final text back toward eNVenta or another CRM/ERP system.

That means:

- The field sales user speaks or writes the report.
- BENNO turns it into structured information.
- BENNO shows the finished report for review.
- The user confirms it.
- Only then are the report and fields saved or handed over.

The field sales user stays in control. The AI may prepare the result, but it does not decide on its own what becomes final system data.

## What Is Created At The End?

The result is a visit report that is useful for humans and for a later CRM/ERP system.

The report can include:

- which AKL account or address context is involved
- who participated in the conversation
- why the meeting took place
- what was discussed
- what the outcome was
- what should happen next
- whether an offer or order is relevant
- how the case is rated
- whether inside sales needs to do something

If a new contact person is mentioned, BENNO does not simply create that contact automatically. Instead, it can create a task for inside sales, such as: "Please check or complete this contact."

This helps avoid uncontrolled or incorrect master data.

## Follow-Ups And Inside Sales Tasks

Follow-ups and next-step tasks are an important part of the project.

Not every visit report is finished when it is saved. Customer meetings often create follow-up work:

- The customer should be called next week.
- An offer should be created or adjusted.
- A new contact person needs to be checked.
- Master data is missing or unclear.
- Inside sales needs to clarify details.

BENNO should detect this follow-up work and turn it into simple eNVenta-like reminders. Older inside-sales-task wording belongs to early scaffolding, not the current Phase 6 target.

Example:

The field sales user says:

> The customer wants an adjusted offer. Inside sales should clarify the technical details again.

BENNO should then not only write a visit report. It should also record that this creates a task for inside sales.

This means the project is not only about documentation. It is also about making sure something actually happens after the customer meeting.

## Example

A field sales user says:

> I just visited NordTech and spoke with Ms. Keller. It was about the open offer for the framework agreement. The mood was good, but she wants to discuss the terms with purchasing. I should follow up next week.

BENNO could answer:

> I understood that the meeting was with NordTech and Ms. Keller. It was about an open offer for the framework agreement. The meeting was positive, but the customer wants to discuss the terms internally with purchasing. The next step is to follow up next week. Is that correct?

If the user says:

> Not Ms. Keller, Mr. Becker.

the correction is applied. After that, the app continues at the right point.

If something is still missing, BENNO asks specifically:

> Should I use next Tuesday as the follow-up date?

At the end, BENNO provides a complete summary:

> I would save the following visit report: ...

It may also say:

> In addition, a follow-up reminder for next week will be created.

Only when the user says:

> Yes, save it.

is the report actually saved.

## Privacy Direction

Gemini is used for the first stable implementation because it is the current practical provider choice for testing the report workflow with a real AI service.

Once the workflow works, the project should evaluate how much can be run locally. That means the AI should run on controlled infrastructure or through a local interface wherever possible, instead of sending sensitive content to external services long term.

The reason is privacy.

Real visit reports may contain confidential information: customer names, contacts, prices, offers, problems, opportunities, and internal assessments. The long-term direction is therefore to process as much as possible locally and under control.

The project itself starts with mock data, meaning invented customers and example data.

## Why Is This Useful?

The value is not that "some AI writes a text."

The value is that the field sales user has less friction:

- They document directly after the meeting.
- They type less.
- The report becomes more complete.
- The company gets more consistent information.
- Follow-up tasks are less likely to be lost.
- Inside sales can continue working more effectively.

BENNO connects two worlds:

On one side, a natural conversation with the user. On the other side, structured documentation that can later fit into a CRM/ERP system.

## Short Version

BENNO is a voice-guided assistant for B2B field sales visit reports.

After a customer meeting, the field sales user should be able to freely describe what happened. The app detects important information, asks for missing details, processes corrections, and creates a clean report. At the end, everything is shown or read aloud. Only after explicit confirmation is the report saved.

The first technical step is a text chat. The actual product goal is a mostly hands-free workflow with speech input and speech output.
