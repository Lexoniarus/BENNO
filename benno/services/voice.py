"""Local STT and TTS sidecar clients for BENNO voice turns."""

import base64
from dataclasses import dataclass

import httpx
from flask import current_app


class VoiceServiceError(RuntimeError):
    """Raised when a local voice sidecar cannot return usable output."""


@dataclass(frozen=True)
class SynthesizedSpeech:
    """Generated assistant speech bytes and browser MIME type."""

    audio_bytes: bytes
    mimetype: str

    def as_base64(self) -> str:
        """Return audio bytes as ASCII base64 for JSON responses."""
        return base64.b64encode(self.audio_bytes).decode("ascii")


def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    content_type: str,
) -> str:
    """Transcribe recorded browser audio through the local Speaches sidecar."""
    _ensure_voice_enabled()
    if not audio_bytes:
        raise VoiceServiceError("Keine Audiodaten empfangen.")

    response = _post_speaches_transcription(audio_bytes, filename, content_type)
    transcript = _extract_transcript(response)
    if not transcript:
        raise VoiceServiceError("Speaches hat kein Transkript geliefert.")

    return transcript


def synthesize_speech(text: str) -> SynthesizedSpeech:
    """Generate assistant speech through the local Kokoro/Martin sidecar."""
    _ensure_voice_enabled()
    clean_text = text.strip()
    if not clean_text:
        raise VoiceServiceError("Kein Text fuer die Sprachausgabe vorhanden.")

    response = _post_kokoro_speech(clean_text)
    if not response.content:
        raise VoiceServiceError("Kokoro hat keine Audiodaten geliefert.")

    return SynthesizedSpeech(
        audio_bytes=response.content,
        mimetype=response.headers.get("content-type", "audio/wav").split(";")[0],
    )


def _ensure_voice_enabled() -> None:
    if not current_app.config.get("VOICE_ENABLED", False):
        raise VoiceServiceError("Sprachmodus ist deaktiviert.")


def _post_speaches_transcription(
    audio_bytes: bytes,
    filename: str,
    content_type: str,
) -> httpx.Response:
    files = {
        "file": (
            filename or "recording.webm",
            audio_bytes,
            content_type or "application/octet-stream",
        )
    }
    data = {
        "model": current_app.config["SPEACHES_STT_MODEL"],
        "language": current_app.config["SPEACHES_STT_LANGUAGE"],
        "response_format": "json",
    }
    return _post_to_sidecar(
        f"{_base_url('SPEACHES_BASE_URL')}/v1/audio/transcriptions",
        data=data,
        files=files,
    )


def _post_kokoro_speech(text: str) -> httpx.Response:
    payload = {
        "model": current_app.config["KOKORO_TTS_MODEL"],
        "input": text,
        "voice": current_app.config["KOKORO_TTS_VOICE"],
        "response_format": "wav",
    }
    return _post_to_sidecar(
        f"{_base_url('KOKORO_BASE_URL')}/v1/audio/speech",
        json=payload,
    )


def _post_to_sidecar(url: str, **kwargs) -> httpx.Response:
    try:
        response = httpx.post(url, timeout=60.0, **kwargs)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise VoiceServiceError("Lokaler Sprachdienst ist nicht verfuegbar.") from error

    return response


def _base_url(config_key: str) -> str:
    return str(current_app.config[config_key]).rstrip("/")


def _extract_transcript(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError as error:
        raise VoiceServiceError(
            "Speaches hat keine gueltige JSON-Antwort geliefert."
        ) from error

    return str(payload.get("text", "")).strip()
