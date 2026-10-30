# The FAQ in tr; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "prepza nedir?",
        "answer": "İş tanımınızdan hazırlanan, her pozisyon için süreli bir mülakat. Adayları onlarla tanışmadan önce elemek için ya da işe alımın bir adımı olarak kullanın: her iki durumda da işi gerçekten kimin bildiğini görürsünüz.",
    },
    {
        "key": "roles",
        "question": "Hangi pozisyonlar için işe alım yapabilirim?",
        "answer": "Bilginin önemli olduğu her pozisyon için: destek, satış, finans, sağlık, zanaat ve teknik meslekler, mühendislik, pazarlama ve daha fazlası. İşi tarif edebiliyorsanız prepza onun için bir mülakat hazırlayabilir.",
    },
    {
        "key": "hiring",
        "question": "Nasıl çalışır?",
        "answer": "Ana sayfaya bir iş tanımı yapıştırın, şirketinize ad verin ve prepza'nın önerdiği konuları kontrol edin. Ardından adayları davet edin: e-postalarını yazın, bir liste yapıştırın ya da dosya yükleyin. Birkaç gün içinde başlamayan adaylara bir hatırlatma gider. Her aday kendi sorularını alır ve her sorunun bir süresi vardır; adaylar bitirir bitirmez puanlarını ve tüm cevaplarını görürsünüz.",
    },
    {
        "key": "link",
        "question": "Bir mülakatı iş ilanına koyabilir miyim?",
        "answer": "Evet. Mülakatın Ayarlar sekmesinden paylaşılabilir bağlantısını açın ve ilanınıza yapıştırın. Bağlantıyı açan herkes giriş yapar ve mülakata girer; her kişi, davet edilen bir aday gibi ücretlendirilir. Mülakatı İşe alındı olarak işaretlediğinizde bağlantı kapanır.",
    },
    {
        "key": "preview",
        "question": "Kimseyi davet etmeden önce bir mülakatı deneyebilir miyim?",
        "answer": "Evet. Mülakatınızı kendi sayfasından ücretsiz olarak aday gibi açın: önizlemeler adaylarınız arasında ya da soru istatistiklerinde görünmez. Ücretsiz pratik mülakatlardan herhangi birine de girebilirsiniz.",
    },
    {
        "key": "cheating",
        "question": "Adaylar yapay zekâ kullanabilir ya da cevapları arayabilir mi?",
        "answer": "Her aday kendi sırasında kendi rastgele sorularını alır ve her sorunun sunucumuzun tuttuğu [bir süre sınırı](/guides/skills-test-timing-and-extra-time) vardır, bu yüzden cevapları aramaya ya da yapay zekâya sormaya pek zaman kalmaz. Değerlendirme kartı ayrıca adayın sayfadan ne zaman ayrıldığını, metin kopyaladığını ya da soruyu okumuş olamayacak kadar hızlı cevap verdiğini gösterir. Aday bitirdiğinde sayfası, soruları bir yapay zekâya aktarmanın genellikle bıraktığı cevap örüntülerini de gösterir, örneğin her soruda yaklaşık aynı süre veya kolay sorular yanlışken zor soruların doğru olması; ayrıca canlı bir mülakatta sormak için adayın doğru cevapladığı soruları önerir. Örüntü, sormak için bir nedendir, kanıt değildir. Başlamadan önce her aday ayrıca soruları yapay zekâ araçları veya başkalarının yardımı olmadan kendisinin yanıtlayacağını onaylar ve değerlendirme kartı bunu gösterir.",
    },
    {
        "key": "cost",
        "question": "Ücreti ne kadar?",
        "answer": "Mülakat oluşturmak ücretsizdir. En az bir soruyu cevaplayan her aday {candidate} kredi ({candidate_price}) tutar; daha büyük yüklemelerden gelen kredilerle daha az, {cheapest_price} seviyesine kadar. İlk şirketiniz {company} ücretsiz kredi alır; bu, ilk {company_candidates} adayı için yeterlidir. [Fiyatlar sayfasında](/pricing) tüm fiyatlar yer alır.",
    },
    {
        "key": "charged",
        "question": "Bir aday için ne zaman ücret alınır?",
        "answer": "Aday en az bir soruyu yanıtlamışsa: mülakatı sona erdiğinde (kendisi bitirdiğinde ya da o yokken süresi dolduğunda) veya onu iptal ettiğinizde. Bir yanıt seçilmeden süresi dolan soru sayılmaz. Kredileri davet ettiğinizde ayrılır; hiçbir şeyi yanıtlamadan önce onu iptal ederseniz, hiç başlamazsa ya da mülakatı hiçbir şey yanıtlanmadan sona ererse geri gelir.",
    },
    {
        "key": "compare_hiring",
        "question": "Fiyat, diğer değerlendirme araçlarıyla nasıl karşılaştırılır?",
        "answer": "Birçok değerlendirme aracı, kimseyi test etmeseniz bile ödediğiniz aylık veya yıllık abonelikle satılır. prepza'da yalnızca aday başına ödersiniz: {candidate} kredi ({candidate_price}); sözleşme, kullanıcı başı ücret ve mülakat oluşturma ücreti yoktur. Ayda {example_candidates} aday davet eden bir şirket yılda yaklaşık {example_year_price} öder. Her ay çok sayıda aday test ediyorsanız bir abonelik daha ucuz olabilir; kendi rakamlarınızla karşılaştırın.",
    },
    {
        "key": "expire",
        "question": "Kredilerin süresi dolar mı?",
        "answer": "Hayır. Kredilerin süresi asla dolmaz; ücretli abonelik yoktur. İsteğe bağlı otomatik yüklemeyi açarsanız Paddle kartınızı {zero_price} tutarında bir abonelik olarak kaydeder; yalnızca yapılan yüklemeler için ödersiniz.",
    },
    {
        "key": "currency",
        "question": "Hangi para biriminde öderim?",
        "answer": "Fiyatlar Kanada, Avustralya, İsrail, Polonya, İsviçre, Japonya, Güney Kore, Tayvan, Hong Kong, Tayland, Singapur ve Hindistan'da yerel para birimi; AB'nin geri kalanında ve İzlanda, Lihtenştayn ve Norveç'te avro; Birleşik Krallık'ta sterlin; diğer yerlerde ise ABD doları cinsindendir. Hesabınız ve her şirket, nereye seyahat ederseniz edin, oluşturuldukları ülkenin para birimini korur: kendinizinkini Ayarlar'da, bir şirketinkini ise o şirketin Kredi yükle düğmesinin yanında değiştirebilirsiniz (sahipler ve yöneticiler). Bir şirketin yüklemeleri, otomatik olanlar da, her zaman şirketin para biriminde tahsil edilir.",
    },
    {
        "key": "refunds",
        "question": "Para iadesi alabilir miyim?",
        "answer": "Evet, son 14 gün içinde satın aldığınız ve harcamadığınız krediler için: Paddle üzerinden veya bize yazarak. Hoş geldin hediyesi gibi ücretsiz krediler iade edilmez. Ayrıntılar [koşullarda](/terms) yer alır.",
    },
    {
        "key": "scorecards",
        "question": "Değerlendirme kartları neleri gösterir?",
        "answer": 'Her cevabı, doğru olup olmadığını ve ne kadar sürdüğünü. Not, kazanılan puanların yüzdesidir: her soru bir puan değerindedir; "doğru olanların hepsini seçin" sorusu işaretlenen her doğru seçenek için bu puanın bir kısmını verir, yanlış bir seçenek işaretlenirse hiç puan vermez. Notlar, mülakat için belirlediğiniz geçme notuna göre yeşil ya da kırmızı görünür. Değerlendirme kartı ayrıca okunamayacak kadar hızlı verilen cevapları, adayın sayfadan ayrıldığı anları ve kopyalama girişimlerini işaretler.',
    },
    {
        "key": "reports",
        "question": "Sonuçları işe alım yöneticisiyle paylaşabilir miyim?",
        "answer": "Evet. Tek bir aday ya da bir mülakatın tüm adayları için PDF raporu indirin, doğrudan prepza'dan e-postayla gönderin ya da WhatsApp, Telegram, Viber veya LINE'da kısa bir özet gönderin.",
    },
    {
        "key": "action_log",
        "question": "Şirketimde kimin ne yaptığını görebilir miyim?",
        "answer": "Evet, şirketin sahibiyseniz. Şirketin İşlem kaydı sekmesi, üyelerinin yaptığı her şeyi en yeniden başlayarak listeler: aday davet etme veya kaldırma, sonuçları görüntüleme ve mülakatlarda, ekipte, faturalandırmada ve entegrasyonlarda yapılan değişiklikler; bunu kimin, ne zaman yaptığı ve asistanın, bir yapay zekâ uygulamasının veya API'nin onun adına yapıp yapmadığıyla birlikte. Kaydı üyeye, işlem türüne ve tarihlere göre filtreleyebilirsiniz. İşlemler 12 ay saklanır. Bir API anahtarının işlemleri anahtarın adıyla görünür.",
    },
    {
        "key": "notes",
        "question": "Ekibim bir mülakata yorum yazabilir mi?",
        "answer": "Evet. Her mülakatın, ekibinizin işe alım süreciyle ilgili düz metin yorumlar yazdığı bir Yorumlar sekmesi vardır; örneğin sırada kimin aranacağı ya da bir ajanssanız mülakatın hangi müşteri için olduğu. Görüntüleyiciler dahil her üye yorum yazabilir ve kendi yorumlarını düzenleyebilir; bir yorumu yazarı, sahipler ve yöneticiler silebilir. Sahipler ve yöneticiler bir yorumu sabitleyebilir; bu yorum mülakatın adının altında görünür. Adaylar yorumları asla görmez.",
    },
    {
        "key": "integrations",
        "question": "prepza, ATS'imle veya diğer araçlarla çalışır mı?",
        "answer": "Evet, ek ücret olmadan. Workable, Greenhouse, Teamtailor, Recruitee veya Breezy HR'ı şirketinizin Entegrasyonlar sekmesinden bağlayın: bir aşamaya taşıdığınız adaylar mülakatı alır ve sonuçları ATS'ye geri gönderilir ([beceri testlerini ATS'nize nasıl bağlarsınız](/guides/ats-integration-skills-tests)). Slack, şirketinizin bildirimlerini bir kanala gönderebilir; API ise kendi platformunuzun mülakat oluşturmasını, adayları davet edip yönetmesini ve sonuçlarını almasını sağlar; her API anahtarı yalnızca onun için işaretlediğiniz işlemleri yapabilir. Ayrıntılar için [API belgeleri](/api-docs) sayfasına bakın.",
    },
    {
        "key": "ai_apps",
        "question": "prepza'yı Claude, ChatGPT veya kendi yapay zekâ ajanımdan kullanabilir miyim?",
        "answer": "Evet. prepza'yı Claude veya ChatGPT'ye bağlayıcı olarak ekleyin (adımlar şirketinizin Entegrasyonlar sekmesinde) ve prepza'da izin verin. Uygulama bundan sonra sizin adınıza ve sizin yetkilerinizle şirketleriniz, mülakatlarınız ve adayların sonuçlarıyla çalışır; çoğu uygulama bir şeyi değiştirmeden önce size sorar. Hesabınızı veya bir şirketi yalnızca prepza'da silebilirsiniz. Uygulamanın okuduğu veriler, o uygulamanın koşullarına göre sağlayıcısına ulaşır. Bağlantıyı istediğiniz zaman aynı sekmeden kesebilirsiniz. Diğer yapay zekâ uygulamaları ve kendi geliştirdiğiniz ajanlar da bağlanabilir: geliştirici belgelerindeki [MCP sekmesinde](/api-docs?tab=mcp) adımlar ve örnek ajanlar vardır; sunucuda çalışan bir ajan, yapay zekâ ajanları yetkisine sahip bir API anahtarıyla oturum açabilir. [Yapay zekâ ajanları, MCP ve API'ler rehberi](/guides/ai-agents-mcp-and-api) her birinin ne işe yaradığını açıklar.",
    },
    {
        "key": "candidates",
        "question": "Adaylar ne görür?",
        "answer": "Şirketinizin adını ve logosunu, şirketinizin renkleri ve yazı tipleriyle (Marka sekmesinde ayarlanır), başlamadan önce neyle karşılaşacaklarını, ardından her seferinde bir süreli soru. Puanlarını ya da bir cevabın doğru olup olmadığını asla görmezler.",
    },
    {
        "key": "verified",
        "question": "Doğrulandı işareti ne anlama gelir?",
        "answer": "Şirketin bir sahibinin ya da yöneticisinin, şirketin web sitesine ait bir iş e-postasıyla (ör. you@acme.com) giriş yaptığı ve ardından ekibimizin şirketi incelediği anlamına gelir. Web sitesini şirketinizin başlığındaki Doğrula ile ekleyin; ücretsiz e-posta servisleri sayılmaz. İnceleme beklerken ekibiniz adın yanında bir saat görür; şirketin adını değiştirmek onu yeniden incelemeye gönderir. İşaret, davetler dahil şirketinizin adının yanında görünür.",
    },
    {
        "key": "languages",
        "question": "Hangi diller destekleniyor?",
        "answer": "Site, mülakatlar ve e-postalar için {count} dil. İş tanımı hangi dilde olursa olsun, mülakatın hangi dilde yazılacağını siz seçersiniz.",
    },
    {
        "key": "privacy",
        "question": "İş tanımları ve cevaplara ne olur?",
        "answer": "İş tanımları şirketinizin mülakatlarını hazırlamak, adayların cevapları ise onları şirketiniz adına puanlamak için kullanılır. prepza'nın oluşturduğu sorular, sizi, şirketinizi veya başka birini tanımlayan hiçbir bilgi olmadan diğer şirketlerin mülakatlarında ve pratiklerinde de yeniden kullanılabilir; bir mülakatın sorularını mülakatın ayarlarından bunun dışında tutabilirsiniz. prepza ayrıca soruların oluşturulma şeklini iyileştirmek için, soruların nasıl cevaplandığından soru kalitesine ilişkin genel, anonimleştirilmiş örüntüler çıkarır. [Gizlilik politikası](/privacy) neleri, ne kadar süre sakladığımızı ve herkesin haklarını açıklar.",
    },
    {
        "key": "eu_ai_law",
        "question": "AB'de adayları ön elemek için yapay zekâ kullanmak yasal mı?",
        "answer": "Evet, kurallara uyarak. AB Yapay Zekâ Yasası'na (AI Act) göre adayları puanlayan araçlar büyük olasılıkla yüksek risklidir ve yükümlülükler 2 Aralık 2027'den itibaren başlar; GDPR ise zaten geçerlidir: işe alım kararını bir insan verir, adaylara yapay zekâ kullanıldığı söylenir ve kayıt tutulur. prepza da böyle çalışır: soruları yapay zekâ yazar, şirketinizdeki kişiler sonuçları inceleyip karar verir ve adaylar başlamadan önce bilgilendirilir. Bu bir hukuki tavsiye değildir; [AB'de yapay zekâ ile işe alım yasal mı?](/guides/is-ai-hiring-legal-in-the-eu) kuralları ve tarihleri açıklar.",
    },
    {
        "key": "emails",
        "question": "prepza hangi e-postaları gönderir ve bunları nasıl durdururum?",
        "answer": 'Davetler, raporlar, ödeme sorunları ve koşullarımızdaki değişiklikler gibi hizmet e-postaları her zaman gönderilir. Günlük etkinlik özeti, hatırlatmalar ve ürün güncellemeleri gibi diğerlerini Ayarlar\'da, E-postalar bölümünde seçebilir ya da her e-postadaki "Abonelikten çık" bağlantısıyla durdurabilirsiniz. Adaylar, davet ve hatırlatma e-postalarındaki bağlantılarla şirketinizin e-postalarını ya da bir mülakatın hatırlatmalarını durdurabilir.',
    },
    {
        "key": "delete",
        "question": "Hesabımı silebilir miyim?",
        "answer": "Evet, Ayarlar'dan. Hesabınız ve verileriniz silinir; öncesinde verilerinizin bir kopyasını indirebilirsiniz. prepza'nın haberleri, üstteki zil simgesinde, yani bildirimlerinizde görünür; önemli haberler ayrıca ürün güncellemesi olarak e-postayla da gelir, ancak yalnızca bu ayar açıkken.",
    },
    {
        "key": "report",
        "question": "Bir sorunu nasıl bildiririm?",
        "answer": "[İletişim sayfasından](/contact) bize yazın ve konu olan şeyin ID'sini yapıştırın: “id'yi kopyala” bir şirketin, mülakatın veya adayın adının altında, hesabınızınki ise hesap menüsünde ve Ayarlar'da. ID sayesinde onu hemen buluruz.",
    },
]
