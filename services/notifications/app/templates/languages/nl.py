# Email texts in Dutch. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van een "
    "bedrijf op prepza."
)

TEXTS = {
    "candidate": {
        "subject": "{company} nodigt je uit voor een interview",
        "preheader": "Doe “{title}” op prepza. Log in met {email} om te beginnen.",
        "heading": "Uitnodiging voor een interview",
        "lines": [
            "{company} nodigt je uit voor het interview “{title}” op prepza.",
            (
                "Log in met {email} om te beginnen. Alleen dit adres kan het interview "
                "doen, en je hebt één poging."
            ),
        ],
        "button": "Uitnodiging openen",
    },
    "joined": {
        "subject": "Je link om “{title}” voort te zetten",
        "preheader": "Als je het interview verlaat, ga dan verder met deze link. Log in met {email}.",
        "heading": "Je link naar het interview",
        "lines": [
            "Je bent begonnen aan het interview “{title}” van {company} op prepza.",
            (
                "Als je het verlaat, ga dan verder met deze link: log in met {email}. Hij blijft "
                "werken, ook als {company} de link uitzet waarmee je begon. De tijd loopt door "
                "terwijl je weg bent."
            ),
        ],
        "button": "Interview voortzetten",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat met dit adres een interview op prepza "
            "is begonnen."
        ),
    },
    "reminder": {
        "subject": "Herinnering: {company} wacht op je interview",
        "preheader": "“{title}” staat nog open. Log in met {email} om te beginnen.",
        "heading": "Je interview wacht op je",
        "lines": [
            (
                "{company} heeft je een paar dagen geleden uitgenodigd voor het interview “{title}” "
                "op prepza, en je bent nog niet begonnen."
            ),
            (
                "Log in met {email} om te beginnen. Alleen dit adres kan het interview doen, en je "
                "hebt één poging. De uitnodiging verloopt 30 dagen na verzending."
            ),
        ],
        "button": "Uitnodiging openen",
    },
    "member": {
        "subject": "{inviter} nodigt je uit voor het team van {company} op prepza",
        "preheader": (
            "Word als {role} lid van het team van {company}. Log in met {email} om de uitnodiging "
            "te accepteren."
        ),
        "heading": "Uitnodiging voor het team",
        "lines": [
            (
                "{inviter} nodigt je uit om als {role} lid te worden van het team van {company} op "
                "prepza."
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
        "subject": "Kandidaatrapport: {candidate}",
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
        "button": "Naar prepza",
        "footer": "Deze e-mail is naar {email} gestuurd omdat {sender} op prepza een "
        "kandidaatrapport met dit adres heeft gedeeld. Verwachtte je hem niet, dan kun je hem "
        "negeren.",
    },
    "candidates": {
        "subject": "Rapport van alle kandidaten: {title}",
        "preheader": "Alle kandidaten voor “{title}” bij {company}. Het rapport zit in de bijlage.",
        "heading": "Kandidatenrapport",
        "lines": [
            "{sender} van {company} heeft het rapport van alle kandidaten voor het interview “{title}” gedeeld.",
            (
                "Het zit als PDF in de bijlage: de score, de voortgang en wat de browser van elke "
                "kandidaat liet zien, beste eerst. Beantwoord deze e-mail om {sender} te antwoorden."
            ),
        ],
        "button": "Naar prepza",
        "footer": "Deze e-mail is naar {email} gestuurd omdat {sender} op prepza een "
        "kandidatenrapport met dit adres heeft gedeeld. Verwachtte je hem niet, dan kun je hem "
        "negeren.",
    },
    "digest": {
        "subject": "Je activiteitenoverzicht op prepza",
        "preheader": "Wat er de afgelopen 24 uur in je bedrijven is gebeurd.",
        "heading": "Je activiteitenoverzicht",
        "lines": [
            "Dit is er de afgelopen 24 uur in je bedrijven op prepza gebeurd.",
        ],
        "rows": {
            "candidate_finished": "Kandidaten die klaar zijn: {count} · “{title}”",
            "invite_undelivered": "Niet-bezorgde uitnodigingen: {count} · “{title}”",
            "ats_not_invited": "Niet-uitgenodigde kandidaten uit {ats}: {count}",
            "interview_ready": "Interview klaar: “{title}”",
        },
        "button": "prepza openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je lid bent van een bedrijf op "
            "prepza en het activiteitenoverzicht ervan ontvangt."
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
        "subject": "prepza werkt de gebruiksvoorwaarden bij op {date}",
        "preheader": "De nieuwe gebruiksvoorwaarden gelden vanaf {date}.",
        "heading": "We werken onze gebruiksvoorwaarden bij",
        "lines": [
            (
                "We hebben een nieuwe versie van de gebruiksvoorwaarden van prepza gepubliceerd. "
                "Deze geldt vanaf {date}; tot die tijd gelden de huidige voorwaarden."
            ),
            (
                "Als je prepza na {date} gebruikt, ga je akkoord met de nieuwe voorwaarden. Wil "
                "je dat niet, dan kun je je account vóór die datum verwijderen in Instellingen."
            ),
        ],
        "button": "Lees de nieuwe voorwaarden",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je een prepza-account hebt. Het is "
            "een bericht over onze gebruiksvoorwaarden en wordt daarom altijd verstuurd, wat "
            "je e-mailinstellingen ook zijn."
        ),
    },
    "legal_privacy": {
        "subject": "prepza werkt het privacybeleid bij op {date}",
        "preheader": "Het nieuwe privacybeleid geldt vanaf {date}.",
        "heading": "We werken ons privacybeleid bij",
        "lines": [
            (
                "We hebben een nieuwe versie van het privacybeleid van prepza gepubliceerd, "
                "waarin staat hoe we je gegevens gebruiken. Deze geldt vanaf {date}; tot die tijd "
                "geldt de huidige versie."
            ),
            "Je kunt je gegevens altijd downloaden of verwijderen in Instellingen.",
        ],
        "button": "Lees het nieuwe privacybeleid",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je een prepza-account hebt. Het is "
            "een bericht over hoe we je gegevens gebruiken en wordt daarom altijd verstuurd, "
            "wat je e-mailinstellingen ook zijn."
        ),
    },
    "legal_dpa": {
        "subject": "prepza werkt de verwerkersovereenkomst bij op {date}",
        "preheader": "De nieuwe overeenkomst geldt voor je bedrijf vanaf {date}.",
        "heading": "We werken onze verwerkersovereenkomst bij",
        "lines": [
            (
                "We hebben een nieuwe versie gepubliceerd van de verwerkersovereenkomst waaronder "
                "prepza de gegevens van je kandidaten verwerkt. Deze geldt vanaf {date}; tot die "
                "tijd geldt de huidige versie."
            ),
            (
                "Een bedrijf dat om redelijke redenen van gegevensbescherming bezwaar maakt, kan "
                "vóór die datum stoppen met prepza en zijn bedrijf verwijderen."
            ),
        ],
        "button": "Lees de nieuwe overeenkomst",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je eigenaar of beheerder bent van een "
            "bedrijf op prepza. Het is een bericht over onze overeenkomst met je bedrijf en "
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
        "open_site": "prepza openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je hebt gekozen voor productupdates en"
            " nieuws van prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "prepza openen",
        "footer": (
            "Deze e-mail is naar {email} gestuurd omdat je hebt gekozen voor aanbiedingen en acties"
            " van prepza."
        ),
    },
    "top_up_failed": {
        "subject": "Automatisch opwaarderen mislukt voor {company}",
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
            "{company} op prepza. Hij gaat over de facturering van je bedrijf en wordt "
            "daarom altijd verstuurd, wat je e-mailinstellingen ook zijn."
        ),
    },
    "footer": "Deze e-mail is naar {email} gestuurd omdat iemand dit adres op prepza heeft "
    "uitgenodigd. Verwachtte je hem niet, dan kun je hem negeren.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza heeft {company} niet geverifieerd.",
    "paste_link": "Of plak deze link in je browser",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Afmelden",
    "email_settings": "E-mailinstellingen wijzigen",
    "stop_reminders": "Stuur me geen herinneringen meer voor dit interview",
    "stop_company": "Stuur me geen e-mails meer namens {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza wordt beheerd door {name}, {address}.",
}
