# MVP 04: Interviewstand zu Providerstrategie, Datenschutz und lokalen LLMs

## 1. Zweck dieses Dokuments

Dieses Dokument hält den nächsten Konzeptstand nach der weiteren Klärung offener Fragen fest.

Es ergänzt die bisherigen Dokumente:

- `MVP_01_Konzeptstand_Besuchsbericht_Assistent.md`
- `MVP_02_Interviewstand_Voice_Architektur_und_Login.md`
- `MVP_03_Testkandidaten_STT_TTS_LLM.md`

Der Fokus dieses Dokuments liegt auf:

- aktueller LLM-Provider-Annahme
- Umgang mit Gemini
- lokale OpenAI-kompatible API als zweite AI-Variante
- lokale LLM-Architektur mit zwei Schichten
- Datenschutz und DSGVO-Einordnung im MVP
- Mock-Daten im MVP
- temporärer Umgang mit Roh-Audio
- offene Punkte für das Gespräch mit Ofer

Wichtig: Dieses Dokument korrigiert die vorherige Annahme, dass Gemini bereits fest als Pflichtsäule eingeplant ist. Diese Frage bleibt bis zum 1:1-Gespräch mit Ofer offen.

## 2. Aktuelle Provider-Arbeitsannahme

Für den weiteren Konzeptstand wird vorerst mit zwei AI-Provider-Varianten geplant:

| Variante | Rolle |
|---|---|
| OpenAI | externer API-Provider und erste stabile Variante für den geführten Dialogworkflow |
| lokale OpenAI-kompatible API | lokale Alternative, zum Beispiel über LM Studio |

Gemini wird vorerst nicht als feste Kernvariante weitergeplant.

Grund:

- Ofer hat zunächst auf Gemini Free Tier verwiesen.
- Es ist noch nicht geklärt, ob Gemini tatsächlich verpflichtend ist.
- Es ist ebenfalls offen, ob die Projektanforderung zur Provider-Auswahl auch durch OpenAI plus lokale OpenAI-kompatible API erfüllt werden kann.

Arbeitsannahme:

> Bis zur Klärung mit Ofer wird der MVP mit OpenAI und einer lokalen OpenAI-kompatiblen API als zwei AI-Varianten gedacht. Gemini bleibt als möglicher zusätzlicher Provider offen, wird aber nicht als feste technische Säule vorausgesetzt.

## 3. Umgang mit Gemini

Gemini wird nicht verworfen.

Der aktuelle Status ist:

- Gemini ist potenziell gefordert.
- Die Nutzung wäre voraussichtlich über den Free Tier.
- Die konkreten Limits und verfügbaren Modelle sind noch nicht final geklärt.
- Ob Gemini für längere geführte Dialoge ausreichend ist, ist unsicher.

Konzeptionelle Einordnung:

| Punkt | Bewertung |
|---|---|
| Demonstration | wahrscheinlich möglich |
| kurze Testdialoge | wahrscheinlich möglich |
| lange geführte Multi-Turn-Berichte | unsicher |
| stabile Entwicklungsbasis | eher nicht als alleinige Grundlage |
| Pflichtintegration | offen bis Ofer-Gespräch |

Gemini wird im Konzept daher als offener Punkt geführt.

Wenn Ofer bestätigt, dass Gemini mandatory ist, wird Gemini als zusätzlicher Provider integriert.

Wenn Ofer bestätigt, dass OpenAI plus lokale OpenAI-kompatible API ausreicht, bleibt Gemini außerhalb des Kern-MVP.

## 4. Lokale OpenAI-kompatible API

Als zweite ernsthafte AI-Variante wird eine lokale OpenAI-kompatible API vorgesehen.

Beispiel:

- LM Studio

Begründung:

- passt zur local-first-Zielrichtung
- vermeidet zusätzliche API-Kosten
- hält Daten stärker lokal
- ist fachlich interessanter für das Projekt
- kann über OpenAI-kompatible Endpoints in dieselbe Provider-Abstraktion eingebunden werden

Das Backend soll deshalb nicht hart auf OpenAI programmiert werden.

Stattdessen soll es eine Provider-Schicht geben, die mindestens folgende Varianten unterstützt:

- OpenAI API
- lokale OpenAI-kompatible API
- optional später Gemini API

## 5. Lokale LLM-Variante wird zurückgestellt

Die konkrete Auswahl lokaler LLM-Modelle wird vorerst zurückgestellt.

Grund:

- Heute ist Dienstag.
- Das Gespräch mit Ofer findet am Donnerstag statt.
- Vorher soll nicht unnötig konkret auf lokale Modellnamen festgelegt werden.
- Erst soll geklärt werden, welche Provider-Anforderungen für das Abschlussprojekt tatsächlich gelten.

Festlegung:

> Konkrete lokale LLM-Kandidaten werden erst nach dem Gespräch mit Ofer priorisiert.

## 6. Zwei LLM-Schichten bei lokaler Variante

Wenn lokale LLMs eingesetzt werden, soll die Architektur nicht aus drei LLM-Schichten bestehen, sondern aus zwei.

Vorgesehene Schichten:

| Schicht | Aufgabe |
|---|---|
| Frontend-AI / Chat-LLM | führt das Gespräch natürlich mit dem Außendienstler |
| Backend-AI / Analyse-LLM | beobachtet den Chat, extrahiert Informationen, erkennt fehlende Berichtsinhalte und bereitet Strukturierung vor |

Wichtig:

- Die Chat-LLM spricht mit dem Nutzer.
- Die Analyse-LLM unterstützt die strukturierte Auswertung.
- Der eigentliche Prozess wird nicht der LLM überlassen.
- So viel wie möglich wird in Code gelöst.
- Die LLMs werden stark geführt.
- Gerade lokale Modelle sollen nur minimal und gezielt eingesetzt werden.

## 7. Code bleibt führend

Die lokale AI-Variante soll nicht bedeuten, dass die LLM frei über den Prozess entscheidet.

Die Anwendung beziehungsweise der Backend-Code übernimmt:

- Gesprächszustand
- Pflichtfeldlogik
- Statusverwaltung
- Validierung
- Entscheidung, ob ein Bericht vollständig ist
- Entscheidung, welche Rückfrage als nächstes sinnvoll ist
- Übernahme oder Ablehnung strukturierter Vorschläge
- finale Speicherung beziehungsweise Übergabe

Die LLM unterstützt bei:

- natürlicher Gesprächsführung
- Interpretation freier Sprache
- Extraktion
- Formulierung von Rückfragen
- Zusammenfassung
- Formulierung des finalen Berichts

Grundsatz:

> Die LLM interpretiert und formuliert. Der Code führt, validiert und entscheidet.

## 8. Datenschutz im MVP

Datenschutz wird als notwendiger Bestandteil des MVP betrachtet.

Der MVP soll sich an den Grundsätzen der Datenschutzgrundverordnung orientieren.

Gleichzeitig wird für den MVP nicht behauptet, dass er vollständig produktiv DSGVO-konform ist.

Saubere Einordnung:

> Der MVP berücksichtigt Datenschutz und DSGVO-Grundsätze von Beginn an. Ziel ist ein datenschutzbewusster Prototyp. Eine vollständige produktive DSGVO-Konformität wird für den MVP nicht pauschal behauptet, sondern wäre abhängig von finaler technischer Umsetzung, Hosting, Auftragsverarbeitung, Löschkonzept, Zugriffskontrolle und rechtlicher Prüfung.

## 9. Mock-Daten im MVP

Im MVP werden ausschließlich Mock-Daten verwendet.

Das betrifft:

- Demo-Nutzer
- Demo-Kunden
- Demo-Ansprechpartner
- Demo-Angebote
- Demo-Aufträge oder Vorgänge
- Demo-Besuchsberichte
- Demo-Chatverläufe
- Demo-Innendienstaufgaben

Damit verarbeitet der MVP keine echten Kunden- oder Mitarbeiterdaten.

Trotzdem soll die Architektur so gedacht werden, dass sie später mit echten Daten datenschutzbewusst umgehen kann.

## 10. Audio als temporäres Arbeitsmaterial

Roh-Audio ist im MVP kein fachlicher Langzeitdatensatz.

Roh-Audio darf temporär existieren, damit Speech-to-Text durchgeführt und ein Gespräch rekonstruiert werden kann, solange der Bericht noch offen ist.

Regel:

> Roh-Audio ist temporäres Arbeitsmaterial. Persistiert werden sollen Chattext, Transkript, strukturierter Draft und finaler Bericht, aber kein dauerhaftes Audioarchiv.

## 11. Speicherort von Audio

Der Speicherort von temporärem Audio ist fachlich relevant.

Zielbild:

| Ort | Umgang |
|---|---|
| Frontend / Smartphone | nur Aufnahmepuffer bis Upload |
| Backend / Server im Netzwerk | temporäre Verarbeitung während der Session beziehungsweise des offenen Berichts |
| Datenbank | keine dauerhafte Roh-Audio-Speicherung |
| Archiv | keine Roh-Audio-Speicherung |

Im MVP-Test kann Frontend und Backend technisch auf demselben Rechner laufen.

Im Zielbild liegt das Backend auf einem Server im Netzwerk, während das Frontend auf dem Smartphone des Außendienstlers läuft.

## 12. Löschung von Audio

Aktuelle Arbeitsannahme:

- Audio darf während eines offenen Besuchsbericht-Chats temporär erhalten bleiben.
- Nach Abschluss oder Abbruch des Berichts wird Audio verworfen.
- Für die KI-Verarbeitung selbst ist das Audio nach der Transkription nicht mehr zwingend erforderlich.
- Die Transkription ist die relevante Arbeitsgrundlage für Chatverlauf, Draft und Bericht.

## 13. Aufbewahrungsfristen

Aufbewahrungsfristen werden im MVP konzeptionell berücksichtigt, aber nicht vollständig technisch umgesetzt.

Für eine spätere produktive Version gilt:

- gesetzliche Aufbewahrungsfristen müssen geprüft werden
- Löschkonzepte müssen definiert werden
- technische Löschroutinen müssen implementiert werden
- Datenschutzanforderungen müssen rechtlich geprüft werden

Für den MVP gilt:

> Das Thema Aufbewahrungsfristen ist im Gedankenkonstrukt berücksichtigt, wird aber in der MVP-Phase nicht vollständig ausprogrammiert.

## 14. Daten, die dauerhaft gespeichert werden

Im MVP sollen dauerhaft beziehungsweise für die Demo nachvollziehbar gespeichert werden:

- textueller Chatverlauf
- Transkripte aus Spracheingaben als normale Chatnachrichten
- strukturierter Berichtsentwurf
- Status des Berichts
- final bestätigter Besuchsbericht
- Nutzerkontext
- relevante Mock-CRM-Bezüge

Nicht dauerhaft gespeichert werden:

- Roh-Audio als Langzeitarchiv
- TTS-Audio als Langzeitarchiv
- echte Kunden- oder Mitarbeiterdaten

## 15. Offene Punkte für Ofer

Im Gespräch mit Ofer sollen folgende Punkte geklärt werden:

1. Ist Gemini tatsächlich mandatory?
2. Reicht OpenAI plus lokale OpenAI-kompatible API als Provider-Auswahl?
3. Welche OpenAI-Modelle dürfen oder sollen verwendet werden?
4. Falls Gemini notwendig ist: Welche Gemini-Modelle stehen im Free Tier konkret zur Verfügung?
5. Ist die local-first-Variante über LM Studio als zweite AI-Alternative für das Abschlussprojekt akzeptabel?

## 16. Aktualisierte offene Fragen

Nach aktuellem Stand bleiben folgende Fragen offen:

1. Welche konkreten OpenAI-Modelle werden eingesetzt?
2. Wird Gemini nach Ofer-Gespräch Pflicht oder optional?
3. Welche lokalen LLMs werden nach Ofer-Gespräch über LM Studio getestet?
4. Wie wird der Provider technisch im Backend abstrahiert?
5. Wie genau wird der strukturierte Draft technisch modelliert?
6. Wie sieht der API-Vertrag zwischen Assistant Backend und Placeholder-CRM aus?
7. Welche eNVenta-orientierten Felder ergeben sich aus dem Input von Bernd?
8. Wie detailliert wird das Lösch- und Aufbewahrungskonzept im finalen Projektbericht beschrieben?

## 17. Zusammenfassung

Der aktuelle Stand ist:

Für die LLM-Provider wird vorerst mit OpenAI und einer lokalen OpenAI-kompatiblen API wie LM Studio geplant. Gemini bleibt offen, bis im 1:1-Gespräch mit Ofer geklärt ist, ob es tatsächlich verpflichtend ist.

Die lokale LLM-Variante wird bis nach dem Ofer-Gespräch nicht weiter auf konkrete Modellnamen festgelegt. Wenn lokale Modelle eingesetzt werden, soll eine zweischichtige Architektur genutzt werden: eine Chat-LLM für die Nutzerinteraktion und eine Analyse-LLM für Extraktion und Berichtsvorbereitung. Die eigentliche Prozesssteuerung bleibt im Code.

Datenschutz wird im MVP berücksichtigt, aber nicht als vollständig produktiv DSGVO-konform behauptet. Der MVP arbeitet ausschließlich mit Mock-Daten. Roh-Audio darf temporär während eines offenen Berichts existieren, wird aber nicht als dauerhafter Datensatz gespeichert. Aufbewahrungsfristen werden konzeptionell berücksichtigt und nach dem MVP an gesetzlichen Anforderungen ausgerichtet.
