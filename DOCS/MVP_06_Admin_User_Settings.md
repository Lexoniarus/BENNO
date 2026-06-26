# MVP 06: Admin, User Settings und Registrierung

## 1. Zweck dieses Dokuments

Dieses Dokument hält den aktuellen Konzeptstand zu Admin-Bereich, Userverwaltung, nutzerbezogenen Einstellungen und Registrierung im MVP fest.

Der Fokus liegt auf einer pragmatischen MVP-Umsetzung.

Das Ziel ist nicht, ein vollständiges Identity-Management-System zu bauen. Der MVP braucht aber genug Nutzerverwaltung, damit Außendienstler sauber getrennt arbeiten können und zentrale Einstellungen kontrollierbar bleiben.

## 2. Grundprinzip

Die Anwendung unterscheidet im MVP zwischen normalen Außendienst-Usern und Admin-Usern.

Der normale Außendienst-User soll Besuchsberichte erfassen, offene Chats fortsetzen und abgeschlossene Berichte sehen.

Der Admin soll einfache Konfiguration und technische Übersicht übernehmen.

Der Admin-Bereich darf im MVP einfach umgesetzt sein. Er muss funktional sein, aber keine vollständige produktive Administrationsoberfläche darstellen.

## 3. Rollen

Für den MVP reichen zwei Rollen.

```python
class UserRole(str, Enum):
    SALES_REP = "sales_rep"
    ADMIN = "admin"
```

| Rolle | Bedeutung |
|---|---|
| `sales_rep` | Außendienstler, erstellt und verwaltet eigene Besuchsbericht-Chats |
| `admin` | Konfiguriert Nutzer, Provider und einfache technische Statusübersicht |

## 4. Sales User Oberfläche

Ein normaler Außendienst-User sieht nach dem Login eine Startseite.

Geplante Bereiche:

- Neuer Chat
- offene Chats
- abgeschlossene Chats
- Optionen

Die Startseite ist auf den Außendienst-Workflow fokussiert.

Der Sales User sieht keine AI-Provider-Auswahl und keine technischen Modellkonfigurationen.

## 5. Sales User Optionen

Der normale User darf seine eigene Spracheinstellung ändern.

Für den MVP sind zwei Sprachen vorgesehen:

```python
class SessionLanguage(str, Enum):
    DE = "de"
    EN = "en"
```

Regeln:

- Standardsprache ist Deutsch.
- Der User kann im Optionsbereich auf Englisch wechseln.
- Die Spracheinstellung wird pro User gespeichert.
- Neue Chats übernehmen die aktuelle Usersprache.
- Laufende Chats behalten die Sprache, mit der sie gestartet wurden.

Beispiel:

```json
{
  "user_id": "user_001",
  "preferred_language": "de"
}
```

Beim Chatstart wird daraus:

```json
{
  "chat_id": "chat_001",
  "session_language": "de"
}
```

## 6. Sprache im MVP

Der MVP soll Deutsch und Englisch unterstützen.

Der Vertical Slice kann zuerst auf Englisch gebaut werden, der MVP soll aber beide Sprachen abdecken.

Die App-Sprache steuert:

- UI-Sprache
- Chatfragen
- Zusammenfassungen
- Bestätigungen
- Text-to-Speech-Ausgabe
- erwartete Speech-to-Text-Sprache

Es gibt keinen primären automatischen Sprachwechsel während eines Chats.

Ein gestarteter Chat bleibt in seiner `session_language`.

## 7. STT und TTS Einstellungen

Speech-to-Text und Text-to-Speech sind im MVP keine normalen User-Einstellungen.

Regeln:

- Der User wählt nur die App-Sprache.
- Das Backend wählt passend dazu die STT- und TTS-Modelle.
- STT/TTS bleiben lokale Backend-Leistung.
- Normale User wählen keine konkreten STT- oder TTS-Modelle.
- Im Debug oder Admin-Kontext kann sichtbar sein, welche Modelle aktiv sind.

Beispiel:

```json
{
  "session_language": "de",
  "stt_model": "german_stt_model",
  "tts_model": "german_tts_model"
}
```

## 8. AI Provider ist Admin-Thema

Die Auswahl zwischen OpenAI und Local ist kein normales User-Thema.

Der AI Provider wird im Admin-Bereich konfiguriert.

```python
class AiProvider(str, Enum):
    OPENAI = "openai"
    LOCAL = "local"
```

Regeln:

- Der normale Sales User sieht diese Auswahl nicht.
- Es gibt einen globalen Default-Provider.
- Optional kann pro User ein Provider-Override gesetzt werden.
- Konkrete Modelle werden im MVP nicht durch normale User gewählt.
- Modellwechsel ist ein Admin- beziehungsweise Konfigurationsthema.

## 9. Globale Einstellungen und User Overrides

Für den MVP werden globale Defaults und optionale User Overrides verwendet.

AI Provider:

- globaler Default für alle User
- optionaler Override pro User
- nur durch Admin konfigurierbar

Sprache:

- globaler Default, voraussichtlich Deutsch
- pro User einstellbar
- User darf eigene Sprache ändern
- Admin darf Sprache pro User setzen

Prioritätslogik beim Chatstart:

```text
ai_provider = user.ai_provider_override or global.default_ai_provider
session_language = user.preferred_language or global.default_language
```

Beispiel:

```json
{
  "global_settings": {
    "default_language": "de",
    "default_ai_provider": "openai"
  },
  "user_settings": {
    "user_001": {
      "preferred_language": "de",
      "ai_provider_override": null
    },
    "user_002": {
      "preferred_language": "en",
      "ai_provider_override": "local"
    }
  }
}
```

## 10. Admin-Bereich

Der MVP braucht einen kleinen Admin-Bereich im Frontend.

Dieser Bereich darf einfach sein, muss aber zentrale Einstellungen und eine technische Übersicht ermöglichen.

Der Admin-Bereich ist keine vollständige Fachbereichs- oder CRM-Admin-Oberfläche.

## 11. Admin darf sehen

Der Admin darf im MVP sehen:

- Userliste
- Rollen der User
- Spracheinstellung pro User
- AI-Provider-Override pro User
- globalen AI Provider
- globalen Sprachdefault
- Anzahl offener Chats pro User
- Anzahl abgeschlossener Chats pro User
- Anzahl Chats mit Fehlerstatus
- Anzahl Chats mit `inside_sales_input_required`
- technische Statusübersicht

Damit ist der Admin-Bereich Konfiguration plus technisches Monitoring.

## 12. Admin darf in dieser View nicht sehen

Der Admin soll in dieser Admin-View keine inhaltliche Detailkontrolle über Außendienstgespräche bekommen.

Nicht sichtbar in dieser View:

- vollständige Chatinhalte der Außendienstler
- Transkripte
- Freitextberichte
- detaillierte Gesprächsverläufe

Das schützt den Fokus des Admin-Bereichs:

- technische Steuerung
- Nutzerverwaltung
- Statusübersicht
- keine fachliche Überwachung einzelner Gespräche

## 13. Einfache Userverwaltung

Für den MVP reicht eine einfache eigene Userverwaltung.

Enthalten:

- User anlegen
- User bearbeiten
- Rolle setzen
- Sprache pro User setzen
- AI-Provider-Override pro User setzen
- Passwort setzen oder zurücksetzen
- Registrierung anstoßen

Alles bleibt MVP-orientiert und arbeitet mit Mock-Daten beziehungsweise einer einfachen lokalen Datenbasis.

Nicht Ziel des MVP:

- vollständiges produktives Identity Management
- komplexes Rechte- und Rollensystem
- Zwei-Faktor-Authentifizierung als Pflicht
- echte E-Mail-Verifikation als Pflicht
- ERP-/CRM-Discovery von Außendienstlern als Pflicht

## 14. Userdaten im MVP

Ein User kann im MVP ungefähr so gedacht werden:

```json
{
  "user_id": "user_001",
  "email": "sales@example.com",
  "username": "sales_user",
  "role": "sales_rep",
  "preferred_language": "de",
  "ai_provider_override": null,
  "external_sales_rep_id": "ERP_REP_123",
  "is_active": true
}
```

`external_sales_rep_id` bleibt optional.

Damit kann später ein Bezug zu einem ERP-/CRM-Vertreter hergestellt werden, ohne dass das im MVP vollständig umgesetzt werden muss.

## 15. Zielbild: ERP-/CRM-Discovery

Langfristig wäre es fachlich sinnvoll, Außendienstler aus dem ERP oder CRM zu erkennen beziehungsweise zu importieren.

Zielbild:

1. ERP/CRM liefert Vertreter oder Außendienstler.
2. Admin ordnet diesen Personen ein Assistant-Profil zu.
3. Die App vermeidet doppelte Vertreterpflege.
4. Wenn ein Zielsystem keine Vertreterlogik bietet, kann die App trotzdem eigene User verwalten.

Das ist nicht Kern des MVP.

Für den MVP reicht eine einfache Userverwaltung mit optionalem externem Bezug.

## 16. Registrierung Zielbild

Das gewünschte Zielbild für Registrierung:

1. Admin legt User mit E-Mail und Username an.
2. System erzeugt einen Registrierungslink.
3. User öffnet den Link.
4. User setzt sein eigenes Passwort.
5. Account ist danach aktiv.

Das ist fachlich sauberer als dauerhaft vom Admin gesetzte Passwörter.

## 17. Registrierung MVP-Abstufung

Der vollständige Prozess mit echtem E-Mail-Versand ist kein harter MVP-Kern.

Pragmatische MVP-Variante:

```text
Admin creates user -> system generates setup token/link -> link is shown in admin UI -> user sets password
```

Damit wird der spätere Registrierungsprozess schon sinnvoll abgebildet, ohne echten E-Mail-Versand bauen zu müssen.

Spätere produktivere Variante:

```text
Admin creates user -> system sends email -> user sets password
```

## 18. Passwort-Reset

Passwort-Reset gehört zur simplen Userverwaltung.

MVP-Logik:

- Admin kann Passwort-Reset für einen User anstoßen.
- System erzeugt einen Reset-Link oder Reset-Token.
- Im MVP kann der Link direkt in der Admin-Oberfläche angezeigt werden.
- User setzt danach ein neues Passwort.

Echter E-Mail-Versand kann später ergänzt werden.

## 19. Zwei-Faktor-Authentifizierung und E-Mail-Bestätigung

Zwei-Faktor-Authentifizierung und echte E-Mail-Bestätigung sind fachlich sinnvoll, aber nicht Kern des MVP.

Wenn genug Zeit bleibt, können sie als Bonus betrachtet werden.

Priorität:

1. funktionierender Login
2. Userrollen
3. einfache Userverwaltung
4. Spracheinstellungen
5. Provider-Konfiguration durch Admin
6. Setup-/Reset-Link ohne zwingenden E-Mail-Versand
7. optional später E-Mail-Versand
8. optional später Zwei-Faktor-Authentifizierung

## 20. Aktueller Arbeitsstand

Für Admin, User Settings und Registrierung sind damit festgelegt:

- zwei Rollen: `sales_rep` und `admin`
- Sales User sieht Chat-Startseite und eigene Optionen
- Sprache ist User-Thema
- AI Provider ist Admin-Thema
- globale Defaults plus optionale User Overrides
- STT/TTS werden automatisch aus der Sprache abgeleitet
- Admin-Bereich für Konfiguration und technische Übersicht
- Admin sieht keine Chatinhalte in dieser View
- einfache Userverwaltung im MVP
- optionaler ERP-/CRM-Vertreterbezug
- Registrierung über Setup-Link als Zielbild
- MVP kann Setup-Link ohne echten E-Mail-Versand darstellen
- Passwort-Reset ist Teil der simplen Userverwaltung
- 2FA und echte E-Mail-Bestätigung sind optional nachgelagert

## 21. Noch offen im Anschluss

Offene Anschlussfragen:

1. Welche konkreten Felder braucht die Userverwaltung technisch?
2. Wie einfach wird die Admin-UI im ersten MVP-Schnitt umgesetzt?
3. Wird der Setup-Link als echter Token umgesetzt oder zunächst als Demo-Flow?
4. Wie wird die Passwortspeicherung im MVP technisch umgesetzt?
5. Welche Provider-Konfigurationswerte müssen im Admin-Bereich sichtbar sein?
6. Wie wird später ein ERP-/CRM-Vertreterbezug genau hergestellt?
7. Muss die Statusübersicht für Admins eigene Filter haben?
8. Wo liegt die Grenze zwischen technischem Monitoring und fachlicher Einsicht?

