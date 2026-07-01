"""Gemini AI provider implementation."""

from __future__ import annotations

import json
from typing import Any

from benno.services.ai_provider import AiMessageAnalysis, AiProviderError


class GeminiService:
    """Small wrapper around the Google GenAI SDK."""

    def __init__(self, api_key: str, model: str) -> None:
        """Create a Gemini provider for BENNO."""
        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise AiProviderError("Google GenAI SDK is not installed.") from error

        self._client = genai.Client(api_key=api_key)
        self._types = types
        self._model = model

    def analyze_report_message(
        self,
        context: dict[str, Any],
        message_text: str,
    ) -> AiMessageAnalysis | None:
        """Ask Gemini for a controlled analysis of one report message."""
        prompt = _build_analysis_prompt(context, message_text)
        response = self._generate_structured_content(prompt, AiMessageAnalysis)
        if response is None:
            return None

        try:
            return AiMessageAnalysis.model_validate(response)
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
        response_schema: type[AiMessageAnalysis],
    ) -> dict[str, Any] | AiMessageAnalysis | None:
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

Allowed intents:
answer, correction, additional_info, confirmation, rejection, repeat, cancel, unknown.

Allowed section update keys:
customer_context, contacts, visit_reason, summary, outcome, next_action,
offer_reference, order_reference, rating_sales_opportunity, rating_meeting_mood,
rating_priority, rating_closing_probability, rating_need_for_action,
rating_customer_satisfaction.

Context:
{context_json}

User message:
{message_text}
""".strip()


def _build_review_prompt(draft_context: dict[str, Any]) -> str:
    context_json = json.dumps(draft_context, ensure_ascii=False, default=str, indent=2)
    return f"""
Write a short, human-readable review summary for this B2B visit report draft.
Do not invent facts. Do not say that anything was saved or submitted.

Draft:
{context_json}
""".strip()


def _build_final_report_prompt(draft_context: dict[str, Any]) -> str:
    context_json = json.dumps(draft_context, ensure_ascii=False, default=str, indent=2)
    return f"""
Write the final CRM visit report text for this B2B field sales visit.
Use clear professional English. Do not invent facts.
Include customer context, participants, reason, summary, outcome, next action,
relevant references, and sales ratings when available.

Draft:
{context_json}
""".strip()
