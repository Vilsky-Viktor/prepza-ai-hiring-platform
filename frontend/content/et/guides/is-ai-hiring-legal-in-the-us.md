---
title: "Kas AI kasutamine värbamisel on USAs seaduslik? Mida tööandjad peavad teadma"
seoTitle: "AI värbamisel USAs: föderaal- ja osariikide reeglid"
description: "AI kasutamine värbamisel on USAs seaduslik, kuid reeglitega: ebasoodne mõju ja kohandused, kallutatuse auditid NYC-s, Illinois, Colorado ja California."
updated: "2026-10-30"
---

# Kas AI kasutamine värbamisel on USAs seaduslik? Mida tööandjad peavad teadma

Üldiselt jah: AI kasutamine värbamisel on USAs seaduslik. Föderaalset AI seadust värbamise kohta ei ole. Selle asemel kohaldub AI-tööriistadele, nagu igale testile, föderaalne diskrimineerimisvastane õigus, ning mõned kohad lisavad omad reeglid: New York City, Illinois, Colorado ja California.

See juhend selgitab üldjoontes reegleid, olulisi kuupäevi, seda, mida tööandjad peavad tegema, ja kuidas prepza sellele läheneb. **See ei ole õigusnõuanne.** See kajastab reegleid 2026. aasta oktoobri seisuga; mitu neist on uued või alles valmimas.

## Lühike vastus

| Küsimus | Lühike vastus |
| --- | --- |
| Kas võin kasutada AI-d kandidaatide sõelumiseks või hindamiseks? | Jah, föderaalse diskrimineerimisvastase õiguse ning osariikide ja linnade reeglite piires |
| Kas pean tulemusi kallutatuse suhtes kontrollima? | Ebasoodne mõju on sinu vastutus; New York Citys on enne kasutamist nõutud sõltumatu kallutatuse audit |
| Kas pean kandidaate teavitama? | New York Citys ja Illinoisis jah; Colorados ja Californias alates 1. jaanuarist 2027 |
| Kas pean pakkuma lisaaega? | Puudega kandidaatidele, kes seda vajavad: see on mõistlik kohandus (reasonable accommodation) |
| Kui kaua pean dokumente säilitama? | Californias neli aastat, Colorados kolm |
| Kes teeb värbamisotsuse? | Inimene. Kõik siinsed reeglid eeldavad inimese tehtavat ülevaatust |

## Föderaalõigus

### Title VII ja ebasoodne mõju

1964. aasta Civil Rights Acti Title VII keelab tööalase diskrimineerimise rassi, nahavärvi, usu, soo või rahvusliku päritolu tõttu, sealhulgas neutraalse testi kaudu, millel on mingile rühmale ebasoodne mõju (adverse impact) ja mis ei ole tööga seotud. Uniform Guidelines on Employee Selection Procedures annavad tavapärase rusikareegli, neli viiendikku reegli ([29 CFR §1607.4(D)](https://www.law.cornell.edu/cfr/text/29/1607.4)):

> Mis tahes rassi-, soo- või etnilise rühma valikumäära, mis on väiksem kui neli viiendikku (4/5) (ehk kaheksakümmend protsenti) kõrgeima määraga rühma määrast, loevad föderaalsed järelevalveasutused üldjuhul ebasoodsa mõju tõendiks. (tõlgitud inglise keelest)

Näiteks kui sinu testi sooritab 60% ühest rühmast ja 42% teisest, on suhe 42 ÷ 60 = 0,70, mis jääb alla 0,80: see on hoiatusmärk, mida tasub uurida. See ei ole diskrimineerimise tõend ja väikeste arvude korral võib suhe tugevalt kõikuda.

EEOC 2023. aasta tehniline juhend AI kasutamise kohta töötajate valikul eemaldati 2025. aasta jaanuaris. Uniform Guidelines on määrus, mitte juhis, ja kehtib endiselt. Vastutus ebasoodsa mõju eest jääb tööandjale, olenemata sellest, kes testi koostas.

### ADA ja kohandused

Americans with Disabilities Act (ADA) nõuab mõistlikke kohandusi kvalifitseeritud puudega kandidaatidele, ka testides ([29 CFR 1630.11](https://www.law.cornell.edu/cfr/text/29/1630.11)): test peab mõõtma oskust, mitte puuet. Ajapiiranguga testi puhul on tavaline kohandus lisaaeg. Ütle kandidaatidele enne alustamist, kuidas seda taotleda.

## New York City: Local Law 144

[Local Law 144](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page) koos Department of Consumer and Worker Protectioni (DCWP) reeglitega (6 RCNY §5-300 jj) kohaldub, kui tööandja või tööagentuur kasutab automatiseeritud töölevõtmisotsuste tööriista (automated employment decision tool, AEDT), mis oluliselt toetab värbamisotsuseid New York City töökohtadele. Tööriist, mis hindab või järjestab kandidaate ja mida kasutatakse otsustamiseks, kes liigub edasi, kuulub sinna väga tõenäoliselt. Enne sellise kasutamist vajad:

- **Kallutatuse auditit,** mille teeb sõltumatu audiitor kasutamisele eelneva aasta jooksul. Sõltumatu audiitor ei saa olla ei pakkuja ega sina kui tööandja.
- **Auditi avaldatud kokkuvõtet:** valiku- või tulemusmäärad ja mõjusuhted (impact ratio) soo, rassi/etnilise päritolu ja nende kombinatsioonide kaupa, teadmata kategooriasse kuuluvate kandidaatide arv ja tööriista kasutuselevõtu kuupäev.
- **Teadet kandidaatidele** vähemalt 10 tööpäeva enne kasutamist, koos teabega selle kohta, kuidas taotleda alternatiivset valikuprotsessi või kohandust.

Kuidas audit arvutab:

- **Valikumäär:** kategooria osakaal, kes liigub edasi. **Tulemusmäär** punkte andvate tööriistade puhul: kategooria osakaal, kelle tulemus on kogu valimi mediaanist kõrgem.
- **Mõjusuhe:** kategooria määr jagatud kõrgeima kategooria määraga.
- Kategooriad, mis moodustavad alla 2% andmetest, võib mõjusuhetest välja jätta.
- Andmed peavad olema päris. DCWP KKK ütleb: „Imputeeritud või tuletatud andmeid ei tohi kallutatuse auditi tegemiseks kasutada.“ (tõlgitud inglise keelest) Demograafilised andmed peavad tulema kandidaatidelt endilt, näiteks vabatahtlikust enesemääratlemise vormist.

## Illinois

Illinois Human Rights Acti muudatus (Public Act 103-0804, 775 ILCS 5/2-102(L)) kehtib alates 1. jaanuarist 2026. Tööandjad ei tohi:

- kasutada AI-d, mis mõjub kandidaatide või töötajate suhtes kaitstud tunnuse alusel diskrimineerivalt;
- kasutada postiindekseid kaitstud tunnuse asendajana.

Ja nad peavad teavitama kandidaate, kui AI-d kasutatakse värbamis- ja töölevõtmisotsustes. Illinois Department of Human Rights pakkus 2026. aasta mais välja teavitamise reeglid ja võttis need 2026. aasta juunis tagasi; ühtegi pole veel vastu võetud, seega järgi seadust ennast.

## Colorado

Colorado AI seadus tunnistati kehtetuks ja võeti uuesti vastu SB 26-189-ga, mis allkirjastati 14. mail 2026 ja kehtib alates 1. jaanuarist 2027. Attorney Generali reeglid on välja pakutud (kuulamine toimus 26. oktoobril 2026) ja need peaksid valmima enne seda kuupäeva. Töölevõtmisotsustes kasutatava suure riskiga AI juurutajate kohustused on:

- **Teade enne kasutamist** kandidaadile.
- **Ebasoodsa otsuse selgitus,** näiteks kui kandidaati ei võeta tööle või ta ei liigu edasi.
- **Parandamine ja ülevaatus:** võimalus andmeid parandada ja taotleda inimese tehtavat ülevaatust.
- **Dokumendid,** mida säilitatakse 3 aastat.

## California

- **Civil Rights Councili määrused automatiseeritud otsustussüsteemide kohta,** kehtivad alates 1. oktoobrist 2025: diskrimineerimisvastane õigus kohaldub automatiseeritud värbamistööriistadele samamoodi kui igale muule valikumeetodile. Tööandjad peavad säilitama töösuhte dokumente, sh automatiseeritud otsustussüsteemide andmeid, neli aastat (Cal. Code Regs. tit. 2, §11013(c)).
- **CCPA reeglid automatiseeritud otsustustehnoloogia kohta** kohalduvad töölevõtmisotsustele alates 1. jaanuarist 2027: teade enne kasutamist, õigus loobuda (opt-out) või otsus edasi kaevata ning õigus saada teavet selle kohta, kuidas tehnoloogiat kasutati.

## Kuupäevad

| Kuupäev | Mis kehtib |
| --- | --- |
| 5. juuli 2023 | New York City Local Law 144 jõustamine |
| 1. oktoober 2025 | California Civil Rights Councili reeglid automatiseeritud otsustussüsteemide kohta |
| 1. jaanuar 2026 | Illinois: teade AI kasutamisest, mitte diskrimineerivat AI-d, mitte postiindekseid asendajana |
| 1. jaanuar 2027 | Colorado AI seadus; California CCPA reeglid automatiseeritud otsuste kohta töölevõtmisel |

## Praktiline kontrollnimekiri tööandjatele

1. **Loetle töökohad ja kohad,** kuhu värbad: New York City, Illinois, Colorado, California, mujal USAs.
2. **Testi ainult seda, mida töö vajab.** Vali teemad ja läbimise lävi, mida saad selle rolli jaoks põhjendada.
3. **Uuenda kandidaatidele mõeldud teadet,** et see ütleks, et kasutatakse AI-d, kuidas tulemusi kasutatakse ning kuidas taotleda kohandust ja inimese tehtavat ülevaatust. Lisa Illinoisi ja Colorado sõnastus, kus need kehtivad.
4. **Paku kohandusi,** näiteks lisaaega, ja lepi need kokku enne, kui kandidaat alustab.
5. **Kogu demograafilised andmed kandidaatidelt endilt** vabatahtliku enesemääratlemise vormiga, hoituna värbamisotsustest eraldi. Ära neid kunagi tuleta.
6. **Kontrolli ebasoodsat mõju** oma tulemustes, esimese kontrollina neli viiendikku reegliga.
7. **New York City töökohtade puhul** telli sõltumatu kallutatuse audit, avalda selle kokkuvõte ja anna teade 10 tööpäeva enne tööriista kasutamist.
8. **Säilita dokumente nii kaua, kui sinu õigus nõuab,** näiteks Californias neli aastat ja Colorados kolm.
9. **Ära kunagi lükka tagasi ainult tulemuse põhjal.** Lase inimesel iga tulemus üle vaadata.

## Kuidas prepza sellele läheneb

prepza viib läbi ajapiiranguga valikvastustega oskuste intervjuusid, mille AI kirjutab töökuulutuse põhjal. USAs läheneb prepza samamoodi kui ELis. prepza ei väida, et ta vastab nõuetele või on sertifitseeritud.

Kuidas see tootes täna välja näeb:

- **AI kirjutab küsimused ja nende vastusevõtmed; hindamine käib kindlate reeglite järgi.** Ükski AI ei loe ega hinda kandidaadi vastust ning video- ega näoanalüüsi ei kasutata. Häälerežiimis muudetakse kõne tekstiks, et sobitada see vastusevariandiga, mille kandidaat kinnitab; kõnet ei salvestata kunagi ja häält ei analüüsita kunagi.
- **Sina kiidad teemad heaks** enne, kui ühtegi küsimust kirjutatakse, ja sina valid läbimise läve.
- **Otsustavad inimesed.** prepza ei lükka kandidaate tagasi ega saada äraütlemiskirju.
- **Kaitstud tunnuseid ei koguta.** prepza ei küsi, ei tuleta ega salvesta kunagi kandidaatide sugu, rassi, vanust, puuet, postiindeksit ega muid kaitstud tunnuseid.
- **Eksport kallutatuse auditi jaoks.** Ettevõtte toimingute logi lehel saab omanik alla laadida CSV-faili lõpetanud kandidaatidest, kogu ettevõtte või ühe intervjuu kohta ja kahe kuupäeva vahel: iga kandidaadi hinne, läbimise lävi, kas ta sooritas ja kas tema tulemus oli intervjuu mediaanist kõrgem. Iga rida on seotud kandidaadi e-posti aadressiga, et saaksid selle ühendada enesemääratletud kategooriatega, mille ise kogusid; seejärel eemalda e-posti veerg ja anna fail oma sõltumatule audiitorile, kes arvutab valiku- ja tulemusmäärad ning mõjusuhted. Sama failiga saad ise teha neli viiendikku kontrolli.
- **Lisaaega** +25%, +50% või +100% iga küsimuse kohta saab anda igale kandidaadile, kes seda palub, enne kui ta alustab. prepza salvestab ainult lisaaja suuruse, mitte kunagi põhjust. Häälerežiimis saab kandidaat alati selle asemel vastusevarianti puudutada ja sa saad seadistada intervjuu nii, et vastata saab ainult puudutades.
- **Kandidaatide teavituse mallid,** üldine ning versioonid New York City, Illinoisi ja Colorado jaoks, on [dokumentide lehel](/documents) koos ettevõtetele mõeldud juhistega.
- **New York City.** prepzal ei ole veel olnud oma sõltumatut kallutatuse auditit. Ära kasuta prepzat New York City töökohtade jaoks enne, kui oled teinud selle, mida Local Law 144 sinult tööandjana nõuab: sõltumatu kallutatuse audit kasutamisele eelneva aasta jooksul, selle avaldatud kokkuvõte ja teade kandidaatidele 10 tööpäeva ette.
- **Andmed.** CCPA mõttes on sinu ettevõte ettevõte (business) ja prepza selle teenusepakkuja (service provider) [andmetöötluslepingu](/dpa) ja selle USA osa alusel. Andmeid majutatakse ELis, mõned volitatud alamtöötlejad asuvad USAs (vaata [privaatsuspoliitikat](/privacy)), ja neid ei kasutata AI-mudelite treenimiseks.
- **Säilitamine.** Kandidaatide andmed kustutatakse 12 kuud pärast kutset. Kui sinu õigus nõuab dokumentide pikemat säilitamist, näiteks Californias neli aastat, laadi PDF-aruanded ja kallutatuse auditi fail alla ja säilita need ise; prepza ei säilita tulemusi vaikimisi kauem.

## Loe ka

- [Kas AI kasutamine värbamisel on ELis seaduslik?](/guides/is-ai-hiring-legal-in-the-eu)
- [Kas AI kasutamine värbamisel on Ühendkuningriigis seaduslik?](/guides/is-ai-hiring-legal-in-the-uk)
- [Kuidas ajastada oskustesti: küsimuse taimer, pikkus ja lisaaeg](/guides/skills-test-timing-and-extra-time)
- [Kandidaatide testimine värbamisel: praktiline juhend](/pre-employment-testing)

## Allikad

- Uniform Guidelines on Employee Selection Procedures, [29 CFR §1607.4(D)](https://www.law.cornell.edu/cfr/text/29/1607.4).
- Regulations to implement the equal employment provisions of the Americans with Disabilities Act, [29 CFR 1630.11](https://www.law.cornell.edu/cfr/text/29/1630.11).
- New York City Local Law 144 of 2021 ja 6 RCNY §5-300 jj; DCWP, [Automated Employment Decision Tools](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page) ja selle KKK.
- Illinois Human Rights Act, 775 ILCS 5/2-102(L), muudetud Public Act 103-0804-ga.
- Colorado SB 26-189.
- California Code of Regulations, title 2, §11013(c); California Consumer Privacy Acti määrused automatiseeritud otsustustehnoloogia kohta.
