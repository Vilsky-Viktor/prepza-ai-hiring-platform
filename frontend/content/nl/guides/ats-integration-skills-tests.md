---
title: "Zo koppel je vaardigheidstests aan je ATS"
seoTitle: "Vaardigheidstests koppelen aan je ATS: een praktische gids"
description: "Verstuur vaardigheidstests en ontvang resultaten automatisch via je ATS, laat selectiebeslissingen bij mensen en weet wat je eerst moet controleren."
updated: "2026-10-21"
---

# Zo koppel je vaardigheidstests aan je ATS

De meeste recruitmentteams houden kandidaten bij in een applicant tracking system (ATS) en nemen vaardigheidstests af in een andere tool. Zonder koppeling tussen de twee kopieert iemand e-mailadressen uit het ATS, verstuurt uitnodigingen met de hand, wacht af en zet daarna de scores weer terug. Bij vijf kandidaten werkt dat. Bij vijftig gaan uitnodigingen te laat de deur uit, staan resultaten in een tweede tabblad dat niemand opent, en nemen goede sollicitanten een ander aanbod aan terwijl ze wachten.

Deze gids legt uit wat een goede koppeling tussen een ATS en een testtool doet, wat je controleert voordat je erop vertrouwt, en hoe je haar zo inricht dat automatisering het routinewerk doet terwijl mensen elke selectiebeslissing blijven nemen.

## Waarom ze überhaupt koppelen

| Zonder koppeling | Met koppeling |
| --- | --- |
| Iemand exporteert of kopieert e-mailadressen van kandidaten | Een kandidaat naar een fase verplaatsen verstuurt de uitnodiging |
| Uitnodigingen gaan eruit als iemand tijd heeft | Uitnodigingen gaan binnen enkele minuten na het verplaatsen eruit |
| Resultaten staan in de testtool | Resultaten verschijnen bij de kandidaat in het ATS |
| Hiring managers vragen: "Heeft iemand ze al getest?" | Het ATS laat zien wie getest is en hoe het ging |
| Typfouten in e-mailadressen en gemiste kandidaten | Het ATS is de enige lijst van wie er solliciteerde |

Snelheid telt zwaarder dan je denkt. Hoe langer het duurt tussen solliciteren en iets terughoren, hoe meer kandidaten afhaken of een andere baan aannemen. Exacte uitvalpercentages verschillen sterk per functie en arbeidsmarkt, dus ga voorzichtig om met gepubliceerde cijfers, maar de richting is steeds dezelfde: een traag proces verliest mensen, en de sterkste sollicitanten hebben meestal de meeste opties.

## Hoe een goede flow eruitziet

Een degelijke integratie volgt de fases die je al gebruikt. Ze bedenkt geen nieuw proces.

1. **Een kandidaat solliciteert** en komt zoals altijd in je ATS terecht.
2. **Iemand verplaatst de kandidaat naar een testfase,** bijvoorbeeld "Vaardigheidstest". Die verplaatsing is de trigger, dus een mens beslist nog steeds wie getest wordt.
3. **De testtool verstuurt de uitnodiging** automatisch, voor de test die aan die vacature gekoppeld is.
4. **De kandidaat maakt de test** wanneer het uitkomt, binnen de deadline die je instelt.
5. **Resultaten worden teruggeschreven naar de kandidaat in het ATS:** de score, of de kandidaat geslaagd is, eventuele integriteitssignalen en een link naar alle antwoorden.
6. **Een mens bekijkt het resultaat** en zet de kandidaat door, of niet.

Twee dingen blijven bewust handwerk: kiezen wie getest wordt en beslissen wat er daarna gebeurt. De koppeling haalt alleen het overtypen ertussenuit.

### Waarom niet bij elke nieuwe sollicitatie?

Sommige tools nodigen iedereen uit die solliciteert. Dat kan prima zijn voor functies met veel sollicitanten waarbij iedereen dezelfde test maakt. Maar een fase waar je kandidaten naartoe verplaatst, is beter te beheersen: je kunt sollicitanten overslaan die duidelijk niet aan een harde eis voldoen (geen werkvergunning, verkeerde locatie), en je test nooit iemand die je toch al zou afwijzen, en betaalt er ook niet voor.

## Wat je controleert voordat je een integratie kiest

Niet elke belofte van "integreert met je ATS" betekent hetzelfde. Stel deze vragen voordat je iets koppelt.

| Vraag | Waarom het ertoe doet | Een goed antwoord |
| --- | --- | --- |
| Hoe maak je verbinding? | Gedeelde wachtwoorden en accounts bij de leverancier zijn lastig te controleren of in te trekken | Een API-sleutel of token die je bedrijf zelf aanmaakt en altijd kan verwijderen |
| Wat kan de sleutel? | Een sleutel met volledige toegang is een risico als hij uitlekt | De minimale rechten die de integratie nodig heeft, vermeld in de documentatie |
| Wat triggert een uitnodiging? | Je moet precies weten wanneer kandidaten worden gemaild | Een specifieke fase die je per vacature kiest |
| Waar komen resultaten terecht? | Resultaten die niemand ziet, helpen niet | Op het profiel van de kandidaat, als notitie of opmerking die je team al leest |
| Wat gebeurt er als een uitnodiging mislukt? | Geen credits, een typfout, een gepauzeerd account: kandidaten blijven ongemerkt hangen | Iemand krijgt een melding en de kandidaat kan opnieuw worden uitgenodigd |
| Kan een gebeurtenis twee keer worden verwerkt? | ATS'en sturen gebeurtenissen opnieuw; een kandidaat hoort geen twee uitnodigingen te krijgen | Elke kandidaat wordt één keer per test uitgenodigd, hoe vaak de gebeurtenis ook binnenkomt |
| Hoe worden binnenkomende gebeurtenissen geverifieerd? | Naar een niet-geverifieerd adres kunnen valse gebeurtenissen worden gestuurd | Ondertekende verzoeken die de tool controleert |
| Hoe lang worden kandidaatgegevens bewaard? | Privacywetten zoals de AVG vragen om een duidelijke bewaartermijn | Een vastgelegde termijn, en verwijdering wanneer je de vacature, de test of je account verwijdert |
| Wat kost het? | Abonnementen per gebruiker kunnen automatisering duur maken | Een voorspelbare prijs per geteste kandidaat |

Als de leverancier de vragen over mislukte uitnodigingen en dubbele gebeurtenissen niet duidelijk kan beantwoorden, kom je er waarschijnlijk op de harde manier achter.

### Gegevensbescherming

Twee systemen koppelen betekent dat kandidaatgegevens, in elk geval namen en e-mailadressen, tussen twee bedrijven worden uitgewisseld. Onder de AVG en vergelijkbare wetten is je testleverancier meestal je verwerker, dus heb je een verwerkersovereenkomst nodig en vertel je kandidaten, in je privacyverklaring of in de uitnodiging, dat een vaardigheidstest deel uitmaakt van de procedure. Geef niet meer gegevens door dan de test nodig heeft. Meer over de juridische kant van tests en AI bij werving vind je in [Is werven met AI legaal in de EU?](/guides/is-ai-hiring-legal-in-the-eu)

## Een checklist voor de inrichting

Voordat je het inschakelt voor een echte vacature:

1. **Maak in je ATS een aparte fase voor het testen,** zoals "Vaardigheidstest". Hergebruik geen fase die iets anders betekent, anders worden kandidaten per ongeluk uitgenodigd.
2. **Maak de sleutel aan vanuit een beheerdersaccount** dat alle vacatures ziet die je wilt koppelen, met alleen de rechten die de documentatie noemt.
3. **Koppel elke vacature aan haar test** en kies de fase die de uitnodiging triggert.
4. **Stel de webhook in** als je ATS vraagt dat met de hand te doen, en plak het secret ervan waar de tool erom vraagt.
5. **Test het met jezelf.** Voeg een kandidaat met je eigen e-mailadres toe, verplaats die naar de fase, maak de test en controleer of de notitie in het ATS verschijnt.
6. **Bepaal wie mislukte uitnodigingen in de gaten houdt:** wie een melding krijgt als een uitnodiging niet verstuurd kan worden, en wie het oplost.
7. **Spreek af hoe je resultaten leest.** Een slaaggrens is een richtlijn, geen automatische afwijzing. Spreek dat af voordat de resultaten binnenkomen, niet erna.

## Veelgemaakte fouten

- **De beslissing automatiseren in plaats van het papierwerk.** Iedereen onder een bepaalde score automatisch afwijzen haalt de menselijke controle weg die een slechte vraag opmerkt of een kandidaat met verbindingsproblemen. Laat de score sorteren; laat een mens beslissen.
- **Triggeren vanuit de verkeerde fase.** Een fase die recruiters om andere redenen gebruiken, stuurt tests naar mensen die ze niet zouden moeten krijgen.
- **Eén test voor elke vacature.** Door de koppeling is het makkelijk om overal dezelfde test te sturen. Een test helpt het meest als hij voor die specifieke functie is gemaakt. Zie [Vaardigheidstests vs. cv-screening](/guides/skills-tests-vs-cv-screening).
- **Niemand houdt mislukte uitnodigingen in de gaten.** Als een uitnodiging ongemerkt mislukt, wacht de kandidaat op een e-mail die nooit komt, en denk jij dat die is genegeerd.
- **Een sleutel gekoppeld aan iemand die vertrekt.** Sommige ATS-sleutels handelen namens de persoon die ze heeft aangemaakt. Wordt het account van die persoon afgesloten, dan stopt de koppeling. Gebruik een account dat blijft, en koppel opnieuw als mensen van rol wisselen.
- **Kandidaten buiten het ATS vergeten.** Doorverwezen kandidaten en directe sollicitanten die nooit in het ATS komen, hebben ook een uitnodiging nodig. Houd ook een handmatige manier om ze uit te nodigen.

## Hoe prepza het doet

prepza koppelt met **Workable, Greenhouse, Teamtailor, Recruitee en Breezy HR**. Het volgt de flow hierboven.

- **Jouw sleutel, jouw controle.** Een eigenaar of beheerder koppelt het ATS op het tabblad Integraties van het bedrijf met een sleutel die je bedrijf in het ATS aanmaakt. prepza controleert de sleutel voordat hij wordt opgeslagen, bewaart hem versleuteld en toont hem nooit meer. Ontkoppelen verwijdert de sleutel en de gekoppelde vacatures meteen.
- **Koppel een vacature aan een interview.** Kies een vacature in het ATS en de fase die de uitnodiging triggert, en koppel die aan een bestaand interview in prepza of maak een nieuw interview op basis van de vacaturetekst in het ATS. Je bekijkt de onderwerpen voordat er ook maar één vraag wordt geschreven.
- **Kandidaat verplaatst, uitnodiging verstuurd.** Elke kandidaat wordt één keer per interview uitgenodigd, ook als het ATS dezelfde gebeurtenis twee keer stuurt.
- **Resultaten terug in het ATS.** Als een kandidaat klaar is, zet prepza een notitie of opmerking bij de kandidaat in het ATS met het cijfer, of de kandidaat geslaagd is, eventuele integriteitssignalen (de pagina verlaten, kopieerpogingen, antwoorden die te snel zijn gekozen om de vraag te hebben gelezen) en een link naar de scorekaart met alle antwoorden.
- **Mislukte uitnodigingen vallen op.** Als een kandidaat niet kan worden uitgenodigd, bijvoorbeeld omdat het bedrijf geen credits meer heeft, een e-maillimiet heeft bereikt, of omdat prepza uitnodigingen tijdelijk heeft gepauzeerd, krijgen alle leden van het bedrijf een melding met de naam van het ATS. Kandidaten die wegens te weinig credits niet zijn uitgenodigd, worden na een opwaardering automatisch uitgenodigd, en de wachtende kandidaten van elke vacature kun je met één klik opnieuw uitnodigen.
- **Slack, als je dat gebruikt.** prepza kan meldingen, zoals een kandidaat die klaar is of een ATS-kandidaat die niet kon worden uitgenodigd, in een Slack-kanaal naar keuze plaatsen.
- **Je eigen platform.** Staat je ATS er niet bij, dan kun je met de [API](/api-docs) van prepza kandidaten uitnodigen met een API-sleutel en een ondertekende webhook ontvangen wanneer een kandidaat begint of klaar is, wanneer de uitnodiging een kandidaat niet bereikt of verloopt, wanneer een kandidaat wordt verwijderd en wanneer een interview klaarstaat.
- **Gegevens voor een vaste termijn bewaard.** Kandidaten die uit een ATS zijn opgeslagen, worden na 365 dagen verwijderd, of eerder samen met hun interview of bedrijf.

Sommige ATS'en vragen een stap aan hun kant. Bij Greenhouse, Teamtailor en Recruitee voeg je een webhook met de hand toe; het venster Instructies in prepza toont het adres en waar je het secret plakt. De webhooks van Workable en Breezy HR stelt prepza zelf in.

Je betaalt per kandidaat, zonder abonnement: alleen voor kandidaten die minstens één vraag beantwoorden, $5 per kandidaat bij de opwaardering van $50, $4 vanaf een opwaardering van $200, $3 vanaf een opwaardering van $600 en $2 vanaf een opwaardering van $1.000. Prijzen zijn hier in Amerikaanse dollars, en in de lokale valuta in Canada, Australië, Israël, Polen, Zwitserland, Japan, Zuid-Korea, Taiwan, Hongkong, Thailand, Singapore, India, de rest van Europa en het Verenigd Koninkrijk; btw of sales tax wordt bij het afrekenen geregeld. Een ATS koppelen en interviews maken is gratis, en de eerste 3 kandidaten van je eerste bedrijf zijn gratis. Zie [prijzen](/pricing).

## Verder lezen

- [Zo screen je 100 sollicitanten in één dag](/guides/screen-100-applicants-in-a-day)
- [Vaardigheidstests vs. cv-screening](/guides/skills-tests-vs-cv-screening)
- [Selectietests: een praktische gids](/pre-employment-testing)
