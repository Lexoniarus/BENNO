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


ANALYSIS_SYSTEM_INSTRUCTION = """
You support BENNO, a B2B visit report assistant.

You are the extractor and observer role.
Return only the structured response requested by the schema.
You may interpret and propose values, but the application validates and decides.
Compare the user message against the full report_requirements checklist.
The checklist shows every needed report field, its current status, current value,
question, and section.
Extract every explicitly mentioned allowed section, not only the current one.
One message may satisfy several requirements at once, even if they are not the
current_step.
Do not propose updates for requirements that are completed or not_applicable
unless the user's intent is correction and the user explicitly targets them.
Preserve German spelling exactly, including ä, ö, ü, Ä, Ö, Ü, and ß.
Do not rewrite umlauts as ae, oe, ue, or ss.
Do not infer unstated agreements, next actions, ratings, offers, or orders.
If the user explicitly says there is no offer, no order, or the account is a lead,
use "keiner" for offer_reference and order_reference when appropriate.
If the user mentions inside sales calling or following up, extract that as
next_action if the next action is still missing.
Ratings may be answered together. Extract every explicitly stated rating clue
into the matching eNVenta rating section. If the user says a rating is too early,
keep that wording as the value instead of inventing a number.
Also propose the next useful German assistant question in suggested_next_question.
Set suggested_next_section to the requirement key that should be asked next after
your proposed section_updates are applied. Ask only for one next requirement, or
one compact rating block when ratings are next. If no useful suggestion is safe,
leave suggested_next_question empty.

Allowed intents:
answer, correction, additional_info, confirmation, rejection, repeat, cancel, unknown.

Allowed section update keys:
visit_context, visit_type, participants, visit_date, target_topic, info_text,
agreement_text, next_action, next_appointment_date, offer_reference,
order_reference, strength_text, weakness_text, reminders,
customer_satisfaction_rating, technical_attractiveness_rating,
commercial_attractiveness_rating, priority_rating.

Return section_updates as an array of objects with exactly these fields:
section, value.
Example:
[
  {"section": "participants", "value": "Frau Schmidt"},
  {"section": "target_topic", "value": "Forecast"}
]
Do not return section_updates as an object with dynamic section keys.

German extraction examples:
- "Ich war bei PerfSolar" -> visit_context = "PerfSolar".
- "mit Frau Müller" -> participants = "Frau Müller".
- "über den Forecast gesprochen" -> target_topic = "Forecast".
- "über eine mögliche Kooperation gesprochen" -> target_topic = "mögliche Kooperation".
- "Wir haben uns über den Forecast unterhalten" -> target_topic = "Forecast".
- "Sie wollen Muster und wir reden in 2 Wochen drüber" ->
  agreement_text = "Kunde möchte Muster"; next_action = "Gespräch in 2 Wochen".
- "nee die sind Lead, da muss der Innendienst nochmal anrufen" ->
  offer_reference = "keiner"; order_reference = "keiner";
  reminders = "Innendienst soll nochmal anrufen".
- "Zufriedenheit 8, technische Attraktivität 7, kaufmännisch 6, Priorität 9" ->
  customer_satisfaction_rating = "8"; technical_attractiveness_rating = "7";
  commercial_attractiveness_rating = "6"; priority_rating = "9".
""".strip()

NEXT_QUESTION_SYSTEM_INSTRUCTION = """
You support BENNO, a B2B visit report assistant.

You are the conversation role.
Write only the next German assistant message for the sales user.
Use the validated backend state, not untrusted guesses.
Use report_requirements and next_step to understand the complete target shape.
Do not ask again for requirements marked completed or not_applicable.
Ask exactly one concise question or combined question.
Use next_step as the target of the message.
Do not ask for every future missing field.
If next_step is not a rating step, ask only about next_step.
If next_step is a rating step, ask for all missing ratings in one natural block.
Do not invent facts, do not claim that anything was saved, and do not mention JSON.
If only one field is missing, ask only for that field.
Keep the tone professional, friendly, and brief.
""".strip()

REVIEW_SYSTEM_INSTRUCTION = """
You support BENNO, a B2B visit report assistant.

Write concise German review wording from validated draft data.
Do not invent facts. Do not say that anything was saved or submitted.
""".strip()

FINAL_REPORT_SYSTEM_INSTRUCTION = """
You support BENNO, a B2B visit report assistant.

Write clear professional German CRM visit report text from validated draft data.
Do not invent facts.
""".strip()


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
        prompt = _build_analysis_content(context, message_text)
        response = self._generate_structured_content(
            prompt=prompt,
            response_schema=GeminiMessageAnalysis,
            system_instruction=ANALYSIS_SYSTEM_INSTRUCTION,
            temperature=0.1,
        )
        if response is None:
            return None

        try:
            return _convert_gemini_analysis(response)
        except ValueError as error:
            message = "Gemini returned invalid message analysis."
            raise AiProviderError(message) from error

    def draft_next_question(self, question_context: dict[str, Any]) -> str | None:
        """Ask Gemini for the next conversational assistant question."""
        prompt = _build_next_question_prompt(question_context)
        return self._generate_text(
            prompt=prompt,
            system_instruction=NEXT_QUESTION_SYSTEM_INSTRUCTION,
            temperature=0.3,
        )

    def draft_review_text(self, draft_context: dict[str, Any]) -> str | None:
        """Ask Gemini for concise review wording."""
        prompt = _build_review_prompt(draft_context)
        return self._generate_text(
            prompt=prompt,
            system_instruction=REVIEW_SYSTEM_INSTRUCTION,
            temperature=0.2,
        )

    def draft_final_report_text(self, draft_context: dict[str, Any]) -> str | None:
        """Ask Gemini for a final visit report text."""
        prompt = _build_final_report_prompt(draft_context)
        return self._generate_text(
            prompt=prompt,
            system_instruction=FINAL_REPORT_SYSTEM_INSTRUCTION,
            temperature=0.2,
        )

    def _generate_structured_content(
        self,
        prompt: str,
        response_schema: type[BaseModel],
        system_instruction: str,
        temperature: float,
    ) -> dict[str, Any] | BaseModel | None:
        config = self._types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction,
            temperature=temperature,
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

    def _generate_text(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float,
    ) -> str | None:
        config = self._types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
        except Exception as error:
            raise AiProviderError("Gemini text generation failed.") from error

        response_text = getattr(response, "text", None)
        if response_text is None:
            return None

        normalized_text = response_text.strip()
        return normalized_text or None


def _build_analysis_content(context: dict[str, Any], message_text: str) -> str:
    context_json = json.dumps(context, ensure_ascii=False, default=str, indent=2)
    return f"""
Context:
{context_json}

User message:
{message_text}
""".strip()


def _build_next_question_prompt(question_context: dict[str, Any]) -> str:
    context_json = json.dumps(
        question_context,
        ensure_ascii=False,
        default=str,
        indent=2,
    )
    return f"""
Validated conversation state:
{context_json}
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
relevant references, strength/weakness notes, and eNVenta ratings when available.

Draft:
{context_json}
""".strip()
