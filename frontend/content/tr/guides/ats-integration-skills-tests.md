---
title: "Beceri testleri ATS'nize nasıl bağlanır"
seoTitle: "Beceri testlerini ATS'ye bağlamak: pratik bir rehber"
description: "Beceri testlerini ATS'niz üzerinden otomatik gönderin ve sonuçları alın, işe alım kararlarını insanlarda bırakın ve önce neyi kontrol edeceğinizi öğrenin."
updated: "2026-10-21"
---

# Beceri testleri ATS'nize nasıl bağlanır

Çoğu işe alım ekibi adayları bir aday takip sisteminde (ATS) tutar, beceri testlerini ise başka bir araçta yapar. İkisi arasında bağlantı yoksa biri ATS'den e-posta adreslerini kopyalar, davetleri elle gönderir, bekler, sonra puanları geri kopyalar. Beş adayda bu işler. Elli adayda davetler geç gider, sonuçlar kimsenin açmadığı ikinci bir sekmede kalır ve iyi adaylar beklerken başka teklifleri kabul eder.

Bu rehber, bir ATS ile bir test aracı arasındaki iyi bir bağlantının ne yaptığını, ona güvenmeden önce neyi kontrol etmeniz gerektiğini ve rutin işleri otomasyona bırakırken her işe alım kararını yine insanların vermesi için nasıl kuracağınızı anlatıyor.

## Neden bağlamalı

| Bağlantı olmadan | Bağlantıyla |
| --- | --- |
| Biri adayların e-posta adreslerini dışa aktarır veya kopyalar | Adayı bir aşamaya taşımak daveti gönderir |
| Davetler birinin vakti olduğunda gider | Davetler taşımadan birkaç dakika sonra gider |
| Sonuçlar test aracında durur | Sonuçlar ATS'de adayın kaydında görünür |
| İşe alım yöneticileri "Bunları test eden oldu mu?" diye sorar | ATS kimin test edildiğini ve nasıl sonuç aldığını gösterir |
| E-postalarda yazım hataları ve gözden kaçan adaylar | ATS, başvuranların tek listesidir |

Hız göründüğünden daha önemlidir. Başvuru ile geri dönüş arasındaki süre uzadıkça daha fazla aday süreçten çekilir ya da başka bir işe girer. Kesin kayıp oranları pozisyona ve piyasaya göre çok değişir, bu yüzden yayımlanan rakamlara temkinli yaklaşın; ama yön hep aynıdır: yavaş bir süreç insan kaybeder ve en güçlü adayların genellikle en çok seçeneği vardır.

## İyi bir akış neye benzer

Sağlam bir entegrasyon zaten kullandığınız aşamaları izler. Yeni bir süreç icat etmez.

1. **Aday başvurur** ve her zamanki gibi ATS'nize düşer.
2. **Bir kişi adayı test aşamasına taşır,** örneğin "Beceri testi". Tetikleyici bu taşımadır, yani kimin test edileceğine yine bir insan karar verir.
3. **Test aracı daveti otomatik olarak gönderir,** o ilana bağlı test için.
4. **Aday testi kendi uygun zamanında çözer,** belirlediğiniz son tarih içinde.
5. **Sonuçlar ATS'de adayın kaydına yazılır:** puan, geçip geçmediği, varsa dürüstlük uyarıları ve tüm cevapların bağlantısı.
6. **Bir kişi sonucu inceler** ve adayı bir sonraki aşamaya taşır ya da taşımaz.

İki şey bilerek elle kalır: kimin test edileceğini seçmek ve sonra ne olacağına karar vermek. Bağlantı yalnızca aradaki kopyalama işini ortadan kaldırır.

### Neden her yeni başvuruda tetiklemiyoruz?

Bazı araçlar başvuran herkesi davet eder. Her adayın aynı testi çözdüğü yüksek hacimli pozisyonlarda bu uygun olabilir. Ama adayları taşıdığınız bir aşama daha kolay kontrol edilir: kesin bir şartı açıkça karşılamayan başvuruları (çalışma izni yok, konum uygun değil) atlayabilirsiniz ve zaten reddedeceğiniz birini asla test etmez, onun için ödeme de yapmazsınız.

## Bir entegrasyon seçmeden önce neyi kontrol etmeli

Her "ATS'nizle entegre çalışır" iddiası aynı anlama gelmez. Herhangi bir şeyi bağlamadan önce şu soruları sorun.

| Soru | Neden önemli | İyi bir cevap |
| --- | --- | --- |
| Bağlantı nasıl kuruluyor? | Paylaşılan şifreler ve tedarikçide tutulan hesaplar denetlenmesi ve iptal edilmesi zor şeylerdir | Şirketinizin oluşturduğu ve istediği an silebileceği bir API anahtarı veya token |
| Anahtar neler yapabiliyor? | Tam erişimli bir anahtar sızarsa risk oluşturur | Entegrasyonun ihtiyaç duyduğu en dar yetkiler, dokümantasyonda listelenmiş olarak |
| Daveti ne tetikliyor? | Adaylara ne zaman e-posta gittiğini tam olarak bilmeniz gerekir | İlan bazında seçtiğiniz belirli bir aşama |
| Sonuçlar nereye düşüyor? | Kimsenin görmediği sonuçlar işe yaramaz | Adayın profiline, ekibinizin zaten okuduğu bir not veya yorum olarak |
| Bir davet başarısız olursa ne oluyor? | Kredi bitmesi, bir yazım hatası, duraklatılmış bir hesap: adaylar sessizce takılı kalır | Birine haber verilir ve aday yeniden davet edilebilir |
| Bir olay iki kez işlenebilir mi? | ATS'ler olayları yeniden gönderir; bir aday iki davet almamalı | Olay kaç kez gelirse gelsin her aday her test için bir kez davet edilir |
| Gelen olaylar nasıl doğrulanıyor? | Doğrulanmayan bir adrese sahte olaylar gönderilebilir | Aracın kontrol ettiği imzalı istekler |
| Aday verileri ne kadar süre saklanıyor? | GDPR gibi veri koruma yasaları net bir saklama süresi bekler | Belirtilmiş bir süre ve ilanı, testi veya hesabınızı sildiğinizde silinme |
| Maliyeti ne? | Kullanıcı başına planlar otomasyonu pahalı hale getirebilir | Test edilen aday başına öngörülebilir bir maliyet |

Tedarikçi başarısızlık ve tekrar eden olay sorularına net cevap veremiyorsa, cevabı acı tecrübeyle öğrenmeye hazır olun.

### Veri koruma

İki sistemi bağlamak, aday verilerinin, en azından isimlerin ve e-posta adreslerinin, iki şirket arasında aktarılması demektir. GDPR ve benzeri yasalara göre test tedarikçiniz genellikle veri işleyeninizdir; bu yüzden bir veri işleme sözleşmesine ihtiyacınız var ve adaylara, aydınlatma metninizde ya da davette, sürecin bir parçası olarak beceri testi yapıldığını bildirmelisiniz. Aktardığınız verileri testin ihtiyaç duyduğu en azla sınırlayın. Testlerin ve işe alımda yapay zekânın hukuki yönü hakkında daha fazlası için [AB'de yapay zekâ ile işe alım yasal mı?](/guides/is-ai-hiring-legal-in-the-eu) yazısına bakın.

## Kurulum kontrol listesi

Gerçek bir pozisyon için açmadan önce:

1. **ATS'nizde yalnızca test için bir aşama oluşturun,** örneğin "Beceri testi". Başka bir anlamı olan bir aşamayı yeniden kullanmayın, yoksa adaylar yanlışlıkla davet edilir.
2. **Anahtarı bir yönetici hesabından oluşturun;** bu hesap bağlamak istediğiniz tüm ilanları görebilmeli ve yalnızca dokümantasyonda listelenen yetkilere sahip olmalı.
3. **Her ilanı kendi testine bağlayın** ve daveti tetikleyen aşamayı seçin.
4. **ATS'niz elle yapmanızı istiyorsa webhook'u kurun** ve gizli anahtarını aracın istediği yere yapıştırın.
5. **Kendinizle deneyin.** Kendi e-posta adresinizle bir aday ekleyin, onu aşamaya taşıyın, testi çözün ve notun ATS'de göründüğünü kontrol edin.
6. **Başarısızlıkları kimin takip edeceğine karar verin:** bir davet gönderilemediğinde kime haber verileceğine ve bunu kimin düzelteceğine.
7. **Sonuçların nasıl okunacağında anlaşın.** Geçme notu bir rehberdir, otomatik bir ret değildir. Buna sonuçlar gelmeden önce karar verin, sonra değil.

## Sık yapılan hatalar

- **Evrak işini değil kararı otomatikleştirmek.** Belirli bir puanın altındaki herkesi otomatik reddetmek, kötü bir soruyu ya da bağlantı sorunu yaşayan bir adayı yakalayan insan kontrolünü ortadan kaldırır. Puan sıralasın, karar insanın olsun.
- **Yanlış aşamadan tetiklemek.** İşe alım uzmanlarının başka amaçlarla kullandığı bir aşama, test almaması gereken kişilere test gönderir.
- **Her ilan için tek bir test.** Bağlantı aynı testi her yere göndermeyi kolaylaştırır. Bir test en çok, söz konusu pozisyon için hazırlandığında işe yarar. Bkz. [Beceri testleri ve CV taraması](/guides/skills-tests-vs-cv-screening).
- **Başarısızlıkları kimsenin izlememesi.** Bir davet sessizce başarısız olursa aday hiç gelmeyecek bir e-postayı bekler, siz de onu görmezden geldiğini sanırsınız.
- **Ayrılacak birine bağlı bir anahtar.** Bazı ATS anahtarları onları oluşturan kişi adına çalışır. O kişinin hesabı kapatıldığında bağlantı durur. Kalıcı bir hesap kullanın ve kişilerin rolleri değiştiğinde yeniden bağlayın.
- **ATS dışındaki adayları unutmak.** ATS'ye hiç girmeyen referanslı adaylar ve doğrudan başvuranlar da davete ihtiyaç duyar. Onları davet etmek için elle bir yol da tutun.

## prepza bunu nasıl yapıyor

prepza **Workable, Greenhouse, Teamtailor, Recruitee ve Breezy HR**'a bağlanır ve yukarıdaki akışı izler.

- **Anahtar sizin, kontrol sizde.** Bir sahip veya yönetici, şirketinizin ATS'de oluşturduğu bir anahtarla ATS'yi şirketin Entegrasyonlar sekmesinden bağlar. prepza anahtarı kaydetmeden önce kontrol eder, şifreli saklar ve bir daha asla göstermez. Bağlantıyı kesmek anahtarı ve bağlı ilanları anında siler.
- **Bir ilanı bir mülakata bağlayın.** Bir ATS ilanını ve daveti tetikleyen aşamayı seçin, ardından onu prepza'daki mevcut bir mülakata bağlayın ya da ATS'deki ilan metninden yeni bir mülakat oluşturun. Tek bir soru yazılmadan önce konuları siz incelersiniz.
- **Adayı taşıyın, davet gitsin.** ATS aynı olayı iki kez gönderse bile her aday her mülakat için bir kez davet edilir.
- **Sonuçlar ATS'ye geri döner.** Aday bitirdiğinde prepza, ATS'de adaya notunu, geçip geçmediğini, varsa dürüstlük uyarılarını (sayfadan ayrılma, kopyalama girişimleri, soruyu okumaya yetmeyecek kadar hızlı seçilen cevaplar) ve tüm cevapları içeren değerlendirme kartının bağlantısını içeren bir not veya yorum ekler.
- **Başarısızlıklar gözden kaçmaz.** Bir aday davet edilemezse, örneğin şirketin kredisi bittiği, e-posta sınırına ulaştığı veya prepza davetleri duraklattığı için, şirketin tüm üyeleri ATS'nin adını belirten bir bildirim alır. Kredi yetersizliği yüzünden davet edilemeyen adaylar kredi yüklendikten sonra otomatik olarak davet edilir ve herhangi bir ilanın bekleyen adayları tek tıkla yeniden davet edilebilir.
- **Kullanıyorsanız Slack.** prepza, testi bitiren bir aday ya da davet edilemeyen bir ATS adayı gibi bildirimleri seçtiğiniz bir Slack kanalına gönderebilir.
- **Kendi platformunuz.** ATS'niz listede yoksa prepza'nın [API](/api-docs)'si, bir API anahtarıyla aday davet etmenize ve bir aday başladığında, bitirdiğinde, daveti kendisine ulaşamadığında, davetinin süresi dolduğunda veya kaldırıldığında ve bir mülakat hazır olduğunda imzalı bir webhook almanıza olanak tanır.
- **Veriler belirli bir süre saklanır.** Bir ATS'den kaydedilen adaylar 365 gün sonra ya da daha önce, mülakatları veya şirketleriyle birlikte silinir.

Bazı ATS'ler kendi tarafında bir adım gerektirir. Greenhouse, Teamtailor ve Recruitee webhook'u elle eklemenizi ister; prepza'nın Talimatlar penceresi adresi ve gizli anahtarın nereye yapıştırılacağını gösterir. Workable ve Breezy HR'ın webhook'larını prepza kendisi kurar.

Fiyatlandırma aday başınadır ve abonelik yoktur: yalnızca en az bir soruyu yanıtlayan adaylar için ödeme yaparsınız; $50'lık yüklemede aday başına $5, $200'lık yüklemeden itibaren $4, $600'lık yüklemeden itibaren $3 ve $1.000'lık yüklemeden itibaren $2. Fiyatlar burada ABD doları, Kanada, Avustralya, İsrail, Polonya, İsviçre, Japonya, Güney Kore, Tayvan, Hong Kong, Tayland, Singapur, Hindistan, Avrupa'nın geri kalanı ve Birleşik Krallık'ta ise yerel para birimi cinsindendir; KDV veya satış vergisi ödeme adımında hesaplanır. ATS bağlamak ve mülakat oluşturmak ücretsizdir ve ilk şirketinizin ilk 3 adayı ücretsizdir. Bkz. [fiyatlar](/pricing).

## İlgili yazılar

- [Bir günde 100 başvuru nasıl elenir](/guides/screen-100-applicants-in-a-day)
- [Beceri testleri ve CV taraması](/guides/skills-tests-vs-cv-screening)
- [İşe alım öncesi testler: pratik bir rehber](/pre-employment-testing)
