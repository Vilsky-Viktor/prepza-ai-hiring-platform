---
title: "AI-agendid, MCP ja API-d: mis need on ja kuidas neid värbamisel kasutada"
seoTitle: "AI-agendid, MCP ja API-d värbamisel: kuidas neid kasutada"
description: "Mis on AI-agent, MCP ja API, kuidas neid värbamisel turvaliselt kasutada ja prepzat juhtida selle AI-assistendi, Claude'i, ChatGPT või oma platvormi kaudu."
updated: "2026-10-22"
---

# AI-agendid, MCP ja API-d: mis need on ja kuidas neid värbamisel kasutada

Enamik inimesi kohtus AI-ga esimest korda vestlusaknas: sina küsid, see vastab. AI-agent läheb sammu kaugemale. See oskab sinu tööriistadest asju järele vaadata ja sinu palvel neis ka midagi teha: luua intervjuu, kutsuda nimekirja kandidaate, öelda, kes sai eelmisel nädalal kõrgeima tulemuse. Model Context Protocol (MCP) on standard, mille abil sinu juba kasutatav AI-vestlus, näiteks Claude või ChatGPT, saab selliste tööriistadega ühenduse luua. API on aga vanem ja täpsem viis, kuidas tarkvara räägib tarkvaraga, ilma et vahel oleks AI-d.

See juhend selgitab lihtsate sõnadega kõiki kolme: milleks need värbamisel head on, millele tähelepanu pöörata ja kuidas neid prepzaga kasutada.

## Mis on AI-agent

Vestlusrobot kirjutab ainult teksti. Agent on keelemudel, millel on **tööriistad**: väikesed, selgelt piiritletud toimingud, mida ta tohib käivitada, näiteks „näita selle intervjuu kandidaate“ või „kutsu see e-posti aadress“. Kui sa midagi küsid, otsustab agent, milliseid tööriistu kasutada, loeb, mida need tagastavad, ja vastab selle põhjal, mitte mälu järgi.

| Vestlusrobot | AI-agent |
| --- | --- |
| Vastab selle põhjal, mida õppis treenimisel | Vastab sinu ajakohaste andmete põhjal, mida loeb tööriistade kaudu |
| Oskab ainult kirjeldada, kuidas midagi teha | Oskab seda teha, kui sa palud ja lubad |
| Arvab, kui ei tea | Vaatab järele või ütleb, et ei saa |
| Elab ühes aknas | Töötab tööriistades, millega sa ta ühendad |

Tööriistad teevad agendi kasulikuks ja otsustavad ka, kas see on turvaline või mitte. Hea agent saab kasutada ainult talle antud tööriistu, ainult sinu õigustega, ja teeb ainult seda, mida sa palusid.

## Mis on MCP

Model Context Protocol on avatud standard, mille Anthropic tutvustas 2024. aasta lõpus ja mida nüüd toetavad Claude, ChatGPT ning paljud teised AI-rakendused ja arendajatööriistad. Seda võrreldakse sageli AI USB-C pordiga: selle asemel et iga AI-rakendus ehitaks oma ühenduse iga tööriistaga, pakub tööriist ühte **MCP-serverit** ja iga AI-rakendus, mis MCP-d räägib, saab seda kasutada.

MCP-server ütleb AI-rakendusele kolm asja:

1. **Millised tööriistad on olemas,** igaühel nimi, kirjeldus ja andmed, mida see vajab.
2. **Millised tööriistad ainult loevad** ja millised midagi muudavad, et AI-rakendus saaks enne muudatust sinult küsida.
3. **Kes sa oled,** sisselogimise kaudu, mille kinnitad ühe korra, nii et iga päring tehakse sinu nimel ja sinu õigustega.

Sinu jaoks tähendab see, et saad tööriistaga töötada samast vestlusest, mida juba kasutad, ilma andmeid akende vahel kopeerimata.

## Mis on API ja mille poolest see erineb

API (rakendusliides) on kogum kindlaid päringuid, mida üks programm saab teisele saata: „näita selle intervjuu kandidaate“, „kutsu see e-posti aadress“. Sinu arendajad kirjutavad koodi, mis neid saadab. AI-d pole selles mängus: sama päring teeb alati sama asja, ja just seda tahad automaatikalt, mis töötab iseseisvalt.

| | Mira, AI-assistent (rakenduses) | MCP (Claude'is või ChatGPT-s) | API |
| --- | --- | --- | --- |
| Kes seda kasutab | Sina, prepzas | Sina, oma AI-vestluses | Sinu platvormi kood |
| Kuidas küsid | Oma sõnadega | Oma sõnadega | Kindlad päringud, mille kirjutab arendaja |
| Kes muudatused kinnitab | Sina, kaardil | Sina, oma AI-rakenduses | Sinu kood, nii nagu see on kirjutatud |
| Sobib kõige paremini | Kiireteks küsimusteks ja ülesanneteks | prepza kombineerimiseks sinu teiste tööriistade ja failidega | Automaatikaks, mis töötab ilma, et keegi jälgiks |
| Logib sisse kui | Sina | Sina | Ettevõtte võti |

Kasuta Mirat või MCP-d, kui protsessis osaleb inimene. Kasuta API-t, kui sinu enda süsteem peab ise kandidaate kutsuma ja tulemusi koguma, näiteks karjäärilehelt või sisemisest personalitööriistast.

## Milleks see värbamisel hea on

Värbamine koosneb paljudest väikestest korduvatest sammudest, mis on laiali eri tööriistades. Just neis on agent hea:

- **Küsimused sinu värbamistoru kohta.** „Millised kandidaadid läbisid sel nädalal Senior Backendi?“, „Kes pole veel oma intervjuud alustanud?“, „Milline on meie keskmine hinne andmeanalüütiku ametikohal?“
- **Seadistamine.** „Loo selle töökuulutuse põhjal intervjuu“, „Sea läbimise läveks 70%“, „Anna sellele kandidaadile 50% lisaaega.“
- **Hulgitöö.** „Kutsu need 12 inimest frontendi intervjuule“, kleebituna otse e-kirjast või tabelist.
- **Allikate kombineerimine.** Claude'is või ChatGPT-s saad prepzat kombineerida oma teiste ühendatud tööriistade ja failidega: võrrelda dokumentides olevat töökuulutust intervjuu teemadega või koostada sõnumi lõppvooru kandidaatidele.

Mida ta tegema ei peaks, on värbamisotsuse tegemine. Hinne toetab inimese otsustust, aga ei asenda seda. Lase agendil sorteerida, kokku võtta ja ette valmistada ning jäta otsus inimesele. Vaata [Kas AI kasutamine värbamisel on ELis seaduslik?](/guides/is-ai-hiring-legal-in-the-eu), miks see on oluline ka õiguslikult.

## Millele tähelepanu pöörata

AI ühendamine oma värbamisandmetega nõuab sama hoolt kui kolleegile ligipääsu andmine.

| Risk | Mis aitab |
| --- | --- |
| Agent teeb midagi, mida sa ei mõelnud | Muudatused vajavad enne sinu kinnitust ja ta teeb ainult seda, mida palusid |
| Ta näeb rohkem, kui peaks | Ta tegutseb sinu nimel: näeb seda, mida sina näed, mitte rohkem |
| Andmetesse peidetud juhised | Kandidaatide nimed, vastused ja dokumendid on andmed, mitte kunagi juhised, mida täita |
| Saladused satuvad vestlusesse | API-võtmed ja paroolid ei käi kunagi läbi vestluse |
| Pöördumatud vead | Konto või ettevõtte kustutamine jääb rakendusse, eraldi kinnituse taha |
| Andmed lahkuvad sinu tööriistadest | Andmed jõuavad AI-rakendusse, mille ühendad, selle rakenduse tingimustel: ühenda ainult rakendusi, mida sinu ettevõte lubab |
| Kontrolli alt väljuv kasutus | Piirangud, mitu toimingut tunnis tehakse |

Enne kui ühendad mõne AI-rakenduse tööandmetega, kontrolli oma ettevõtte AI-tööriistade poliitikat ja ütle kandidaatidele oma privaatsusteates, millised teenused nende andmeid töötlevad.

## Kolm viisi töötada prepzaga väljaspool selle lehti

### 1. Mira, sisseehitatud AI-assistent

Vali mis tahes lehe päises **küsi Miralt**. Mira, prepza AI-assistent, tunneb sinu ettevõtteid, intervjuusid, kandidaate, krediite ja integratsioone ning teab, kuidas prepza töötab. Ta vastab sinu keeles ning sa võid kirjutada või rääkida.

- **Ta vastab sinu andmete põhjal,** sama vaatega kui sinul: administraator näeb seda, mida administraator, vaataja seda, mida vaataja.
- **Ta teab, millisel lehel sa oled.** Küsi „Mida ma sellel lehel teha saan?“, et saada selle lehe juhend, või intervjuu kandidaatide juures „Kes on siin parim?“, ja ta vastab just selle intervjuu kohta, küsimata, millist sa mõtled.
- **Ta valmistab muudatused ette, sina kinnitad.** Kui palud tal kandidaate kutsuda, näitab ta kaarti, kus on täpselt kirjas, mis juhtub, näiteks „Kutsu 12 kandidaati intervjuule Backend developer“. Midagi ei käivitu enne, kui valid Kinnita.
- **Ta näitab oma allikaid.** Vastuse all näed kandidaate või intervjuusid, mida ta kasutas, ja linki lehele, kust need pärinevad.
- **Ta püsib teemas.** Ta vastab küsimustele prepza ja sellega värbamise kohta ning ütleb ülejäänust ära.

### 2. prepza Claude'is või ChatGPT-s, MCP kaudu

Kui sinu meeskond juba töötab Claude'is või ChatGPT-s, saad prepza sinna tuua. prepza MCP-server pakub samu tööriistu mis Mira, sisseehitatud assistent.

**Ühendamiseks:**

1. Ava prepzas ettevõtte vahekaart **Integratsioonid** ja vali **AI-rakendused**. Kopeeri serveri aadress: `https://prepza.ai/mcp`.
2. **Claude'is:** ava Seaded, siis Konnektorid, ja lisa selle aadressiga kohandatud konnektor. **Claude Code'is:** käivita `claude mcp add --transport http prepza https://prepza.ai/mcp`. **ChatGPT-s:** lisa see kohandatud konnektorina rakenduste ja konnektorite seadetes.
3. Sinu AI-rakendus avab prepza sisselogimise. Logi sisse, kontrolli, milline rakendus luba küsib, ja vali **Luba**. Kui see tohib ainult lugeda, lülita enne välja **Luba muudatused**.

Edaspidi küsi oma vestluses nii, nagu küsiksid kolleegilt: „Kes on prepzas kolm parimat kandidaati Product designeri ametikohale?“ Enamik AI-rakendusi küsib sinult enne muudatust ja hoiatab enne kõike, mida ei saa tagasi võtta: prepza ütleb neile, millised toimingud midagi muudavad või kustutavad.

**Mis jääb samaks nagu rakenduses:**

- **Sinu õigused.** Ta tegutseb sinu nimel igas ettevõttes, kuhu kuulud, sinu rolliga igas neist.
- **Krediidid ja piirangud.** Kandidaadi kutsumine maksab sama palju kui rakenduses ja kehtivad samad e-kirjade piirangud.
- **Logi.** Kõik, mida tehisintellekti rakendus sinu eest teeb, kuvatakse ettevõtte toimingute logis tehisintellekti rakenduse kaudu tehtuna, alates teemade kinnitamisest ja tulemuste vaatamisest kuni lisaaja andmise või kandidaadi tühistamiseni. Ettevõtte omanik loeb seda ettevõtte vahekaardil **Toimingute logi**.
- **Ettevõte otsustab.** Omanikud ja administraatorid saavad keelata tehisintellekti rakendustel ettevõtte andmete kasutamise valikuga **Luba selles ettevõttes tehisintellekti rakendused** ettevõtte tehisintellekti rakenduste lehel.
- **Mida ta teha ei saa.** Ta ei näe sinu parooli ega API-võtmeid ning ei saa kustutada sinu kontot ega ettevõtet. Need jäävad rakendusse.

**Ühenduse katkestamiseks** eemalda konnektor oma AI-rakenduses või vali selle kõrval **Katkesta ühendus** vahekaardi Integratsioonid jaotises **AI-rakendused**. See lakkab kohe töötamast.

**Muud rakendused ja sinu oma agendid.** Arendajate dokumentatsiooni [MCP-vahekaardil](/api-docs?tab=mcp) on sammud rakenduste Gemini CLI, Cursor, VS Code ja Le Chat jaoks ning täielikud näidisagendid keeltes Python ja TypeScript. Serveris töötav agent, mille sisselogimist pole kellelgi kinnitada, kasutab ettevõtte API-võtit õigusega **Kasutamine AI-agentidega (MCP)**: see töötab ainult selles ettevõttes ja ainult nende tööriistadega, mida võtme ülejäänud õigused lubavad. Kõik, mida see teeb, on ettevõtte toimingute logis näidatud võtme nime all.

### 3. Sinu oma platvorm, API kaudu

Automaatikaks ilma AI-ta on prepzal API, mida kirjeldab selle [arendajate dokumentatsioon](/api-docs).

1. Omanik või administraator avab ettevõtte vahekaardi **Integratsioonid**, siis **API**, ja valib **Uus võti**. Pane sellele nimeks platvorm, mis seda kasutama hakkab, vali, millal see aegub, ja märgi ainult see, mida see vajab: töölaua võti ainult loeb, karjäärilehe võti ka kutsub. Õigusi saad hiljem lisada või ära võtta. Võtit näidatakse ainult üks kord; hoia seda turvalises kohas.
2. Sinu platvorm saadab selle võtmega päringuid: näitab ettevõtte intervjuusid, näitab või loeb kandidaate koos nende hinde, läbimise ja aususe märgetega ning kutsub kandidaadi.
3. Lisa **webhook**: aadress sinu platvormil, mida prepza kutsub allkirjastatult kui kandidaat alustab, lõpetab, kutse ei jõua temani, tema kutse aegub või ta eemaldatakse, ning kui intervjuu on valmis, et sa ei peaks pidevalt järele küsima. API lehelt saad sellele saata testsündmuse ja näha selle saatmislogi.

Iga kandidaadiga tuleb kaasa link tema täielikele tulemustele prepzas ja, kuni ta pole lõpetanud, tema enda kutselink, nii et sinu platvorm saab selle soovi korral saata oma sõnumis. Kui sinu platvorm juba teab, kes kandidaat on, kutsu ta ilma sisselogimiseta: prepza ei saada e-kirju ja kandidaat teeb intervjuu lingi kaudu ilma prepzasse sisse logimata, nii et saada link ainult talle. Kutse võib ka viia kandidaadi lõpetamislehel oleva nupuga tagasi sinu saidile (ükskõik millisele https-aadressile) ning määrata heleda või tumeda teema sinu ettevõtte värvides. Sinu enda leht saab prepza SDK abil intervjuu ise kuvada, kuid ainult saitidel, mille sinu ettevõte on oma API lehel lubanud. API ja webhookid ei sõltu neist saitidest: selle asemel saab iga võtme piirata sinu serverite IP-aadressidega. Kinnitamine lisab ainult kinnitatud ettevõtte märgi.

Kehtib sama reegel kui mujal: hinne toetab inimese otsust, nii et ära lükka kandidaate selle põhjal automaatselt tagasi.

## Mida millal kasutada

Lähtu sellest, kes tööd teeb ja kui sageli.

| Sinu olukord | Kasuta |
| --- | --- |
| Oled prepzas ja tahad kiiret vastust: kes läbis, kes pole alustanud, palju krediiti on alles | Mirat, sisseehitatud assistenti |
| Tahad paari sõnaga midagi seadistada: intervjuu töökuulutuse põhjal, läbimise lävi, lisaaeg | Mirat, sisseehitatud assistenti |
| Töötad niikuinii terve päeva Claude'is või ChatGPT-s ja tahad prepzat ka sinna | MCP-d |
| Ülesanne vajab prepzat ja veel midagi: sinu dokumente, e-kirjade mustandeid, mõnda teist ühendatud tööriista | MCP-d |
| Liikvel olev värbaja tahab värbamistoru telefonis oleva AI-rakenduse kaudu üle vaadata | MCP-d |
| Sinu karjäärileht või personalisüsteem peab kandidaate ise kutsuma, ilma et keegi klõpsaks | API-t |
| Tulemused peavad jõudma sinu enda andmebaasi või töölauale kohe, kui kandidaadid lõpetavad | API-t koos webhookiga |
| Sinu ATS on üks neist, millega prepza ühendub (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Mitte ühtki neist: ühenda ATS vahekaardil Integratsioonid. Vaata [Kuidas ühendada oskustestid oma ATS-süsteemiga](/guides/ats-integration-skills-tests) |

Lihtne rusikareegel:

- **Inimene küsib ja kontrollib iga muudatust:** Mira prepzas või MCP, kui see inimene töötab niikuinii Claude'is või ChatGPT-s.
- **Tarkvara tegutseb iseseisvalt, iga kord samamoodi:** API.
- **Alustuseks:** proovi esmalt Mirat, sisseehitatud assistenti. Ta ei vaja seadistamist ja see, mida õpid, kehtib ka MCP puhul.

Need töötavad ka koos. Meeskond võib saata kutseid oma personalisüsteemist API kaudu, samal ajal kui värbajad küsivad tulemuste kohta Miralt või oma AI-vestluselt.

## Kuidas saada häid tulemusi

- **Nimeta asju.** „Senior Backendi intervjuu“ toimib paremini kui „see intervjuu“.
- **Küsi üks samm korraga,** kui see on oluline. Kontrolli tulemust ja küsi siis järgmist.
- **Loe kinnitus läbi enne, kui lubad.** See näitab täpselt, mis käivitub.
- **Küsi, kust number tuli.** Hea agent oskab näidata kandidaate või lehte, mis selle taga on.
- **Jäta otsused inimestele.** Kasuta agenti leidmiseks, sorteerimiseks ja ettevalmistamiseks; otsusta ise.

## Hinnad

Mira, MCP-ühendus ja API on tasuta. Maksad ainult kandidaatide eest, nagu alati: iga kandidaadi eest, kes vastab vähemalt ühele küsimusele, ilma tellimuseta. Vaata [hindu](/pricing).

## Loe ka

- [Kuidas ühendada oskustestid oma ATS-süsteemiga](/guides/ats-integration-skills-tests)
- [Inseneride intervjueerimine AI ajastul](/guides/interviewing-in-the-age-of-ai)
- [Kas AI kasutamine värbamisel on ELis seaduslik?](/guides/is-ai-hiring-legal-in-the-eu)
