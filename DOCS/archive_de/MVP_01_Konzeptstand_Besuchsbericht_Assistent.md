# MVP Konzeptstand: Sprachgeführter Besuchsbericht Assistent für B2B Außendienst

## 1. Arbeitstitel

**Voice Guided CRM Visit Report Assistant**

Alternativer deutscher Titel:

**Sprachgeführter Besuchsbericht Assistent für B2B Außendienst und CRM Übergabe**

## 2. Grundidee

Das Projekt entwickelt eine mobile Web App für Außendienstmitarbeiter im B2B Vertrieb. Die App ermöglicht es, direkt nach einem Kundentermin einen Besuchsbericht per geführtem Gespräch zu erfassen.

Der Außendienstler soll nach dem Termin möglichst wenig tippen müssen. Nach dem Login startet er einen neuen Bericht und spricht frei los. Die KI erkennt relevante Informationen aus dem gesprochenen Bericht, stellt gezielte Rückfragen, validiert Stammdaten gegen ein Muster CRM und erzeugt am Ende einen strukturierten Besuchsbericht.

Der Bericht wird vor dem Speichern vollständig vorgelesen. Erst nach expliziter Bestätigung durch den Außendienstler wird der Bericht gespeichert beziehungsweise an das Muster CRM übergeben.

Das Projekt baut kein eigenes CRM. Es baut eine mobile Erfassungs und Übergabeschicht, die beispielhaft an ein Muster CRM angebunden wird.

## 3. Problemstellung

Außendienstmitarbeiter erstellen Besuchsberichte häufig verspätet, unvollständig oder uneinheitlich. Der Grund ist, dass CRM Formulare auf mobilen Geräten oder nach langen Terminen als störend empfunden werden.

Dadurch entstehen mehrere Probleme:

- Informationen werden erst später dokumentiert, wenn Details nicht mehr frisch sind.
- Besuchsberichte sind unterschiedlich ausführlich und unterschiedlich formuliert.
- Pflichtfelder werden unvollständig oder ungenau gefüllt.
- Wichtige Folgeaktionen gehen verloren oder werden nicht sauber zugeordnet.
- Innendienst und Vertrieb haben nicht immer denselben Informationsstand.
- CRM Daten verlieren an Qualität.

Das Projekt adressiert genau diese Lücke: Frisches Außendienstwissen soll direkt nach dem Termin erfasst und in ein standardisiertes CRM kompatibles Format gebracht werden.

## 4. Ziel des MVP

Der MVP soll zeigen, dass ein Außendienstler einen klassischen B2B Vertriebsbesuch über eine geführte, turn based Gesprächslogik erfassen kann.

Der MVP muss folgende Kernfunktion abbilden:

1. Außendienstler loggt sich in eine mobile Web App ein.
2. Außendienstler startet einen neuen Besuchsbericht.
3. Außendienstler gibt seinen Bericht zunächst frei als Text ein.
4. Das System extrahiert relevante Informationen.
5. Das System führt den Außendienstler durch fehlende Pflichtinformationen.
6. Das System erlaubt Korrekturen jederzeit im Gespräch.
7. Das System validiert Kunden, Ansprechpartner und Angebote gegen eine Muster CRM Datenbank.
8. Das System erzeugt strukturierte CRM Felder und einen ausformulierten Besuchsbericht.
9. Das System liest vor dem Speichern vollständig vor, was gespeichert wird.
10. Der Außendienstler bestätigt per Sprache beziehungsweise im textbasierten MVP per Eingabe.
11. Der Bericht wird in der Datenbank gespeichert.
12. Bei fehlenden Stammdaten oder Folgeaktionen entstehen einfache Innendienstaufgaben.

## 5. Nicht Ziel des MVP

Der MVP soll bewusst kein vollständiges CRM oder ERP nachbauen.

Nicht Bestandteil des MVP:

- Vollständiges CRM System
- Stammdatenpflege durch den Außendienstler
- Innendienst Oberfläche
- Vollständiges Lead Management
- Vollständiges Opportunity Management
- Vollständiges Angebotswesen
- Auftragsanlage
- Echtzeit Audio Streaming
- Vollwertige mobile App mit App Store Deployment
- Komplexe Rollen und Rechteverwaltung
- Produktivfähige CRM Integration in ein echtes ERP
- Visitenkarten OCR als Pflichtbestandteil
- QR Code Visitenkarten Scan als Pflichtbestandteil

## 6. Zielbild über den MVP hinaus

Langfristig soll das Tool als allgemeines, möglichst sprachgesteuertes Erfassungstool für den B2B Außendienst funktionieren.

Mögliche spätere Erweiterungen:

- QR Code Scan von digitalen Visitenkarten
- Fotografieren von Visitenkarten mit OCR Extraktion
- Biometrischer Login über Smartphone Funktionen
- Echte Speech to Text Eingabe
- Text to Speech Ausgabe
- Integration mit realen CRM oder ERP Systemen
- Angebotsanlage über definierte CRM Workflows
- Opportunity oder Lead Qualifizierung
- Kalenderintegration
- Aufgabenübergabe an Innendienstsysteme
- Mehrsprachige UI

Diese Erweiterungen sind konzeptionell relevant, aber im MVP klar nachrangig.

## 7. Fachlicher Scope des MVP

Der MVP startet mit dem klassischen B2B Vertriebsbesuch.

Im Fokus stehen:

- bestehender Kunde
- Ansprechpartner
- Gesprächsanlass
- Besuchszusammenfassung
- Gesprächsergebnis
- nächster Schritt
- Follow up
- Priorität oder Vertriebsbewertung
- optionaler Angebotsbezug
- optionale Innendienstaufgabe

Nicht im Fokus als Hauptfall:

- Serviceeinsatz
- Reklamation
- technischer Supportfall
- vollständige Auftragsabwicklung
- vollständige Neukundenanlage

Solche Fälle können im Gespräch erkannt und als Aufgabe oder Sonderfall dokumentiert werden, aber sie sind nicht der Hauptpfad des MVP.

## 8. Branchenkontext

Das Muster CRM wird bewusst neutral als B2B Vertriebskontext modelliert.

Es soll nicht auf eine bestimmte Branche zugeschnitten sein.

Nicht spezifisch:

- PV
- Maschinenbau
- Software
- Großhandel
- Handwerk
- Industriebedarf

Stattdessen wird ein generischer B2B Kontext verwendet, der Kunden, Ansprechpartner, Angebote und Besuchsberichte enthält.

## 9. Grundprinzip: Kein CRM Ersatz

Das Tool ist kein CRM Ersatz.

Das Tool ist eine Erfassungs, Strukturierungs und Übergabeschicht.

Die Rolle des Tools:

- Sprache oder Text entgegennehmen
- Gespräch führen
- Informationen extrahieren
- fehlende Informationen abfragen
- Informationen standardisieren
- Stammdaten gegen das Muster CRM prüfen
- Besuchsbericht erzeugen
- Follow up Aufgaben vorbereiten
- Daten nach Bestätigung speichern oder übergeben

Die Rolle des Muster CRM:

- Kunden bereitstellen
- Ansprechpartner bereitstellen
- Angebote bereitstellen
- Besuchsberichte aufnehmen
- Innendienstaufgaben aufnehmen

## 10. Grundprinzip: Hands free nach Start

Nach dem Start eines Besuchsberichts soll der Außendienstler seine Hände möglichst nicht mehr benutzen müssen.

Im finalen Zielbild funktioniert der Ablauf wie ein Telefonat über eine Freisprechanlage:

1. Außendienstler startet den Bericht.
2. Außendienstler spricht frei.
3. System antwortet per Text to Speech.
4. Außendienstler korrigiert oder ergänzt per Sprache.
5. System führt weiter durch den Bericht.
6. System liest die finale Version vollständig vor.
7. Außendienstler bestätigt per Sprache.
8. System speichert den Bericht.

Der MVP beginnt textbasiert, aber die Architektur muss so aufgebaut sein, dass Speech to Text und Text to Speech als Layer darüber gelegt werden können.

## 11. Technischer MVP Ansatz: Text zuerst, Voice später

Die erste funktionierende Version soll textbasiert umgesetzt werden.

Das bedeutet:

- Nutzer gibt Text ein.
- KI antwortet als Text.
- Chatverlauf ist sichtbar.
- Conversation State wird gespeichert.
- Bericht wird strukturiert erzeugt.
- Bericht wird nach Bestätigung gespeichert.

Speech to Text und Text to Speech werden als spätere Layer behandelt:

- Speech to Text ersetzt die manuelle Texteingabe.
- Text to Speech liest die KI Antwort vor.
- Der Core Workflow bleibt gleich.

Diese Trennung reduziert das technische Risiko und erleichtert Debugging.

## 12. Turn based Gesprächsmodell

Das System arbeitet turn based, nicht als Echtzeit Streaming Voice Chat.

Ein Turn besteht aus:

1. Nutzeräußerung
2. Transkription oder Texteingabe
3. Verarbeitung durch Backend und LLM
4. Aktualisierung des Conversation State
5. Antwort oder Rückfrage durch die KI
6. sichtbare Protokollierung im Chatverlauf

Im Voice Zielbild wird jeder Turn zusätzlich durch Speech to Text und Text to Speech ergänzt.

Echtzeit Audio Streaming ist nicht Bestandteil des MVP.

## 13. Gesprächsverhalten der KI

Die KI soll nicht einfach ein starres Formular abfragen.

Sie soll ein natürliches Gespräch führen und gleichzeitig intern Pflichtfelder und fachliche Routen abarbeiten.

Grundregeln:

- Der Außendienstler darf frei lossprechen.
- Die KI extrahiert bereits genannte Informationen.
- Bereits erkannte Informationen werden nicht unnötig erneut abgefragt.
- Unsichere Informationen werden bestätigt.
- Fehlende Informationen werden gezielt erfragt.
- Korrekturen sind jederzeit möglich.
- Nach jeder Korrektur bestätigt die KI die Änderung.
- Die KI führt anschließend zum nächsten fehlenden Punkt weiter.

Beispiel:

Nutzer:

> Ich war heute bei NordTech und habe mit Frau Keller gesprochen. Es ging um das offene Angebot für die Rahmenvereinbarung.

KI:

> Ich habe verstanden: Kunde ist NordTech, Ansprechpartnerin ist Frau Keller, und Anlass war die Besprechung eines offenen Angebots zur Rahmenvereinbarung. Ist das korrekt?

Nutzer:

> Ja.

KI:

> Alles klar. Ging es um ein konkretes Angebot mit Angebotsnummer?

## 14. Korrekturen im Gespräch

Korrekturen müssen jederzeit möglich sein.

Beispiele:

- „Nein, der Ansprechpartner war Herr Becker.“
- „Korrigiere: Die Priorität ist hoch.“
- „Das war kein Angebot, sondern ein Erstgespräch.“
- „Das Follow up ist nicht morgen, sondern nächste Woche Dienstag.“
- „Streich das mit dem Rabatt.“
- „Formuliere das neutraler.“

Eine Korrektur hat Vorrang vor der aktuell gestellten Frage.

Wenn die KI gerade nach der nächsten Aktion fragt und der Nutzer zuerst eine frühere Information korrigiert, muss die Korrektur verarbeitet werden. Danach kehrt das System zur nächsten offenen Frage zurück.

## 15. Finaler Review vor dem Speichern

Vor dem Speichern muss die KI vollständig mitteilen, was gespeichert wird.

Der finale Review muss enthalten:

- alle relevanten strukturierten CRM Felder
- den vollständigen ausformulierten Besuchsbericht
- Angebotsverknüpfungen oder fehlende Angebotsreferenzen
- Stammdatenwarnungen
- geplante Innendienstaufgaben
- Berichtstatus
- Sprache des finalen Berichts
- Hinweis, ob der Bericht final gespeichert oder wegen Stammdatenprüfung blockiert wird

Erst danach darf das System fragen:

> Soll ich den Besuchsbericht genau so speichern?

Mögliche Nutzerantworten:

- „Ja, speichern.“
- „Nein, ändere die Priorität auf hoch.“
- „Nein, der Ansprechpartner war Herr Becker.“
- „Lies den Bericht nochmal vor.“
- „Abbrechen.“

Ohne explizite Bestätigung wird kein finaler Bericht gespeichert oder übergeben.

## 16. Sprache und Mehrsprachigkeit

Das System soll Deutsch und Englisch berücksichtigen.

Es gibt drei getrennte Sprachebenen:

| Ebene | Regel |
|---|---|
| Gesprächssprache | folgt der Sprache des Außendienstlers |
| Interne Struktur | sprachneutrale Codes |
| Finale Berichtssprache | kommt aus dem Kundenstamm |

Beispiel:

Der Außendienstler spricht Deutsch.

Der Kunde hat im CRM `customer_language = en`.

Dann führt die KI das Gespräch auf Deutsch, erzeugt den finalen CRM Bericht aber auf Englisch.

Interne Werte werden nicht sprachabhängig gespeichert.

Beispiel:

```json
{
  "visit_type": "on_site",
  "priority": "medium",
  "reason_code": "offer_follow_up"
}
```

Nicht:

```json
{
  "visit_type": "Vor Ort",
  "priority": "mittel",
  "reason_code": "Angebotsnachfassung"
}
```

## 17. Muster CRM Daten

Das Muster CRM soll bewusst klein bleiben.

Geplante Datenbereiche:

- Außendienstler
- Kunden
- Ansprechpartner
- Angebote
- Besuchsberichte
- Chatverläufe
- strukturierte Berichtsentwürfe
- Innendienstaufgaben

Das Muster CRM soll ungefähr 3 bis 4 Kunden enthalten.

Jeder Kunde soll 1 bis 3 Ansprechpartner haben.

Einige Kunden sollen offene Angebote haben, damit Angebotsverknüpfungen validiert werden können.

## 18. Validierung gegen Muster CRM

Das System soll erkannte Namen und Referenzen gegen das Muster CRM prüfen.

Validierungsfälle:

| Fall | Verhalten |
|---|---|
| Kunde erkannt und vorhanden | Kunde wird verknüpft |
| Kunde erkannt, aber nicht eindeutig | KI fragt nach |
| Kunde unbekannt | KI klärt, ob neuer Lead oder Stammdatenfall |
| Ansprechpartner erkannt und vorhanden | Ansprechpartner wird verknüpft |
| Ansprechpartner unbekannt | KI fragt, ob neuer Ansprechpartner |
| Angebot genannt und vorhanden | Angebot wird verknüpft |
| Angebot genannt, aber nicht vorhanden | Nummer wird gespeichert, Innendiensthinweis möglich |
| Angebot relevant, aber nicht genannt | KI fragt nach Angebotsnummer oder Kontext |

## 19. CRM Objekte und fachliche Unterscheidungen

Das Konzept muss CRM Begriffe sauber trennen.

| Objekt | Bedeutung |
|---|---|
| Kunde | bestehendes Unternehmen im CRM |
| Ansprechpartner | konkrete Person bei einem Kunden |
| Interessent | potenzieller Kunde, noch nicht zwingend CRM Kunde |
| Lead | noch nicht qualifizierter vertrieblicher Hinweis |
| Opportunity | qualifizierte Verkaufschance |
| Angebot | konkretes kaufmännisches Angebot mit Angebotsnummer |
| Auftrag | angenommener oder erfasster Kundenauftrag |
| Aufgabe | interne Folgeaktion |

Der MVP soll diese Begriffe nicht vermischen.

Insbesondere:

- Ein Ansprechpartner ist kein Lead.
- Ein Interessent ist kein bestehender Kunde.
- Ein Angebot ist kein Auftrag.
- Eine Verkaufschance ist nicht automatisch ein Angebot.
- Ein neuer Lead wird nicht automatisch als Kunde angelegt.

## 20. Fachliche Routen im Gespräch

Das System muss im Gespräch erkennen, welche Route gilt.

### 20.1 Normaler Besuchsbericht

Bedingung:

- Kunde existiert
- Ansprechpartner existiert oder ist eindeutig
- kein besonderer Stammdatenkonflikt

Ergebnis:

- Besuchsbericht wird nach Bestätigung gespeichert.

### 20.2 Neuer Ansprechpartner bei bestehendem Kunden

Bedingung:

- Kunde existiert
- Ansprechpartner wurde genannt, ist aber nicht im CRM vorhanden

System fragt:

> Ich finde Frau Müller nicht als Ansprechpartnerin bei diesem Kunden. Ist das ein neuer Ansprechpartner?

Wenn bestätigt:

- Besuchsbericht wird erstellt
- Bericht bleibt gegebenenfalls mit Hinweis versehen
- Innendienstaufgabe zur Kontaktprüfung wird erzeugt

### 20.3 Neuer Lead oder Interessent

Bedingung:

- Gespräch betrifft keinen bestehenden Kunden
- Nutzer beschreibt neuen Interessenten oder Lead

System fragt:

> Handelt es sich um einen neuen Lead oder Interessenten, der vom Innendienst geprüft werden soll?

Wenn bestätigt:

- Besuchsinformationen werden dokumentiert
- eine Innendienstaufgabe `new_lead_review` wird erzeugt
- keine automatische Kundenanlage

### 20.4 Bestehendes Angebot wurde besprochen

Bedingung:

- Nutzer erwähnt ein Angebot, eine Angebotsnummer oder Angebotsnachfassung

System prüft:

- Gibt es das Angebot?
- Gehört das Angebot zum genannten Kunden?
- Ist die Angebotsnummer eindeutig?
- Gibt es mehrere offene Angebote?

Ergebnis:

- Angebot wird verknüpft oder als Referenz im Bericht gespeichert.

### 20.5 Neues Angebot soll erstellt werden

Bedingung:

- Kunde oder Lead möchte ein neues Angebot
- Es gibt noch kein bestehendes Angebot

Ergebnis:

- Besuchsbericht hält Bedarf fest
- Innendienstaufgabe `create_offer` wird erzeugt

### 20.6 Rückruf oder Klärungsaufgabe

Bedingung:

- Es fehlen Informationen
- Kunde soll kontaktiert werden
- Innendienst oder Außendienst soll Details klären

Ergebnis:

- Aufgabe wird erzeugt
- Verantwortlichkeit und Follow up Datum werden abgefragt

## 21. Pflichtfelder für den Besuchsbericht

Pflichtfelder im klassischen B2B Vertriebsbesuch:

| Feld | Beschreibung |
|---|---|
| Kunde oder Lead Kontext | bestehender Kunde oder neuer Lead Fall |
| Ansprechpartner oder Teilnehmer | beteiligte Person beim Kunden |
| Außendienstler | aus Login Kontext |
| Besuchsdatum | Datum des Besuchs |
| Besuchsart | vor Ort, Telefon, Video, Messe, sonstiges |
| Besuchsanlass | Grund des Gesprächs |
| Zusammenfassung | was wurde besprochen |
| Ergebnis oder Vereinbarung | was kam heraus |
| nächste Aktion | was passiert als nächstes |
| Follow up Datum | wann wird nachgefasst |
| Priorität oder Vertriebsbewertung | niedrig, mittel, hoch oder vergleichbar |
| finaler Berichtstext | ausformulierte CRM Dokumentation |
| Nutzerbestätigung | explizite Freigabe vor Speicherung |

Kontextabhängige Pflichtfelder:

| Auslöser | Zusatzfeld |
|---|---|
| Angebot wurde besprochen | Angebotsnummer oder Angebotsreferenz |
| neues Angebot nötig | Angebotsaufgabe mit Beschreibung |
| neuer Ansprechpartner | Innendienstaufgabe zur Kontaktprüfung |
| neuer Lead | Innendienstaufgabe zur Leadprüfung |
| unklare Stammdaten | Klärungsstatus und Aufgabe |
| offene Details | Rückruf oder Klärungsaufgabe |

## 22. Strukturierter Output

Das System erzeugt zwei Arten von Output.

### 22.1 Strukturierte CRM Felder

Diese dienen der maschinellen Verarbeitung.

Beispiel:

```json
{
  "customer_id": "CUST-1001",
  "contact_id": "CONT-2001",
  "sales_user_id": "USER-001",
  "visit_date": "2026-06-19",
  "visit_type": "on_site",
  "reason_code": "offer_follow_up",
  "related_offer_id": "OFF-3001",
  "priority": "medium",
  "follow_up_date": "2026-06-24",
  "status": "pending_confirmation"
}
```

### 22.2 Ausformulierter Besuchsbericht

Dieser dient der menschlichen Nachvollziehbarkeit im CRM.

Beispiel:

> Der Außendiensttermin fand am 19.06.2026 bei NordTech Solutions AG mit Frau Keller statt. Anlass des Gesprächs war die Nachbesprechung des offenen Angebots Q-2026-1007 zur Rahmenvereinbarung. Der Kunde zeigte grundsätzliches Interesse, möchte die Konditionen jedoch intern mit dem Einkauf abstimmen. Als nächste Aktion soll bis zum 24.06.2026 ein angepasstes Angebot vorbereitet und an Frau Keller gesendet werden. Die Vertriebspriorität wird als mittel eingestuft.

Der ausformulierte Bericht muss so vollständig sein, dass auch Innendienstmitarbeiter den Vorgang ohne zusätzliche Erklärung nachvollziehen können.

## 23. Conversation State

Die Anwendung ist stateful.

Die LLM wird als stateless behandelt.

Das bedeutet:

- Die LLM muss sich nichts dauerhaft merken.
- Der aktuelle Stand liegt im Backend.
- Bei jedem Turn bekommt die LLM den aktuellen Stand injiziert.
- Wenn die LLM neu geladen wird, kann das Gespräch trotzdem fortgesetzt werden.

Ein offener Bericht besteht aus:

| Bestandteil | Zweck |
|---|---|
| Chatverlauf | Nachvollziehbarkeit und Fortsetzung |
| Structured Draft | aktueller strukturierter Berichtsentwurf |
| Missing Fields | noch offene Pflichtfelder |
| Last Question | zuletzt gestellte Frage |
| CRM Context | relevante Kunden, Kontakte, Angebote |
| Status | aktueller Verarbeitungsstand |

Beispiel Draft:

```json
{
  "report_status": "in_progress",
  "customer": {
    "crm_customer_id": "CUST-1001",
    "detected_name": "NordTech",
    "validation_status": "matched"
  },
  "contact": {
    "crm_contact_id": "CONT-2001",
    "detected_name": "Frau Keller",
    "validation_status": "matched"
  },
  "visit": {
    "visit_date": "2026-06-19",
    "visit_type": "on_site",
    "reason_code": "offer_follow_up"
  },
  "offer": {
    "is_offer_related": true,
    "offer_number": "Q-2026-1007",
    "crm_offer_id": "OFF-3001",
    "validation_status": "matched"
  },
  "content": {
    "summary": null,
    "outcome": null,
    "next_action": null,
    "follow_up_date": null,
    "priority": null
  },
  "missing_fields": [
    "summary",
    "outcome",
    "next_action",
    "follow_up_date",
    "priority"
  ],
  "last_question": "Was war das Ergebnis des Gesprächs?"
}
```

## 24. Offene Berichte und Fortsetzung

Ein Bericht kann unterbrochen werden.

Gründe:

- Nutzer beendet die App
- schlechter Empfang
- Akku leer
- Nutzer will später fortsetzen
- LLM oder Backend wird neu gestartet

Offene Berichte werden auf der Startseite angezeigt.

Beim Fortsetzen lädt das System:

1. bisherigen Chatverlauf
2. strukturierten Draft State
3. offene Pflichtfelder
4. letzten Stand der Validierung
5. relevante CRM Stammdaten
6. letzte gestellte Frage

Danach wird das Gespräch an der passenden Stelle fortgesetzt.

## 25. Startseite nach Login

Nach dem Login soll der Außendienstler eine kleine Startseite sehen.

Geplante Bereiche:

| Bereich | Zweck |
|---|---|
| Neuer Bericht | startet eine neue Besuchsbericht Erfassung |
| Offene Berichte | zeigt nicht abgeschlossene Vorgänge |
| Berichtsverlauf | zeigt letzte abgeschlossene Berichte |
| Chatverlauf je Bericht | zeigt den Verlauf einer Berichterfassung |

Alle Außendienstler nutzen dieselbe Oberfläche, sehen aber nur ihren eigenen Bereich.

## 26. Authentifizierung und Nutzerkontext

Das Tool darf nicht offen ohne Anmeldung genutzt werden.

MVP Mindestanforderung:

- Außendienstler müssen sich anmelden.
- Berichte werden einem Nutzer zugeordnet.
- Nutzer sehen nur eigene Berichte.
- Berichtserstellung läuft immer im Kontext des eingeloggten Nutzers.

Mögliche MVP Umsetzung:

- Tabelle `sales_users`
- Login per E Mail und Passwort oder Demo PIN
- Session Token
- `sales_user_id` in Besuchsberichten
- Zugriff nur auf eigene Berichte

Biometrischer Login ist eine spätere Komfortfunktion.

## 27. Datenmodell Vorschlag

### 27.1 sales_users

Zweck:

Bekannte Außendienstmitarbeiter.

Mögliche Felder:

- id
- name
- email
- password_hash
- region
- language_preference
- is_active
- created_at

### 27.2 customers

Zweck:

Bestehende B2B Kunden im Muster CRM.

Mögliche Felder:

- id
- customer_number
- company_name
- city
- country
- customer_language
- status
- created_at

### 27.3 contacts

Zweck:

Ansprechpartner bei Kunden.

Mögliche Felder:

- id
- customer_id
- first_name
- last_name
- full_name
- role
- email
- phone
- is_active
- created_at

### 27.4 offers

Zweck:

Kleine Auswahl offener Angebote je Kunde.

Mögliche Felder:

- id
- offer_number
- customer_id
- title
- status
- amount
- currency
- valid_until
- created_at

### 27.5 visit_reports

Zweck:

Finale oder blockierte Besuchsberichte.

Mögliche Felder:

- id
- sales_user_id
- customer_id
- contact_id
- visit_date
- visit_type
- reason_code
- related_offer_id
- summary
- outcome
- next_action
- follow_up_date
- priority
- report_language
- final_report_text
- status
- created_at
- submitted_at

### 27.6 report_drafts

Zweck:

Zwischengespeicherte strukturierte Arbeitsversionen.

Mögliche Felder:

- id
- sales_user_id
- visit_report_id
- draft_state_json
- status
- last_question
- missing_fields_json
- created_at
- updated_at

### 27.7 chat_messages

Zweck:

Protokollierung des Gesprächsverlaufs.

Mögliche Felder:

- id
- report_draft_id
- sender
- message_text
- message_type
- created_at

Mögliche Sender:

- user
- assistant
- system

### 27.8 inside_sales_tasks

Zweck:

Einfache Aufgaben für Innendienst oder nachgelagerte CRM Bearbeitung.

Mögliche Felder:

- id
- linked_visit_report_id
- task_type
- title
- description
- detected_customer_name
- detected_contact_name
- related_customer_id
- status
- due_date
- created_at

Mögliche `task_type` Werte:

- `new_contact_review`
- `new_lead_review`
- `create_offer`
- `clarify_offer_details`
- `master_data_review`
- `follow_up_call`

## 28. Berichtstatus

Mögliche Statuswerte:

| Status | Bedeutung |
|---|---|
| `in_progress` | Gespräch läuft oder wurde unterbrochen |
| `pending_confirmation` | Bericht ist vorbereitet, aber noch nicht bestätigt |
| `blocked_master_data` | Stammdaten fehlen oder müssen geprüft werden |
| `inside_sales_review` | Innendienstaufgabe wurde erzeugt |
| `confirmed` | Nutzer hat final bestätigt |
| `submitted` | Bericht wurde im Muster CRM gespeichert |
| `cancelled` | Bericht wurde abgebrochen |

Für den MVP können Statuswerte reduziert werden, aber die fachliche Bedeutung sollte erhalten bleiben.

## 29. Datenschutz und Datensparsamkeit

Datenschutz muss explizit im Konzept berücksichtigt werden.

Grundsätze:

- Roh Audio wird nach der Transkription verworfen.
- Audio wird nicht dauerhaft gespeichert.
- Der Chatverlauf wird gespeichert, aber als sensibler Verlauf behandelt.
- Der strukturierte Draft soll möglichst IDs und Codes statt ausgeschriebener personenbezogener Daten enthalten.
- Freitext und finale Berichte können sensible Geschäftsinformationen enthalten.
- Zugriff muss auf den jeweiligen Nutzerkontext beschränkt sein.
- Offene Entwürfe sollten nicht länger gespeichert werden als nötig.
- Final bestätigte Berichte werden als CRM relevante Dokumentation gespeichert.
- Hashing wird für Passwörter und Integritätsprüfungen genutzt, aber nicht als Ersatz für wiederherstellbare Berichtsdaten.

Wichtige Klarstellung:

Ein vollständiger JSON Draft kann nicht einfach gehasht werden, wenn er später fortgesetzt werden soll. Hashing ist ein Einwegverfahren. Für fortsetzbare Berichte braucht das System den Inhalt wiederherstellbar.

Geeignete Maßnahmen sind stattdessen:

- Datenminimierung
- Nutzung von CRM IDs statt wiederholter Namen
- getrennte Speicherung sensibler Inhalte
- Zugriffskontrolle
- Verschlüsselung sensibler Drafts und Chatlogs
- kurze Aufbewahrung von Entwürfen
- keine dauerhafte Speicherung von Roh Audio

## 30. LLM Rolle

Die LLM übernimmt nicht die vollständige Geschäftslogik.

Die LLM unterstützt bei:

- Sprachverständnis
- Extraktion aus freier Sprache
- Formulierung von Rückfragen
- Gesprächsführung
- Zusammenfassung
- Formulierung des finalen Berichtstexts

Das Backend übernimmt:

- Authentifizierung
- Nutzerkontext
- Datenbankzugriff
- CRM Validierung
- Statusverwaltung
- Pflichtfeldprüfung
- Speicherung
- Entscheidung, ob ein Bericht geschrieben werden darf
- Erzeugung von Innendienstaufgaben
- Verwaltung des Conversation State

Grundsatz:

Die LLM formuliert und interpretiert.  
Die Anwendung validiert und entscheidet.

## 31. Mögliche LLM Architektur

Für den MVP kann zunächst eine einfache LLM Verarbeitung verwendet werden.

Langfristig ist eine Trennung denkbar:

| Schicht | Aufgabe |
|---|---|
| Extraction Layer | freie Sprache in strukturierte Felder überführen |
| Dialogue Layer | nächste sinnvolle Rückfrage erzeugen |
| Report Writing Layer | finalen Bericht aus bestätigten Daten formulieren |

Da lokale Modelle verwendet werden sollen, kann diese Trennung später relevant werden.

Für den MVP gilt:

- simpel starten
- Struktur über Backend und Prompting erzwingen
- LLM Ausgabe validieren
- keine direkte ungeprüfte CRM Speicherung durch die LLM

## 32. Lokales Modell und API Fallback

Ziel ist die prototypische Nutzung eines lokalen Modells.

Vorhandene Alternativen:

- lokales Modell
- Gemini API
- OpenAI API

Für das Projekt ist wichtig:

- Der Core Workflow darf nicht hart an einen Anbieter gebunden sein.
- Die LLM Schnittstelle sollte austauschbar sein.
- Das System sollte mit lokalem Modell testbar sein.
- Für bessere Qualität oder Vergleichbarkeit können API Modelle als Fallback oder Benchmark dienen.

## 33. MVP User Journey

### Schritt 1: Login

Der Außendienstler öffnet die Web App und meldet sich an.

### Schritt 2: Startseite

Er sieht:

- Neuer Besuchsbericht
- Offene Berichte
- Letzte Berichte

### Schritt 3: Neuer Bericht

Er startet einen neuen Bericht.

### Schritt 4: Freie Ersteingabe

Er erzählt frei:

> Ich war heute bei NordTech und habe mit Frau Keller gesprochen. Es ging um das offene Angebot zur Rahmenvereinbarung. Die Stimmung war gut, aber sie möchte nochmal mit dem Einkauf sprechen.

### Schritt 5: Extraktion und Bestätigung

Die KI antwortet:

> Ich habe verstanden: Kunde ist NordTech, Ansprechpartnerin ist Frau Keller, Anlass war die Nachbesprechung eines offenen Angebots zur Rahmenvereinbarung. Ist das korrekt?

### Schritt 6: Validierung

Das System prüft:

- NordTech existiert?
- Frau Keller ist Ansprechpartnerin?
- Gibt es offene Angebote?
- Ist eine Angebotsnummer nötig?

### Schritt 7: Rückfragen

Die KI fragt gezielt nach fehlenden Details:

- Welche Angebotsnummer war gemeint?
- Was wurde konkret vereinbart?
- Was ist der nächste Schritt?
- Bis wann soll nachgefasst werden?
- Wie bewertest du die Priorität?

### Schritt 8: Finaler Review

Die KI liest vollständig vor:

- strukturierte Felder
- finalen Berichtstext
- Aufgaben
- Status

### Schritt 9: Bestätigung

Nutzer bestätigt:

> Ja, speichern.

### Schritt 10: Speicherung

Das System speichert:

- Besuchsbericht
- finalen Berichtstext
- strukturierte Felder
- Chatverlauf
- eventuell Innendienstaufgabe

## 34. MVP Erfolgskriterien

Der MVP gilt als erfolgreich, wenn:

- ein Nutzer sich anmelden kann
- ein neuer Bericht gestartet werden kann
- ein freier Berichtstext verarbeitet wird
- Pflichtfelder erkannt und ergänzt werden
- Kunden gegen Muster CRM validiert werden
- Ansprechpartner gegen Muster CRM validiert werden
- Angebotsbezug erkannt und validiert werden kann
- Korrekturen im Gespräch übernommen werden
- offene Berichte fortgesetzt werden können
- ein strukturierter Draft gespeichert wird
- ein finaler Berichtstext erzeugt wird
- der finale Inhalt vor Speicherung bestätigt wird
- der Bericht in der Datenbank gespeichert wird
- Innendienstaufgaben bei Sonderfällen erzeugt werden

## 35. Priorisierung

### Priorität 1: Core

- Login
- Startseite
- neuer Bericht
- textbasierter Chat
- Conversation State
- Pflichtfeldführung
- CRM Validierung
- strukturierter Draft
- finaler Bericht
- finale Bestätigung
- Speicherung in DB

### Priorität 2: Fachliche Zusatzlogik

- Angebotsverknüpfung
- Innendienstaufgaben
- neue Ansprechpartner
- neue Leads als Wiedervorlage
- offene Berichte fortsetzen

### Priorität 3: Voice Layer

- Speech to Text
- Text to Speech
- Audio nach Transkription verwerfen

### Priorität 4: Spätere Komfortfeatures

- QR Code Visitenkarten
- Visitenkartenfoto mit OCR
- biometrischer Login
- echte CRM API Integration
- mobile App Packaging

## 36. Offene Konzeptfragen

Noch zu klären:

1. Welche konkrete Tech Architektur wird genutzt?
2. FastAPI plus React oder einfacherer Prototyp?
3. SQLite oder PostgreSQL für MVP?
4. Welches lokale Modell wird zuerst getestet?
5. Wie wird die LLM Ausgabe technisch validiert?
6. Wie genau sieht das JSON Schema für den Draft aus?
7. Welche Demo Kunden und Angebote werden angelegt?
8. Wie ausführlich muss der finale Bericht im MVP sein?
9. Welche Innendienstaufgaben werden im MVP wirklich erzeugt?
10. Wie stark wird Datenschutz technisch im MVP umgesetzt?
11. Wann wird Speech to Text integriert?
12. Wann wird Text to Speech integriert?

## 37. Aktuelle Konzeptentscheidung

Der aktuelle Stand ist:

Der MVP wird als textbasierter, später sprachfähiger, mobiler Besuchsbericht Assistent für B2B Außendienstler konzipiert. Er nutzt eine kleine Muster CRM Datenbank mit Kunden, Ansprechpartnern und Angeboten. Der Außendienstler startet nach Login einen Bericht, spricht beziehungsweise schreibt frei los, wird durch fehlende Informationen geführt, kann jederzeit korrigieren und bestätigt am Ende den vollständigen Bericht. Erst danach wird der Bericht gespeichert. Fehlende Stammdaten oder Folgeaktionen erzeugen einfache Innendienstaufgaben. Roh Audio wird im MVP nicht dauerhaft gespeichert, sondern nach Transkription verworfen.
