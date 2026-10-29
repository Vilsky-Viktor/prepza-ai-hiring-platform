---
title: "Yapay zekâ çağında mühendislerle mülakat: artık neyi test etmeli"
seoTitle: "Yapay Zekâ Çağında Teknik Mülakat: Artık Neyi Test Etmeli"
description: "Yapay zekâ asistanları günlük yazılım işinin parçası. Bu, mülakatta neyin test edileceğini nasıl değiştiriyor, bilgi testleri nerede devreye giriyor."
updated: "2026-10-29"
---

# Yapay zekâ çağında mühendislerle mülakat: artık neyi test etmeli

Yıllarca klasik teknik mülakat, adaydan sıfırdan kod yazmasını istedi: bir listeyi tersine çevirmek, bir önbellek uygulamak, beyaz tahtada veya ortak bir editörde bir bulmaca çözmek. Fikir basitti. Biri kodu yazabiliyorsa, muhtemelen işi de yapabilir.

Yapay zekâ kodlama asistanları bu bağı zayıflattı. Pek çok rutin kod parçası artık bir asistan tarafından saniyeler içinde taslak olarak yazılabiliyor; hem işte hem de, siz engellemedikçe, uzaktan yapılan bir mülakat sırasında. Bu, mühendislik becerisini daha az önemli kılmıyor. Hangi becerilerin en önemli olduğunu ve dolayısıyla bir mülakatın neyi kontrol etmesi gerektiğini değiştiriyor.

Bu rehber neyin değiştiğini, bazı şirketlerin nasıl uyum sağladığını ve işi kimin yapabileceğini hâlâ gösteren bir mülakat sürecinin nasıl tasarlanacağını ele alıyor. İşe alım yöneticileri ve mühendislik liderleri için yazıldı.

## Ne değişti

Yapay zekâ asistanları artık birçok geliştiricinin günlük işinin parçası. 2025 Stack Overflow Geliştirici Anketi'nde katılımcıların %84'ü geliştirme süreçlerinde yapay zekâ araçlarını kullandığını veya kullanmayı planladığını, profesyonel geliştiricilerin %51'i ise bunları her gün kullandığını söyledi ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)). GitHub'ın Octoverse 2025 raporu, GitHub'daki yeni geliştiricilerin %80'inin ilk haftalarında Copilot kullandığını belirtiyor ([GitHub, Ekim 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)).

Aynı anket sınırları da gösteriyor. Yapay zekâ çıktısının doğruluğuna güvenmeyen katılımcılar (yaklaşık %46), güvenenlerden (yaklaşık %33) daha fazlaydı. %66'nın dile getirdiği en yaygın şikâyet “neredeyse doğru ama tam olarak doğru olmayan yapay zekâ çözümleri” idi ve %45'i yapay zekânın ürettiği kodda hata ayıklamanın daha fazla zaman aldığını söyledi ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)).

Bir araya getirildiğinde bu rakamlar işin kendisindeki bir kaymayı tarif ediyor. Kodun ilk taslağını üretmek ucuzluyor. O taslağın doğru olup olmadığını değerlendirmek ve değilse düzeltmek, becerinin büyük kısmının artık yattığı yer.

## Şirketler nasıl uyum sağlıyor

Henüz sektör genelinde tek bir yanıt yok. Bildirilen yaklaşımlar farklı yönlere gidiyor:

- **Mülakatta yapay zekâya izin vermek veya bunu şart koşmak.** Haziran 2025'te Canva, backend, makine öğrenimi ve frontend adaylarından artık yeni bir “Yapay Zekâ Destekli Kodlama” (AI-Assisted Coding) turunda Copilot, Cursor ve Claude gibi yapay zekâ araçlarını kullanmalarını beklediğini açıkladı. Adayların “karmaşık, belirsiz gereksinimleri parçalara ayırıp ayıramadığını”, “yapay zekânın ürettiği koddaki sorunları bulup düzeltip düzeltemediğini” ve “yapay zekânın ürettiği çözümlerin üretim standartlarını karşılamasını sağlayıp sağlayamadığını” değerlendiriyor ([Canva Engineering, Haziran 2025](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews)).
- **Yapay zekâ destekli kodlama turlarını denemek.** Temmuz 2025'te Business Today, 404 Media'ya dayanarak Meta'nın adayların bir yapay zekâ asistanına sahip olduğu bir kodlama mülakatı geliştirdiğini bildirdi. Meta'nın bunun “gelecekteki çalışanlarımızın çalışacağı geliştirici ortamını daha iyi temsil ettiğini ve ayrıca LLM tabanlı kopya çekmeyi daha az etkili hâle getirdiğini” söylediğini aktardı ([Business Today, Temmuz 2025](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31)).
- **Araçları kısıtlamak ve yüz yüze görüşmek.** Mart 2025'te CNBC, adayların uzaktan kodlama mülakatlarında yapay zekâyı fark edilmeden kullanmalarına yardımcı olmak için geliştirilmiş bir aracı haberleştirdi. Aynı haberde Amazon, adayların yetkisiz araçlar kullanmayacaklarını kabul etmeleri gerektiğini söyledi; Google'ın CEO'su işe alım yöneticilerinin bazı yüz yüze mülakatları değerlendirmesini önerdi; Deloitte ise Birleşik Krallık'taki yeni mezun programı için yüz yüze mülakatlara geri dönmüştü ([CNBC, NBC New York aracılığıyla, Mart 2025](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1)).

Bunlar piyasaya ilişkin bir anket değil, birkaç büyük şirketin örneği ve politikalar değişiyor. Ama aynı yönü gösteriyorlar: uzaktan verilen “bunu sıfırdan yaz” görevine güvenmek artık daha zor ve ilginç soru “kod üretebiliyor musun?” sorusundan “onu değerlendirecek kadar iyi anlıyor musun?” sorusuna kaydı.

## Bilgi neden erken bir filtre olarak daha önemli

Kodu bir asistan taslak olarak yazabiliyorsa, güçlü bir mühendisi zayıf olandan ne ayırır? Çoğunlukla bir asistanın onun yerine sağlayamayacağı şeyler:

- **Kavramlar ve teori.** Bir veritabanının indeksi nasıl kullandığını, bir yarış durumunun (race condition) neden oluştuğunu veya bir framework'ün her istekte ne yaptığını bilmek, bir mühendisin üretilen kodun yanlış olduğunu görmesini sağlar.
- **Kod okuma.** Yapay zekâ çıktısını kullanmadan önce birinin onu okuması ve neyi yazdıracağını, döndüreceğini veya değiştireceğini bilmesi gerekir.
- **Hata ayıklama.** “Neredeyse doğru” kod hata verdiğinde, çözüm nedenini anlamaktan gelir.
- **Muhakeme.** Çalışan iki yaklaşım arasında seçim yapmak, ödünleşimleri bilmeyi gerektirir: performans, güvenlik, sürdürülebilirlik.

Bunlar bilgi ve muhakeme becerileridir ve doğrudan, hızlıca test edilebilirler. İşe alım araştırmaları mesleki bilgi testlerini zaten ortalamada iş performansının daha iyi yordayıcıları arasında sıralıyor: onlarca yıllık çalışmaların 2022'deki bir yeniden analizinde Sackett, Zhang, Berry ve Lievens, mesleki bilgi testleri için .40'lık bir geçerlik tahmin etti; bu, .42 ile yapılandırılmış mülakatlara yakın ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Bu araştırma yapay zekâ asistanlarından önceye ait, dolayısıyla yapay zekâ çağındaki iş hakkında bir şey kanıtlamıyor. Ancak işe özgü bir bilgi testinin erken bir filtre olarak kullanılmasını destekliyor ve yukarıda anlatılan kayma, ölçtüğü bilgiyi iş için daha az değil, daha merkezi hâle getiriyor.

## Uygulamalı alıştırmaların hâlâ bir yeri var

Bunların hiçbiri kodlama alıştırmalarını işe yaramaz kılmıyor. Ne zaman uygulandıklarını ve nasıl göründüklerini değiştiriyor:

- **Yapay zekâ ile eşli çalışma.** Canva'nın turunda olduğu gibi adaylara bir asistan ve gerçekçi, açık uçlu bir görev verin. Görevi nasıl parçaladıklarını, asistana ne sorduklarını ve neyi kabul edip neyi reddettiklerini izleyin.
- **Kod incelemesi.** Belki yapay zekâ tarafından yazılmış, birkaç gerçek hata içeren bir pull request verin. Neyi neden değiştireceklerini sorun.
- **Hata ayıklama.** Başarısız bir testi olan küçük bir kod tabanı verin. Bu, anketin tarif ettiği günlük işe yakındır ve taklit edilmesi zordur.
- **Sistem tasarımı.** Kıdemli pozisyonlar için ödünleşimler üzerine bir tartışma, tek bir prompt'un üretemeyeceği muhakemeyi gösterir.

Bu alıştırmaları yürütmek ve puanlamak bir mühendisin zamanını alır. Önlerine hızlı ve kapsamlı bir bilgi kontrolü koymanın asıl nedeni budur; böylece başarılı olma olasılığı en yüksek adaylara ayrılırlar.

## Yapay zekâ çağı için bir süreç

1. **Başvuruları yalnızca kesin gerekliliklere göre eleyin:** çalışma hakkı, konum, olmazsa olmaz deneyim.
2. **Teknoloji yığınınız için kavramlar, teori ve kod okuma üzerine kısa bir bilgi elemesi yapın.**
3. **Ekibinizin çalışma şekline uyan bir biçimde uygulamalı bir alıştırma yapın:** yapay zekâ destekli eşli çalışma, kod incelemesi veya hata ayıklama; uzaktan ya da yüz yüze.
4. **Kıdemli pozisyonlar için sistem tasarımı ekleyin.**
5. **Belirlenmiş sorular ve bir puanlama ölçütüyle yapılandırılmış bir mülakat yapın;** adayın yapay zekâ araçlarını nasıl kullandığı ve çıktılarını nasıl kontrol ettiği de dahil.
6. **Kararı insanlar versin;** her sonuç girdilerden yalnızca biri olsun.

Adaylara her aşamada hangi araçlara izin verildiğini baştan söyleyin. Net bir kural, tahmin oyunundan daha adildir ve sonuçları karşılaştırmayı kolaylaştırır.

Adım adım eksiksiz sürüm için [Mühendis işe alımı nasıl yapılır](/guides/hiring-engineers) rehberine bakın.

## prepza nerede devreye girer

prepza 2. adım için çok uygundur. İş tanımınızı süreli, çoktan seçmeli bir bilgi mülakatına dönüştürür ve herhangi bir soru yazılmadan önce önerilen konuları gözden geçirirsiniz; böylece test teknoloji yığınınızı kapsar, başka hiçbir şeyi değil.

- **İş tanımından kavramlar ve teori:** veritabanları, API'ler, mimari, bir framework'ün davranışı, güvenlik uygulamaları.
- **Kod okuma soruları:** kısa bir kod parçası ve bunun ne yazdırdığı veya döndürdüğü, ne yaptığı, neden hata verdiği ya da hangi değişikliğin sorunu düzelttiği üzerine sorular. Bu, yapay zekâ destekli işin dayandığı inceleme becerisinin ta kendisidir.
- **Her soruda bir zamanlayıcı:** her sorunun sunucu tarafından uygulanan kendi geri sayımı vardır ve her aday kendine ait rastgele bir soru seti alır. Bu, yanıtları araştırmayı, bir yapay zekâ asistanına sormak da dahil, zorlaştırır. İmkânsız kılmaz.
- **Güvenilirlik sinyalleri:** değerlendirme kartları, soruyu okumaya yetmeyecek kadar hızlı verilen yanıtları, adayın sayfadan ayrıldığı anları ve kopyalama girişimlerini işaretler. Aday bitirdiğinde raporu, soruları bir yapay zekâya aktarıp onun yanıtlarını kopyalamanın genellikle bıraktığı yanıt örüntülerini de gösterir: uzunluğu ya da zorluğu ne olursa olsun her soruda yaklaşık aynı süre veya kolay sorular yanlışken zor soruların doğru olması. İşaret ya da örüntü, daha yakından bakmak için bir nedendir, kopya çekildiğinin kanıtı değildir.
- **Canlı mülakat için sorular:** rapor, adayın en güçlü konularından doğru yanıtladığı en fazla 3 soruyu, hiçbir yapay zekânın onun yerine yanıt veremeyeceği canlı bir mülakatta konuşmak için önerir.

prepza'nın yapmadıkları: adaylar prepza'da kod yazmaz, çalıştırmaz veya hata ayıklamaz ve prepza onların bir yapay zekâ asistanını kullanmasını izlemez. Bunun yeri, şirket içinde veya bir geliştirici platformunda yürütülen ve bilgi elemesini tamamlayan uygulamalı aşamadır. Başlangıç için hazır testler için [pozisyona göre beceri testleri](/tests) sayfasına, prepza'nın yapay zekâyı nasıl kullandığı ve neyi insanlara bıraktığı için [Yapay zekâ mülakatları](/ai-interviews) sayfasına bakın.

## Adillik ve aday deneyimi

Sürecinizi değiştirmek, adil olup olmadığını kontrol etmek için iyi bir fırsattır:

- **Yapay zekâ kurallarını** her aşamada yazılı olarak **net belirtin.**
- **Belirli bir aşamada koşulları herkes için aynı tutun.**
- **İsteyen adaylara ek süre gibi makul düzenlemeler sunun.**
- **Bir sinyali hüküm gibi görmeyin.** Duraksamanın, başka yere bakmanın veya hızlı yanıt vermenin masum nedenleri olabilir.
- **Kısa tutun.** Eklediğiniz her aşama, güçlü adaylara başka bir teklife ayırabilecekleri zamana mal olur.

## Özet

Yapay zekâ asistanları kod üretmeyi ucuzlattı, kodu değerlendirmeyi ise daha önemli hâle getirdi. İyi bir süreç bunu yansıtır: bilgiyi, teoriyi ve kod okumayı erken aşamada, hızlı olduğu ve her soruda zamanlayıcı olduğunda dışarıya yaptırmanın daha zor olduğu yerde test edin; ardından adayların nasıl çalıştığını görmek için çoğu zaman yapay zekâya izin verilen uygulamalı alıştırmalar kullanın. Kurallar konusunda net olun ve kararı insanlara bırakın.

## Kaynaklar

- Stack Overflow, [2025 Developer Survey: AI](https://survey.stackoverflow.co/2025/ai).
- GitHub, [Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), 28 Ekim 2025.
- Canva Engineering, [Yes, you can use AI in our interviews](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews), 11 Haziran 2025.
- Business Today, [Meta to test job applicants with AI-assisted coding interviews](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31), 31 Temmuz 2025, 404 Media'ya dayanarak.
- CNBC, NBC New York aracılığıyla, [Meet the 21-year-old helping coders use AI to cheat in Google and other tech job interviews](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1), 9 Mart 2025.
- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## İlgili yazılar

- [Mühendis işe alımı nasıl yapılır](/guides/hiring-engineers)
- [Pozisyona göre beceri testleri](/tests)
- [Online değerlendirmelerde kopya ve buna karşı işe yarayanlar](/guides/cheating-in-online-assessments)
- [Yapay zekâ mülakatları: nedir ve adil şekilde nasıl kullanılır](/ai-interviews)
- [Beceri testleri ve CV taraması](/guides/skills-tests-vs-cv-screening)
