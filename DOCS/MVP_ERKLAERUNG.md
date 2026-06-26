# BENNO: Sprachgeführter Besuchsbericht-Assistent

## Was bedeutet BENNO?

BENNO ist der Projektname für den Besuchsbericht-Assistenten.

BENNO steht für:

**B2B Encounter Notes and Next-step Organizer**

Der Name beschreibt ziemlich genau, worum es geht: BENNO hilft dabei, Notizen aus B2B-Kundenterminen festzuhalten und die nächsten Schritte zu organisieren.

Gleichzeitig ist der Name bewusst menschlich gewählt. Die Anwendung soll sich nicht wie ein weiteres Formular oder wie ein kompliziertes CRM-Modul anfühlen, sondern eher wie ein digitaler Begleiter, der nach einem Kundentermin hilft, den Besuch sauber zu dokumentieren.

Man kann sich BENNO wie einen ruhigen Beifahrer für den Außendienst vorstellen: Er hört zu, fragt nach, sortiert die Informationen und sorgt dafür, dass am Ende ein brauchbarer Besuchsbericht entsteht.

## Worum geht es?

BENNO ist ein digitaler Assistent für Menschen im B2B-Außendienst.

Gemeint sind zum Beispiel Vertriebsmitarbeiter, die Kunden besuchen, Gespräche führen, Angebote nachfassen, neue Bedarfe aufnehmen oder nächste Schritte vereinbaren. Nach solchen Terminen müssen sie normalerweise einen Besuchsbericht schreiben, damit im Unternehmen nachvollziehbar bleibt, was besprochen wurde und was als Nächstes passieren soll.

Genau dabei soll die Anwendung helfen.

Die Idee ist: Der Außendienstler soll nach einem Kundentermin nicht lange am Handy tippen oder später am Laptop aus dem Gedächtnis einen Bericht schreiben müssen. Stattdessen startet er die App, spricht frei über den Termin, beantwortet ein paar gezielte Rückfragen und bekommt am Ende einen sauberen Besuchsbericht vorgeschlagen.

Das System speichert den Bericht aber nicht einfach automatisch. Vorher wird alles noch einmal zusammengefasst. Erst wenn der Nutzer ausdrücklich bestätigt, wird der Bericht gespeichert oder später an ein CRM-/ERP-System zurückgeschrieben.

## Welches Problem löst das?

Besuchsberichte sind im Vertrieb wichtig, werden aber oft als lästig empfunden.

Typische Probleme sind:

- Der Bericht wird erst Stunden oder Tage später geschrieben.
- Details aus dem Gespräch gehen verloren.
- Jeder schreibt anders ausführlich.
- Wichtige nächste Schritte werden vergessen.
- Der Innendienst weiß nicht genau, was beim Kunden besprochen wurde.
- Kunden-, Angebots- oder Ansprechpartnerinformationen landen unvollständig im System.

Das Projekt soll diese Lücke schließen: Frisches Wissen aus dem Kundentermin soll direkt nach dem Gespräch festgehalten und in eine brauchbare Form gebracht werden.

## Die typische Nutzungssituation

Ein Außendienstler kommt gerade aus einem Kundentermin.

Er setzt sich ins Auto, startet die App und beginnt einen neuen Besuchsbericht. Danach soll er möglichst wenig anfassen müssen. Im Zielbild läuft es ungefähr so:

1. Die App fragt, worum es beim Termin ging.
2. Der Außendienstler erzählt frei, was passiert ist.
3. Die App erkennt Namen, Themen, Ergebnisse und nächste Schritte.
4. Wenn etwas fehlt oder unklar ist, fragt die App gezielt nach.
5. Der Außendienstler kann jederzeit etwas korrigieren.
6. Die App prüft, ob die wichtigen Besuchsbericht-Felder gefüllt sind.
7. Am Ende liest die App den Bericht vollständig vor.
8. Der Außendienstler bestätigt oder korrigiert.
9. Erst nach der Bestätigung wird der Bericht gespeichert.

Der Ablauf soll sich eher wie ein geführtes Gespräch anfühlen und nicht wie ein Formular.

## Was bedeutet "hands-free"?

Das eigentliche Produktziel ist eine möglichst freihändige Nutzung.

Der Nutzer soll nach dem Start des Berichts idealerweise nicht mehr tippen müssen. Die App spricht mit ihm, hört seine Antworten, stellt Rückfragen und liest am Ende die Zusammenfassung vor.

Das ist besonders für Außendienstler interessant, weil sie häufig zwischen Terminen unterwegs sind. Ein Bericht kann direkt nach dem Termin entstehen, solange die Erinnerung frisch ist, ohne dass der Nutzer längere Texte auf dem Smartphone schreiben muss.

Wichtig ist aber: Auch im Hands-free-Zielbild bleibt die sichtbare Textansicht erhalten. Der Nutzer kann also weiterhin sehen, was verstanden wurde, und bei Bedarf per Text eingreifen.

## Was macht die KI?

Die KI soll nicht einfach einen fertigen Text erfinden.

Sie soll vor allem helfen, aus freier Sprache einen brauchbaren Bericht zu machen. Dazu gehören mehrere Aufgaben:

- Sie hört bzw. liest die freie Beschreibung des Nutzers.
- Sie erkennt wichtige Informationen wie Kunde, Ansprechpartner, Gesprächsanlass und Ergebnis.
- Sie merkt, wenn Pflichtinformationen fehlen.
- Sie fragt fehlende Besuchsbericht-Felder gezielt ab.
- Sie stellt gezielte Rückfragen.
- Sie verarbeitet Korrekturen.
- Sie schlägt Bewertungen vor, zum Beispiel zur Vertriebschance oder Dringlichkeit.
- Sie formuliert am Ende einen verständlichen Bericht.

Die fachlichen Entscheidungen sollen dabei nicht blind der KI überlassen werden. Die Anwendung prüft, was gespeichert werden darf, welche Informationen fehlen und ob der Nutzer wirklich bestätigt hat.

Kurz gesagt:

Die KI hilft beim Verstehen und Formulieren. Die Anwendung sorgt für Struktur, Prüfung und Bestätigung.

## Was ist das System bewusst nicht?

Das Projekt baut kein eigenes CRM-System.

Ein CRM oder ERP ist das System, in dem Unternehmen ihre Kunden, Ansprechpartner, Angebote, Aufträge und Vertriebsaktivitäten verwalten. Dieses Projekt soll so ein System nicht ersetzen.

Die Anwendung ist stattdessen eine Erfassungs- und Übergabeschicht.

Sie hilft dabei, einen Besuchsbericht bequem zu erfassen, zu strukturieren und später an ein bestehendes System zu übergeben oder zurückzuschreiben. Für das Projekt wird zunächst mit einer kleinen Mock-Datenbank gearbeitet. Später soll sich die Struktur an eNVenta orientieren, sobald die echten Besuchsbericht-Felder vorliegen.

Der relevante CRM-/ERP-Kontext ist eNVenta von der eNVenta Group:

https://www.enventa-group.com/

## Warum erst Text und später Sprache?

Das vollständige Ziel ist sprachgeführt und möglichst hands-free.

Trotzdem wird der erste technische Schritt textbasiert gebaut. Das bedeutet: Der Nutzer schreibt zunächst in einen Chat, und die App antwortet ebenfalls als Text.

Das klingt erstmal weniger spektakulär, ist aber sinnvoll. Der wichtigste Teil des Projekts ist nicht das Mikrofon, sondern der Ablauf dahinter:

- Was wurde verstanden?
- Welche Informationen fehlen noch?
- Welche Rückfrage ist sinnvoll?
- Wie werden Korrekturen verarbeitet?
- Wann ist der Bericht vollständig?
- Wie sieht die finale Bestätigung aus?

Wenn dieser Ablauf stabil funktioniert, kann Sprache ergänzt werden:

- Spracheingabe wird in Text umgewandelt.
- Der gleiche Berichtsdialog verarbeitet diesen Text.
- Die Antwort der App wird wieder vorgelesen.

So bleibt der Kern gleich, egal ob der Nutzer tippt oder spricht.

## Wie geht BENNO mit CRM-Feldern um?

Ein Besuchsbericht besteht nicht nur aus einem schönen Text.

In einem CRM- oder ERP-System gibt es bestimmte Felder, die gefüllt werden müssen. Dazu können zum Beispiel Kunde, Ansprechpartner, Besuchsdatum, Anlass, Ergebnis, nächster Schritt, Wiedervorlagedatum oder Angebotsbezug gehören.

BENNO soll diese Felder nicht einfach als starres Formular abfragen. Stattdessen soll die Anwendung aus dem Gespräch erkennen, welche Informationen schon vorhanden sind.

Wenn der Außendienstler in seiner ersten Beschreibung bereits sagt, bei welchem Kunden er war, mit wem er gesprochen hat und was als Nächstes passieren soll, muss BENNO diese Dinge nicht noch einmal unnötig abfragen.

Wenn aber etwas fehlt, fragt BENNO gezielt nach:

> Wann soll nachgefasst werden?

oder:

> Ging es dabei um ein bestehendes Angebot?

So entsteht Schritt für Schritt ein Bericht, der nicht nur sprachlich gut klingt, sondern auch die benötigten CRM-Felder abdeckt.

## Was passiert mit dem fertigen Bericht?

Am Ende soll BENNO den bestätigten Besuchsbericht an das passende System übergeben.

Im Projekt wird dafür zunächst mit Beispieldaten gearbeitet. Später soll der Ablauf so gedacht sein, dass die ausgefüllten Besuchsbericht-Felder und der ausformulierte Bericht in Richtung eNVenta beziehungsweise CRM-/ERP-System zurückgeschrieben werden können.

Das bedeutet:

- Der Außendienstler spricht oder schreibt seinen Bericht.
- BENNO macht daraus strukturierte Informationen.
- BENNO zeigt den fertigen Bericht zur Kontrolle.
- Der Nutzer bestätigt.
- Erst danach werden Bericht und Felder gespeichert oder übergeben.

Dadurch bleibt der Außendienstler in Kontrolle. Die KI darf vorbereiten, aber sie entscheidet nicht alleine, was final im System landet.

## Was entsteht am Ende?

Am Ende entsteht ein Besuchsbericht, der sowohl für Menschen als auch für ein späteres CRM-/ERP-System brauchbar ist.

Der Bericht enthält zum Beispiel:

- welcher Kunde oder Lead betroffen ist
- mit wem gesprochen wurde
- warum der Termin stattfand
- was besprochen wurde
- welches Ergebnis es gab
- was als Nächstes passieren soll
- ob ein Angebot oder Auftrag eine Rolle spielt
- wie der Vorgang bewertet wird
- ob der Innendienst etwas erledigen muss

Wenn etwa ein neuer Ansprechpartner genannt wird, legt die App ihn nicht einfach automatisch an. Stattdessen kann eine Aufgabe für den Innendienst entstehen: "Bitte Ansprechpartner prüfen oder ergänzen."

So wird verhindert, dass unkontrolliert falsche Stammdaten entstehen.

## Wiedervorlagen und Aufgaben für den Innendienst

Ein wichtiger Teil des Projekts sind Wiedervorlagen und Folgeaufgaben.

Nicht jeder Besuchsbericht ist mit dem Speichern erledigt. Oft ergeben sich aus einem Termin nächste Schritte:

- Der Kunde soll nächste Woche angerufen werden.
- Ein Angebot soll erstellt oder angepasst werden.
- Ein neuer Ansprechpartner muss im System geprüft werden.
- Stammdaten fehlen oder sind unklar.
- Der Innendienst soll Details klären.

BENNO soll solche Folgeaufgaben erkennen und daraus einfache Wiedervorlagen oder Aufgaben für den Innendienst ableiten.

Beispiel:

Der Außendienstler sagt:

> Der Kunde möchte ein angepasstes Angebot. Die technischen Details soll bitte der Innendienst nochmal klären.

Dann soll BENNO nicht nur einen Besuchsbericht schreiben, sondern auch festhalten, dass daraus eine Aufgabe für den Innendienst entsteht.

Damit geht es nicht nur um Dokumentation, sondern auch darum, dass nach dem Kundentermin wirklich etwas passiert.

## Beispiel

Ein Außendienstler sagt:

> Ich war gerade bei NordTech und habe mit Frau Keller gesprochen. Es ging um das offene Angebot zur Rahmenvereinbarung. Die Stimmung war gut, aber sie möchte die Konditionen noch mit dem Einkauf abstimmen. Ich soll nächste Woche nochmal nachfassen.

BENNO könnte antworten:

> Ich habe verstanden: Der Termin war bei NordTech mit Frau Keller. Es ging um ein offenes Angebot zur Rahmenvereinbarung. Das Gespräch war positiv, aber die Kundin möchte intern noch mit dem Einkauf sprechen. Als nächster Schritt soll nächste Woche nachgefasst werden. Stimmt das so?

Wenn der Nutzer sagt:

> Nicht Frau Keller, sondern Herr Becker.

dann wird diese Korrektur übernommen. Danach macht die App an der passenden Stelle weiter.

Wenn noch etwas fehlt, fragt BENNO gezielt nach:

> Soll ich als Follow-up-Datum kommenden Dienstag eintragen?

Am Ende folgt eine vollständige Zusammenfassung:

> Ich würde folgenden Besuchsbericht speichern: ...

Darin kann auch stehen:

> Zusätzlich wird eine Wiedervorlage für nächste Woche angelegt.

Erst wenn der Nutzer sagt:

> Ja, speichern.

wird der Bericht tatsächlich gespeichert.

## Datenschutzrichtung

Für den ersten stabilen Aufbau wird OpenAI genutzt, weil damit der Berichtsdialog schneller und zuverlässiger getestet werden kann.

Sobald der Ablauf funktioniert, soll geprüft werden, wie weit sich das System lokal betreiben lässt. Das bedeutet: Die KI läuft dann möglichst auf eigener Infrastruktur oder über eine lokale Schnittstelle, statt sensible Inhalte dauerhaft an externe Dienste zu geben.

Der Grund dafür ist Datenschutz.

In echten Besuchsberichten können vertrauliche Informationen stehen: Kundennamen, Ansprechpartner, Preise, Angebote, Probleme, Chancen oder interne Einschätzungen. Deshalb ist die langfristige Richtung, so viel wie möglich lokal und kontrolliert zu verarbeiten.

Im Projekt selbst wird zunächst mit Mock-Daten gearbeitet, also mit erfundenen Kunden und Beispieldaten.

## Warum ist das nützlich?

Der Nutzen liegt nicht darin, dass "irgendeine KI einen Text schreibt".

Der Nutzen liegt darin, dass der Außendienstler weniger Reibung hat:

- Er dokumentiert direkt nach dem Termin.
- Er muss weniger tippen.
- Der Bericht wird vollständiger.
- Das Unternehmen bekommt einheitlichere Informationen.
- Folgeaufgaben gehen seltener verloren.
- Der Innendienst kann besser weiterarbeiten.

Das Projekt verbindet also zwei Welten:

Auf der einen Seite ein natürliches Gespräch mit dem Nutzer. Auf der anderen Seite eine strukturierte Dokumentation, die später in ein CRM-/ERP-System passt.

## Kurzfassung

Das Projekt ist ein sprachgeführter Assistent für Besuchsberichte im B2B-Außendienst.

Ein Außendienstler soll nach einem Kundentermin frei erzählen können, was passiert ist. Die App erkennt daraus die wichtigen Informationen, fragt fehlende Punkte nach, verarbeitet Korrekturen und erstellt einen sauberen Bericht. Am Ende wird alles vorgelesen oder angezeigt. Erst nach ausdrücklicher Bestätigung wird gespeichert.

Der erste technische Schritt läuft als Textchat. Das eigentliche Produktziel ist aber eine möglichst hands-free Nutzung mit Spracheingabe und Sprachausgabe.
