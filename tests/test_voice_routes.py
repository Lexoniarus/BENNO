"""Tests for sales voice routes."""

from io import BytesIO
from urllib.parse import urlparse

from benno.enums import MessageSender
from benno.extensions import db
from benno.models import Chat, ChatMessage, User
from benno.seed import seed_database
from benno.services.ai_provider import AiMessageAnalysis
from benno.services.report_loop import process_report_message_with_ai, start_report_chat
from benno.services.voice import VoiceServiceError


def test_report_chat_renders_voice_controls(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client)
        response = client.get("/sales/reports/new", follow_redirects=True)

    assert response.status_code == 200
    assert b'data-voice-auto-start="true"' in response.data
    assert b"data-voice-controls" in response.data
    assert b"data-speech-url" in response.data
    assert b"Sprachmodus starten" in response.data


def test_new_report_redirects_with_voice_autostart_intent(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client)
        response = client.get("/sales/reports/new")

    assert response.status_code == 302
    assert response.location.endswith("?voice=auto")


def test_confirmed_report_chat_does_not_render_voice_autostart(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_location(new_response.location)
        chat = db.session.get(Chat, chat_id)
        chat.status = "confirmed"
        db.session.commit()
        response = client.get(f"/sales/reports/{chat_id}?voice=auto")

    assert response.status_code == 200
    assert b"data-voice-auto-start" not in response.data


def test_voice_turn_transcribes_and_advances_own_chat(app, monkeypatch) -> None:
    seed_database()
    monkeypatch.setattr(
        "benno.sales.transcribe_audio",
        lambda *_args: "Ich war vor Ort bei Nordlicht Solar.",
    )
    monkeypatch.setattr(
        "benno.sales.synthesize_assistant_speech",
        lambda *_args: _FakeSpeech(b"wav-bytes"),
    )

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_location(new_response.location)
        response = client.post(
            f"/sales/reports/{chat_id}/voice-turn",
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm", "audio/webm")},
            content_type="multipart/form-data",
        )

    payload = response.get_json()
    chat = db.session.get(Chat, chat_id)
    user_messages = [
        message
        for message in chat.messages
        if message.sender == MessageSender.USER.value
    ]

    assert response.status_code == 200
    assert payload["transcript"] == "Ich war vor Ort bei Nordlicht Solar."
    assert payload["assistant_reply"]
    assert payload["assistant_message_id"]
    assert payload["assistant_speech_url"].endswith(
        f"/sales/reports/{chat_id}/messages/"
        f"{payload['assistant_message_id']}/speech"
    )
    assert payload["audio"] == "d2F2LWJ5dGVz"
    assert payload["tts_error"] is None
    assert user_messages[-1].message_text == "Ich war vor Ort bei Nordlicht Solar."


def test_voice_turn_keeps_chat_turn_when_tts_fails(app, monkeypatch) -> None:
    seed_database()
    monkeypatch.setattr(
        "benno.sales.transcribe_audio",
        lambda *_args: "Ich war virtuell bei Nordlicht Solar.",
    )

    def fail_speech(*_args):
        raise VoiceServiceError("Lokaler Sprachdienst ist nicht verfügbar.")

    monkeypatch.setattr("benno.sales.synthesize_assistant_speech", fail_speech)

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_location(new_response.location)
        response = client.post(
            f"/sales/reports/{chat_id}/voice-turn",
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm", "audio/webm")},
            content_type="multipart/form-data",
        )

    payload = response.get_json()
    chat = db.session.get(Chat, chat_id)
    user_messages = [
        message
        for message in chat.messages
        if message.sender == MessageSender.USER.value
    ]

    assert response.status_code == 200
    assert payload["transcript"] == "Ich war virtuell bei Nordlicht Solar."
    assert payload["assistant_reply"]
    assert payload["assistant_speech_url"]
    assert payload["audio"] is None
    assert payload["audio_mime_type"] is None
    assert payload["tts_error"] == "Sprachausgabe nicht verfügbar."
    assert user_messages[-1].message_text == "Ich war virtuell bei Nordlicht Solar."


def test_voice_turn_requires_own_chat(app, monkeypatch) -> None:
    seed_database()
    other_user = User.query.filter_by(email="markus.weber@solar-sales.example").one()
    other_chat = Chat(sales_user=other_user)
    db.session.add(other_chat)
    db.session.commit()
    monkeypatch.setattr(
        "benno.sales.transcribe_audio",
        lambda *_args: "Should not be used.",
    )

    with app.test_client() as client:
        _login(client)
        response = client.post(
            f"/sales/reports/{other_chat.id}/voice-turn",
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm", "audio/webm")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 404


def test_voice_turn_rejects_oversized_audio_upload(app, monkeypatch) -> None:
    seed_database()
    app.config["VOICE_MAX_UPLOAD_BYTES"] = 3
    monkeypatch.setattr(
        "benno.sales.transcribe_audio",
        lambda *_args: "Should not be used.",
    )

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_location(new_response.location)
        response = client.post(
            f"/sales/reports/{chat_id}/voice-turn",
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm", "audio/webm")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 413
    assert response.get_json() == {"error": "Audiodatei ist zu groß."}


def test_voice_turn_rejects_unsupported_audio_mimetype(app, monkeypatch) -> None:
    seed_database()
    monkeypatch.setattr(
        "benno.sales.transcribe_audio",
        lambda *_args: "Should not be used.",
    )

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_location(new_response.location)
        response = client.post(
            f"/sales/reports/{chat_id}/voice-turn",
            data={"audio": (BytesIO(b"not-audio"), "answer.txt", "text/plain")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 415
    assert response.get_json() == {"error": "Audioformat wird nicht unterstützt."}


def test_voice_turn_returns_controlled_error_when_stt_fails(app, monkeypatch) -> None:
    seed_database()

    def fail_transcription(*_args):
        raise VoiceServiceError("Lokaler Sprachdienst ist nicht verfügbar.")

    monkeypatch.setattr("benno.sales.transcribe_audio", fail_transcription)

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_location(new_response.location)
        response = client.post(
            f"/sales/reports/{chat_id}/voice-turn",
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm", "audio/webm")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 503
    assert response.get_json() == {"error": "Lokaler Sprachdienst ist nicht verfügbar."}


def test_assistant_speech_rejects_user_messages(app, monkeypatch) -> None:
    seed_database()
    monkeypatch.setattr(
        "benno.sales.synthesize_assistant_speech",
        lambda *_args: _FakeSpeech(b"wav-bytes"),
    )

    with app.test_client() as client:
        _login(client)
        client.get("/sales/reports/new")
        chat = Chat.query.order_by(Chat.id.desc()).first()
        user_message = ChatMessage(
            chat=chat,
            sender=MessageSender.USER.value,
            message_text="Hallo",
            message_type="free_input",
        )
        db.session.add(user_message)
        db.session.commit()
        response = client.post(
            f"/sales/reports/{chat.id}/messages/{user_message.id}/speech"
        )

    assert response.status_code == 404


def test_assistant_speech_returns_audio(app, monkeypatch) -> None:
    seed_database()
    monkeypatch.setattr(
        "benno.sales.synthesize_assistant_speech",
        lambda *_args: _FakeSpeech(b"wav-bytes"),
    )

    with app.test_client() as client:
        _login(client)
        client.get("/sales/reports/new")
        chat = Chat.query.order_by(Chat.id.desc()).first()
        assistant_message = next(
            message
            for message in chat.messages
            if message.sender == MessageSender.ASSISTANT.value
        )
        response = client.post(
            f"/sales/reports/{chat.id}/messages/{assistant_message.id}/speech"
        )

    assert response.status_code == 200
    assert response.data == b"wav-bytes"
    assert response.mimetype == "audio/wav"


def test_report_review_renders_structured_correction_fields(app) -> None:
    seed_database()
    chat = _ready_report_chat()

    with app.test_client() as client:
        _login(client)
        response = client.get(f"/sales/reports/{chat.id}/review")

    assert response.status_code == 200
    assert b"correction_visit_context" in response.data
    assert b"correction_account_type" in response.data
    assert b"correction_priority_rating" in response.data


class _FakeSpeech:
    mimetype = "audio/wav"

    def __init__(self, audio_bytes: bytes) -> None:
        self.audio_bytes = audio_bytes

    def as_base64(self) -> str:
        return "d2F2LWJ5dGVz"


def _login(client):
    return client.post(
        "/login",
        data={
            "email": "laura.schneider@solar-sales.example",
            "password": "Sales123",
        },
    )


def _chat_id_from_location(location: str) -> int:
    return int(urlparse(location).path.rsplit("/", 1)[-1])


def _ready_report_chat() -> Chat:
    sales_user = User.query.filter_by(email="laura.schneider@solar-sales.example").one()
    chat = start_report_chat(sales_user)
    for answer in (
        "Nordlicht Maschinenbau GmbH",
        "persoenlich",
        "Mara Stein",
        "2026-07-07",
        "Forecast",
        "Forecast und Lieferfaehigkeit besprochen.",
        "Revidiertes Angebot wird geschickt.",
        "Innendienst soll anrufen.",
        "8 7 6 9",
    ):
        process_report_message_with_ai(chat, answer, _NoAiService())

    return chat


class _NoAiService:
    def analyze_report_message(self, _context, _message_text):
        return AiMessageAnalysis()
