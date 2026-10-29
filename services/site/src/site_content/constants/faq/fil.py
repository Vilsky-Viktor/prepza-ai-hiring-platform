# The FAQ in fil; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Ano ang prepza?",
        "answer": "Isang timed interview mula sa iyong job description, para sa kahit anong role. Gamitin ito para i-screen ang mga aplikante bago mo sila makilala, o bilang mismong hakbang ng hiring: alinman dito, makikita mo kung sino ang talagang marunong sa trabaho.",
    },
    {
        "key": "roles",
        "question": "Para sa aling mga role ako puwedeng mag-hire?",
        "answer": "Kahit anong role kung saan mahalaga ang kaalaman: support, sales, finance, healthcare, trades, engineering, marketing at iba pa. Kung kaya mong ilarawan ang trabaho, kayang gumawa ng prepza ng interview para dito.",
    },
    {
        "key": "hiring",
        "question": "Paano ito gumagana?",
        "answer": "Mag-paste ng job description sa home page, pangalanan ang iyong kumpanya at tingnan ang mga topic na iminumungkahi ng prepza. Pagkatapos ay mag-imbita ng mga aplikante: i-type ang kanilang mga email, mag-paste ng listahan o mag-upload ng file. Ang mga aplikanteng hindi pa nagsisimula pagkalipas ng ilang araw ay makakatanggap ng isang paalala. Bawat aplikante ay may sariling mga tanong at timer sa bawat isa, at makikita mo ang kanilang score at bawat sagot sa sandaling matapos sila.",
    },
    {
        "key": "link",
        "question": "Puwede ko bang ilagay ang interview sa isang job ad?",
        "answer": "Oo. I-on ang shareable link ng interview sa tab nitong Mga setting at i-paste ito sa iyong ad. Ang sinumang magbukas nito ay magsa-sign in at sasagot sa interview, at sinisingil ang bawat tao tulad ng isang inimbitahang aplikante. Mag-o-off ang link kapag minarkahan mo ang interview bilang na-hire.",
    },
    {
        "key": "preview",
        "question": "Puwede ko bang subukan ang interview bago mag-imbita ng kahit sino?",
        "answer": "Oo. Buksan ang iyong interview bilang aplikante mula sa page nito, nang libre: hindi lumalabas ang mga preview sa iyong mga aplikante o sa statistics ng mga tanong. Puwede mo ring sagutan ang alinman sa mga libreng practice interview.",
    },
    {
        "key": "cheating",
        "question": "Puwede bang gumamit ng AI ang mga aplikante o hanapin ang mga sagot?",
        "answer": "Bawat aplikante ay may sariling random na mga tanong sa sarili nilang pagkakasunod-sunod, may [timer sa bawat tanong](/guides/skills-test-timing-and-extra-time) na binabantayan ng aming server, kaya kaunti lang ang oras para maghanap ng sagot o magtanong sa AI. Ipinapakita rin ng scorecard ng aplikante kung kailan siya umalis sa page, kumopya ng text, o sumagot nang masyadong mabilis para nabasa ang tanong. Kapag tapos na siya, itinuturo rin ng kanyang page ang mga pattern ng sagot na kadalasang naiiwan kapag ipinapasa ang mga tanong sa AI, gaya ng halos parehong oras sa bawat tanong o tama ang mahihirap na tanong habang mali ang madadali, at nagmumungkahi ng mga tanong na tama ang sagot niya para itanong sa isang live na interview. Ang pattern ay dahilan para magtanong, hindi patunay. Bago magsimula, kinukumpirma rin ng bawat aplikante na sasagot siya nang mag-isa, nang walang AI tool o tulong ng ibang tao, at ipinapakita ito ng kanyang scorecard.",
    },
    {
        "key": "cost",
        "question": "Magkano ito?",
        "answer": "Libre ang paggawa ng interview. Bawat aplikanteng sumagot ng kahit isang tanong ay {candidate} credits ({candidate_price}), at mas mura gamit ang credits mula sa mas malalaking top-up, hanggang {cheapest_price}. Makakatanggap ang iyong unang kumpanya ng {company} libreng credits, sapat para sa unang {company_candidates} aplikante nito. Nakalista sa [pricing page](/pricing) ang bawat presyo.",
    },
    {
        "key": "charged",
        "question": "Kailan sinisingil ang isang aplikante?",
        "answer": "Kapag may nasagot na siyang kahit isang tanong: kapag natapos ang interview niya (tinapos niya ito, o naubos ang oras nito habang wala siya), o kapag binawi mo siya. Hindi binibilang ang tanong na naubusan ng oras nang walang napiling sagot. Itinatabi ang credits niya kapag inimbitahan mo siya, at ibinabalik kung bawiin mo siya bago siya makasagot ng anuman, kung hindi siya kailanman magsimula, o kung matapos ang interview niya nang wala siyang nasagot.",
    },
    {
        "key": "compare_hiring",
        "question": "Paano maihahambing ang presyo sa ibang assessment tool?",
        "answer": "Maraming assessment tool ang ibinebenta bilang buwanan o taunang subscription na binabayaran kahit wala kang tine-test. Sa prepza, nagbabayad ka lang kada aplikante: {candidate} credits ({candidate_price}), walang kontrata, walang bayad kada user, at walang bayad sa paggawa ng interview. Ang kumpanyang nag-iimbita ng {example_candidates} aplikante kada buwan ay nagbabayad ng mga {example_year_price} kada taon. Kung maraming aplikante ang tine-test mo buwan-buwan, maaaring mas mura ang subscription, kaya ihambing sa sarili mong mga numero.",
    },
    {
        "key": "expire",
        "question": "Nag-e-expire ba ang credits?",
        "answer": "Hindi. Hindi kailanman nag-e-expire ang credits, at walang bayad na subscription. Kung bubuksan mo ang opsyonal na awtomatikong top-up, ise-save ng Paddle ang card mo bilang {zero_price} na subscription; ang mga top-up lang na ginagawa nito ang babayaran mo.",
    },
    {
        "key": "currency",
        "question": "Anong currency ang ibabayad ko?",
        "answer": "Nasa lokal na currency ang mga presyo sa Canada, Australia, Israel, Poland, Switzerland, Japan, South Korea, Taiwan, Hong Kong, Thailand, Singapore at India; sa euro sa iba pang bahagi ng EU at sa Iceland, Liechtenstein at Norway; sa pound sa UK; at sa US dollars sa ibang lugar. Pinananatili ng account mo at ng bawat kumpanya ang currency ng bansa kung saan sila ginawa, saan ka man bumiyahe: palitan ang sa iyo sa Mga setting, at ang sa isang kumpanya sa tabi ng button nitong Mag-top up (mga owner at admin). Ang mga top-up ng isang kumpanya, pati ang mga awtomatiko, ay laging sinisingil sa currency ng kumpanya.",
    },
    {
        "key": "refunds",
        "question": "Puwede ba akong ma-refund?",
        "answer": "Oo, para sa credits na binili mo sa nakaraang 14 na araw at hindi pa nagagastos: sa Paddle o sa pagsulat sa amin. Hindi nire-refund ang libreng credits, gaya ng welcome gift. Nasa [terms](/terms) ang mga detalye.",
    },
    {
        "key": "scorecards",
        "question": "Ano ang ipinapakita ng scorecard ng aplikante?",
        "answer": 'Bawat sagot, kung tama ito at gaano katagal ito. Ang grade ay ang porsiyento ng puntos na nakuha: bawat tanong ay isang puntos, at ang tanong na "piliin ang lahat ng tama" ay nagbibigay ng bahagi nito sa bawat tamang opsyong na-check, at wala kung may na-check na mali. Berde o pula ang mga grade batay sa passing grade na itinakda mo para sa interview. Nagfa-flag din ang scorecard ng mga sagot na masyadong mabilis para nabasa ang tanong, mga pagkakataong umalis ang aplikante sa page, at mga pagtatangkang mangopya.',
    },
    {
        "key": "reports",
        "question": "Puwede ko bang i-share ang mga resulta sa isang hiring manager?",
        "answer": "Oo. Mag-download ng PDF report para sa isang aplikante o para sa lahat ng aplikante ng isang interview, i-email ito direkta mula sa prepza, o magpadala ng maikling buod sa WhatsApp, Telegram, Viber o LINE.",
    },
    {
        "key": "action_log",
        "question": "Puwede ko bang makita kung sino ang gumawa ng ano sa kumpanya ko?",
        "answer": "Oo, kung ikaw ang may-ari ng kumpanya. Nakalista sa tab na Log ng aksyon nito ang lahat ng ginawa ng mga miyembro nito, simula sa pinakabago: pag-imbita o pag-alis ng mga aplikante, pagtingin sa mga resulta, at pagbabago sa mga interview, sa team, sa billing at sa mga integration, kasama kung sino ang gumawa, kailan, at kung ang assistant, isang AI app o ang API ang gumawa nito para sa kanila. Puwede mo itong i-filter ayon sa miyembro, uri ng aksyon at petsa. Itinatago ang mga aksyon nang 12 buwan.",
    },
    {
        "key": "notes",
        "question": "Puwede bang magtala ng mga note ang team ko tungkol sa isang interview?",
        "answer": "Oo. May tab na Mga note ang bawat interview kung saan nagsusulat ang team mo ng mga plain-text na note tungkol sa hiring, gaya ng kung sino ang susunod na tatawagan o, para sa isang recruitment agency, kung para saang kliyente ang interview. Puwedeng magsulat ng note ang bawat miyembro, pati ang mga viewer, at i-edit ang sarili nilang note; puwede itong i-delete ng sumulat, ng mga may-ari at ng mga admin. Puwedeng mag-pin ng isang note ang mga may-ari at admin, na lalabas sa ilalim ng pangalan ng interview. Hindi kailanman nakikita ng mga aplikante ang mga note.",
    },
    {
        "key": "integrations",
        "question": "Gumagana ba ang prepza sa ATS ko o sa iba pang tool?",
        "answer": "Oo, nang walang dagdag na bayad. I-connect ang Workable, Greenhouse, Teamtailor, Recruitee o Breezy HR sa tab na Mga integration ng iyong kumpanya: makukuha ng mga aplikanteng ililipat mo sa isang stage ang interview, at babalik sa ATS ang mga resulta nila ([paano ikonekta ang skills tests sa iyong ATS](/guides/ats-integration-skills-tests)). Kayang i-post ng Slack ang mga notification ng iyong kumpanya sa isang channel, at sa pamamagitan ng API, makakagawa ang sarili mong platform ng mga interview, makakapag-imbita at makakapamahala ng mga aplikante, at makakatanggap ng mga resulta nila, at limitado ang bawat API key sa kung ano ang i-check mo para rito; tingnan ang [Dokumentasyon ng API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Puwede ko bang gamitin ang prepza mula sa Claude, ChatGPT o sarili kong AI agent?",
        "answer": "Oo. Idagdag ang prepza sa Claude o ChatGPT bilang connector (nasa tab na Mga integration ng iyong kumpanya ang mga hakbang) at payagan ito sa prepza. Pagkatapos, gagamitin ng app ang iyong mga kumpanya, interview at resulta ng mga aplikante bilang ikaw, gamit ang mga pahintulot mo; karamihan sa mga app ay nagtatanong muna bago may baguhin. Sa prepza lang mabubura ang account mo o ang isang kumpanya. Ang nababasa ng app ay napupunta sa provider nito, ayon sa mga tuntunin ng app na iyon. Puwede mo itong i-disconnect anumang oras sa parehong tab. Puwede ring kumonekta ang ibang AI app at mga agent na ikaw mismo ang gumawa: nasa [tab na MCP](/api-docs?tab=mcp) ng dokumentasyon para sa mga developer ang mga hakbang at mga halimbawang agent, at puwedeng mag-sign in ang agent sa server gamit ang API key na may pahintulot para sa mga AI agent. Ipinapaliwanag ng [gabay sa AI agents, MCP at APIs](/guides/ai-agents-mcp-and-api) kung para saan ang bawat isa.",
    },
    {
        "key": "candidates",
        "question": "Ano ang nakikita ng mga aplikante?",
        "answer": "Ang pangalan at logo ng iyong kumpanya, sa mga kulay at mga font ng iyong kumpanya (itinakda sa tab nitong Brand), kung ano ang aasahan bago sila magsimula, pagkatapos ay isang timed na tanong sa bawat pagkakataon. Hindi nila kailanman nakikita ang kanilang score o kung tama ang isang sagot.",
    },
    {
        "key": "verified",
        "question": "Ano ang ibig sabihin ng verified check?",
        "answer": "Na nag-sign in ang isang may-ari o admin ng kumpanya gamit ang work email sa website ng kumpanya, gaya ng you@acme.com, at sinuri ng aming team ang kumpanya pagkatapos. Idagdag ang website gamit ang I-verify sa header ng iyong kumpanya; hindi binibilang ang mga libreng email service. Habang naghihintay ng review, may orasan sa tabi ng pangalan na nakikita ng iyong team, at ang pagpapalit ng pangalan ng kumpanya ay nagpapadala ulit nito para sa review. Lumalabas ang check sa tabi ng pangalan ng iyong kumpanya, pati sa mga invite.",
    },
    {
        "key": "languages",
        "question": "Aling mga wika ang suportado?",
        "answer": "{count} wika, para sa site, sa mga interview at sa mga email. Piliin ang wika ng interview, anuman ang wika ng job description.",
    },
    {
        "key": "privacy",
        "question": "Ano ang nangyayari sa mga job description at mga sagot?",
        "answer": "Ginagamit ang mga job description para buuin ang mga interview ng iyong kumpanya, at ang mga sagot ng aplikante para i-score ang mga ito para sa iyong kumpanya. Maaari ding muling gamitin ang mga tanong na ginagawa ng prepza sa mga interview at practice ng ibang mga kumpanya, nang walang anumang tumutukoy sa iyo, sa iyong kumpanya o sa sinumang iba; maaari mong hindi isama rito ang mga tanong ng isang interview sa mga setting nito. Natututo rin ang prepza ng mga pangkalahatan at anonymized na pattern ng kalidad ng tanong mula sa kung paano sinasagot ang mga tanong, para pahusayin kung paano ginagawa ang mga tanong. Ipinapaliwanag ng [privacy policy](/privacy) kung ano ang itinatago namin, gaano katagal, at ang mga karapatan ng lahat.",
    },
    {
        "key": "eu_ai_law",
        "question": "Legal ba ang paggamit ng AI sa pag-screen ng mga aplikante sa EU?",
        "answer": "Oo, basta may sinusunod na patakaran. Sa ilalim ng EU AI Act, malaki ang posibilidad na high-risk ang mga tool na nag-i-score ng mga aplikante, na may mga obligasyon simula 2 Disyembre 2027, at umiiral na ang GDPR: tao ang gumagawa ng desisyon sa pag-hire, sinasabihan ang mga aplikante na ginagamit ang AI, at may itinatagong mga record. Ganito gumagana ang prepza: AI ang sumusulat ng mga tanong, ang mga tao sa iyong kumpanya ang nagre-review ng mga resulta at nagdedesisyon, at sinasabihan ang mga aplikante bago sila magsimula. Hindi ito legal advice; ipinapaliwanag ng [Legal ba ang AI hiring sa EU?](/guides/is-ai-hiring-legal-in-the-eu) ang mga patakaran at petsa.",
    },
    {
        "key": "emails",
        "question": "Anong mga email ang ipinapadala ng prepza, at paano ko ito ihihinto?",
        "answer": 'Laging ipinapadala ang mga email ng serbisyo, gaya ng mga imbitasyon, report, problema sa bayad at pagbabago sa aming mga tuntunin. Ang iba, gaya ng araw-araw na buod ng aktibidad, mga paalala at mga update tungkol sa produkto, ay pinipili mo sa Mga setting, sa ilalim ng Mga email, o inihihinto gamit ang link na "Mag-unsubscribe" sa bawat email. Puwedeng ihinto ng mga aplikante ang mga email ng iyong kumpanya, o ang mga paalala ng isang interview, gamit ang mga link sa kanilang mga imbitasyon at paalala.',
    },
    {
        "key": "delete",
        "question": "Puwede ko bang burahin ang account ko?",
        "answer": "Oo, sa Settings. Buburahin ang account at data mo, at puwede mo munang i-download ang kopya ng data mo. Lumalabas ang mga balita ng prepza sa iyong mga notification, ang kampana sa itaas; ipinapadala rin sa email ang mahahalagang balita bilang update tungkol sa produkto, habang naka-on lang ang setting na iyon.",
    },
    {
        "key": "report",
        "question": "Paano ako mag-uulat ng problema?",
        "answer": "Sumulat sa amin sa [page na Makipag-ugnayan](/contact) at i-paste ang ID ng tinutukoy mo: nasa ilalim ng pangalan ng kumpanya, interview o aplikante ang “kopyahin ang id”, at nasa menu ng account mo at sa Mga setting ang ID ng iyong account. Sa ID, agad namin itong mahahanap.",
    },
]
