# The FAQ in et; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Mis on prepza?",
        "answer": "Ajapiiranguga intervjuu sinu töökuulutuse põhjal, mis tahes rolli jaoks. Kasuta seda kandidaatide sõelumiseks enne, kui nendega kohtud, või värbamise omaette sammuna: mõlemal juhul näed, kes tööd päriselt tunneb.",
    },
    {
        "key": "roles",
        "question": "Milliste rollide jaoks saan värvata?",
        "answer": "Iga rolli jaoks, kus teadmised loevad: klienditugi, müük, rahandus, tervishoid, oskustööd, inseneeria, turundus ja palju muud. Kui oskad tööd kirjeldada, oskab prepza selle jaoks intervjuu teha.",
    },
    {
        "key": "hiring",
        "question": "Kuidas see töötab?",
        "answer": "Kleebi avalehele töökuulutus, anna oma ettevõttele nimi ja vaata üle teemad, mida prepza pakub. Seejärel kutsu kandidaadid: kirjuta nende e-posti aadressid, kleebi nimekiri või laadi üles fail. Kandidaadid, kes pole mõne päeva jooksul alustanud, saavad ühe meeldetuletuse. Iga kandidaat saab oma küsimused, igal küsimusel on ajapiirang, ja sa näed tema tulemust ning kõiki vastuseid kohe, kui ta lõpetab.",
    },
    {
        "key": "link",
        "question": "Kas saan intervjuu töökuulutusse panna?",
        "answer": "Jah. Lülita intervjuu vahekaardil Kandidaadid sisse jagatav link ja kleebi see oma kuulutusse. Igaüks, kes selle avab, logib sisse ja teeb intervjuu, ning iga inimese eest võetakse tasu nagu kutsutud kandidaadi eest. Link lülitub välja, kui märgid intervjuu palgatuks.",
    },
    {
        "key": "preview",
        "question": "Kas saan intervjuud proovida enne, kui kedagi kutsun?",
        "answer": "Jah. Ava oma intervjuu selle lehelt kandidaadina, tasuta: eelvaated ei ilmu sinu kandidaatide hulka ega küsimuste statistikasse. Võid teha ka ükskõik millise tasuta harjutusintervjuu.",
    },
    {
        "key": "cheating",
        "question": "Kas kandidaadid saavad kasutada tehisaru või vastuseid otsida?",
        "answer": "Iga kandidaat saab oma juhuslikud küsimused oma järjekorras ja igal küsimusel on [ajapiirang](/guides/skills-test-timing-and-extra-time), mida jälgib meie server, nii et vastuste otsimiseks või tehisarult küsimiseks jääb vähe aega. Kandidaadi tulemused näitavad ka, millal kandidaat lehelt lahkus, teksti kopeeris või vastas liiga kiiresti, et küsimust lugeda.",
    },
    {
        "key": "cost",
        "question": "Kui palju see maksab?",
        "answer": "Intervjuude loomine on tasuta. Iga kandidaat, kes vastab vähemalt ühele küsimusele, maksab {candidate} krediiti ({candidate_price}), ja suuremate juurdelaadimiste krediitidega vähem, kuni {cheapest_price}. Sinu esimene ettevõte saab {company} tasuta krediiti, millest piisab tema esimese {company_candidates} kandidaadi jaoks. [Hinnalehel](/pricing) on kõik hinnad.",
    },
    {
        "key": "charged",
        "question": "Millal kandidaadi eest tasu võetakse?",
        "answer": "Kui ta on vastanud vähemalt ühele küsimusele: kui tema intervjuu lõpeb (ta lõpetab selle või aeg saab otsa, kui ta on eemal) või kui tühistad ta. Küsimus, mille aeg sai otsa ilma vastust valimata, ei lähe arvesse. Tema krediidid broneeritakse kutsumisel ja tulevad tagasi, kui tühistad ta enne, kui ta midagi vastab, kui ta ei alusta või kui tema intervjuu lõpeb ilma ühegi vastuseta.",
    },
    {
        "key": "compare_hiring",
        "question": "Milline on hind võrreldes teiste hindamisvahenditega?",
        "answer": "Paljusid hindamisvahendeid müüakse kuu- või aastatellimusena, mille eest maksad ka siis, kui kedagi ei testi. prepzas maksad ainult kandidaatide eest: {candidate} krediiti ({candidate_price}) kandidaadi kohta, ilma lepingu, kasutajatasude ja intervjuu loomise tasuta. Ettevõte, kes kutsub {example_candidates} kandidaati kuus, maksab umbes {example_year_price} aastas. Kui testid igal kuul palju kandidaate, võib tellimus olla odavam, nii et võrdle oma numbritega.",
    },
    {
        "key": "expire",
        "question": "Kas krediidid aeguvad?",
        "answer": "Ei. Krediidid ei aegu kunagi ning tasulisi tellimusi pole. Kui lülitad sisse valikulise automaatse juurdelaadimise, salvestab Paddle sinu kaardi tellimusena hinnaga {zero_price}; maksad ainult selle tehtud juurdelaadimiste eest.",
    },
    {
        "key": "currency",
        "question": "Millises valuutas ma maksan?",
        "answer": "Hinnad on kohalikus valuutas Kanadas, Austraalias, Iisraelis, Poolas, Šveitsis, Jaapanis, Lõuna-Koreas, Taiwanis, Hongkongis, Tais, Singapuris ja Indias; ülejäänud ELis ning Islandil, Liechtensteinis ja Norras eurodes; Ühendkuningriigis naelsterlingites; ja mujal USA dollarites. Sinu konto ja iga ettevõte jäävad selle riigi valuutale, kus need loodi, ükskõik kuhu sa reisid: enda oma muudad seadetes, ettevõtte oma tema nupu „Laadi juurde“ kõrval (omanikud ja administraatorid). Ettevõtte juurdelaadimised, ka automaatsed, võetakse alati ettevõtte valuutas.",
    },
    {
        "key": "refunds",
        "question": "Kas saan raha tagasi?",
        "answer": "Jah, viimase 14 päeva jooksul ostetud ja kulutamata krediitide eest: Paddle'i kaudu või meile kirjutades. Tasuta krediite, näiteks tervituskingitust, ei hüvitata. Üksikasjad on [tingimustes](/terms).",
    },
    {
        "key": "scorecards",
        "question": "Mida kandidaatide tulemused näitavad?",
        "answer": "Iga vastust, kas see oli õige ja kui kaua see aega võttis. Hinne on teenitud punktide protsent: iga küsimus annab ühe punkti ja „vali kõik õiged“ küsimus annab osa sellest iga märgitud õige variandi eest, kuid mitte midagi, kui märgitud on vale variant. Hinded on rohelised või punased vastavalt läbimise lävele, mille intervjuule määrasid. Tulemused märgivad ka vastused, mis anti liiga kiiresti, et küsimust lugeda, korrad, kui kandidaat lehelt lahkus, ja kopeerimiskatsed.",
    },
    {
        "key": "reports",
        "question": "Kas saan tulemusi värbava juhiga jagada?",
        "answer": "Jah. Laadi alla PDF-aruanne ühe kandidaadi või intervjuu kõigi kandidaatide kohta, saada see e-postiga otse prepzast või saada lühike kokkuvõte WhatsAppis, Telegramis, Viberis või LINE'is.",
    },
    {
        "key": "action_log",
        "question": "Kas saan näha, kes minu ettevõttes mida tegi?",
        "answer": "Jah, kui oled ettevõtte omanik. Selle vahekaardil Toimingute logi on kõik, mida liikmed tegid, uuemad eespool: kandidaatide kutsumine või eemaldamine, tulemuste vaatamine ning intervjuude, meeskonna, arvelduse ja integratsioonide muutmine, koos sellega, kes ja millal seda tegi ning kas assistent, AI-rakendus või API tegi seda tema nimel. Saad seda filtreerida liikme, toimingu liigi ja kuupäevade järgi. Toiminguid hoitakse 12 kuud.",
    },
    {
        "key": "integrations",
        "question": "Kas prepza töötab minu ATS-i või muude tööriistadega?",
        "answer": "Jah, ilma lisatasuta. Ühenda Workable, Greenhouse, Teamtailor, Recruitee või Breezy HR oma ettevõtte vahekaardil Integratsioonid: kandidaadid, kelle viid etappi, saavad intervjuu ja nende tulemused lähevad tagasi ATS-i ([kuidas ühendada oskustestid ATS-iga](/guides/ats-integration-skills-tests)). Slack saab postitada sinu ettevõtte teavitusi kanalisse ja API kaudu saab sinu enda platvorm luua intervjuusid, kandidaate kutsuda ja hallata ning nende tulemusi vastu võtta, kusjuures iga API-võti saab teha ainult seda, mille talle märgid; vaata [API dokumentatsiooni](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Kas saan prepzat kasutada Claude'i, ChatGPT või oma AI-agendi kaudu?",
        "answer": "Jah. Lisa prepza Claude'i või ChatGPT-sse konnektorina (sammud on sinu ettevõtte vahekaardil Integratsioonid) ja luba see prepzas. Seejärel töötab rakendus sinu nimel ja sinu õigustega sinu ettevõtete, intervjuude ja kandidaatide tulemustega; enamik rakendusi küsib sinult enne, kui midagi muudab. Oma kontot või ettevõtet saad kustutada ainult prepzas. See, mida rakendus loeb, jõuab selle rakenduse tingimuste alusel tema pakkujani. Ühenduse saad igal ajal samal vahekaardil katkestada. Ühendada saab ka teisi AI-rakendusi ja ise loodud agente: arendajate dokumentatsiooni [MCP-vahekaardil](/api-docs?tab=mcp) on sammud ja näidisagendid ning serveris töötav agent saab sisse logida API-võtmega, millel on AI-agentide õigus. [Juhend AI-agentide, MCP ja API-de kohta](/guides/ai-agents-mcp-and-api) selgitab, milleks igaüks neist on.",
    },
    {
        "key": "candidates",
        "question": "Mida kandidaadid näevad?",
        "answer": "Sinu ettevõtte nime ja logo sinu ettevõtte värvides ja fondis (määratud selle vahekaardil Bränd), enne alustamist seda, mida oodata, ja seejärel ühe ajapiiranguga küsimuse korraga. Nad ei näe kunagi oma tulemust ega seda, kas vastus oli õige.",
    },
    {
        "key": "verified",
        "question": "Mida kinnitusmärk tähendab?",
        "answer": "Seda, et ettevõtte omanik või administraator logis sisse ettevõtte veebilehe domeeni e-posti aadressiga, näiteks you@acme.com, ja meie meeskond vaatas ettevõtte seejärel üle. Lisa veebileht oma ettevõtte päises nupuga Kinnita; tasuta e-postiteenused ei sobi. Kuni ülevaatus on ootel, näeb su meeskond nime kõrval kella, ja ettevõtte ümbernimetamine saadab selle uuesti ülevaatusele. Märk on näha ettevõtte nime kõrval, ka kutsetes.",
    },
    {
        "key": "languages",
        "question": "Milliseid keeli toetatakse?",
        "answer": "{count} keelt saidi, intervjuude ja e-kirjade jaoks. Vali, mis keeles intervjuu kirjutatakse, olenemata sellest, mis keeles on töökuulutus.",
    },
    {
        "key": "privacy",
        "question": "Mis saab töökuulutustest ja vastustest?",
        "answer": "Töökuulutusi kasutatakse sinu ettevõtte intervjuude loomiseks ja kandidaatide vastuseid nende hindamiseks sinu ettevõtte jaoks. prepza loodud küsimusi võidakse taaskasutada ka teiste ettevõtete intervjuudes ja harjutusintervjuudes, ilma millegita, mis tuvastaks sind, sinu ettevõtet või kedagi teist; saad intervjuu küsimused sellest välja jätta selle intervjuu seadetes. Samuti tuletab prepza sellest, kuidas küsimustele vastatakse, üldisi, anonüümitud küsimuste kvaliteedi mustreid, et parandada küsimuste loomist. [Privaatsuspoliitika](/privacy) selgitab, mida me säilitame, kui kaua ja millised on kõigi õigused.",
    },
    {
        "key": "eu_ai_law",
        "question": "Kas ELis on seaduslik kasutada tehisaru kandidaatide eelvalikuks?",
        "answer": "Jah, reeglite järgi. ELi tehisintellekti määruse (AI Act) alusel on kandidaate hindavad tööriistad väga tõenäoliselt suure riskiga, kohustustega alates 2. detsembrist 2027, ja GDPR kehtib juba praegu: värbamisotsuse teeb inimene, kandidaatidele öeldakse, et kasutatakse tehisaru, ja kõik dokumenteeritakse. prepza töötab just nii: tehisaru koostab küsimused, sinu ettevõtte inimesed vaatavad tulemused üle ja otsustavad ning kandidaatidele öeldakse seda enne alustamist. See ei ole õigusnõustamine; [Kas AI kasutamine värbamisel on ELis seaduslik?](/guides/is-ai-hiring-legal-in-the-eu) selgitab reegleid ja tähtaegu.",
    },
    {
        "key": "emails",
        "question": "Milliseid e-kirju prepza saadab ja kuidas neid peatada?",
        "answer": "Teenusekirjad, nagu kutsed, aruanded, makseprobleemid ja meie tingimuste muudatused, saadetakse alati. Ülejäänud, näiteks igapäevase tegevuste kokkuvõtte, meeldetuletused ja tooteuudised, valid seadetes jaotises E-kirjad või peatad iga kirja lingiga „Loobu tellimusest“. Kandidaadid saavad sinu ettevõtte kirjad või ühe intervjuu meeldetuletused peatada oma kutsetes ja meeldetuletustes olevate linkidega. prepza uudised on sinu teavitustes, ülaosas oleva kella all; olulisemad uudised tulevad ka e-kirjaga tooteuudisena, kuid ainult siis, kui see seade on sees.",
    },
    {
        "key": "delete",
        "question": "Kas saan oma konto kustutada?",
        "answer": "Jah, seadetes. Sinu konto ja andmed kustutatakse ning enne seda saad oma andmetest koopia alla laadida.",
    },
    {
        "key": "report",
        "question": "Kuidas probleemist teada anda?",
        "answer": "Kirjuta meile [kontaktilehel](/contact) ja kleebi selle ID, millest jutt käib: „kopeeri id“ on ettevõtte, intervjuu või kandidaadi nime all, sinu konto oma aga kontomenüüs ja seadetes. ID järgi leiame selle kohe üles.",
    },
]
