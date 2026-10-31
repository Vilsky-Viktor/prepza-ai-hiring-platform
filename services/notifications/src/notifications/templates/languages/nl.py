# Email texts in Dutch. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van een "
    "bedrijf op testee."
)

TEXTS = {
    "candidate": {
        "subject": "Uitnodiging voor een interview van {company}",
        "preheader": "Doe “{title}” op testee. Log in met {email} om te beginnen.",
        "heading": "Uitnodiging voor een interview",
        "lines": [
            "{company} nodigt je uit voor het interview “{title}” op testee.",
            (
                "Log in met {email} om te beginnen. Alleen dit adres kan het interview "
                "doen, en je hebt één poging."
            ),
        ],
        "button": "Uitnodiging openen",
    },
    "joined": {
        "subject": "Je link naar “{title}”",
        "preheader": "Als je het interview verlaat, ga dan verder met deze link. Log in met {email}.",
        "heading": "Je link naar het interview",
        "lines": [
            "Je bent begonnen aan het interview “{title}” van {company} op testee.",
            (
                "Als je het verlaat, ga dan verder met deze link: log in met {email}. Hij blijft "
                "werken, ook als {company} de link uitzet waarmee je begon. De tijd loopt door "
                "terwijl je weg bent."
            ),
        ],
        "button": "Interview voortzetten",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat met dit adres een interview op testee "
            "is begonnen."
        ),
    },
    "reminder": {
        "subject": "Herinnering: je interview bij {company}",
        "preheader": "“{title}” staat nog open. Log in met {email} om te beginnen.",
        "heading": "Je interview wacht op je",
        "lines": [
            (
                "{company} heeft je een paar dagen geleden uitgenodigd voor het interview “{title}” "
                "op testee, en je bent nog niet begonnen."
            ),
            (
                "Log in met {email} om te beginnen. Alleen dit adres kan het interview doen, en je "
                "hebt één poging. De uitnodiging verloopt 30 dagen na verzending."
            ),
        ],
        "button": "Uitnodiging openen",
    },
    "member": {
        "subject": "Word lid van {company} op testee",
        "preheader": (
            "Word als {role} lid van het team van {company}. Log in met {email} om de uitnodiging "
            "te accepteren."
        ),
        "heading": "Uitnodiging voor het team",
        "lines": [
            (
                "{inviter} nodigt je uit om als {role} lid te worden van het team van {company} op "
                "testee."
            ),
            (
                "Log in met {email} om de uitnodiging te accepteren. Alleen dit adres kan de "
                "uitnodiging accepteren."
            ),
        ],
        "button": "Uitnodiging openen",
        # The role's name as the lines use it.
        "roles": {"admin": "beheerder", "viewer": "kijker"},
    },
    "report": {
        "subject": "Rapport: {candidate}",
        "preheader": "{candidate} deed “{title}” bij {company}. Het rapport zit in de bijlage.",
        "heading": "Kandidaatrapport",
        "lines": [
            "{sender} van {company} heeft het rapport van {candidate} voor het interview “{title}” gedeeld.",
            (
                "Het zit als PDF van één pagina in de bijlage: de totaalscore, de score per "
                "onderwerp en wat de browser van de kandidaat liet zien. Beantwoord deze e-mail om "
                "{sender} te antwoorden."
            ),
        ],
        "button": "Naar testee",
        "footer": "Deze e-mail is naar {email} gestuurd omdat {sender} op testee een "
        "kandidaatrapport met dit adres heeft gedeeld. Verwachtte je hem niet, dan kun je hem "
        "negeren.",
    },
    "candidates": {
        "subject": "Alle kandidaten: {title}",
        "preheader": "Alle kandidaten voor “{title}” bij {company}. Het rapport zit in de bijlage.",
        "heading": "Kandidatenrapport",
        "lines": [
            "{sender} van {company} heeft het rapport van alle kandidaten voor het interview “{title}” gedeeld.",
            (
                "Het zit als PDF in de bijlage: de score, de voortgang en wat de browser van elke "
                "kandidaat liet zien, beste eerst. Beantwoord deze e-mail om {sender} te antwoorden."
            ),
        ],
        "button": "Naar testee",
        "footer": "Deze e-mail is naar {email} gestuurd omdat {sender} op testee een "
        "kandidatenrapport met dit adres heeft gedeeld. Verwachtte je hem niet, dan kun je hem "
        "negeren.",
    },
    "digest": {
        "subject": "Je activiteitenoverzicht op testee",
        "preheader": "Wat er de afgelopen 24 uur in je bedrijven is gebeurd.",
        "heading": "Je activiteitenoverzicht",
        "lines": [
            "Dit is er de afgelopen 24 uur in je bedrijven op testee gebeurd.",
        ],
        "rows": {
            "candidate_finished": "Kandidaten die klaar zijn: {count} · “{title}”",
            "invite_undelivered": "Niet-bezorgde uitnodigingen: {count} · “{title}”",
            "ats_not_invited": "Niet-uitgenodigde kandidaten uit {ats}: {count}",
            "interview_ready": "Interview klaar: “{title}”",
            "note_added": "Nieuwe notities van je team: {count} · “{title}”",
            "note": "{author}: “{excerpt}”",
            "note_by_former": "Een voormalig lid: “{excerpt}”",
        },
        "button": "testee openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je lid bent van een bedrijf op "
            "testee en het activiteitenoverzicht ervan ontvangt."
        ),
    },
    "low_credits": {
        "subject": "Je credits raken op",
        "preheader": "Waardeer op om kandidaten te blijven uitnodigen.",
        "heading": "Credits raken op",
        "lines": [
            (
                "Deze bedrijven hebben niet genoeg credits om nog een kandidaat uit te "
                "nodigen. Waardeer op om kandidaten te blijven uitnodigen."
            ),
        ],
        "rows": {
            "company": "{company} · beschikbare credits: {available}",
        },
        "button": "Opwaarderen",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Wachten op kandidaten",
        "preheader": "Nodig kandidaten uit per e-mail of deel de link van het interview.",
        "heading": "Wachten op kandidaten",
        "lines": [
            (
                "Deze interviews zijn al een paar dagen klaar, maar er is nog niemand "
                "uitgenodigd. Nodig kandidaten uit per e-mail of deel de link van het "
                "interview."
            ),
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "Kandidaten uitnodigen",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Je onderwerpen wachten op controle",
        "preheader": "Bevestig de onderwerpen, dan worden de vragen gemaakt.",
        "heading": "Controleer je onderwerpen",
        "lines": [
            (
                "De onderwerpen van de interviews die je bent begonnen, wachten op je "
                "controle. Zodra je ze bevestigt, worden de vragen gemaakt. Een controle "
                "die 14 dagen openstaat, wordt geannuleerd."
            ),
        ],
        "rows": {
            "interview": "{company} · wachttijd in dagen: {days}",
        },
        "button": "Onderwerpen controleren",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Nieuwe gebruiksvoorwaarden vanaf {date}",
        "preheader": "De nieuwe gebruiksvoorwaarden gelden vanaf {date}.",
        "heading": "We werken onze gebruiksvoorwaarden bij",
        "lines": [
            (
                "We hebben een nieuwe versie van de gebruiksvoorwaarden van testee gepubliceerd. "
                "Deze geldt vanaf {date}; tot die tijd gelden de huidige voorwaarden."
            ),
            (
                "Als je testee na {date} gebruikt, ga je akkoord met de nieuwe voorwaarden. Wil "
                "je dat niet, dan kun je je account vóór die datum verwijderen in Instellingen."
            ),
        ],
        "button": "Lees de nieuwe voorwaarden",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je een testee-account hebt. Het is "
            "een bericht over onze gebruiksvoorwaarden en wordt daarom altijd verstuurd, wat "
            "je e-mailinstellingen ook zijn."
        ),
    },
    "legal_privacy": {
        "subject": "Nieuw privacybeleid vanaf {date}",
        "preheader": "Het nieuwe privacybeleid geldt vanaf {date}.",
        "heading": "We werken ons privacybeleid bij",
        "lines": [
            (
                "We hebben een nieuwe versie van het privacybeleid van testee gepubliceerd, "
                "waarin staat hoe we je gegevens gebruiken. Deze geldt vanaf {date}; tot die tijd "
                "geldt de huidige versie."
            ),
            "Je kunt je gegevens altijd downloaden of verwijderen in Instellingen.",
        ],
        "button": "Lees het nieuwe privacybeleid",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je een testee-account hebt. Het is "
            "een bericht over hoe we je gegevens gebruiken en wordt daarom altijd verstuurd, "
            "wat je e-mailinstellingen ook zijn."
        ),
    },
    "legal_dpa": {
        "subject": "Nieuwe verwerkersovereenkomst vanaf {date}",
        "preheader": "De nieuwe overeenkomst geldt voor je bedrijf vanaf {date}.",
        "heading": "We werken onze verwerkersovereenkomst bij",
        "lines": [
            (
                "We hebben een nieuwe versie gepubliceerd van de verwerkersovereenkomst waaronder "
                "testee de gegevens van je kandidaten verwerkt. Deze geldt vanaf {date}; tot die "
                "tijd geldt de huidige versie."
            ),
            (
                "Een bedrijf dat om redelijke redenen van gegevensbescherming bezwaar maakt, kan "
                "vóór die datum stoppen met testee en zijn bedrijf verwijderen."
            ),
        ],
        "button": "Lees de nieuwe overeenkomst",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van een "
            "bedrijf op testee. Het is een bericht over onze overeenkomst met je bedrijf en "
            "wordt daarom altijd verstuurd, wat je e-mailinstellingen ook zijn."
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
        "open_site": "testee openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je hebt gekozen voor productupdates en"
            " nieuws van testee."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "testee openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je hebt gekozen voor aanbiedingen en acties"
            " van testee."
        ),
    },
    # An important notice: a service email about testee itself (a security incident, planned
    # downtime, a change to how it works), whatever the email settings; never a promotion.
    "notices": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "testee openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je een testee-account hebt. Het is een"
            " belangrijke mededeling over de dienst, zoals de beveiliging of beschikbaarheid"
            " ervan, en wordt daarom altijd verstuurd, wat je e-mailinstellingen ook zijn."
        ),
    },
    "top_up_failed": {
        "subject": "Opwaarderen mislukt: {company}",
        "preheader": (
            "De kaart kon niet worden belast. Waardeer op om kandidaten te blijven uitnodigen."
        ),
        "heading": "Automatisch opwaarderen mislukt",
        "lines": [
            (
                "Automatisch opwaarderen kon de kaart voor {company} niet belasten, dus er "
                "zijn geen credits toegevoegd."
            ),
            (
                "Waardeer op om kandidaten te blijven uitnodigen. Automatisch opwaarderen "
                "probeert de kaart later opnieuw."
            ),
        ],
        "button": "Opwaarderen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van "
            "{company} op testee. Hij gaat over de facturering van je bedrijf en wordt "
            "daarom altijd verstuurd, wat je e-mailinstellingen ook zijn."
        ),
    },
    "top_up_paused": {
        "subject": "Opwaarderen gepauzeerd: {company}",
        "preheader": (
            "De kaart is geweigerd. Werk hem bij om automatisch opwaarderen weer aan te zetten."
        ),
        "heading": "Automatisch opwaarderen is gepauzeerd",
        "lines": [
            (
                "De kaart voor het automatisch opwaarderen van {company} is geweigerd, en opnieuw "
                "proberen helpt niet. Daarom is automatisch opwaarderen gepauzeerd en wordt de "
                "kaart niet belast."
            ),
            (
                "Werk de kaart bij op de factureringspagina om automatisch opwaarderen weer aan "
                "te zetten. Waardeer tot die tijd handmatig op om kandidaten te blijven "
                "uitnodigen."
            ),
        ],
        "button": "Kaart bijwerken",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van "
            "{company} op testee. Hij gaat over de facturering van je bedrijf en wordt "
            "daarom altijd verstuurd, wat je e-mailinstellingen ook zijn."
        ),
    },
    "top_up_on": {
        "subject": "Automatisch opwaarderen staat aan: {company}",
        "preheader": (
            "{price} plus belasting elke keer dat het beschikbare saldo onder {threshold, "
            "plural, one {# credit} other {# credits}} zakt."
        ),
        "heading": "Automatisch opwaarderen staat aan",
        "lines": [
            (
                "Automatisch opwaarderen staat nu aan voor {company}. Elke keer dat het "
                "beschikbare saldo onder {threshold, plural, one {# credit} other {# credits}} "
                "zakt, wordt de opgeslagen kaart belast met {price}, plus btw of verkoopbelasting "
                "waar die van toepassing is, totdat automatisch opwaarderen wordt uitgezet."
            ),
            (
                "Elke afschrijving wordt gemaild naar de eigenaren en beheerders van het bedrijf, "
                "en Paddle, onze wederverkoper, mailt zijn bon."
            ),
            (
                "Wil je het uitzetten, open dan automatisch opwaarderen op de factureringspagina "
                "en kies ‘Uitzetten’. Het stopt meteen en er wordt niets meer afgeschreven."
            ),
        ],
        "button": "Facturering openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van "
            "{company} op testee. Hij gaat over de facturering van je bedrijf en wordt daarom "
            "altijd verstuurd, wat je e-mailinstellingen ook zijn."
        ),
    },
    "top_up_charged": {
        "subject": "Automatisch opgewaardeerd: {company}",
        "preheader": "{price} voor {credits, plural, one {# credit} other {# credits}} op {date}.",
        "heading": "Automatisch opwaarderen heeft de kaart belast",
        "lines": [
            (
                "Op {date} heeft automatisch opwaarderen de kaart voor {company} belast met "
                "{price}, inclusief belasting, en {credits, plural, one {# credit} other {# "
                "credits}} toegevoegd. {company} heeft nu {available, plural, one {# credit} "
                "other {# credits}} beschikbaar."
            ),
            "Paddle, onze wederverkoper, mailt de bon.",
            (
                "Wil je deze afschrijvingen stoppen, open dan automatisch opwaarderen op de "
                "factureringspagina en kies ‘Uitzetten’. Het stopt meteen en er wordt niets meer "
                "afgeschreven."
            ),
        ],
        "button": "Facturering openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van "
            "{company} op testee. Hij gaat over de facturering van je bedrijf en wordt daarom "
            "altijd verstuurd, wat je e-mailinstellingen ook zijn."
        ),
    },
    "top_up_price_change": {
        "subject": "Nieuwe opwaardeerprijs voor {company}",
        "preheader": (
            "Vanaf {date} kost elke automatische opwaardering {new_price} in plaats van {price}."
        ),
        "heading": "De prijs van automatisch opwaarderen verandert",
        "lines": [
            (
                "Vanaf {date} kost elke automatische opwaardering voor {company} {new_price} in "
                "plaats van {price}, plus btw of verkoopbelasting waar die van toepassing is. Je "
                "krijgt er evenveel kandidaten voor."
            ),
            (
                "Afschrijvingen vóór die datum kosten nog {price}. Wil je een ander bedrag, "
                "wijzig automatisch opwaarderen dan vóór {date} op de factureringspagina of zet "
                "het uit."
            ),
        ],
        "button": "Facturering openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van "
            "{company} op testee. Hij gaat over de facturering van je bedrijf en wordt "
            "daarom altijd verstuurd, wat je e-mailinstellingen ook zijn."
        ),
    },
    "footer": "Deze e-mail is naar {email} gestuurd omdat iemand dit adres op testee heeft "
    "uitgenodigd. Verwachtte je hem niet, dan kun je hem negeren.",
    # An invite from a company testee hasn't verified, at the end of the footer.
    "unverified": "testee heeft {company} niet geverifieerd.",
    "paste_link": "Of plak deze link in je browser",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Afmelden",
    "email_settings": "E-mailinstellingen wijzigen",
    "stop_reminders": "Stuur me geen herinneringen meer voor dit interview",
    "stop_company": "Stuur me geen e-mails meer namens {company}",
    # Who runs testee, at the end of every email.
    "operator": "testee wordt beheerd door {name}, {address}.",
}
