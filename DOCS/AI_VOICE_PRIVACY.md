# BENNO AI, Voice, And Privacy Direction

## Purpose

This document defines BENNO's current direction for AI providers, voice features, local models, and privacy.

It consolidates valid content from the archived German notes while keeping only current decisions.

## Provider Sequence

The current provider sequence is:

1. Build and stabilize the text workflow with Gemini.
2. Keep the provider abstraction compatible with OpenAI-style local APIs.
3. Add a local provider after the workflow is stable.
4. Compare local model behavior against the same demo scenarios.

Gemini is the first implementation provider because the current project path and available key make it the most practical first real AI integration.

The local provider direction is primarily motivated by privacy and data protection.

## Provider Abstraction

BENNO should not hard-code business logic to one provider.

The provider service should hide provider-specific details behind a stable application interface.

The application should be able to ask for:

- intent detection
- structured extraction
- assistant reply wording
- final review wording
- final report wording

The rest of the application should not need to know whether the response came from Gemini or a later local provider.

## AI Responsibility Boundary

The AI may:

- interpret free text
- propose extracted fields
- propose intent and confidence
- suggest a next assistant question
- draft a final report
- word the final review

The application must:

- validate all AI output
- decide which sections are missing
- validate codes and references
- enforce correction behavior
- enforce explicit confirmation
- decide whether saving is allowed
- write to the database
- create inside sales tasks

Guiding principle:

> The AI interprets and writes. The application validates and decides.

## Local Provider Direction

The local provider is planned after the Gemini workflow is stable.

Likely technical direction:

- OpenAI-compatible local API
- LM Studio or a similar local runtime
- same provider contract shape as Gemini

Local models may require:

- stricter prompts
- smaller tasks
- stronger backend validation
- more deterministic code-side flow control
- possible separation between chat wording and structured extraction

## Voice Strategy

Voice is a layer over the text workflow.

The target flow is:

```text
voice input -> STT -> text turn -> same chat workflow -> assistant text -> TTS -> voice output
```

Speech-to-text only replaces manual text input.

Text-to-speech only adds spoken output. It does not replace the visible text interface.

The core report workflow remains text-based internally.

## Hands-Free Target

The long-term product target is hands-free usage after the report has been started.

Scenario:

1. The field sales user leaves a customer meeting.
2. The user starts a new BENNO report.
3. The phone can stay in a car holder.
4. BENNO asks questions aloud.
5. The user answers by voice.
6. BENNO processes the transcribed text turn.
7. BENNO reads the final review aloud.
8. The user confirms or corrects.

The visible chat remains available as fallback and transparency layer.

## STT And TTS Candidates

Initial STT candidate:

- `primeline/whisper-large-v3-turbo-german`

STT fallback or performance paths:

- `primeline/whisper-tiny-german`
- faster-whisper
- whisper.cpp or GGML-based runtime

Initial TTS candidate:

- `Godelaune/Kokoro-82M-ONNX-German-Martin`

TTS fallback:

- Thorsten/Piper voices

These are test candidates, not final commitments.

## Privacy Direction

The MVP starts with mock data.

Even with mock data, the architecture should respect privacy principles from the beginning.

The project should not claim full production-grade GDPR compliance during the MVP. A safe statement is:

```text
The MVP considers privacy and GDPR principles from the beginning, but full production-grade GDPR compliance depends on final hosting, access control, retention rules, deletion workflows, processor agreements, and legal review.
```

## Audio Handling

Raw audio should not become a long-term business record.

Target behavior:

- frontend keeps audio only as recording/upload buffer
- backend processes audio for transcription
- transcript becomes the relevant chat input
- raw audio is discarded after transcription, completion, or cancellation
- generated TTS audio is not stored as a long-term archive

During development, temporary audio may exist for processing, but the product direction is no raw-audio archive.

## Persisted Data

Persisted MVP data:

- text chat history
- transcripts as chat messages
- structured report draft
- report status
- final confirmed visit report
- user context
- mock CRM/ERP references
- inside sales tasks

Not persisted as long-term records:

- raw audio archive
- generated TTS audio archive
- real customer data in the mock MVP
- real employee data in the mock MVP

## Provider And Privacy Risks

Main risks:

- AI extraction may be unreliable for free-form text.
- Local models may be weaker than Gemini for structured extraction.
- Long prompts may become expensive or slow.
- Sensitive content must not be logged unnecessarily.
- Raw audio must not accidentally become persistent business data.
- Provider switching must not change business rules.

Mitigation:

- keep the application in control
- validate all AI output
- use clear prompt contracts
- log carefully
- test with fixed demo scenarios
- add local provider only after the Gemini text workflow is stable
