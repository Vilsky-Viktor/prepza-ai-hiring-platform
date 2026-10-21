# Email texts in Polish. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Ta wiadomość została wysłana na {email}, ponieważ masz rolę właściciela lub "
    "administratora w firmie w prepza."
)

TEXTS = {
    "candidate": {
        "subject": "{company} zaprasza Cię na rozmowę kwalifikacyjną",
        "preheader": "Weź udział w „{title}” w prepza. Zaloguj się adresem {email}, aby zacząć.",
        "heading": "Zaproszenie na rozmowę",
        "lines": [
            "{company} zaprasza Cię na rozmowę „{title}” w prepza.",
            (
                "Zaloguj się adresem {email}, aby zacząć. Tylko ten adres może wziąć "
                "udział w rozmowie i masz jedno podejście."
            ),
        ],
        "button": "Otwórz zaproszenie",
    },
    "joined": {
        "subject": "Twój link, aby kontynuować „{title}”",
        "preheader": "Jeśli opuścisz rozmowę, wróć do niej tym linkiem. Zaloguj się adresem {email}.",
        "heading": "Twój link do rozmowy",
        "lines": [
            "Twoja rozmowa „{title}” z {company} w prepza została rozpoczęta.",
            (
                "Jeśli ją opuścisz, wróć tym linkiem: zaloguj się adresem {email}. Działa nawet "
                "wtedy, gdy {company} wyłączy link, przez który ją rozpoczęto. Czas biegnie dalej, "
                "gdy Cię nie ma."
            ),
        ],
        "button": "Kontynuuj rozmowę",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ tym adresem rozpoczęto rozmowę "
            "w prepza."
        ),
    },
    "reminder": {
        "subject": "Przypomnienie: {company} czeka na Twoją rozmowę",
        "preheader": "Rozmowa „{title}” jest nadal otwarta. Zaloguj się adresem {email}, aby zacząć.",
        "heading": "Twoja rozmowa czeka",
        "lines": [
            (
                "Zaproszenie od {company} na rozmowę „{title}” w prepza czeka od kilku dni, "
                "a rozmowa nie została jeszcze rozpoczęta."
            ),
            (
                "Zaloguj się adresem {email}, aby zacząć. Tylko ten adres może wziąć udział w "
                "rozmowie i masz jedno podejście. Zaproszenie wygasa 30 dni po wysłaniu."
            ),
        ],
        "button": "Otwórz zaproszenie",
    },
    "member": {
        "subject": "{inviter} zaprasza Cię do zespołu {company} w prepza",
        "preheader": (
            "Dołącz do zespołu {company} jako {role}. Zaloguj się adresem {email}, aby przyjąć "
            "zaproszenie."
        ),
        "heading": "Zaproszenie do zespołu",
        "lines": [
            "{inviter} zaprasza Cię do zespołu {company} w prepza jako {role}.",
            (
                "Zaloguj się adresem {email}, aby przyjąć zaproszenie. Tylko ten adres może "
                "przyjąć zaproszenie."
            ),
        ],
        "button": "Otwórz zaproszenie",
        # The role's name as the lines use it.
        "roles": {"admin": "administrator", "viewer": "obserwator"},
    },
    "report": {
        "subject": "Raport kandydata: {candidate}",
        "preheader": "Kandydat {candidate} ukończył rozmowę „{title}” w firmie {company}. Raport jest w załączniku.",
        "heading": "Raport kandydata",
        "lines": [
            "{sender} z firmy {company} udostępnił(a) raport kandydata {candidate} z rozmowy „{title}”.",
            (
                "Jest w załączniku jako jednostronicowy PDF: wynik ogólny, wynik z każdego tematu "
                "i to, co pokazała przeglądarka kandydata. Odpowiedz na tę wiadomość, aby "
                "odpisać {sender}."
            ),
        ],
        "button": "Odwiedź prepza",
        "footer": "Ta wiadomość została wysłana na {email}, ponieważ {sender} udostępnił(a) temu "
        "adresowi raport kandydata w prepza. Jeśli się jej nie spodziewasz, możesz ją zignorować.",
    },
    "candidates": {
        "subject": "Raport wszystkich kandydatów: {title}",
        "preheader": "Wszyscy kandydaci z rozmowy „{title}” w firmie {company}. Raport jest w załączniku.",
        "heading": "Raport kandydatów",
        "lines": [
            "{sender} z firmy {company} udostępnił(a) raport wszystkich kandydatów z rozmowy „{title}”.",
            (
                "Jest w załączniku jako PDF: wynik i postęp każdego kandydata oraz to, co pokazała "
                "jego przeglądarka, od najlepszych. Odpowiedz na tę wiadomość, aby odpisać {sender}."
            ),
        ],
        "button": "Odwiedź prepza",
        "footer": "Ta wiadomość została wysłana na {email}, ponieważ {sender} udostępnił(a) temu "
        "adresowi raport kandydatów w prepza. Jeśli się jej nie spodziewasz, możesz ją zignorować.",
    },
    "digest": {
        "subject": "Twoje podsumowanie aktywności w prepza",
        "preheader": "Co wydarzyło się w Twoich firmach w ciągu ostatnich 24 godzin.",
        "heading": "Twoje podsumowanie aktywności",
        "lines": [
            "Oto, co wydarzyło się w Twoich firmach w prepza w ciągu ostatnich 24 godzin.",
        ],
        "rows": {
            "candidate_finished": "Kandydaci, którzy skończyli: {count} · „{title}”",
            "invite_undelivered": "Niedostarczone zaproszenia: {count} · „{title}”",
            "ats_not_invited": "Niezaproszeni kandydaci z systemu {ats}: {count}",
            "interview_ready": "Gotowa rozmowa: „{title}”",
        },
        "button": "Otwórz prepza",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ należysz do firmy w prepza i"
            " otrzymujesz jej podsumowanie aktywności."
        ),
    },
    "low_credits": {
        "subject": "Twoje kredyty się kończą",
        "preheader": "Doładuj, aby dalej zapraszać kandydatów.",
        "heading": "Kredyty się kończą",
        "lines": [
            (
                "Te firmy nie mają wystarczająco kredytów, aby zaprosić kolejnego "
                "kandydata. Doładuj, aby dalej zapraszać kandydatów."
            ),
        ],
        "rows": {
            "company": "{company} · dostępne kredyty: {available}",
        },
        "button": "Doładuj",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Oczekiwanie na kandydatów",
        "preheader": "Zaproś kandydatów e-mailem lub udostępnij link do rozmowy.",
        "heading": "Oczekiwanie na kandydatów",
        "lines": [
            (
                "Te rozmowy są gotowe od kilku dni, ale nikt nie został jeszcze zaproszony."
                " Zaproś kandydatów e-mailem lub udostępnij link do rozmowy."
            ),
        ],
        "rows": {
            "interview": "„{title}” · {company}",
        },
        "button": "Zaproś kandydatów",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Twoje tematy czekają na przegląd",
        "preheader": "Zatwierdź tematy, a pytania zostaną wygenerowane.",
        "heading": "Przejrzyj tematy",
        "lines": [
            (
                "Tematy rozpoczętych przez Ciebie rozmów czekają na Twój przegląd. Gdy je "
                "zatwierdzisz, pytania zostaną wygenerowane. Przegląd pozostawiony otwarty "
                "przez 14 dni zostaje anulowany."
            ),
        ],
        "rows": {
            "interview": "{company} · dni oczekiwania: {days}",
        },
        "button": "Przejrzyj tematy",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Zmieniamy regulamin prepza od {date}",
        "preheader": "Nowy regulamin obowiązuje od {date}.",
        "heading": "Zmieniamy nasz regulamin",
        "lines": [
            (
                "Opublikowaliśmy nową wersję regulaminu prepza. Obowiązuje od {date}; do tego "
                "czasu obowiązuje obecny regulamin."
            ),
            (
                "Korzystając z prepza po {date}, akceptujesz nowy regulamin. Jeśli go nie "
                "akceptujesz, możesz wcześniej usunąć konto w Ustawieniach."
            ),
        ],
        "button": "Przeczytaj nowy regulamin",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ masz konto w prepza. To "
            "powiadomienie o naszym regulaminie, więc jest wysyłane niezależnie od Twoich "
            "ustawień e-maili."
        ),
    },
    "legal_privacy": {
        "subject": "Zmieniamy politykę prywatności prepza od {date}",
        "preheader": "Nowa polityka prywatności obowiązuje od {date}.",
        "heading": "Zmieniamy naszą politykę prywatności",
        "lines": [
            (
                "Opublikowaliśmy nową wersję polityki prywatności prepza, która opisuje, jak "
                "wykorzystujemy Twoje dane. Obowiązuje od {date}; do tego czasu obowiązuje obecna "
                "wersja."
            ),
            "W każdej chwili możesz pobrać lub usunąć swoje dane w Ustawieniach.",
        ],
        "button": "Przeczytaj nową politykę prywatności",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ masz konto w prepza. To "
            "powiadomienie o tym, jak wykorzystujemy Twoje dane, więc jest wysyłane "
            "niezależnie od Twoich ustawień e-maili."
        ),
    },
    "legal_dpa": {
        "subject": "Zmieniamy umowę powierzenia przetwarzania danych prepza od {date}",
        "preheader": "Nowa umowa obowiązuje Twoją firmę od {date}.",
        "heading": "Zmieniamy naszą umowę powierzenia przetwarzania danych",
        "lines": [
            (
                "Opublikowaliśmy nową wersję umowy powierzenia przetwarzania danych, na podstawie "
                "której prepza przetwarza dane Twoich kandydatów. Obowiązuje od {date}; do tego "
                "czasu obowiązuje obecna wersja."
            ),
            (
                "Firma, która zgłasza sprzeciw z uzasadnionych powodów dotyczących ochrony "
                "danych, może przed tą datą zrezygnować z prepza i usunąć swoją firmę."
            ),
        ],
        "button": "Przeczytaj nową umowę",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ masz rolę właściciela lub "
            "administratora firmy w prepza. To powiadomienie o naszej umowie z Twoją firmą, "
            "więc jest wysyłane niezależnie od Twoich ustawień e-maili."
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
        "open_site": "Otwórz prepza",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ chcesz otrzymywać od prepza nowości"
            " o produkcie i aktualności."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Otwórz prepza",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ chcesz otrzymywać od prepza oferty i"
            " promocje."
        ),
    },
    "top_up_failed": {
        "subject": "Automatyczne doładowanie dla {company} nie powiodło się",
        "preheader": "Nie udało się obciążyć karty. Doładuj, aby dalej zapraszać kandydatów.",
        "heading": "Automatyczne doładowanie nie powiodło się",
        "lines": [
            (
                "Automatyczne doładowanie nie mogło obciążyć karty dla {company}, więc nie "
                "dodano kredytów."
            ),
            (
                "Doładuj, aby dalej zapraszać kandydatów. Automatyczne doładowanie spróbuje"
                " ponownie obciążyć kartę później."
            ),
        ],
        "button": "Doładuj",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ masz rolę właściciela lub "
            "administratora w {company} w prepza. Dotyczy rozliczeń Twojej firmy, więc jest"
            " wysyłana niezależnie od Twoich ustawień e-maili."
        ),
    },
    "top_up_paused": {
        "subject": "Automatyczne doładowanie dla {company} wstrzymane",
        "preheader": (
            "Karta została odrzucona. Zaktualizuj ją, aby ponownie włączyć automatyczne "
            "doładowanie."
        ),
        "heading": "Automatyczne doładowanie jest wstrzymane",
        "lines": [
            (
                "Karta do automatycznego doładowania dla {company} została odrzucona, a ponowne "
                "próby nie pomogą, więc automatyczne doładowanie jest wstrzymane i nie obciąży "
                "tej karty."
            ),
            (
                "Zaktualizuj kartę na stronie rozliczeń, aby ponownie włączyć automatyczne "
                "doładowanie. Do tego czasu doładowuj ręcznie, aby dalej zapraszać kandydatów."
            ),
        ],
        "button": "Zaktualizuj kartę",
        "footer": (
            "Ta wiadomość została wysłana na {email}, ponieważ masz rolę właściciela lub "
            "administratora w {company} w prepza. Dotyczy rozliczeń Twojej firmy, więc jest"
            " wysyłana niezależnie od Twoich ustawień e-maili."
        ),
    },
    "footer": "Ta wiadomość została wysłana na {email}, ponieważ ktoś zaprosił ten adres w "
    "prepza. Jeśli się jej nie spodziewasz, możesz ją zignorować.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza nie zweryfikowała firmy {company}.",
    "paste_link": "Lub wklej ten link do przeglądarki",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Wypisz się",
    "email_settings": "Zmień ustawienia e-maili",
    "stop_reminders": "Nie wysyłaj mi przypomnień o tej rozmowie",
    "stop_company": "Nie wysyłaj mi e-maili od {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza jest prowadzona przez {name}, {address}.",
}
