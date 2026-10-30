---
title: "Yapay zekâ ajanları, MCP ve API'ler: nedir ve işe alımda nasıl kullanılır"
seoTitle: "İşe Alımda Yapay Zekâ Ajanları, MCP ve API'ler"
description: "Yapay zekâ ajanı, MCP, API nedir, işe alımda güvenle nasıl kullanılır, prepza yapay zekâ asistanıyla, Claude, ChatGPT veya platformunuzla nasıl yönetilir."
updated: "2026-10-22"
---

# Yapay zekâ ajanları, MCP ve API'ler: nedir ve işe alımda nasıl kullanılır

Çoğu kişi yapay zekâyla ilk kez bir sohbet penceresinde tanıştı: siz sorarsınız, o yanıtlar. Bir yapay zekâ ajanı (AI agent) bir adım öteye gider. Araçlarınızda bilgi arayabilir ve siz istediğinizde onlarda işlem yapabilir: bir mülakat oluşturmak, bir aday listesini davet etmek, geçen hafta en yüksek puanı kimin aldığını söylemek gibi. Model Context Protocol (MCP), zaten kullandığınız Claude veya ChatGPT gibi yapay zekâ sohbetinin bu tür araçlara bağlanmasını sağlayan standarttır. API ise yazılımların arada yapay zekâ olmadan birbiriyle konuşmasının daha eski ve daha kesin yoludur.

Bu rehber üçünü de sade bir dille, işe alımda ne işe yaradıklarını, nelere dikkat etmeniz gerektiğini ve prepza ile nasıl kullanacağınızı anlatıyor.

## Yapay zekâ ajanı nedir

Bir sohbet botu yalnızca metin yazar. Ajan ise **araçlara** sahip bir dil modelidir: "bu mülakatın adaylarını listele" veya "bu e-posta adresini davet et" gibi, çağırabileceği küçük ve net tanımlı işlemler. Bir şey sorduğunuzda ajan hangi araçları kullanacağına karar verir, onların döndürdüğünü okur ve yanıtını hafızasına göre değil, buna göre verir.

| Sohbet botu | Yapay zekâ ajanı |
| --- | --- |
| Eğitimde öğrendiklerine göre yanıtlar | Araçlarla okunan güncel verilerinize göre yanıtlar |
| Bir şeyin nasıl yapılacağını yalnızca anlatabilir | Siz isteyip izin verdiğinizde onu yapabilir |
| Bilmediğinde tahmin yürütür | Bakar ya da yapamayacağını söyler |
| Tek bir pencerede yaşar | Bağladığınız araçların içinde çalışır |

Bir ajanı işe yarar kılan araçlardır; güvenli olup olmadığını belirleyen de yine onlardır. İyi bir ajan yalnızca kendisine verilen araçları, yalnızca sizin yetkilerinizle kullanabilir ve yalnızca sizin istediğinizi yapar.

## MCP nedir

Model Context Protocol, Anthropic'in 2024'ün sonunda tanıttığı ve bugün Claude, ChatGPT ve birçok başka yapay zekâ uygulaması ile geliştirici aracının desteklediği açık bir standarttır. Sık sık yapay zekâ için bir USB-C girişine benzetilir: her yapay zekâ uygulamasının her araca kendi bağlantısını kurması yerine araç tek bir **MCP sunucusu** sunar ve MCP destekleyen her yapay zekâ uygulaması onu kullanabilir.

Bir MCP sunucusu yapay zekâ uygulamasına üç şey söyler:

1. **Hangi araçların olduğunu;** her birinin adı, açıklaması ve ihtiyaç duyduğu bilgilerle.
2. **Hangi araçların yalnızca okuduğunu** ve hangilerinin bir şeyi değiştirdiğini; böylece yapay zekâ uygulaması bir değişiklikten önce size sorabilir.
3. **Kim olduğunuzu;** bir kez onayladığınız bir girişle, böylece her çağrı sizin adınıza ve sizin yetkilerinizle çalışır.

Sizin için bu, verileri pencereler arasında kopyalamadan, zaten kullandığınız sohbetten bir araçla çalışabilmeniz demektir.

## API nedir ve farkı ne

API (uygulama programlama arayüzü), bir programın başka bir programa gönderebileceği sabit isteklerden oluşan bir kümedir: "bu mülakatın adaylarını listele", "bu e-posta adresini davet et". Geliştiricileriniz bu istekleri gönderen kodu yazar. Arada yapay zekâ yoktur: aynı istek her zaman aynı şeyi yapar ve kendi kendine çalışan otomasyon için tam da istediğiniz budur.

| | Mira, yapay zekâ asistanı (uygulamada) | MCP (Claude veya ChatGPT'de) | API |
| --- | --- | --- | --- |
| Kim kullanır | Siz, prepza'da | Siz, yapay zekâ sohbetinizde | Platformunuzun kodu |
| Nasıl istersiniz | Kendi sözlerinizle | Kendi sözlerinizle | Bir geliştiricinin yazdığı sabit isteklerle |
| Değişiklikleri kim onaylar | Siz, bir kartta | Siz, yapay zekâ uygulamanızda | Kodunuz, yazıldığı şekilde |
| En uygun olduğu iş | Hızlı sorular ve görevler | prepza'yı diğer araçlarınız ve dosyalarınızla birlikte kullanmak | Kimse izlemeden çalışan otomasyon |
| Kimin adına giriş yapar | Siz | Siz | Bir şirket anahtarı |

Süreçte bir insan varsa Mira'yı veya MCP'yi kullanın. Kendi sisteminizin adayları kendiliğinden davet etmesi ve sonuçları toplaması gerekiyorsa, örneğin bir kariyer sitesinden veya şirket içi bir İK aracından, API'yi kullanın.

## İşe alımda ne işe yarar

İşe alımda farklı araçlara dağılmış çok sayıda küçük, tekrarlayan adım vardır. Yapay zekâ ajanı tam olarak bunlarda iyidir:

- **Süreçle ilgili sorular.** "Senior Backend için bu hafta hangi adaylar geçti?", "Mülakatına henüz başlamayan kim var?", "Veri analisti pozisyonunda ortalama notumuz ne?"
- **Kurulum.** "Bu iş tanımından bir mülakat oluştur", "Geçme notunu %70 yap", "Bu adaya %50 ek süre ver."
- **Toplu işler.** "Bu 12 kişiyi Frontend mülakatına davet et"; liste doğrudan bir e-postadan veya tablodan yapıştırılarak.
- **Kaynakları birleştirmek.** Claude veya ChatGPT'de prepza'yı bağlı diğer araçlarınız ve dosyalarınızla birlikte kullanabilirsiniz: belgelerinizdeki bir iş tanımını mülakatın konularıyla karşılaştırabilir ya da kısa listedeki adaylara bir mesaj taslağı hazırlayabilirsiniz.

Yapmaması gereken şey ise işe alım kararını vermektir. Not, bir insanın değerlendirmesini destekler, onun yerini almaz. Ajandan sıralamasını, özetlemesini ve hazırlamasını isteyin, kararı bir insana bırakın. Bunun hukuken neden de önemli olduğu için [AB'de yapay zekâ ile işe alım yasal mı?](/guides/is-ai-hiring-legal-in-the-eu) yazısına bakın.

## Nelere dikkat etmeli

Bir yapay zekâyı işe alım verilerinize bağlamak, bir iş arkadaşınıza erişim vermek kadar özen ister.

| Risk | Ne işe yarar |
| --- | --- |
| Ajan kastetmediğiniz bir şey yapar | Değişiklikler önce sizin onayınızı gerektirir ve yalnızca istediğinizi yapar |
| Görmesi gerekenden fazlasını görür | Sizin adınıza çalışır: sizin gördüğünüzü görür, fazlasını değil |
| Verilerin içine gizlenmiş talimatlar | Adayların adları, cevapları ve belgeleri veridir, asla uyulacak talimat değildir |
| Gizli bilgiler sohbete düşer | API anahtarları ve şifreler asla sohbetten geçmez |
| Geri alınamaz hatalar | Bir hesabı veya şirketi silmek uygulamada, kendi onay adımının arkasında kalır |
| Veriler araçlarınızın dışına çıkar | Veriler bağladığınız yapay zekâ uygulamasına, o uygulamanın koşullarıyla ulaşır: yalnızca şirketinizin izin verdiği uygulamaları bağlayın |
| Kontrolden çıkan kullanım | Saatte kaç işlem yapılabileceğine dair sınırlar |

Herhangi bir yapay zekâ uygulamasını iş verilerine bağlamadan önce şirketinizin yapay zekâ araçlarıyla ilgili politikasını kontrol edin ve aydınlatma metninizde adaylara verilerini hangi hizmetlerin işlediğini bildirin.

## prepza ile sayfalarının ötesinde çalışmanın üç yolu

### 1. Mira, yerleşik yapay zekâ asistanı

Herhangi bir sayfanın üst kısmında **Mira'ya sor**'u seçin. prepza'nın yapay zekâ asistanı Mira, şirketlerinizi, mülakatlarınızı, adaylarınızı, kredilerinizi ve entegrasyonlarınızı, ayrıca prepza'nın nasıl çalıştığını bilir. Sizin dilinizde yanıt verir; yazarak veya konuşarak sorabilirsiniz.

- **Verilerinize göre yanıtlar,** sizinle aynı görünümle: bir yönetici bir yöneticinin gördüğünü, bir görüntüleyici bir görüntüleyicinin gördüğünü görür.
- **Hangi sayfada olduğunuzu bilir.** O sayfanın rehberi için "Bu sayfada neler yapabilirim?" diye sorun ya da bir mülakatın adaylarındayken "Burada en iyisi kim?" diye sorun; hangisi olduğunu sormadan o mülakat hakkında yanıt verir.
- **Değişiklikleri o hazırlar, siz onaylarsınız.** Aday davet etmesini istediğinizde, ne olacağını tam olarak gösteren bir kart sunar; örneğin "Backend geliştirici mülakatına 12 aday davet et". Siz Onayla'yı seçene kadar hiçbir şey çalışmaz.
- **Kaynaklarını gösterir.** Bir yanıtın altında kullandığı adayları veya mülakatları ve geldikleri sayfanın bağlantısını görürsünüz.
- **Konunun dışına çıkmaz.** prepza ve onunla işe alım hakkında yanıt verir, gerisini reddeder.

### 2. MCP ile Claude veya ChatGPT'de prepza

Ekibiniz zaten Claude veya ChatGPT'de çalışıyorsa prepza'yı oraya taşıyabilirsiniz. prepza'nın MCP sunucusu, yerleşik asistan Mira ile aynı araçları sunar.

**Bağlamak için:**

1. prepza'da bir şirketin **Entegrasyonlar** sekmesini açın ve **Yapay zekâ uygulamaları**'nı seçin. Sunucu adresini kopyalayın: `https://prepza.ai/mcp`.
2. **Claude'da:** Ayarlar'ı, ardından Bağlayıcılar'ı açın ve bu adresle özel bir bağlayıcı ekleyin. **Claude Code'da:** `claude mcp add --transport http prepza https://prepza.ai/mcp` komutunu çalıştırın. **ChatGPT'de:** uygulama ve bağlayıcı ayarlarında özel bir bağlayıcı olarak ekleyin.
3. Yapay zekâ uygulamanız prepza'nın giriş sayfasını açar. Giriş yapın, hangi uygulamanın izin istediğini kontrol edin ve **İzin ver**'i seçin. Yalnızca okuyabilmesi için önce **Değişikliklere izin ver** seçeneğini kapatın.

Bundan sonra sohbetinizde bir iş arkadaşınıza sorar gibi sorun: "prepza'da Ürün tasarımcısı için en iyi üç aday kim?" Çoğu yapay zekâ uygulaması bir değişiklikten önce size sorar ve geri alınamayacak her şeyden önce uyarır: prepza onlara hangi işlemlerin bir şeyi değiştirdiğini veya sildiğini bildirir.

**Uygulamadakiyle aynı kalanlar:**

- **Yetkileriniz.** Bağlantı, üyesi olduğunuz her şirkette, her birindeki rolünüzle sizin adınıza çalışır.
- **Krediler ve sınırlar.** Bir adayı davet etmek uygulamadakiyle aynı tutardadır ve aynı e-posta sınırları geçerlidir.
- **Kayıt.** Bir yapay zekâ uygulamasının sizin için yaptığı her şey, konuları onaylamaktan sonuçları görüntülemeye, ek süre vermekten bir adayı iptal etmeye kadar, şirketin işlem kaydında bir yapay zekâ uygulaması üzerinden yapılmış olarak görünür. Şirketin sahibi bunu şirketin **İşlem kaydı** sekmesinde okur.
- **Karar şirketin.** Sahipler ve yöneticiler, şirketin yapay zekâ uygulamaları sayfasındaki **Bu şirkette yapay zekâ uygulamalarına izin ver** ile bu uygulamaların şirket verilerini kullanmasını durdurabilir.
- **Yapamadıkları.** Şifrenizi veya API anahtarlarınızı göremez, hesabınızı veya bir şirketi silemez. Bunlar uygulamada kalır.

**Bağlantıyı kaldırmak için** yapay zekâ uygulamanızda bağlayıcıyı silin ya da Entegrasyonlar sekmesindeki **Yapay zekâ uygulamaları** altında yanındaki **Bağlantıyı kes**'i seçin. Hemen çalışmayı bırakır.

**Diğer uygulamalar ve kendi ajanlarınız.** Geliştirici belgelerindeki [MCP sekmesi](/api-docs?tab=mcp), Gemini CLI, Cursor, VS Code ve Le Chat için adımları ve Python ile TypeScript'te eksiksiz örnek ajanları içerir. Bir sunucuda çalışan ve oturum açmayı onaylayacak kimsenin olmadığı bir ajan, **Yapay zekâ ajanlarıyla kullanma (MCP)** yetkisine sahip bir şirket API anahtarı kullanır: yalnızca o şirkette ve yalnızca anahtarın diğer yetkilerinin izin verdiği araçlarla çalışır. Yaptığı her şey şirketin işlem kaydında anahtarın adıyla görünür.

### 3. API ile kendi platformunuz

Yapay zekâ olmadan otomasyon için prepza'nın [geliştirici belgelerinde](/api-docs) açıklanan bir API'si vardır.

1. Bir sahip veya yönetici, bir şirketin **Entegrasyonlar** sekmesini, ardından **API**'yi açar ve **Yeni anahtar**'ı seçer. Anahtara onu kullanacak platformun adını verin, ne zaman sona ereceğini seçin ve yalnızca ihtiyaç duyduklarını işaretleyin: bir panonun anahtarı yalnızca okur, bir kariyer sitesinin anahtarı davet de eder. Yetkileri daha sonra ekleyebilir veya kaldırabilirsiniz. Anahtar yalnızca bir kez gösterilir; güvenli bir yerde saklayın.
2. Platformunuz bu anahtarla istek gönderir: şirketin mülakatlarını listeler, adayları notları, geçip geçmedikleri ve dürüstlük uyarılarıyla birlikte listeler veya okur ve bir adayı davet eder.
3. Bir **webhook** ekleyin: bir aday başladığında, bitirdiğinde, daveti kendisine ulaşamadığında, davetinin süresi dolduğunda veya kaldırıldığında ve bir mülakat hazır olduğunda prepza'nın imzalı olarak çağırdığı, platformunuzdaki bir adres; böylece sürekli sormanız gerekmez. API sayfası ona bir test olayı gönderebilir ve teslim günlüğünü gösterir.

Her aday, prepza'daki tüm sonuçlarının bağlantısıyla ve bitirene kadar kendi davet bağlantısıyla gelir; böylece isterseniz platformunuz bu bağlantıyı kendi mesajında gönderebilir. Platformunuz adayın kim olduğunu zaten biliyorsa onu giriş yapmadan davet edin: prepza hiç e-posta göndermez ve aday mülakata prepza'ya giriş yapmadan bağlantıdan katılır; bu yüzden bağlantıyı yalnızca adaya gönderin. Bir davet, bitiş sayfasındaki bir düğmeyle adayı sitenize (herhangi bir https adresine) geri de getirebilir ve şirketinizin renklerinde açık veya koyu bir tema ayarlayabilir. prepza'nın SDK'sı ile mülakatın kendisini kendi sayfanızda gösterebilirsiniz, ancak yalnızca şirketinizin API sayfasında izin verdiği sitelerde. API ve webhook'lar bu sitelere bağlı değildir: bunun yerine her anahtar sunucularınızın IP adresleriyle sınırlandırılabilir. Doğrulama yalnızca doğrulanmış şirket rozetini ekler.

Her yerde geçerli olan kural burada da geçerlidir: not bir insanın kararını destekler, bu yüzden adayları ona göre otomatik olarak reddetmeyin.

## Hangisi ne zaman kullanılmalı

İşi kimin yaptığından ve ne sıklıkla yapıldığından başlayın.

| Durumunuz | Kullanın |
| --- | --- |
| prepza'dasınız ve hızlı bir yanıt istiyorsunuz: kim geçti, kim başlamadı, ne kadar kredi kaldı | Mira, yerleşik asistan |
| Bir şeyi birkaç kelimeyle kurmak istiyorsunuz: bir iş tanımından mülakat, geçme notu, ek süre | Mira, yerleşik asistan |
| Zaten bütün gün Claude veya ChatGPT'de çalışıyorsunuz ve prepza'yı da orada istiyorsunuz | MCP |
| Görev prepza'nın yanında başka bir şey de gerektiriyor: belgeleriniz, e-posta taslakları, bağlı başka bir araç | MCP |
| Yoldaki bir işe alım uzmanı süreci telefonundaki yapay zekâ uygulamasından kontrol etmek istiyor | MCP |
| Kariyer siteniz veya İK sisteminiz, kimse tıklamadan adayları kendiliğinden davet etmeli | API |
| Sonuçlar, adaylar bitirir bitirmez kendi veritabanınıza veya panonuza düşmeli | API, bir webhook ile |
| ATS'niz prepza'nın bağlandıklarından biri (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Hiçbiri: ATS'yi Entegrasyonlar sekmesinden bağlayın. Bkz. [Beceri testleri ATS'nize nasıl bağlanır](/guides/ats-integration-skills-tests) |

Basit bir kural:

- **Bir insan soruyor ve her değişikliği kontrol ediyor:** prepza'daki Mira ya da o kişi tüm gününü Claude veya ChatGPT'de geçiriyorsa MCP.
- **Yazılım kendi başına, her seferinde aynı şekilde çalışıyor:** API.
- **Yeni başlıyorsanız:** önce yerleşik asistan Mira'yı deneyin. Kurulum gerektirmez ve öğrendikleriniz MCP'de de işinize yarar.

Birlikte de çalışırlar. Bir ekip davetleri İK sisteminden API ile gönderirken işe alım uzmanları sonuçları Mira'ya veya yapay zekâ sohbetlerine sorabilir.

## İyi sonuç almak için

- **Adıyla söyleyin.** "Senior Backend mülakatı", "o mülakat"tan daha iyi sonuç verir.
- **Önemli olduğunda her seferinde tek bir adım isteyin.** Sonucu kontrol edin, sonra bir sonrakini isteyin.
- **İzin vermeden önce onay isteğini okuyun.** Neyin çalışacağını tam olarak gösterir.
- **Bir sayının nereden geldiğini sorun.** İyi bir ajan arkasındaki adayları veya sayfayı gösterebilir.
- **Kararları insanlara bırakın.** Ajanı bulmak, sıralamak ve hazırlamak için kullanın; kararı siz verin.

## Fiyatlandırma

Mira, MCP bağlantısı ve API ücretsizdir. Her zamanki gibi yalnızca adaylar için ödeme yaparsınız: en az bir soruyu yanıtlayan aday başına, abonelik olmadan. Bkz. [fiyatlar](/pricing).

## İlgili yazılar

- [Beceri testleri ATS'nize nasıl bağlanır](/guides/ats-integration-skills-tests)
- [Yapay zekâ çağında mühendislerle mülakat](/guides/interviewing-in-the-age-of-ai)
- [AB'de yapay zekâ ile işe alım yasal mı?](/guides/is-ai-hiring-legal-in-the-eu)
