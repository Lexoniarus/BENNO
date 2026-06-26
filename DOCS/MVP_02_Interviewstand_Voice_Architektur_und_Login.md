# MVP 02: Interviewstand zu Voice, Architektur, Providerstrategie und Login

## 1. Zweck dieses Dokuments

Dieses Dokument hält den gemeinsam erarbeiteten Zwischenstand nach der weiteren Konzeptklärung fest.

Es ersetzt keinen finalen technischen Entwurf und legt noch kein vollständiges Datenmodell fest. Der Fokus liegt auf den inhaltlichen Entscheidungen, die im Gespräch konkretisiert wurden:

- fachlicher Kern des Projekts
- dialoggesteuerte Besuchsbericht-Erfassung
- Hands-free-Zielbild
- Textchat, Speech-to-Text und Text-to-Speech
- Python Backend als zentrale Anwendungsschicht
- Local-first-Zielrichtung
- notwendige Einbindung von OpenAI und Gemini
- Provider-Auswahl im Frontend
- CRM als externe beziehungsweise simulierte Gegenstelle
- eigene Login-Logik mit optionaler CRM-Vertreter-Verknüpfung
- Bewertungsblock im Besuchsbericht

Wichtig: Das Muster-CRM beziehungsweise die Placeholder-SQL-Datenbank ist nicht der Kern des Projekts. Der Kern ist das sprach- und dialoggesteuerte Tool zur Erfassung, Strukturierung, Bewertung und Bestätigung von Besuchsberichten.

## 2. Fachlicher Kern des Projekts

Das Projekt ist primär ein sprach- beziehungsweise dialoggesteuertes Tool für Außendienstmitarbeiter im B2B Vertrieb.

Der Außendienstler soll direkt nach einem Kundentermin möglichst natürlich einen Besuchsbericht erfassen können. Ziel ist nicht, ein CRM nachzubauen, sondern die Hürde zwischen frischem Außendienstwissen und einem verwertbaren Besuchsbericht zu senken.

Der Assistent übernimmt dabei folgende Kernaufgaben:

- freie Aussage entgegennehmen
- relevante Inhalte erkennen
- Informationen strukturieren
- fehlende Angaben dialoggesteuert nachfragen
- Bewertungen vorschlagen
- Korrekturen verarbeiten
- einen ausformulierten Besuchsbericht erzeugen
- vor dem Speichern vollständig zusammenfassen
- erst nach expliziter Bestätigung speichern beziehungsweise übergeben

Das CRM ist in diesem Konzept nur die Gegenstelle für typische CRM-Bezüge wie Kunde, Ansprechpartner, Angebote, Vertreter und gespeicherte Besuchsberichte.

## 3. Dialogsteuerung statt starres Interview

Die Berichtserfassung soll dialoggesteuert sein, aber nicht künstlich verlängert werden.

Das bedeutet:

- Der Außendienstler kann frei beginnen.
- Das System analysiert die erste Aussage.
- Wenn Informationen fehlen, fragt das System gezielt nach.
- Wenn alle notwendigen Informationen bereits enthalten sind, wird keine künstliche Interviewstrecke gestartet.
- In diesem Fall erzeugt das System direkt eine Zusammenfassung und fragt, ob der Bericht so korrekt ist.

Die Dialogführung ist damit keine starre Formularabfrage. Sie ist eine Kontrolllogik, die erkennt, ob ein Besuchsbericht vollständig genug ist.

## 4. Grundablauf aus Nutzersicht

Der erwartete Ablauf im MVP sieht wie folgt aus:

1. Der Außendienstler öffnet die mobile Web-Oberfläche.
2. Der Außendienstler loggt sich ein.
3. Nach dem Login sieht er bestehende Chat- beziehungsweise Berichtsverläufe.
4. Er kann einen neuen Chat beziehungsweise Besuchsbericht starten.
5. Das System stellt die erste Frage sichtbar als Text dar.
6. Dieselbe Frage wird per Text-to-Speech vorgelesen.
7. Der Außendienstler antwortet entweder per Texteingabe oder per Sprache.
8. Bei Spracheingabe wird Speech-to-Text genutzt.
9. Das System verarbeitet den Turn.
10. Das System zeigt die nächste Antwort oder Rückfrage als Text.
11. Die Antwort oder Rückfrage wird zusätzlich per Text-to-Speech vorgelesen.
12. Dieser turn-basierte Ablauf wiederholt sich bis zur finalen Zusammenfassung.
13. Die finale Zusammenfassung wird vollständig angezeigt und vorgelesen.
14. Der Außendienstler bestätigt oder korrigiert.
15. Erst nach Bestätigung wird der Bericht gespeichert beziehungsweise an die Gegenstelle übergeben.

## 5. Hands-free-Zielbild

Das Zielbild ist eine möglichst vollständige Hands-free-Nutzung nach dem Start des Berichtschats.

Der praktische Nutzungskontext:

Ein Außendienstler verlässt den Kunden, startet die App, beginnt einen neuen Bericht, legt das Smartphone in die Handyhalterung im Auto und kann den Besuchsbericht während der Weiterfahrt vollständig per Sprache erfassen.

Ab Start des Berichtschats soll der Nutzer das Smartphone möglichst nicht mehr berühren oder anschauen müssen.

Daraus ergeben sich folgende Anforderungen:

- Systemantworten müssen automatisch vorgelesen werden.
- Nach einer vorgelesenen Systemfrage soll der Nutzer möglichst direkt sprechen können.
- Spracheingaben müssen in Text umgewandelt und im Chat sichtbar werden.
- Korrekturen müssen per Sprache möglich sein.
- Die finale Zusammenfassung muss vollständig vorgelesen werden.
- Die finale Bestätigung muss per Sprache möglich sein.
- Die sichtbare Textoberfläche bleibt vorhanden, ist aber nicht zwingend für den Abschluss des Berichts erforderlich.

## 6. Turn-basiertes Voice-Modell

Das Projekt soll kein Echtzeit-Voice-Streaming als Kernfunktion verwenden.

Der Ablauf bleibt turn-basiert:

1. System stellt eine Frage oder gibt eine Zusammenfassung aus.
2. Text-to-Speech liest die Systemausgabe vor.
3. Nach dem Vorlesen geht die Anwendung idealerweise in den Zuhörmodus.
4. Der Nutzer spricht seine Antwort.
5. Speech-to-Text erzeugt ein Transkript.
6. Das Transkript wird an die Dialoglogik übergeben.
7. Die Dialoglogik erzeugt den nächsten Schritt.

Bevorzugte Variante:

- Nach jeder vorgelesenen Systemantwort startet die Spracheingabe möglichst automatisch.

Fallback:

- Falls automatische Spracheingabe im Browser oder im Frontend instabil ist, darf es einen manuellen Start der Aufnahme geben.

Wake-Word-Logik ist nicht primärer MVP-Fokus, weil dauerhaftes Mithören und Aktivierungswort-Erkennung technisch und konzeptionell komplexer sind.

## 7. Textchat als sichtbare Basis

Der Textchat ist nicht nur ein Debug-Werkzeug.

Er ist die sichtbare Oberfläche des MVP:

- Systemfragen werden im Chat angezeigt.
- Nutzerantworten werden im Chat angezeigt.
- Transkripte aus Spracheingaben werden im Chat angezeigt.
- Korrekturen bleiben nachvollziehbar.
- Der Gesprächsverlauf kann später wieder geöffnet werden.

Voice erweitert diesen Textchat:

- Speech-to-Text ist ein zusätzlicher Eingabeweg.
- Text-to-Speech ist ein zusätzlicher Ausgabeweg.
- Der fachliche Workflow bleibt derselbe.

## 8. Frontend-Verständnis

Mit mobiler Web-App ist keine native App gemeint.

Gemeint ist ein separates Frontend im Browser:

- responsive Oberfläche für Smartphone
- keine native iOS- oder Android-App
- kein App-Store-Deployment
- Kommunikation mit dem Backend über API-Calls
- perspektivisch als PWA denkbar, aber nicht zwingend für den MVP

Der Begriff sollte im weiteren Konzept präziser als mobile Web-Oberfläche oder Mobile Web Frontend verwendet werden, damit keine native App suggeriert wird.

## 9. Python Backend als zentrale Anwendungsschicht

Die bevorzugte Projektsprache ist Python.

Das Python Backend soll die zentrale Logik des Assistenten enthalten:

- Dialogsteuerung
- LLM-Provider-Anbindung
- Extraktion und Strukturierung
- Bewertungsvorschläge
- Korrekturverarbeitung
- finale Berichtserstellung
- Koordination von Speech-to-Text
- Koordination von Text-to-Speech
- API-Kommunikation mit der CRM-Gegenstelle
- Login- und Sessionlogik

Das Frontend soll möglichst schlank bleiben und vor allem:

- Audio aufnehmen
- Text anzeigen
- Audio abspielen
- Nutzereingaben senden
- Ergebnisse darstellen

Die zentrale Verarbeitung liegt im Backend.

## 10. Speech-to-Text und Text-to-Speech als Backend-Leistung

Speech-to-Text und Text-to-Speech sollen konzeptionell vom Backend geleistet beziehungsweise koordiniert werden.

Der Grundgedanke:

- Das Frontend nimmt Audio auf.
- Das Frontend sendet Audio an das Python Backend.
- Das Backend transkribiert Audio zu Text.
- Das Backend verarbeitet den Dialogturn.
- Das Backend erzeugt die Antwort.
- Das Backend erzeugt daraus Audio.
- Das Frontend spielt das Antwort-Audio ab.

Dadurch bleibt die Voice-Logik zentral kontrollierbar und wird nicht abhängig von den Fähigkeiten einzelner Browser.

## 11. Local-first-Zielrichtung

Die persönliche technische Zielrichtung ist local-first.

Das bedeutet:

- lokale Modelle sind das bevorzugte Ziel
- Speech-to-Text soll im Idealfall lokal laufen
- Text-to-Speech soll im Idealfall lokal laufen
- lokale LLMs über LM Studio sollen perspektivisch nutzbar sein
- externe APIs sollen nicht unnötig verwendet werden, insbesondere wegen möglicher Kosten

Für STT und TTS sind Hugging-Face-Modelle eine naheliegende Option.

Für die LLM-Logik bleibt LM Studio als lokale Option vorgesehen.

## 12. Projektanforderung: OpenAI und Gemini

Obwohl local-first die persönliche Zielrichtung ist, fordert das Abschlussprojekt die Einbindung von OpenAI und Gemini.

Daher gilt:

- OpenAI muss als Provider integriert werden.
- Gemini muss als Provider integriert werden.
- Beide APIs sollen technisch demonstrierbar sein.
- Die Anwendung darf nicht hart an einen einzelnen Provider gebunden sein.
- Die Architektur muss provider-unabhängig aufgebaut werden.

Diese Anforderung steht nicht im Widerspruch zur local-first-Zielrichtung. Es sind zwei verschiedene Ebenen:

| Ebene | Bedeutung |
|---|---|
| Persönliches technisches Ziel | möglichst lokale Ausführung |
| Projektanforderung | OpenAI und Gemini müssen eingebunden werden |
| Architekturprinzip | austauschbare Provider |

## 13. Reihenfolge der LLM-Umsetzung

Die Umsetzung der Dialog- beziehungsweise LLM-Logik soll schrittweise erfolgen.

Erster Schritt:

- OpenAI anbinden
- Gemini anbinden
- mit stärkeren API-Modellen den fachlichen Ablauf stabil bekommen

Ziel dieses ersten Schritts:

- Dialogführung testen
- Extraktion testen
- Rückfragen testen
- Bewertungen testen
- Korrekturen testen
- finale Berichtserstellung testen

Zweiter Schritt:

- lokale Modelle über LM Studio prüfen
- analysieren, wie gut derselbe Ablauf lokal funktioniert
- bei Bedarf stärker geführte Code-Logik einbauen

Lokale Modelle werden voraussichtlich mehr Steuerung durch den Code brauchen als starke API-Modelle.

Mögliche Konsequenzen:

- engeres JSON-Schema
- kleinere Teilaufgaben pro Turn
- stärkere Backend-Validierung
- eventuell Trennung zwischen Extraktionsmodell und Formulierungsmodell
- klarere Systemprompts und kontrollierte Ausgabeformate

## 14. Provider-Auswahl im Frontend

Der LLM-Provider soll im Frontend auswählbar sein.

Für den MVP gilt:

- Die Auswahl ist sichtbar in den Optionen.
- Mindestens OpenAI und Gemini sind auswählbar.
- Lokale Modelle über LM Studio können perspektivisch ergänzt werden.
- Die Auswahl wird nicht dauerhaft nutzerspezifisch gespeichert.
- Es gibt keine komplexe Admin-Konfiguration.
- Die Auswahl wird für den aktuellen Workflow beziehungsweise Chat an das Backend übergeben.

Die Provider-Auswahl dient im MVP vor allem dem Vergleich und der Demonstration der unterschiedlichen LLM-Anbindungen.

## 15. CRM-Gegenstelle statt CRM-Kern

Das Muster-CRM ist nicht Teil des eigentlichen Programms.

Der Assistent soll nicht direkt als CRM-System gedacht werden. Stattdessen spricht der Assistent konzeptionell mit einer CRM-API.

Auch wenn diese CRM-API im MVP lokal simuliert wird, bleibt die gedankliche Trennung wichtig:

- Der Assistent ist die Erfassungs- und Dialogschicht.
- Die CRM-Gegenstelle liefert Stammdaten und nimmt Berichte entgegen.
- Die SQL-Datenbank ist nur die technische Placeholder-Basis hinter dieser CRM-Gegenstelle.

Typische Daten der CRM-Gegenstelle:

- Kunden
- Ansprechpartner
- Angebote
- Aufträge oder Vorgänge, soweit für den Besuchsbericht relevant
- Vertreter beziehungsweise Außendienstler
- gespeicherte Besuchsberichte

Der Assistent soll nicht unnötig doppelte Stammdatenstrukturen aufbauen.

## 16. Nutzerkontext und Vertreterlogik

Der Außendienstler kann fachlich als Vertreter aus dem CRM verstanden werden.

Gleichzeitig soll der Assistent eine eigene Login-Logik besitzen, damit er nicht vollständig davon abhängig ist, ob ein konkretes CRM eine Vertreterlogik anbietet.

Die gemeinsam festgelegte Richtung:

- Der Assistent hat eine eigene Anmeldung.
- Ein Assistant-User kann mit einem CRM-Vertreter verknüpft sein.
- Wenn die CRM-Gegenstelle Vertreterdaten bietet, können diese genutzt werden.
- Wenn ein angebundenes CRM keine Vertreterlogik besitzt, kann der Assistent trotzdem eigene Nutzer verwalten.
- Der Login-Kontext bestimmt, welcher Nutzer einen Bericht erstellt.
- Der optionale CRM-Vertreterbezug kann bei Übergabe oder Speicherung mitgegeben werden.

Damit bleibt das System flexibel und baut keine harte Abhängigkeit zum Placeholder CRM auf.

## 17. Login-Logik

Für den MVP soll es eine echte Login-Logik mit E-Mail und Passwort geben.

Auch wenn im MVP nur Mock-Daten verwendet werden, soll der Login fachlich realistisch abgebildet werden.

MVP-Anforderungen:

- Login per E-Mail und Passwort
- Nutzer wird im Assistenten authentifiziert
- Nutzer kann optional einem CRM-Vertreter zugeordnet sein
- Berichte laufen im Kontext des angemeldeten Nutzers
- keine reine Vertreterauswahl ohne Authentifizierung
- keine übertriebene Rollen- und Rechteverwaltung im MVP

Nicht erforderlich für den MVP:

- komplexe Benutzerverwaltung
- Admin-Oberfläche
- Passwort-Reset-Prozess
- Single Sign-On
- OAuth-Anbindung
- produktionsreifes Rollenmodell

## 18. Bewertungsblock im Besuchsbericht

Der Besuchsbericht enthält nicht nur Freitext, sondern auch strukturierte Bewertungswerte.

Für den MVP sind sechs Bewertungsfelder Pflicht:

| Bewertungsfeld | Skala | Bedeutung hoher Wert |
|---|---:|---|
| Vertriebschance | 1 bis 10 | hohe Vertriebschance |
| Gesprächsstimmung | 1 bis 10 | sehr positive Stimmung |
| Priorität | 1 bis 10 | hohe Priorität |
| Abschlusswahrscheinlichkeit | 1 bis 10 | hohe Abschlusswahrscheinlichkeit |
| Handlungsbedarf | 1 bis 10 | dringender Handlungsbedarf |
| Kundenzufriedenheit | 1 bis 10 | hohe Kundenzufriedenheit |

Die Skala ist nicht bei jedem Feld einfach gut gegen schlecht. Ein hoher Wert bedeutet, dass der jeweilige Aspekt stark ausgeprägt ist.

Beispiel:

- Hohe Gesprächsstimmung ist positiv.
- Hoher Handlungsbedarf bedeutet hohe Aufmerksamkeit und Dringlichkeit.

## 19. Ableitung und Bestätigung der Bewertungen

Das System soll die Bewertungen nicht stumpf als Formular abfragen.

Stattdessen soll es versuchen, aus der Aussage des Außendienstlers passende Werte abzuleiten.

Ablauf:

1. Nutzer schildert den Termin.
2. System erkennt Hinweise für die Bewertungsfelder.
3. System schlägt Werte auf einer Skala von 1 bis 10 vor.
4. System gibt eine kurze Begründung für die Bewertung.
5. Nutzer bestätigt oder korrigiert die Werte.
6. Korrigierte Werte überschreiben den Vorschlag.

Wenn einzelne Bewertungen nicht seriös ableitbar sind, fragt das System gezielt nur diese fehlenden Bewertungen nach.

Die Begründung dient im Dialog zur Kontrolle. Sie hilft dem Außendienstler zu erkennen, ob das System die Situation richtig interpretiert hat.

## 20. Verhältnis von Bewertung und Freitext

Die strukturierten Bewertungsfelder werden als Werte gespeichert.

Der ausformulierte Freitextbericht muss inhaltlich zu diesen Bewertungen passen.

Der Freitext muss die Zahlenwerte nicht stumpf wiederholen. Er soll aber dieselbe fachliche Einschätzung widerspiegeln.

Beispiel:

Strukturierte Werte:

- Vertriebschance: 7 von 10
- Gesprächsstimmung: 8 von 10
- Handlungsbedarf: 6 von 10

Passender Freitext:

> Der Kunde zeigte grundsätzliches Interesse und das Gespräch verlief positiv. Vor einer Entscheidung möchte der Kunde die Konditionen intern mit dem Einkauf abstimmen. Als nächster Schritt soll ein angepasstes Angebot vorbereitet werden.

Die Begründung der Bewertung muss nicht zwingend als eigener Textblock im CRM-Bericht gespeichert werden. Sie ist primär Teil des Dialogs und der Nutzerkontrolle.

## 21. Aktuell gesetzte Leitplanken

Aus dem bisherigen Gespräch ergeben sich folgende Leitplanken:

| Bereich | Entscheidung |
|---|---|
| Fachlicher Kern | sprach- und dialoggesteuerte Besuchsbericht-Erfassung |
| CRM | nur Gegenstelle, nicht Kern des Programms |
| Frontend | mobile Web-Oberfläche im Browser |
| Backend | Python |
| Eingabe | Text und Sprache |
| Ausgabe | Text und Text-to-Speech |
| Ablauf | turn-basiert |
| Hands-free | Ziel nach Start des Chats |
| STT/TTS | bevorzugt Backend-Leistung |
| STT/TTS-Ziel | möglichst lokal |
| LLM-Ziel | provider-unabhängig |
| erste LLM-Provider | OpenAI und Gemini |
| spätere LLM-Option | LM Studio / lokale Modelle |
| Provider-Auswahl | im Frontend auswählbar |
| Login | E-Mail und Passwort |
| CRM-Vertreter | optionale Verknüpfung mit Assistant-User |
| Bewertungsblock | sechs Pflichtfelder, Skala 1 bis 10 |

## 22. Noch offene Konzeptfragen

Folgende Punkte sind noch nicht final entschieden und sollten weiter im Interviewmodus geklärt werden:

1. Darf der LLM-Provider während eines laufenden Besuchsbericht-Chats gewechselt werden oder nur vor Chatstart?
2. Wie genau soll die Aufnahme im Frontend gestartet und beendet werden?
3. Welche Mindestfelder machen einen Besuchsbericht final speicherfähig?
4. Wie ausführlich muss die finale Zusammenfassung vorgelesen werden?
5. Welche Korrekturbefehle müssen im Voice-Modus sicher funktionieren?
6. Welche Daten werden im Chatverlauf gespeichert?
7. Wie lange bleiben offene Berichtsentwürfe gespeichert?
8. Wie genau wird der Placeholder-CRM-API-Vertrag geschnitten?
9. Welche konkreten OpenAI- und Gemini-Modelle werden zuerst getestet?
10. Welche lokalen STT- und TTS-Modelle werden als erste Kandidaten geprüft?
11. Welche lokalen LLMs über LM Studio werden als erste Kandidaten geprüft?
12. Wie wird Datenschutz im MVP praktisch umgesetzt?

## 23. Zusammenfassung

Der aktuelle Konzeptstand ist:

Der MVP ist ein sprach- und dialoggesteuerter Besuchsbericht-Assistent für den B2B Außendienst. Die sichtbare Basis ist ein mobiler Textchat im Browser. Dieser Chat wird durch Speech-to-Text und Text-to-Speech erweitert, sodass der Bericht nach dem Start des Chats möglichst hands-free erstellt werden kann.

Das Python Backend ist die zentrale Anwendungsschicht. Es koordiniert Dialoglogik, LLM-Provider, STT, TTS, Bewertungsvorschläge, Korrekturen und die Übergabe an eine CRM-Gegenstelle.

Das System ist local-first gedacht, muss aber aufgrund der Projektanforderungen OpenAI und Gemini integrieren. Lokale Modelle über LM Studio sowie lokale STT- und TTS-Modelle bleiben als Zielrichtung erhalten.

Das CRM ist nicht Kern des Programms. Es ist eine externe oder simulierte Gegenstelle, die typische CRM-Daten bereitstellt und Besuchsberichte aufnehmen kann. Der Assistent verwaltet den Login selbst, kann Nutzer aber optional mit CRM-Vertretern verknüpfen.

Der Besuchsbericht besteht aus einem ausformulierten Freitext und strukturierten Feldern. Ein besonderer Bestandteil ist der Bewertungsblock mit sechs Pflichtwerten auf einer Skala von 1 bis 10. Das System soll diese Bewertungen aus dem Gespräch ableiten, kurz begründen und vom Außendienstler bestätigen oder korrigieren lassen.
