"""Tests for optional Langfuse observability helpers."""

from types import SimpleNamespace

from benno.models import User
from benno.seed import seed_database
from benno.services.ai_provider import AiMessageAnalysis
from benno.services.observability import (
    observability_status,
    trace_report_decision,
    traced_generation_input,
    traced_usage_details,
)
from benno.services.report_loop import process_report_message_with_ai, start_report_chat


def test_observability_is_disabled_by_default(app) -> None:
    with app.app_context():
        assert observability_status() == {
            "label": "Langfuse: disabled",
            "state": "inactive",
        }


def test_generation_input_uses_role_labeled_messages() -> None:
    input_payload = traced_generation_input("User prompt", "System instruction")

    assert input_payload == {
        "messages": [
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "User prompt"},
        ]
    }


def test_gemini_usage_metadata_maps_to_langfuse_usage_details() -> None:
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=11,
            candidates_token_count=7,
            total_token_count=18,
            cached_content_token_count=3,
        )
    )

    assert traced_usage_details(response) == {
        "input": 11,
        "output": 7,
        "total": 18,
        "cached_input": 3,
    }


def test_report_decision_updates_current_span(app, monkeypatch) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)
    captured_update = {}

    class FakeLangfuseClient:
        def update_current_span(self, **kwargs):
            captured_update.update(kwargs)

    monkeypatch.setattr(
        "benno.services.observability._langfuse_client",
        lambda: FakeLangfuseClient(),
    )
    analysis = AiMessageAnalysis(section_updates={"visit_context": "PerfSolar"})

    trace_report_decision(
        chat.report_draft,
        analysis,
        ["visit_context"],
        "visit_type",
    )

    assert captured_update["output"]["next_step"] == "visit_type"
    assert captured_update["output"]["applied_step_keys"] == ["visit_context"]
    assert captured_update["output"]["accepted_ai_update_keys"] == ["visit_context"]


def test_report_loop_wraps_turn_with_observability_trace(app, monkeypatch) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)
    captured_trace = {}

    class FakeTrace:
        def __enter__(self):
            captured_trace["entered"] = True
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            captured_trace["exited"] = True
            return False

    def fake_trace_report_turn(chat, draft, current_step, message_text):
        captured_trace["chat_id"] = chat.id
        captured_trace["current_step"] = current_step
        captured_trace["message_text"] = message_text
        return FakeTrace()

    monkeypatch.setattr(
        "benno.services.report_loop.trace_report_turn",
        fake_trace_report_turn,
    )

    process_report_message_with_ai(chat, "PerfSolar", None)

    assert captured_trace["entered"] is True
    assert captured_trace["exited"] is True
    assert captured_trace["chat_id"] == chat.id
    assert captured_trace["current_step"] == "visit_context"
    assert captured_trace["message_text"] == "PerfSolar"
