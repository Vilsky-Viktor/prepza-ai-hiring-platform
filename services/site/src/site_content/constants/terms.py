from site_content.constants.legal import COMPANY

# The terms of use, in English only: it's a legal text, and a translation would need its own
# legal review. The FAQ page's chat answers from it too.
TERMS_INTRO = f"These terms apply when you use prepza, a service of {COMPANY['name']} (registry code {COMPANY['registry_code']}), {COMPANY['address']}. By signing in, you agree to them. prepza.ai also shows this document in other languages; only this English version is binding, and where a translation differs, the English version applies."

TERMS_SECTIONS = [
    {
        "heading": "Your account",
        "paragraphs": [
            "You sign in with Google, LinkedIn or GitHub (one account per email, whichever you use) and are responsible for what happens in your account. You can delete it at any time in Settings.",
            "We send you service emails, such as invites, reports, billing problems and changes to these terms. You choose which other emails you get in Settings, under Emails, and every one of them has an unsubscribe link.",
        ],
    },
    {
        "heading": "The service and its limits",
        "items": [
            "Questions and answers are written by AI and can be wrong. We check and improve them continuously, and a company reviews its interviews before inviting candidates, but a result is one input for a hiring decision, not a qualification.",
            "The assistant and the help chat also answer with AI and can be wrong: check what matters before relying on it. The assistant changes something only after you confirm it. AI apps you connect, such as Claude or ChatGPT, are run by their own providers, who are responsible for what they say and do.",
        ],
    },
    {
        "heading": "Your content",
        "paragraphs": [
            "You keep the rights to what you paste and create. You let us store and process it to run prepza, including sending it to the AI services we use. You also give us a worldwide, royalty-free, perpetual licence to use, adapt and reuse the questions prepza generates for you in interviews and practice for other customers, without anything that identifies you, your company or anyone else; you can keep an interview's questions out of this in its settings, and questions already reused stay where they are. We also learn general, anonymised patterns of question quality from all questions to improve how questions are generated. Don't paste trade secrets or personal data into a job description.",
        ],
    },
    {
        "heading": "Fair use",
        "items": [
            "Don't use prepza to send unwanted email, to scrape it, or to overload or attack it.",
            "Don't try to get around limits, security or another user's access.",
            "In an interview, answer on your own and follow its rules; the company sees how long each answer took, when you left the page and when you copied text. Before you start, you confirm you'll answer on your own, and the company sees that you did.",
        ],
    },
    {
        "heading": "Companies",
        "paragraphs": [
            "A company using prepza to interview candidates is responsible for inviting candidates lawfully, for telling them how their results are used, and for its hiring decisions. We process candidates' data on the company's behalf, under the data processing agreement at prepza.ai/dpa.",
        ],
        "items": [
            "A company's logo must be one it has the right to use.",
            "The verified check means that an owner or admin signed in with a work email on the company's website. It doesn't mean we vouch for the company.",
            "Anyone with an interview's shareable link can take the interview, and each person who does is charged like an invited candidate. The company decides where it shares the link.",
            "A company that sends a report is responsible for whom it sends it to.",
            "Results support a company's decision; they don't make it. A company reviews them before deciding, doesn't reject a candidate on the score alone, and lets a candidate ask for a person to review their result.",
            "A company gives a candidate who needs it an accommodation, such as extra time, which it can set for each candidate before they start.",
            "A company that connects its own tools (an applicant tracking system, Slack, or its systems through prepza's API and web hooks) chooses where its candidates' results go and is responsible for those tools, and doesn't set them up to reject candidates automatically on prepza's results.",
            "API keys and web hooks' secrets are the company's to keep secret: anything done with a valid key is done for the company, as if by the member who made it. A key or web hook that may have leaked should be deleted at once on the company's API page.",
            "The data processing agreement at prepza.ai/dpa forms part of these terms for every company that uses prepza for candidates.",
            "Until prepza has an independent bias audit, a company may not use it to assess candidates for jobs in New York City, where Local Law 144 requires one.",
        ],
    },
    {
        "heading": "Practice",
        "items": [
            "Practice interviews are free, and their results are private to you.",
        ],
    },
    {
        "heading": "Credits and payments",
        "items": [
            "prepza is paid with credits: each top-up buys the number of credits shown before you pay, and larger top-ups buy more credits for the money. What each thing costs in credits is on the pricing page and is shown before you use it.",
            "Top-ups are sold by Paddle, who acts as the reseller (merchant of record): Paddle takes the payment, charges any VAT or sales tax, and issues the receipt or invoice. Businesses and consumers can both buy them. The prices on the pricing page don't include VAT or sales tax: where it applies, Paddle adds it at checkout, on top of the listed price. Prices are in the local currency in Canada (Canadian dollars), Australia (Australian dollars), Israel (shekels), Poland (zlotys), Switzerland (Swiss francs), Japan (yen), South Korea (won), Taiwan (New Taiwan dollars), Hong Kong (Hong Kong dollars), Thailand (baht), Singapore (Singapore dollars) and India (rupees); in euros in the rest of the European Union and in Iceland, Liechtenstein and Norway; in pounds sterling in the United Kingdom; and in US dollars elsewhere. A company pays in its own currency, first set from the country it was created in and changeable by its owners and admins; the checkout shows the final amount, with any tax, before you pay. If your card is in another currency, your bank or card issuer may convert the amount.",
            "Credits belong to a company and are used for its candidates; its owner and admins can top them up. Credits can't be transferred between accounts or companies, sold, or paid out as money.",
            "Automatic top-up is optional and off unless you turn it on. When you turn it on, you authorise Paddle to save your card and to charge it the top-up amount you chose each time the available balance falls under the level you chose, without asking again. Paddle emails a receipt for every charge. You can change or turn it off at any time on the top-up page, which also cancels the saved card's authorisation; charges already made follow the refund rules below.",
            "Credits don't expire. Deleting a company deletes its credits, and they aren't refunded: ask for any refund you're due before deleting it.",
            "Referrals: when a company created through your company's link first tops up, of any amount, both companies get the referral credits shown on the pricing page, for up to 25 referrals a year. Referring your own companies doesn't count, and we may withhold referral credits obtained by abuse.",
            "Some credits are free: the welcome credits, top-up bonuses, referral credits and similar gifts. They are given once, as described on the pricing page, and are never refunded or paid out. Free credits are used before paid ones.",
            "Credits are only charged for what works: a candidate who never starts or answers nothing costs nothing, and the credits set aside for them come back. Generating interviews is free.",
            "Refunds: you can ask for a refund of credits you bought in the last 14 days and haven't spent, through Paddle or by writing to us. Once you start using credits you bought, you agree that the service begins at once, and spent credits can't be refunded.",
            "If a payment is refunded or reversed by your bank, the credits it bought are removed. If they were already spent, your balance can go below zero, and credits can't be used until a top-up brings it back up.",
            "We may change prices, in money or in credits, and the top-up amounts, for future purchases. Changes apply from when they are shown on the pricing page and never take away credits you already have. If a change affects the amount an automatic top-up charges, we email the company's owner and admins at least 30 days before it applies, and they can change or turn off automatic top-up before then.",
        ],
    },
    {
        "heading": "Availability and changes",
        "paragraphs": [
            "We work to keep prepza available and safe but can't promise it will always be. We may change or stop features, and may suspend accounts that break these terms. We email you about a significant change to these terms at least 14 days before it applies; using prepza after that day means you accept the new terms. Every earlier version stays readable on this page.",
        ],
    },
    {
        "heading": "Liability",
        "paragraphs": [
            "prepza is provided as it is. As far as the law allows, we are not liable for indirect losses, and our total liability is limited to what you paid for credits in the last 12 months, or 100 US dollars (or the equivalent in your currency) if you paid nothing. Nothing here limits rights you have as a consumer under the law of your country.",
        ],
    },
    {
        "heading": "Law",
        "paragraphs": [
            f"Estonian law applies, without taking away the mandatory protections of the country you live in. Questions about these terms: {COMPANY['email']}.",
            "A dispute with a business goes to Harju County Court (Harju Maakohus) in Tallinn. As a consumer, you can also go to the courts where you live.",
            f"If you're a consumer, write to us first at {COMPANY['email']}: we answer within 15 days. If we can't agree and you live in Estonia, you can take the dispute to the Consumer Disputes Committee (Tarbijavaidluste komisjon) of the Consumer Protection and Technical Regulatory Authority, ttja.ee, free of charge.",
        ],
    },
]
