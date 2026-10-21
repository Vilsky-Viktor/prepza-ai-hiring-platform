# The FAQ in de; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Was ist prepza?",
        "answer": "Ein Interview mit Zeitlimit, erstellt aus deiner Stellenbeschreibung, für jede Rolle. Nutze es, um Kandidaten zu prüfen, bevor du sie triffst, oder als eigenen Schritt im Einstellungsprozess: So oder so siehst du, wer den Job wirklich beherrscht.",
    },
    {
        "key": "roles",
        "question": "Für welche Rollen kann ich einstellen?",
        "answer": "Für jede Rolle, in der Wissen zählt: Support, Vertrieb, Finanzen, Gesundheitswesen, Handwerk, Technik, Marketing und mehr. Wenn du den Job beschreiben kannst, kann prepza ein Interview dafür erstellen.",
    },
    {
        "key": "hiring",
        "question": "Wie funktioniert es?",
        "answer": "Füge auf der Startseite eine Stellenbeschreibung ein, gib den Namen deines Unternehmens an und prüfe die Themen, die prepza vorschlägt. Dann lade Kandidaten ein: Tippe ihre E-Mail-Adressen ein, füge eine Liste ein oder lade eine Datei hoch. Kandidaten, die nach ein paar Tagen noch nicht angefangen haben, bekommen eine Erinnerung. Jeder Kandidat bekommt eigene Fragen mit einem Zeitlimit für jede, und du siehst sein Ergebnis und jede Antwort, sobald er fertig ist.",
    },
    {
        "key": "link",
        "question": "Kann ich ein Interview in eine Stellenanzeige setzen?",
        "answer": "Ja. Schalte den Link zum Teilen des Interviews im Tab Kandidaten ein und füge ihn in deine Anzeige ein. Jeder, der ihn öffnet, meldet sich an und macht das Interview, und jede Person wird wie ein eingeladener Kandidat berechnet. Der Link wird abgeschaltet, wenn du das Interview als eingestellt markierst.",
    },
    {
        "key": "preview",
        "question": "Kann ich ein Interview ausprobieren, bevor ich jemanden einlade?",
        "answer": "Ja. Öffne dein Interview über seine Seite als Kandidat, kostenlos: Vorschauen erscheinen weder bei deinen Kandidaten noch in der Fragenstatistik. Du kannst auch jedes der kostenlosen Übungsinterviews machen.",
    },
    {
        "key": "cheating",
        "question": "Können Kandidaten KI nutzen oder die Antworten nachschlagen?",
        "answer": "Jeder Kandidat bekommt eigene, zufällige Fragen in eigener Reihenfolge, mit [einem Zeitlimit für jede Frage](/guides/skills-test-timing-and-extra-time), das unser Server überwacht, also bleibt wenig Zeit, Antworten nachzuschlagen oder eine KI zu fragen. Die Auswertung zeigt außerdem, wann ein Kandidat die Seite verlassen, Text kopiert oder zu schnell geantwortet hat, um die Frage gelesen zu haben.",
    },
    {
        "key": "cost",
        "question": "Was kostet es?",
        "answer": "Interviews zu generieren ist kostenlos. Jeder Kandidat, der mindestens eine Frage beantwortet, kostet {candidate} Credits ({candidate_price}), mit Credits aus größeren Aufladungen weniger, bis hinunter auf {cheapest_price}. Dein erstes Unternehmen bekommt {company} kostenlose Credits, genug für seine ersten {company_candidates} Kandidaten. Auf der [Preisseite](/pricing) stehen alle Preise.",
    },
    {
        "key": "charged",
        "question": "Wann wird ein Kandidat berechnet?",
        "answer": "Sobald er mindestens eine Frage beantwortet hat: wenn sein Interview endet (er beendet es, oder die Zeit läuft ab, während er weg ist), oder wenn du ihn widerrufst. Eine Frage, deren Zeit ohne gewählte Antwort abgelaufen ist, zählt nicht. Seine Credits werden bei der Einladung zurückgelegt und kommen zurück, wenn du ihn widerrufst, bevor er etwas beantwortet, wenn er nie anfängt oder wenn sein Interview endet, ohne dass er etwas beantwortet hat.",
    },
    {
        "key": "compare_hiring",
        "question": "Wie ist der Preis im Vergleich zu anderen Bewertungstools?",
        "answer": "Viele Tools für Eignungstests werden als Monats- oder Jahresabo verkauft, das du zahlst, auch wenn du niemanden testest. Bei prepza zahlst du nur pro Kandidat: {candidate} Credits ({candidate_price}), ohne Vertrag, ohne Gebühren pro Nutzer und ohne Kosten für das Generieren eines Interviews. Ein Unternehmen, das {example_candidates} Kandidaten im Monat einlädt, zahlt etwa {example_year_price} im Jahr. Wenn du jeden Monat viele Kandidaten testest, kann ein Abo günstiger sein, also vergleiche mit deinen eigenen Zahlen.",
    },
    {
        "key": "expire",
        "question": "Verfallen Credits?",
        "answer": "Nein. Credits verfallen nie, und es gibt keine kostenpflichtigen Abos. Wenn du das optionale automatische Aufladen einschaltest, speichert Paddle deine Karte als Abo für {zero_price}; du zahlst nur die Aufladungen, die es vornimmt.",
    },
    {
        "key": "refunds",
        "question": "Kann ich mein Geld zurückbekommen?",
        "answer": "Ja, für Credits, die du in den letzten 14 Tagen gekauft und noch nicht ausgegeben hast: über Paddle oder indem du uns schreibst. Gratis-Credits wie das Willkommensgeschenk werden nicht erstattet. Details stehen in den [Bedingungen](/terms).",
    },
    {
        "key": "scorecards",
        "question": "Was zeigen die Auswertungen?",
        "answer": "Jede Antwort, ob sie richtig war und wie lange sie gedauert hat. Das Ergebnis ist der Anteil der erreichten Punkte: Jede Frage zählt einen Punkt, und eine Frage mit Mehrfachauswahl bringt einen Teil davon für jede angekreuzte richtige Option, aber nichts, wenn eine falsche angekreuzt ist. Ergebnisse erscheinen grün oder rot, gemessen an der Bestehensgrenze, die du für das Interview festgelegt hast. Außerdem markieren die Auswertungen Antworten, die zu schnell waren, um die Frage gelesen zu haben, wann der Kandidat die Seite verlassen hat und Kopierversuche.",
    },
    {
        "key": "reports",
        "question": "Kann ich Ergebnisse mit einem Hiring Manager teilen?",
        "answer": "Ja. Lade einen PDF-Bericht für einen Kandidaten oder für alle Kandidaten eines Interviews herunter, sende ihn direkt aus prepza per E-Mail oder schick eine kurze Zusammenfassung über WhatsApp, Telegram, Viber oder LINE.",
    },
    {
        "key": "action_log",
        "question": "Kann ich sehen, wer in meinem Unternehmen was gemacht hat?",
        "answer": "Ja, wenn du Inhaber des Unternehmens bist. Sein Tab Aktionsprotokoll listet alles, was seine Mitglieder getan haben, das Neueste zuerst: Kandidaten einladen oder entfernen, Ergebnisse ansehen und Interviews, das Team, die Abrechnung und Integrationen ändern, jeweils damit, wer es getan hat, wann und ob der Assistent, eine KI-App oder die API es in seinem Namen getan hat. Du kannst es nach Mitglied, Art der Aktion und Datum filtern. Aktionen werden 12 Monate lang aufbewahrt.",
    },
    {
        "key": "integrations",
        "question": "Funktioniert prepza mit meinem ATS oder anderen Tools?",
        "answer": "Ja, ohne Aufpreis. Verbinde Workable, Greenhouse, Teamtailor, Recruitee oder Breezy HR im Tab Integrationen deines Unternehmens: Kandidaten, die du in eine Phase verschiebst, bekommen das Interview, und ihre Ergebnisse gehen zurück an das ATS ([so verbindest du Fachtests mit deinem ATS](/guides/ats-integration-skills-tests)). Slack kann die Benachrichtigungen deines Unternehmens in einem Kanal posten, und über die API kann deine eigene Plattform Interviews erstellen, Kandidaten einladen und verwalten und ihre Ergebnisse empfangen, wobei jeder API-Schlüssel nur darf, was du für ihn ankreuzt; siehe [API-Dokumentation](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Kann ich prepza aus Claude, ChatGPT oder meinem eigenen KI-Agenten heraus nutzen?",
        "answer": "Ja. Füge prepza in Claude oder ChatGPT als Connector hinzu (die Schritte stehen im Tab Integrationen deines Unternehmens) und lass es in prepza zu. Die App arbeitet dann in deinem Namen und mit deinen Berechtigungen mit deinen Unternehmen, Interviews und den Ergebnissen der Kandidaten; die meisten Apps fragen dich, bevor sie etwas ändern. Dein Konto oder ein Unternehmen löschst du nur in prepza. Was die App liest, geht nach den Bedingungen dieser App an ihren Anbieter. Du kannst sie jederzeit im selben Tab trennen. Auch andere KI-Apps und selbst gebaute Agenten lassen sich verbinden: Im [MCP-Tab](/api-docs?tab=mcp) der Entwicklerdokumentation stehen die Schritte und Beispiel-Agenten, und ein Agent auf einem Server kann sich mit einem API-Schlüssel anmelden, der die Berechtigung für KI-Agenten hat. Der [Leitfaden zu KI-Agenten, MCP und APIs](/guides/ai-agents-mcp-and-api) erklärt, wofür jedes davon gedacht ist.",
    },
    {
        "key": "candidates",
        "question": "Was sehen Kandidaten?",
        "answer": "Den Namen und das Logo deines Unternehmens, in den Farben und der Schriftart deines Unternehmens (festgelegt im Tab Marke), vor dem Start, was sie erwartet, dann jeweils eine Frage mit Zeitlimit. Sie sehen nie ihr Ergebnis oder ob eine Antwort richtig war.",
    },
    {
        "key": "verified",
        "question": "Was bedeutet das Verifiziert-Häkchen?",
        "answer": "Dass sich ein Inhaber oder Admin des Unternehmens mit einer geschäftlichen E-Mail-Adresse auf der Domain des Unternehmens angemeldet hat, etwa du@acme.com, und unser Team das Unternehmen danach geprüft hat. Füge die Website über Verifizieren im Kopfbereich deines Unternehmens hinzu; kostenlose E-Mail-Dienste zählen nicht. Solange die Prüfung aussteht, sieht dein Team eine Uhr neben dem Namen, und eine Umbenennung schickt das Unternehmen erneut zur Prüfung. Das Häkchen erscheint neben dem Namen deines Unternehmens, auch in Einladungen.",
    },
    {
        "key": "languages",
        "question": "Welche Sprachen werden unterstützt?",
        "answer": "{count} Sprachen, für die Website, die Interviews und die E-Mails. Wähle die Sprache, in der ein Interview geschrieben wird, egal in welcher Sprache die Stellenbeschreibung ist.",
    },
    {
        "key": "privacy",
        "question": "Was passiert mit Stellenbeschreibungen und Antworten?",
        "answer": "Stellenbeschreibungen werden genutzt, um die Interviews deines Unternehmens zu erstellen, und die Antworten der Kandidaten, um sie für dein Unternehmen zu bewerten. Die Fragen, die prepza generiert, können außerdem in Interviews und Übungsinterviews anderer Unternehmen wiederverwendet werden, ohne etwas, das dich, dein Unternehmen oder andere Personen identifiziert; du kannst die Fragen eines Interviews in dessen Einstellungen davon ausnehmen. Zudem leitet prepza daraus, wie Fragen beantwortet werden, allgemeine, anonymisierte Muster der Fragenqualität ab, um die Generierung von Fragen zu verbessern. Die [Datenschutzerklärung](/privacy) erklärt, was wir speichern, wie lange und welche Rechte alle haben.",
    },
    {
        "key": "eu_ai_law",
        "question": "Darf man in der EU KI für die Vorauswahl von Kandidaten nutzen?",
        "answer": "Ja, mit Regeln. Nach der KI-Verordnung der EU (AI Act) gelten Tools, die Kandidaten bewerten, sehr wahrscheinlich als Hochrisiko-Systeme, mit Pflichten ab dem 2. Dezember 2027, und die DSGVO gilt schon heute: Ein Mensch trifft die Einstellungsentscheidung, Kandidaten erfahren, dass KI eingesetzt wird, und alles wird dokumentiert. prepza arbeitet genau so: KI schreibt die Fragen, Menschen in deinem Unternehmen prüfen die Ergebnisse und entscheiden, und Kandidaten werden informiert, bevor sie beginnen. Das ist keine Rechtsberatung; [Ist KI im Recruiting in der EU erlaubt?](/guides/is-ai-hiring-legal-in-the-eu) erklärt die Regeln und Fristen.",
    },
    {
        "key": "emails",
        "question": "Welche E-Mails sendet prepza und wie stelle ich sie ab?",
        "answer": "Service-E-Mails wie Einladungen, Berichte, Zahlungsprobleme und Änderungen unserer Bedingungen werden immer gesendet. Alles andere, etwa die tägliche Aktivitätsübersicht, Erinnerungen und Produkt-Updates, wählst du in den Einstellungen unter E-Mails oder stellst es mit dem Link „Abmelden“ in jeder E-Mail ab. Kandidaten können die E-Mails deines Unternehmens oder die Erinnerungen zu einem Interview mit den Links in ihren Einladungen und Erinnerungen abstellen. Neuigkeiten von prepza erscheinen in deinen Benachrichtigungen, der Glocke oben; die wichtigsten kommen außerdem als Produkt-Update per E-Mail, aber nur, solange diese Einstellung an ist.",
    },
    {
        "key": "delete",
        "question": "Kann ich mein Konto löschen?",
        "answer": "Ja, in den Einstellungen. Dein Konto und deine Daten werden gelöscht, und vorher kannst du eine Kopie deiner Daten herunterladen.",
    },
    {
        "key": "report",
        "question": "Wie melde ich ein Problem?",
        "answer": "Schreib uns über die [Kontaktseite](/contact) und füge die ID dessen ein, worum es geht: „id kopieren“ steht unter dem Namen eines Unternehmens, eines Interviews oder eines Kandidaten, die ID deines Kontos im Kontomenü und in den Einstellungen. Mit der ID finden wir es sofort.",
    },
]
