"""Tests for sales voice routes."""

from io import BytesIO

from benno.enums import MessageSender
from benno.extensions import db
from benno.models import Chat, ChatMessage, User
from benno.seed import seed_database
from benno.services.voice import VoiceServiceError


def test_report_chat_renders_voice_controls(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client)
        response = client.get("/sales/reports/new", follow_redirects=True)

    assert response.status_code == 200
    assert b"data-voice-controls" in response.data
    assert b"data-speech-url" in response.data
    assert b"Sprachmodus starten" in response.data


def test_voice_turn_transcribes_and_advances_own_chat(app, monkeypatch) -> None:
    seed_database()
    monkeypatch.setattr(
        "benno.sales.transcribe_audio",
        lambda *_args: "Ich war vor Ort bei Nordlicht Solar.",
    )
    monkeypatch.setattr(
        "benno.sales.synthesize_speech",
        lambda _text: _FakeSpeech(b"wav-bytes"),
    )

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = int(new_response.location.rsplit("/", 1)[-1])
        response = client.post(
            f"/sales/reports/{chat_id}/voice-turn",
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm")},
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
    assert payload["audio"] == "d2F2LWJ5dGVz"
    assert user_messages[-1].message_text == "Ich war vor Ort bei Nordlicht Solar."


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
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 404


def test_voice_turn_returns_controlled_error_when_stt_fails(app, monkeypatch) -> None:
    seed_database()

    def fail_transcription(*_args):
        raise VoiceServiceError("Lokaler Sprachdienst ist nicht verfuegbar.")

    monkeypatch.setattr("benno.sales.transcribe_audio", fail_transcription)

    with app.test_client() as client:
        _login(client)
        new_response = client.get("/sales/reports/new")
        chat_id = int(new_response.location.rsplit("/", 1)[-1])
        response = client.post(
            f"/sales/reports/{chat_id}/voice-turn",
            data={"audio": (BytesIO(b"audio-bytes"), "answer.webm")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "Lokaler Sprachdienst ist nicht verfuegbar."
    }


def test_assistant_speech_rejects_user_messages(app, monkeypatch) -> None:
    seed_database()
    monkeypatch.setattr(
        "benno.sales.synthesize_speech",
        lambda _text: _FakeSpeech(b"wav-bytes"),
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
        "benno.sales.synthesize_speech",
        lambda _text: _FakeSpeech(b"wav-bytes"),
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
