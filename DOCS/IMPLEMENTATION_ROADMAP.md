# BENNO Implementation Roadmap

## Zweck

Dieses Dokument beschreibt den geplanten Entwicklungsablauf für BENNO.

Es ist kein fachliches Konzeptpapier, sondern ein praktischer Laufplan: In welcher Reihenfolge wird gebaut, wann ist ein Schritt fertig, und welche Themen werden bewusst erst später angegangen?

Grundsatz:

> Erst einen kleinen, vollständigen Text-Loop bauen. Danach Tiefe, Voice, eNVenta-Feldmapping und lokale KI ergänzen.

BENNO soll nicht als Big-Bang-App entstehen. Jede Phase soll lauffähig, testbar und committbar sein.

## Phase 0: Projektbasis

Status: weitgehend erledigt.

Ziel:

- Lokales Git-Repository ist initialisiert.
- Privates GitHub-Repository ist verbunden.
- Dokumentation ist versioniert.
- Das Projekt kann in PyCharm geöffnet werden.

Erledigt:

- Git lokal auf Branch `main`
- privates GitHub-Remote `Lexoniarus/BENNO`
- erste Dokumentationsbasis
- `.gitignore`

Nächster kleiner Schritt:

- Python-/Flask-Projektstruktur anlegen.
- Virtuelle Umgebung vorbereiten.
- Startkommando dokumentieren.

## Phase 1: Flask-Grundgerüst

Ziel:

BENNO startet als lokale Web-App.

Umfang:

- Flask App Factory
- Konfiguration
- `templates`
- `static`
- SQLite-Anbindung vorbereiten
- einfacher Startscreen oder Login-Screen
- Basislayout für Desktop und Smartphone
- `.env.example`
- Abhängigkeiten in `requirements.txt` oder `pyproject.toml`

Technische Richtung:

- Flask
- Jinja
- Vanilla JavaScript
- SQLite
- SQLAlchemy oder Flask-SQLAlchemy
- Passwort-Hashing mit Werkzeug

Fertig, wenn:

- Die App lokal startet.
- Eine erste Seite im Browser sichtbar ist.
- Es noch keine KI geben muss.

## Phase 2: Datenmodell und MockDB

Ziel:

BENNO bekommt die Datenbasis, auf der der spätere Bericht-Loop läuft.

Erste Tabellen:

- `users`
- `global_settings`
- `chats`
- `chat_messages`
- `report_drafts`
- `final_reports`
- `inside_sales_tasks`
- `mock_customers`
- `mock_contacts`
- `mock_offers`
- `mock_orders`

Seed-Daten:

- ein Admin-User
- ein Sales-User
- drei bis vier Demo-Kunden
- Ansprechpartner
- Angebote
- optional ein bis zwei Aufträge

Wichtig:

- Die finale eNVenta-Feldstruktur wird erst ergänzt, wenn Bernds Feldliste vorliegt.
- Bis dahin dienen die bestehenden Report Sections als interne Arbeitsstruktur.

Fertig, wenn:

- Die Datenbank initialisiert werden kann.
- Demo-User existieren.
- Mock-Kunden, Kontakte, Angebote und Aufträge abgefragt werden können.

## Phase 3: Login, Rollen und Navigation

Ziel:

Nutzer kommen sauber in ihren jeweiligen Bereich.

Sales User sieht:

- Neuer Bericht
- Offene Berichte
- Abgeschlossene Berichte
- Optionen

Admin sieht:

- Userliste
- einfache Statusübersicht
- globale Provider-Einstellung

Entscheidung für den ersten Schnitt:

- Keine Setup-/Reset-Link-Logik.
- Seed-User reichen für den Start.
- Registrierung und Passwort-Reset können später ergänzt werden.

Fertig, wenn:

- Login funktioniert.
- Sales User und Admin landen auf verschiedenen Dashboards.
- Sales User sehen nur ihre eigenen Chats und Berichte.
- Admin sieht keine Chatinhalte.

## Phase 4: Erster kompletter Text-Loop ohne echte KI-Magie

Ziel:

Der wichtigste Produktfluss funktioniert einmal komplett.

Ein Sales User kann:

1. einen Bericht starten
2. freien Text eingeben
3. daraus einen Draft aufbauen
4. fehlende Informationen ergänzen
5. einen Review sehen
6. den Review bestätigen
7. einen finalen Bericht speichern

Vorgehen:

Zuerst wird die Logik bewusst einfach gebaut. Es muss noch keine perfekte KI-Extraktion geben. Wichtig ist, dass der gesamte Ablauf steht.

Zu prüfende Berichtsteile:

- Kunde oder Lead
- Ansprechpartner
- Besuchsanlass
- Zusammenfassung
- Ergebnis
- nächste Aktion
- Follow-up oder Wiedervorlagedatum
- Angebotsbezug, falls relevant
- Auftragsbezug, falls relevant
- Ratings

Benötigtes Verhalten:

- Chat starten
- freie Eingabe speichern
- Draft State anlegen
- fehlende Bereiche erkennen
- nächste sinnvolle Frage stellen
- Korrekturen übernehmen
- blockweisen Review erzeugen
- finale Bestätigung einholen
- Final Report speichern
- bei Bedarf Inside-Sales-Task erzeugen

Fertig, wenn:

- Ein kompletter Bericht ohne OpenAI gespeichert werden kann.
- Der Ablauf von Start bis Speicherung demonstrierbar ist.
- Korrekturen nicht verloren gehen.

## Phase 5: OpenAI-Anbindung

Ziel:

BENNO versteht freie Texte besser und formuliert natürlicher.

Umfang:

- OpenAI Provider Service
- kontrollierte KI-Antwortstruktur
- Extraktion aus freier Nutzereingabe
- Intent-Erkennung
- Vorschlag für nächste Frage
- Review-Formulierung
- finaler Berichtstext

Wichtige Regel:

Die KI darf Vorschläge machen, aber nicht direkt speichern.

Der Code entscheidet weiterhin:

- Welche Felder fehlen?
- Welche Werte sind erlaubt?
- Was wurde gegen Mock-CRM validiert?
- Wann ist der Bericht bereit für Review?
- Wann darf gespeichert werden?
- Ob eine Innendienstaufgabe entsteht.

Fertig, wenn:

- OpenAI freie Besuchsbeschreibungen sinnvoll auswertet.
- Rückfragen natürlicher werden.
- Review und finaler Bericht verständlich formuliert sind.
- Der Backend-Code weiterhin die Kontrolle über Speicherung und Status behält.

## Phase 6: eNVenta-Felder und Placeholder-CRM-Vertrag

Auslöser:

Bernds eNVenta-Feldliste liegt vor.

Ziel:

Die interne Berichtstruktur wird auf die erwarteten eNVenta-Besuchsberichtfelder gemappt.

Zu klären:

- Welche Felder sind Pflicht?
- Welche Felder sind optional?
- Welche Werte kommen aus Login oder User-Kontext?
- Welche Werte kommen aus Mock-CRM-Daten?
- Welche Werte muss BENNO abfragen?
- Welche Felder werden zurückgeschrieben?
- Welche Informationen erzeugen Wiedervorlagen oder Innendienstaufgaben?

Placeholder-CRM-Service soll danach klar definieren:

- Kunde suchen
- Ansprechpartner suchen
- Angebot suchen
- Auftrag suchen
- Besuchsbericht speichern
- Wiedervorlage oder Innendienstaufgabe erzeugen

Fertig, wenn:

- Die MockDB die relevanten eNVenta-Felder abbildet.
- Ein finaler Bericht in der erwarteten Struktur gespeichert werden kann.
- Der Placeholder-CRM-Vertrag klar genug ist, um später durch eine echte Integration ersetzt zu werden.

## Phase 7: Admin minimal fertigstellen

Ziel:

Der Admin-Bereich ist funktional, aber nicht überbaut.

Admin kann:

- User sehen
- Rollen sehen oder ändern
- Sprache pro User setzen
- globalen Provider setzen
- offene Chats pro User zählen
- abgeschlossene Berichte zählen
- problematische Chats zählen
- Fälle mit `inside_sales_input_required` sehen

Admin darf nicht:

- vollständige Chatinhalte sehen
- Transkripte lesen
- komplette Freitextberichte kontrollieren

Fertig, wenn:

- Admin-Konfiguration funktioniert.
- Die Statusübersicht einfach, aber brauchbar ist.
- Keine fachliche Überwachung einzelner Außendienstgespräche entsteht.

## Phase 8: Stabilisierung und Demo-Fälle

Ziel:

BENNO ist als textbasierter MVP zuverlässig vorführbar.

Demo-Szenarien:

1. Bekannter Kunde, bekannter Ansprechpartner, normales Follow-up
2. Bekannter Kunde, neuer Ansprechpartner, Innendienstaufgabe
3. Bestehendes Angebot wird erwähnt und gefunden
4. Angebot wird erwähnt, ist aber unklar
5. Neuer Lead mit Wiedervorlage
6. Nutzer korrigiert eine frühere Angabe
7. Review wird abgelehnt und korrigiert
8. Review wird bestätigt und gespeichert

Fertig, wenn:

- Alle Demo-Szenarien durchspielbar sind.
- Fehlerfälle verständlich behandelt werden.
- Der Text-Loop stabil genug ist, um darauf Voice aufzubauen.

## Phase 9: STT und TTS

Ziel:

Sprache wird als Layer auf denselben Workflow gelegt.

Grundprinzip:

```text
voice input -> STT -> text turn -> same chat workflow -> assistant text -> TTS -> voice output
```

Umfang:

- Spracheingabe aufnehmen
- Sprache in Text umwandeln
- Transkript als normale Chatnachricht behandeln
- BENNO-Antwort vorlesen
- finalen Review vorlesen

Wichtig:

- Der fachliche Workflow bleibt derselbe.
- STT ersetzt nur die Texteingabe.
- TTS ersetzt nur die visuelle Ausgabe nicht, sondern ergänzt sie.

Fertig, wenn:

- Ein Bericht per Spracheingabe begonnen werden kann.
- BENNO Antworten vorlesen kann.
- Der Nutzer weiterhin Text sehen und notfalls eingreifen kann.

## Phase 10: Local Provider

Ziel:

Die Datenschutzrichtung wird praktisch geprüft.

Umfang:

- lokaler Provider über OpenAI-kompatible API
- zum Beispiel LM Studio
- gleicher Provider-Vertrag wie OpenAI
- Vergleich gegen dieselben Demo-Fälle

Zu prüfen:

- Versteht das lokale Modell die Eingaben ausreichend gut?
- Liefert es stabile strukturierte Vorschläge?
- Braucht es engere Prompts?
- Müssen Aufgaben stärker in Code aufgeteilt werden?
- Ist die Performance akzeptabel?

Fertig, wenn:

- Der gleiche Text-Loop mit einem lokalen Provider testbar ist.
- Unterschiede zu OpenAI dokumentiert sind.
- Eine belastbare Entscheidung möglich ist, wie weit BENNO lokal betrieben werden kann.

## Empfohlener Start

Als nächstes sollten Phase 1 und Phase 2 umgesetzt werden:

1. Flask-Projektstruktur
2. SQLite-Anbindung
3. Datenmodelle
4. Seed-Daten
5. Login-Grundlage

Danach folgt direkt Phase 4:

> Ein kompletter Bericht-Loop von "Neuer Bericht" bis "gespeichert".

Dieser Loop ist das Fundament. Sobald er steht, sind OpenAI, Voice, eNVenta-Feldmapping und Local Provider Erweiterungen auf einem tragfähigen Kern.
