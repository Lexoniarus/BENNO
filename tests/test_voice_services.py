"""Tests for local STT/TTS voice sidecar clients."""

import wave
from io import BytesIO

import httpx
import pytest

from benno.services.voice import VoiceServiceError, synthesize_speech, transcribe_audio
from benno.services.voice_tts_cache import (
    prewarm_voice_cache,
    synthesize_assistant_speech,
)


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


def test_assistant_speech_reuses_cached_standard_and_name_snippets(
    app,
    monkeypatch,
    tmp_path,
) -> None:
    app.config["VOICE_TTS_CACHE_DIR"] = str(tmp_path)
    calls = []

    def fake_synthesize(text: str):
        calls.append(text)
        return _FakeSpeech(_wav_bytes(text.encode("utf-8")[:8] or b"voice"))

    monkeypatch.setattr(
        "benno.services.voice_tts_cache.synthesize_speech",
        fake_synthesize,
    )

    text = "Danke für die Informationen zu Nordlicht Solar. Wann genau war das?"
    context = {"visit_context": "Nordlicht Solar"}

    with app.app_context():
        first_speech = synthesize_assistant_speech(text, context)
        second_speech = synthesize_assistant_speech(text, context)

    assert first_speech.audio_bytes.startswith(b"RIFF")
    assert second_speech.audio_bytes == first_speech.audio_bytes
    assert calls == [
        "Danke für die Informationen zu",
        "Nordlicht Solar",
        ". Wann genau war das?",
    ]


def test_assistant_speech_cache_key_separates_voice_model(
    app,
    monkeypatch,
    tmp_path,
) -> None:
    app.config["VOICE_TTS_CACHE_DIR"] = str(tmp_path)
    calls = []

    def fake_synthesize(text: str):
        calls.append((app.config["KOKORO_TTS_VOICE"], text))
        return _FakeSpeech(_wav_bytes(b"voice"))

    monkeypatch.setattr(
        "benno.services.voice_tts_cache.synthesize_speech",
        fake_synthesize,
    )

    with app.app_context():
        synthesize_assistant_speech("Hallo BENNO.")
        app.config["KOKORO_TTS_VOICE"] = "other-voice"
        synthesize_assistant_speech("Hallo BENNO.")

    assert calls == [
        ("martin", "Hallo BENNO."),
        ("other-voice", "Hallo BENNO."),
    ]


def test_assistant_speech_cache_can_be_disabled(app, monkeypatch, tmp_path) -> None:
    app.config["VOICE_TTS_CACHE_DIR"] = str(tmp_path)
    app.config["VOICE_TTS_CACHE_ENABLED"] = False
    calls = []

    def fake_synthesize(text: str):
        calls.append(text)
        return _FakeSpeech(_wav_bytes(b"direct"))

    monkeypatch.setattr(
        "benno.services.voice_tts_cache.synthesize_speech",
        fake_synthesize,
    )

    with app.app_context():
        synthesize_assistant_speech("Hallo BENNO.")
        synthesize_assistant_speech("Hallo BENNO.")

    assert calls == ["Hallo BENNO.", "Hallo BENNO."]


def test_assistant_speech_falls_back_when_cached_wav_is_invalid(
    app,
    monkeypatch,
    tmp_path,
) -> None:
    app.config["VOICE_TTS_CACHE_DIR"] = str(tmp_path)
    calls = []

    def fake_synthesize(text: str):
        calls.append(text)
        if text == "Nordlicht Solar":
            return _FakeSpeech(b"not-a-wav")

        return _FakeSpeech(_wav_bytes(b"valid"))

    monkeypatch.setattr(
        "benno.services.voice_tts_cache.synthesize_speech",
        fake_synthesize,
    )

    with app.app_context():
        speech = synthesize_assistant_speech(
            "Danke für die Informationen zu Nordlicht Solar.",
            {"visit_context": "Nordlicht Solar"},
        )

    assert speech.audio_bytes.startswith(b"RIFF")
    assert calls[-1] == "Danke für die Informationen zu Nordlicht Solar."


def test_prewarm_voice_cache_generates_standard_snippets(
    app,
    monkeypatch,
    tmp_path,
) -> None:
    app.config["VOICE_TTS_CACHE_DIR"] = str(tmp_path)
    calls = []

    def fake_synthesize(text: str):
        calls.append(text)
        return _FakeSpeech(_wav_bytes(b"warm"))

    monkeypatch.setattr(
        "benno.services.voice_tts_cache.synthesize_speech",
        fake_synthesize,
    )

    with app.app_context():
        warmed_count = prewarm_voice_cache()
        second_warmed_count = prewarm_voice_cache()

    assert warmed_count > 0
    assert second_warmed_count == 0
    assert len(calls) == warmed_count


class _FakeSpeech:
    mimetype = "audio/wav"

    def __init__(self, audio_bytes: bytes) -> None:
        self.audio_bytes = audio_bytes


def _wav_bytes(frame_bytes: bytes) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(1)
        wav_file.setframerate(8000)
        wav_file.writeframes(frame_bytes)

    return buffer.getvalue()
