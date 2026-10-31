---
title: "Is AI bij werving en selectie legaal in de VS? Wat werkgevers moeten weten"
seoTitle: "AI bij werving en selectie: legaal in de VS?"
description: "AI bij werving is legaal in de VS, met regels: federaal recht over adverse impact en aanpassingen, bias-audits in NYC, en Illinois, Colorado en Californië."
updated: "2026-10-30"
---

# Is AI bij werving en selectie legaal in de VS? Wat werkgevers moeten weten

Over het algemeen wel: AI gebruiken bij werving en selectie is legaal in de VS. Er is geen federale AI-wet voor werving. In plaats daarvan geldt het federale antidiscriminatierecht voor AI-tools zoals voor elke test, en een paar plaatsen voegen eigen regels toe: New York City, Illinois, Colorado en Californië.

Deze gids legt de regels op hoofdlijnen uit, de data die ertoe doen, wat werkgevers moeten doen en hoe testee ermee omgaat. **Dit is geen juridisch advies.** Het geeft de regels weer zoals ze in oktober 2026 gelden; een aantal daarvan is nieuw of wordt nog afgerond.

## Het korte antwoord

| Vraag | Kort antwoord |
| --- | --- |
| Mag ik AI gebruiken om kandidaten te screenen of te beoordelen? | Ja, binnen het federale antidiscriminatierecht en de regels van staten en steden |
| Moet ik de resultaten op bias controleren? | Adverse impact is jouw verantwoordelijkheid; in New York City is vóór gebruik een onafhankelijke bias-audit verplicht |
| Moet ik het kandidaten vertellen? | In New York City en Illinois wel; in Colorado en Californië vanaf 1 januari 2027 |
| Moet ik extra tijd geven? | Aan kandidaten met een beperking die het nodig hebben: een redelijke aanpassing |
| Hoe lang moet ik gegevens bewaren? | Vier jaar in Californië, drie in Colorado |
| Wie neemt het besluit om iemand aan te nemen? | Een mens. Alle regels hier gaan uit van menselijke beoordeling |

## Federaal recht

### Title VII en adverse impact

Title VII van de Civil Rights Act van 1964 verbiedt discriminatie in werk op grond van ras, huidskleur, religie, geslacht of nationale afkomst, ook via een neutrale test die een groep onevenredig benadeelt (adverse impact) en niet met de functie samenhangt. De Uniform Guidelines on Employee Selection Procedures geven de gebruikelijke vuistregel, de vier-vijfdenregel ([29 CFR §1607.4(D)](https://www.law.cornell.edu/cfr/text/29/1607.4)):

> Een selectiepercentage voor een ras-, geslachts- of etnische groep dat lager is dan vier vijfde (4/5) (of tachtig procent) van het percentage van de groep met het hoogste percentage, wordt door de federale handhavingsinstanties in het algemeen beschouwd als bewijs van adverse impact.

Als bijvoorbeeld 60% van de ene groep voor je test slaagt en 42% van een andere, is de verhouding 42 ÷ 60 = 0,70, onder 0,80: een waarschuwingssignaal om uit te zoeken. Het is geen bewijs van discriminatie, en bij kleine aantallen kan de verhouding flink schommelen.

De technische toelichting van de EEOC uit 2023 over AI bij selectie werd in januari 2025 offline gehaald. De Uniform Guidelines zijn regelgeving, geen richtsnoer, en gelden nog steeds. De verantwoordelijkheid voor adverse impact blijft bij de werkgever, wie de test ook heeft gebouwd.

### De ADA en aanpassingen

De Americans with Disabilities Act verplicht tot redelijke aanpassingen voor gekwalificeerde kandidaten met een beperking, ook bij tests ([29 CFR 1630.11](https://www.law.cornell.edu/cfr/text/29/1630.11)): een test moet de vaardigheid meten, niet de beperking. Extra tijd is de gebruikelijke aanpassing bij een getimede test. Vertel kandidaten hoe ze erom kunnen vragen, voordat ze beginnen.

## New York City: Local Law 144

[Local Law 144](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page) geldt, met de regels van het Department of Consumer and Worker Protection (6 RCNY §5-300 en volgende), wanneer een werkgever of uitzendbureau een automated employment decision tool (AEDT) gebruikt die wervingsbesluiten voor banen in New York City wezenlijk ondersteunt. Een tool die kandidaten scoort of rangschikt en wordt gebruikt om te beslissen wie doorgaat, telt zeer waarschijnlijk mee. Voordat je er een gebruikt, heb je nodig:

- **Een bias-audit** door een onafhankelijke auditor, uitgevoerd binnen een jaar vóór gebruik. Noch de leverancier noch jij, de werkgever, kan de onafhankelijke auditor zijn.
- **Een gepubliceerde samenvatting** van de audit: de selectie- of scorepercentages en impact ratios naar geslacht, ras/etniciteit en intersectionele categorieën, het aantal kandidaten in een onbekende categorie en de distributiedatum van de tool.
- **Een melding aan kandidaten** minstens 10 werkdagen vóór gebruik, met informatie over hoe ze om een alternatieve selectieprocedure of een aanpassing kunnen vragen.

Hoe de audit rekent:

- **Selectiepercentage:** het deel van een categorie dat doorgaat. **Scorepercentage,** bij tools die scores geven: het deel van een categorie dat boven de mediaan van de hele steekproef scoort.
- **Impact ratio:** het percentage van een categorie gedeeld door het percentage van de hoogste categorie.
- Categorieën met minder dan 2% van de gegevens mogen buiten de impact ratios worden gelaten.
- De gegevens moeten echt zijn. De FAQ van het DCWP zegt: "Geïmputeerde of afgeleide gegevens mogen niet worden gebruikt om een bias-audit uit te voeren." Demografische gegevens moeten van de kandidaten zelf komen, bijvoorbeeld uit een vrijwillig zelfidentificatieformulier.

## Illinois

Een wijziging van de Illinois Human Rights Act (Public Act 103-0804, 775 ILCS 5/2-102(L)) geldt sinds 1 januari 2026. Werkgevers mogen niet:

- AI gebruiken die tot gevolg heeft dat kandidaten of werknemers worden gediscrimineerd op grond van een beschermde klasse;
- postcodes gebruiken als vervanging (proxy) voor een beschermde klasse.

En ze moeten kandidaten vertellen wanneer AI wordt gebruikt bij wervings- en aannamebesluiten. Het Illinois Department of Human Rights stelde in mei 2026 regels voor de melding voor en trok ze in juni 2026 in; er zijn er nog geen vastgesteld, dus volg de wet zelf.

## Colorado

De AI-wet van Colorado werd ingetrokken en opnieuw vastgesteld door SB 26-189, ondertekend op 14 mei 2026 en van kracht vanaf 1 januari 2027. De regels van de Attorney General zijn voorgesteld (op 26 oktober 2026 was er een hoorzitting) en moeten vóór die datum klaar zijn. Voor gebruikers (deployers) van hoogrisico-AI die bij arbeidsbesluiten wordt ingezet, zijn de plichten:

- **Melding vóór gebruik** aan de kandidaat.
- **Uitleg van een ongunstig besluit,** zoals niet worden aangenomen of niet doorgaan.
- **Correctie en herbeoordeling:** een manier om gegevens te corrigeren en om een menselijke beoordeling te vragen.
- **Gegevens,** 3 jaar bewaard.

## Californië

- **Regels van de Civil Rights Council over geautomatiseerde besluitvormingssystemen,** van kracht sinds 1 oktober 2025: het antidiscriminatierecht geldt voor geautomatiseerde tools bij werving zoals voor elke andere selectiemethode. Werkgevers moeten personeelsgegevens, inclusief gegevens van geautomatiseerde besluitvormingssystemen, vier jaar bewaren (Cal. Code Regs. tit. 2, §11013(c)).
- **De regels van de CCPA over geautomatiseerde besluitvormingstechnologie** gelden vanaf 1 januari 2027 voor arbeidsbesluiten: een melding vóór gebruik, het recht om bezwaar te maken (opt-out) of in beroep te gaan, en het recht op inzage in hoe de technologie is gebruikt.

## De data

| Datum | Wat geldt |
| --- | --- |
| 5 juli 2023 | Handhaving van Local Law 144 in New York City |
| 1 oktober 2025 | Regels van de Californische Civil Rights Council over geautomatiseerde besluitvormingssystemen |
| 1 januari 2026 | Illinois: melding van AI-gebruik, geen discriminerende AI, geen postcodes als proxy |
| 1 januari 2027 | De AI-wet van Colorado; de Californische CCPA-regels over geautomatiseerde besluitvorming bij werk |

## Een praktische checklist voor werkgevers

1. **Maak een lijst van de functies en plaatsen** waarvoor je werft: New York City, Illinois, Colorado, Californië, elders in de VS.
2. **Test alleen wat de functie vraagt.** Kies onderwerpen en een slaaggrens die je voor de rol kunt verantwoorden.
3. **Werk je informatie voor kandidaten bij** met dat AI wordt gebruikt, hoe resultaten worden gebruikt en hoe ze om een aanpassing en een menselijke beoordeling kunnen vragen. Voeg de formuleringen voor Illinois en Colorado toe waar die gelden.
4. **Bied aanpassingen aan,** zoals extra tijd, en spreek ze af voordat de kandidaat begint.
5. **Verzamel demografische gegevens bij de kandidaten zelf,** via een vrijwillig zelfidentificatieformulier, gescheiden van de wervingsbesluiten. Leid ze nooit af.
6. **Controleer adverse impact** op je eigen uitkomsten, met de vier-vijfdenregel als eerste check.
7. **Voor banen in New York City** laat je een onafhankelijke bias-audit uitvoeren, publiceer je de samenvatting en geef je de melding 10 werkdagen voordat je de tool gebruikt.
8. **Bewaar gegevens zo lang als jouw recht vereist,** bijvoorbeeld vier jaar in Californië en drie in Colorado.
9. **Wijs nooit af op alleen een score.** Laat een mens elk resultaat beoordelen.

## Hoe testee hiermee omgaat

testee neemt getimede meerkeuze-vaardigheidstests af die door AI worden geschreven op basis van een functieomschrijving. In de VS gaat testee er op dezelfde manier mee om als in de EU. testee claimt niet dat het compliant of gecertificeerd is.

Zo ziet dat er vandaag in het product uit:

- **AI schrijft de vragen en de antwoordsleutels; het nakijken volgt vaste regels.** Geen AI leest of beoordeelt het antwoord van een kandidaat, en er wordt geen video- of gezichtsanalyse gebruikt. In de spraakmodus wordt spraak omgezet in tekst en gekoppeld aan een antwoordoptie, die de kandidaat te horen krijgt en op het scherm ziet: één duidelijk genoemde optie wordt meteen vastgelegd, een keuze van meerdere opties wordt eerst bevestigd. De spraak wordt nooit opgeslagen en de stem wordt nooit geanalyseerd.
- **Jij keurt de onderwerpen goed** voordat er ook maar één vraag wordt geschreven, en jij kiest de slaaggrens.
- **Mensen beslissen.** testee wijst geen kandidaten af en stuurt geen afwijzingsberichten.
- **Geen beschermde kenmerken.** testee vraagt, leidt af of bewaart nooit het geslacht, het ras, de leeftijd, een beperking, de postcode of andere beschermde kenmerken van kandidaten.
- **Een export voor een bias-audit.** Op de pagina Actielog van het bedrijf kan de eigenaar een csv-bestand downloaden van de kandidaten die klaar zijn, voor het hele bedrijf of één interview en tussen twee data: per kandidaat het cijfer, de slaaggrens, of de kandidaat geslaagd is en of die boven de mediaan van het interview scoorde. Elke rij heeft het e-mailadres van de kandidaat als sleutel, zodat je hem kunt koppelen aan de zelfgerapporteerde categorieën die je zelf hebt verzameld; verwijder daarna de kolom met e-mailadressen en geef het bestand aan je onafhankelijke auditor, die de selectie- en scorepercentages en de impact ratios berekent. Met hetzelfde bestand kun je de vier-vijfdencheck zelf uitvoeren.
- **Extra tijd** van +25%, +50% of +100% per vraag kan worden gegeven aan elke kandidaat die erom vraagt, voordat die begint. testee bewaart alleen de hoeveelheid, nooit de reden. In de spraakmodus kan een kandidaat altijd in plaats daarvan op een optie tikken, en je kunt een interview instellen op alleen antwoorden door te tikken.
- **Sjablonen voor de informatie aan kandidaten,** een algemene en versies voor New York City, Illinois en Colorado, staan op de [documentenpagina](/documents), samen met de instructies voor bedrijven.
- **New York City.** testee heeft nog geen eigen onafhankelijke bias-audit gehad. Gebruik testee niet voor banen in New York City totdat je hebt gedaan wat Local Law 144 van jou als werkgever vraagt: een onafhankelijke bias-audit binnen het jaar vóór gebruik, de samenvatting gepubliceerd en een melding aan kandidaten 10 werkdagen vooraf.
- **Gegevens.** Je bedrijf is onder de CCPA de business en testee zijn service provider, onder de [verwerkersovereenkomst](/dpa) en het Amerikaanse deel daarvan. Gegevens worden gehost in de EU, met sommige subverwerkers in de VS (zie het [privacybeleid](/privacy)), en worden niet gebruikt om AI-modellen te trainen.
- **Bewaartermijn.** Kandidaatgegevens worden 12 maanden na de uitnodiging verwijderd. Waar jouw recht vraagt om gegevens langer te bewaren, zoals vier jaar in Californië, download je de pdf-rapporten en het bestand voor de bias-audit en bewaar je ze zelf; testee bewaart resultaten standaard niet langer.

## Verder lezen

- [Is AI bij werving en selectie legaal in de EU?](/guides/is-ai-hiring-legal-in-the-eu)
- [Is AI bij werving en selectie legaal in het VK?](/guides/is-ai-hiring-legal-in-the-uk)
- [Zo stel je de tijd van een vaardigheidstest in: timer per vraag, lengte en extra tijd](/guides/skills-test-timing-and-extra-time)
- [Selectietests: een praktische gids](/pre-employment-testing)

## Bronnen

- Uniform Guidelines on Employee Selection Procedures, [29 CFR §1607.4(D)](https://www.law.cornell.edu/cfr/text/29/1607.4).
- Regulations to implement the equal employment provisions of the Americans with Disabilities Act, [29 CFR 1630.11](https://www.law.cornell.edu/cfr/text/29/1630.11).
- New York City Local Law 144 of 2021 en 6 RCNY §5-300 en volgende; DCWP, [Automated Employment Decision Tools](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page) en de bijbehorende FAQ.
- Illinois Human Rights Act, 775 ILCS 5/2-102(L), zoals gewijzigd door Public Act 103-0804.
- Colorado SB 26-189.
- California Code of Regulations, title 2, §11013(c); de regels van de California Consumer Privacy Act over geautomatiseerde besluitvormingstechnologie.
