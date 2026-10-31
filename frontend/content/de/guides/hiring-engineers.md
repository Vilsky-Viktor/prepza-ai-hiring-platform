---
title: "Softwareentwickler einstellen: ein strukturierter Prozess von der Stellenbeschreibung bis zum Angebot"
seoTitle: "Entwickler einstellen: strukturierter Recruiting-Prozess"
description: "Schritt für Schritt Softwareentwickler einstellen: Anforderungsprofil, Vorauswahl, Wissenstest, Coding, Systemdesign, strukturierte Interviews und Angebot."
updated: "2026-10-29"
---

# Softwareentwickler einstellen: ein strukturierter Prozess von der Stellenbeschreibung bis zum Angebot

Entwickler einzustellen ist auf eine Weise teuer, die man leicht übersieht: Der größte Teil der Kosten ist die Zeit deiner eigenen Entwickler. Jede Stunde, die sie in einem Interview mit jemandem verbringen, der den Stack nicht kennt, ist eine Stunde, in der sie nichts bauen. Ein guter Prozess stellt die günstigen, breiten Prüfungen an den Anfang und hebt die teuren, tiefen für die wenigen auf, die voraussichtlich erfolgreich sein werden.

Dieser Leitfaden geht diesen Prozess Schritt für Schritt durch. Er stützt sich auf die Forschung zur Personalauswahl, wo diese eindeutig ist, und sagt es, wo sie es nicht ist.

## Der Prozess im Überblick

| Phase | Was geprüft wird | Wer Zeit investiert |
| --- | --- | --- |
| 1. Anforderungsprofil und Stellenbeschreibung | Was die Stelle tatsächlich braucht | Hiring Manager, ein erfahrener Entwickler |
| 2. Sichtung von Lebenslauf oder Bewerbung | Nur harte Anforderungen | Recruiter oder Hiring Manager |
| 3. Wissenstest | Was der Kandidat über deinen Stack weiß | Der Kandidat; du liest die Ergebnisse |
| 4. Take-Home-Aufgabe oder Live-Coding | Ob er funktionierenden Code schreiben kann | Ein oder zwei Entwickler |
| 5. Systemdesign (Senior-Stellen) | Wie er über größere Systeme nachdenkt | Ein erfahrener Entwickler |
| 6. Strukturiertes Verhaltensinterview | Wie er mit anderen zusammenarbeitet | Hiring Manager, ein Kollege |
| 7. Referenzen einholen | Bestätigung des bisher Gehörten | Hiring Manager |
| 8. Entscheidung und Angebot | Eine faire, dokumentierte Entscheidung | Das Recruiting-Team |

## Was die Forschung sagt

Große Übersichtsarbeiten der Personalauswahlforschung vergleichen Methoden danach, wie gut ihre Ergebnisse mit der späteren Arbeitsleistung zusammenhängen. Die jüngste große Studie von Sackett, Zhang, Berry und Lievens (2022) hat frühere Schätzungen nach unten korrigiert und festgestellt, dass die im Durchschnitt stärksten Prädiktoren durchweg stellenspezifische Verfahren waren ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Ihre Schätzwerte, auf einer Skala, auf der 0 keinen Zusammenhang und 1 einen perfekten bedeutet:

| Methode | Geschätzte Validität |
| --- | --- |
| Strukturierte Interviews | 0,42 |
| Fachwissenstests | 0,40 |
| Arbeitsproben | 0,33 |
| Unstrukturierte Interviews | 0,19 |
| Jahre an Berufserfahrung | 0,07 |

Daraus folgen drei Lehren für die Einstellung von Entwicklern:

- **Struktur zählt mehr als das Format.** Dasselbe Interview mit festgelegten Fragen und einem Bewertungsleitfaden sagte die Leistung weit besser vorher als ein unstrukturiertes Gespräch.
- **Berufsjahre allein sagen wenig.** „Fünf Jahre Java“ ist ein schwaches Signal im Vergleich dazu, was jemand tatsächlich weiß und kann.
- **Kombiniere Methoden.** Keine einzelne Methode sagt gut genug vorher, um allein zu stehen.

Das sind Durchschnittswerte über viele Stellen und Studien hinweg, keine Garantien für deine Stelle. Die Autoren weisen außerdem darauf hin, dass Wissenstests und Arbeitsproben zu Stellen passen, bei denen von Kandidaten bereits Ausbildung oder Erfahrung erwartet wird. Das trifft auf die meisten Entwicklerstellen zu, aber nicht auf eine Ausbildungsstelle.

## Schritt 1: Ein klares Anforderungsprofil und eine Stellenbeschreibung schreiben

Bevor du etwas ausschreibst, halte fest, was die Person in ihren ersten sechs Monaten tun wird und was sie am ersten Tag wissen muss. Werde konkret:

- **Muss können:** „Schreibt und reviewt PostgreSQL-Abfragen, einschließlich Joins und Indizes“ ist testbar. „Gute Datenbankkenntnisse“ ist es nicht.
- **Lernt im Job:** eure internen Tools, eure Domäne, die Teile des Stacks, die ihr selbst vermittelt.
- **Level:** was in deinem Team eine Einstellung auf mittlerem Level von einer Senior-Einstellung unterscheidet, etwa die Verantwortung für einen Service von Anfang bis Ende oder das Leiten von Designentscheidungen.

Stimm das mit allen ab, die an der Einstellung beteiligt sind. Schreib dann daraus die Stellenbeschreibung. Eine Stellenbeschreibung, die der echten Arbeit entspricht, zieht die richtigen Menschen an und erleichtert die Einrichtung jedes späteren Schritts, weil sich jeder Test und jedes Interview auf sie zurückführen lässt.

Halte die „Wünschenswert“-Liste kurz. Lange Anforderungslisten schrecken qualifizierte Menschen ab, die nicht jeden Punkt abhaken können.

## Schritt 2: Lebensläufe nur auf harte Anforderungen prüfen

Nutze Lebenslauf oder Bewerbung für Ja-Nein-Prüfungen: Arbeitserlaubnis, Standort oder Zeitzone, falls die Stelle das verlangt, eine erforderliche Sprache und jedes Muss, ohne das die Stelle wirklich nicht auskommt.

Ordne Menschen nicht nach ihrem Lebenslauf. Jobtitel, Arbeitgebernamen und Berufsjahre sind schwache Prädiktoren, und Lebensläufe sind schwer fair zu vergleichen: Ein starker Lebenslauf kann ebenso gutes Schreiben widerspiegeln wie gute Arbeit. Behandle den Lebenslauf als Filter für das, was sich nicht testen lässt, und lass alle, die ihn passieren, zum Wissenstest weiter.

## Schritt 3: Einen kurzen Wissenstest durchführen

Dieser Schritt spart deinen Entwicklern die meiste Zeit. Bevor jemand eine Stunde in einem Live-Interview verbringt, prüfst du, was jeder Kandidat über deinen Stack weiß.

Ein guter Wissenstest ist:

- **Stellenspezifisch:** Er prüft die Sprachen, Frameworks, Datenbanken und Praktiken aus deinem Anforderungsprofil, kein allgemeines Trivia-Wissen.
- **Kurz:** einige Themen mit jeweils etwa 10 Fragen, damit auch starke Kandidaten mit anderen Angeboten ihn zu Ende bringen.
- **Für alle gleich:** dieselben Themen, dieselbe Anzahl Fragen und dieselben Zeitlimits.

Hier passt testee. Es macht aus deiner Stellenbeschreibung ein zeitlich begrenztes Multiple-Choice-Interview zum Fachwissen. Du prüfst die vorgeschlagenen Themen, bevor eine Frage geschrieben wird, sodass der Test deinen Stack abdeckt und nichts anderes. Für eine Entwicklerstelle kann das umfassen:

- **Fragen zum Lesen von Code:** ein kurzes Stück Code mit Fragen dazu, was es ausgibt oder zurückgibt, was es tut, warum es fehlschlägt oder welche Änderung es behebt.
- **SQL:** eine kleine Tabelle und eine Abfrage, mit der Frage, welche Zeilen zurückkommen.
- **Architektur- und Framework-Wissen:** Zielkonflikte, wie sich ein Framework verhält, was unter Last schiefgeht.

Jeder Kandidat erhält einen eigenen zufälligen Fragensatz mit einem Countdown bei jeder Frage. Du siehst eine Auswertung mit jeder Antwort und ihrer Dauer sowie Hinweisen auf zu schnelle Antworten, das Verlassen der Seite, Kopierversuche und ungewöhnliche Muster in den Antworten und Antwortzeiten. Ein Hinweis ist ein Grund, genauer hinzusehen, kein Beweis für irgendetwas. Der Bericht schlägt außerdem richtig beantwortete Fragen vor, nach denen du im nächsten Gespräch fragen kannst.

Was testee nicht tut: Kandidaten schreiben, starten oder debuggen in testee keinen Code. Code lesen und Code schreiben sind unterschiedliche Fähigkeiten, deshalb bleibt der nächste Schritt wichtig. Unter [Fachtests nach Stelle](/tests) findest du fertige Tests als Ausgangspunkt.

## Schritt 4: Take-Home-Aufgabe oder Live-Coding

Prüfe jetzt, ob Kandidaten funktionierenden Code schreiben können. In dieser Phase wird Code geschrieben, ausgeführt und debuggt, entweder mit deiner eigenen Übung oder auf einer Entwicklerplattform. Unter [Alternativen zu HackerRank](/compare/hackerrank-alternatives) siehst du, wie ein Wissenstest und eine Programmierplattform zusammenpassen.

Zwei verbreitete Formate:

- **Take-Home-Aufgabe:** realistisch und mit wenig Druck, kostet die Kandidaten aber ihre Abende. Begrenze sie auf höchstens ein paar Stunden, sag, wie lange sie dauern soll, und bewerte sie mit einem schriftlichen Bewertungsraster.
- **Live-Coding:** kürzer und schwerer auszulagern, aber stressiger. Arbeitet gemeinsam an einem realistischen Problem, lass Kandidaten die Sprache nutzen, die sie am besten beherrschen, und beurteile ihre Denkweise, nicht nur, ob sie fertig werden.

In beiden Fällen bewertest du anhand vorab vereinbarter Kriterien: Korrektheit, Lesbarkeit, Tests, Umgang mit Randfällen. Weil der Wissenstest die Gruppe bereits gefiltert hat, führst du diesen Schritt mit einer Handvoll Menschen statt mit allen durch.

## Schritt 5: Systemdesign für Senior-Stellen

Für erfahrene Entwickler ergänzt du ein Designgespräch: „Wie würdest du einen Service bauen, der X tut?“ Achte darauf, wie sie Anforderungen klären, zwischen Zielkonflikten abwägen und Schwachstellen erkennen. Es gibt selten die eine richtige Antwort, deshalb ist ein Bewertungsraster unverzichtbar. Halte vor dem ersten Interview fest, wie eine schwache, solide und starke Antwort aussieht.

Lass das bei Junior-Stellen weg; dort prüft es vor allem Selbstsicherheit statt Können.

## Schritt 6: Strukturierte Verhaltensinterviews mit Bewertungsraster

Strukturierte Interviews waren bei Sackett et al. (2022) der stärkste einzelne Prädiktor. Struktur bedeutet:

- **Dieselben Fragen für alle Kandidaten,** bezogen auf das Anforderungsprofil: „Erzähl von einer Situation, in der du mit einer Designentscheidung nicht einverstanden warst. Was hast du getan?“
- **Ein Bewertungsraster für jede Frage,** mit Beispielen für schwache, solide und starke Antworten.
- **Unabhängige Bewertungen:** Alle Interviewer bewerten, bevor sie sich mit anderen austauschen, damit nicht die lauteste Meinung das Ergebnis bestimmt.

Nutze diese Phase für das, was Tests nicht zeigen können: Zusammenarbeit, Verantwortungsübernahme, Umgang mit Feedback, Kommunikation mit Nicht-Technikern.

## Schritt 7: Referenzen einholen

Referenzen können bestätigen, was du erfahren hast, und Bedenken zutage fördern, aber behandle sie als letzte Prüfung, nicht als entscheidenden Test. Sackett et al. haben für Referenzen keine Validitätsschätzung vorgelegt, weil die verfügbare Forschung zu dünn war; es gibt also wenig Belege dafür, wie gut sie Leistung vorhersagen. Wenn du Referenzen einholst, stell allen Referenzgebern dieselben wenigen Fragen zu konkretem Verhalten.

## Schritt 8: Candidate Experience und Zeit bis zum Angebot

Starke Entwickler haben oft mehrere Bewerbungsprozesse gleichzeitig laufen. Ein langsamer oder unübersichtlicher Prozess verliert sie.

- **Erkläre Kandidaten den ganzen Prozess vorab:** die Phasen, wie lange jede dauert und wann sie eine Rückmeldung bekommen.
- **Halte ihn kurz.** Leg die späteren Phasen nah beieinander und entscheide bald nach dem letzten Interview.
- **Respektiere ihre Zeit.** Ein kurzer Wissenstest früh im Prozess bedeutet, dass weniger Menschen lange Interviews durchsitzen, die sie wahrscheinlich nicht bestanden hätten.
- **Gib allen zeitnah eine Antwort,** auch denen, mit denen du nicht weitermachst.

## Fairness im gesamten Prozess

Ein strukturierter Prozess ist auch ein fairerer, aber nur, wenn du ihn konsequent durchführst:

- **Einheitliche Fragen** in jeder Phase, für alle Kandidaten derselben Stelle.
- **Vorab geschriebene Bewertungsraster,** damit Menschen nach denselben Kriterien beurteilt werden.
- **Anpassungen:** Biete Kandidaten, die darum bitten, zusätzliche Zeit oder ein anderes Format an, zum Beispiel wegen einer Behinderung. In testee kannst du einem Kandidaten vor dem Start zusätzliche Zeit geben.
- **Ergebnisse beobachten.** Verschiedene Methoden zeigen unterschiedliche Punktunterschiede zwischen Gruppen. Sackett et al. fanden bei Fachwissenstests und Arbeitsproben im Durchschnitt größere Unterschiede als bei strukturierten Interviews; ein weiterer Grund, Methoden zu kombinieren. Beobachte die Bestehensquoten in jeder Phase.
- **Menschen entscheiden.** Eine Punktzahl stützt eine Entscheidung; sie trifft sie nicht. Sieh dir die Antworten an, bevor du jemandem absagst.

Die rechtlichen Grundlagen, einschließlich der KI-Verordnung der EU (AI Act) und der US-Regeln zu Auswahlquoten, findest du unter [Einstellungstests](/pre-employment-testing).

## Zusammenfassung

Stell die breiten, günstigen Prüfungen an den Anfang und die tiefen, teuren ans Ende. Prüf Lebensläufe auf harte Anforderungen, führ einen kurzen Wissenstest durch und investier die Zeit deiner Entwickler dann in Coding, Design und strukturierte Interviews mit den wenigen, die übrig sind. Bewerte anhand vorab geschriebener Bewertungsraster, und halte den Prozess schnell und klar.

## Quellen

- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection: Addressing systematic overcorrection for restriction of range. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Weiterlesen

- [Fachtests nach Stelle](/tests)
- [Alternativen zu HackerRank](/compare/hackerrank-alternatives)
- [Leitfaden zu Einstellungstests](/pre-employment-testing)
- [Fachtests vs. Lebenslauf-Screening](/guides/skills-tests-vs-cv-screening)
- [Entwickler interviewen im KI-Zeitalter](/guides/interviewing-in-the-age-of-ai)
