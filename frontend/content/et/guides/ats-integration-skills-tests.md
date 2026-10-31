---
title: "Kuidas ühendada oskustestid oma ATS-süsteemiga"
seoTitle: "Oskustestide ühendamine ATS-süsteemiga: praktiline juhend"
description: "Saada oskustestid ja saa tulemused automaatselt oma ATS-süsteemi kaudu, jäta värbamisotsused inimestele ja tea, mida kõigepealt kontrollida."
updated: "2026-10-21"
---

# Kuidas ühendada oskustestid oma ATS-süsteemiga

Enamik värbamismeeskondi hoiab kandidaate kandidaatide haldussüsteemis (ATS) ja teeb oskusteste mõnes teises tööriistas. Kui need kaks pole ühendatud, kopeerib keegi ATS-ist e-posti aadressid, saadab kutsed käsitsi, ootab ja kopeerib siis tulemused tagasi. Viie kandidaadiga see toimib. Viiekümnega lähevad kutsed välja hilja, tulemused seisavad teises vahekaardis, mida keegi ei ava, ja head kandideerijad võtavad ootamise ajal vastu teisi pakkumisi.

See juhend selgitab, mida teeb hea ühendus ATS-süsteemi ja testimistööriista vahel, mida kontrollida enne, kui sellele loota, ja kuidas see seadistada nii, et rutiinse töö teeb automaatika, aga iga värbamisotsuse teevad endiselt inimesed.

## Miks neid üldse ühendada

| Ilma ühenduseta | Ühendusega |
| --- | --- |
| Keegi ekspordib või kopeerib kandidaatide e-posti aadresse | Kandidaadi viimine etappi saadab kutse |
| Kutsed lähevad välja siis, kui kellelgi on aega | Kutsed lähevad välja mõne minuti jooksul pärast liigutamist |
| Tulemused jäävad testimistööriista | Tulemused ilmuvad kandidaadi juurde ATS-süsteemis |
| Värbavad juhid küsivad: „Kas keegi on teda juba testinud?“ | ATS näitab, keda testiti ja kuidas tal läks |
| Trükivead e-posti aadressides ja kahe silma vahele jäänud kandidaadid | ATS on ainus nimekiri kõigist kandideerijatest |

Kiirus on olulisem, kui paistab. Mida kauem kulub kandideerimisest vastuseni, seda rohkem kandidaate loobub või võtab vastu teise töö. Täpsed loobumismäärad sõltuvad palju rollist ja turust, nii et suhtu avaldatud numbritesse ettevaatlikult, aga suund on alati sama: aeglane protsess kaotab inimesi ja tugevaimatel kandideerijatel on tavaliselt kõige rohkem valikuid.

## Milline on hea töövoog

Korralik integratsioon järgib etappe, mida sa juba kasutad. See ei leiuta uut protsessi.

1. **Kandidaat kandideerib** ja jõuab nagu tavaliselt sinu ATS-süsteemi.
2. **Inimene viib ta testimise etappi,** näiteks „Oskustest“. See liigutus on käivitaja, nii et testitavad valib endiselt inimene.
3. **Testimistööriist saadab kutse** automaatselt, selle ametikohaga seotud testile.
4. **Kandidaat teeb testi** endale sobival ajal, sinu määratud tähtaja jooksul.
5. **Tulemused kirjutatakse ATS-süsteemis kandidaadi juurde:** punktisumma, kas ta läbis testi, võimalikud aususe märked ja link kõigile vastustele.
6. **Inimene vaatab tulemuse üle** ja viib kandidaadi edasi või mitte.

Kaks asja jäävad meelega käsitsi: testitavate valimine ja otsus, mis edasi saab. Ühendus kaotab ainult vahepealse kopeerimise.

### Miks mitte käivitada iga uue kandideerimise peale?

Mõni tööriist kutsub kõiki, kes kandideerivad. Suure kandidaatide arvuga ametikohtadel, kus kõik teevad sama testi, võib see sobida. Etappi, kuhu kandidaate liigutad, on aga lihtsam kontrollida: saad vahele jätta kandideerijad, kes selgelt ei vasta kohustuslikule nõudele (puudub tööluba, vale asukoht), ega testi kunagi, ega maksa, kellegi eest, kellest sa niikuinii loobuksid.

## Mida kontrollida enne integratsiooni valimist

Iga lubadus „integreerub sinu ATS-süsteemiga“ ei tähenda sama asja. Esita need küsimused enne, kui midagi ühendad.

| Küsimus | Miks see on oluline | Hea vastus |
| --- | --- | --- |
| Kuidas ühendus luuakse? | Jagatud paroole ja teenusepakkuja hoitavaid kontosid on raske auditeerida või tühistada | API-võti või token, mille sinu ettevõte loob ja saab igal ajal kustutada |
| Mida võti teha saab? | Täieliku ligipääsuga võti on lekke korral risk | Kitsaimad õigused, mida integratsioon vajab, dokumentatsioonis kirjas |
| Mis käivitab kutse? | Pead täpselt teadma, millal kandidaadid e-kirja saavad | Konkreetne etapp, mille valid iga ametikoha jaoks |
| Kuhu tulemused jõuavad? | Tulemustest, mida keegi ei näe, pole abi | Kandidaadi profiilile, märkme või kommentaarina, mida sinu meeskond juba loeb |
| Mis juhtub, kui kutse ei õnnestu? | Krediit otsas, trükiviga, peatatud konto: kandidaadid jäävad märkamatult toppama | Keegi saab teate ja kandidaadi saab uuesti kutsuda |
| Kas sündmust saab töödelda kaks korda? | ATS-süsteemid saadavad sündmusi uuesti; kandidaat ei tohiks saada kahte kutset | Iga kandidaat kutsutakse testile üks kord, ükskõik mitu korda sündmus saabub |
| Kuidas sissetulevaid sündmusi kontrollitakse? | Kontrollimata aadressile saab saata võltssündmusi | Allkirjastatud päringud, mida tööriist kontrollib |
| Kui kaua kandidaatide andmeid hoitakse? | Andmekaitseseadused, näiteks GDPR, eeldavad selget säilitusaega | Kindel tähtaeg ja kustutamine, kui kustutad ametikoha, testi või konto |
| Mis see maksab? | Kasutajapõhised paketid võivad automaatika kalliks teha | Kulu, mida saad testitud kandidaadi kohta ette arvestada |

Kui teenusepakkuja ei oska tõrgete ja korduste küsimustele selgelt vastata, siis arvesta, et saad selle teada valusal teel.

### Andmekaitse

Kahe süsteemi ühendamine tähendab, et kandidaatide andmed, vähemalt nimed ja e-posti aadressid, liiguvad kahe ettevõtte vahel. GDPR-i ja sarnaste seaduste järgi on testimisteenuse pakkuja tavaliselt sinu volitatud töötleja, seega vajad andmetöötluslepingut ja peaksid kandidaatidele privaatsusteates või kutses ütlema, et oskustest on protsessi osa. Edasta ainult need andmed, mida test vajab. Testide ja AI õigusliku poole kohta värbamisel loe [Kas AI kasutamine värbamisel on ELis seaduslik?](/guides/is-ai-hiring-legal-in-the-eu)

## Seadistamise kontrollnimekiri

Enne kui lülitad selle päris ametikoha jaoks sisse:

1. **Loo ATS-süsteemis eraldi etapp ainult testimiseks,** näiteks „Oskustest“. Ära kasuta etappi, mis tähendab midagi muud, muidu kutsutakse kandidaate kogemata.
2. **Loo võti administraatori kontolt,** mis näeb kõiki töökuulutusi, mida soovid siduda, ja ainult dokumentatsioonis nimetatud õigustega.
3. **Seo iga töökuulutus oma testiga** ja vali etapp, mis kutse käivitab.
4. **Seadista webhook,** kui sinu ATS nõuab seda käsitsi, ja kleebi selle saladus sinna, kus tööriist seda küsib.
5. **Testi iseendaga.** Lisa kandidaat oma e-posti aadressiga, vii ta etappi, tee test ja kontrolli, et märge ilmub ATS-süsteemi.
6. **Otsusta, kes jälgib tõrkeid:** kes saab teate, kui kutset ei saa saata, ja kes selle korda teeb.
7. **Lepi meeskonnaga kokku, kuidas tulemusi lugeda.** Läbimispiir on suunis, mitte automaatne äraütlemine. Otsusta see enne tulemuste saabumist, mitte pärast.

## Levinud vead

- **Automatiseeritakse otsus, mitte paberitöö.** Kõigi teatud punktisummast allapoole jääjate automaatne tagasilükkamine kaotab inimkontrolli, mis märkab halba küsimust või kandidaati, kellel oli ühendusprobleem. Las punktisumma sorteerib, otsustab inimene.
- **Käivitamine valest etapist.** Etapp, mida värbajad kasutavad muul otstarbel, saadab teste inimestele, kes neid saama ei peaks.
- **Üks test kõigile ametikohtadele.** Ühendus teeb sama testi igale poole saatmise lihtsaks. Test aitab kõige rohkem siis, kui see on loodud just selle töö jaoks. Vaata [Oskustestid vs CV-de sõelumine](/guides/skills-tests-vs-cv-screening).
- **Keegi ei jälgi tõrkeid.** Kui kutse ebaõnnestub vaikselt, ootab kandidaat e-kirja, mis kunagi ei tule, ja sina arvad, et ta eiras seda.
- **Võti, mis on seotud lahkuva inimesega.** Mõni ATS-i võti tegutseb selle looja nimel. Kui selle inimese konto suletakse, lakkab ühendus töötamast. Kasuta kontot, mis jääb alles, ja ühenda uuesti, kui inimeste rollid muutuvad.
- **ATS-ist väljaspool olevad kandidaadid ununevad.** Soovitatud kandidaadid ja otse pöördujad, kes ATS-i ei jõua, vajavad samuti kutset. Hoia alles ka käsitsi kutsumise võimalus.

## Kuidas testee seda teeb

testee ühendub süsteemidega **Workable, Greenhouse, Teamtailor, Recruitee ja Breezy HR** ning järgib ülal kirjeldatud töövoogu.

- **Sinu võti, sinu kontroll.** Omanik või administraator ühendab ATS-i ettevõtte vahekaardil Integratsioonid võtmega, mille sinu ettevõte ATS-is loob. testee kontrollib seda enne salvestamist, hoiab seda krüpteeritult ega näita seda enam kunagi. Ühenduse katkestamine kustutab võtme ja seotud töökuulutused kohe.
- **Seo töökuulutus intervjuuga.** Vali ATS-i töökuulutus ja kutse käivitav etapp ning seo see olemasoleva testee intervjuuga või loo uus intervjuu töökuulutuse ATS-is oleva teksti põhjal. Vaatad teemad üle enne, kui ühtki küsimust kirjutatakse.
- **Liiguta kandidaati, kutse läheb välja.** Iga kandidaat kutsutakse intervjuule üks kord, isegi kui ATS saadab sama sündmuse kaks korda.
- **Tulemused tagasi ATS-is.** Kui kandidaat lõpetab, lisab testee talle ATS-is märkme või kommentaari tema hinde, läbimise, võimalike aususe märgetega (lehelt lahkumine, kopeerimiskatsed, vastused, mis valiti liiga kiiresti, et küsimust lugeda) ja lingiga hindamislehele, kus on kõik vastused.
- **Tõrked ei jää märkamata.** Kui kandidaati ei saa kutsuda, näiteks sest ettevõttel on krediit otsas, e-kirjade limiit täis või testee on kutsed peatanud, saavad kõik ettevõtte liikmed teate, kus on ATS-i nimi. Krediidi puudumise tõttu kutsumata jäänud kandidaadid kutsutakse pärast juurdelaadimist automaatselt ja iga töökuulutuse ootel kandidaate saab ühe klikiga uuesti kutsuda.
- **Slack, kui sa seda kasutad.** testee saab postitada teateid, näiteks lõpetanud kandidaadist või ATS-i kandidaadist, keda ei õnnestunud kutsuda, sinu valitud Slacki kanalisse.
- **Sinu oma platvorm.** Kui sinu ATS-i nimekirjas pole, saad testee [API](/api-docs) abil kutsuda kandidaate API-võtmega ja saada allkirjastatud webhooki, kui kandidaat alustab, lõpetab, kutse ei jõua temani, tema kutse aegub või ta eemaldatakse, ning kui intervjuu on valmis.
- **Andmeid hoitakse kindla aja.** ATS-ist salvestatud kandidaadid kustutatakse 365 päeva pärast või varem koos nende intervjuu või ettevõttega.

Mõni ATS vajab sammu enda poolel. Greenhouse, Teamtailor ja Recruitee paluvad lisada webhooki käsitsi; testee dialoog Juhised näitab aadressi ja kuhu selle saladus kleepida. Workable'i ja Breezy HR-i webhookid seadistab testee ise.

Hind on kandidaadipõhine, ilma tellimuseta: maksad ainult kandidaatide eest, kes vastavad vähemalt ühele küsimusele, 50 $ juurdelaadimise puhul 5 $ kandidaadi kohta, alates 200 $ juurdelaadimisest 4 $, alates 600 $ juurdelaadimisest 3 $ ja alates 1000 $ juurdelaadimisest 2 $. Hinnad on siin USA dollarites, Kanadas, Austraalias, Iisraelis, Poolas, Šveitsis, Jaapanis, Lõuna-Koreas, Taiwanis, Hongkongis, Tais, Singapuris, Indias, ülejäänud Euroopas ja Ühendkuningriigis aga kohalikus valuutas; käibemaksu või müügimaksu arvestatakse maksmise ajal. ATS-i ühendamine ja intervjuude loomine on tasuta ning sinu esimese ettevõtte esimesed 3 kandidaati on tasuta. Vaata [hindu](/pricing).

## Loe ka

- [Kuidas sõeluda 100 kandidaati päevaga](/guides/screen-100-applicants-in-a-day)
- [Oskustestid vs CV-de sõelumine](/guides/skills-tests-vs-cv-screening)
- [Kandidaatide testimine värbamisel: praktiline juhend](/pre-employment-testing)
