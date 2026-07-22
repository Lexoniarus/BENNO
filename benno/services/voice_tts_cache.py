"""Cached assistant TTS orchestration for BENNO voice replies."""

from __future__ import annotations

import hashlib
import re
import wave
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from flask import current_app

from benno.services.voice import SynthesizedSpeech, synthesize_speech

STANDARD_TTS_SNIPPETS = (
    "Hallo ",
    ", ich bin bereit für deinen Besuchsbericht.",
    "Um welchen Kunden, Lead oder Kontakt ging es bei dem Besuch?",
    "Danke für die Informationen zu ",
    "Wann genau hat der Besuch stattgefunden?",
    "Was war die Besuchsart: vor Ort, virtuell oder telefonisch?",
    "Wer hat an dem Gespräch teilgenommen?",
    "Was war das Ziel oder Thema des Besuchs?",
    "Was wurde besprochen?",
    "Was wurde vereinbart?",
    "Was ist der nächste Schritt?",
    "Wie bewertest du Zufriedenheit, technische Attraktivität, "
    "kaufmännische Attraktivität und Priorität?",
    "Alle Pflichtbereiche sind vollständig.",
    "Bitte prüfe den Bericht über den Button Bericht prüfen im "
    "Schreibzurück-Bereich.",
    "BENNO bereitet die Sprachausgabe vor.",
    "BENNO spricht.",
    "Ich höre zu. Sprich deine Antwort.",
    "BENNO transkribiert und analysiert.",
)

CONTEXT_TERM_KEYS = (
    "username",
    "visit_context",
    "participants",
    "target_topic",
    "account_name",
    "contact_name",
)


@dataclass(frozen=True)
class _WavSnippet:
    params: wave._wave_params
    frames: bytes


def synthesize_assistant_speech(
    text: str,
    context: dict[str, Any] | None = None,
) -> SynthesizedSpeech:
    """Return assistant speech from cached TTS snippets when possible."""
    clean_text = _normalized_text(text)
    if not clean_text:
        return synthesize_speech(text)
    if not _tts_cache_enabled():
        return synthesize_speech(clean_text)

    segments = _assistant_text_segments(clean_text, context or {})
    if len(segments) <= 1:
        return _cached_snippet(clean_text)

    try:
        return _compose_cached_segments(segments)
    except (OSError, wave.Error, ValueError):
        return synthesize_speech(clean_text)


def prewarm_voice_cache() -> int:
    """Generate cache files for standard BENNO voice phrases."""
    if not _tts_cache_enabled() or not current_app.config["VOICE_TTS_PREWARM_ENABLED"]:
        return 0

    warmed_count = 0
    for snippet_text in STANDARD_TTS_SNIPPETS:
        cache_path = _cache_path_for_text(snippet_text)
        if cache_path.exists():
            continue
        _cached_snippet(snippet_text)
        warmed_count += 1

    return warmed_count


def _compose_cached_segments(segments: list[str]) -> SynthesizedSpeech:
    snippets = [
        _wav_snippet(_cached_snippet(segment).audio_bytes) for segment in segments
    ]
    first_params = snippets[0].params
    if any(snippet.params != first_params for snippet in snippets):
        raise ValueError("TTS snippets use incompatible WAV parameters.")

    output = BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setparams(first_params)
        for snippet in snippets:
            wav_file.writeframes(snippet.frames)

    return SynthesizedSpeech(audio_bytes=output.getvalue(), mimetype="audio/wav")


def _cached_snippet(text: str) -> SynthesizedSpeech:
    cache_path = _cache_path_for_text(text)
    if cache_path.exists():
        return SynthesizedSpeech(
            audio_bytes=cache_path.read_bytes(),
            mimetype="audio/wav",
        )

    speech = synthesize_speech(text)
    if speech.mimetype != "audio/wav":
        return speech

    _cache_directory().mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(speech.audio_bytes)
    return speech


def _wav_snippet(audio_bytes: bytes) -> _WavSnippet:
    with wave.open(BytesIO(audio_bytes), "rb") as wav_file:
        params = wav_file.getparams()
        frames = wav_file.readframes(wav_file.getnframes())

    return _WavSnippet(params=params, frames=frames)


def _assistant_text_segments(text: str, context: dict[str, Any]) -> list[str]:
    segments = [text]
    for term in _context_terms(context):
        segments = _split_segments_by_term(segments, term)

    max_chars = current_app.config["VOICE_TTS_MAX_SNIPPET_CHARS"]
    return [
        split_segment
        for segment in segments
        for split_segment in _split_long_segment(segment, max_chars)
        if split_segment.strip()
    ]


def _split_segments_by_term(segments: list[str], term: str) -> list[str]:
    split_segments: list[str] = []
    pattern = re.compile(f"({re.escape(term)})", re.IGNORECASE)
    for segment in segments:
        parts = [part for part in pattern.split(segment) if part]
        split_segments.extend(parts or [segment])

    return split_segments


def _split_long_segment(segment: str, max_chars: int) -> list[str]:
    clean_segment = segment.strip()
    if len(clean_segment) <= max_chars:
        return [clean_segment]

    sentence_parts = re.split(r"(?<=[.!?])\s+", clean_segment)
    if all(len(part) <= max_chars for part in sentence_parts):
        return sentence_parts

    return _split_by_words(clean_segment, max_chars)


def _split_by_words(text: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    current_words: list[str] = []
    current_length = 0
    for word in text.split():
        next_length = current_length + len(word) + (1 if current_words else 0)
        if current_words and next_length > max_chars:
            chunks.append(" ".join(current_words))
            current_words = [word]
            current_length = len(word)
        else:
            current_words.append(word)
            current_length = next_length

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def _context_terms(context: dict[str, Any]) -> list[str]:
    configured_terms = _values_from_context(context)
    explicit_terms = context.get("snippet_terms", [])
    if isinstance(explicit_terms, list):
        configured_terms.extend(str(term) for term in explicit_terms)

    return sorted(
        {
            _normalized_text(term)
            for term in configured_terms
            if _valid_dynamic_term(_normalized_text(term))
        },
        key=len,
        reverse=True,
    )


def _values_from_context(context: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in CONTEXT_TERM_KEYS:
        value = context.get(key)
        if isinstance(value, str):
            values.append(value)

    return values


def _valid_dynamic_term(term: str) -> bool:
    return 2 <= len(term) <= 80 and len(term.split()) <= 8


def _cache_path_for_text(text: str) -> Path:
    cache_key = _cache_key_for_text(text)
    return _cache_directory() / f"{cache_key}.wav"


def _cache_key_for_text(text: str) -> str:
    cache_source = "|".join(
        (
            current_app.config["KOKORO_TTS_MODEL"],
            current_app.config["KOKORO_TTS_VOICE"],
            _normalized_text(text),
        )
    )
    return hashlib.sha256(cache_source.encode("utf-8")).hexdigest()


def _cache_directory() -> Path:
    configured_path = Path(str(current_app.config["VOICE_TTS_CACHE_DIR"]))
    if configured_path.is_absolute():
        return configured_path

    return Path(current_app.root_path).parent / configured_path


def _tts_cache_enabled() -> bool:
    return bool(current_app.config["VOICE_TTS_CACHE_ENABLED"])


def _normalized_text(text: object) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()
