# Email texts in Italian. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Questa email è stata inviata a {email} perché sei proprietario o amministratore di "
    "un'azienda su prepza."
)

TEXTS = {
    "candidate": {
        "subject": "{company} ti invita a un colloquio",
        "preheader": "Svolgi «{title}» su prepza. Accedi con {email} per iniziare.",
        "heading": "Invito a un colloquio",
        "lines": [
            "{company} ti invita al colloquio «{title}» su prepza.",
            (
                "Accedi con {email} per iniziare. Solo questo indirizzo può svolgere "
                "il colloquio, e hai un solo tentativo."
            ),
        ],
        "button": "Apri l'invito",
    },
    "joined": {
        "subject": "Il tuo link per continuare «{title}»",
        "preheader": "Se lasci il colloquio, continua con questo link. Accedi con {email}.",
        "heading": "Il tuo link al colloquio",
        "lines": [
            "Hai iniziato il colloquio «{title}» di {company} su prepza.",
            (
                "Se lo lasci, continua con questo link: accedi con {email}. Funziona anche se "
                "{company} disattiva il link da cui hai iniziato. Il tempo continua a scorrere "
                "mentre sei via."
            ),
        ],
        "button": "Continua il colloquio",
        "footer": (
            "Questa email è stata inviata a {email} perché con questo indirizzo è stato iniziato "
            "un colloquio su prepza."
        ),
    },
    "reminder": {
        "subject": "Promemoria: {company} aspetta il tuo colloquio",
        "preheader": "«{title}» è ancora aperto. Accedi con {email} per iniziare.",
        "heading": "Il tuo colloquio ti aspetta",
        "lines": [
            (
                "{company} ti ha invitato al colloquio «{title}» su prepza qualche giorno fa, e "
                "non l'hai ancora iniziato."
            ),
            (
                "Accedi con {email} per iniziare. Solo questo indirizzo può svolgere il "
                "colloquio, e hai un solo tentativo. L'invito scade 30 giorni dopo l'invio."
            ),
        ],
        "button": "Apri l'invito",
    },
    "member": {
        "subject": "{inviter} ti invita a unirti al team di {company} su prepza",
        "preheader": "Unisciti al team di {company} come {role}. Accedi con {email} per accettare.",
        "heading": "Invito nel team",
        "lines": [
            "{inviter} ti invita a unirti al team di {company} su prepza come {role}.",
            "Accedi con {email} per accettare. Solo questo indirizzo può accettare l'invito.",
        ],
        "button": "Apri l'invito",
        # The role's name as the lines use it.
        "roles": {"admin": "amministratore", "viewer": "visualizzatore"},
    },
    "report": {
        "subject": "Report del candidato: {candidate}",
        "preheader": "{candidate} ha svolto «{title}» presso {company}. Il report è in allegato.",
        "heading": "Report del candidato",
        "lines": [
            "{sender} di {company} ha condiviso il report di {candidate} per il colloquio «{title}».",
            (
                "È allegato come PDF di una pagina: il punteggio complessivo, quello di ogni "
                "argomento e cosa ha mostrato il browser del candidato. Rispondi a questa email "
                "per rispondere a {sender}."
            ),
        ],
        "button": "Visita prepza",
        "footer": "Questa email è stata inviata a {email} perché {sender} ha condiviso il report "
        "di un candidato con questo indirizzo su prepza. Se non te l'aspettavi, puoi ignorarla.",
    },
    "candidates": {
        "subject": "Report di tutti i candidati: {title}",
        "preheader": "Tutti i candidati per «{title}» presso {company}. Il report è in allegato.",
        "heading": "Report dei candidati",
        "lines": [
            "{sender} di {company} ha condiviso il report di tutti i candidati per il colloquio «{title}».",
            (
                "È allegato come PDF: il punteggio di ogni candidato, i suoi progressi e cosa ha mostrato "
                "il suo browser, dai migliori in giù. Rispondi a questa email per rispondere a "
                "{sender}."
            ),
        ],
        "button": "Visita prepza",
        "footer": "Questa email è stata inviata a {email} perché {sender} ha condiviso il report "
        "dei candidati con questo indirizzo su prepza. Se non te l'aspettavi, puoi ignorarla.",
    },
    "digest": {
        "subject": "Il tuo riepilogo attività su prepza",
        "preheader": "Cosa è successo nelle tue aziende nelle ultime 24 ore.",
        "heading": "Il tuo riepilogo attività",
        "lines": [
            "Ecco cosa è successo nelle tue aziende su prepza nelle ultime 24 ore.",
        ],
        "rows": {
            "candidate_finished": "Candidati che hanno finito: {count} · «{title}»",
            "invite_undelivered": "Inviti non consegnati: {count} · «{title}»",
            "ats_not_invited": "Candidati da {ats} non invitati: {count}",
            "interview_ready": "Colloquio pronto: «{title}»",
        },
        "button": "Apri prepza",
        "footer": (
            "Questa email è stata inviata a {email} perché fai parte di un'azienda su "
            "prepza e ricevi il suo riepilogo attività."
        ),
    },
    "low_credits": {
        "subject": "I tuoi crediti stanno finendo",
        "preheader": "Ricarica per continuare a invitare candidati.",
        "heading": "I crediti stanno finendo",
        "lines": [
            (
                "Queste aziende non hanno abbastanza crediti per invitare un altro "
                "candidato. Ricarica per continuare a invitare candidati."
            ),
        ],
        "rows": {
            "company": "{company} · crediti disponibili: {available}",
        },
        "button": "Ricarica",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "In attesa di candidati",
        "preheader": "Invita i candidati via email o condividi il link del colloquio.",
        "heading": "In attesa di candidati",
        "lines": [
            (
                "Questi colloqui sono pronti da qualche giorno, ma non è ancora stato "
                "invitato nessuno. Invita i candidati via email o condividi il link del "
                "colloquio."
            ),
        ],
        "rows": {
            "interview": "«{title}» · {company}",
        },
        "button": "Invita i candidati",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "I tuoi argomenti aspettano la revisione",
        "preheader": "Conferma gli argomenti e le domande verranno generate.",
        "heading": "Rivedi i tuoi argomenti",
        "lines": [
            (
                "Gli argomenti dei colloqui che hai avviato aspettano la tua revisione. "
                "Appena li confermi, le domande vengono generate. Una revisione lasciata "
                "aperta per 14 giorni viene annullata."
            ),
        ],
        "rows": {
            "interview": "{company} · giorni di attesa: {days}",
        },
        "button": "Rivedi gli argomenti",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "prepza aggiorna i suoi termini di servizio il {date}",
        "preheader": "I nuovi termini di servizio si applicano dal {date}.",
        "heading": "Aggiorniamo i nostri termini di servizio",
        "lines": [
            (
                "Abbiamo pubblicato una nuova versione dei termini di servizio di prepza. Si "
                "applica dal {date}; fino ad allora valgono i termini attuali."
            ),
            (
                "Se usi prepza dopo il {date}, accetti i nuovi termini. Se non li accetti, puoi "
                "eliminare il tuo account nelle Impostazioni prima di quella data."
            ),
        ],
        "button": "Leggi i nuovi termini",
        "footer": (
            "Questa email è stata inviata a {email} perché hai un account prepza. È un avviso "
            "sui nostri termini di servizio, quindi viene inviata indipendentemente dalle tue "
            "impostazioni email."
        ),
    },
    "legal_privacy": {
        "subject": "prepza aggiorna la sua informativa sulla privacy il {date}",
        "preheader": "La nuova informativa sulla privacy si applica dal {date}.",
        "heading": "Aggiorniamo la nostra informativa sulla privacy",
        "lines": [
            (
                "Abbiamo pubblicato una nuova versione dell'informativa sulla privacy di prepza, "
                "che spiega come usiamo i tuoi dati. Si applica dal {date}; fino ad allora vale "
                "quella attuale."
            ),
            "Puoi scaricare o eliminare i tuoi dati nelle Impostazioni in qualsiasi momento.",
        ],
        "button": "Leggi la nuova informativa sulla privacy",
        "footer": (
            "Questa email è stata inviata a {email} perché hai un account prepza. È un avviso "
            "su come usiamo i tuoi dati, quindi viene inviata indipendentemente dalle tue "
            "impostazioni email."
        ),
    },
    "legal_dpa": {
        "subject": "prepza aggiorna il suo accordo sul trattamento dei dati il {date}",
        "preheader": "Il nuovo accordo si applica alla tua azienda dal {date}.",
        "heading": "Aggiorniamo il nostro accordo sul trattamento dei dati",
        "lines": [
            (
                "Abbiamo pubblicato una nuova versione dell'accordo sul trattamento dei dati in "
                "base al quale prepza tratta i dati dei tuoi candidati. Si applica dal {date}; "
                "fino ad allora vale quello attuale."
            ),
            (
                "Un'azienda che si oppone per ragionevoli motivi di protezione dei dati può "
                "smettere di usare prepza ed eliminare la propria azienda prima di quella data."
            ),
        ],
        "button": "Leggi il nuovo accordo",
        "footer": (
            "Questa email è stata inviata a {email} perché sei proprietario o amministratore "
            "di un'azienda su prepza. È un avviso sul nostro accordo con la tua azienda, "
            "quindi viene inviata indipendentemente dalle tue impostazioni email."
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
        "open_site": "Apri prepza",
        "footer": (
            "Questa email è stata inviata a {email} perché hai scelto di ricevere novità sul"
            " prodotto e notizie da prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Apri prepza",
        "footer": (
            "Questa email è stata inviata a {email} perché hai scelto di ricevere offerte e"
            " promozioni da prepza."
        ),
    },
    "top_up_failed": {
        "subject": "Ricarica automatica non riuscita per {company}",
        "preheader": (
            "Non è stato possibile addebitare la carta. Ricarica per continuare a invitare "
            "candidati."
        ),
        "heading": "Ricarica automatica non riuscita",
        "lines": [
            (
                "La ricarica automatica non è riuscita ad addebitare la carta per "
                "{company}, quindi non sono stati aggiunti crediti."
            ),
            (
                "Ricarica per continuare a invitare candidati. La ricarica automatica "
                "riproverà più tardi con la carta."
            ),
        ],
        "button": "Ricarica",
        "footer": (
            "Questa email è stata inviata a {email} perché sei proprietario o "
            "amministratore di {company} su prepza. Riguarda la fatturazione della tua "
            "azienda, quindi viene inviata indipendentemente dalle tue impostazioni email."
        ),
    },
    "top_up_paused": {
        "subject": "Ricarica automatica in pausa per {company}",
        "preheader": (
            "La carta è stata rifiutata. Aggiornala per riattivare la ricarica automatica."
        ),
        "heading": "La ricarica automatica è in pausa",
        "lines": [
            (
                "La carta della ricarica automatica di {company} è stata rifiutata e riprovare "
                "non servirebbe, quindi la ricarica automatica è in pausa e non la addebiterà."
            ),
            (
                "Aggiorna la carta nella pagina Fatturazione per riattivare la ricarica "
                "automatica. Nel frattempo, ricarica manualmente per continuare a invitare "
                "candidati."
            ),
        ],
        "button": "Aggiorna la carta",
        "footer": (
            "Questa email è stata inviata a {email} perché sei proprietario o "
            "amministratore di {company} su prepza. Riguarda la fatturazione della tua "
            "azienda, quindi viene inviata indipendentemente dalle tue impostazioni email."
        ),
    },
    "top_up_price_change": {
        "subject": "Cambia il prezzo della ricarica automatica per {company}",
        "preheader": "Dal {date}, ogni ricarica automatica costa {new_price} invece di {price}.",
        "heading": "Cambia il prezzo della ricarica automatica",
        "lines": [
            (
                "Dal {date}, ogni ricarica automatica per {company} costa {new_price} invece di "
                "{price}, più IVA o imposta sulle vendite dove si applica. Il numero di candidati "
                "resta lo stesso."
            ),
            (
                "Gli addebiti fino ad allora costano ancora {price}. Se preferisci un importo "
                "diverso, modifica o disattiva la ricarica automatica nella pagina Fatturazione "
                "prima del {date}."
            ),
        ],
        "button": "Apri Fatturazione",
        "footer": (
            "Questa email è stata inviata a {email} perché sei proprietario o "
            "amministratore di {company} su prepza. Riguarda la fatturazione della tua "
            "azienda, quindi viene inviata indipendentemente dalle tue impostazioni email."
        ),
    },
    "footer": "Questa email è stata inviata a {email} perché qualcuno ha invitato questo "
    "indirizzo su prepza. Se non te l'aspettavi, puoi ignorarla.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza non ha verificato {company}.",
    "paste_link": "Oppure incolla questo link nel tuo browser",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Annulla l'iscrizione",
    "email_settings": "Modifica le impostazioni email",
    "stop_reminders": "Non inviarmi promemoria per questo colloquio",
    "stop_company": "Non inviarmi email da parte di {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza è gestita da {name}, {address}.",
}
