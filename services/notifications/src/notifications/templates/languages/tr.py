# Email texts in Turkish. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Bu e-posta {email} adresine, testee'de bir şirketin sahibi veya yöneticisi olduğunuz "
    "için gönderildi."
)

TEXTS = {
    "candidate": {
        "subject": "{company} mülakat daveti",
        "preheader": "testee'de “{title}” mülakatına katılın. Başlamak için {email} "
        "ile giriş yapın.",
        "heading": "Mülakat daveti",
        "lines": [
            "{company} sizi testee'deki “{title}” mülakatına davet ediyor.",
            (
                "Başlamak için {email} ile giriş yapın. Mülakata yalnızca bu adres "
                "katılabilir ve tek bir hakkınız var."
            ),
        ],
        "button": "Daveti aç",
    },
    "joined": {
        "subject": "“{title}” bağlantınız",
        "preheader": "Mülakattan ayrılırsanız bu bağlantıyla devam edin. {email} ile giriş yapın.",
        "heading": "Mülakat bağlantınız",
        "lines": [
            "testee'de {company} şirketinin “{title}” mülakatına başladınız.",
            (
                "Ayrılırsanız bu bağlantıyla devam edin: {email} ile giriş yapın. {company} başladığını"
                "z bağlantıyı kapatsa bile çalışmaya devam eder. Siz yokken süre işlemeye devam "
                "eder."
            ),
        ],
        "button": "Mülakata devam et",
        "footer": (
            "Bu e-posta {email} adresine, bu adresle testee'de bir mülakata başlandığı için gönderildi."
        ),
    },
    "reminder": {
        "subject": "Hatırlatma: {company} mülakatınız",
        "preheader": "“{title}” hâlâ açık. Başlamak için {email} ile giriş yapın.",
        "heading": "Mülakatınız sizi bekliyor",
        "lines": [
            (
                "{company} birkaç gün önce sizi testee'deki “{title}” mülakatına davet etti "
                "ve henüz başlamadınız."
            ),
            (
                "Başlamak için {email} ile giriş yapın. Mülakata yalnızca bu adres katılabilir "
                "ve tek bir hakkınız var. Davet, gönderildikten 30 gün sonra geçerliliğini yitirir."
            ),
        ],
        "button": "Daveti aç",
    },
    "member": {
        "subject": "testee'de {company} ekibine katılın",
        "preheader": (
            "{company} ekibine {role} olarak katılın. Daveti kabul etmek için {email} ile giriş "
            "yapın."
        ),
        "heading": "Ekip daveti",
        "lines": [
            "{inviter} sizi testee'deki {company} ekibine {role} olarak davet ediyor.",
            (
                "Daveti kabul etmek için {email} ile giriş yapın. Daveti yalnızca bu adres kabul "
                "edebilir."
            ),
        ],
        "button": "Daveti aç",
        # The role's name as the lines use it.
        "roles": {"admin": "yönetici", "viewer": "görüntüleyici"},
    },
    "report": {
        "subject": "Rapor: {candidate}",
        "preheader": "{candidate}, {company} şirketinde “{title}” mülakatına girdi. Rapor ektedir.",
        "heading": "Aday raporu",
        "lines": [
            "{company} şirketinden {sender}, “{title}” mülakatı için {candidate} adlı adayın raporunu paylaştı.",
            (
                "Rapor tek sayfalık bir PDF olarak ektedir: genel not, her konunun puanı ve "
                "adayın tarayıcısının gösterdikleri. {sender} kişisine yanıt vermek için bu "
                "e-postayı yanıtlayın."
            ),
        ],
        "button": "testee'yi ziyaret et",
        "footer": "Bu e-posta {email} adresine, {sender} testee'de bu adresle bir aday raporu "
        "paylaştığı için gönderildi. Beklemiyorsanız görmezden gelebilirsiniz.",
    },
    "candidates": {
        "subject": "Tüm adaylar: {title}",
        "preheader": "{company} şirketinde “{title}” için tüm adaylar. Rapor ektedir.",
        "heading": "Adaylar raporu",
        "lines": [
            "{company} şirketinden {sender}, “{title}” mülakatının tüm adaylarının raporunu paylaştı.",
            (
                "Rapor PDF olarak ektedir: her adayın notu, ilerlemesi ve tarayıcısının "
                "gösterdikleri, en iyiden başlayarak. {sender} kişisine yanıt vermek için bu "
                "e-postayı yanıtlayın."
            ),
        ],
        "button": "testee'yi ziyaret et",
        "footer": "Bu e-posta {email} adresine, {sender} testee'de bu adresle bir aday raporu "
        "paylaştığı için gönderildi. Beklemiyorsanız görmezden gelebilirsiniz.",
    },
    "digest": {
        "subject": "testee etkinlik özetiniz",
        "preheader": "Son 24 saatte şirketlerinizde olanlar.",
        "heading": "Etkinlik özetiniz",
        "lines": [
            "Son 24 saatte testee'deki şirketlerinizde olanlar şunlar.",
        ],
        "rows": {
            "candidate_finished": "Mülakatı tamamlayan adaylar: {count} · “{title}”",
            "invite_undelivered": "İletilemeyen davetler: {count} · “{title}”",
            "ats_not_invited": "Davet edilmeyen {ats} adayları: {count}",
            "interview_ready": "Hazır mülakat: “{title}”",
            "note_added": "Ekibinizin yeni yorumları: {count} · “{title}”",
            "note": "{author}: “{excerpt}”",
            "note_by_former": "Eski bir üye: “{excerpt}”",
        },
        "button": "testee'yi aç",
        "footer": (
            "Bu e-posta {email} adresine, testee'de bir şirketin üyesi olduğunuz ve "
            "etkinlik özetini aldığınız için gönderildi."
        ),
    },
    "low_credits": {
        "subject": "Kredileriniz azalıyor",
        "preheader": "Aday davet etmeye devam etmek için kredi yükleyin.",
        "heading": "Krediler azalıyor",
        "lines": [
            (
                "Bu şirketlerin bir aday daha davet etmeye yetecek kredisi yok. Aday davet "
                "etmeye devam etmek için kredi yükleyin."
            ),
        ],
        "rows": {
            "company": "{company} · kullanılabilir kredi: {available}",
        },
        "button": "Kredi yükle",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Adaylar bekleniyor",
        "preheader": "Adayları e-postayla davet edin veya mülakatın bağlantısını paylaşın.",
        "heading": "Adaylar bekleniyor",
        "lines": [
            (
                "Bu mülakatlar birkaç gündür hazır, ancak henüz kimse davet edilmedi. "
                "Adayları e-postayla davet edin veya mülakatın bağlantısını paylaşın."
            ),
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "Adayları davet et",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Konularınız incelemenizi bekliyor",
        "preheader": "Konuları onaylayın, sorular oluşturulsun.",
        "heading": "Konularınızı inceleyin",
        "lines": [
            (
                "Başlattığınız mülakatların konuları incelemenizi bekliyor. Onayladığınızda"
                " sorular oluşturulur. 14 gün açık kalan bir inceleme iptal edilir."
            ),
        ],
        "rows": {
            "interview": "{company} · bekleme süresi (gün): {days}",
        },
        "button": "Konuları incele",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "{date} itibarıyla yeni kullanım koşulları",
        "preheader": "Yeni kullanım koşulları {date} tarihinden itibaren geçerli.",
        "heading": "Kullanım koşullarımızı güncelliyoruz",
        "lines": [
            (
                "testee kullanım koşullarının yeni bir sürümünü yayımladık. Yeni sürüm {date} "
                "tarihinden itibaren geçerli; o zamana kadar mevcut koşullar geçerli olmaya devam "
                "ediyor."
            ),
            (
                "testee'yi {date} tarihinden sonra kullanmanız, yeni koşulları kabul ettiğiniz "
                "anlamına gelir. Kabul etmiyorsanız, bu tarihten önce Ayarlar'dan hesabınızı "
                "silebilirsiniz."
            ),
        ],
        "button": "Yeni koşulları oku",
        "footer": (
            "Bu e-posta {email} adresine, bir testee hesabınız olduğu için gönderildi. "
            "Kullanım koşullarımızla ilgili bir bildirim olduğundan e-posta ayarlarınızdan "
            "bağımsız olarak gönderilir."
        ),
    },
    "legal_privacy": {
        "subject": "{date} itibarıyla yeni gizlilik politikası",
        "preheader": "Yeni gizlilik politikası {date} tarihinden itibaren geçerli.",
        "heading": "Gizlilik politikamızı güncelliyoruz",
        "lines": [
            (
                "testee gizlilik politikasının, verilerinizi nasıl kullandığımızı açıklayan yeni "
                "bir sürümünü yayımladık. Yeni sürüm {date} tarihinden itibaren geçerli; o zamana "
                "kadar mevcut sürüm geçerli olmaya devam ediyor."
            ),
            "Verilerinizi istediğiniz zaman Ayarlar'dan indirebilir veya silebilirsiniz.",
        ],
        "button": "Yeni gizlilik politikasını oku",
        "footer": (
            "Bu e-posta {email} adresine, bir testee hesabınız olduğu için gönderildi. "
            "Verilerinizi nasıl kullandığımızla ilgili bir bildirim olduğundan e-posta "
            "ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    "legal_dpa": {
        "subject": "{date} itibarıyla yeni veri işleme sözleşmesi",
        "preheader": "Yeni sözleşme şirketiniz için {date} tarihinden itibaren geçerli.",
        "heading": "Veri işleme sözleşmemizi güncelliyoruz",
        "lines": [
            (
                "testee'nin adaylarınızın verilerini işlerken dayandığı veri işleme sözleşmesinin "
                "yeni bir sürümünü yayımladık. Yeni sürüm {date} tarihinden itibaren geçerli; o "
                "zamana kadar mevcut sürüm geçerli olmaya devam ediyor."
            ),
            (
                "Makul veri koruma gerekçeleriyle itiraz eden bir şirket, bu tarihten önce "
                "testee'yi kullanmayı bırakıp şirketini silebilir."
            ),
        ],
        "button": "Yeni sözleşmeyi oku",
        "footer": (
            "Bu e-posta {email} adresine, testee'de bir şirketin sahibi veya yöneticisi "
            "olduğunuz için gönderildi. Şirketinizle yaptığımız sözleşmeyle ilgili bir "
            "bildirim olduğundan e-posta ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    # Campaigns (services/campaign_sends.py), named after the setting they need: a superadmin's
    # subject and text, and its button's text, or "open_site" when it has none.
    "updates": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "testee'yi aç",
        "footer": (
            "Bu e-posta {email} adresine, testee'den ürün güncellemeleri ve haberler almayı"
            " seçtiğiniz için gönderildi."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "testee'yi aç",
        "footer": (
            "Bu e-posta {email} adresine, testee'den teklifler ve kampanyalar almayı seçtiğiniz"
            " için gönderildi."
        ),
    },
    # An important notice: a service email about testee itself (a security incident, planned
    # downtime, a change to how it works), whatever the email settings; never a promotion.
    "notices": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "testee'yi aç",
        "footer": (
            "Bu e-posta {email} adresine, bir testee hesabınız olduğu için gönderildi. Hizmetle"
            " ilgili, örneğin güvenliği veya erişilebilirliği hakkında önemli bir duyuru"
            " olduğundan e-posta ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    "top_up_failed": {
        "subject": "Otomatik yükleme başarısız: {company}",
        "preheader": "Karttan ödeme alınamadı. Aday davet etmeye devam etmek için kredi yükleyin.",
        "heading": "Otomatik yükleme başarısız oldu",
        "lines": [
            "Otomatik yükleme {company} için karttan ödeme alamadı, bu yüzden kredi eklenmedi.",
            (
                "Aday davet etmeye devam etmek için kredi yükleyin. Otomatik yükleme kartı "
                "daha sonra yeniden deneyecek."
            ),
        ],
        "button": "Kredi yükle",
        "footer": (
            "Bu e-posta {email} adresine, testee'de {company} şirketinin sahibi veya "
            "yöneticisi olduğunuz için gönderildi. Şirketinizin faturalandırmasıyla ilgili "
            "olduğundan e-posta ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    "top_up_paused": {
        "subject": "Otomatik yükleme duraklatıldı: {company}",
        "preheader": "Kart reddedildi. Otomatik yüklemeyi yeniden açmak için kartı güncelleyin.",
        "heading": "Otomatik yükleme duraklatıldı",
        "lines": [
            (
                "{company} için otomatik yüklemenin kartı reddedildi ve yeniden denemek işe "
                "yaramayacak; bu yüzden otomatik yükleme duraklatıldı ve bu karttan ödeme "
                "almayacak."
            ),
            (
                "Otomatik yüklemeyi yeniden açmak için faturalandırma sayfasında kartı "
                "güncelleyin. O zamana kadar aday davet etmeye devam etmek için elle kredi "
                "yükleyin."
            ),
        ],
        "button": "Kartı güncelle",
        "footer": (
            "Bu e-posta {email} adresine, testee'de {company} şirketinin sahibi veya "
            "yöneticisi olduğunuz için gönderildi. Şirketinizin faturalandırmasıyla ilgili "
            "olduğundan e-posta ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    "top_up_on": {
        "subject": "Otomatik yükleme açıldı: {company}",
        "preheader": (
            "Kullanılabilir bakiye her {threshold, plural, one {# kredinin} other {# "
            "kredinin}} altına düştüğünde {price} artı vergi."
        ),
        "heading": "Otomatik yükleme açık",
        "lines": [
            (
                "{company} için otomatik yükleme artık açık. Kullanılabilir bakiyesi her "
                "{threshold, plural, one {# kredinin} other {# kredinin}} altına düştüğünde, "
                "otomatik yükleme kapatılana kadar kayıtlı karttan {price} tahsil edilir; geçerli "
                "olduğu yerlerde KDV veya satış vergisi eklenir."
            ),
            (
                "Her tahsilat şirketin sahiplerine ve yöneticilerine e-postayla bildirilir; "
                "yeniden satıcımız Paddle da makbuzunu e-postayla gönderir."
            ),
            (
                "Kapatmak için faturalandırma sayfasında otomatik yükleme bölümüne gidin ve "
                "“Kapat”ı seçin. Hemen durur ve başka hiçbir tahsilat yapılmaz."
            ),
        ],
        "button": "Faturalandırmayı aç",
        "footer": (
            "Bu e-posta {email} adresine, testee'de {company} şirketinin sahibi veya "
            "yöneticisi olduğunuz için gönderildi. Şirketinizin faturalandırmasıyla ilgili "
            "olduğundan e-posta ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    "top_up_charged": {
        "subject": "Otomatik yükleme tahsil edildi: {company}",
        "preheader": "{date} tarihinde {credits, plural, one {# kredi} other {# kredi}} için {price}.",
        "heading": "Otomatik yükleme karttan tahsilat yaptı",
        "lines": [
            (
                "{date} tarihinde otomatik yükleme {company} için karttan vergiler dahil {price} "
                "tahsil etti ve {credits, plural, one {# kredi} other {# kredi}} ekledi. "
                "{company} şirketinin artık {available, plural, one {# kullanılabilir kredisi} "
                "other {# kullanılabilir kredisi}} var."
            ),
            "Makbuzu yeniden satıcımız Paddle e-postayla gönderir.",
            (
                "Bu tahsilatları durdurmak için faturalandırma sayfasında otomatik yükleme "
                "bölümüne gidin ve “Kapat”ı seçin. Hemen durur ve başka hiçbir tahsilat yapılmaz."
            ),
        ],
        "button": "Faturalandırmayı aç",
        "footer": (
            "Bu e-posta {email} adresine, testee'de {company} şirketinin sahibi veya "
            "yöneticisi olduğunuz için gönderildi. Şirketinizin faturalandırmasıyla ilgili "
            "olduğundan e-posta ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    "top_up_price_change": {
        "subject": "{company} için yeni otomatik yükleme fiyatı",
        "preheader": (
            "{date} itibarıyla her otomatik yüklemenin ücreti {price} yerine {new_price} olacak."
        ),
        "heading": "Otomatik yükleme fiyatı değişiyor",
        "lines": [
            (
                "{date} itibarıyla {company} için her otomatik yüklemenin ücreti {price} yerine "
                "{new_price} olacak; geçerli olduğu yerlerde KDV veya satış vergisi eklenir. Aday "
                "sayısı aynı kalır."
            ),
            (
                "O tarihe kadarki tahsilatlar yine {price} olur. Farklı bir tutar isterseniz "
                "{date} tarihinden önce faturalandırma sayfasında otomatik yüklemeyi değiştirin "
                "veya kapatın."
            ),
        ],
        "button": "Faturalandırmayı aç",
        "footer": (
            "Bu e-posta {email} adresine, testee'de {company} şirketinin sahibi veya "
            "yöneticisi olduğunuz için gönderildi. Şirketinizin faturalandırmasıyla ilgili "
            "olduğundan e-posta ayarlarınızdan bağımsız olarak gönderilir."
        ),
    },
    "footer": "Bu e-posta {email} adresine, biri bu adresi testee'ye davet ettiği için "
    "gönderildi. Beklemiyorsanız görmezden gelebilirsiniz.",
    # An invite from a company testee hasn't verified, at the end of the footer.
    "unverified": "testee, {company} şirketini doğrulamadı.",
    "paste_link": "Ya da bu bağlantıyı tarayıcınıza yapıştırın",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Abonelikten çık",
    "email_settings": "E-posta ayarlarını değiştir",
    "stop_reminders": "Bu mülakat için bana hatırlatma gönderme",
    "stop_company": "{company} adına bana e-posta gönderme",
    # Who runs testee, at the end of every email.
    "operator": "testee, {name} tarafından işletilir, {address}.",
}
