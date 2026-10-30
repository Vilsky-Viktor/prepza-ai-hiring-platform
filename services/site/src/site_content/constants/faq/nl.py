# The FAQ in nl; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Wat is prepza?",
        "answer": "Een interview met tijdslimiet, gemaakt op basis van je functieomschrijving, voor elke functie. Gebruik het om kandidaten te screenen voordat je ze ontmoet, of als stap in de werving zelf: hoe dan ook zie je wie het vak echt kent.",
    },
    {
        "key": "roles",
        "question": "Voor welke functies kan ik werven?",
        "answer": "Elke functie waarin kennis telt: support, sales, financiën, zorg, technische vakken, engineering, marketing en meer. Als je de functie kunt beschrijven, kan prepza er een interview voor maken.",
    },
    {
        "key": "hiring",
        "question": "Hoe werkt het?",
        "answer": "Plak een functieomschrijving op de startpagina, geef je bedrijf een naam en controleer de onderwerpen die prepza voorstelt. Nodig daarna kandidaten uit: typ hun e-mailadressen, plak een lijst of upload een bestand. Kandidaten die na een paar dagen nog niet zijn begonnen, krijgen één herinnering. Elke kandidaat krijgt eigen vragen met een timer bij elke vraag, en je ziet hun score en elk antwoord zodra ze klaar zijn.",
    },
    {
        "key": "link",
        "question": "Kan ik een interview in een vacature zetten?",
        "answer": "Ja. Zet de deelbare link van het interview aan op het tabblad Instellingen en plak hem in je vacature. Iedereen die hem opent, logt in en doet het interview, en je betaalt per persoon hetzelfde als voor een uitgenodigde kandidaat. De link gaat uit wanneer je het interview markeert als aangenomen.",
    },
    {
        "key": "preview",
        "question": "Kan ik een interview proberen voordat ik iemand uitnodig?",
        "answer": "Ja. Open je interview gratis als kandidaat vanaf de pagina ervan: voorbeelden verschijnen niet tussen je kandidaten of in de vraagstatistieken. Je kunt ook elk gratis oefeninterview doen.",
    },
    {
        "key": "open-to-offers",
        "question": "Kunnen bedrijven me vinden via mijn oefeningen?",
        "answer": "Alleen als je daarvoor kiest. Zet Open voor nieuwe kansen aan na een oefenronde of in Instellingen, met het adres van je LinkedIn-profiel. Bedrijven die via prepza werven, zien dan je naam, je LinkedIn-profiel en je nieuwste oefenresultaat op elk onderwerp van hun interviews dat je hebt geoefend, en kunnen je uitnodigen voor een interview. prepza rangschikt je niet en beveelt je niet aan. Zet het op elk moment uit in Instellingen, en je verdwijnt meteen uit de lijst van elk bedrijf; het stopt ook een jaar nadat je het voor het laatst hebt aangezet of je LinkedIn-profiel hebt opgeslagen.",
    },
    {
        "key": "cheating",
        "question": "Kunnen kandidaten AI gebruiken of de antwoorden opzoeken?",
        "answer": "Elke kandidaat krijgt eigen willekeurige vragen in een eigen volgorde, met [een timer bij elke vraag](/guides/skills-test-timing-and-extra-time) die onze server bijhoudt, dus er is weinig tijd om antwoorden op te zoeken of het een AI te vragen. De resultaten laten ook zien wanneer een kandidaat de pagina verliet, tekst kopieerde of te snel antwoordde om de vraag te hebben gelezen. Zodra ze klaar zijn, wijst de pagina van de kandidaat ook op antwoordpatronen die vaak ontstaan als iemand de vragen aan een AI doorgeeft en de antwoorden overneemt, zoals ongeveer even lang bij elke vraag of moeilijke vragen goed terwijl makkelijke fout waren, en stelt vragen voor die de kandidaat goed had, om in een live gesprek op door te vragen. Een patroon is een reden om door te vragen, geen bewijs. Voordat ze beginnen, bevestigt elke kandidaat ook dat die de vragen zelf beantwoordt, zonder AI-tools of hulp van anderen, en de resultaten laten dat zien.",
    },
    {
        "key": "voice",
        "question": "Kunnen kandidaten met hun stem antwoorden?",
        "answer": "Ja, als het bedrijf een interview op spraakmodus zet (in het Engels, Spaans, Duits, Frans, Portugees of Italiaans). De vragen worden voorgelezen en kandidaten antwoorden hardop; wat ze zeggen, wordt omgezet in tekst en gekoppeld aan een optie die ze bevestigen, en wordt nooit opgeslagen. Stemmen worden niet geanalyseerd op toon of emotie, en kandidaten kunnen altijd in plaats daarvan tikken.",
    },
    {
        "key": "cost",
        "question": "Wat kost het?",
        "answer": "Interviews genereren is gratis. Elke kandidaat die minstens één vraag beantwoordt, kost {candidate} credits ({candidate_price}), en minder met credits uit grotere opwaarderingen, tot {cheapest_price}. Je eerste bedrijf krijgt {company} gratis credits, genoeg voor de eerste {company_candidates} kandidaten. De [prijzenpagina](/pricing) toont elke prijs.",
    },
    {
        "key": "charged",
        "question": "Wanneer wordt er voor een kandidaat betaald?",
        "answer": "Als hij minstens één vraag heeft beantwoord: wanneer zijn interview eindigt (hij rondt het af, of de tijd loopt af terwijl hij weg is), of wanneer je hem intrekt. Een vraag waarvan de tijd afliep zonder dat er een antwoord is gekozen, telt niet mee. Zijn credits worden bij de uitnodiging gereserveerd en komen terug als je hem intrekt voordat hij iets beantwoordt, als hij nooit begint of als zijn interview eindigt zonder dat hij iets heeft beantwoord.",
    },
    {
        "key": "compare_hiring",
        "question": "Hoe verhoudt de prijs zich tot andere assessmenttools?",
        "answer": "Veel assessmenttools worden verkocht als maand- of jaarabonnement, dat je ook betaalt als je niemand test. Bij prepza betaal je alleen per kandidaat: {candidate} credits ({candidate_price}), zonder contract, zonder kosten per gebruiker en zonder te betalen voor het maken van een interview. Een bedrijf dat {example_candidates} kandidaten per maand uitnodigt, betaalt ongeveer {example_year_price} per jaar. Test je elke maand veel kandidaten, dan kan een abonnement goedkoper zijn, dus vergelijk met je eigen cijfers.",
    },
    {
        "key": "expire",
        "question": "Verlopen credits?",
        "answer": "Nee. Credits verlopen nooit, en er zijn geen betaalde abonnementen. Zet je het optionele automatisch opwaarderen aan, dan bewaart Paddle je kaart als abonnement van {zero_price}; je betaalt alleen de opwaarderingen die het doet.",
    },
    {
        "key": "currency",
        "question": "In welke valuta betaal ik?",
        "answer": "Prijzen zijn in de lokale valuta in Canada, Australië, Israël, Polen, Zwitserland, Japan, Zuid-Korea, Taiwan, Hongkong, Thailand, Singapore en India; in euro in de rest van de EU en in IJsland, Liechtenstein en Noorwegen; in ponden in het Verenigd Koninkrijk; en elders in Amerikaanse dollars. Je account en elk bedrijf houden de valuta van het land waarin ze zijn aangemaakt, waar je ook naartoe reist: wijzig de jouwe in Instellingen, en die van een bedrijf naast de knop Opwaarderen ervan (eigenaren en beheerders). De opwaarderingen van een bedrijf, ook de automatische, worden altijd in de valuta van het bedrijf in rekening gebracht.",
    },
    {
        "key": "refunds",
        "question": "Kan ik mijn geld terugkrijgen?",
        "answer": "Ja, voor credits die je de afgelopen 14 dagen hebt gekocht en nog niet hebt besteed: via Paddle of door ons te schrijven. Gratis credits, zoals het welkomstcadeau, worden niet terugbetaald. De [voorwaarden](/terms) geven de details.",
    },
    {
        "key": "scorecards",
        "question": "Wat laat een scorekaart zien?",
        "answer": "Elk antwoord, of het goed was en hoe lang het duurde. De score is het percentage behaalde punten: elke vraag is één punt waard, en een vraag waarbij je alle juiste opties aanvinkt levert een deel daarvan op voor elke aangevinkte juiste optie, en niets als er een foute is aangevinkt. Scores zijn groen of rood ten opzichte van de slaaggrens die je voor het interview hebt ingesteld. De scorekaart markeert ook antwoorden die te snel waren om de vraag te hebben gelezen, keren dat de kandidaat de pagina verliet, en kopieerpogingen.",
    },
    {
        "key": "reports",
        "question": "Kan ik resultaten delen met een hiring manager?",
        "answer": "Ja. Download een PDF-rapport voor één kandidaat of voor alle kandidaten van een interview, mail het rechtstreeks vanuit prepza, of stuur een korte samenvatting via WhatsApp, Telegram, Viber of LINE.",
    },
    {
        "key": "action_log",
        "question": "Kan ik zien wie wat heeft gedaan in mijn bedrijf?",
        "answer": "Ja, als je eigenaar van het bedrijf bent. Het tabblad Actielog toont alles wat de leden hebben gedaan, nieuwste eerst: kandidaten uitnodigen of verwijderen, resultaten bekijken, en interviews, het team, de facturering en integraties wijzigen, met wie het deed, wanneer en of de assistent, een AI-app of de API het namens diegene deed. Je kunt filteren op lid, soort actie en datums. Acties worden 12 maanden bewaard. De acties van een API-sleutel staan onder de naam van de sleutel.",
    },
    {
        "key": "notes",
        "question": "Kan mijn team notities bijhouden bij een interview?",
        "answer": "Ja. Elk interview heeft een tabblad Notities waar je team notities in platte tekst schrijft over de wervingsronde, zoals wie jullie hierna bellen of, voor een bureau, voor welke klant het interview is. Elk lid kan notities schrijven, kijkers ook, en de eigen notities bewerken; de schrijver, eigenaren en beheerders kunnen er een verwijderen. Eigenaren en beheerders kunnen één notitie vastzetten, die dan onder de naam van het interview staat. Kandidaten zien notities nooit.",
    },
    {
        "key": "integrations",
        "question": "Werkt prepza met mijn ATS of andere tools?",
        "answer": "Ja, zonder extra kosten. Koppel Workable, Greenhouse, Teamtailor, Recruitee of Breezy HR op het tabblad Integraties van je bedrijf: kandidaten die je naar een fase verplaatst, krijgen het interview, en hun resultaten gaan terug naar het ATS ([zo koppel je vaardigheidstests aan je ATS](/guides/ats-integration-skills-tests)). Slack kan de meldingen van je bedrijf in een kanaal plaatsen, en met de API kan je eigen platform interviews aanmaken, kandidaten uitnodigen en beheren en hun resultaten ontvangen, waarbij elke API-sleutel alleen mag wat je ervoor aanvinkt; zie de [API-documentatie](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Kan ik prepza vanuit Claude, ChatGPT of mijn eigen AI-agent gebruiken?",
        "answer": "Ja. Voeg prepza als connector toe aan Claude of ChatGPT (de stappen staan op het tabblad Integraties van je bedrijf) en sta het toe in prepza. De app werkt dan namens jou en met jouw rechten met je bedrijven, interviews en de resultaten van kandidaten; de meeste apps vragen het je voordat ze iets wijzigen. Je account of een bedrijf verwijder je alleen in prepza. Wat de app leest, gaat naar de aanbieder ervan, onder de voorwaarden van die app. Je kunt de app altijd ontkoppelen op hetzelfde tabblad. Ook andere AI-apps en agents die je zelf bouwt kunnen verbinden: het [MCP-tabblad](/api-docs?tab=mcp) van de ontwikkelaarsdocumentatie heeft de stappen en voorbeeldagents, en een agent op een server kan zich aanmelden met een API-sleutel die het recht voor AI-agents heeft. De [gids over AI-agents, MCP en API's](/guides/ai-agents-mcp-and-api) legt uit waarvoor elk ervan dient.",
    },
    {
        "key": "candidates",
        "question": "Wat zien kandidaten?",
        "answer": "De naam en het logo van je bedrijf, in de kleuren en lettertypen van je bedrijf (ingesteld op het tabblad Merk), wat ze kunnen verwachten voordat ze beginnen, en daarna één vraag met tijdslimiet tegelijk. Ze zien nooit hun score of of een antwoord goed was.",
    },
    {
        "key": "verified",
        "question": "Wat betekent het verificatievinkje?",
        "answer": "Dat een eigenaar of beheerder van het bedrijf heeft ingelogd met een zakelijk e-mailadres op de website van het bedrijf, zoals you@acme.com, en dat ons team het bedrijf daarna heeft beoordeeld. Voeg de website toe met Verifiëren in de kop van je bedrijf; gratis e-maildiensten tellen niet mee. Zolang de beoordeling loopt, ziet je team een klokje naast de naam, en een nieuwe bedrijfsnaam stuurt het opnieuw ter beoordeling. Het vinkje staat naast de naam van je bedrijf, ook in uitnodigingen.",
    },
    {
        "key": "languages",
        "question": "Welke talen worden ondersteund?",
        "answer": "{count} talen, voor de site, de interviews en de e-mails. Kies de taal waarin een interview wordt geschreven, in welke taal de functieomschrijving ook is.",
    },
    {
        "key": "privacy",
        "question": "Wat gebeurt er met functieomschrijvingen en antwoorden?",
        "answer": "Functieomschrijvingen worden gebruikt om de interviews van jouw bedrijf te maken, en de antwoorden van kandidaten om ze voor jouw bedrijf te beoordelen. De vragen die prepza genereert, kunnen ook worden hergebruikt in interviews en oefeninterviews van andere bedrijven, zonder iets wat jou, je bedrijf of iemand anders identificeert; je kunt de vragen van een interview hiervan uitsluiten in de instellingen van dat interview. prepza leidt daarnaast uit hoe vragen worden beantwoord algemene, geanonimiseerde patronen in de kwaliteit van vragen af, om te verbeteren hoe vragen worden gegenereerd. Het [privacybeleid](/privacy) legt uit wat we bewaren, hoe lang en welke rechten iedereen heeft.",
    },
    {
        "key": "eu_ai_law",
        "question": "Is het legaal om AI te gebruiken voor de preselectie van kandidaten in de EU?",
        "answer": "Ja, met regels. Onder de Europese AI-verordening (AI Act) zijn tools die kandidaten beoordelen zeer waarschijnlijk hoog risico, met verplichtingen vanaf 2 december 2027, en de AVG geldt nu al: een mens neemt het besluit om iemand aan te nemen, kandidaten horen dat er AI wordt gebruikt en alles wordt vastgelegd. prepza werkt zo: AI schrijft de vragen, mensen in jouw bedrijf bekijken de resultaten en beslissen, en kandidaten worden geïnformeerd voordat ze beginnen. Dit is geen juridisch advies; [Is AI bij werving en selectie legaal in de EU?](/guides/is-ai-hiring-legal-in-the-eu) legt de regels en de data uit.",
    },
    {
        "key": "uk_us",
        "question": "Kunnen we prepza gebruiken voor kandidaten in het Verenigd Koninkrijk en de VS?",
        "answer": "Ja. De verwerkersovereenkomst dekt het Britse en Amerikaanse recht, en de instructies voor bedrijven en de sjablonen voor kandidaatinformatie (met versies voor New York City, Illinois en Colorado) dekken wat je kandidaten moet vertellen. Voor vacatures in New York City gebruik je het pas als je hebt gedaan wat Local Law 144 van je vraagt: een onafhankelijke bias-audit binnen het jaar vóór het gebruik, de publicatie van een samenvatting daarvan, en een kennisgeving aan kandidaten 10 werkdagen vooraf.",
    },
    {
        "key": "emails",
        "question": "Welke e-mails stuurt prepza, en hoe stop ik ze?",
        "answer": "Service-e-mails, zoals uitnodigingen, rapporten, betalingsproblemen en wijzigingen in onze voorwaarden, worden altijd verstuurd. De rest, zoals het dagelijkse activiteitenoverzicht, herinneringen en productupdates, kies je in Instellingen, onder E-mails, of stop je met de link 'Afmelden' in elke e-mail. Kandidaten kunnen de e-mails van je bedrijf, of de herinneringen voor een interview, stoppen met de links in hun uitnodigingen en herinneringen. Nieuws van prepza staat bij je meldingen, de bel bovenaan; het belangrijkste nieuws komt ook per e-mail als productupdate, alleen zolang die instelling aan staat.",
    },
    {
        "key": "delete",
        "question": "Kan ik mijn account verwijderen?",
        "answer": "Ja, in Instellingen. Je account en je gegevens worden verwijderd, en vooraf kun je een kopie van je gegevens downloaden.",
    },
    {
        "key": "report",
        "question": "Hoe meld ik een probleem?",
        "answer": "Schrijf ons via de [contactpagina](/contact) en plak de ID van waar het om gaat: “id kopiëren” staat onder de naam van een bedrijf, een interview of een kandidaat, en die van je account in je accountmenu en in Instellingen. Met de ID vinden we het meteen.",
    },
]
