# MVP 03: Testkandidaten für STT, TTS und LLM Provider

## 1. Zweck dieses Dokuments

Dieses Dokument hält die ersten technischen Testkandidaten für Speech-to-Text, Text-to-Speech und LLM Provider fest.

Es beschreibt noch keine finale technische Implementierung. Ziel ist, eine nachvollziehbare Testbasis für den MVP zu definieren:

- Welche Modelle oder Provider werden zuerst getestet?
- Warum kommen sie in Frage?
- Welche Lizenz- oder Limitierungsfragen sind zu beachten?
- Welche Fallbacks gibt es?

Die Projektleitlinie bleibt:

- Der MVP soll local-first gedacht werden.
- OpenAI und Gemini müssen aufgrund der Projektanforderung eingebunden werden.
- Lokale Modelle sollen perspektivisch eine echte Alternative zu externen API Calls sein.
- STT und TTS sollen bevorzugt lokal im Python Backend laufen.
- Die LLM-Provider sollen austauschbar bleiben.

## 2. Technische Ausgangslage der Testmaschine

Die aktuell verfügbare Testmaschine:

| Komponente | Ausstattung |
|---|---|
| CPU | Intel Core Ultra 7 265K |
| RAM | 32 GB |
| GPU | NVIDIA GeForce RTX 3060 |
| VRAM | 12 GB |
| Betriebssystem | Windows 11 |

Einschätzung:

Für lokale STT- und TTS-Tests ist diese Maschine grundsätzlich geeignet.

Wichtig ist aber, STT, TTS und lokale LLMs nicht ungeplant gleichzeitig voll in den VRAM zu laden. Für den ersten MVP ist das unkritisch, weil die Reihenfolge so gedacht ist:

1. STT/TTS lokal testen.
2. LLM-Dialog zunächst über OpenAI/Gemini stabilisieren.
3. Danach lokale LLMs über LM Studio prüfen.

## 3. STT-Testkandidaten

Speech-to-Text soll im Idealfall lokal über das Python Backend laufen.

### 3.1 Primärer STT-Kandidat

| Kriterium | Wert |
|---|---|
| Modell | `primeline/whisper-large-v3-turbo-german` |
| Aufgabe | German Automatic Speech Recognition |
| Grundlage | Whisper Large v3 Turbo, deutsch optimiert |
| Lizenz | Apache-2.0 laut Modellkarte |
| Parametergröße | ca. 809M |
| Nutzung | Transformers Pipeline möglich |
| Rolle im MVP | erster Qualitätskandidat |

Begründung:

Das Modell ist speziell für deutsche Spracherkennung optimiert und damit fachlich passend für deutschsprachige Außendienstberichte. Die Apache-2.0-Lizenz ist grundsätzlich permissiv. Der Disclaimer des Anbieters bedeutet, dass keine Gewährleistung für korrekte Outputs übernommen wird. Er bedeutet nach aktuellem Verständnis nicht automatisch, dass kommerzielle Nutzung ausgeschlossen ist.

Einordnung:

- guter erster Qualitätskandidat
- auf RTX 3060 12 GB realistisch testbar
- mögliche Performance-Optimierung später über `faster-whisper`, CTranslate2 oder GGML/whisper.cpp

### 3.2 Kleiner STT-Fallback

| Kriterium | Wert |
|---|---|
| Modell | `primeline/whisper-tiny-german` |
| Aufgabe | German Automatic Speech Recognition |
| Parametergröße | ca. 37.8M |
| Rolle im MVP | Geschwindigkeits- oder Notfallfallback |

Begründung:

Das Modell ist sehr klein und dadurch interessant, falls Performance oder Hardware zum Problem werden. Die Modellkarte weist aber darauf hin, dass es für Edge-Fälle gedacht ist und nicht für kritische Qualität empfohlen wird.

Einordnung:

- sehr leichtgewichtig
- schnell testbar
- nicht erste Wahl für zuverlässige Besuchsberichte
- sinnvoll als Vergleich: Geschwindigkeit gegen Qualität

### 3.3 Lokaler Performance-Pfad

| Kriterium | Wert |
|---|---|
| Kandidat | `cstr/whisper-large-v3-turbo-german-ggml` |
| Grundlage | GGML-Konvertierung des deutschen Whisper-Turbo-Modells |
| Ziel | Performance-Pfad über whisper.cpp oder vergleichbare lokale Runtime |
| Rolle im MVP | technische Alternative, falls Transformers zu schwerfällig ist |

Begründung:

Falls die normale Transformers-Nutzung zu langsam oder zu ressourcenintensiv ist, kann ein GGML/whisper.cpp-Pfad sinnvoll werden. Dieser Pfad ist besonders interessant für lokale CPU/GPU-optimierte Inferenz.

## 4. TTS-Testkandidaten

Text-to-Speech soll im Idealfall lokal über das Python Backend laufen.

### 4.1 Primärer TTS-Kandidat

| Kriterium | Wert |
|---|---|
| Modell | `Godelaune/Kokoro-82M-ONNX-German-Martin` |
| Aufgabe | German Text-to-Speech |
| Format | ONNX |
| Lizenz | Apache-2.0 laut Modellkarte |
| Parametergröße | ca. 82M |
| Rolle im MVP | erster TTS-Kandidat |

Begründung:

Kokoro klingt qualitativ vielversprechend, ist vergleichsweise klein, deutsch nutzbar und durch ONNX gut für lokale Inferenz geeignet. Die Modellkarte beschreibt außerdem einen OpenAI-kompatiblen `/v1/audio/speech`-Ansatz, was gut zum API-orientierten Backend-Konzept passt.

Einordnung:

- sehr guter erster TTS-Kandidat
- local-first passend
- Lizenzstand günstiger als Non-Commercial-Modelle
- ideal für Test: deutsche Antworttexte des Assistenten vorlesen

### 4.2 Einfacher TTS-Fallback

| Kriterium | Wert |
|---|---|
| Modelle | `Thorsten-Voice/Piper`, `rhasspy/piper-voices` |
| Aufgabe | German Text-to-Speech |
| Format | ONNX / Piper |
| Lizenz | MIT laut Modellkarten |
| Rolle im MVP | einfacher lokaler Fallback |

Begründung:

Piper-Stimmen sind für lokale TTS-Nutzung etabliert, technisch vergleichsweise einfach und lizenzseitig angenehm. Wenn Kokoro im Setup zu aufwendig wird oder Probleme macht, ist Piper ein guter pragmatischer Fallback.

Einordnung:

- technisch schlanker
- gute Lizenzlage
- vermutlich einfacher zu integrieren
- Qualität wahrscheinlich weniger beeindruckend als Kokoro, aber ausreichend für einen MVP

### 4.3 TTS-Research-Kandidat

| Kriterium | Wert |
|---|---|
| Modell | `aihpi/F5-TTS-German` |
| Aufgabe | German Text-to-Speech / Voice Cloning |
| Lizenz | CC-BY-NC-4.0 laut Modellkarte |
| Rolle im MVP | Research, nicht primär |

Begründung:

Das Modell ist qualitativ interessant, aber die Non-Commercial-Lizenz macht es für die Produkt- und MVP-Richtung weniger sauber. Für ein Abschlussprojekt kann es als Research interessant sein, aber es sollte nicht der primäre technische Kandidat werden.

## 5. LLM-Providerstrategie

Die Dialog- und LLM-Logik soll provider-unabhängig aufgebaut werden.

Der Ablauf des Besuchsbericht-Assistenten soll unabhängig davon funktionieren, ob im Hintergrund OpenAI, Gemini oder ein lokales Modell verwendet wird.

## 6. OpenAI

OpenAI ist ein Pflichtprovider aufgrund der Projektanforderung.

Rolle im MVP:

- erster stabiler API-Provider für die Dialoglogik
- besonders geeignet, um den fachlichen Ablauf zuverlässig zu testen
- Grundlage für Extraktion, Rückfragen, Bewertungsvorschläge, Korrekturen und finale Berichtserstellung

Konkretes Modell:

- noch offen
- wird später abhängig von Projektvorgabe, Kosten und Verfügbarkeit festgelegt

## 7. Gemini

Gemini ist ebenfalls ein Pflichtprovider aufgrund der Projektanforderung.

Aktueller Stand:

- Nutzung über Gemini Free Tier vorgesehen
- konkrete Modelle und Limits müssen geprüft werden
- Mentor-Feedback zu verfügbaren Modellen steht noch aus

Einordnung:

Gemini Free Tier eignet sich voraussichtlich für:

- Demonstration der Integration
- kurze Testdialoge
- Vergleich mit OpenAI

Gemini Free Tier ist voraussichtlich weniger geeignet als alleinige Grundlage für:

- lange geführte Berichtsdialoge
- viele parallele Tests
- zuverlässige Entwicklung ohne Rate-Limit-Risiko

Konzeptentscheidung:

Gemini wird integriert und demonstrierbar gemacht. Der vollständige MVP-Workflow soll aber nicht ausschließlich vom Gemini Free Tier abhängen.

## 8. LM Studio als lokale LLM-Alternative

LM Studio soll als lokale Alternative ernsthaft berücksichtigt werden.

Begründung:

- entspricht der local-first-Zielrichtung
- ermöglicht lokale Modelle ohne externe API-Kosten
- bietet OpenAI-kompatible Endpoints
- kann dadurch relativ sauber in dieselbe Provider-Architektur eingebunden werden

Wichtige technische Eigenschaft:

LM Studio kann lokale Modelle über einen lokalen Server bereitstellen. Die offizielle Dokumentation beschreibt OpenAI-kompatible Endpoints, bei denen bestehende OpenAI-Clients durch Änderung der `base_url` auf LM Studio zeigen können.

Rolle im MVP:

- nicht zwingend erster stabiler Provider
- aber wichtige zweite technische Alternative neben OpenAI
- besonders relevant, wenn Gemini Free Tier für längere Dialoge zu eingeschränkt ist

## 9. Reihenfolge der Tests

Empfohlene Testreihenfolge:

1. OpenAI-Provider für die Dialoglogik anbinden.
2. Gemini-Provider über Free Tier anbinden und Limits prüfen.
3. LM-Studio-Provider als OpenAI-kompatible lokale Alternative vorbereiten.
4. STT mit `primeline/whisper-large-v3-turbo-german` testen.
5. TTS mit `Godelaune/Kokoro-82M-ONNX-German-Martin` testen.
6. Falls Performance oder Setup problematisch wird:
   - STT-Fallback über `whisper-tiny-german`, `faster-whisper` oder GGML prüfen.
   - TTS-Fallback über Piper/Thorsten prüfen.

## 10. Lizenzleitlinie für lokale Modelle

Für lokale Modelle gilt:

- bevorzugt Apache-2.0 oder MIT
- Non-Commercial-Lizenzen nicht als Primärkandidat
- Lizenz der Modellkarte dokumentieren
- Disclaimer dokumentieren
- keine Modellentscheidung ohne Lizenzprüfung

Einordnung Apache-2.0 plus Disclaimer:

Wenn ein Modell unter Apache-2.0 steht, ist es grundsätzlich permissiv und auch kommerziell nutzbar. Ein Disclaimer wie „not a commercial product“ oder „use at your own risk“ ist nach aktuellem Verständnis kein automatisches Verbot kommerzieller Nutzung. Er weist vor allem darauf hin, dass der Anbieter keine Produktgarantie, keinen Support und keine Haftung für Fehler übernimmt.

Für den Projektbericht sollte trotzdem dokumentiert werden:

- welche Modellkarte verwendet wurde
- welche Lizenz dort angegeben ist
- welche Disclaimer genannt werden
- dass keine Rechtsberatung erfolgt, sondern eine technische MVP-Einordnung

## 11. Aktuelle Arbeitsfestlegung

| Bereich | Erste Wahl | Fallback / Alternative |
|---|---|---|
| STT | `primeline/whisper-large-v3-turbo-german` | `whisper-tiny-german`, GGML/whisper.cpp, faster-whisper |
| TTS | `Godelaune/Kokoro-82M-ONNX-German-Martin` | Thorsten/Piper |
| LLM API | OpenAI | Gemini Free Tier |
| Lokale LLM Alternative | LM Studio | später konkrete lokale Modelle |

## 12. Frage an Mentor

Offen ist die Rückfrage an Ofer:

- Ist es für das Abschlussprojekt ausreichend, Gemini über den Free Tier als demonstrierbaren Provider einzubinden?
- Darf LM Studio mit lokalen Modellen als zweite ernsthafte Alternative neben OpenAI vorgesehen werden?
- Welche konkreten OpenAI- und Gemini-Modelle sollen oder dürfen im Projekt verwendet werden?

## 13. Zusammenfassung

Die lokale STT/TTS-Richtung ist auf der vorhandenen Maschine realistisch. Für STT wird zuerst ein deutsch optimiertes Whisper-Turbo-Modell getestet. Für TTS wird zuerst Kokoro ONNX German Martin getestet, weil es lokal, deutsch, qualitativ vielversprechend und Apache-2.0-lizenziert ist.

Für die LLM-Logik bleibt OpenAI der erste stabile API-Provider. Gemini wird wegen der Projektanforderung integriert, aber aufgrund des Free-Tier-Risikos nicht als alleinige Grundlage für lange Dialoge geplant. LM Studio ist eine vernünftige zweite Alternative, weil es lokal läuft und OpenAI-kompatible API-Calls unterstützt.
