---
title: "Paano ikonekta ang skills tests sa iyong ATS"
seoTitle: "Paano Ikonekta ang Skills Tests sa ATS: Praktikal na Gabay"
description: "Awtomatikong magpadala ng skills tests at tumanggap ng resulta sa iyong ATS, hayaang tao ang magpasya, at alamin kung ano ang unang dapat i-check."
updated: "2026-10-21"
---

# Paano ikonekta ang skills tests sa iyong ATS

Karamihan sa mga hiring team ay nagtatago ng mga aplikante sa isang applicant tracking system (ATS) at nagpapatakbo ng skills tests sa ibang tool. Kung walang koneksyon ang dalawa, may kumokopya ng mga email mula sa ATS, nagpapadala ng mga imbitasyon nang mano-mano, naghihintay, at saka kinokopya pabalik ang mga score. Gumagana ito sa limang aplikante. Sa limampu, huli nang naipapadala ang mga imbitasyon, nakatambak ang mga resulta sa pangalawang tab na walang nagbubukas, at tumatanggap ng ibang alok ang magagaling na aplikante habang naghihintay.

Ipinapaliwanag ng gabay na ito kung ano ang ginagawa ng isang mahusay na koneksyon sa pagitan ng ATS at testing tool, kung ano ang dapat i-check bago ka umasa rito, at kung paano ito i-set up para ang automation ang humawak sa paulit-ulit na trabaho habang tao pa rin ang gumagawa ng bawat hiring decision.

## Bakit kailangang ikonekta

| Kung walang koneksyon | Kung may koneksyon |
| --- | --- |
| May nag-e-export o kumokopya ng email ng mga aplikante | Kapag inilipat ang aplikante sa isang stage, naipapadala ang imbitasyon |
| Naipapadala ang imbitasyon kapag may oras ang isang tao | Naipapadala ang imbitasyon ilang minuto lang matapos ilipat |
| Nananatili ang mga resulta sa testing tool | Lumalabas ang mga resulta sa aplikante sa ATS |
| Nagtatanong ang mga hiring manager, "May nag-test na ba sa kanya?" | Ipinapakita ng ATS kung sino ang na-test at kumusta ang resulta |
| Mga typo sa email at mga aplikanteng nakaligtaan | Ang ATS ang iisang listahan ng lahat ng nag-apply |

Mas mahalaga ang bilis kaysa sa inaakala. Habang tumatagal ang pagitan ng pag-apply at pagtanggap ng sagot, mas maraming aplikante ang umaatras o tumatanggap ng ibang trabaho. Malaki ang pagkakaiba-iba ng eksaktong drop-off rate depende sa role at market, kaya mag-ingat sa mga nailathalang numero, pero pare-pareho ang direksyon: nawawalan ng tao ang mabagal na proseso, at kadalasang may pinakamaraming opsyon ang pinakamagagaling na aplikante.

## Ano ang hitsura ng mahusay na flow

Sinusundan ng isang maayos na integration ang mga stage na ginagamit mo na. Hindi ito gumagawa ng bagong proseso.

1. **Nag-a-apply ang isang aplikante** at pumapasok sa iyong ATS gaya ng dati.
2. **Inililipat siya ng isang tao sa isang testing stage,** halimbawa "Skills test". Ang paglipat na iyon ang trigger, kaya tao pa rin ang nagpapasya kung sino ang ite-test.
3. **Awtomatikong nagpapadala ng imbitasyon ang testing tool,** para sa test na naka-link sa job na iyon.
4. **Kinukuha ng aplikante ang test** sa oras na gusto niya, sa loob ng deadline na itinakda mo.
5. **Isinusulat pabalik sa aplikante sa ATS ang mga resulta:** ang score, kung pumasa siya, anumang integrity flag, at link sa lahat ng sagot.
6. **Nire-review ng isang tao ang resulta** at isinusulong ang aplikante, o hindi.

Dalawang bagay ang sadyang nananatiling mano-mano: ang pagpili kung sino ang ite-test at ang pagpapasya kung ano ang susunod. Ang tinatanggal lang ng koneksyon ay ang pagkopya sa pagitan.

### Bakit hindi mag-trigger sa bawat bagong application?

May mga tool na nag-iimbita sa lahat ng nag-a-apply. Puwede iyon sa mga high-volume na role kung saan iisang test ang kinukuha ng lahat. Pero mas madaling kontrolin ang isang stage na pinaglilipatan mo ng mga aplikante: puwede mong laktawan ang mga malinaw na hindi pumapasa sa mahigpit na requirement (walang work permit, maling lokasyon), at hindi ka kailanman magte-test, o magbabayad, para sa taong ire-reject mo rin naman.

## Ano ang dapat i-check bago pumili ng integration

Hindi pare-pareho ang ibig sabihin ng bawat "integrated sa iyong ATS". Itanong ang mga ito bago ka magkonekta ng kahit ano.

| Tanong | Bakit ito mahalaga | Magandang sagot |
| --- | --- | --- |
| Paano kumokonekta? | Mahirap i-audit o bawiin ang mga shared password at account na hawak ng vendor | Isang API key o token na ginagawa ng kumpanya mo at puwede mong burahin anumang oras |
| Ano ang kayang gawin ng key? | Panganib ang key na may full access kapag nag-leak | Ang pinakamakitid na permission na kailangan ng integration, nakalista sa docs |
| Ano ang nagti-trigger ng imbitasyon? | Kailangan mong malaman kung kailan eksaktong makakatanggap ng email ang mga aplikante | Isang partikular na stage na pinipili mo, bawat job |
| Saan napupunta ang mga resulta? | Walang silbi ang mga resultang walang nakakakita | Sa profile ng aplikante, bilang note o comment na binabasa na ng team mo |
| Ano ang mangyayari kapag pumalya ang imbitasyon? | Ubos na credits, typo, naka-pause na account: tahimik na naiipit ang mga aplikante | May naaabisuhan, at puwedeng imbitahan ulit ang aplikante |
| Puwede bang maproseso nang dalawang beses ang isang event? | Nagpapadala ulit ng event ang mga ATS; hindi dapat makatanggap ng dalawang imbitasyon ang isang aplikante | Isang beses lang iniimbitahan ang bawat aplikante kada test, ilang beses man dumating ang event |
| Paano bine-verify ang mga papasok na event? | Puwedeng padalhan ng pekeng event ang isang address na hindi bine-verify | Mga signed request na sinusuri ng tool |
| Gaano katagal itinatago ang data ng mga aplikante? | Inaasahan ng mga privacy law gaya ng GDPR ang malinaw na retention period | Isang nakasaad na limitasyon, at pagbura kapag binura mo ang job, ang test, o ang account mo |
| Magkano ito? | Puwedeng gawing mahal ng per-seat na plano ang automation | Gastos na kaya mong tantiyahin bawat aplikanteng na-test |

Kung hindi malinaw na masagot ng vendor ang mga tanong tungkol sa pagpalya at mga duplicate, asahan mong malalaman mo ito sa mahirap na paraan.

### Proteksyon ng data

Ang pagkonekta ng dalawang system ay nangangahulugang lumilipat ang data ng mga aplikante, kahit pangalan at email man lang, sa pagitan ng dalawang kumpanya. Sa ilalim ng GDPR at mga katulad na batas, kadalasang data processor mo ang testing vendor, kaya kailangan mo ng data processing agreement at dapat mong sabihin sa mga aplikante, sa iyong privacy notice o sa imbitasyon, na bahagi ng proseso ang skills test. Ipasa lang ang data na talagang kailangan ng test. Para sa legal na bahagi ng tests at AI sa hiring, tingnan ang [Legal ba ang AI hiring sa EU?](/guides/is-ai-hiring-legal-in-the-eu)

## Checklist sa pag-set up

Bago mo ito i-on para sa isang totoong role:

1. **Gumawa ng stage na para lang sa testing** sa iyong ATS, gaya ng "Skills test". Huwag gumamit ulit ng stage na may ibang ibig sabihin, kundi maiimbitahan ang mga aplikante nang hindi sinasadya.
2. **Gawin ang key mula sa isang admin account** na nakakakita sa bawat job na gusto mong i-link, na may mga permission lang na nakalista sa docs.
3. **I-link ang bawat job sa test nito** at piliin ang stage na magti-trigger ng imbitasyon.
4. **I-set up ang webhook** kung kailangan itong gawin nang mano-mano sa iyong ATS, at i-paste ang secret nito kung saan ito hinihingi ng tool.
5. **Subukan sa sarili mo.** Magdagdag ng aplikante gamit ang sarili mong email, ilipat siya sa stage, kunin ang test, at i-check kung lumalabas ang note sa ATS.
6. **Tukuyin kung sino ang magbabantay sa mga pagpalya:** sino ang aabisuhan kapag hindi maipadala ang imbitasyon, at sino ang aayos nito.
7. **Pagkasunduan kung paano babasahin ang mga resulta.** Gabay ang passing mark, hindi awtomatikong rejection. Pagpasyahan iyon bago dumating ang mga resulta, hindi pagkatapos.

## Mga karaniwang pagkakamali

- **Ina-automate ang desisyon, hindi ang paperwork.** Kapag awtomatikong nire-reject ang lahat ng nasa ilalim ng isang score, nawawala ang pagsusuri ng tao na nakakahuli ng maling tanong o ng aplikanteng nagkaproblema sa koneksyon. Hayaang ang score ang mag-ayos; hayaang tao ang magpasya.
- **Nagti-trigger mula sa maling stage.** Ang stage na ginagamit ng mga recruiter sa ibang dahilan ay nagpapadala ng tests sa mga taong hindi dapat makatanggap nito.
- **Iisang test para sa lahat ng job.** Pinapadali ng koneksyon na ipadala ang parehong test kahit saan. Pinakamalaki ang naitutulong ng test kapag ginawa ito para sa partikular na trabaho. Tingnan ang [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening).
- **Walang nagbabantay sa mga pagpalya.** Kapag tahimik na pumalya ang imbitasyon, naghihintay ang aplikante ng email na hindi darating, at akala mo ay hindi niya ito pinansin.
- **Key na nakatali sa taong aalis.** May mga ATS key na kumikilos bilang ang taong gumawa nito. Kapag isinara ang account ng taong iyon, titigil ang koneksyon. Gumamit ng account na mananatili, at ikonekta ulit kapag nagpalit ng role ang mga tao.
- **Nakakalimutan ang mga aplikanteng wala sa ATS.** Kailangan pa rin ng imbitasyon ang mga referral at direktang aplikante na hindi kailanman pumasok sa ATS. Magtabi rin ng mano-manong paraan para imbitahan sila.

## Paano ito ginagawa ng prepza

Kumokonekta ang prepza sa **Workable, Greenhouse, Teamtailor, Recruitee at Breezy HR**, at sinusundan nito ang flow sa itaas.

- **Ang key mo, ang kontrol mo.** Ikinokonekta ng isang may-ari o admin ang ATS sa tab na Mga integration ng kumpanya gamit ang key na ginawa ng kumpanya mo sa ATS. Sinusuri ito ng prepza bago i-save, itinatago itong naka-encrypt, at hindi na ito ipinapakita ulit. Kapag nag-disconnect, sabay na nabubura ang key at ang mga naka-link na job.
- **I-link ang isang job sa isang interview.** Pumili ng job sa ATS at ng stage na magti-trigger ng imbitasyon, at i-link ito sa isang umiiral na interview sa prepza o gumawa ng bago mula sa text ng job sa ATS. Nire-review mo ang mga topic bago maisulat ang kahit isang tanong.
- **Ilipat ang aplikante, maipapadala ang imbitasyon.** Isang beses lang iniimbitahan ang bawat aplikante kada interview, kahit dalawang beses ipadala ng ATS ang parehong event.
- **Bumabalik sa ATS ang mga resulta.** Kapag tapos na ang isang aplikante, nagdadagdag ang prepza ng note o comment sa kanya sa ATS na may grade niya, kung pumasa siya, anumang integrity flag (pag-alis sa page, pagtatangkang kumopya, mga sagot na napili nang masyadong mabilis para nabasa ang tanong), at link sa kanyang scorecard na may bawat sagot.
- **Hindi nakakalusot ang mga pagpalya.** Kapag hindi maimbitahan ang isang aplikante, halimbawa dahil ubos na ang credits ng kumpanya, naabot na ang email limit, o pansamantalang ipina-pause ng prepza ang mga imbitasyon, makakatanggap ang lahat ng miyembro ng kumpanya ng notification na nagsasabi kung aling ATS. Awtomatikong iniimbitahan pagkatapos ng top-up ang mga aplikanteng hindi naimbitahan dahil kulang ang credits, at puwedeng imbitahan ulit sa isang click ang mga naghihintay na aplikante ng kahit anong job.
- **Slack, kung ginagamit mo ito.** Puwedeng mag-post ang prepza ng mga notification, gaya ng aplikanteng tapos na o ng aplikante mula sa ATS na hindi naimbitahan, sa Slack channel na pipiliin mo.
- **Ang sarili mong platform.** Kung wala sa listahan ang ATS mo, hinahayaan ka ng [API](/api-docs) ng prepza na mag-imbita ng mga aplikante gamit ang API key at makatanggap ng signed webhook kapag nagsimula, natapos, hindi naabot ng imbitasyon, nag-expire ang imbitasyon, o tinanggal ang isang aplikante, at kapag handa na ang isang interview.
- **Itinatago ang data sa takdang panahon.** Binubura ang mga aplikanteng na-save mula sa ATS pagkalipas ng 365 araw, o mas maaga kasabay ng kanilang interview o kumpanya.

May mga ATS na nangangailangan ng hakbang sa kanilang panig. Hinihiling ng Greenhouse, Teamtailor at Recruitee na magdagdag ka ng webhook nang mano-mano; ipinapakita ng dialog na Mga tagubilin ng prepza ang address at kung saan ipe-paste ang secret nito. Ang prepza mismo ang nagse-set up ng webhooks ng Workable at Breezy HR.

Per aplikante ang presyo, walang subscription: nagbabayad ka lang para sa mga aplikanteng sumagot ng kahit isang tanong, $5 bawat isa sa $50 na top-up, $4 simula sa $200 na top-up, $3 simula sa $600 na top-up at $2 simula sa $1,000 na top-up. Nasa US dollars ang mga presyo, nasa euro sa Europe (parehong mga numero) at nasa pound sa UK (£4 hanggang £1.50); hinahawakan sa checkout ang VAT o sales tax. Libre ang pagkonekta ng ATS at paggawa ng interviews, at libre ang unang 3 aplikante ng iyong unang kumpanya. Tingnan ang [pricing](/pricing).

## Kaugnay na babasahin

- [Paano mag-screen ng 100 aplikante sa isang araw](/guides/screen-100-applicants-in-a-day)
- [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening)
- [Pre-employment testing: isang praktikal na gabay](/pre-employment-testing)
