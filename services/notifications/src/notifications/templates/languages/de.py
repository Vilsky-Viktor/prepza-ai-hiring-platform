# Email texts in German. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Diese E-Mail wurde an {email} gesendet, weil du Inhaber oder Admin eines Unternehmens "
    "auf prepza bist."
)

TEXTS = {
    "candidate": {
        "subject": "Interview-Einladung von {company}",
        "preheader": "Absolviere „{title}“ auf prepza. Melde dich mit {email} an, um zu beginnen.",
        "heading": "Einladung zum Interview",
        "lines": [
            "{company} lädt dich zum Interview „{title}“ auf prepza ein.",
            (
                "Melde dich mit {email} an, um zu beginnen. Nur diese Adresse "
                "kann das Interview absolvieren, und du hast einen Versuch."
            ),
        ],
        "button": "Einladung öffnen",
    },
    "joined": {
        "subject": "Dein Link zu „{title}“",
        "preheader": (
            "Wenn du das Interview verlässt, mach mit diesem Link weiter. Melde dich mit {email} "
            "an."
        ),
        "heading": "Dein Link zum Interview",
        "lines": [
            "Du hast das Interview „{title}“ von {company} auf prepza begonnen.",
            (
                "Wenn du es verlässt, mach mit diesem Link weiter: Melde dich mit {email} an. "
                "Er funktioniert auch dann, wenn {company} den Link deaktiviert, über den du "
                "begonnen hast. Die Zeit läuft weiter, während du weg bist."
            ),
        ],
        "button": "Interview fortsetzen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil mit dieser Adresse ein Interview auf "
            "prepza begonnen wurde."
        ),
    },
    "reminder": {
        "subject": "Erinnerung: dein Interview bei {company}",
        "preheader": "„{title}“ ist noch offen. Melde dich mit {email} an, um zu beginnen.",
        "heading": "Dein Interview wartet",
        "lines": [
            (
                "{company} hat dich vor einigen Tagen zum Interview „{title}“ auf "
                "prepza eingeladen, und du hast es noch nicht begonnen."
            ),
            (
                "Melde dich mit {email} an, um zu beginnen. Nur diese Adresse kann das "
                "Interview absolvieren, und du hast einen Versuch. Die Einladung läuft 30 Tage "
                "nach dem Versand ab."
            ),
        ],
        "button": "Einladung öffnen",
    },
    "member": {
        "subject": "Tritt {company} auf prepza bei",
        "preheader": (
            "Tritt dem Team von {company} als {role} bei. Melde dich mit {email} an, um die "
            "Einladung anzunehmen."
        ),
        "heading": "Einladung ins Team",
        "lines": [
            "{inviter} lädt dich ein, dem Team von {company} auf prepza als {role} beizutreten.",
            (
                "Melde dich mit {email} an, um die Einladung anzunehmen. Nur diese Adresse kann "
                "die Einladung annehmen."
            ),
        ],
        "button": "Einladung öffnen",
        # The role's name as the lines use it.
        "roles": {"admin": "Admin", "viewer": "Betrachter"},
    },
    "report": {
        "subject": "Bericht: {candidate}",
        "preheader": "{candidate} hat „{title}“ bei {company} absolviert. Der Bericht ist angehängt.",
        "heading": "Kandidatenbericht",
        "lines": [
            "{sender} von {company} hat den Bericht von {candidate} zum Interview „{title}“ geteilt.",
            (
                "Er ist als einseitiges PDF angehängt: das Gesamtergebnis, das Ergebnis jedes Themas "
                "und was der Browser des Kandidaten gezeigt hat. Antworte auf diese E-Mail, "
                "um {sender} zu antworten."
            ),
        ],
        "button": "prepza besuchen",
        "footer": "Diese E-Mail wurde an {email} gesendet, weil {sender} einen Kandidatenbericht "
        "mit dieser Adresse auf prepza geteilt hat. Wenn du sie nicht erwartet hast, kannst "
        "du sie ignorieren.",
    },
    "candidates": {
        "subject": "Alle Kandidaten: {title}",
        "preheader": "Alle Kandidaten für „{title}“ bei {company}. Der Bericht ist angehängt.",
        "heading": "Kandidatenbericht",
        "lines": [
            "{sender} von {company} hat den Bericht aller Kandidaten zum Interview „{title}“ geteilt.",
            (
                "Er ist als PDF angehängt: Ergebnis, Fortschritt und was der Browser jedes Kandidaten "
                "gezeigt hat, die Besten zuerst. Antworte auf diese E-Mail, um {sender} zu "
                "antworten."
            ),
        ],
        "button": "prepza besuchen",
        "footer": "Diese E-Mail wurde an {email} gesendet, weil {sender} einen Kandidatenbericht "
        "mit dieser Adresse auf prepza geteilt hat. Wenn du sie nicht erwartet hast, kannst "
        "du sie ignorieren.",
    },
    "digest": {
        "subject": "Deine Aktivitätsübersicht auf prepza",
        "preheader": "Was in den letzten 24 Stunden in deinen Unternehmen passiert ist.",
        "heading": "Deine Aktivitätsübersicht",
        "lines": [
            "Das ist in den letzten 24 Stunden in deinen Unternehmen auf prepza passiert.",
        ],
        "rows": {
            "candidate_finished": "Kandidaten, die fertig sind: {count} · „{title}“",
            "invite_undelivered": "Nicht zugestellte Einladungen: {count} · „{title}“",
            "ats_not_invited": "Nicht eingeladene Kandidaten aus {ats}: {count}",
            "interview_ready": "Interview fertig: „{title}“",
            "note_added": "Neue Notizen deines Teams: {count} · „{title}“",
            "note": "{author}: „{excerpt}“",
            "note_by_former": "Ehemaliges Mitglied: „{excerpt}“",
        },
        "button": "prepza öffnen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Mitglied eines Unternehmens "
            "auf prepza bist und seine Aktivitätsübersicht erhältst."
        ),
    },
    "low_credits": {
        "subject": "Deine Credits werden knapp",
        "preheader": "Lade auf, um weiter Kandidaten einzuladen.",
        "heading": "Credits werden knapp",
        "lines": [
            (
                "Diese Unternehmen haben nicht genug Credits, um einen weiteren Kandidaten "
                "einzuladen. Lade auf, um weiter Kandidaten einzuladen."
            ),
        ],
        "rows": {
            "company": "{company} · verfügbare Credits: {available}",
        },
        "button": "Aufladen",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Warten auf Kandidaten",
        "preheader": "Lade Kandidaten per E-Mail ein oder teile den Link des Interviews.",
        "heading": "Warten auf Kandidaten",
        "lines": [
            (
                "Diese Interviews sind seit ein paar Tagen fertig, aber noch niemand wurde "
                "eingeladen. Lade Kandidaten per E-Mail ein oder teile den Link des "
                "Interviews."
            ),
        ],
        "rows": {
            "interview": "„{title}“ · {company}",
        },
        "button": "Kandidaten einladen",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Deine Themen warten auf deine Prüfung",
        "preheader": "Bestätige die Themen, dann werden die Fragen erstellt.",
        "heading": "Prüfe deine Themen",
        "lines": [
            (
                "Die Themen der Interviews, die du begonnen hast, warten auf deine Prüfung."
                " Sobald du sie bestätigst, werden die Fragen erstellt. Eine Prüfung, die "
                "14 Tage offen bleibt, wird abgebrochen."
            ),
        ],
        "rows": {
            "interview": "{company} · Wartezeit in Tagen: {days}",
        },
        "button": "Themen prüfen",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Neue Nutzungsbedingungen ab {date}",
        "preheader": "Die neuen Nutzungsbedingungen gelten ab {date}.",
        "heading": "Wir aktualisieren unsere Nutzungsbedingungen",
        "lines": [
            (
                "Wir haben eine neue Fassung der Nutzungsbedingungen von prepza veröffentlicht. "
                "Sie gilt ab {date}; bis dahin gelten die aktuellen Nutzungsbedingungen."
            ),
            (
                "Wenn du prepza ab {date} weiter nutzt, akzeptierst du die neuen "
                "Nutzungsbedingungen. Wenn nicht, kannst du dein Konto vorher in den "
                "Einstellungen löschen."
            ),
        ],
        "button": "Neue Nutzungsbedingungen lesen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du ein prepza-Konto hast. Sie ist "
            "ein Hinweis zu unseren Nutzungsbedingungen und wird daher unabhängig von deinen "
            "E-Mail-Einstellungen gesendet."
        ),
    },
    "legal_privacy": {
        "subject": "Neue Datenschutzerklärung ab {date}",
        "preheader": "Die neue Datenschutzerklärung gilt ab {date}.",
        "heading": "Wir aktualisieren unsere Datenschutzerklärung",
        "lines": [
            (
                "Wir haben eine neue Fassung der Datenschutzerklärung von prepza veröffentlicht, "
                "die beschreibt, wie wir deine Daten verwenden. Sie gilt ab {date}; bis dahin "
                "gilt die aktuelle Fassung."
            ),
            "Du kannst deine Daten jederzeit in den Einstellungen herunterladen oder löschen.",
        ],
        "button": "Neue Datenschutzerklärung lesen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du ein prepza-Konto hast. Sie ist "
            "ein Hinweis dazu, wie wir deine Daten verwenden, und wird daher unabhängig von "
            "deinen E-Mail-Einstellungen gesendet."
        ),
    },
    "legal_dpa": {
        "subject": "Neuer Auftragsverarbeitungsvertrag ab {date}",
        "preheader": "Der neue Vertrag gilt für dein Unternehmen ab {date}.",
        "heading": "Wir aktualisieren unseren Auftragsverarbeitungsvertrag",
        "lines": [
            (
                "Wir haben eine neue Fassung des Auftragsverarbeitungsvertrags veröffentlicht, "
                "nach dem prepza die Daten deiner Kandidaten verarbeitet. Sie gilt ab {date}; bis "
                "dahin gilt die aktuelle Fassung."
            ),
            (
                "Widerspricht ein Unternehmen aus berechtigten Gründen des Datenschutzes, kann es "
                "die Nutzung von prepza vorher beenden und sein Unternehmen in prepza löschen."
            ),
        ],
        "button": "Neuen Vertrag lesen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Inhaber oder Admin eines "
            "Unternehmens auf prepza bist. Sie ist ein Hinweis zu unserem Vertrag mit deinem "
            "Unternehmen und wird daher unabhängig von deinen E-Mail-Einstellungen gesendet."
        ),
    },
    # Campaigns (services/campaign_sends.py), named after the setting they need: a superadmin's
    # subject and text, and its button's text, or "open_site" when it has none.
    "updates": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "prepza öffnen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Produkt-Updates und Neuigkeiten von"
            " prepza erhalten möchtest."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "prepza öffnen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Angebote und Aktionen von prepza"
            " erhalten möchtest."
        ),
    },
    # An important notice: a service email about prepza itself (a security incident, planned
    # downtime, a change to how it works), whatever the email settings; never a promotion.
    "notices": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "prepza öffnen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du ein prepza-Konto hast. Sie ist ein"
            " wichtiger Hinweis zum Dienst, etwa zu seiner Sicherheit oder Verfügbarkeit, und"
            " wird daher unabhängig von deinen E-Mail-Einstellungen gesendet."
        ),
    },
    "top_up_failed": {
        "subject": "Aufladen fehlgeschlagen: {company}",
        "preheader": (
            "Die Karte konnte nicht belastet werden. Lade auf, um weiter Kandidaten einzuladen."
        ),
        "heading": "Automatisches Aufladen fehlgeschlagen",
        "lines": [
            (
                "Automatisches Aufladen konnte die Karte für {company} nicht belasten, "
                "daher wurden keine Credits hinzugefügt."
            ),
            (
                "Lade auf, um weiter Kandidaten einzuladen. Automatisches Aufladen versucht"
                " es später erneut mit der Karte."
            ),
        ],
        "button": "Aufladen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Inhaber oder Admin von "
            "{company} auf prepza bist. Sie betrifft die Abrechnung deines Unternehmens und"
            " wird daher unabhängig von deinen E-Mail-Einstellungen gesendet."
        ),
    },
    "top_up_paused": {
        "subject": "Aufladen pausiert: {company}",
        "preheader": (
            "Die Karte wurde abgelehnt. Aktualisiere sie, um das automatische Aufladen wieder "
            "einzuschalten."
        ),
        "heading": "Automatisches Aufladen ist pausiert",
        "lines": [
            (
                "Die Karte für das automatische Aufladen von {company} wurde abgelehnt, und ein "
                "erneuter Versuch hilft nicht. Deshalb ist das automatische Aufladen pausiert und "
                "belastet die Karte nicht."
            ),
            (
                "Aktualisiere die Karte auf der Abrechnungsseite, um das automatische Aufladen "
                "wieder einzuschalten. Lade bis dahin von Hand auf, um weiter Kandidaten "
                "einzuladen."
            ),
        ],
        "button": "Karte aktualisieren",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Inhaber oder Admin von "
            "{company} auf prepza bist. Sie betrifft die Abrechnung deines Unternehmens und"
            " wird daher unabhängig von deinen E-Mail-Einstellungen gesendet."
        ),
    },
    "top_up_on": {
        "subject": "Automatisches Aufladen ist an: {company}",
        "preheader": (
            "{price} zzgl. Steuern jedes Mal, wenn das verfügbare Guthaben unter {threshold, "
            "plural, one {# Credit} other {# Credits}} fällt."
        ),
        "heading": "Automatisches Aufladen ist an",
        "lines": [
            (
                "Automatisches Aufladen ist jetzt für {company} eingeschaltet. Jedes Mal, wenn "
                "das verfügbare Guthaben unter {threshold, plural, one {# Credit} other {# "
                "Credits}} fällt, wird die gespeicherte Karte mit {price} belastet, zuzüglich "
                "MwSt. oder Sales Tax, wo sie anfällt, bis das automatische Aufladen "
                "ausgeschaltet wird."
            ),
            (
                "Jede Belastung wird den Inhabern und Admins des Unternehmens per E-Mail "
                "mitgeteilt, und Paddle, unser Wiederverkäufer, schickt seine Quittung per "
                "E-Mail."
            ),
            (
                "Um es auszuschalten, öffne das automatische Aufladen auf der Abrechnungsseite "
                "und wähle „Ausschalten“. Das gilt sofort, und es wird nichts mehr abgebucht."
            ),
        ],
        "button": "Abrechnung öffnen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Inhaber oder Admin von {company} "
            "auf prepza bist. Sie betrifft die Abrechnung deines Unternehmens und wird daher "
            "unabhängig von deinen E-Mail-Einstellungen gesendet."
        ),
    },
    "top_up_charged": {
        "subject": "Automatisches Aufladen abgebucht: {company}",
        "preheader": "{price} für {credits, plural, one {# Credit} other {# Credits}} am {date}.",
        "heading": "Automatisches Aufladen hat die Karte belastet",
        "lines": [
            (
                "Am {date} hat das automatische Aufladen die Karte für {company} mit {price} "
                "inklusive Steuern belastet und {credits, plural, one {# Credit} other {# "
                "Credits}} hinzugefügt. {company} hat jetzt {available, plural, one {# Credit} "
                "other {# Credits}} verfügbar."
            ),
            "Paddle, unser Wiederverkäufer, schickt die Quittung per E-Mail.",
            (
                "Um diese Belastungen zu beenden, öffne das automatische Aufladen auf der "
                "Abrechnungsseite und wähle „Ausschalten“. Das gilt sofort, und es wird nichts "
                "mehr abgebucht."
            ),
        ],
        "button": "Abrechnung öffnen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Inhaber oder Admin von {company} "
            "auf prepza bist. Sie betrifft die Abrechnung deines Unternehmens und wird daher "
            "unabhängig von deinen E-Mail-Einstellungen gesendet."
        ),
    },
    "top_up_price_change": {
        "subject": "Neuer Aufladepreis für {company}",
        "preheader": "Ab {date} kostet jedes automatische Aufladen {new_price} statt {price}.",
        "heading": "Der Preis des automatischen Aufladens ändert sich",
        "lines": [
            (
                "Ab {date} kostet jedes automatische Aufladen für {company} {new_price} statt "
                "{price}, zuzüglich MwSt. oder Sales Tax, wo sie anfällt. Die Anzahl der "
                "Kandidaten bleibt gleich."
            ),
            (
                "Abbuchungen davor kosten weiterhin {price}. Wenn du einen anderen Betrag "
                "möchtest, ändere das automatische Aufladen vor dem {date} auf der "
                "Abrechnungsseite oder schalte es aus."
            ),
        ],
        "button": "Abrechnung öffnen",
        "footer": (
            "Diese E-Mail wurde an {email} gesendet, weil du Inhaber oder Admin von "
            "{company} auf prepza bist. Sie betrifft die Abrechnung deines Unternehmens und"
            " wird daher unabhängig von deinen E-Mail-Einstellungen gesendet."
        ),
    },
    "footer": "Diese E-Mail wurde an {email} gesendet, weil jemand diese Adresse auf prepza "
    "eingeladen hat. Wenn du sie nicht erwartet hast, kannst du sie ignorieren.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza hat {company} nicht verifiziert.",
    "paste_link": "Oder füge diesen Link in deinen Browser ein",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Abmelden",
    "email_settings": "E-Mail-Einstellungen ändern",
    "stop_reminders": "Keine Erinnerungen mehr zu diesem Interview",
    "stop_company": "Keine E-Mails mehr von {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza wird von {name} betrieben, {address}.",
}
