# Email texts in Filipino. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Ipinadala ang email na ito sa {email} dahil ikaw ay may-ari o admin ng isang kumpanya "
    "sa prepza."
)

TEXTS = {
    "candidate": {
        "subject": "Imbitasyon sa interview mula sa {company}",
        "preheader": "Sagutan ang “{title}” sa prepza. Mag-sign in gamit ang {email} "
        "para magsimula.",
        "heading": "Imbitasyon sa interview",
        "lines": [
            "Iniimbitahan ka ng {company} sa interview na “{title}” sa prepza.",
            (
                "Mag-sign in gamit ang {email} para magsimula. Ang address na ito "
                "lang ang puwedeng sumagot sa interview, at may isang pagkakataon ka "
                "lang."
            ),
        ],
        "button": "Buksan ang imbitasyon",
    },
    "joined": {
        "subject": "Ang link mo sa “{title}”",
        "preheader": (
            "Kung aalis ka sa interview, ituloy ito gamit ang link na ito. Mag-sign in gamit "
            "ang {email}."
        ),
        "heading": "Ang link ng interview mo",
        "lines": [
            "Sinimulan mo ang interview na “{title}” ng {company} sa prepza.",
            (
                "Kung aalis ka, ituloy ito gamit ang link na ito: mag-sign in gamit ang {email}. "
                "Gagana pa rin ito kahit i-off ng {company} ang link kung saan ka nagsimula. "
                "Patuloy na tumatakbo ang oras habang wala ka."
            ),
        ],
        "button": "Ituloy ang interview",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil may sinimulang interview sa prepza gamit "
            "ang address na ito."
        ),
    },
    "reminder": {
        "subject": "Paalala: ang interview mo sa {company}",
        "preheader": "Bukas pa ang “{title}”. Mag-sign in gamit ang {email} para magsimula.",
        "heading": "Naghihintay ang iyong interview",
        "lines": [
            (
                "Inimbitahan ka ng {company} sa interview na “{title}” sa prepza ilang araw na "
                "ang nakalipas, at hindi mo pa ito nasisimulan."
            ),
            (
                "Mag-sign in gamit ang {email} para magsimula. Ang address na ito lang ang "
                "puwedeng sumagot sa interview, at may isang pagkakataon ka lang. Mag-e-expire "
                "ang imbitasyon 30 araw matapos itong ipadala."
            ),
        ],
        "button": "Buksan ang imbitasyon",
    },
    "member": {
        "subject": "Sumali sa {company} sa prepza",
        "preheader": (
            "Sumali sa team ng {company} bilang {role}. Mag-sign in gamit ang {email} para "
            "tanggapin."
        ),
        "heading": "Imbitasyon sa team",
        "lines": [
            "Iniimbitahan ka ni {inviter} na sumali sa team ng {company} sa prepza bilang {role}.",
            (
                "Mag-sign in gamit ang {email} para tanggapin ito. Ang address na ito lang ang "
                "puwedeng tumanggap sa imbitasyon."
            ),
        ],
        "button": "Buksan ang imbitasyon",
        # The role's name as the lines use it.
        "roles": {"admin": "admin", "viewer": "viewer"},
    },
    "report": {
        "subject": "Report: {candidate}",
        "preheader": "Sinagutan ni {candidate} ang “{title}” sa {company}. Naka-attach ang report.",
        "heading": "Report ng aplikante",
        "lines": [
            "Ibinahagi ni {sender} mula sa {company} ang report ni {candidate} para sa interview na “{title}”.",
            (
                "Naka-attach ito bilang isang pahinang PDF: ang kabuuang grade, ang score sa "
                "bawat topic at ang ipinakita ng browser ng aplikante. Mag-reply sa email na ito "
                "para sumagot kay {sender}."
            ),
        ],
        "button": "Bisitahin ang prepza",
        "footer": "Ipinadala ang email na ito sa {email} dahil nag-share si {sender} ng report ng "
        "aplikante sa address na ito sa prepza. Kung hindi mo ito inaasahan, puwede mo itong "
        "balewalain.",
    },
    "candidates": {
        "subject": "Lahat ng aplikante: {title}",
        "preheader": "Lahat ng aplikante para sa “{title}” sa {company}. Naka-attach ang report.",
        "heading": "Report ng mga aplikante",
        "lines": [
            "Ibinahagi ni {sender} mula sa {company} ang report ng lahat ng aplikante para sa interview na “{title}”.",
            (
                "Naka-attach ito bilang PDF: ang grade, progreso at ipinakita ng browser ng bawat "
                "aplikante, simula sa pinakamahusay. Mag-reply sa email na ito para sumagot kay "
                "{sender}."
            ),
        ],
        "button": "Bisitahin ang prepza",
        "footer": "Ipinadala ang email na ito sa {email} dahil nag-share si {sender} ng report ng "
        "mga aplikante sa address na ito sa prepza. Kung hindi mo ito inaasahan, puwede mo itong "
        "balewalain.",
    },
    "digest": {
        "subject": "Ang iyong buod ng aktibidad sa prepza",
        "preheader": "Ang nangyari sa mga kumpanya mo sa nakalipas na 24 oras.",
        "heading": "Ang iyong buod ng aktibidad",
        "lines": [
            "Narito ang nangyari sa mga kumpanya mo sa prepza sa nakalipas na 24 oras.",
        ],
        "rows": {
            "candidate_finished": "Mga aplikanteng nakatapos: {count} · “{title}”",
            "invite_undelivered": "Mga imbitasyong hindi naihatid: {count} · “{title}”",
            "ats_not_invited": "Mga aplikante mula sa {ats} na hindi na-imbitahan: {count}",
            "interview_ready": "Handa na ang interview: “{title}”",
            "note_added": "Mga bagong note ng team mo: {count} · “{title}”",
            "note": "{author}: “{excerpt}”",
            "note_by_former": "Isang dating miyembro: “{excerpt}”",
        },
        "button": "Buksan ang prepza",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil miyembro ka ng isang kumpanya sa "
            "prepza at natatanggap mo ang buod ng aktibidad nito."
        ),
    },
    "low_credits": {
        "subject": "Paubos na ang iyong mga credit",
        "preheader": "Mag-top up para patuloy na makapag-imbita ng aplikante.",
        "heading": "Paubos na ang mga credit",
        "lines": [
            (
                "Kulang na ang credits ng mga kumpanyang ito para mag-imbita ng isa pang "
                "aplikante. Mag-top up para patuloy na makapag-imbita ng aplikante."
            ),
        ],
        "rows": {
            "company": "{company} · available na credits: {available}",
        },
        "button": "Mag-top up",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Naghihintay ng mga aplikante",
        "preheader": "Mag-imbita ng mga aplikante sa email o ibahagi ang link ng interview.",
        "heading": "Naghihintay ng mga aplikante",
        "lines": [
            (
                "Ilang araw nang handa ang mga interview na ito, pero wala pang "
                "naiimbitahan. Mag-imbita ng mga aplikante sa email o ibahagi ang link ng "
                "interview."
            ),
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "Mag-imbita ng mga aplikante",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Naghihintay ng review ang iyong mga topic",
        "preheader": "Kumpirmahin ang mga topic, at gagawin na ang mga tanong.",
        "heading": "I-review ang iyong mga topic",
        "lines": [
            (
                "Naghihintay ng iyong review ang mga topic ng mga interview na sinimulan "
                "mo. Kapag kinumpirma mo ang mga ito, gagawin na ang mga tanong. "
                "Kinakansela ang review na nakabukas nang 14 na araw."
            ),
        ],
        "rows": {
            "interview": "{company} · araw na naghihintay: {days}",
        },
        "button": "I-review ang mga topic",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Bagong mga tuntunin simula {date}",
        "preheader": "Ipapatupad ang bagong mga tuntunin simula {date}.",
        "heading": "Ina-update namin ang aming mga tuntunin",
        "lines": [
            (
                "Naglathala kami ng bagong bersyon ng mga tuntunin ng prepza. Ipapatupad ito "
                "simula {date}; hanggang doon, ang kasalukuyang mga tuntunin ang umiiral."
            ),
            (
                "Kapag ginamit mo ang prepza pagkatapos ng {date}, tinatanggap mo ang bagong mga "
                "tuntunin. Kung hindi, puwede mong burahin ang iyong account sa Mga setting bago "
                "ang petsang iyon."
            ),
        ],
        "button": "Basahin ang bagong mga tuntunin",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil may prepza account ka. Abiso ito "
            "tungkol sa aming mga tuntunin, kaya ipinapadala ito anuman ang iyong email "
            "settings."
        ),
    },
    "legal_privacy": {
        "subject": "Bagong patakaran sa privacy simula {date}",
        "preheader": "Ipapatupad ang bagong patakaran sa privacy simula {date}.",
        "heading": "Ina-update namin ang aming patakaran sa privacy",
        "lines": [
            (
                "Naglathala kami ng bagong bersyon ng patakaran sa privacy ng prepza, na "
                "nagsasabi kung paano namin ginagamit ang data mo. Ipapatupad ito simula {date}; "
                "hanggang doon, ang kasalukuyang bersyon ang umiiral."
            ),
            "Puwede mong i-download o burahin ang data mo sa Mga setting anumang oras.",
        ],
        "button": "Basahin ang bagong patakaran sa privacy",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil may prepza account ka. Abiso ito "
            "tungkol sa kung paano namin ginagamit ang data mo, kaya ipinapadala ito anuman "
            "ang iyong email settings."
        ),
    },
    "legal_dpa": {
        "subject": "Bagong data processing agreement simula {date}",
        "preheader": "Ipapatupad sa kumpanya mo ang bagong kasunduan simula {date}.",
        "heading": "Ina-update namin ang aming data processing agreement",
        "lines": [
            (
                "Naglathala kami ng bagong bersyon ng data processing agreement na batayan ng "
                "prepza sa pagproseso ng data ng mga aplikante mo. Ipapatupad ito simula {date}; "
                "hanggang doon, ang kasalukuyang bersyon ang umiiral."
            ),
            (
                "Ang kumpanyang tumututol dahil sa makatwirang dahilan tungkol sa proteksyon ng "
                "data ay puwedeng tumigil sa paggamit ng prepza at burahin ang kumpanya nito bago "
                "ang petsang iyon."
            ),
        ],
        "button": "Basahin ang bagong kasunduan",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil ikaw ay may-ari o admin ng isang "
            "kumpanya sa prepza. Abiso ito tungkol sa kasunduan namin sa kumpanya mo, kaya "
            "ipinapadala ito anuman ang iyong email settings."
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
        "open_site": "Buksan ang prepza",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil pinili mong makatanggap ng mga update at"
            " balita tungkol sa produkto mula sa prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Buksan ang prepza",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil pinili mong makatanggap ng mga alok at"
            " promo mula sa prepza."
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
        "open_site": "Buksan ang prepza",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil may prepza account ka. Mahalagang"
            " abiso ito tungkol sa serbisyo, gaya ng seguridad o availability nito, kaya"
            " ipinapadala ito anuman ang iyong email settings."
        ),
    },
    "top_up_failed": {
        "subject": "Pumalya ang top-up: {company}",
        "preheader": (
            "Hindi ma-charge ang card. Mag-top up para patuloy na makapag-imbita ng aplikante."
        ),
        "heading": "Pumalya ang awtomatikong top-up",
        "lines": [
            (
                "Hindi ma-charge ng awtomatikong top-up ang card para sa {company}, kaya "
                "walang naidagdag na credits."
            ),
            (
                "Mag-top up para patuloy na makapag-imbita ng aplikante. Susubukan ulit ng "
                "awtomatikong top-up ang card mamaya."
            ),
        ],
        "button": "Mag-top up",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil ikaw ay may-ari o admin ng "
            "{company} sa prepza. Tungkol ito sa billing ng kumpanya mo, kaya ipinapadala "
            "ito anuman ang iyong email settings."
        ),
    },
    "top_up_paused": {
        "subject": "Naka-pause ang top-up: {company}",
        "preheader": "Tinanggihan ang card. I-update ito para i-on ulit ang awtomatikong top-up.",
        "heading": "Naka-pause ang awtomatikong top-up",
        "lines": [
            (
                "Tinanggihan ang card para sa awtomatikong top-up ng {company}, at hindi "
                "makakatulong ang pagsubok ulit, kaya naka-pause ang awtomatikong top-up at hindi "
                "nito iti-charge ang card."
            ),
            (
                "I-update ang card sa billing page para i-on ulit ang awtomatikong top-up. "
                "Hanggang doon, mag-top up nang mano-mano para patuloy na makapag-imbita ng "
                "aplikante."
            ),
        ],
        "button": "I-update ang card",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil ikaw ay may-ari o admin ng "
            "{company} sa prepza. Tungkol ito sa billing ng kumpanya mo, kaya ipinapadala "
            "ito anuman ang iyong email settings."
        ),
    },
    "top_up_on": {
        "subject": "Naka-on ang awtomatikong top-up: {company}",
        "preheader": (
            "{price} dagdag ang buwis tuwing bababa ang available na balance sa ilalim ng "
            "{threshold, plural, =1 {# credit} one {# credits} other {# credits}}."
        ),
        "heading": "Naka-on ang awtomatikong top-up",
        "lines": [
            (
                "Naka-on na ang awtomatikong top-up para sa {company}. Tuwing bababa ang "
                "available nitong balance sa ilalim ng {threshold, plural, =1 {# credit} one {# "
                "credits} other {# credits}}, sisingilin ang naka-save na card ng {price}, dagdag "
                "ang VAT o sales tax kung saan ito naaangkop, hanggang i-off ang awtomatikong "
                "top-up."
            ),
            (
                "Ini-email ang bawat singil sa mga may-ari at admin ng kumpanya, at nag-e-email "
                "ng resibo ang Paddle, ang aming reseller."
            ),
            (
                "Para i-off ito, buksan ang awtomatikong top-up sa billing page at piliin ang "
                "“I-off”. Titigil ito agad, at wala nang sisingilin."
            ),
        ],
        "button": "Buksan ang billing",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil ikaw ay may-ari o admin ng {company} "
            "sa prepza. Tungkol ito sa billing ng kumpanya mo, kaya ipinapadala ito anuman "
            "ang iyong email settings."
        ),
    },
    "top_up_charged": {
        "subject": "Nag-charge ang awtomatikong top-up: {company}",
        "preheader": (
            "{price} para sa {credits, plural, =1 {# credit} one {# credits} other {# "
            "credits}} noong {date}."
        ),
        "heading": "Nag-charge sa card ang awtomatikong top-up",
        "lines": [
            (
                "Noong {date}, siningil ng awtomatikong top-up ang card para sa {company} ng "
                "{price}, kasama ang buwis, at nagdagdag ito ng {credits, plural, =1 {# credit} "
                "one {# credits} other {# credits}}. May {available, plural, =1 {# credit} one {# "
                "credits} other {# credits}} na available ngayon ang {company}."
            ),
            "Nag-e-email ng resibo ang Paddle, ang aming reseller.",
            (
                "Para ihinto ang mga singil na ito, buksan ang awtomatikong top-up sa billing "
                "page at piliin ang “I-off”. Titigil ito agad, at wala nang sisingilin."
            ),
        ],
        "button": "Buksan ang billing",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil ikaw ay may-ari o admin ng {company} "
            "sa prepza. Tungkol ito sa billing ng kumpanya mo, kaya ipinapadala ito anuman "
            "ang iyong email settings."
        ),
    },
    "top_up_price_change": {
        "subject": "Bagong presyo ng top-up para sa {company}",
        "preheader": (
            "Simula {date}, {new_price} na ang bawat awtomatikong top-up sa halip na {price}."
        ),
        "heading": "Magbabago ang presyo ng awtomatikong top-up",
        "lines": [
            (
                "Simula {date}, {new_price} na ang bawat awtomatikong top-up para sa {company} sa "
                "halip na {price}, dagdag ang VAT o sales tax kung saan ito naaangkop. Pareho pa "
                "rin ang dami ng aplikanteng saklaw nito."
            ),
            (
                "{price} pa rin ang mga charge bago noon. Kung gusto mo ng ibang halaga, baguhin "
                "o i-off ang awtomatikong top-up sa billing page bago ang {date}."
            ),
        ],
        "button": "Buksan ang billing",
        "footer": (
            "Ipinadala ang email na ito sa {email} dahil ikaw ay may-ari o admin ng "
            "{company} sa prepza. Tungkol ito sa billing ng kumpanya mo, kaya ipinapadala "
            "ito anuman ang iyong email settings."
        ),
    },
    "footer": "Ipinadala ang email na ito sa {email} dahil may nag-imbita sa address na ito sa "
    "prepza. Kung hindi mo ito inaasahan, puwede mo itong balewalain.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "Hindi pa na-verify ng prepza ang {company}.",
    "paste_link": "O i-paste ang link na ito sa iyong browser",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Mag-unsubscribe",
    "email_settings": "Baguhin ang iyong mga setting sa email",
    "stop_reminders": "Huwag na akong padalhan ng paalala para sa interview na ito",
    "stop_company": "Huwag na akong padalhan ng email para sa {company}",
    # Who runs prepza, at the end of every email.
    "operator": "Ang prepza ay pinapatakbo ng {name}, {address}.",
}
