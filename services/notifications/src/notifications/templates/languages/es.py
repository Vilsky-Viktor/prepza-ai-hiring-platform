# Email texts in Spanish. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Este correo se envió a {email} porque eres propietario o administrador de una empresa "
    "en prepza."
)

TEXTS = {
    "candidate": {
        "subject": "Invitación a entrevista de {company}",
        "preheader": "Haz «{title}» en prepza. Inicia sesión con {email} para empezar.",
        "heading": "Invitación a una entrevista",
        "lines": [
            "{company} te invita a la entrevista «{title}» en prepza.",
            (
                "Inicia sesión con {email} para empezar. Solo esta dirección puede "
                "hacer la entrevista, y tienes un solo intento."
            ),
        ],
        "button": "Abrir la invitación",
    },
    "joined": {
        "subject": "Tu enlace a «{title}»",
        "preheader": "Si sales de la entrevista, continúa con este enlace. Inicia sesión con {email}.",
        "heading": "Tu enlace a la entrevista",
        "lines": [
            "Empezaste la entrevista «{title}» de {company} en prepza.",
            (
                "Si sales, continúa con este enlace: inicia sesión con {email}. Sigue funcionando "
                "aunque {company} retire el enlace con el que empezaste. El tiempo sigue corriendo "
                "mientras no estás."
            ),
        ],
        "button": "Continuar la entrevista",
        "footer": (
            "Este correo se envió a {email} porque se empezó una entrevista en prepza con esta "
            "dirección."
        ),
    },
    "reminder": {
        "subject": "Recordatorio: tu entrevista con {company}",
        "preheader": "«{title}» sigue abierta. Inicia sesión con {email} para empezar.",
        "heading": "Tu entrevista te espera",
        "lines": [
            (
                "{company} te invitó a la entrevista «{title}» en prepza hace unos días, y aún "
                "no la has empezado."
            ),
            (
                "Inicia sesión con {email} para empezar. Solo esta dirección puede hacer la "
                "entrevista, y tienes un solo intento. La invitación caduca 30 días después de "
                "su envío."
            ),
        ],
        "button": "Abrir la invitación",
    },
    "member": {
        "subject": "Únete a {company} en prepza",
        "preheader": (
            "Únete al equipo de {company} como {role}. Inicia sesión con {email} para aceptar."
        ),
        "heading": "Invitación al equipo",
        "lines": [
            "{inviter} te invita a unirte al equipo de {company} en prepza como {role}.",
            (
                "Inicia sesión con {email} para aceptar. Solo esta dirección puede aceptar la "
                "invitación."
            ),
        ],
        "button": "Abrir la invitación",
        # The role's name as the lines use it.
        "roles": {"admin": "administrador", "viewer": "lector"},
    },
    "report": {
        "subject": "Informe: {candidate}",
        "preheader": "{candidate} hizo «{title}» en {company}. El informe va adjunto.",
        "heading": "Informe de candidato",
        "lines": [
            "{sender} de {company} compartió el informe de {candidate} de la entrevista «{title}».",
            (
                "Va adjunto como PDF de una página: la nota general, la puntuación de cada tema "
                "y lo que registró el navegador del candidato. Responde a este correo para "
                "contestar a {sender}."
            ),
        ],
        "button": "Visitar prepza",
        "footer": "Este correo se envió a {email} porque {sender} compartió un informe de "
        "candidato con esta dirección en prepza. Si no lo esperabas, puedes ignorarlo.",
    },
    "candidates": {
        "subject": "Todos los candidatos: {title}",
        "preheader": "Todos los candidatos de «{title}» en {company}. El informe va adjunto.",
        "heading": "Informe de candidatos",
        "lines": [
            "{sender} de {company} compartió el informe de todos los candidatos de la entrevista «{title}».",
            (
                "Va adjunto como PDF: la nota de cada candidato, su progreso y lo que registró su "
                "navegador, los mejores primero. Responde a este correo para contestar a {sender}."
            ),
        ],
        "button": "Visitar prepza",
        "footer": "Este correo se envió a {email} porque {sender} compartió un informe de "
        "candidatos con esta dirección en prepza. Si no lo esperabas, puedes ignorarlo.",
    },
    "digest": {
        "subject": "Tu resumen de actividad en prepza",
        "preheader": "Lo que pasó en tus empresas en las últimas 24 horas.",
        "heading": "Tu resumen de actividad",
        "lines": [
            "Esto es lo que pasó en tus empresas en prepza en las últimas 24 horas.",
        ],
        "rows": {
            "candidate_finished": "Candidatos que terminaron: {count} · «{title}»",
            "invite_undelivered": "Invitaciones no entregadas: {count} · «{title}»",
            "ats_not_invited": "Candidatos de {ats} no invitados: {count}",
            "interview_ready": "Entrevista lista: «{title}»",
            "note_added": "Nuevos comentarios de tu equipo: {count} · «{title}»",
            "note": "{author}: «{excerpt}»",
            "note_by_former": "Un exmiembro: «{excerpt}»",
        },
        "button": "Abrir prepza",
        "footer": (
            "Este correo se envió a {email} porque eres miembro de una empresa en prepza y "
            "recibes su resumen de actividad."
        ),
    },
    "low_credits": {
        "subject": "Te estás quedando sin créditos",
        "preheader": "Recarga para seguir invitando a candidatos.",
        "heading": "Se están acabando los créditos",
        "lines": [
            (
                "Estas empresas no tienen créditos suficientes para invitar a otro "
                "candidato. Recarga para seguir invitando a candidatos."
            ),
        ],
        "rows": {
            "company": "{company} · créditos disponibles: {available}",
        },
        "button": "Recargar",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Esperando candidatos",
        "preheader": "Invita a candidatos por correo o comparte el enlace de la entrevista.",
        "heading": "Esperando candidatos",
        "lines": [
            (
                "Estas entrevistas están listas desde hace unos días, pero aún no se ha "
                "invitado a nadie. Invita a candidatos por correo o comparte el enlace de "
                "la entrevista."
            ),
        ],
        "rows": {
            "interview": "«{title}» · {company}",
        },
        "button": "Invitar a candidatos",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Tus temas esperan tu revisión",
        "preheader": "Confirma los temas y se generarán las preguntas.",
        "heading": "Revisa tus temas",
        "lines": [
            (
                "Los temas de las entrevistas que iniciaste esperan tu revisión. Cuando los"
                " confirmes, se generarán las preguntas. Una revisión que quede abierta 14 "
                "días se cancela."
            ),
        ],
        "rows": {
            "interview": "{company} · días de espera: {days}",
        },
        "button": "Revisar los temas",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Nuevos términos desde el {date}",
        "preheader": "Los nuevos términos se aplican a partir del {date}.",
        "heading": "Actualizamos nuestros términos",
        "lines": [
            (
                "Hemos publicado una nueva versión de los términos de prepza. Se aplica a partir "
                "del {date}; hasta entonces, se aplican los términos actuales."
            ),
            (
                "Si usas prepza después del {date}, aceptas los nuevos términos. Si no los "
                "aceptas, puedes eliminar tu cuenta en Ajustes antes de esa fecha."
            ),
        ],
        "button": "Leer los nuevos términos",
        "footer": (
            "Este correo se envió a {email} porque tienes una cuenta en prepza. Es un aviso "
            "sobre nuestros términos, así que se envía sin importar tu configuración de "
            "correo."
        ),
    },
    "legal_privacy": {
        "subject": "Nueva política de privacidad desde el {date}",
        "preheader": "La nueva política de privacidad se aplica a partir del {date}.",
        "heading": "Actualizamos nuestra política de privacidad",
        "lines": [
            (
                "Hemos publicado una nueva versión de la política de privacidad de prepza, que "
                "explica cómo usamos tus datos. Se aplica a partir del {date}; hasta entonces, se "
                "aplica la actual."
            ),
            "Puedes descargar o eliminar tus datos en Ajustes en cualquier momento.",
        ],
        "button": "Leer la nueva política de privacidad",
        "footer": (
            "Este correo se envió a {email} porque tienes una cuenta en prepza. Es un aviso "
            "sobre cómo usamos tus datos, así que se envía sin importar tu configuración de "
            "correo."
        ),
    },
    "legal_dpa": {
        "subject": "Nuevo acuerdo de tratamiento de datos: {date}",
        "preheader": "El nuevo acuerdo se aplica a tu empresa a partir del {date}.",
        "heading": "Actualizamos nuestro acuerdo de tratamiento de datos",
        "lines": [
            (
                "Hemos publicado una nueva versión del acuerdo de tratamiento de datos según el "
                "cual prepza trata los datos de tus candidatos. Se aplica a partir del {date}; "
                "hasta entonces, se aplica el actual."
            ),
            (
                "Una empresa que se oponga por motivos razonables de protección de datos puede "
                "dejar de usar prepza y eliminar su empresa antes de esa fecha."
            ),
        ],
        "button": "Leer el nuevo acuerdo",
        "footer": (
            "Este correo se envió a {email} porque eres propietario o administrador de una "
            "empresa en prepza. Es un aviso sobre nuestro acuerdo con tu empresa, así que se "
            "envía sin importar tu configuración de correo."
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
        "open_site": "Abrir prepza",
        "footer": (
            "Este correo se envió a {email} porque elegiste recibir novedades del producto de"
            " prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Abrir prepza",
        "footer": (
            "Este correo se envió a {email} porque elegiste recibir ofertas y promociones de"
            " prepza."
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
        "open_site": "Abrir prepza",
        "footer": (
            "Este correo se envió a {email} porque tienes una cuenta en prepza. Es un aviso"
            " importante sobre el servicio, como su seguridad o disponibilidad, así que se"
            " envía sin importar tu configuración de correo."
        ),
    },
    "top_up_failed": {
        "subject": "Recarga automática fallida: {company}",
        "preheader": "No se pudo cobrar a la tarjeta. Recarga para seguir invitando a candidatos.",
        "heading": "Falló la recarga automática",
        "lines": [
            (
                "La recarga automática no pudo cobrar a la tarjeta de {company}, así que no"
                " se añadieron créditos."
            ),
            (
                "Recarga para seguir invitando a candidatos. La recarga automática volverá "
                "a intentarlo con la tarjeta más tarde."
            ),
        ],
        "button": "Recargar",
        "footer": (
            "Este correo se envió a {email} porque eres propietario o administrador de "
            "{company} en prepza. Trata sobre la facturación de tu empresa, así que se "
            "envía sin importar tu configuración de correo."
        ),
    },
    "top_up_paused": {
        "subject": "Recarga automática en pausa: {company}",
        "preheader": (
            "La tarjeta fue rechazada. Actualízala para volver a activar la recarga automática."
        ),
        "heading": "La recarga automática está en pausa",
        "lines": [
            (
                "La tarjeta de la recarga automática de {company} fue rechazada y volver a "
                "intentarlo no servirá, así que la recarga automática está en pausa y no hará "
                "cargos en ella."
            ),
            (
                "Actualiza la tarjeta en la página de facturación para volver a activar la "
                "recarga automática. Mientras tanto, recarga manualmente para seguir invitando a "
                "candidatos."
            ),
        ],
        "button": "Actualizar la tarjeta",
        "footer": (
            "Este correo se envió a {email} porque eres propietario o administrador de "
            "{company} en prepza. Trata sobre la facturación de tu empresa, así que se "
            "envía sin importar tu configuración de correo."
        ),
    },
    "top_up_on": {
        "subject": "Recarga automática activada: {company}",
        "preheader": (
            "{price} más impuestos cada vez que los créditos disponibles bajen de {threshold}."
        ),
        "heading": "La recarga automática está activada",
        "lines": [
            (
                "La recarga automática ya está activada para {company}. Cada vez que sus créditos "
                "disponibles bajen de {threshold}, se cargarán {price} a la tarjeta guardada, más "
                "el IVA o el impuesto sobre las ventas donde corresponda, hasta que se desactive "
                "la recarga automática."
            ),
            (
                "Cada cargo se notifica por correo a los propietarios y administradores de la "
                "empresa, y Paddle, nuestro revendedor, envía su recibo por correo."
            ),
            (
                "Para desactivarla, abre la recarga automática en la página de facturación y "
                "elige «Desactivar». Se detiene al instante y no se cobra nada más."
            ),
        ],
        "button": "Abrir facturación",
        "footer": (
            "Este correo se envió a {email} porque eres propietario o administrador de "
            "{company} en prepza. Trata sobre la facturación de tu empresa, así que se envía "
            "sin importar tu configuración de correo."
        ),
    },
    "top_up_charged": {
        "subject": "Recarga automática cobrada: {company}",
        "preheader": "{price} por {credits} créditos el {date}.",
        "heading": "La recarga automática cobró a la tarjeta",
        "lines": [
            (
                "El {date}, la recarga automática cobró {price}, impuestos incluidos, a la "
                "tarjeta de {company} y añadió {credits} créditos. {company} tiene ahora "
                "{available} créditos disponibles."
            ),
            "Paddle, nuestro revendedor, envía el recibo por correo.",
            (
                "Para detener estos cargos, abre la recarga automática en la página de "
                "facturación y elige «Desactivar». Se detiene al instante y no se cobra nada más."
            ),
        ],
        "button": "Abrir facturación",
        "footer": (
            "Este correo se envió a {email} porque eres propietario o administrador de "
            "{company} en prepza. Trata sobre la facturación de tu empresa, así que se envía "
            "sin importar tu configuración de correo."
        ),
    },
    "top_up_price_change": {
        "subject": "Nuevo precio de recarga para {company}",
        "preheader": (
            "Desde el {date}, cada recarga automática cuesta {new_price} en lugar de {price}."
        ),
        "heading": "Cambia el precio de la recarga automática",
        "lines": [
            (
                "Desde el {date}, cada recarga automática de {company} cuesta {new_price} en "
                "lugar de {price}, más el IVA o el impuesto sobre las ventas donde corresponda. "
                "Incluye el mismo número de candidatos."
            ),
            (
                "Los cargos anteriores a esa fecha siguen costando {price}. Si prefieres otro "
                "importe, cambia o desactiva la recarga automática en la página de facturación "
                "antes del {date}."
            ),
        ],
        "button": "Abrir facturación",
        "footer": (
            "Este correo se envió a {email} porque eres propietario o administrador de "
            "{company} en prepza. Trata sobre la facturación de tu empresa, así que se "
            "envía sin importar tu configuración de correo."
        ),
    },
    "footer": "Este correo se envió a {email} porque alguien invitó a esta dirección en prepza. "
    "Si no lo esperabas, puedes ignorarlo.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza no ha verificado {company}.",
    "paste_link": "O pega este enlace en tu navegador",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Cancelar la suscripción",
    "email_settings": "Cambiar tu configuración de correo",
    "stop_reminders": "No enviarme más recordatorios de esta entrevista",
    "stop_company": "No enviarme más correos de {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza está gestionada por {name}, {address}.",
}
