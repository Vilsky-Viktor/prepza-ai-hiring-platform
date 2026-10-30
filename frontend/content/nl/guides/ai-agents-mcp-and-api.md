---
title: "AI-agents, MCP en API's: wat het zijn en hoe je ze inzet bij werving en selectie"
seoTitle: "AI-agents, MCP en API's bij werving: zo zet je ze in"
description: "Wat een AI-agent, MCP en API zijn, hoe je ze veilig inzet bij werving en hoe je prepza bedient via de eigen AI-assistent, Claude, ChatGPT of je platform."
updated: "2026-10-22"
---

# AI-agents, MCP en API's: wat het zijn en hoe je ze inzet bij werving en selectie

De meeste mensen leerden AI eerst kennen als chatvenster: jij vraagt, het antwoordt. Een AI-agent gaat een stap verder. Die kan dingen opzoeken in je tools en er, als je erom vraagt, ook dingen in doen: een interview aanmaken, een lijst kandidaten uitnodigen, vertellen wie vorige week het hoogst scoorde. Het Model Context Protocol (MCP) is de standaard waarmee de AI-chat die je al gebruikt, zoals Claude of ChatGPT, verbinding maakt met zulke tools. En een API is de oudere, preciezere manier waarop software met software praat, zonder AI ertussen.

Deze gids legt alle drie in gewone taal uit: waar ze goed voor zijn bij werving en selectie, waar je op moet letten en hoe je ze met prepza gebruikt.

## Wat een AI-agent is

Een chatbot schrijft alleen tekst. Een agent is een taalmodel met **tools**: kleine, duidelijk afgebakende acties die hij mag aanroepen, zoals "toon de kandidaten van dit interview" of "nodig dit e-mailadres uit". Als je iets vraagt, bepaalt de agent welke tools hij gebruikt, leest hij wat ze teruggeven en antwoordt hij op basis daarvan, niet uit zijn geheugen.

| Een chatbot | Een AI-agent |
| --- | --- |
| Antwoordt vanuit wat hij tijdens de training leerde | Antwoordt vanuit je actuele gegevens, gelezen via tools |
| Kan alleen beschrijven hoe je iets doet | Kan het doen, als je erom vraagt en het toestaat |
| Gokt als hij het niet weet | Zoekt het op, of zegt dat hij het niet kan |
| Leeft in één venster | Werkt binnen de tools waarmee je hem verbindt |

De tools maken een agent nuttig, en ze bepalen ook of hij veilig is of niet. Een goede agent kan alleen de tools gebruiken die hij krijgt, alleen met jouw rechten, en doet alleen wat je hebt gevraagd.

## Wat MCP is

Het Model Context Protocol is een open standaard die Anthropic eind 2024 introduceerde en die inmiddels wordt ondersteund door Claude, ChatGPT en veel andere AI-apps en ontwikkeltools. Het wordt vaak vergeleken met een USB-C-poort voor AI: in plaats van dat elke AI-app een eigen verbinding met elke tool bouwt, biedt een tool één **MCP-server** aan, en elke AI-app die MCP spreekt kan die gebruiken.

Een MCP-server vertelt de AI-app drie dingen:

1. **Welke tools er zijn,** met een naam, een beschrijving en de gegevens die elke tool nodig heeft.
2. **Welke tools alleen lezen** en welke iets veranderen, zodat de AI-app het je kan vragen voor een wijziging.
3. **Wie je bent,** via een aanmelding die je één keer goedkeurt, zodat elke aanroep namens jou wordt uitgevoerd, met jouw rechten.

Voor jou betekent dit dat je met een tool kunt werken vanuit de chat die je al gebruikt, zonder gegevens tussen vensters te kopiëren.

## Wat een API is, en waarin die verschilt

Een API (application programming interface) is een set vaste verzoeken die het ene programma naar het andere kan sturen: "toon de kandidaten van dit interview", "nodig dit e-mailadres uit". Je developers schrijven de code die ze verstuurt. Er komt geen AI aan te pas: hetzelfde verzoek doet altijd hetzelfde, en dat is precies wat je wilt voor automatisering die vanzelf draait.

| | Mira, de AI-assistent (in de app) | MCP (in Claude of ChatGPT) | API |
| --- | --- | --- | --- |
| Wie het gebruikt | Jij, in prepza | Jij, in je AI-chat | De code van je platform |
| Hoe je vraagt | In je eigen woorden | In je eigen woorden | Vaste verzoeken die een developer schrijft |
| Wie wijzigingen goedkeurt | Jij, op een kaart | Jij, in je AI-app | Je code, zoals die geschreven is |
| Het meest geschikt voor | Snelle vragen en taken | prepza combineren met je andere tools en bestanden | Automatisering die draait zonder dat iemand meekijkt |
| Meldt zich aan als | Jij | Jij | Een bedrijfssleutel |

Gebruik Mira of MCP als er een mens bij betrokken is. Gebruik de API als je eigen systeem zelf kandidaten moet uitnodigen en resultaten moet ophalen, bijvoorbeeld vanuit een vacaturesite of een interne HR-tool.

## Waar dit goed voor is bij werving en selectie

Werving en selectie bestaat uit veel kleine, terugkerende stappen, verspreid over verschillende tools. Juist daar is een agent goed in:

- **Vragen over je pipeline.** "Welke kandidaten voor Senior Backend zijn deze week geslaagd?", "Wie is nog niet aan het interview begonnen?", "Wat is onze gemiddelde score voor de functie van data-analist?"
- **Dingen inrichten.** "Maak een interview op basis van deze vacaturetekst", "Zet de slaaggrens op 70%", "Geef deze kandidaat 50% extra tijd."
- **Bulkwerk.** "Nodig deze 12 mensen uit voor het frontend-interview", rechtstreeks geplakt uit een e-mail of spreadsheet.
- **Bronnen combineren.** In Claude of ChatGPT kun je prepza combineren met je andere gekoppelde tools en bestanden: een vacaturetekst uit je documenten vergelijken met de onderwerpen van het interview, of een bericht opstellen aan de kandidaten op de shortlist.

Wat de agent niet moet doen, is de selectiebeslissing nemen. Een score ondersteunt het oordeel van een mens, maar vervangt het niet. Laat de agent sorteren, samenvatten en voorbereiden, en laat de beslissing bij een mens. Zie [Is AI bij werving en selectie legaal in de EU?](/guides/is-ai-hiring-legal-in-the-eu) voor waarom dat ook juridisch belangrijk is.

## Waar je op moet letten

Een AI koppelen aan je wervingsgegevens verdient dezelfde zorg als een collega toegang geven.

| Risico | Wat helpt |
| --- | --- |
| De agent doet iets wat je niet bedoelde | Wijzigingen hebben eerst jouw goedkeuring nodig, en hij doet alleen wat je vroeg |
| Hij ziet meer dan hij zou moeten | Hij handelt namens jou: hij ziet wat jij ziet, niets meer |
| Instructies verstopt in gegevens | Namen, antwoorden en documenten van kandidaten zijn gegevens, nooit instructies om op te volgen |
| Geheimen belanden in een chat | API-sleutels en wachtwoorden gaan nooit via de chat |
| Onomkeerbare fouten | Een account of bedrijf verwijderen blijft in de app, achter een eigen bevestiging |
| Gegevens verlaten je tools | Gegevens gaan naar de AI-app die je koppelt, onder de voorwaarden van die app: koppel alleen apps die je bedrijf toestaat |
| Gebruik dat uit de hand loopt | Limieten op hoeveel acties er per uur worden uitgevoerd |

Controleer voordat je een AI-app aan werkgegevens koppelt het beleid van je bedrijf voor AI-tools, en vertel kandidaten in je privacyverklaring welke diensten hun gegevens verwerken.

## Drie manieren om met prepza te werken buiten de pagina's zelf

### 1. Mira, de ingebouwde AI-assistent

Kies **vraag Mira** in de kop van elke pagina. Mira, de AI-assistent van prepza, kent je bedrijven, interviews, kandidaten, credits en integraties, en weet hoe prepza werkt. Ze antwoordt in jouw taal, en je kunt typen of spreken.

- **Hij antwoordt vanuit je gegevens,** met hetzelfde zicht als jij: een beheerder ziet wat een beheerder ziet, een kijker wat een kijker ziet.
- **Hij weet op welke pagina je bent.** Vraag "Wat kan ik op deze pagina doen?" voor de uitleg bij die pagina, of "Wie is hier de beste?" bij de kandidaten van een interview, en hij antwoordt over dat interview zonder te vragen welk.
- **Hij bereidt wijzigingen voor, jij bevestigt ze.** Vraag je hem kandidaten uit te nodigen, dan toont hij een kaart met precies wat er gaat gebeuren, zoals "12 kandidaten uitnodigen voor Backend developer". Er gebeurt niets totdat je Bevestigen kiest.
- **Hij laat zijn bronnen zien.** Onder een antwoord zie je de kandidaten of interviews die hij gebruikte en een link naar de pagina waar ze vandaan komen.
- **Hij blijft bij het onderwerp.** Hij beantwoordt vragen over prepza en werven met prepza, en slaat de rest af.

### 2. prepza in Claude of ChatGPT, via MCP

Werkt je team al in Claude of ChatGPT, dan kun je prepza daarheen halen. De MCP-server van prepza biedt dezelfde tools als Mira, de ingebouwde assistent.

**Zo koppel je:**

1. Open in prepza het tabblad **Integraties** van een bedrijf en kies **AI-apps**. Kopieer het serveradres: `https://prepza.ai/mcp`.
2. **In Claude:** open Instellingen, dan Connectors, en voeg een aangepaste connector toe met dat adres. **In Claude Code:** voer `claude mcp add --transport http prepza https://prepza.ai/mcp` uit. **In ChatGPT:** voeg het toe als aangepaste connector in de instellingen voor apps en connectors.
3. Je AI-app opent de aanmelding van prepza. Meld je aan, controleer welke app erom vraagt, en kies **Toestaan**. Mag de app alleen lezen, zet dan eerst **Wijzigingen toestaan** uit.

Vanaf dan vraag je in je chat wat je ook een collega zou vragen: "Wie zijn in prepza de drie beste kandidaten voor Product designer?" De meeste AI-apps vragen je om toestemming voor een wijziging en waarschuwen je voor alles wat niet ongedaan kan worden gemaakt: prepza vertelt ze welke acties iets wijzigen of verwijderen.

**Wat hetzelfde blijft als in de app:**

- **Je rechten.** Hij handelt namens jou, in elk bedrijf waar je lid van bent, met je rol in elk ervan.
- **Credits en limieten.** Een kandidaat uitnodigen kost hetzelfde als in de app, en dezelfde e-maillimieten gelden.
- **De registratie.** Alles wat een AI-app voor je doet, verschijnt in het actielog van het bedrijf als gedaan via een AI-app, van onderwerpen goedkeuren en resultaten bekijken tot extra tijd geven of een kandidaat intrekken. De eigenaar van het bedrijf leest het op het tabblad **Actielog** van het bedrijf.
- **Het bedrijf beslist.** Eigenaren en beheerders kunnen AI-apps het gebruik van de gegevens van een bedrijf ontzeggen met **AI-apps toestaan in dit bedrijf** op de pagina AI-apps van het bedrijf.
- **Wat hij niet kan.** Hij kan je wachtwoord en API-sleutels niet zien, en kan je account of een bedrijf niet verwijderen. Dat blijft in de app.

**Om te ontkoppelen** verwijder je de connector in je AI-app, of kies je **Ontkoppelen** ernaast onder **AI-apps** op het tabblad Integraties. Hij werkt dan meteen niet meer.

**Andere apps en je eigen agents.** Het [MCP-tabblad](/api-docs?tab=mcp) van de ontwikkelaarsdocumentatie heeft de stappen voor Gemini CLI, Cursor, VS Code en Le Chat, en complete voorbeeldagents in Python en TypeScript. Een agent die op een server draait, zonder iemand die een aanmelding kan goedkeuren, gebruikt een API-sleutel van het bedrijf met het recht **Gebruiken met AI-agents (MCP)**: hij werkt alleen in dat bedrijf, en alleen met de tools die de andere rechten van de sleutel toestaan. Wat hij doet, staat in de actielog van het bedrijf onder de naam van de sleutel.

### 3. Je eigen platform, via de API

Voor automatisering zonder AI heeft prepza een API, beschreven in de [ontwikkelaarsdocumentatie](/api-docs).

1. Een eigenaar of beheerder opent het tabblad **Integraties** van een bedrijf, dan **API**, en kiest **Nieuwe sleutel**. Geef hem de naam van het platform dat hem gaat gebruiken, kies wanneer hij verloopt en vink alleen aan wat hij nodig heeft: de sleutel van een dashboard leest alleen, die van een vacaturesite nodigt ook uit. Rechten kun je later toevoegen of intrekken. De sleutel wordt één keer getoond; bewaar hem op een veilige plek.
2. Je platform stuurt verzoeken met die sleutel: de interviews van het bedrijf ophalen, kandidaten ophalen of opvragen met hun score, of ze geslaagd zijn en hun integriteitssignalen, en een kandidaat uitnodigen.
3. Voeg een **webhook** toe: een adres op je platform dat prepza ondertekend aanroept wanneer een kandidaat begint of klaar is, wanneer de uitnodiging een kandidaat niet bereikt of verloopt, wanneer een kandidaat wordt verwijderd en wanneer een interview klaarstaat, zodat je niet steeds hoeft te vragen. Op de API-pagina kun je er een testgebeurtenis naartoe sturen en zie je het afleverlogboek.

Bij elke kandidaat zit een link naar de volledige resultaten in prepza en, tot de kandidaat klaar is, een eigen uitnodigingslink, zodat je platform die in een eigen bericht kan versturen als je dat liever hebt. Weet je platform al wie de kandidaat is, nodig de kandidaat dan uit zonder inloggen: prepza verstuurt geen e-mails en de kandidaat doet het interview via de link zonder bij prepza in te loggen, dus stuur de link alleen naar die kandidaat. Een uitnodiging kan de kandidaat ook terugsturen naar je website (elk https-adres) met een knop op de pagina na afloop, en een licht of donker thema in de kleuren van je bedrijf instellen. Met de SDK van prepza kan je eigen pagina het interview zelf tonen, maar alleen op de sites die je bedrijf op zijn API-pagina toestaat. De API en webhooks hangen niet van die sites af: in plaats daarvan kun je elke sleutel beperken tot de IP-adressen van je servers. Verificatie voegt alleen de badge van een geverifieerd bedrijf toe.

Dezelfde regel geldt als overal: de score ondersteunt de beslissing van een mens, dus wijs kandidaten er niet automatisch op af.

## Wat je wanneer gebruikt

Ga uit van wie het werk doet en hoe vaak.

| Jouw situatie | Gebruik |
| --- | --- |
| Je zit in prepza en wilt snel antwoord: wie is geslaagd, wie is nog niet begonnen, hoeveel credits er nog zijn | Mira, de ingebouwde assistent |
| Je wilt iets in een paar woorden inrichten: een interview op basis van een vacaturetekst, een slaaggrens, extra tijd | Mira, de ingebouwde assistent |
| Je werkt al de hele dag in Claude of ChatGPT en wilt prepza daar ook | MCP |
| De taak vraagt om prepza plus iets anders: je documenten, e-mailconcepten, een andere gekoppelde tool | MCP |
| Een recruiter onderweg wil de pipeline checken vanuit de AI-app op de telefoon | MCP |
| Je vacaturesite of HR-systeem moet zelf kandidaten uitnodigen, zonder dat iemand klikt | De API |
| Resultaten moeten in je eigen database of dashboard terechtkomen zodra kandidaten klaar zijn | De API, met een webhook |
| Je ATS is er een waarmee prepza koppelt (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Geen van deze: koppel het ATS op het tabblad Integraties. Zie [Zo koppel je vaardigheidstests aan je ATS](/guides/ats-integration-skills-tests) |

Een eenvoudige vuistregel:

- **Een mens vraagt en controleert elke wijziging:** Mira in prepza, of MCP als die persoon de hele dag in Claude of ChatGPT werkt.
- **Software handelt zelfstandig, elke keer op dezelfde manier:** de API.
- **Net begonnen:** probeer eerst Mira, de ingebouwde assistent. Daarvoor hoef je niets in te stellen, en wat je leert neem je mee naar MCP.

Ze werken ook samen. Een team kan uitnodigingen vanuit zijn HR-systeem via de API versturen, terwijl recruiters Mira of hun AI-chat naar de resultaten vragen.

## Goede resultaten krijgen

- **Noem dingen bij naam.** "Het interview Senior Backend" werkt beter dan "dat interview".
- **Vraag om één stap tegelijk** als het ertoe doet. Controleer het resultaat en vraag dan om de volgende.
- **Lees de goedkeuring voordat je toestaat.** Die laat precies zien wat er wordt uitgevoerd.
- **Vraag waar een getal vandaan komt.** Een goede agent kan de kandidaten of de pagina erachter aanwijzen.
- **Laat beslissingen bij mensen.** Gebruik de agent om te zoeken, te sorteren en voor te bereiden; beslis zelf.

## Prijzen

Mira, de MCP-koppeling en de API zijn gratis te gebruiken. Je betaalt alleen voor kandidaten, net als altijd: per kandidaat die minstens één vraag beantwoordt, zonder abonnement. Zie [prijzen](/pricing).

## Verder lezen

- [Zo koppel je vaardigheidstests aan je ATS](/guides/ats-integration-skills-tests)
- [Developers interviewen in het tijdperk van AI](/guides/interviewing-in-the-age-of-ai)
- [Is AI bij werving en selectie legaal in de EU?](/guides/is-ai-hiring-legal-in-the-eu)
