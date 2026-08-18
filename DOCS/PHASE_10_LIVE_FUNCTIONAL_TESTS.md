# Phase 10 Live Functional Test Harness

Status: planned specification. The runner is not implemented yet.

## Purpose

Phase 10 should add automated live functional tests for BENNO's demo-critical
flows.

These tests are not normal deterministic regression tests. They are started
explicitly when the developer wants to exercise the real local demo stack:

- BENNO running locally
- Gemini as the configured AI provider
- Speaches as the local STT sidecar
- Kokoro/Martin as the local TTS sidecar
- optional Langfuse tracing

The goal is to provoke the fragile parts of the MVP on purpose and verify that
BENNO fails safely: no uncontrolled writeback, no Flask 500, clear
clarification or review correction, and useful traces for debugging.

## Test Boundary

Normal `pytest` remains fast and deterministic. It should keep using fake AI,
fake STT, fake TTS, and isolated databases unless a test is explicitly designed
as a live integration test.

Live functional tests are different:

- they may call Gemini
- they may call local Speaches and Kokoro containers
- they may create real Langfuse traces when enabled
- they may take longer and be rate-limit dependent
- they must be opt-in

The planned runner should use a dedicated command or script. The following
interface is illustrative and is not available yet:

```powershell
python scripts/run_live_demo_tests.py
```

or an equivalent Flask CLI command if that fits the implementation better.

## Required Environment

The live harness should check required services and configuration before
running scenarios:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `SPEACHES_BASE_URL`
- `KOKORO_BASE_URL`
- `VOICE_ENABLED=true`
- optional `LANGFUSE_ENABLED=true`
- optional Langfuse public key, secret key, and base URL

If a required service is missing, the harness should stop with a clear
preflight error instead of producing misleading scenario failures.

## Scenario Style

The scenarios should be automated but intentionally realistic and messy. They
should not be clean form-fill tests.

Good scenario inputs include:

- natural German sentences
- noisy or ambiguous wording
- STT-prone company and person names
- irrelevant small talk
- corrections in the middle of the flow
- qualitative ratings without exact numbers
- explicit "new interested party" or address cases without a company name
- inside-sales follow-up phrased in a way that STT may distort

## Initial Scenario Set

### 1. New Address Without Company Name

Input idea:

```text
Das ist ein neuer Interessent aus NRW.
```

Expected behavior:

- BENNO treats the AKL type as `Adresse`
- BENNO does not treat `Adresse`, `Lead`, or `Interessent` as the company name
- BENNO asks for the concrete company or address name
- no Mock-eNVenta writeback happens before review confirmation

### 2. Noisy STT Company Name

Input idea:

```text
Ich war vor Ort bei PerfSolar und habe mit Frau Müller gesprochen.
```

Expected behavior:

- transcript is stored as a normal user chat message
- Gemini may propose AKL name, visit type, and participant
- BENNO keeps the result reviewable
- if the name is uncertain or wrong, the review correction fields allow direct
  correction

### 3. Qualitative Ratings

Input idea:

```text
Zufriedenheit war eher positiv, technisch sind sie unsicher,
kaufmännisch ist es spannend, Priorität vielleicht sieben.
```

Expected behavior:

- explicit numeric rating values are accepted
- qualitative rating clues are kept as clarification context
- BENNO does not invent final rating numbers
- BENNO asks for missing numeric values or explicit "not assessable" statements

### 4. Inside-Sales Follow-Up With Near Miss

Input idea:

```text
Der Indienst soll nächste Woche nochmal nachfassen.
```

Expected behavior:

- BENNO recognizes this as inside-sales follow-up when the sentence context is
  clear
- review shows a pending `MockReminder`
- confirm creates exactly one reminder through the gateway

### 5. Irrelevant Small Talk

Input idea:

```text
Der Kaffee war gut, aber fachlich ging es um Forecast, Muster und eine
mögliche Kooperation.
```

Expected behavior:

- irrelevant small talk is not promoted into the eNVenta target fields
- relevant discussion content remains available for `Info`, `Ziel/Thema`, or
  `Vereinbarung`

### 6. Mid-Flow Correction

Input idea:

```text
Nein, nicht PerfSolar, eigentlich SunSolar.
```

Expected behavior:

- BENNO treats the sentence as correction
- the relevant AKL name is updated when the target is clear
- unrelated fields are not overwritten silently
- review remains the final safety boundary

## Voice Harness Strategy

The first live harness does not need real microphone automation.

It may generate audio through Kokoro/Martin from predefined German scenario
sentences, then submit that audio to BENNO's voice endpoint. This exercises the
real TTS -> STT -> transcript -> Gemini -> backend decision loop while staying
repeatable enough for development.

Later, browser-level tests may add microphone simulation or Playwright flows,
but that is not required for the first Phase 10 harness.

## Langfuse Evidence

When Langfuse is enabled, every live scenario should try to capture or print
enough identifiers to inspect the run:

- scenario name
- chat id
- final report id, if created
- Langfuse trace or session id, if available
- accepted section keys
- rejected or ignored AI proposal keys, if available
- current missing sections
- final status

The point is not only to prove that the UI can be clicked. The trace should
make it visible where the real chain behaved well or badly:

- STT transcript quality
- Gemini structured proposal
- backend validation decision
- clarification or review correction
- Mock-eNVenta writeback boundary

## Pass Criteria

A live scenario passes when:

- the app does not return a Flask 500
- the report loop remains usable
- uncertain information triggers a clarification or review correction path
- no Mock-eNVenta writeback occurs before explicit confirmation
- expected final artifacts are created only after confirmation
- Langfuse traces are available when tracing is enabled
- the script produces a readable summary for the developer

## Fail Criteria

A live scenario fails when:

- BENNO crashes with an unhandled exception
- a report is saved before explicit confirmation
- an unknown AKL name is treated as complete without clarification
- qualitative ratings are silently converted into invented numbers
- STT/TTS/Gemini errors leave the user without text fallback
- the run cannot be inspected afterward

## Expected Output

The harness should produce a concise summary such as:

```text
PASS new-address-without-company-name
  chat_id: 14
  status: in_progress
  expected_question: company/address name
  trace_id: ...

FAIL qualitative-ratings
  chat_id: 15
  reason: priority was accepted, but satisfaction was invented as 8
  trace_id: ...
```

The output may also be written to a local ignored artifact file, for example
under `instance/live_test_runs/`, but it must not commit transcripts, audio, or
secrets to Git.

## Out Of Scope

The first Phase 10 live harness should not implement:

- production HTTPS deployment
- Postgres migration
- real eNVenta access
- real customer or employee data
- complete STT model benchmarking
- true realtime streaming, barge-in, or interrupt handling
- native mobile app tests
