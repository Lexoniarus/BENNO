"""Gemini AI provider implementation."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from benno.enums import UserIntent
from benno.services.ai_provider import AiMessageAnalysis, AiProviderError


class GeminiSectionUpdate(BaseModel):
    """Provider-facing section update without free-form object keys."""

    model_config = ConfigDict(extra="ignore")

    section: str | None = None
    value: str | None = None


class GeminiMessageAnalysis(BaseModel):
    """Gemini-compatible structured proposal for one user message."""

    model_config = ConfigDict(extra="ignore")

    intent: UserIntent = UserIntent.UNKNOWN
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    target_sections: list[str] = Field(default_factory=list)
    section_updates: list[GeminiSectionUpdate] = Field(default_factory=list)
    suggested_next_section: str | None = None
    suggested_next_question: str | None = None


class GeminiService:
    """Small wrapper around the Google GenAI SDK."""

    def __init__(self, api_key: str, model: str) -> None:
        """Create a Gemini provider for BENNO."""
        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise AiProviderError("Google GenAI SDK is not installed.") from error

        try:
            self._client = genai.Client(api_key=api_key)
        except Exception as error:
            raise AiProviderError("Gemini client initialization failed.") from error

        self._model = model
        self._types = types

    def analyze_report_message(
        self,
        context: dict[str, Any],
        message_text: str,
    ) -> AiMessageAnalysis | None:
        """Ask Gemini for a controlled analysis of one report message."""
        prompt = _build_analysis_prompt(context, message_text)
        response = self._generate_structured_content(prompt, GeminiMessageAnalysis)
        if response is None:
            return None

        try:
            return _convert_gemini_analysis(response)
        except ValueError as error:
            message = "Gemini returned invalid message analysis."
            raise AiProviderError(message) from error

    def draft_review_text(self, draft_context: dict[str, Any]) -> str | None:
        """Ask Gemini for concise review wording."""
        prompt = _build_review_prompt(draft_context)
        return self._generate_text(prompt)

    def draft_final_report_text(self, draft_context: dict[str, Any]) -> str | None:
        """Ask Gemini for a final visit report text."""
        prompt = _build_final_report_prompt(draft_context)
        return self._generate_text(prompt)

    def _generate_structured_content(
        self,
        prompt: str,
        response_schema: type[BaseModel],
    ) -> dict[str, Any] | BaseModel | None:
        config = self._types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.1,
        )
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
        except Exception as error:
            raise AiProviderError("Gemini message analysis failed.") from error

        parsed_response = getattr(response, "parsed", None)
        if parsed_response is not None:
            return parsed_response

        response_text = getattr(response, "text", None)
        if not response_text:
            return None

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as error:
            raise AiProviderError("Gemini returned malformed JSON.") from error

    def _generate_text(self, prompt: str) -> str | None:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
        except Exception as error:
            raise AiProviderError("Gemini text generation failed.") from error

        response_text = getattr(response, "text", None)
        if response_text is None:
            return None

        normalized_text = response_text.strip()
        return normalized_text or None


def _build_analysis_prompt(context: dict[str, Any], message_text: str) -> str:
    context_json = json.dumps(context, ensure_ascii=False, default=str, indent=2)
    return f"""
You support BENNO, a B2B visit report assistant.

Return only the structured response requested by the schema.
You may interpret and propose values, but the application validates and decides.
Extract every explicitly mentioned allowed section, not only the current one.
Preserve German spelling exactly, including ä, ö, ü, Ä, Ö, Ü, and ß.
Do not rewrite umlauts as ae, oe, ue, or ss.
Do not infer unstated outcomes, next actions, ratings, offers, or orders.
If the user explicitly says there is no offer, no order, or the account is a lead,
use "keiner" for offer_reference and order_reference when appropriate.
If the user mentions inside sales calling or following up, extract that as
next_action if the next action is still missing.
Ratings may be answered together. Extract every explicitly stated rating clue
into the matching rating_* section. If the user says a rating is too early,
keep that wording as the value instead of inventing a number.

Allowed intents:
answer, correction, additional_info, confirmation, rejection, repeat, cancel, unknown.

Allowed section update keys:
customer_context, contacts, visit_reason, summary, outcome, next_action,
offer_reference, order_reference, rating_sales_opportunity, rating_meeting_mood,
rating_priority, rating_closing_probability, rating_need_for_action,
rating_customer_satisfaction.

Return section_updates as an array of objects with exactly these fields:
section, value.
Example:
[
  {{"section": "contacts", "value": "Frau Schmidt"}},
  {{"section": "visit_reason", "value": "Forecast"}}
]
Do not return section_updates as an object with dynamic section keys.

German extraction examples:
- "Ich war bei PerfSolar" -> customer_context = "PerfSolar".
- "mit Frau Müller" -> contacts = "Frau Müller".
- "über den Forecast gesprochen" -> visit_reason = "Forecast".
- "über eine mögliche Kooperation gesprochen" -> visit_reason = "mögliche Kooperation".
- "Wir haben uns über den Forecast unterhalten" -> visit_reason = "Forecast".
- "Sie wollen Muster und wir reden in 2 Wochen drüber" ->
  outcome = "Kunde möchte Muster"; next_action = "Gespräch in 2 Wochen".
- "nee die sind Lead, da muss der Innendienst nochmal anrufen" ->
  offer_reference = "keiner"; order_reference = "keiner";
  next_action = "Innendienst soll nochmal anrufen".
- "Priorität 7, Stimmung gut, Abschluss noch zu früh" ->
  rating_priority = "7"; rating_meeting_mood = "gut";
  rating_closing_probability = "zu früh".

Only provide suggested_next_question if suggested_next_section is exactly the
next report section the question is about.
Write suggested_next_question in German. Keep it short, natural, and dialog-like.
Ask exactly one next question. You may briefly acknowledge already detected
information before the question. Do not invent facts or pretend anything was
saved.

Context:
{context_json}

User message:
{message_text}
""".strip()


def _convert_gemini_analysis(
    response: dict[str, Any] | BaseModel,
) -> AiMessageAnalysis:
    gemini_analysis = GeminiMessageAnalysis.model_validate(response)
    section_updates = {}
    for section_update in gemini_analysis.section_updates:
        if not isinstance(section_update.section, str):
            continue
        if not isinstance(section_update.value, str):
            continue

        section = section_update.section.strip()
        value = section_update.value.strip()
        if section and value:
            section_updates[section] = value

    return AiMessageAnalysis(
        intent=gemini_analysis.intent,
        intent_confidence=gemini_analysis.intent_confidence,
        target_sections=gemini_analysis.target_sections,
        section_updates=section_updates,
        suggested_next_section=gemini_analysis.suggested_next_section,
        suggested_next_question=gemini_analysis.suggested_next_question,
    )


def _build_review_prompt(draft_context: dict[str, Any]) -> str:
    context_json = json.dumps(draft_context, ensure_ascii=False, default=str, indent=2)
    return f"""
Write a short, human-readable German review summary for this B2B visit report draft.
Do not invent facts. Do not say that anything was saved or submitted.

Draft:
{context_json}
""".strip()


def _build_final_report_prompt(draft_context: dict[str, Any]) -> str:
    context_json = json.dumps(draft_context, ensure_ascii=False, default=str, indent=2)
    return f"""
Write the final CRM visit report text for this B2B field sales visit.
Use clear professional German. Do not invent facts.
Include customer context, participants, reason, summary, outcome, next action,
relevant references, and sales ratings when available.

Draft:
{context_json}
""".strip()
