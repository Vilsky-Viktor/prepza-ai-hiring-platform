---
title: "AI agents, MCP at APIs: ano ang mga ito at paano gamitin sa hiring"
seoTitle: "AI Agents, MCP at APIs sa Hiring: Paano Gamitin"
description: "Ano ang AI agent, MCP at API, paano gamitin nang ligtas sa hiring, at paano patakbuhin ang prepza mula sa AI assistant nito, Claude, ChatGPT o platform mo."
updated: "2026-10-22"
---

# AI agents, MCP at APIs: ano ang mga ito at paano gamitin sa hiring

Para sa karamihan, unang nakilala ang AI bilang isang chat window: magtatanong ka, sasagot ito. Isang hakbang pa ang lampas ng AI agent. Kaya nitong maghanap ng impormasyon sa mga tool mo at, kapag hiniling mo, gumawa ng mga bagay doon: gumawa ng interview, mag-imbita ng listahan ng mga aplikante, sabihin sa iyo kung sino ang may pinakamataas na score noong nakaraang linggo. Ang Model Context Protocol (MCP) ang standard na nagpapahintulot sa AI chat na ginagamit mo na, gaya ng Claude o ChatGPT, na kumonekta sa mga ganitong tool. At ang API naman ang mas luma at mas eksaktong paraan ng pag-uusap ng software sa software, nang walang AI sa gitna.

Ipinapaliwanag ng gabay na ito ang tatlo sa simpleng salita: kung saan sila magagamit sa hiring, ano ang dapat bantayan, at paano sila gamitin kasama ang prepza.

## Ano ang AI agent

Text lang ang isinusulat ng chatbot. Ang agent ay isang language model na may **tools**: maliliit at malinaw na aksyon na puwede nitong tawagin, gaya ng "ilista ang mga aplikante ng interview na ito" o "imbitahan ang email na ito". Kapag may itinanong ka, ang agent ang nagpapasya kung aling tools ang gagamitin, binabasa ang ibinabalik ng mga ito, at doon ibinabatay ang sagot, hindi sa memorya.

| Chatbot | AI agent |
| --- | --- |
| Sumasagot mula sa natutunan nito sa training | Sumasagot mula sa live mong data, na binabasa gamit ang tools |
| Kaya lang ilarawan kung paano gawin ang isang bagay | Kaya itong gawin, kapag hiniling at pinayagan mo |
| Nanghuhula kapag hindi alam | Hinahanap ito, o sinasabing hindi nito kaya |
| Nasa iisang window lang | Gumagana sa loob ng mga tool na ikinonekta mo rito |

Ang tools ang nagpapakinabang sa isang agent, at sila rin ang nagpapasya kung ligtas ito o hindi. Ang mahusay na agent ay makakagamit lang ng tools na ibinigay sa kanya, sa loob lang ng mga permission mo, at ginagawa lang ang hiniling mo.

## Ano ang MCP

Ang Model Context Protocol ay isang open standard na ipinakilala ng Anthropic noong huling bahagi ng 2024 at sinusuportahan na ngayon ng Claude, ChatGPT at marami pang ibang AI app at developer tool. Madalas itong ihambing sa USB-C port para sa AI: sa halip na gumawa ang bawat AI app ng sarili nitong koneksyon sa bawat tool, nag-aalok ang isang tool ng iisang **MCP server**, at magagamit ito ng kahit anong AI app na marunong ng MCP.

Tatlong bagay ang sinasabi ng MCP server sa AI app:

1. **Kung anong tools ang mayroon**, kasama ang pangalan, paglalarawan at mga detalyeng kailangan ng bawat isa.
2. **Kung aling tools ang nagbabasa lang** at alin ang may binabago, para matanong ka muna ng AI app bago ang isang pagbabago.
3. **Kung sino ka**, sa pamamagitan ng sign-in na isang beses mo lang aaprubahan, para tumakbo ang bawat tawag bilang ikaw, gamit ang mga permission mo.

Para sa iyo, ibig sabihin nito ay puwede kang magtrabaho sa isang tool mula sa chat na ginagamit mo na, nang hindi kinokopya ang data mula sa isang window papunta sa iba.

## Ano ang API, at paano ito naiiba

Ang API (application programming interface) ay isang hanay ng mga nakapirming request na puwedeng ipadala ng isang program sa iba: "ilista ang mga aplikante ng interview na ito", "imbitahan ang email na ito". Ang mga developer mo ang sumusulat ng code na nagpapadala ng mga ito. Walang AI na kasangkot: laging pareho ang ginagawa ng parehong request, at iyon mismo ang kailangan mo para sa automation na tumatakbo nang mag-isa.

| | Si Mira, ang AI assistant (sa app) | MCP (sa Claude o ChatGPT) | API |
| --- | --- | --- | --- |
| Sino ang gumagamit | Ikaw, sa prepza | Ikaw, sa AI chat mo | Ang code ng platform mo |
| Paano ka nagtatanong | Sa sarili mong salita | Sa sarili mong salita | Mga nakapirming request na isinulat ng developer |
| Sino ang nag-aapruba ng mga pagbabago | Ikaw, sa isang card | Ikaw, sa AI app mo | Ang code mo, ayon sa pagkakasulat |
| Pinakabagay para sa | Mabilisang tanong at gawain | Pagsasama ng prepza sa iba mo pang tools at file | Automation na tumatakbo nang walang nagbabantay |
| Nagsa-sign in bilang | Ikaw | Ikaw | Isang key ng kumpanya |

Gamitin si Mira o ang MCP kapag may taong kasali sa proseso. Gamitin ang API kapag ang sarili mong system ang dapat mag-imbita ng mga aplikante at mangolekta ng mga resulta nang mag-isa, halimbawa mula sa isang careers site o internal na HR tool.

## Saan ito magagamit sa hiring

Maraming maliliit at paulit-ulit na hakbang ang hiring na nakakalat sa iba't ibang tool. Doon mismo magaling ang isang agent:

- **Mga tanong tungkol sa pipeline mo.** "Aling mga aplikante para sa Senior Backend ang pumasa ngayong linggo?", "Sino ang hindi pa nagsisimula ng interview nila?", "Ano ang average na grade natin para sa data analyst na role?"
- **Pag-set up ng mga bagay.** "Gumawa ng interview mula sa job description na ito", "Gawing 70% ang passing mark", "Bigyan ang aplikanteng ito ng 50% na dagdag na oras."
- **Maramihang gawain.** "Imbitahan ang 12 taong ito sa frontend interview", na direktang kinopya mula sa isang email o spreadsheet.
- **Pagsasama ng mga source.** Sa Claude o ChatGPT, puwede mong pagsamahin ang prepza at ang iba mo pang nakakonektang tools at file: ihambing ang job description sa mga dokumento mo sa mga topic ng interview, o gumawa ng draft na mensahe para sa mga aplikanteng nasa shortlist.

Ang hindi nito dapat gawin ay ang magpasya kung sino ang iha-hire. Sinusuportahan ng grade ang paghuhusga ng isang tao; hindi nito ito pinapalitan. Ipagawa sa agent ang pag-sort, pagbubuod at paghahanda, at iwan sa isang tao ang desisyon. Tingnan ang [Legal ba ang AI hiring sa EU?](/guides/is-ai-hiring-legal-in-the-eu) para malaman kung bakit mahalaga rin iyon sa legal na aspeto.

## Ano ang dapat bantayan

Ang pagkonekta ng AI sa hiring data mo ay nangangailangan ng parehong ingat gaya ng pagbibigay ng access sa isang katrabaho.

| Panganib | Ano ang nakakatulong |
| --- | --- |
| May ginawa ang agent na hindi mo sinadya | Kailangan muna ng approval mo ang mga pagbabago, at ang hiniling mo lang ang ginagawa nito |
| Mas marami itong nakikita kaysa sa nararapat | Kumikilos ito bilang ikaw: nakikita nito ang nakikita mo, wala nang iba |
| Mga instruction na nakatago sa data | Data ang mga pangalan, sagot at dokumento ng mga aplikante, hindi kailanman instruction na susundin |
| Napupunta sa chat ang mga sikreto | Hindi kailanman dumadaan sa chat ang mga API key at password |
| Mga pagkakamaling hindi na maibabalik | Nananatili sa app ang pagbura ng account o kumpanya, na may sariling kumpirmasyon |
| Lumalabas ang data sa mga tool mo | Umaabot ang data sa AI app na ikinonekta mo, sa ilalim ng mga tuntunin ng app na iyon: ikonekta lang ang mga app na pinapayagan ng kumpanya mo |
| Sobra-sobrang paggamit | May limitasyon kung ilang aksyon ang puwedeng tumakbo kada oras |

Bago ikonekta ang kahit anong AI app sa data ng trabaho, i-check ang patakaran ng kumpanya mo tungkol sa AI tools, at sabihin sa mga aplikante sa privacy notice mo kung aling mga serbisyo ang nagpoproseso ng data nila.

## Tatlong paraan ng paggamit ng prepza lampas sa mga page nito

### 1. Si Mira, ang built-in na AI assistant

Piliin ang **magtanong kay Mira** sa header ng kahit anong page. Alam ni Mira, ang AI assistant ng prepza, ang mga kumpanya, interview, aplikante, credits at integration mo, at kung paano gumagana ang prepza. Sumasagot ito sa wika mo, at puwede kang mag-type o magsalita.

- **Sumasagot ito mula sa data mo**, na may parehong access na mayroon ka: nakikita ng admin ang nakikita ng admin, ng viewer ang nakikita ng viewer.
- **Alam nito ang page na kinaroroonan mo.** Itanong ang "Ano ang magagawa ko sa page na ito?" para sa gabay ng page na iyon, o "Sino ang pinakamahusay dito?" sa mga aplikante ng isang interview, at sasagot ito tungkol sa interview na iyon nang hindi nagtatanong kung alin.
- **Inihahanda nito ang mga pagbabago, ikaw ang nagkukumpirma.** Kapag hiniling na mag-imbita ng mga aplikante, nagpapakita ito ng card na may eksaktong mangyayari, gaya ng "Imbitahan ang 12 aplikante sa Backend developer". Walang tatakbo hangga't hindi mo pinipili ang kumpirmahin.
- **Ipinapakita nito ang mga source nito.** Sa ilalim ng sagot, makikita mo ang mga aplikante o interview na ginamit nito at link sa page na pinanggalingan ng mga ito.
- **Nananatili ito sa paksa.** Sumasagot ito tungkol sa prepza at sa pagha-hire gamit ito, at tumatanggi sa iba pa.

### 2. prepza sa Claude o ChatGPT, gamit ang MCP

Kung nagtatrabaho ka na sa Claude o ChatGPT, puwede mong dalhin doon ang prepza. Pareho ang tools na iniaalok ng MCP server ng prepza at ni Mira, ang built-in na assistant.

**Para kumonekta:**

1. Sa prepza, buksan ang tab na **Mga integration** ng isang kumpanya at piliin ang **Mga AI app**. Kopyahin ang address ng server: `https://prepza.ai/mcp`.
2. **Sa Claude:** buksan ang Settings, pagkatapos ang Connectors, at magdagdag ng custom connector gamit ang address na iyon. **Sa Claude Code:** patakbuhin ang `claude mcp add --transport http prepza https://prepza.ai/mcp`. **Sa ChatGPT:** idagdag ito bilang custom connector sa settings nito para sa apps at connectors.
3. Bubuksan ng AI app mo ang sign-in ng prepza. Mag-sign in, i-check kung aling app ang humihingi ng access, at piliin ang **Payagan**. Para makapagbasa lang ito, i-off muna ang **Payagan ang mga pagbabago**.

Mula noon, magtanong sa chat mo gaya ng pagtatanong mo sa isang katrabaho: "Sa prepza, sino ang top three na aplikante para sa Product designer?" Karamihan sa mga AI app ay nagtatanong muna sa iyo bago ang isang pagbabago, at nagbababala bago ang anumang hindi na maibabalik: sinasabi sa kanila ng prepza kung aling mga aksyon ang nagbabago o nagbubura ng isang bagay.

**Ano ang nananatiling pareho gaya ng sa app:**

- **Ang mga permission mo.** Kumikilos ito bilang ikaw, sa bawat kumpanyang kinabibilangan mo, gamit ang role mo sa bawat isa.
- **Credits at mga limitasyon.** Pareho ang gastos ng pag-imbita ng aplikante gaya ng sa app, at pareho ang mga email limit na nalalapat.
- **Ang tala.** Lahat ng ginagawa ng isang AI app para sa iyo ay lumalabas sa log ng aksyon ng kumpanya bilang ginawa sa pamamagitan ng AI app, mula sa pag-apruba ng mga topic at pagtingin ng resulta hanggang sa pagbibigay ng dagdag na oras o pagbawi sa isang aplikante. Binabasa ito ng may-ari ng kumpanya sa tab na **Log ng aksyon** ng kumpanya.
- **Ang kumpanya ang magpapasya.** Mapipigilan ng mga may-ari at admin ang mga AI app sa paggamit ng data ng kumpanya gamit ang **Payagan ang mga AI app sa kumpanyang ito** sa page ng mga AI app nito.
- **Ang hindi nito kayang gawin.** Hindi nito nakikita ang password o mga API key mo, at hindi nito kayang burahin ang account mo o ang isang kumpanya. Nananatili ang mga iyon sa app.

**Para mag-disconnect,** alisin ang connector sa AI app mo, o piliin ang **I-disconnect** sa tabi nito sa ilalim ng **Mga AI app** sa tab na Mga integration. Agad itong titigil sa paggana.

**Ibang app at sarili mong mga agent.** Nasa [tab na MCP](/api-docs?tab=mcp) ng dokumentasyon para sa mga developer ang mga hakbang para sa Gemini CLI, Cursor, VS Code at Le Chat, at kumpletong mga halimbawang agent sa Python at TypeScript. Ang agent na tumatakbo sa server, na walang taong mag-a-approve ng sign-in, ay gumagamit ng API key ng kumpanya na may pahintulot na **Gamitin sa mga AI agent (MCP)**: gumagana lang ito sa kumpanyang iyon, at sa mga tool lang na pinapayagan ng iba pang pahintulot ng key.

### 3. Ang sarili mong platform, gamit ang API

Para sa automation na walang AI, may API ang prepza, na inilalarawan sa [dokumentasyon nito para sa mga developer](/api-docs).

1. Bubuksan ng isang may-ari o admin ang tab na **Mga integration** ng isang kumpanya, pagkatapos ang **API**, at pipiliin ang **Bagong key**. Pangalanan ito ayon sa platform na gagamit nito, piliin kung kailan ito mag-e-expire, at i-check lang ang kailangan nito: nagbabasa lang ang key ng isang dashboard, at nag-iimbita rin ang key ng isang careers site. Puwede kang magdagdag o mag-alis ng mga pahintulot sa ibang pagkakataon. Isang beses lang ipinapakita ang key; itago ito sa ligtas na lugar.
2. Nagpapadala ang platform mo ng mga request gamit ang key na iyon: ilista ang mga interview ng kumpanya, ilista o basahin ang mga aplikante kasama ang grade nila, kung pumasa sila at ang mga integrity flag nila, at mag-imbita ng aplikante.
3. Magdagdag ng **webhook**: isang address sa platform mo na tinatawagan ng prepza, na may signature, kapag nagsimula, natapos, hindi naabot ng imbitasyon, nag-expire ang imbitasyon, o tinanggal ang isang aplikante, at kapag handa na ang isang interview, para hindi mo na kailangang paulit-ulit na magtanong. Sa API page, puwede mo itong padalhan ng test event at makikita mo ang delivery log nito.

May kasamang link ang bawat aplikante sa buong resulta niya sa prepza at, hanggang sa matapos siya, sa sarili niyang invite link, para maipadala ito ng platform mo sa sarili nitong mensahe kung gusto mo. Kapag alam na ng platform mo kung sino ang aplikante, imbitahin siya nang walang sign-in: walang email na ipinapadala ang prepza, at sasagutan ng aplikante ang interview mula sa link nang hindi nagsa-sign in sa prepza, kaya sa kanya lang ipadala ang link. Puwede ring ibalik ng imbitasyon ang aplikante sa site mo (kahit anong https address) gamit ang isang button sa pahina ng pagtatapos, at magtakda ng light o dark na theme sa mga kulay ng kumpanya mo. Gamit ang SDK ng prepza, maipapakita mismo ng sarili mong pahina ang interview, pero sa mga site lang na pinapayagan ng kumpanya mo sa API page nito. Hindi nakadepende sa mga site na iyon ang API at ang mga webhook: sa halip, puwedeng limitahan ang bawat key sa mga IP address ng mga server mo. Verified badge lang ang idinadagdag ng verification.

Pareho ang patakaran gaya ng saanman: sinusuportahan ng grade ang desisyon ng isang tao, kaya huwag awtomatikong i-reject ang mga aplikante batay rito.

## Alin ang gagamitin at kailan

Magsimula sa kung sino ang gagawa ng trabaho at gaano kadalas.

| Ang sitwasyon mo | Gamitin |
| --- | --- |
| Nasa prepza ka at gusto mo ng mabilis na sagot: sino ang pumasa, sino ang hindi pa nagsisimula, ilan pa ang natitirang credits | Si Mira, ang built-in na assistant |
| Gusto mong mag-set up ng isang bagay sa ilang salita: interview mula sa job description, passing mark, dagdag na oras | Si Mira, ang built-in na assistant |
| Buong araw ka nang nagtatrabaho sa Claude o ChatGPT at gusto mong nandoon din ang prepza | MCP |
| Kailangan ng gawain ang prepza at iba pa: mga dokumento mo, mga draft ng email, isa pang nakakonektang tool | MCP |
| Isang recruiter na nasa labas ang gustong i-check ang pipeline mula sa AI app sa phone niya | MCP |
| Ang careers site o HR system mo ang dapat mag-imbita ng mga aplikante nang mag-isa, nang walang nagki-click | Ang API |
| Dapat mapunta ang mga resulta sa sarili mong database o dashboard sa sandaling matapos ang mga aplikante | Ang API, kasama ang webhook |
| Isa ang ATS mo sa mga kinokonektahan ng prepza (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Wala sa mga ito: ikonekta ang ATS sa tab na Mga integration. Tingnan ang [Paano ikonekta ang skills tests sa iyong ATS](/guides/ats-integration-skills-tests) |

Isang simpleng panuntunan:

- **Isang tao ang nagtatanong, at sinusuri niya ang bawat pagbabago:** si Mira sa prepza, o MCP kung nasa Claude o ChatGPT ang taong iyon buong araw.
- **Software ang kumikilos nang mag-isa, sa parehong paraan tuwing pagkakataon:** ang API.
- **Kung nagsisimula pa lang:** subukan muna si Mira, ang built-in na assistant. Hindi ito kailangang i-set up, at magagamit mo rin sa MCP ang matututunan mo.

Puwede rin silang magtulungan. Puwedeng magpadala ang isang team ng mga imbitasyon mula sa HR system nito gamit ang API, habang nagtatanong ang mga recruiter kay Mira o sa AI chat nila tungkol sa mga resulta.

## Paano makakuha ng magagandang resulta

- **Pangalanan ang mga bagay.** Mas gumagana ang "ang Senior Backend na interview" kaysa sa "yung interview na iyon".
- **Isang hakbang lang muna ang hilingin** kapag mahalaga ito. I-check ang resulta, saka hilingin ang susunod.
- **Basahin ang approval bago mo ito payagan.** Ipinapakita nito kung ano mismo ang tatakbo.
- **Itanong kung saan galing ang isang numero.** Kayang ituro ng mahusay na agent ang mga aplikante o page na pinagbatayan nito.
- **Iwan sa tao ang mga desisyon.** Gamitin ang agent para maghanap, mag-sort at maghanda; ikaw ang magpasya.

## Presyo

Libreng gamitin si Mira, ang koneksyon sa MCP at ang API. Nagbabayad ka lang para sa mga aplikante, gaya ng dati: bawat aplikanteng sumagot ng kahit isang tanong, walang subscription. Tingnan ang [pricing](/pricing).

## Kaugnay na babasahin

- [Paano ikonekta ang skills tests sa iyong ATS](/guides/ats-integration-skills-tests)
- [Pag-interview ng mga engineer sa panahon ng AI: ano ang dapat i-test ngayon](/guides/interviewing-in-the-age-of-ai)
- [Legal ba ang AI hiring sa EU?](/guides/is-ai-hiring-legal-in-the-eu)
