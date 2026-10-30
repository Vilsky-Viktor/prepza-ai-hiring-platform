# Email texts in Portuguese. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Este e-mail foi enviado para {email} porque você é proprietário ou administrador de "
    "uma empresa na prepza."
)

TEXTS = {
    "candidate": {
        "subject": "Convite para entrevista de {company}",
        "preheader": "Faça “{title}” na prepza. Entre com {email} para começar.",
        "heading": "Convite para entrevista",
        "lines": [
            "{company} convida você para a entrevista “{title}” na prepza.",
            (
                "Entre com {email} para começar. Só este endereço pode fazer a "
                "entrevista, e você tem uma única tentativa."
            ),
        ],
        "button": "Abrir o convite",
    },
    "joined": {
        "subject": "Seu link para “{title}”",
        "preheader": "Se você sair da entrevista, continue com este link. Entre com {email}.",
        "heading": "Seu link da entrevista",
        "lines": [
            "Você começou a entrevista “{title}” da {company} na prepza.",
            (
                "Se você sair, continue com este link: entre com {email}. Ele continua funcionando "
                "mesmo que a {company} desative o link pelo qual você começou. O tempo continua "
                "correndo enquanto você estiver fora."
            ),
        ],
        "button": "Continuar a entrevista",
        "footer": (
            "Este e-mail foi enviado para {email} porque uma entrevista foi iniciada na prepza "
            "com este endereço."
        ),
    },
    "reminder": {
        "subject": "Lembrete: sua entrevista com {company}",
        "preheader": "“{title}” ainda está aberta. Entre com {email} para começar.",
        "heading": "Sua entrevista está esperando",
        "lines": [
            (
                "{company} convidou você para a entrevista “{title}” na prepza há alguns dias, e "
                "você ainda não começou."
            ),
            (
                "Entre com {email} para começar. Só este endereço pode fazer a entrevista, e você "
                "tem uma única tentativa. O convite expira 30 dias depois de enviado."
            ),
        ],
        "button": "Abrir o convite",
    },
    "member": {
        "subject": "Entre na equipe de {company} na prepza",
        "preheader": (
            "Faça parte da equipe de {company} como {role}. Entre com {email} para aceitar."
        ),
        "heading": "Convite para a equipe",
        "lines": [
            "{inviter} convida você para fazer parte da equipe de {company} na prepza como {role}.",
            "Entre com {email} para aceitar. Só este endereço pode aceitar o convite.",
        ],
        "button": "Abrir o convite",
        # The role's name as the lines use it.
        "roles": {"admin": "administrador", "viewer": "visualizador"},
    },
    "report": {
        "subject": "Relatório: {candidate}",
        "preheader": "{candidate} fez “{title}” na {company}. O relatório está anexado.",
        "heading": "Relatório do candidato",
        "lines": [
            "{sender}, da {company}, compartilhou o relatório de {candidate} na entrevista “{title}”.",
            (
                "Ele está anexado como um PDF de uma página: a nota geral, a pontuação de cada "
                "tópico e o que o navegador do candidato registrou. Responda a este e-mail para "
                "falar com {sender}."
            ),
        ],
        "button": "Acessar a prepza",
        "footer": "Este e-mail foi enviado para {email} porque {sender} compartilhou um relatório "
        "de candidato com este endereço na prepza. Se você não esperava por ele, pode ignorá-lo.",
    },
    "candidates": {
        "subject": "Todos os candidatos: {title}",
        "preheader": "Todos os candidatos de “{title}” na {company}. O relatório está anexado.",
        "heading": "Relatório de candidatos",
        "lines": [
            "{sender}, da {company}, compartilhou o relatório de todos os candidatos da entrevista “{title}”.",
            (
                "Ele está anexado como PDF: a nota, o progresso e o que o navegador de cada candidato "
                "registrou, dos melhores para os demais. Responda a este e-mail para falar com {sender}."
            ),
        ],
        "button": "Acessar a prepza",
        "footer": "Este e-mail foi enviado para {email} porque {sender} compartilhou um relatório "
        "de candidatos com este endereço na prepza. Se você não esperava por ele, pode ignorá-lo.",
    },
    "digest": {
        "subject": "Seu resumo de atividades na prepza",
        "preheader": "O que aconteceu nas suas empresas nas últimas 24 horas.",
        "heading": "Seu resumo de atividades",
        "lines": [
            "Veja o que aconteceu nas suas empresas na prepza nas últimas 24 horas.",
        ],
        "rows": {
            "candidate_finished": "Candidatos que concluíram: {count} · “{title}”",
            "invite_undelivered": "Convites não entregues: {count} · “{title}”",
            "ats_not_invited": "Candidatos de {ats} não convidados: {count}",
            "interview_ready": "Entrevista pronta: “{title}”",
            "note_added": "Novas anotações da sua equipe: {count} · “{title}”",
            "note": "{author}: “{excerpt}”",
            "note_by_former": "Um ex-membro: “{excerpt}”",
        },
        "button": "Abrir a prepza",
        "footer": (
            "Este e-mail foi enviado para {email} porque você é membro de uma empresa no "
            "prepza e recebe o resumo de atividades dela."
        ),
    },
    "low_credits": {
        "subject": "Seus créditos estão acabando",
        "preheader": "Recarregue para continuar convidando candidatos.",
        "heading": "Os créditos estão acabando",
        "lines": [
            (
                "Estas empresas não têm créditos suficientes para convidar outro candidato."
                " Recarregue para continuar convidando candidatos."
            ),
        ],
        "rows": {
            "company": "{company} · créditos disponíveis: {available}",
        },
        "button": "Recarregar",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Aguardando candidatos",
        "preheader": "Convide candidatos por e-mail ou compartilhe o link da entrevista.",
        "heading": "Aguardando candidatos",
        "lines": [
            (
                "Estas entrevistas estão prontas há alguns dias, mas ninguém foi convidado "
                "ainda. Convide candidatos por e-mail ou compartilhe o link da entrevista."
            ),
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "Convidar candidatos",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Seus tópicos estão aguardando revisão",
        "preheader": "Confirme os tópicos e as perguntas serão geradas.",
        "heading": "Revise seus tópicos",
        "lines": [
            (
                "Os tópicos das entrevistas que você iniciou estão aguardando sua revisão. "
                "Assim que você os confirmar, as perguntas serão geradas. Uma revisão "
                "deixada aberta por 14 dias é cancelada."
            ),
        ],
        "rows": {
            "interview": "{company} · dias aguardando: {days}",
        },
        "button": "Revisar os tópicos",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Novos termos de uso em {date}",
        "preheader": "Os novos termos de uso valem a partir de {date}.",
        "heading": "Estamos atualizando nossos termos de uso",
        "lines": [
            (
                "Publicamos uma nova versão dos termos de uso da prepza. Ela vale a partir de "
                "{date}; até lá, valem os termos atuais."
            ),
            (
                "Ao usar a prepza depois de {date}, você aceita os novos termos. Se não aceitar, "
                "pode excluir sua conta em Configurações antes dessa data."
            ),
        ],
        "button": "Ler os novos termos",
        "footer": (
            "Este e-mail foi enviado para {email} porque você tem uma conta na prepza. É um "
            "aviso sobre nossos termos de uso, por isso é enviado independentemente das suas "
            "configurações de e-mail."
        ),
    },
    "legal_privacy": {
        "subject": "Nova política de privacidade em {date}",
        "preheader": "A nova política de privacidade vale a partir de {date}.",
        "heading": "Estamos atualizando nossa política de privacidade",
        "lines": [
            (
                "Publicamos uma nova versão da política de privacidade da prepza, que explica "
                "como usamos seus dados. Ela vale a partir de {date}; até lá, vale a atual."
            ),
            "Você pode baixar ou excluir seus dados em Configurações a qualquer momento.",
        ],
        "button": "Ler a nova política de privacidade",
        "footer": (
            "Este e-mail foi enviado para {email} porque você tem uma conta na prepza. É um "
            "aviso sobre como usamos seus dados, por isso é enviado independentemente das "
            "suas configurações de e-mail."
        ),
    },
    "legal_dpa": {
        "subject": "Novo acordo de tratamento de dados em {date}",
        "preheader": "O novo acordo vale para sua empresa a partir de {date}.",
        "heading": "Estamos atualizando nosso acordo de tratamento de dados",
        "lines": [
            (
                "Publicamos uma nova versão do acordo de tratamento de dados segundo o qual a "
                "prepza trata os dados dos seus candidatos. Ela vale a partir de {date}; até lá, "
                "vale o atual."
            ),
            (
                "Uma empresa que se oponha por motivos razoáveis de proteção de dados pode deixar "
                "de usar a prepza e excluir a empresa antes dessa data."
            ),
        ],
        "button": "Ler o novo acordo",
        "footer": (
            "Este e-mail foi enviado para {email} porque você é proprietário ou administrador "
            "de uma empresa na prepza. É um aviso sobre nosso acordo com sua empresa, por "
            "isso é enviado independentemente das suas configurações de e-mail."
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
        "open_site": "Abrir a prepza",
        "footer": (
            "Este e-mail foi enviado para {email} porque você escolheu receber novidades do produto"
            " e notícias da prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Abrir a prepza",
        "footer": (
            "Este e-mail foi enviado para {email} porque você escolheu receber ofertas e promoções"
            " da prepza."
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
        "open_site": "Abrir a prepza",
        "footer": (
            "Este e-mail foi enviado para {email} porque você tem uma conta na prepza. É um"
            " aviso importante sobre o serviço, como a segurança ou a disponibilidade dele, por"
            " isso é enviado independentemente das suas configurações de e-mail."
        ),
    },
    "top_up_failed": {
        "subject": "Recarga automática falhou: {company}",
        "preheader": (
            "Não foi possível cobrar o cartão. Recarregue para continuar convidando candidatos."
        ),
        "heading": "A recarga automática falhou",
        "lines": [
            (
                "A recarga automática não conseguiu cobrar o cartão de {company}, então "
                "nenhum crédito foi adicionado."
            ),
            (
                "Recarregue para continuar convidando candidatos. A recarga automática "
                "tentará cobrar o cartão de novo mais tarde."
            ),
        ],
        "button": "Recarregar",
        "footer": (
            "Este e-mail foi enviado para {email} porque você é proprietário ou "
            "administrador de {company} na prepza. Ele trata do faturamento da sua empresa,"
            " por isso é enviado independentemente das suas configurações de e-mail."
        ),
    },
    "top_up_paused": {
        "subject": "Recarga automática pausada: {company}",
        "preheader": "O cartão foi recusado. Atualize-o para reativar a recarga automática.",
        "heading": "A recarga automática está pausada",
        "lines": [
            (
                "O cartão da recarga automática de {company} foi recusado, e tentar de novo não "
                "vai adiantar, então a recarga automática está pausada e não vai cobrá-lo."
            ),
            (
                "Atualize o cartão na página de faturamento para reativar a recarga automática. "
                "Até lá, recarregue manualmente para continuar convidando candidatos."
            ),
        ],
        "button": "Atualizar o cartão",
        "footer": (
            "Este e-mail foi enviado para {email} porque você é proprietário ou "
            "administrador de {company} na prepza. Ele trata do faturamento da sua empresa,"
            " por isso é enviado independentemente das suas configurações de e-mail."
        ),
    },
    "top_up_price_change": {
        "subject": "Novo preço de recarga para {company}",
        "preheader": (
            "A partir de {date}, cada recarga automática custa {new_price} em vez de {price}."
        ),
        "heading": "O preço da recarga automática vai mudar",
        "lines": [
            (
                "A partir de {date}, cada recarga automática de {company} custa {new_price} em "
                "vez de {price}, mais IVA ou imposto sobre vendas onde se aplicar. O número de "
                "candidatos continua o mesmo."
            ),
            (
                "As cobranças até lá continuam custando {price}. Se preferir outro valor, altere "
                "ou desative a recarga automática na página de faturamento antes de {date}."
            ),
        ],
        "button": "Abrir faturamento",
        "footer": (
            "Este e-mail foi enviado para {email} porque você é proprietário ou "
            "administrador de {company} na prepza. Ele trata do faturamento da sua empresa,"
            " por isso é enviado independentemente das suas configurações de e-mail."
        ),
    },
    "footer": "Este e-mail foi enviado para {email} porque alguém convidou este endereço no "
    "prepza. Se você não esperava por ele, pode ignorá-lo.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "A prepza não verificou {company}.",
    "paste_link": "Ou cole este link no seu navegador",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Cancelar inscrição",
    "email_settings": "Alterar suas configurações de e-mail",
    "stop_reminders": "Não me enviar lembretes desta entrevista",
    "stop_company": "Não me enviar e-mails de {company}",
    # Who runs prepza, at the end of every email.
    "operator": "A prepza é operada pela {name}, {address}.",
}
