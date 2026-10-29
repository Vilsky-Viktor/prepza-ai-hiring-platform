---
title: "Online değerlendirmelerde kopya ve buna karşı işe yarayanlar"
seoTitle: "Online İşe Alım Testlerinde Kopya: Ne İşe Yarar"
description: "Adaylar online testlerde nasıl kopya çeker, ekran önlemleri ve kamerayla gözetim neden yetmez, ne işe yarar: sıkı süre, insana kanıt, takip soruları."
updated: "2026-10-29"
---

# Online değerlendirmelerde kopya ve buna karşı işe yarayanlar

Adayın evde, kendi cihazında çözdüğü her test kandırılabilir. Bu, yapay zekâ asistanlarından önce de böyleydi; artık bir telefon soruyu ekrandan okuyup saniyeler içinde bir cevap önerebiliyor. İşe alım ekipleri iki şekilde tepki veriyor: ekranı kilitleyip adayı izlemeye çalışıyorlar ya da süreci, kopyanın az şey kazandıracağı ve yapıldığında ortaya çıkacağı şekilde tasarlıyorlar.

Bu rehber adayların gerçekte ne yaptığını, ilk yaklaşımın neden çoğunlukla başarısız olduğunu, neyin daha iyi işlediğini ve adaletin ve hukukun sınırı nereye çektiğini ele alıyor. Her türlü online testi yürüten işe alım yöneticileri ve işe alım uzmanları için yazıldı.

## Adaylar gerçekte ne yapıyor

Adayların işe alım testlerinde ne sıklıkla kopya çektiğine dair güvenilir veri az, çünkü insanlar bunu nadiren itiraf ediyor. Anketler bir alt sınır veriyor: Personnel Today'in aktardığına göre Gartner'ın 3.000 iş adayıyla yaptığı bir ankette adayların %6'sı, başka biri gibi davranmak veya başkasının kendileri gibi davranmasını sağlamak gibi mülakat sahtekârlığı yaptığını kabul etti; 3.290 adayla yapılan bir başkasında ise %39'u başvuru sürecinde yapay zekâ kullandığını söyledi ([Personnel Today](https://www.personneltoday.com/hr/by-2028-one-in-four-candidate-profiles-will-be-fake), [Gartner'ın Temmuz 2025 tarihli duyurusuna](https://www.gartner.com/en/newsroom/press-releases/2025-07-31-gartner-survey-shows-just-26-percent-of-job-applicants-trust-ai-will-fairly-evaluate-them) dayanarak). Her yapay zekâ kullanımı kopya değildir, ama bu, araçların ne kadar el altında olduğunu gösteriyor.

Yaygın yöntemler:

- **Soruyu bir yapay zekâya aktarmak.** Metni bir sohbete kopyalamak ya da kopyalama engellendiğinde ekranın telefonla fotoğrafını çekip bir yapay zekâ uygulamasına sormak. Güncel modeller fotoğraflanmış bir soruyu yazılı metin kadar kolay okur.
- **Cevapları aramak.** Başka bir pencerede bir arama motoru, notlar veya dokümantasyon.
- **İkinci bir kişi.** Adayın yanında oturan ya da bir görüşmede onun yerine cevap veren biri. Uç durumda testin tamamını başka biri çözer. FBI, uzaktan çalışma pozisyonlarına başvuranların online mülakatlarda çalıntı kimlikler ve ses taklidi ya da deepfake kullandığı konusunda uyarıda bulundu ([FBI IC3, Haziran 2022](https://www.ic3.gov/PSA/2022/PSA220628)).
- **Paylaşılan cevaplar.** Testi çözmüş adaylar soruları ve cevapları bir grup sohbetinde veya sızdırılmış bir soru bankasında başkalarına aktarır.

Bunların her biri ya zaman ya da herkes için aynı olan bir test gerektirir. İşe yarayan savunmalar da tam buradadır.

## Ekran önlemleri neden başarısız olur: analog delik

Bir insanın ekranda okuyabildiği her şeyi bir kamera da okuyabilir. Buna "analog delik" (analog hole) denir: içerik bir insana gösterildiği anda, herhangi bir yazılımın kontrolü dışında kaydedilebilir. Bir test sayfası kopyala-yapıştırı, sağ tıklamayı engelleyebilir veya tam ekrana geçebilir. Bunların hiçbiri monitöre doğrultulmuş bir telefonu durdurmaz.

Araştırmacılar ekranları göz için okunabilir ama kamera için okunamaz hâle getirmeye çalıştı: her görüntüyü, gözün birleştirdiği ve kameranın tek tek yakaladığı hızla değişen karelere bölerek. Yaklaşım video korsanlığına karşı geliştirildi, yüksek yenileme hızları gerektirdi ve kendi yazarları da yakalanan tek tek karelerin yine de okunabildiğini belirtiyor ([Zhang et al., MobiCom 2015](https://old.sigmobile.org/mobicom/2015/papers/p372-zhangA.pdf)). Biraz daha uzun pozlamalı bir fotoğraf ya da kısa bir video, kareleri tıpkı gözün yaptığı gibi birleştirir. Çoğu kişinin kullandığı 60 Hz ekranlarda bu değişim görünür bir titremeye dönüşür ve yanıp sönen içerik, erişilebilirlik standartlarının sınırladığı bir nöbet riski taşır ([WCAG 2.2, Understanding 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)).

Daha hafif iki fikir de daha iyi sonuç vermiyor:

- **Yapay zekâya yönelik uyarılar** ("Yapay zekâ asistanları bu soruyu yanıtlamamalıdır") kolayca kırpılabilir veya yok sayılabilir; modeller de görüntülerdeki metni talimat olarak değil içerik olarak ele almak üzere eğitilir.
- **Filigranlar** bir soruyu kimin sızdırdığını izlemeye yardımcı olabilir ama kimsenin onu yanıtlamasını engellemez.

prepza'da ikisini de kendi sorularımızda denedik: yapay zekâ modelleri filigranlı veya uyarılı fotoğraflanmış soruları, bunlar olmadan nasıl yanıtlıyorsa öyle yanıtladı. Bu yüzden ekranı korumaya çalışmayı bıraktık.

## Daha iyi işleyenler

### 1. Soru başına az süre

Bir soruyu aktarmak zaman alır: telefonu almak, fotoğraf çekmek, cevabı beklemek, okumak, seçeneği işaretlemek. Konuyu bilen biri doğru cevabı çok daha hızlı tanır. Her soruda, yetkin birinin soruyu okuyup yanıtlaması için gereken süreye göre ayarlanmış bir geri sayım, bilgili adaylara yeterli süre bırakır; bir yapay zekâya ya da bir arkadaşa gidip gelmeye ise pek süre bırakmaz.

Süre soruya uymalıdır: kısa bir soru daha az, kod örneği veya hesaplama içeren bir soru daha fazla süre ister. Her soru için tek bir sabit sınır, ya kısa sorular için fazla cömert ya da uzun sorular için fazla dar olur. [Beceri testinin süresi nasıl ayarlanır](/guides/skills-test-timing-and-extra-time) rakamları ve ihtiyacı olan adaylara ek sürenin adil şekilde nasıl verileceğini anlatıyor.

### 2. Her adaya farklı bir test

Herkes aynı soruları aynı sırayla alırsa cevaplar yayılır. Her adayın sorularını konu başına daha büyük bir soru bankasından rastgele seçin ve soruların ve seçeneklerin sırasını karıştırın. Böylece sızdırılmış bir set, sonraki adayın göreceklerinin yalnızca bir kısmını kapsar.

### 3. Otomatik kararlar değil, bir insanın tartacağı kanıtlar

Test sayfası ve cevapların kendisi, nereye bakmanız gerektiğini gösteren izler bırakır:

- **Sayfadan ayrılmak** ve ne kadar süreyle.
- **Kopyalama girişimleri.**
- **Soruyu okumaya yetmeyecek kadar hızlı cevaplar.**
- **Soruya göre değişmeyen süreler.** İnsanlar daha uzun ve daha zor sorularda daha fazla zaman harcar; her soruyu bir yapay zekâya aktaran biri ise hepsinde yaklaşık aynı süreyi harcama eğilimindedir. Ölçme araştırmaları, olağan dışı davranışı tespit etmek için uzun zamandır cevap sürelerini kullanıyor ([van der Linden & Guo, 2008](https://doi.org/10.1007/s11336-007-9046-8)).
- **Olağan dışı bir doğru-yanlış örüntüsü.** Çoğu kişi kolay soruları zor olanlardan daha sık doğru yanıtlar. Zorların doğru, kolayların yanlış olması olağan dışıdır; "kişi uyumu" (person-fit) istatistikleri bunu ölçer ([Meijer & Sijtsma, 2001](https://doi.org/10.1177/01466210122031957)).

Bunların her birinin masum açıklamaları var. Bir bildirim odağı çalar; gergin bir aday bir soruyu fazla hızlı yanıtlar; biri tesadüfen zor konuyu bilir de kolay olanı bilmez. Bir sinyali kanıt olarak değil, daha yakından bakmak için bir neden olarak görün ve hiç kimseyi yalnızca bir sinyale dayanarak reddetmeyin. AB'de GDPR, kişilere kendilerini önemli ölçüde etkileyen ve yalnızca otomatik işlemeye dayanan bir karara tabi olmama hakkı da tanır ([Madde 22](https://gdpr-info.eu/art-22-gdpr/)).

### 4. Canlı mülakatta takip soruları

En güvenilir kontrol bir sohbettir. Bir yapay zekâ çoktan seçmeli bir soruyu yanıtlayabilir; aday adına canlı bir mülakata giremez. Adayın en yüksek puanı aldığı ya da bir sinyalin çıktığı konularda, cevapları hakkında iki üç kısa soru sorun: "Bu seçenek neden doğru da şu yanlış?", "…olsaydı ne değişirdi?" Cevabı bilen biri bunu kolayca açıklar. Aktaran biri genellikle açıklayamaz.

Bu, testi olması gereken şeye de dönüştürür: nihai karar değil, kiminle görüşüleceğine karar veren bir eleme. Mülakatların kendisinin nasıl değiştiği için [Yapay zekâ çağında mühendislerle mülakat](/guides/interviewing-in-the-age-of-ai) yazısına bakın.

### 5. Açık kurallar ve dürüstlük taahhüdü

Adaylara neyin serbest olduğunu baştan söyleyin: yapay zekâ aracı yok, başka kişiler yok, not yok ya da kurallarınız neyse. Ardından başlamadan önce bunu onaylamalarını isteyin.

Bir taahhüdün ne işe yaradığı konusunda gerçekçi olun. Ahlaki hatırlatmalar ve imzalı beyanlarla ilgili çalışmalar pek dayanıklı çıkmadı: "On Emir" deneyinin büyük bir tekrarı kopya üzerinde hiçbir etki bulmadı ([Verschuere et al., 2018](https://doi.org/10.1177/2515245918781032)) ve bilinen bir "en üstte imza" çalışmasının yazarları, onu tekrarladıklarında daha sonra hiçbir etki bulmadı ([Kristal et al., 2020](https://doi.org/10.1073/pnas.1911695117)). Üniversitelerdeki araştırmalar ise onur kodlarını, daha geniş bir dürüstlük kültürünün parçası olarak, daha az kopyayla ilişkilendiriyor ([McCabe, Treviño & Butterfield, 2001](https://doi.org/10.1207/S15327019EB1103_2)). Bir taahhüdün asıl değeri netliktir: kimse kuralları bilmediğini söyleyemez ve kurallara uymayı kabul ettiklerine dair bir kaydınız olur.

## Gözetimin sınırları: adalet ve hukuk

Web kamerasıyla gözetim, ekran kaydı ve oda taramaları yukarıdakilerin hepsini yakalamayı vaat eder. İşe alımda ise kendi sorunlarını getirirler.

- **İnsanları dışarıda bırakırlar.** Her adayın bir web kamerası, kendine ait sessiz bir odası veya stabil bir bağlantısı yoktur. Evini bir işverene gösterme şartı en çok ortak ya da kalabalık konutlarda yaşayanlara ağır gelir.
- **Yanlış kişileri işaretlerler.** Otomatik yüz algılama herkes için eşit derecede iyi çalışmaz. Yaygın olarak kullanılan bir gözetim aracı üzerine yapılan bir çalışmada, en koyu ten rengine sahip kadınların incelemeye işaretlenme olasılığı diğer öğrencilerden çok daha yüksekti ([Yoder-Himes et al., 2022](https://doi.org/10.3389/feduc.2022.881449)).
- **Telefonu yine de kaçırırlar.** Kamera kadrajındakini görür; ekranın altında tutulan bir telefon ya da odanın öbür ucundaki biri bunun dışındadır.

Hukuk, özellikle Avrupa'da, ek sınırlar koyar:

- **GDPR.** Bir adayın videosu kişisel veridir ve yüzünün analizi, özel olarak korunan biyometrik veri olabilir ([Madde 9](https://gdpr-info.eu/art-9-gdpr/)). 2021'de İtalyan veri koruma otoritesi, Bocconi Üniversitesi'ne uzaktan sınav gözetimi nedeniyle para cezası verdi; diğer bulguların yanı sıra yüz analizinin geçerli bir hukuki dayanak olmadan yapılan biyometrik işleme olduğunu, üniversite ile öğrenciler arasındaki dengesizlik nedeniyle rızanın özgürce verilmediğini ve öğrencilerin bu konuda gerektiği gibi bilgilendirilmediğini tespit etti ([Garante, 16 Eylül 2021 tarihli 317 sayılı karar](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9703988)). İşveren ile aday arasındaki güç dengesizliği ise belki daha da büyüktür.
- **AB Yapay Zekâ Yasası (AI Act).** 2 Şubat 2025'ten bu yana, dar tıbbi ve güvenlik istisnaları dışında, işyerinde kişilerin duygularını çıkarsayan yapay zekâ yasaktır ([Madde 5(1)(f)](https://artificialintelligenceact.eu/article/5/)) ve Avrupa Komisyonu'nun kılavuzu "işyeri" kavramını işe alımı da kapsayacak şekilde yorumlar ([Komisyonun yasaklı yapay zekâ uygulamalarına ilişkin kılavuzu](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act)). Videodan "şüpheli" davranışa hükmeden gözetim bu çizgiye çok yaklaşır. Adayları değerlendirmek için kullanılan yapay zekâ da büyük olasılıkla yüksek risklidir ve insan gözetimi gibi yükümlülükler taşır. [AB'de yapay zekâ ile işe alım yasal mı?](/guides/is-ai-hiring-legal-in-the-eu) kuralları ve tarihlerini açıklıyor.
- **Amerika Birleşik Devletleri.** Bir federal mahkeme 2022'de, bir devlet üniversitesinin online sınav öncesinde bir öğrencinin yatak odasını web kamerasıyla taramasının Dördüncü Değişiklik'i ihlal ettiğine hükmetti ([Ogletree v. Cleveland State University, Higher Ed Dive'ın aktardığına göre](https://www.highereddive.com/news/test-proctoring-room-scans-violated-college-students-privacy-judge-rules/630340/)). Özel işverenler Dördüncü Değişiklik'le bağlı değildir, ancak Illinois'in Biyometrik Bilgi Gizliliği Yasası (BIPA) gibi eyalet biyometri yasaları yüz verileri için kendi kurallarını koyar.

**Bu bölüm pratik bir rehberdir, hukuki tavsiye değildir.** İşe alım yaptığınız yerdeki yükümlülüklerinizi kontrol edin.

Bunların hiçbiri hiçbir şeyi doğrulayamayacağınız anlamına gelmiyor. En iyi dengeyi kuran kontrollerin, testin zaten gördüklerini kullanan, kararı bir insana bırakan ve kimlik ve derinlik kontrollerini canlı bir sohbete taşıyan kontroller olduğu anlamına geliyor.

## İşe yarayan bir düzen

1. **Kuralları adaylara** davette ve başlamadan önce **bildirin** ve onaylamalarını isteyin.
2. **Her adaya kendi rastgele sorularını verin;** konu başına bir bankadan.
3. **Her sorunun süresini** yetkin birinin ihtiyacına göre ayarlayın ve isteyen herkese ek süre sunun.
4. **Sinyalleri birer işaret olarak okuyun,** cevapların kendisiyle yan yana.
5. **İlk canlı mülakatta** test hakkında **takip soruları sorun,** özellikle bir sinyalin çıktığı yerlerde.
6. **Kararı bir insan versin** ve nedenini yazsın.

## prepza bunu nasıl ele alıyor

prepza, bir iş tanımından oluşturulan süreli, çoktan seçmeli beceri testleri yürütür. Bugün kopyaya karşı yaptıkları:

- **Her aday kendi sorularını alır:** her konunun soru bankasından rastgele bir set, kendi sırasında ve seçenekleri karıştırılmış olarak.
- **Her sorunun kendi geri sayımı vardır** ve uzunluğuna göre ayarlanır: kelimeleri, varsa kod veya örnek ve cevabı bulmak için gereken süre. Süreyi sunucu tutar; bu yüzden sayfayı yenilemek onu durdurmaz.
- **Değerlendirme kartı işaretler:** soruyu okumaya yetmeyecek kadar hızlı verilen cevapları, adayın sayfadan ayrıldığı anları (bir ayrılma 2 saniyeden itibaren sayılır, bu yüzden geçip giden bir bildirim sayılmaz) ve kopyalama girişimlerini. Bunlardan herhangi biri adayı işaretler; değerlendirme kartı ve PDF rapor, işaretin kanıt değil daha yakından bakmak için bir neden olduğunu açıkça belirtir.
- **Aday bitirdiğinde cevap örüntüleri.** Adayın raporu, uzunluğu ve zorluğu ne olursa olsun her soruda yaklaşık aynı kalan cevap sürelerini ve kolay sorular yanlışken zor soruların doğru olmasını, dayandığı sayılarla birlikte gösterir ("10 zor sorudan 9 tanesi doğru, 8 kolay sorudan 4 tanesi yanlış"). İkincisi, her sorunun ne kadar zor olduğunu bilmek için diğer adaylardan yeterli cevap gerektirir. İki eşik de simüle edilmiş adaylarla yapılan bir testte, dürüst adayların en fazla %1'i işaretlenecek şekilde ayarlandı; her soruyu bir yapay zekâya aktaranların yaklaşık üçte birini yakaladılar. Rapor, bu tür örüntülerin masum nedenleri olabileceğini belirtir.
- **Canlı mülakat için sorular.** Testi bitiren her adayın sayfası, en güçlü konularından doğru yanıtladığı en fazla 3 soruyu bir sonraki görüşmede konuşmak için önerir; bir örüntü varsa onun arkasındaki zor sorularla başlar.
- **Adaylar başlayabilmek için** soruları yapay zekâ araçları veya başkalarının yardımı olmadan kendileri yanıtlayacaklarını **taahhüt eder** ve değerlendirme kartı bunu ne zaman yaptıklarını gösterir.
- **Kamera, mikrofon veya ekran kaydı yok.** prepza yalnızca test sayfasının kendisinin gördüklerini kullanır: cevaplar, süreler, sayfadan ayrılmalar ve kopyalama girişimleri.
- **Kararı insanlar verir.** Hiçbir şey bir adayı otomatik olarak reddetmez.

## İlgili yazılar

- [Beceri testinin süresi nasıl ayarlanır](/guides/skills-test-timing-and-extra-time)
- [Yapay zekâ çağında mühendislerle mülakat](/guides/interviewing-in-the-age-of-ai)
- [AB'de yapay zekâ ile işe alım yasal mı?](/guides/is-ai-hiring-legal-in-the-eu)
- [Bir günde 100 başvuru nasıl elenir](/guides/screen-100-applicants-in-a-day)

## Kaynaklar

- Gartner, [Gartner survey shows just 26% of job applicants trust AI will fairly evaluate them](https://www.gartner.com/en/newsroom/press-releases/2025-07-31-gartner-survey-shows-just-26-percent-of-job-applicants-trust-ai-will-fairly-evaluate-them), 31 Temmuz 2025; rakamlar [Personnel Today](https://www.personneltoday.com/hr/by-2028-one-in-four-candidate-profiles-will-be-fake)'in aktardığı şekliyle.
- FBI Internet Crime Complaint Center, [Deepfakes and stolen PII utilized to apply for remote work positions](https://www.ic3.gov/PSA/2022/PSA220628), 28 Haziran 2022.
- Zhang, L., et al. (2015). Kaleido: You can watch it but cannot record it. *MobiCom 2015*. [PDF](https://old.sigmobile.org/mobicom/2015/papers/p372-zhangA.pdf)
- W3C, [Understanding Success Criterion 2.3.1: Three Flashes or Below Threshold](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), WCAG 2.2.
- van der Linden, W. J., & Guo, F. (2008). Bayesian procedures for identifying aberrant response-time patterns in adaptive testing. *Psychometrika, 73*(3), 365–384. [doi:10.1007/s11336-007-9046-8](https://doi.org/10.1007/s11336-007-9046-8)
- Meijer, R. R., & Sijtsma, K. (2001). Methodology review: Evaluating person fit. *Applied Psychological Measurement, 25*(2), 107–135. [doi:10.1177/01466210122031957](https://doi.org/10.1177/01466210122031957)
- Verschuere, B., et al. (2018). Registered replication report on Mazar, Amir, and Ariely (2008). *Advances in Methods and Practices in Psychological Science, 1*(3), 299–317. [doi:10.1177/2515245918781032](https://doi.org/10.1177/2515245918781032)
- Kristal, A. S., Whillans, A. V., Bazerman, M. H., Gino, F., Shu, L. L., Mazar, N., & Ariely, D. (2020). Signing at the beginning versus at the end does not decrease dishonesty. *PNAS, 117*(13), 7103–7107. [doi:10.1073/pnas.1911695117](https://doi.org/10.1073/pnas.1911695117)
- McCabe, D. L., Treviño, L. K., & Butterfield, K. D. (2001). Cheating in academic institutions: A decade of research. *Ethics & Behavior, 11*(3), 219–232. [doi:10.1207/S15327019EB1103_2](https://doi.org/10.1207/S15327019EB1103_2)
- Yoder-Himes, D. R., et al. (2022). Racial, skin tone, and sex disparities in automated proctoring software. *Frontiers in Education, 7*. [doi:10.3389/feduc.2022.881449](https://doi.org/10.3389/feduc.2022.881449)
- Garante per la protezione dei dati personali, [16 Eylül 2021 tarihli 317 sayılı karar](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9703988) (Università Bocconi).
- Regulation (EU) 2024/1689 (AI Act), [Madde 5](https://artificialintelligenceact.eu/article/5/); Avrupa Komisyonu, [Guidelines on prohibited AI practices](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act), 4 Şubat 2025.
- GDPR, [Madde 9](https://gdpr-info.eu/art-9-gdpr/) ve [Madde 22](https://gdpr-info.eu/art-22-gdpr/).
- Higher Ed Dive, [Test proctoring room scans violated college student's privacy, judge rules](https://www.highereddive.com/news/test-proctoring-room-scans-violated-college-students-privacy-judge-rules/630340/), Ağustos 2022 (Ogletree v. Cleveland State University, N.D. Ohio).
