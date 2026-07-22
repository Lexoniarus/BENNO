"""Tests for local STT/TTS voice sidecar clients."""

import httpx
import pytest

from benno.services.voice import VoiceServiceError, synthesize_speech, transcribe_audio


class _FakeResponse:
    def __init__(
        self,
        *,
        json_payload=None,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
        status_code: int = 200,
    ) -> None:
        self._json_payload = json_payload or {}
        self.content = content
        self.headers = headers or {}
        self.status_code = status_code

    def json(self):
        return self._json_payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "fake status error",
                request=httpx.Request("POST", "http://example.invalid"),
                response=httpx.Response(self.status_code),
            )


def test_transcribe_audio_posts_openai_compatible_payload(app, monkeypatch) -> None:
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return _FakeResponse(json_payload={"text": "Ich war bei PerfSolar."})

    monkeypatch.setattr("benno.services.voice.httpx.post", fake_post)

    with app.app_context():
        transcript = transcribe_audio(b"audio-bytes", "answer.webm", "audio/webm")

    assert transcript == "Ich war bei PerfSolar."
    assert captured["url"] == "http://127.0.0.1:8000/v1/audio/transcriptions"
    assert captured["data"] == {
        "model": "Systran/faster-whisper-base",
        "language": "de",
        "response_format": "json",
    }
    assert captured["files"]["file"] == (
        "answer.webm",
        b"audio-bytes",
        "audio/webm",
    )


def test_transcribe_audio_rejects_empty_transcript(app, monkeypatch) -> None:
    monkeypatch.setattr(
        "benno.services.voice.httpx.post",
        lambda *_args, **_kwargs: _FakeResponse(json_payload={"text": " "}),
    )

    with app.app_context(), pytest.raises(VoiceServiceError):
        transcribe_audio(b"audio-bytes", "answer.webm", "audio/webm")


def test_transcribe_audio_reports_invalid_json_with_umlauts(app, monkeypatch) -> None:
    class BrokenJsonResponse(_FakeResponse):
        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(
        "benno.services.voice.httpx.post",
        lambda *_args, **_kwargs: BrokenJsonResponse(content=b"not-json"),
    )

    with app.app_context(), pytest.raises(VoiceServiceError) as error:
        transcribe_audio(b"audio-bytes", "answer.webm", "audio/webm")

    assert str(error.value) == "Speaches hat keine gültige JSON-Antwort geliefert."


def test_synthesize_speech_posts_kokoro_payload(app, monkeypatch) -> None:
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return _FakeResponse(
            content=b"wav-bytes",
            headers={"content-type": "audio/wav"},
        )

    monkeypatch.setattr("benno.services.voice.httpx.post", fake_post)

    with app.app_context():
        speech = synthesize_speech("Hallo von BENNO.")

    assert speech.audio_bytes == b"wav-bytes"
    assert speech.mimetype == "audio/wav"
    assert speech.as_base64() == "d2F2LWJ5dGVz"
    assert captured["url"] == "http://127.0.0.1:8881/v1/audio/speech"
    assert captured["json"] == {
        "model": "kokoro",
        "input": "Hallo von BENNO.",
        "voice": "martin",
        "response_format": "wav",
    }


def test_sidecar_http_errors_are_controlled(app, monkeypatch) -> None:
    def fake_post(_url, **_kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr("benno.services.voice.httpx.post", fake_post)

    with app.app_context(), pytest.raises(VoiceServiceError) as error:
        synthesize_speech("Hallo.")

    assert str(error.value) == "Lokaler Sprachdienst ist nicht verfügbar."


def test_synthesize_speech_rejects_empty_text_with_umlauts(app) -> None:
    with app.app_context(), pytest.raises(VoiceServiceError) as error:
        synthesize_speech(" ")

    assert str(error.value) == "Kein Text für die Sprachausgabe vorhanden."
