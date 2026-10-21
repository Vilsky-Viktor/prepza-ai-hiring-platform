# Email texts in Estonian. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "See e-kiri saadeti aadressile {email}, sest oled prepzas ettevõtte omanik või administraator."
)

TEXTS = {
    "candidate": {
        "subject": "{company} kutsub sind intervjuule",
        "preheader": "Tee prepzas intervjuu „{title}“. Alustamiseks logi sisse aadressiga {email}.",
        "heading": "Kutse intervjuule",
        "lines": [
            "{company} kutsub sind prepzas intervjuule „{title}“.",
            (
                "Alustamiseks logi sisse aadressiga {email}. Intervjuud saab teha "
                "ainult see aadress ja sul on üks katse."
            ),
        ],
        "button": "Ava kutse",
    },
    "joined": {
        "subject": "Sinu link, et jätkata intervjuud „{title}“",
        "preheader": "Kui lahkud intervjuult, jätka selle lingiga. Logi sisse aadressiga {email}.",
        "heading": "Sinu intervjuu link",
        "lines": [
            "Alustasid prepzas ettevõtte {company} intervjuud „{title}“.",
            (
                "Kui lahkud, jätka selle lingiga: logi sisse aadressiga {email}. See töötab ka "
                "siis, kui {company} lülitab välja lingi, millega alustasid. Aeg jookseb edasi "
                "ka siis, kui oled eemal."
            ),
        ],
        "button": "Jätka intervjuud",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest selle aadressiga alustati prepzas intervjuud."
        ),
    },
    "reminder": {
        "subject": "Meeldetuletus: {company} ootab sinu intervjuud",
        "preheader": "„{title}“ on endiselt avatud. Alustamiseks logi sisse aadressiga {email}.",
        "heading": "Sinu intervjuu ootab",
        "lines": [
            (
                "{company} kutsus sind mõni päev tagasi prepzas intervjuule „{title}“, "
                "kuid sa pole seda veel alustanud."
            ),
            (
                "Alustamiseks logi sisse aadressiga {email}. Intervjuud saab teha ainult see "
                "aadress ja sul on üks katse. Kutse aegub 30 päeva pärast saatmist."
            ),
        ],
        "button": "Ava kutse",
    },
    "member": {
        "subject": "{inviter} kutsub sind prepzas ettevõtte {company} meeskonda",
        "preheader": (
            "Liitu ettevõtte {company} meeskonnaga {role}. Kutse vastuvõtmiseks logi sisse "
            "aadressiga {email}."
        ),
        "heading": "Kutse meeskonda",
        "lines": [
            "{inviter} kutsub sind prepzas ettevõtte {company} meeskonda {role}.",
            (
                "Kutse vastuvõtmiseks logi sisse aadressiga {email}. Kutset saab vastu võtta "
                "ainult see aadress."
            ),
        ],
        "button": "Ava kutse",
        # The role's name as the lines use it.
        "roles": {"admin": "administraatorina", "viewer": "vaatajana"},
    },
    "report": {
        "subject": "Kandidaadi aruanne: {candidate}",
        "preheader": "{candidate} tegi ettevõttes {company} intervjuu „{title}“. Aruanne on manuses.",
        "heading": "Kandidaadi aruanne",
        "lines": [
            "{sender} ettevõttest {company} jagas kandidaadi {candidate} aruannet intervjuu „{title}“ kohta.",
            (
                "See on manuses üheleheküljelise PDF-ina: üldhinne, iga teema tulemus ja see, "
                "mida kandidaadi brauser näitas. Kasutajale {sender} vastamiseks vasta sellele "
                "e-kirjale."
            ),
        ],
        "button": "Külasta prepzat",
        "footer": "See e-kiri saadeti aadressile {email}, sest {sender} jagas prepzas selle "
        "aadressiga kandidaadi aruannet. Kui sa seda ei oodanud, võid selle tähelepanuta jätta.",
    },
    "candidates": {
        "subject": "Kõigi kandidaatide aruanne: {title}",
        "preheader": "Kõik intervjuu „{title}“ kandidaadid ettevõttes {company}. Aruanne on manuses.",
        "heading": "Kandidaatide aruanne",
        "lines": [
            "{sender} ettevõttest {company} jagas intervjuu „{title}“ kõigi kandidaatide aruannet.",
            (
                "See on manuses PDF-ina: iga kandidaadi hinne, edenemine ja see, mida tema "
                "brauser näitas, parimad eespool. Kasutajale {sender} vastamiseks vasta sellele "
                "e-kirjale."
            ),
        ],
        "button": "Külasta prepzat",
        "footer": "See e-kiri saadeti aadressile {email}, sest {sender} jagas prepzas selle "
        "aadressiga kandidaatide aruannet. Kui sa seda ei oodanud, võid selle tähelepanuta jätta.",
    },
    "digest": {
        "subject": "Sinu tegevuste kokkuvõte prepzas",
        "preheader": "Mis sinu ettevõtetes viimase 24 tunni jooksul juhtus.",
        "heading": "Sinu tegevuste kokkuvõte",
        "lines": [
            "Siin on, mis sinu ettevõtetes prepzas viimase 24 tunni jooksul juhtus.",
        ],
        "rows": {
            "candidate_finished": "Lõpetanud kandidaadid: {count} · „{title}“",
            "invite_undelivered": "Kohale jõudmata kutsed: {count} · „{title}“",
            "ats_not_invited": "Kutsumata kandidaadid süsteemist {ats}: {count}",
            "interview_ready": "Valmis intervjuu: „{title}“",
        },
        "button": "Ava prepza",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest kuulud prepzas ettevõttesse ja "
            "saad selle tegevuste kokkuvõtet."
        ),
    },
    "low_credits": {
        "subject": "Sinu krediidid hakkavad otsa saama",
        "preheader": "Laadi juurde, et kandidaate edasi kutsuda.",
        "heading": "Krediidid hakkavad otsa saama",
        "lines": [
            (
                "Nendel ettevõtetel pole piisavalt krediiti, et veel üht kandidaati "
                "kutsuda. Laadi juurde, et kandidaate edasi kutsuda."
            ),
        ],
        "rows": {
            "company": "{company} · saadaval krediiti: {available}",
        },
        "button": "Laadi juurde",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Ootab kandidaate",
        "preheader": "Kutsu kandidaadid e-postiga või jaga intervjuu linki.",
        "heading": "Ootab kandidaate",
        "lines": [
            (
                "Need intervjuud on juba mõni päev valmis, kuid kedagi pole veel kutsutud. "
                "Kutsu kandidaadid e-postiga või jaga intervjuu linki."
            ),
        ],
        "rows": {
            "interview": "„{title}“ · {company}",
        },
        "button": "Kutsu kandidaadid",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Sinu teemad ootavad ülevaatamist",
        "preheader": "Kinnita teemad ja küsimused luuakse.",
        "heading": "Vaata oma teemad üle",
        "lines": [
            (
                "Sinu alustatud intervjuude teemad ootavad ülevaatamist. Kui need kinnitad,"
                " luuakse küsimused. Ülevaatus, mis jääb 14 päevaks avatuks, tühistatakse."
            ),
        ],
        "rows": {
            "interview": "{company} · ootepäevi: {days}",
        },
        "button": "Vaata teemad üle",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "prepza uuendab kasutustingimusi alates {date}",
        "preheader": "Uued kasutustingimused kehtivad alates {date}.",
        "heading": "Uuendame oma kasutustingimusi",
        "lines": [
            (
                "Avaldasime prepza kasutustingimuste uue versiooni. See kehtib alates {date}; "
                "seni kehtivad praegused tingimused."
            ),
            (
                "Kui kasutad prepzat ka alates {date}, nõustud uute tingimustega. Kui sa ei "
                "nõustu, saad enne seda kuupäeva oma konto seadetes kustutada."
            ),
        ],
        "button": "Loe uusi tingimusi",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest sul on prepza konto. See on teade "
            "meie kasutustingimuste kohta, seega saadetakse see sõltumata sinu e-kirjade "
            "seadetest."
        ),
    },
    "legal_privacy": {
        "subject": "prepza uuendab privaatsuspoliitikat alates {date}",
        "preheader": "Uus privaatsuspoliitika kehtib alates {date}.",
        "heading": "Uuendame oma privaatsuspoliitikat",
        "lines": [
            (
                "Avaldasime prepza privaatsuspoliitika uue versiooni, mis kirjeldab, kuidas me "
                "sinu andmeid kasutame. See kehtib alates {date}; seni kehtib praegune versioon."
            ),
            "Saad oma andmed seadetes igal ajal alla laadida või kustutada.",
        ],
        "button": "Loe uut privaatsuspoliitikat",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest sul on prepza konto. See on teade "
            "selle kohta, kuidas me sinu andmeid kasutame, seega saadetakse see sõltumata "
            "sinu e-kirjade seadetest."
        ),
    },
    "legal_dpa": {
        "subject": "prepza uuendab andmetöötluslepingut alates {date}",
        "preheader": "Uus leping kehtib sinu ettevõttele alates {date}.",
        "heading": "Uuendame oma andmetöötluslepingut",
        "lines": [
            (
                "Avaldasime andmetöötluslepingu uue versiooni, mille alusel prepza sinu "
                "kandidaatide andmeid töötleb. See kehtib alates {date}; seni kehtib praegune "
                "versioon."
            ),
            (
                "Ettevõte, mis on sellele mõistlikel andmekaitselistel põhjustel vastu, saab enne "
                "seda kuupäeva lõpetada prepza kasutamise ja oma ettevõtte kustutada."
            ),
        ],
        "button": "Loe uut lepingut",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest oled prepzas mõne ettevõtte omanik "
            "või administraator. See on teade meie lepingu kohta sinu ettevõttega, seega "
            "saadetakse see sõltumata sinu e-kirjade seadetest."
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
        "open_site": "Ava prepza",
        "footer": "See e-kiri saadeti aadressile {email}, sest valisid prepzalt tooteuudiste saamise.",
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Ava prepza",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest valisid prepzalt pakkumiste ja kampaaniate"
            " saamise."
        ),
    },
    "top_up_failed": {
        "subject": "Automaatne juurdelaadimine ebaõnnestus: {company}",
        "preheader": "Kaardilt ei saanud makset võtta. Laadi juurde, et kandidaate edasi kutsuda.",
        "heading": "Automaatne juurdelaadimine ebaõnnestus",
        "lines": [
            (
                "Automaatne juurdelaadimine ei saanud ettevõtte {company} kaardilt makset "
                "võtta, seega krediiti ei lisatud."
            ),
            (
                "Laadi juurde, et kandidaate edasi kutsuda. Automaatne juurdelaadimine "
                "proovib kaarti hiljem uuesti."
            ),
        ],
        "button": "Laadi juurde",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest oled prepzas ettevõtte {company} "
            "omanik või administraator. See puudutab sinu ettevõtte arveldust, seega "
            "saadetakse see sõltumata sinu e-kirjade seadetest."
        ),
    },
    "top_up_paused": {
        "subject": "Automaatne juurdelaadimine peatatud: {company}",
        "preheader": (
            "Kaart lükati tagasi. Uuenda kaarti, et automaatne juurdelaadimine uuesti sisse "
            "lülitada."
        ),
        "heading": "Automaatne juurdelaadimine on peatatud",
        "lines": [
            (
                "Ettevõtte {company} automaatse juurdelaadimise kaart lükati tagasi ja uus katse "
                "ei aita, seega on automaatne juurdelaadimine peatatud ega võta sellelt kaardilt "
                "makseid."
            ),
            (
                "Uuenda kaarti arvelduse lehel, et automaatne juurdelaadimine uuesti sisse "
                "lülitada. Seni laadi juurde käsitsi, et kandidaate edasi kutsuda."
            ),
        ],
        "button": "Uuenda kaarti",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest oled prepzas ettevõtte {company} "
            "omanik või administraator. See puudutab sinu ettevõtte arveldust, seega "
            "saadetakse see sõltumata sinu e-kirjade seadetest."
        ),
    },
    "top_up_price_change": {
        "subject": "Automaatse juurdelaadimise hind muutub: {company}",
        "preheader": (
            "Alates kuupäevast {date} maksab iga automaatne juurdelaadimine {price} asemel "
            "{new_price}."
        ),
        "heading": "Automaatse juurdelaadimise hind muutub",
        "lines": [
            (
                "Alates kuupäevast {date} maksab iga ettevõtte {company} automaatne "
                "juurdelaadimine {price} asemel {new_price}, millele lisandub käibemaks või "
                "müügimaks, kus see kehtib. Kandidaatide arv jääb samaks."
            ),
            (
                "Seni maksavad maksed endiselt {price}. Kui soovid teist summat, muuda "
                "automaatset juurdelaadimist arvelduse lehel või lülita see välja enne kuupäeva "
                "{date}."
            ),
        ],
        "button": "Ava arveldus",
        "footer": (
            "See e-kiri saadeti aadressile {email}, sest oled prepzas ettevõtte {company} "
            "omanik või administraator. See puudutab sinu ettevõtte arveldust, seega "
            "saadetakse see sõltumata sinu e-kirjade seadetest."
        ),
    },
    "footer": "See e-kiri saadeti aadressile {email}, sest keegi kutsus selle aadressi "
    "prepzasse. Kui sa seda ei oodanud, võid selle tähelepanuta jätta.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza ei ole ettevõtet {company} kinnitanud.",
    "paste_link": "Või kleebi see link oma brauserisse",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Loobu tellimusest",
    "email_settings": "Muuda oma e-kirjade seadeid",
    "stop_reminders": "Ära saada mulle selle intervjuu meeldetuletusi",
    "stop_company": "Ära saada mulle e-kirju ettevõttelt {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepzat haldab {name}, {address}.",
}
