# Email texts in French. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Cet e-mail a été envoyé à {email} parce que vous êtes propriétaire ou admin d'une "
    "entreprise sur prepza."
)

TEXTS = {
    "candidate": {
        "subject": "Invitation à un entretien : {company}",
        "preheader": "Passez « {title} » sur prepza. Connectez-vous avec {email} pour commencer.",
        "heading": "Invitation à un entretien",
        "lines": [
            "{company} vous invite à l'entretien « {title} » sur prepza.",
            (
                "Connectez-vous avec {email} pour commencer. Seule cette adresse "
                "peut passer l'entretien, et vous n'avez qu'une tentative."
            ),
        ],
        "button": "Ouvrir l'invitation",
    },
    "joined": {
        "subject": "Votre lien vers « {title} »",
        "preheader": "Si vous quittez l'entretien, continuez avec ce lien. Connectez-vous avec {email}.",
        "heading": "Votre lien vers l'entretien",
        "lines": [
            "Vous avez commencé l'entretien « {title} » de {company} sur prepza.",
            (
                "Si vous le quittez, continuez avec ce lien : connectez-vous avec {email}. Il "
                "fonctionne même si {company} désactive le lien par lequel vous avez commencé. "
                "Le temps continue de s'écouler pendant votre absence."
            ),
        ],
        "button": "Continuer l'entretien",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce qu'un entretien a été commencé sur prepza "
            "avec cette adresse."
        ),
    },
    "reminder": {
        "subject": "Rappel : votre entretien avec {company}",
        "preheader": "« {title} » est toujours ouvert. Connectez-vous avec {email} pour commencer.",
        "heading": "Votre entretien vous attend",
        "lines": [
            (
                "{company} vous a invité à l'entretien « {title} » sur prepza il y a quelques "
                "jours, et vous ne l'avez pas encore commencé."
            ),
            (
                "Connectez-vous avec {email} pour commencer. Seule cette adresse peut passer "
                "l'entretien, et vous n'avez qu'une tentative. L'invitation expire 30 jours "
                "après son envoi."
            ),
        ],
        "button": "Ouvrir l'invitation",
    },
    "member": {
        "subject": "Rejoignez {company} sur prepza",
        "preheader": (
            "Rejoignez l'équipe de {company} en tant que {role}. Connectez-vous avec {email} pour "
            "accepter."
        ),
        "heading": "Invitation à rejoindre l'équipe",
        "lines": [
            (
                "{inviter} vous invite à rejoindre l'équipe de {company} sur prepza en tant que "
                "{role}."
            ),
            (
                "Connectez-vous avec {email} pour accepter. Seule cette adresse peut accepter "
                "l'invitation."
            ),
        ],
        "button": "Ouvrir l'invitation",
        # The role's name as the lines use it.
        "roles": {"admin": "admin", "viewer": "lecteur"},
    },
    "report": {
        "subject": "Rapport : {candidate}",
        "preheader": "{candidate} a passé « {title} » chez {company}. Le rapport est en pièce jointe.",
        "heading": "Rapport de candidat",
        "lines": [
            "{sender} de {company} a partagé le rapport de {candidate} pour l'entretien « {title} ».",
            (
                "Il est joint sous forme de PDF d'une page : la note globale, le score de chaque "
                "thème et ce que le navigateur du candidat a montré. Répondez à cet e-mail pour "
                "répondre à {sender}."
            ),
        ],
        "button": "Visiter prepza",
        "footer": "Cet e-mail a été envoyé à {email} parce que {sender} a partagé un rapport de "
        "candidat avec cette adresse sur prepza. Si vous ne l'attendiez pas, vous pouvez "
        "l'ignorer.",
    },
    "candidates": {
        "subject": "Tous les candidats : {title}",
        "preheader": "Tous les candidats pour « {title} » chez {company}. Le rapport est en pièce jointe.",
        "heading": "Rapport des candidats",
        "lines": [
            "{sender} de {company} a partagé le rapport de tous les candidats pour l'entretien « {title} ».",
            (
                "Il est joint sous forme de PDF : la note de chaque candidat, sa progression et ce "
                "que son navigateur a montré, les meilleurs en premier. Répondez à cet e-mail pour "
                "répondre à {sender}."
            ),
        ],
        "button": "Visiter prepza",
        "footer": "Cet e-mail a été envoyé à {email} parce que {sender} a partagé un rapport des "
        "candidats avec cette adresse sur prepza. Si vous ne l'attendiez pas, vous pouvez "
        "l'ignorer.",
    },
    "digest": {
        "subject": "Votre récapitulatif d'activité sur prepza",
        "preheader": "Ce qui s'est passé dans vos entreprises ces dernières 24 heures.",
        "heading": "Votre récapitulatif d'activité",
        "lines": [
            "Voici ce qui s'est passé dans vos entreprises sur prepza ces dernières 24 heures.",
        ],
        "rows": {
            "candidate_finished": "Candidats ayant terminé : {count} · « {title} »",
            "invite_undelivered": "Invitations non remises : {count} · « {title} »",
            "ats_not_invited": "Candidats de {ats} non invités : {count}",
            "interview_ready": "Entretien prêt : « {title} »",
            "note_added": "Nouveaux commentaires de votre équipe : {count} · « {title} »",
            "note": "{author} : « {excerpt} »",
            "note_by_former": "Un ancien membre : « {excerpt} »",
        },
        "button": "Ouvrir prepza",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous êtes membre d'une entreprise "
            "sur prepza et recevez son récapitulatif d'activité."
        ),
    },
    "low_credits": {
        "subject": "Vos crédits sont bientôt épuisés",
        "preheader": "Rechargez pour continuer à inviter des candidats.",
        "heading": "Crédits bientôt épuisés",
        "lines": [
            (
                "Ces entreprises n'ont plus assez de crédits pour inviter un autre "
                "candidat. Rechargez pour continuer à inviter des candidats."
            ),
        ],
        "rows": {
            "company": "{company} · crédits disponibles : {available}",
        },
        "button": "Recharger",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "En attente de candidats",
        "preheader": "Invitez des candidats par e-mail ou partagez le lien de l'entretien.",
        "heading": "En attente de candidats",
        "lines": [
            (
                "Ces entretiens sont prêts depuis quelques jours, mais personne n'a encore "
                "été invité. Invitez des candidats par e-mail ou partagez le lien de "
                "l'entretien."
            ),
        ],
        "rows": {
            "interview": "« {title} » · {company}",
        },
        "button": "Inviter des candidats",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Vos thèmes attendent votre relecture",
        "preheader": "Validez les thèmes, et les questions seront générées.",
        "heading": "Relisez vos thèmes",
        "lines": [
            (
                "Les thèmes des entretiens que vous avez lancés attendent votre relecture. "
                "Dès que vous les validez, les questions sont générées. Une relecture "
                "restée ouverte 14 jours est annulée."
            ),
        ],
        "rows": {
            "interview": "{company} · jours d'attente : {days}",
        },
        "button": "Relire les thèmes",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Nouvelles conditions d'utilisation le {date}",
        "preheader": "Les nouvelles conditions d'utilisation s'appliquent à partir du {date}.",
        "heading": "Nous mettons à jour nos conditions d'utilisation",
        "lines": [
            (
                "Nous avons publié une nouvelle version des conditions d'utilisation de prepza. "
                "Elle s'applique à partir du {date} ; d'ici là, les conditions actuelles restent "
                "en vigueur."
            ),
            (
                "En utilisant prepza après le {date}, vous acceptez les nouvelles conditions. Si "
                "vous ne les acceptez pas, vous pouvez supprimer votre compte dans les Paramètres "
                "avant cette date."
            ),
        ],
        "button": "Lire les nouvelles conditions",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous avez un compte prepza. Il "
            "s'agit d'un avis concernant nos conditions d'utilisation ; il est donc envoyé "
            "quels que soient vos réglages d'e-mails."
        ),
    },
    "legal_privacy": {
        "subject": "Nouvelle politique de confidentialité le {date}",
        "preheader": "La nouvelle politique de confidentialité s'applique à partir du {date}.",
        "heading": "Nous mettons à jour notre politique de confidentialité",
        "lines": [
            (
                "Nous avons publié une nouvelle version de la politique de confidentialité de "
                "prepza, qui explique comment nous utilisons vos données. Elle s'applique à "
                "partir du {date} ; d'ici là, la version actuelle reste en vigueur."
            ),
            "Vous pouvez télécharger ou supprimer vos données dans les Paramètres à tout moment.",
        ],
        "button": "Lire la nouvelle politique de confidentialité",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous avez un compte prepza. Il "
            "s'agit d'un avis concernant l'utilisation de vos données ; il est donc envoyé "
            "quels que soient vos réglages d'e-mails."
        ),
    },
    "legal_dpa": {
        "subject": "Nouvel accord de traitement des données le {date}",
        "preheader": "Le nouvel accord s'applique à votre entreprise à partir du {date}.",
        "heading": "Nous mettons à jour notre accord de traitement des données",
        "lines": [
            (
                "Nous avons publié une nouvelle version de l'accord de traitement des données "
                "selon lequel prepza traite les données de vos candidats. Elle s'applique à "
                "partir du {date} ; d'ici là, la version actuelle reste en vigueur."
            ),
            (
                "Une entreprise qui s'y oppose pour des motifs raisonnables liés à la protection "
                "des données peut cesser d'utiliser prepza et supprimer son entreprise avant "
                "cette date."
            ),
        ],
        "button": "Lire le nouvel accord",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous êtes propriétaire ou admin "
            "d'une entreprise sur prepza. Il s'agit d'un avis concernant notre accord avec "
            "votre entreprise ; il est donc envoyé quels que soient vos réglages d'e-mails."
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
        "open_site": "Ouvrir prepza",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous avez choisi de recevoir les"
            " nouveautés du produit et les actualités de prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Ouvrir prepza",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous avez choisi de recevoir les offres et"
            " promotions de prepza."
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
        "open_site": "Ouvrir prepza",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous avez un compte prepza. Il s'agit"
            " d'un avis important concernant le service, comme sa sécurité ou sa disponibilité"
            " ; il est donc envoyé quels que soient vos réglages d'e-mails."
        ),
    },
    "top_up_failed": {
        "subject": "Échec de la recharge : {company}",
        "preheader": (
            "La carte n'a pas pu être débitée. Rechargez pour continuer à inviter des candidats."
        ),
        "heading": "Échec de la recharge automatique",
        "lines": [
            (
                "La recharge automatique n'a pas pu débiter la carte pour {company}, aucun "
                "crédit n'a donc été ajouté."
            ),
            (
                "Rechargez pour continuer à inviter des candidats. La recharge automatique "
                "réessaiera la carte plus tard."
            ),
        ],
        "button": "Recharger",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous êtes propriétaire ou admin de"
            " {company} sur prepza. Il concerne la facturation de votre entreprise ; il est"
            " donc envoyé quels que soient vos réglages d'e-mails."
        ),
    },
    "top_up_paused": {
        "subject": "Recharge en pause : {company}",
        "preheader": (
            "La carte a été refusée. Mettez-la à jour pour réactiver la recharge automatique."
        ),
        "heading": "La recharge automatique est en pause",
        "lines": [
            (
                "La carte de la recharge automatique de {company} a été refusée, et réessayer n'y "
                "changerait rien : la recharge automatique est donc en pause et ne la débitera "
                "pas."
            ),
            (
                "Mettez la carte à jour sur la page Facturation pour réactiver la recharge "
                "automatique. D'ici là, rechargez manuellement pour continuer à inviter des "
                "candidats."
            ),
        ],
        "button": "Mettre à jour la carte",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous êtes propriétaire ou admin de"
            " {company} sur prepza. Il concerne la facturation de votre entreprise ; il est"
            " donc envoyé quels que soient vos réglages d'e-mails."
        ),
    },
    "top_up_price_change": {
        "subject": "Nouveau prix de recharge pour {company}",
        "preheader": (
            "À partir du {date}, chaque recharge automatique coûte {new_price} au lieu de {price}."
        ),
        "heading": "Le prix de la recharge automatique change",
        "lines": [
            (
                "À partir du {date}, chaque recharge automatique pour {company} coûte {new_price} "
                "au lieu de {price}, hors TVA ou taxe de vente là où elle s'applique. Elle couvre "
                "toujours le même nombre de candidats."
            ),
            (
                "Les débits d'ici là coûtent toujours {price}. Si vous souhaitez un autre "
                "montant, modifiez ou désactivez la recharge automatique sur la page Facturation "
                "avant le {date}."
            ),
        ],
        "button": "Ouvrir la facturation",
        "footer": (
            "Cet e-mail a été envoyé à {email} parce que vous êtes propriétaire ou admin de"
            " {company} sur prepza. Il concerne la facturation de votre entreprise ; il est"
            " donc envoyé quels que soient vos réglages d'e-mails."
        ),
    },
    "footer": "Cet e-mail a été envoyé à {email} parce que quelqu'un a invité cette adresse sur "
    "prepza. Si vous ne l'attendiez pas, vous pouvez l'ignorer.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza n'a pas vérifié {company}.",
    "paste_link": "Ou collez ce lien dans votre navigateur",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Se désabonner",
    "email_settings": "Modifier vos préférences d'e-mail",
    "stop_reminders": "Ne plus m'envoyer de rappels pour cet entretien",
    "stop_company": "Ne plus m'envoyer d'e-mails de la part de {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza est exploitée par {name}, {address}.",
}
