# MVP 05: Berichtsentwurf und Conversation State

## 1. Zweck dieses Dokuments

Dieses Dokument hält den aktuellen Konzeptstand zum fachlichen Berichtsentwurf und zum Conversation State des Besuchsbericht-Assistenten fest.

Es baut auf den vorherigen Konzeptständen auf, insbesondere:

- Grundidee
- Problemstellung
- Ziel des MVP
- Interviewstand Voice, Architektur und Login
- Testkandidaten STT, TTS und LLM
- Providerstrategie, Datenschutz und lokale LLMs

Der Fokus dieses Dokuments liegt nicht auf Provider-Auswahl, Datenschutzdetails oder konkreten lokalen Modellen, sondern auf der Frage:

> Welche fachlichen Informationen muss der Assistent während eines Besuchsbericht-Chats erfassen, verfolgen, bewerten, korrigieren und am Ende zur Bestätigung vorlegen?

## 2. Grundprinzip

Der Besuchsbericht-Assistent arbeitet dialoggesteuert.

Der Außendienstler soll frei starten können. Das System soll aus der ersten Aussage alle bereits enthaltenen Informationen erkennen und daraus einen strukturierten Berichtsentwurf aufbauen.

Das System fragt nicht formularartig jeden Punkt nacheinander ab. Es fragt nur dann nach, wenn Informationen fehlen, unklar sind oder widersprüchlich wirken.

Wenn der Außendienstler in seiner ersten Aussage bereits alle notwendigen Informationen liefert, soll keine unnötige weitere Interaktion folgen. In diesem Fall erstellt das System direkt eine blockweise Zusammenfassung und fragt nach der finalen Bestätigung.

## 3. Fachliche Berichtsblöcke

Der MVP arbeitet mit elf fachlichen Berichtsblöcken.

Intern werden alle Namen auf Englisch geführt. Code, Funktionsnamen, Variablennamen, Klassen, Enums, Statuswerte und Docstrings sollen im späteren Programm Englisch sein und sich an PEP 8 orientieren.

```python
class ReportSection(str, Enum):
    CUSTOMER_CONTEXT = "customer_context"
    CONTACTS = "contacts"
    VISIT_REASON = "visit_reason"
    SUMMARY = "summary"
    OUTCOME = "outcome"
    NEXT_ACTION = "next_action"
    OFFER_REFERENCE = "offer_reference"
    ORDER_REFERENCE = "order_reference"
    RATINGS = "ratings"
    FINAL_REPORT = "final_report"
    USER_CONFIRMATION = "user_confirmation"
```

| Section | Fachliche Bedeutung |
|---|---|
| `customer_context` | Kunde, bestehender Lead, neue Adresse oder neuer Lead aus Sales-Perspektive |
| `contacts` | Ansprechpartner oder Teilnehmer des Besuchs |
| `visit_reason` | Anlass des Besuchs |
| `summary` | Gesprächszusammenfassung |
| `outcome` | Ergebnis, Vereinbarung oder Gesprächsausgang |
| `next_action` | Nächste Aktion, Follow-up oder Nachfassdatum |
| `offer_reference` | Angebotsbezug, falls relevant |
| `order_reference` | Auftragsbezug, falls relevant |
| `ratings` | Sechs Bewertungsfelder mit Begründung |
| `final_report` | Ausformulierter Besuchsbericht |
| `user_confirmation` | Finale Bestätigung durch den Außendienstler |

## 4. Angebot und Auftrag werden getrennt

Angebotsbezug und Auftragsbezug werden bewusst getrennt.

Ein Angebot und ein Auftrag sind aus Sales-Sicht unterschiedliche fachliche Brillen.

Ein Angebotsbezug bedeutet typischerweise:

- Vorverkaufsphase
- Abschlusschance
- Angebot wurde besprochen
- Angebot soll angepasst werden
- Angebot soll erstellt werden
- Verwirklichung steht noch aus

Ein Auftragsbezug bedeutet typischerweise:

- Es gibt bereits einen Auftrag
- Es gab Gesprächsbedarf zu einem laufenden oder abgeschlossenen Vorgang
- Etwas ist nicht rund gelaufen
- Es gibt Klärungs-, Änderungs-, Reklamations- oder Nachbesprechungsbedarf

Deshalb gibt es zwei getrennte Sections:

- `offer_reference`
- `order_reference`

Beide Sections sind optional beziehungsweise kontextabhängig.

Wenn der Nutzer ein Angebot erwähnt, wird `offer_reference` aktiv verfolgt.

Wenn der Nutzer einen Auftrag erwähnt, wird `order_reference` aktiv verfolgt.

Wenn aus dem Kontext klar hervorgeht, dass weder Angebot noch Auftrag relevant sind, werden beide Sections auf `not_applicable` gesetzt.

Wenn der Kontext dazu nichts hergibt, fragt der Assistent einmal nach.

## 5. Section Status

Jeder Berichtsblock bekommt einen internen Status.

Dieser Status dient der Gesprächssteuerung und dem Debugging. Er ist keine normale CRM-Oberfläche.

```python
class SectionStatus(str, Enum):
    OPEN = "open"
    DETECTED = "detected"
    UNCLEAR = "unclear"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    NOT_APPLICABLE = "not_applicable"
```

| Status | Bedeutung |
|---|---|
| `open` | Für diesen Block fehlt noch verwertbarer Inhalt |
| `detected` | Das System hat Inhalt erkannt, aber noch nicht final bestätigt |
| `unclear` | Das System ist unsicher oder erkennt einen Widerspruch |
| `confirmed` | Der Inhalt wurde bestätigt oder nicht widersprochen |
| `corrected` | Der Nutzer hat den Inhalt korrigiert |
| `not_applicable` | Der Block ist für diesen Bericht nicht relevant |

## 6. Dialoglogik

Der Ablauf folgt diesem Prinzip:

1. Der Nutzer startet einen neuen Chat.
2. Das System stellt die erste Frage sichtbar als Text und per Text-to-Speech.
3. Der Nutzer antwortet per Textchat oder Speech-to-Text.
4. Das System analysiert die Aussage.
5. Bereits enthaltene Informationen werden den passenden Berichtsblöcken zugeordnet.
6. Das System aktualisiert den Conversation State.
7. Das System fragt nur fehlende, unklare oder widersprüchliche Informationen nach.
8. Bewertungen werden aus dem Gespräch abgeleitet und begründet.
9. Der Nutzer kann jederzeit korrigieren.
10. Am Ende folgt eine blockweise Zusammenfassung.
11. Erst nach ausdrücklicher Bestätigung wird der Bericht finalisiert oder übergeben.

Eine Korrektur hat Vorrang vor der aktuell gestellten Frage.

Wenn der Nutzer also auf eine Frage zur nächsten Aktion eigentlich eine vorherige Angabe korrigiert, muss zuerst die Korrektur verarbeitet werden. Danach kehrt das System zur offenen Frage oder zum nächsten fehlenden Block zurück.

## 7. User Intents

Jede Nutzereingabe wird intern als Intent klassifiziert.

```python
class UserIntent(str, Enum):
    ANSWER = "answer"
    CORRECTION = "correction"
    ADDITIONAL_INFO = "additional_info"
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"
    REPEAT = "repeat"
    CANCEL = "cancel"
    UNKNOWN = "unknown"
```

| Intent | Bedeutung |
|---|---|
| `answer` | Nutzer beantwortet die aktuelle Frage |
| `correction` | Nutzer korrigiert eine frühere oder aktuelle Information |
| `additional_info` | Nutzer liefert zusätzliche Information, die nicht direkt zur aktuellen Frage passen muss |
| `confirmation` | Nutzer bestätigt eine Zusammenfassung oder einen Inhalt |
| `rejection` | Nutzer lehnt eine Zusammenfassung, Speicherung oder Annahme ab |
| `repeat` | Nutzer möchte die letzte Frage oder Zusammenfassung erneut hören |
| `cancel` | Nutzer bricht den aktuellen Vorgang ab |
| `unknown` | Intent ist nicht sicher erkennbar |

## 8. Intent Confidence

Die Intent-Erkennung erhält einen Confidence Score.

Dieser Score ist keine mathematisch belastbare Wahrscheinlichkeit. Er ist eine interne Einschätzung der Entscheidungssicherheit und dient Debugging, Nachvollziehbarkeit und späterer Nachjustierung.

```python
intent_confidence: float
```

Vorläufige Schwellenwerte:

| Score | Verhalten |
|---|---|
| ab `0.75` | direkt verarbeiten |
| `0.45` bis `0.74` | vorsichtig bestätigen oder Rückfrage einbauen |
| unter `0.45` | gezielt nachfragen |

Der Confidence Score wird im Debug-Log ausgegeben.

## 9. Target Sections

Jede Intent-Erkennung soll zusätzlich angeben, welche Berichtsblöcke betroffen sind.

Da eine Nutzeraussage mehrere Blöcke betreffen kann, wird mit einer Liste gearbeitet.

Beispiel:

```json
{
  "intent": "additional_info",
  "intent_confidence": 0.78,
  "target_sections": ["summary", "next_action", "ratings"]
}
```

Beispiel für eine Korrektur:

```json
{
  "intent": "correction",
  "intent_confidence": 0.82,
  "target_sections": ["contacts"],
  "text": "Nein, das war nicht Frau Keller, sondern Herr Becker."
}
```

Damit kann das System sauber entscheiden, welche Berichtsblöcke aktualisiert werden und welche Status neu bewertet werden müssen.

## 10. Customer Context

Der Block `customer_context` ist Pflicht.

Fachlich orientiert sich dieser Bereich an der eNVenta-Logik AKL.

AKL steht in diesem Kontext für:

- Adresse
- Kunde
- Lieferant

Für den MVP wird diese Logik aus der Sales-Perspektive betrachtet.

Lieferanten sind im aktuellen MVP nicht aktiv im Fokus.

Der MVP berücksichtigt:

- bestehende Kunden
- bestehende Leads beziehungsweise bestehende Adressen
- neue Leads beziehungsweise neue Adressen
- unklare Fälle

```python
class CustomerContextType(str, Enum):
    EXISTING_CUSTOMER = "existing_customer"
    EXISTING_LEAD = "existing_lead"
    NEW_LEAD = "new_lead"
    UNCLEAR = "unclear"
```

| Typ | Bedeutung |
|---|---|
| `existing_customer` | Kunde ist im System vorhanden und kann referenziert werden |
| `existing_lead` | Lead oder Adresse ist im System vorhanden und kann referenziert werden |
| `new_lead` | Neuer Lead oder neue Adresse wurde genannt, aber nicht automatisch angelegt |
| `unclear` | System kann nicht sicher entscheiden und muss nachfragen |

## 11. Regeln für Leads und Adressen

Neue Leads, Kunden oder Adressen werden durch das Programm nicht automatisch angelegt.

Wenn der Außendienstler bei einem neuen Lead war, wird der Besuch erfasst, aber nicht als vollständig abgeschlossener CRM-Bericht behandelt.

Stattdessen entsteht:

- ein unvollständiger oder wartender Besuchsbericht
- eine Wiedervorlage beziehungsweise Aufgabe für den Innendienst

Beispiele für notwendige Innendienstarbeit:

- Stammdaten vervollständigen
- Lead oder Adresse prüfen
- Ansprechpartner ergänzen
- potenzielles Angebot anlegen
- Details telefonisch klären

Wenn ein bestehender Lead oder eine bestehende Adresse im System vorhanden ist, kann der Bezug hergestellt werden.

Auch dann kann eine Innendienstaufgabe entstehen, wenn für die weitere Bearbeitung Informationen fehlen oder ein Angebot erstellt werden muss.

## 12. Contacts

Der Block `contacts` ist Pflicht.

Der Besuchsbericht muss enthalten, mit wem gesprochen wurde.

Dies kann ein bestehender Ansprechpartner sein oder eine neu genannte Person.

Wenn eine Person neu ist oder nicht sauber im System gefunden wird, legt der Assistent sie nicht automatisch als Stammdatensatz an.

Stattdessen wird der Bericht mit Hinweis erstellt und bei Bedarf eine Innendienstaufgabe erzeugt.

## 13. Innendienst-Wiedervorlagen

Für den MVP reichen vier Task-Typen.

```python
class InsideSalesTaskType(str, Enum):
    COMPLETE_MASTER_DATA = "complete_master_data"
    CREATE_OFFER = "create_offer"
    CLARIFY_DETAILS = "clarify_details"
    FOLLOW_UP_CALL = "follow_up_call"
```

| Task Type | Zweck |
|---|---|
| `complete_master_data` | Kunde, Lead, Adresse oder Ansprechpartner muss gepflegt oder vervollständigt werden |
| `create_offer` | Aus dem Gespräch ergibt sich ein Angebotsbedarf |
| `clarify_details` | Inhalte sind fachlich noch unklar und müssen geklärt werden |
| `follow_up_call` | Rückruf oder Nachfassen ist erforderlich |

## 14. Report Status

Ein Bericht bekommt einen fachlichen Status.

```python
class ReportStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    INSIDE_SALES_INPUT_REQUIRED = "inside_sales_input_required"
    BLOCKED = "blocked"
    CONFIRMED = "confirmed"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"
```

| Status | Bedeutung |
|---|---|
| `in_progress` | Gespräch läuft oder ist offen |
| `ready_for_review` | alle nötigen Inhalte sind vorhanden, finale Prüfung steht an |
| `inside_sales_input_required` | Bericht ist fachlich erfasst, braucht aber Innendienst-Zuarbeit |
| `blocked` | Bericht kann aktuell nicht sinnvoll abgeschlossen werden |
| `confirmed` | Außendienstler hat final bestätigt |
| `submitted` | Bericht wurde an die CRM-Gegenstelle gespeichert oder übergeben |
| `cancelled` | Bericht wurde abgebrochen |

## 15. Bedeutung von `inside_sales_input_required`

`inside_sales_input_required` ist kein Fehlerstatus.

Der Status bedeutet:

- Der Außendienstler hat seine Erfassung abgeschlossen.
- Der Besuchsbericht ist fachlich angelegt.
- Der Bericht ist im CRM-System aber noch nicht final erledigt.
- Innendienst muss etwas tun.
- Der Chat gilt nicht als abgeschlossener Besuchsbericht.
- Der Status bleibt bestehen, bis die CRM-Gegenstelle den Bericht als erledigt oder final zurückmeldet.

Beispiele:

- neuer Lead muss geprüft werden
- Stammdaten fehlen
- Ansprechpartner muss angelegt oder vervollständigt werden
- Angebot muss erstellt werden
- Details müssen geklärt werden
- Rückruf ist nötig

Eine spätere UI könnte dafür einen eigenen Bereich bieten, damit der Außendienstler sehen kann, welche seiner Berichte auf Innendienst-Zuarbeit warten.

Dieser separate View ist für den MVP aber noch keine festgelegte Umsetzung.

## 16. Debug-Informationen

Für den Weg zum MVP sind Debug-Informationen notwendig.

Im ersten Schritt reicht Backend-Logging in der Konsole.

Es wird keine eigene Debug-UI und keine Admin-Oberfläche vorausgesetzt.

Die technische Umsetzung soll über Python-`logging` erfolgen, nicht über verstreute `print()`-Statements.

Pro Turn sollen mindestens folgende Informationen geloggt werden:

- `chat_id`
- `user_id`
- `ai_provider`
- eingehender Text oder STT-Transkript
- erkannter Intent
- `intent_confidence`
- `target_sections`
- aktualisierte Section Status
- fehlende Sections
- nächste Systemfrage
- Fehler oder Unsicherheiten

## 17. Bewertungsblock

Der Block `ratings` ist Pflicht.

Der MVP arbeitet mit sechs Bewertungsfeldern.

| Bewertungsfeld | Skala | Bedeutung |
|---|---|---|
| Vertriebschance | 1 bis 10 | Wie relevant ist die Chance vertrieblich? |
| Gesprächsstimmung | 1 bis 10 | Wie positiv oder schwierig war die Stimmung? |
| Priorität | 1 bis 10 | Wie stark muss Aufmerksamkeit auf den Vorgang gelegt werden? |
| Abschlusswahrscheinlichkeit | 1 bis 10 | Wie wahrscheinlich ist ein Abschluss? |
| Handlungsbedarf | 1 bis 10 | Wie dringend ist weiteres Handeln? |
| Kundenzufriedenheit | 1 bis 10 | Wie zufrieden wirkt der Kunde? |

Die Zahlenwerte werden vom System aus dem Gespräch abgeleitet.

Die KI soll die Bewertungen kurz begründen, damit der Außendienstler Fehlinterpretationen erkennen und korrigieren kann.

Der Freitextbericht muss inhaltlich zu den Bewertungswerten passen.

Die Begründung muss nicht zwingend als eigener CRM-Textblock gespeichert werden. Sie ist primär Teil des Dialogs und der Nutzerkontrolle.

## 18. Finale Review-Logik

Die finale Zusammenfassung erfolgt blockweise.

Es wird nicht einfach ein rohes JSON vorgelesen.

Das System liest beziehungsweise zeigt die relevanten fachlichen Abschnitte:

- Kunde beziehungsweise Lead-Kontext
- Ansprechpartner oder Teilnehmer
- Anlass des Besuchs
- Gesprächszusammenfassung
- Ergebnis oder Vereinbarung
- nächste Aktion und Follow-up
- Angebotsbezug, falls relevant
- Auftragsbezug, falls relevant
- Bewertungen mit Begründung
- finaler Freitextbericht

Erst danach fragt das System nach der finalen Bestätigung.

Ohne explizite Bestätigung wird kein Bericht final gespeichert oder übergeben.

## 19. Aktueller Arbeitsstand

Für den Abschnitt Berichtsentwurf und Conversation State sind damit festgelegt:

- fachliche Report Sections
- getrennte Offer- und Order-References
- Section Status
- Dialoglogik
- User Intents
- Intent Confidence
- Target Sections
- Customer Context mit Kunde, bestehendem Lead und neuem Lead
- keine automatische Anlage von Kunden, Leads oder Ansprechpartnern
- vier minimale Innendienst-Task-Typen
- Report Status inklusive `inside_sales_input_required`
- Debug-Logging im Backend
- Bewertungsblock mit sechs Pflichtbewertungen
- blockweise finale Review-Logik

## 20. Noch offen im Anschluss

Folgende Punkte bleiben nach diesem Abschnitt offen:

1. Wie genau wird der strukturierte Draft technisch als Datenobjekt modelliert?
2. Welche Felder enthält der Draft pro Section konkret?
3. Welche API-Endpunkte braucht das Backend für Chat, Draft, Review und Submission?
4. Wie wird der API-Vertrag zur Placeholder-CRM-Gegenstelle geschnitten?
5. Welche eNVenta-orientierten Felder ergeben sich aus dem Input von Bernd?
6. Welche konkreten OpenAI-Modelle werden verwendet?
7. Wird Gemini nach dem Gespräch mit Ofer Pflicht oder optional?
8. Welche lokalen LLMs werden nach dem Ofer-Gespräch getestet?
9. Wie detailliert wird der spätere Innendienst-Status-View im MVP berücksichtigt?
