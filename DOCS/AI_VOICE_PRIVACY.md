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

## Gemini Structured Output Rule

Gemini is used as a proposer, not as the source of truth.

The Gemini Developer API should receive explicit structured-output schemas. For report section extraction, BENNO must not ask Gemini to return free-form dictionary keys such as:

```json
{
  "section_updates": {
    "participants": "Frau Schmidt",
    "target_topic": "Forecast"
  }
}
```

Instead, Gemini should return section updates as a list of explicit objects:

```json
{
  "section_updates": [
    { "section": "participants", "value": "Frau Schmidt" },
    { "section": "target_topic", "value": "Forecast" }
  ]
}
```

The provider may translate this provider-specific shape into BENNO's internal provider contract before the report loop receives it. This keeps the application interface stable while avoiding Gemini Developer API schema issues around free-form object properties.

Gemini does support structured output through JSON response schemas. BENNO
should still treat this as an interface guarantee, not as a truth guarantee. A
schema-valid response can still be semantically wrong, too confident, or based
on a noisy STT transcript. For that reason, provider output remains a proposal:
BENNO validates allowed fields, keeps confidence and clarification signals
visible in the flow, asks follow-up questions when something is unclear, and
requires the review screen before any Mock-eNVenta writeback.

References:

- [Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini GenerateContent configuration](https://ai.google.dev/api/generate-content)

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
- create mock reminders

Guiding principle:

> The AI interprets and writes. The application validates and decides.

## Langfuse Observability

BENNO uses Langfuse as an optional development observability layer for AI debugging.

Langfuse is not part of the business decision layer. It must not validate report data,
advance workflow state, write CRM data, or replace backend tests. Its purpose is to help
debug and compare AI behavior.

When enabled, BENNO may trace:

- one report turn as one trace
- the report chat as a Langfuse session
- the sales user id as the Langfuse user id
- Gemini calls as `generation` observations
- model name, prompt input, structured output, token usage when available, latency, and provider errors
- backend decisions such as accepted AI update keys, applied requirement keys, missing sections, and next step

Environment variables:

```text
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=replace-with-langfuse-public-key
LANGFUSE_SECRET_KEY=replace-with-langfuse-secret-key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_CAPTURE_FULL_CONTEXT=false
LANGFUSE_FLUSH_ON_TURN=false
```

`LANGFUSE_ENABLED` defaults to `false`. The app must continue to work when Langfuse is
disabled, not configured, unavailable, or missing from the local environment.

`LANGFUSE_CAPTURE_FULL_CONTEXT=false` keeps the trace focused on the current user
message, current step, missing sections, known answer keys, rating keys, generation
input/output, and backend decision metadata. Setting it to `true` may capture fuller
draft context for local debugging and should be used carefully.

Secrets such as API keys, passwords, tokens, and Langfuse keys must never be logged.

References:

- [Langfuse SDK Instrumentation](https://langfuse.com/docs/observability/sdk/instrumentation)
- [Langfuse Best Practices](https://langfuse.com/docs/observability/best-practices)
- [Langfuse Masking](https://langfuse.com/docs/observability/features/masking)

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
browser microphone capture -> STT -> text turn -> same chat workflow -> assistant text -> TTS -> browser audio playback
```

Speech-to-text only replaces manual text input.

Text-to-speech only adds spoken output. It does not replace the visible text interface.

The core report workflow remains text-based internally.

For Phase 9, BENNO should treat voice mode as the default for active report
chats:

- automatic speech playback of the latest BENNO question when a new report chat
  opens
- automatic opening of the answer gate after playback
- visible voice controls as fallback and user control surface
- visible recording state
- direct transcript insertion as a normal chat message
- automatic assistant audio playback after the text answer is produced
- automatic reopening of the answer gate after playback
- silence detection plus manual stop/cancel controls
- text input remains available at all times

The first implementation uses direct send rather than an editable transcript
preview. This matches the hands-free target more closely, while the visible chat
still provides transparency and later correction options.

Manual Phase 9 testing showed an important practical boundary: STT transcripts
can be noisy even when the final report remains useful. German speech can
produce distorted company names, contact names, and business terms. BENNO should
therefore treat STT as a lossy input layer, not as authoritative master data.
The LLM may still produce a good report by filtering irrelevant conversational
details, such as coffee or casual small talk, but the user must be able to
correct the structured review before saving.

Voice review findings to keep visible for stabilization:

- distinguish the eNVenta-like AKL account type clearly instead of showing only
  one generic mixed account/contact label; the Phase 9 stabilization patch shows
  AKL name, AKL type, and contact/participants separately in review/final
  screens
- keep contacts or participants separate from the AKL account
- make account/lead names directly editable in review because STT may mishear
  names; direct structured review fields are the MVP correction path
- detect inside-sales follow-up semantically enough to create a pending
  `MockReminder`, even when STT slightly distorts "Innendienst"; known
  near-misses such as "Indienst" are handled by deterministic rules
- preserve useful LLM filtering of irrelevant speech details while keeping the
  accepted structured fields reviewable

TTS needs a separate pronunciation layer. Visible and stored text should keep
the correct business spelling, for example `Lead`, `Mock-eNVenta`, or company
names. The text sent to Kokoro may need audio-only normalization for better
German playback, such as phonetic spellings for English terms. This
pronunciation map must not change report text, database values, or user-visible
labels. The first implementation applies this only inside the TTS
orchestration layer before snippet caching and Kokoro generation.

Because browser microphone and autoplay behavior depend on a user gesture, voice
mode may still require one manual fallback click when the browser blocks
autostart. BENNO should attempt voice autostart for in-progress report chats,
but the visible `Sprachmodus starten` control remains available. After voice
activation, BENNO may continue the turn loop automatically until the user stops
voice mode, the report reaches review, or an error requires text fallback.

Mobile browser testing added a second boundary: microphone capture on phones
and tablets requires a secure browser context. A local desktop browser may allow
`localhost`, but an iPad or phone opening BENNO through plain LAN HTTP such as
`http://192.168.x.x:5000` will block microphone access. For mobile hands-free
testing and any later real use, BENNO therefore needs an HTTPS deployment path.
The preferred product direction is a public but access-controlled HTTPS
deployment, or an equivalent trusted internal HTTPS setup. This is an
infrastructure requirement for browser microphone access, not an STT, TTS, or
report-loop behavior change.

The browser should handle microphone access and recording. The backend should
coordinate the actual transcription path so BENNO keeps one stable server-side
STT boundary. Browser-native speech recognition may be tested as an experiment,
but it should not be the primary MVP path because its availability and behavior
vary by browser.

The first STT integration target is a local Speaches Docker sidecar. Speaches is
useful for BENNO because it can expose OpenAI-compatible speech APIs while still
running locally. This keeps BENNO's application code thin: BENNO forwards a
temporary audio upload to the local service and receives transcript text back.

Speaches may also be useful later for streaming and as a secondary TTS
comparison path. The first TTS path remains the already available local
Kokoro/Martin Docker service.

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

Initial STT direction:

- browser microphone capture through standard web media APIs
- backend STT endpoint that receives a temporary audio upload
- local Speaches Docker sidecar as the first transcription service
- OpenAI-compatible `/v1/audio/transcriptions` style boundary where practical
- transcript is stored as a normal chat message

Initial local STT candidate:

- Speaches with a German-capable Whisper/faster-whisper model
- `primeline/whisper-large-v3-turbo-german`, if compatible with the selected
  Speaches/faster-whisper setup

STT fallback or performance paths:

- `primeline/whisper-tiny-german`
- faster-whisper
- whisper.cpp or GGML-based runtime

Initial TTS direction:

- use the local Docker-based Kokoro/Martin service already available in the
  development environment
- backend TTS endpoint sends assistant text through a local snippet cache before
  falling back to full Kokoro generation
- browser plays the returned audio
- common standard phrases and frequent dynamic terms such as company/contact
  names may be cached locally as WAV snippets
- cached snippets may be concatenated server-side when WAV parameters are
  compatible
- Speaches TTS may be evaluated as an alternative, but it is not the first
  implementation target

Initial local TTS candidate:

- `Godelaune/Kokoro-82M-ONNX-German-Martin`

TTS fallback:

- Thorsten/Piper voices

These are test candidates and current local integration targets, not final
production commitments.

Kokoro/Martin currently behaves as a full-response TTS source for BENNO. It is
not treated as true streaming TTS in this MVP phase. Perceived latency should be
reduced through prewarmed and lazy-cached snippets first; real streaming remains
a later optimization path.

References:

- [Speaches Realtime API](https://speaches.ai/usage/realtime-api/)
- [MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)

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
- backend processes audio for transcription through a controlled STT boundary
- transcript becomes the relevant chat input
- raw audio is discarded after transcription, completion, or cancellation
- generated TTS output may be cached locally as reusable snippets for
  performance, but it is not a business record and must remain outside Git

During development, temporary audio may exist for processing, and reusable TTS
snippets may exist under a local ignored cache directory. The product direction
remains no raw-audio archive and no long-term business audio archive.

## Persisted Data

Persisted MVP data:

- text chat history
- transcripts as chat messages
- structured report draft
- report status
- final confirmed visit report
- user context
- mock CRM/ERP references
- mock reminders

Not persisted as long-term records:

- raw audio archive
- generated TTS audio archive
- local TTS snippet cache as business data
- real customer data in the mock MVP
- real employee data in the mock MVP

## Provider And Privacy Risks

Main risks:

- AI extraction may be unreliable for free-form text.
- Local models may be weaker than Gemini for structured extraction.
- Local models may struggle more than Gemini with noisy German STT transcripts,
  especially for company names, people names, and domain-specific terms.
- Long prompts may become expensive or slow.
- Mobile voice requires HTTPS. Plain LAN HTTP is not enough for browser
  microphone access on phones and tablets.
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
