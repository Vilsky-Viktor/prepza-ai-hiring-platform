---
title: "So verbindest du Fachtests mit deinem ATS"
seoTitle: "Fachtests mit dem ATS verbinden: ein Praxisleitfaden"
description: "Fachtests automatisch über dein ATS versenden und Ergebnisse dort erhalten, Entscheidungen bei Menschen lassen und wissen, was du zuerst prüfen solltest."
updated: "2026-10-21"
---

# So verbindest du Fachtests mit deinem ATS

Die meisten Recruiting-Teams verwalten Kandidaten in einem Bewerbermanagementsystem (ATS) und führen Fachtests in einem anderen Tool durch. Ohne Verbindung zwischen beiden kopiert jemand E-Mail-Adressen aus dem ATS, verschickt Einladungen von Hand, wartet und überträgt dann die Ergebnisse zurück. Bei fünf Kandidaten geht das. Bei fünfzig gehen Einladungen zu spät raus, Ergebnisse liegen in einem zweiten Tab, den niemand öffnet, und gute Bewerber nehmen während des Wartens andere Angebote an.

Dieser Leitfaden erklärt, was eine gute Verbindung zwischen einem ATS und einem Testtool leistet, was du prüfen solltest, bevor du dich darauf verlässt, und wie du sie so einrichtest, dass die Automatisierung die Routinearbeit übernimmt und Menschen weiterhin jede Einstellungsentscheidung treffen.

## Warum überhaupt verbinden

| Ohne Verbindung | Mit Verbindung |
| --- | --- |
| Jemand exportiert oder kopiert E-Mail-Adressen von Kandidaten | Das Verschieben eines Kandidaten in eine Phase verschickt die Einladung |
| Einladungen gehen raus, wenn jemand Zeit hat | Einladungen gehen wenige Minuten nach dem Verschieben raus |
| Ergebnisse bleiben im Testtool | Ergebnisse erscheinen beim Kandidaten im ATS |
| Hiring Manager fragen: „Hat die schon jemand getestet?“ | Das ATS zeigt, wer getestet wurde und wie gut |
| Tippfehler in E-Mail-Adressen und übersehene Kandidaten | Das ATS ist die einzige Liste aller Bewerber |

Tempo ist wichtiger, als es scheint. Je länger es zwischen Bewerbung und Rückmeldung dauert, desto mehr Kandidaten springen ab oder nehmen eine andere Stelle an. Die genauen Abbruchquoten schwanken stark je nach Rolle und Markt, geh mit veröffentlichten Zahlen also vorsichtig um. Die Richtung ist aber eindeutig: Ein langsamer Prozess verliert Menschen, und die stärksten Bewerber haben meist die meisten Optionen.

## Wie ein guter Ablauf aussieht

Eine solide Integration folgt den Phasen, die du ohnehin nutzt. Sie erfindet keinen neuen Prozess.

1. **Ein Kandidat bewirbt sich** und landet wie gewohnt in deinem ATS.
2. **Ein Mensch verschiebt ihn in eine Testphase,** zum Beispiel „Fachtest“. Dieses Verschieben ist der Auslöser, also entscheidet weiterhin ein Mensch, wer getestet wird.
3. **Das Testtool verschickt die Einladung** automatisch, für den Test, der mit dieser Stelle verknüpft ist.
4. **Der Kandidat macht den Test,** wann es ihm passt, innerhalb der Frist, die du setzt.
5. **Die Ergebnisse werden beim Kandidaten im ATS eingetragen:** die Punktzahl, ob er bestanden hat, Hinweise zur Integrität und ein Link zu allen Antworten.
6. **Ein Mensch prüft das Ergebnis** und bringt den Kandidaten weiter, oder nicht.

Zwei Dinge bleiben bewusst manuell: auszuwählen, wer getestet wird, und zu entscheiden, wie es weitergeht. Die Verbindung nimmt dir nur das Kopieren dazwischen ab.

### Warum nicht bei jeder neuen Bewerbung auslösen?

Manche Tools laden jeden ein, der sich bewirbt. Das kann bei Stellen mit vielen Bewerbungen passen, bei denen alle denselben Test machen. Eine Phase, in die du Kandidaten verschiebst, lässt sich aber besser steuern: Du kannst Bewerber überspringen, die eine harte Anforderung klar nicht erfüllen (keine Arbeitserlaubnis, falscher Standort), und du testest nie jemanden, den du ohnehin abgelehnt hättest, und zahlst auch nicht dafür.

## Was du vor der Wahl einer Integration prüfen solltest

Nicht jedes „integriert sich mit deinem ATS“ bedeutet dasselbe. Stell diese Fragen, bevor du etwas verbindest.

| Frage | Warum sie wichtig ist | Eine gute Antwort |
| --- | --- | --- |
| Wie wird verbunden? | Geteilte Passwörter und Konten beim Anbieter sind schwer zu prüfen oder zu widerrufen | Ein API-Schlüssel oder Token, den dein Unternehmen erstellt und jederzeit löschen kann |
| Was darf der Schlüssel? | Ein Schlüssel mit vollem Zugriff ist ein Risiko, wenn er nach außen gelangt | Die geringsten Berechtigungen, die die Integration braucht, in der Dokumentation aufgeführt |
| Was löst eine Einladung aus? | Du musst genau wissen, wann Kandidaten eine E-Mail bekommen | Eine bestimmte Phase, die du pro Stelle wählst |
| Wo landen die Ergebnisse? | Ergebnisse, die niemand sieht, helfen nicht | Im Profil des Kandidaten, als Notiz oder Kommentar, den dein Team ohnehin liest |
| Was passiert, wenn eine Einladung fehlschlägt? | Keine Credits mehr, ein Tippfehler, ein pausiertes Konto: Kandidaten bleiben unbemerkt hängen | Jemand wird benachrichtigt, und der Kandidat kann erneut eingeladen werden |
| Kann ein Ereignis doppelt verarbeitet werden? | ATS senden Ereignisse erneut; ein Kandidat sollte nicht zwei Einladungen bekommen | Jeder Kandidat wird pro Test einmal eingeladen, egal wie oft das Ereignis ankommt |
| Wie werden eingehende Ereignisse geprüft? | An eine ungeprüfte Adresse lassen sich gefälschte Ereignisse schicken | Signierte Anfragen, die das Tool prüft |
| Wie lange werden Kandidatendaten gespeichert? | Datenschutzgesetze wie die DSGVO verlangen eine klare Speicherdauer | Eine genannte Frist und Löschung, wenn du die Stelle, den Test oder dein Konto löschst |
| Was kostet es? | Preise pro Nutzer können Automatisierung teuer machen | Kosten, die du pro getestetem Kandidaten vorhersagen kannst |

Wenn der Anbieter die Fragen zu Fehlern und Duplikaten nicht klar beantworten kann, rechne damit, es auf die harte Tour herauszufinden.

### Datenschutz

Wenn du zwei Systeme verbindest, wandern Kandidatendaten, mindestens Namen und E-Mail-Adressen, zwischen zwei Unternehmen. Nach der DSGVO und ähnlichen Gesetzen ist dein Testanbieter in der Regel dein Auftragsverarbeiter. Du brauchst also einen Auftragsverarbeitungsvertrag und solltest Kandidaten in deiner Datenschutzerklärung oder in der Einladung mitteilen, dass ein Fachtest Teil des Prozesses ist. Gib nur die Daten weiter, die der Test wirklich braucht. Mehr zur rechtlichen Seite von Tests und KI im Recruiting findest du unter [Ist KI im Recruiting in der EU erlaubt?](/guides/is-ai-hiring-legal-in-the-eu)

## Checkliste für die Einrichtung

Bevor du die Verbindung für eine echte Stelle einschaltest:

1. **Leg in deinem ATS eine eigene Phase nur für den Test an,** etwa „Fachtest“. Nutze keine Phase, die schon etwas anderes bedeutet, sonst werden Kandidaten versehentlich eingeladen.
2. **Erstelle den Schlüssel mit einem Admin-Konto,** das alle Stellen sieht, die du verknüpfen möchtest, und nur mit den Berechtigungen, die die Dokumentation nennt.
3. **Verknüpfe jede Stelle mit ihrem Test** und wähle die Phase, die die Einladung auslöst.
4. **Richte den Webhook ein,** falls dein ATS das von Hand verlangt, und füge sein Secret dort ein, wo das Tool danach fragt.
5. **Teste mit dir selbst.** Leg einen Kandidaten mit deiner eigenen E-Mail-Adresse an, verschieb ihn in die Phase, mach den Test und prüf, ob die Notiz im ATS erscheint.
6. **Leg fest, wer auf Fehler achtet:** wer benachrichtigt wird, wenn eine Einladung nicht verschickt werden kann, und wer sich darum kümmert.
7. **Einigt euch, wie Ergebnisse gelesen werden.** Eine Bestehensgrenze ist eine Orientierung, keine automatische Absage. Klärt das, bevor die Ergebnisse eintreffen, nicht danach.

## Häufige Fehler

- **Die Entscheidung automatisieren statt der Routinearbeit.** Wer alle unter einer Punktzahl automatisch ablehnt, verliert die menschliche Kontrolle, die eine schlechte Frage oder einen Kandidaten mit Verbindungsproblemen bemerkt. Die Punktzahl sortiert, ein Mensch entscheidet.
- **Aus der falschen Phase auslösen.** Eine Phase, die Recruiter auch aus anderen Gründen nutzen, schickt Tests an Menschen, die keine bekommen sollten.
- **Ein Test für jede Stelle.** Die Verbindung macht es leicht, überall denselben Test zu verschicken. Am meisten bringt ein Test, der für die jeweilige Stelle erstellt wurde. Siehe [Fachtests vs. Lebenslauf-Screening](/guides/skills-tests-vs-cv-screening).
- **Niemand achtet auf Fehler.** Schlägt eine Einladung unbemerkt fehl, wartet der Kandidat auf eine E-Mail, die nie kommt, und du glaubst, er habe sie ignoriert.
- **Ein Schlüssel, der an eine Person gebunden ist, die geht.** Manche ATS-Schlüssel handeln im Namen der Person, die sie erstellt hat. Wird deren Konto geschlossen, bricht die Verbindung ab. Nutze ein Konto, das bleibt, und verbinde neu, wenn Personen die Rolle wechseln.
- **Kandidaten außerhalb des ATS vergessen.** Empfehlungen und Direktbewerbungen, die nie ins ATS gelangen, brauchen trotzdem eine Einladung. Behalte auch einen manuellen Weg, sie einzuladen.

## So macht es prepza

prepza verbindet sich mit **Workable, Greenhouse, Teamtailor, Recruitee und Breezy HR** und folgt dem oben beschriebenen Ablauf.

- **Dein Schlüssel, deine Kontrolle.** Ein Inhaber oder Admin verbindet das ATS im Tab Integrationen des Unternehmens mit einem Schlüssel, den dein Unternehmen im ATS erstellt. prepza prüft ihn vor dem Speichern, speichert ihn verschlüsselt und zeigt ihn nie wieder an. Beim Trennen werden der Schlüssel und die verknüpften Stellen sofort gelöscht.
- **Eine Stelle mit einem Interview verknüpfen.** Wähle eine Stelle im ATS und die Phase, die die Einladung auslöst, und verknüpfe sie mit einem bestehenden prepza-Interview oder erstelle ein neues aus dem Text der Stelle im ATS. Du prüfst die Themen, bevor eine einzige Frage geschrieben wird.
- **Kandidat verschieben, Einladung geht raus.** Jeder Kandidat wird pro Interview einmal eingeladen, auch wenn das ATS dasselbe Ereignis zweimal sendet.
- **Ergebnisse zurück im ATS.** Wenn ein Kandidat fertig ist, fügt prepza ihm im ATS eine Notiz oder einen Kommentar hinzu, mit seinem Ergebnis, ob er bestanden hat, Hinweisen zur Integrität (Verlassen der Seite, Kopierversuche, Antworten, die zu schnell gewählt wurden, um die Frage gelesen zu haben) und einem Link zu seiner Auswertung mit allen Antworten.
- **Fehler bleiben nicht unbemerkt.** Kann ein Kandidat nicht eingeladen werden, etwa weil das Unternehmen keine Credits mehr hat, ein E-Mail-Limit erreicht hat oder weil prepza Einladungen vorübergehend pausiert hat, erhalten alle Mitglieder des Unternehmens eine Benachrichtigung mit dem Namen des ATS. Kandidaten, die mangels Credits nicht eingeladen wurden, werden nach einer Aufladung automatisch eingeladen, und die wartenden Kandidaten jeder Stelle lassen sich mit einem Klick erneut einladen.
- **Slack, wenn du es nutzt.** prepza kann Benachrichtigungen, etwa über einen Kandidaten, der fertig ist, oder einen ATS-Kandidaten, der nicht eingeladen werden konnte, in einem Slack-Kanal deiner Wahl posten.
- **Deine eigene Plattform.** Steht dein ATS nicht auf der Liste, kannst du über die [API](/api-docs) von prepza Kandidaten mit einem API-Schlüssel einladen und einen signierten Webhook erhalten, wenn ein Kandidat beginnt, fertig ist, seine Einladung nicht zugestellt werden kann oder abläuft oder er entfernt wird, und wenn ein Interview bereit ist.
- **Daten für eine feste Zeit gespeichert.** Aus einem ATS übernommene Kandidaten werden nach 365 Tagen gelöscht, oder früher zusammen mit ihrem Interview oder Unternehmen.

Manche ATS brauchen einen Schritt auf ihrer Seite. Bei Greenhouse, Teamtailor und Recruitee fügst du einen Webhook von Hand hinzu; der Dialog Anleitung in prepza zeigt die Adresse und wo du das Secret einfügst. Die Webhooks von Workable und Breezy HR richtet prepza selbst ein.

Abgerechnet wird pro Kandidat, ohne Abo: Du zahlst nur für Kandidaten, die mindestens eine Frage beantworten, 5 $ pro Kandidat bei der Aufladung über 50 $, 4 $ ab einer Aufladung von 200 $, 3 $ ab einer Aufladung von 600 $ und 2 $ ab einer Aufladung von 1.000 $. Die Preise sind in US-Dollar angegeben, in Europa in Euro (mit denselben Beträgen) und im Vereinigten Königreich in Pfund (4 £ bis 1,50 £); Mehrwertsteuer oder Sales Tax werden beim Bezahlen berechnet. Ein ATS zu verbinden und Interviews zu erstellen ist kostenlos, und die ersten 3 Kandidaten deines ersten Unternehmens sind kostenlos. Siehe [Preise](/pricing).

## Weiterlesen

- [So sichtest du 100 Bewerbungen an einem Tag](/guides/screen-100-applicants-in-a-day)
- [Fachtests vs. Lebenslauf-Screening](/guides/skills-tests-vs-cv-screening)
- [Einstellungstests: ein Praxisleitfaden](/pre-employment-testing)
