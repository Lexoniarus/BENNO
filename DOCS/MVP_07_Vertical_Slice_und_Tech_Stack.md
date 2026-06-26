# MVP 07: Vertical Slice und Tech Stack

## 1. Zweck dieses Dokuments

Dieses Dokument hält den aktuellen Konzeptstand zum ersten Vertical Slice und zur vorläufigen technischen Arbeitsannahme fest.

Der Fokus liegt auf der Frage:

> Was ist der kleinste durchgehende technische Schnitt, mit dem der Kern des Besuchsbericht-Assistenten nachweisbar funktioniert?

Dieses Dokument ist keine finale Architekturentscheidung für das gesamte Projekt.

Der hier beschriebene Tech Stack ist eine vorläufige Arbeitsannahme, die für den ersten MVP-Durchstich pragmatisch sinnvoll erscheint.

## 2. Ausgangslage

Der fachliche Kern des Projekts ist geklärt:

- sprach- und dialoggesteuerter Besuchsbericht-Assistent
- B2B-Außendienst als Hauptnutzer
- kein CRM-Ersatz
- CRM/ERP nur als Gegenstelle
- textbasierter Kern mit späterem STT/TTS-Layer
- Report Draft als Zwischenstand
- Final Report nach Bestätigung
- Admin-Bereich für User und zentrale Einstellungen

Für den nächsten Schritt muss der MVP technisch so geschnitten werden, dass ein vollständiger Ablauf schnell testbar wird.

## 3. Ziel des ersten Vertical Slice

Vertical Slice 1 soll zeigen:

> Ein Außendienstler kann sich einloggen, einen Besuchsbericht-Chat starten, frei Text eingeben, vom System durch fehlende Informationen geführt werden, einen Report Draft aufbauen, eine blockweise Zusammenfassung bestätigen und daraus einen finalen Bericht lokal speichern.

Der erste Vertical Slice beweist damit den Kern:

```text
free input -> structured draft -> guided questions -> review -> confirmation -> final report
```

## 4. Abgrenzung: Text zuerst

Vertical Slice 1 läuft textbasiert.

Diese Abgrenzung ist bewusst gewählt.

Gründe:

- STT- und TTS-Modelle müssen noch getestet werden.
- Der zentrale Projektnutzen liegt im geführten Berichtsdialog, nicht zuerst in der Audioverarbeitung.
- Textbetrieb erleichtert Debugging.
- Der spätere Voice Layer kann auf denselben Chat- und Draft-Ablauf aufgesetzt werden.
- LLM-Verhalten, Section Status, Intents, Confidence und Review-Logik können ohne Audio schneller stabilisiert werden.

## 5. Enthalten in Vertical Slice 1

Vertical Slice 1 enthält:

- Login
- Rollenrouting nach Login
- Sales-Frontend
- Admin-Frontend
- Startseite für Außendienstler
- neuer Chat
- textbasierte Eingabe
- textbasierte Systemantwort
- Report Template als interne Vorlage
- Report Draft als Arbeitsstand
- Section- und Statuslogik
- Intent-Erkennung
- Intent Confidence
- Target Sections
- LLM-gestützte Extraktion
- Rückfragen zu fehlenden oder unklaren Sections
- blockweise Review
- finale Bestätigung
- lokale Speicherung des finalen Reports
- Debug-Logging im Backend
- einfache Userverwaltung im Admin-Bereich
- globale und userbezogene Provider-Einstellungen im Admin-Bereich

## 6. Nicht enthalten in Vertical Slice 1

Vertical Slice 1 enthält noch nicht:

- echte Speech-to-Text-Nutzung
- echte Text-to-Speech-Nutzung
- Audioaufnahme im Browser
- Audioausgabe im Browser
- Voice Interrupt Handling
- vollständige eNVenta-Feldmaske
- echte CRM-/ERP-Integration
- produktives Sicherheitskonzept für CRM-/ERP-Zugriff
- Admin-Template-Editor
- echter E-Mail-Versand für Registrierung oder Passwort-Reset
- Zwei-Faktor-Authentifizierung
- finale lokale LLM-Auswahl
- Gemini-Entscheidung

Diese Punkte bleiben relevant, blockieren aber den ersten technischen Durchstich nicht.

## 7. Vorläufiger Tech Stack

Für den ersten MVP-Durchstich wird folgender Tech Stack als Arbeitsannahme festgehalten:

```text
Backend/Web-App: Flask
Templates: Jinja
Frontend-Interaktion: Vanilla JavaScript
Styling: responsive HTML/CSS
Datenbank: SQLite
LLM Start: OpenAI API
Local später: OpenAI-kompatible lokale API, zum Beispiel LM Studio
CRM/ERP: lokale Placeholder-API
```

Diese Entscheidung ist noch nicht endgültig.

Sie wird als pragmatische Startannahme dokumentiert.

## 8. Begründung für Flask, Jinja und SQLite

Flask ist für den MVP plausibel, weil:

- Flask im Kurs behandelt wurde.
- Das Projekt primär Python-basiert sein soll.
- Der erste Slice wenig Frontend-Komplexität braucht.
- Jinja-Templates für einfache Seiten ausreichen.
- Vanilla JavaScript für Chat-Interaktion genügt.
- Deployment als Web-App einfacher bleibt als eine native App.
- Der MVP auf Desktop und Smartphone im Browser laufen kann.

SQLite ist für den ersten MVP plausibel, weil:

- lokale Entwicklung einfach ist.
- Mock-Daten ausreichen.
- kein produktiver Mehrbenutzerbetrieb nachgewiesen werden muss.
- Datenmodell und Workflow schnell testbar sind.

Noch offen bleibt, ob SQLite für den gesamten MVP reicht oder später PostgreSQL sinnvoller wird.

## 9. Zielgerät und Deployment-Denke

Das Zielgerät für Außendienstler ist ein Smartphone.

Trotzdem wird keine native Mobile App als MVP-Ziel festgelegt.

Der MVP wird als responsive Web-App gedacht.

Zielbild:

```text
Smartphone Browser -> HTTPS -> App Backend
```

Später kann daraus eine PWA entstehen.

Für den ersten textbasierten Slice ist HTTPS noch nicht kritisch.

Für spätere Browser-Audiofunktionen wird HTTPS jedoch relevant, weil Mikrofonzugriff im Browser in der Regel einen sicheren Kontext benötigt.

## 10. Grundarchitektur

Für Vertical Slice 1 wird folgende Grundarchitektur angenommen:

```text
Browser
  -> Flask Web App
      -> Auth/User Service
      -> Sales Routes
      -> Admin Routes
      -> Chat Service
      -> Report Draft Service
      -> AI Provider Service
      -> Placeholder CRM Service
      -> SQLite
```

Das Frontend spricht nur mit dem App-Backend.

Das Backend ist die zentrale Anwendungsschicht.

## 11. Rollenrouting

Nach dem Login wird anhand der Userrolle entschieden, welcher Bereich geöffnet wird.

```text
Login
  -> role == admin      -> Admin Frontend
  -> role == sales_rep  -> Sales Frontend
```

Geplante Routes:

```text
/login
/sales/...
/admin/...
```

Regeln:

- Ein Admin landet nach Login im Admin-Bereich.
- Ein Sales User landet nach Login im Sales-Bereich.
- Sales User dürfen keine Admin-Routes öffnen.
- Admin User landen nicht automatisch im Sales-Workflow.
- Für den MVP ist keine Mischrolle erforderlich.

## 12. Sales Frontend

Das Sales Frontend wird mobil optimiert.

Es enthält im ersten Slice:

- Login-Weiterleitung in den Sales-Bereich
- Startseite
- neuer Chat
- offene Chats
- abgeschlossene Chats
- Optionen
- Chat-Ansicht
- Review-Ansicht
- finale Bestätigung

Die Sales-Optionen enthalten für normale User zunächst:

- Sprache Deutsch oder Englisch

Nicht im Sales-Frontend sichtbar:

- AI-Provider-Auswahl
- konkrete Modellkonfiguration
- STT-Modellauswahl
- TTS-Modellauswahl

## 13. Admin Frontend

Das Admin Frontend ist Teil des MVP.

Es muss nicht mobil optimiert sein.

Ein Desktop-Browser reicht.

Der Admin-Bereich enthält im ersten Slice:

- Userliste
- User anlegen
- User bearbeiten
- Rolle setzen
- Sprache pro User setzen
- globalen AI Provider setzen
- AI-Provider-Override pro User setzen
- einfache Statusübersicht

Die Statusübersicht zeigt keine Chatinhalte.

Erlaubt sind technische Übersichten wie:

- Anzahl offener Chats pro User
- Anzahl abgeschlossener Chats pro User
- Anzahl Chats mit Fehlerstatus
- Anzahl Chats mit `inside_sales_input_required`

Nicht sichtbar in dieser View:

- vollständige Chatinhalte
- Transkripte
- Freitextberichte
- detaillierte Gesprächsverläufe

## 14. Login Session

Die Login Session bleibt minimal.

Für Sales User:

```json
{
  "user_id": "user_001",
  "role": "sales_rep",
  "preferred_language": "de"
}
```

Für Admin User:

```json
{
  "user_id": "admin_001",
  "role": "admin",
  "preferred_language": "de"
}
```

Alles Weitere wird bei Bedarf aus der Datenbank geladen.

Dazu gehören:

- AI Provider
- Provider Overrides
- Userdetails
- Chatlisten
- Report Drafts
- Admin-Statusdaten

## 15. AI Provider im Vertical Slice

Vertical Slice 1 nutzt echte OpenAI-Anbindung.

Der Masterschool-API-Key soll verwendet werden.

Der erste Slice wird nicht primär mit einem Fake-LLM gebaut.

Mock- oder Fake-LLM kann später für Tests sinnvoll sein, ist aber nicht der Hauptpfad.

Provider-Grundsatz:

```text
Textchat -> Backend -> OpenAI -> Draft Update -> nächste Frage / Review -> Speicherung
```

Die Provider-Schicht bleibt trotzdem so gedacht, dass später `local` über eine OpenAI-kompatible API ergänzt werden kann.

## 16. Provider-Konfiguration

Die Auswahl zwischen OpenAI und Local ist ein Admin-Thema.

Normale Sales User wählen den Provider nicht selbst.

Es gibt:

- globalen Default Provider
- optionalen Provider Override pro User

Beispiel:

```json
{
  "global_settings": {
    "default_ai_provider": "openai"
  },
  "user_settings": {
    "user_001": {
      "ai_provider_override": null
    },
    "user_002": {
      "ai_provider_override": "local"
    }
  }
}
```

Konkrete Modelle sind im MVP kein normales User-Thema.

Modellkonfiguration bleibt Admin- beziehungsweise Backend-Konfiguration.

## 17. STT und TTS als spätere Layer

STT und TTS werden nicht in Vertical Slice 1 umgesetzt.

Die Architektur muss sie aber vorbereiten.

Späterer Zielablauf:

```text
Voice input
  -> STT
      -> text turn
          -> same chat workflow
              -> assistant text
                  -> TTS
                      -> voice output
```

Wichtig:

Der Kernworkflow verarbeitet Text.

Speech-to-Text erzeugt nur den Textinput.

Text-to-Speech liest nur den Textoutput vor.

Dadurch bleibt der Dialogkern unabhängig vom Audio-Layer.

## 18. Sprache im Vertical Slice

Der MVP soll Deutsch und Englisch unterstützen.

Für den Vertical Slice kann zuerst Englisch als technische Startsprache verwendet werden.

Die Anwendung soll aber auf Deutsch und Englisch umstellbar sein.

Regeln:

- Sprache ist pro User gespeichert.
- Default ist Deutsch.
- Neue Chats übernehmen die aktuelle User-Sprache.
- Laufende Chats behalten ihre Startsprache.
- UI, Chatfragen, Zusammenfassungen und Bestätigungen folgen der gewählten Sprache.

## 19. CRM-/ERP-Integration im MVP

Im MVP gibt es keine echte CRM-/ERP-Anbindung als Pflicht.

Stattdessen wird eine lokale Placeholder-API verwendet.

Diese simuliert typische CRM-/ERP-Funktionen wie:

- Kunden suchen
- Leads oder Adressen suchen
- Ansprechpartner suchen
- Angebote referenzieren
- Aufträge referenzieren
- Besuchsbericht speichern
- Innendienstaufgabe erzeugen

Das Placeholder-CRM bleibt Gegenstelle.

Es ist nicht der Kern des Programms.

## 20. Sicherheitslinie für spätere CRM-/ERP-Anbindung

Mobile Clients verbinden sich niemals direkt mit dem CRM/ERP.

Das Frontend spricht nur mit dem App-Backend.

Das Backend ist die einzige Schicht, die später mit CRM/ERP spricht.

Zielbild:

```text
Mobile Web-App
  -> App Backend
      -> CRM/ERP Connector
          -> CRM/ERP
```

Wenn CRM/ERP nur intern erreichbar ist:

```text
Mobile Web-App
  -> App Backend
      -> Connector/Agent im Firmennetz
          -> CRM/ERP
```

Nicht vorgesehen:

- Handy direkt ins Firmen-VPN zwingen
- CRM-Zugangsdaten im Frontend speichern
- 2FA-Codes abgreifen oder umgehen
- direkte Browser-zu-CRM-Kommunikation

Dieses Thema bleibt relevant, blockiert aber Vertical Slice 1 nicht.

## 21. Datenbereiche für Vertical Slice 1

Vertical Slice 1 braucht mindestens folgende Datenbereiche:

- users
- global_settings
- user_settings
- chats
- chat_turns
- report_templates
- report_drafts
- final_reports
- inside_sales_tasks
- mock_customers
- mock_leads
- mock_contacts
- mock_offers
- mock_orders

Diese Liste ist noch kein finales Datenbankschema.

Sie beschreibt nur die fachlichen Speicherbereiche für den ersten Durchstich.

## 22. Debugging im Vertical Slice

Debugging erfolgt zuerst über Backend-Logging.

Pro Turn sollen mindestens geloggt werden:

- `chat_id`
- `user_id`
- `ai_provider`
- eingehender Text
- erkannter Intent
- `intent_confidence`
- `target_sections`
- aktualisierte Section Status
- fehlende Sections
- nächste Systemfrage
- Fehler oder Unsicherheiten

Eine eigene Debug-UI ist für den ersten Slice nicht erforderlich.

## 23. Externe Abhängigkeiten

Zwei Punkte sind extern blockiert.

Ofer:

- Ist Gemini mandatory?
- Reicht OpenAI plus lokale OpenAI-kompatible API?
- Welche OpenAI-Modelle dürfen oder sollen verwendet werden?
- Welche lokalen Modelle sind sinnvoll beziehungsweise erlaubt?

Bernd:

- Welche eNVenta-Felder enthält die Besuchsberichtmaske?
- Gibt es einen Screenshot oder eine Feldliste?
- Welche Felder sind Pflicht?
- Welche Felder sind optional?

Diese Punkte dürfen den ersten textbasierten Vertical Slice nicht blockieren.

## 24. Aktuelle Entscheidungen

Für Vertical Slice und Tech Stack sind aktuell festgehalten:

- Vertical Slice 1 läuft textbasiert.
- OpenAI wird als erster echter LLM-Provider genutzt.
- STT/TTS werden später ergänzt.
- Flask, Jinja, Vanilla JavaScript und SQLite sind die vorläufige Arbeitsannahme.
- Die App wird als responsive Web-App gedacht.
- Native Mobile App ist kein MVP-Ziel.
- Sales- und Admin-Frontend sind beide Teil des MVP.
- Rollenrouting erfolgt nach Login.
- Session bleibt minimal.
- Admin konfiguriert Provider und User.
- CRM/ERP wird über Placeholder-API simuliert.
- Mobile Clients sprechen nicht direkt mit CRM/ERP.

## 25. Noch offen

Offene Punkte nach diesem Stand:

1. Bleibt Flask endgültig der Tech Stack oder wird später noch gewechselt?
2. Reicht SQLite für den vollständigen MVP oder nur für den ersten Slice?
3. Wie genau wird die Flask-Projektstruktur organisiert?
4. Welche Routes braucht der erste Slice konkret?
5. Welche Tabellen werden im ersten Datenbankschema angelegt?
6. Wie wird der OpenAI Provider technisch abstrahiert?
7. Wie wird die Placeholder-CRM-API konkret geschnitten?
8. Welche eNVenta-Felder kommen später in das `report_template`?
9. Welche Entscheidung bringt das Gespräch mit Ofer zu Gemini und Local?
10. Wann werden STT und TTS in den Ablauf integriert?

## 26. Nächster sinnvoller Schritt

Der nächste sinnvolle Schritt ist die technische Grobstruktur des ersten Flask-Slice:

- App-Struktur
- Routes
- Templates
- Services
- Datenbanktabellen
- erste Sequenz des Chatablaufs

Dabei sollte weiterhin gelten:

- keine eNVenta-Felder erfinden
- keine lokale LLM-Auswahl vor Ofer finalisieren
- CRM/ERP nur als Placeholder-Gegenstelle behandeln
- den ersten Durchstich klein halten
