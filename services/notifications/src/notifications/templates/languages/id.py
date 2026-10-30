# Email texts in Indonesian. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Email ini dikirim ke {email} karena kamu pemilik atau admin sebuah perusahaan di prepza."
)

TEXTS = {
    "candidate": {
        "subject": "Undangan wawancara dari {company}",
        "preheader": "Ikuti “{title}” di prepza. Masuk dengan {email} untuk mulai.",
        "heading": "Undangan wawancara",
        "lines": [
            "{company} mengundangmu mengikuti wawancara “{title}” di prepza.",
            (
                "Masuk dengan {email} untuk mulai. Hanya alamat ini yang bisa "
                "mengikuti wawancara, dan kamu punya satu kesempatan."
            ),
        ],
        "button": "Buka undangan",
    },
    "joined": {
        "subject": "Tautanmu ke “{title}”",
        "preheader": "Jika kamu meninggalkan wawancara, lanjutkan dengan tautan ini. Masuk dengan {email}.",
        "heading": "Tautan wawancaramu",
        "lines": [
            "Kamu memulai wawancara “{title}” dari {company} di prepza.",
            (
                "Jika kamu pergi, lanjutkan dengan tautan ini: masuk dengan {email}. Tautan ini "
                "tetap berfungsi meskipun {company} menonaktifkan tautan yang kamu gunakan untuk "
                "memulai. Waktu terus berjalan selama kamu pergi."
            ),
        ],
        "button": "Lanjutkan wawancara",
        "footer": (
            "Email ini dikirim ke {email} karena sebuah wawancara di prepza dimulai dengan alamat "
            "ini."
        ),
    },
    "reminder": {
        "subject": "Pengingat: wawancaramu dengan {company}",
        "preheader": "“{title}” masih terbuka. Masuk dengan {email} untuk mulai.",
        "heading": "Wawancaramu sedang menunggu",
        "lines": [
            (
                "{company} mengundangmu mengikuti wawancara “{title}” di prepza beberapa hari "
                "lalu, dan kamu belum memulainya."
            ),
            (
                "Masuk dengan {email} untuk mulai. Hanya alamat ini yang bisa mengikuti wawancara, "
                "dan kamu punya satu kesempatan. Undangan kedaluwarsa 30 hari setelah dikirim."
            ),
        ],
        "button": "Buka undangan",
    },
    "member": {
        "subject": "Bergabung dengan {company} di prepza",
        "preheader": (
            "Bergabunglah dengan tim {company} sebagai {role}. Masuk dengan {email} untuk menerima "
            "undangan."
        ),
        "heading": "Undangan bergabung dengan tim",
        "lines": [
            "{inviter} mengundangmu bergabung dengan tim {company} di prepza sebagai {role}.",
            (
                "Masuk dengan {email} untuk menerima undangan. Hanya alamat ini yang bisa menerima "
                "undangan."
            ),
        ],
        "button": "Buka undangan",
        # The role's name as the lines use it.
        "roles": {"admin": "admin", "viewer": "pelihat"},
    },
    "report": {
        "subject": "Laporan: {candidate}",
        "preheader": "{candidate} mengikuti “{title}” di {company}. Laporannya terlampir.",
        "heading": "Laporan kandidat",
        "lines": [
            "{sender} dari {company} membagikan laporan {candidate} untuk wawancara “{title}”.",
            (
                "Laporan terlampir sebagai PDF satu halaman: nilai keseluruhan, skor tiap topik, dan "
                "apa yang ditunjukkan browser kandidat. Balas email ini untuk menjawab {sender}."
            ),
        ],
        "button": "Kunjungi prepza",
        "footer": "Email ini dikirim ke {email} karena {sender} membagikan laporan kandidat "
        "dengan alamat ini di prepza. Jika kamu tidak mengharapkannya, abaikan saja.",
    },
    "candidates": {
        "subject": "Semua kandidat: {title}",
        "preheader": "Semua kandidat untuk “{title}” di {company}. Laporannya terlampir.",
        "heading": "Laporan kandidat",
        "lines": [
            "{sender} dari {company} membagikan laporan semua kandidat untuk wawancara “{title}”.",
            (
                "Laporan terlampir sebagai PDF: nilai, progres, dan apa yang ditunjukkan browser "
                "tiap kandidat, diurutkan dari yang terbaik. Balas email ini untuk menjawab {sender}."
            ),
        ],
        "button": "Kunjungi prepza",
        "footer": "Email ini dikirim ke {email} karena {sender} membagikan laporan kandidat "
        "dengan alamat ini di prepza. Jika kamu tidak mengharapkannya, abaikan saja.",
    },
    "digest": {
        "subject": "Ringkasan aktivitasmu di prepza",
        "preheader": "Apa yang terjadi di perusahaanmu dalam 24 jam terakhir.",
        "heading": "Ringkasan aktivitasmu",
        "lines": [
            "Inilah yang terjadi di perusahaanmu di prepza dalam 24 jam terakhir.",
        ],
        "rows": {
            "candidate_finished": "Kandidat yang selesai: {count} · “{title}”",
            "invite_undelivered": "Undangan yang tidak terkirim: {count} · “{title}”",
            "ats_not_invited": "Kandidat dari {ats} yang tidak diundang: {count}",
            "interview_ready": "Wawancara siap: “{title}”",
            "note_added": "Catatan baru dari timmu: {count} · “{title}”",
            "note": "{author}: “{excerpt}”",
            "note_by_former": "Mantan anggota: “{excerpt}”",
        },
        "button": "Buka prepza",
        "footer": (
            "Email ini dikirim ke {email} karena kamu anggota sebuah perusahaan di prepza "
            "dan menerima ringkasan aktivitasnya."
        ),
    },
    "low_credits": {
        "subject": "Kreditmu hampir habis",
        "preheader": "Isi ulang untuk terus mengundang kandidat.",
        "heading": "Kredit hampir habis",
        "lines": [
            (
                "Perusahaan ini tidak punya cukup kredit untuk mengundang satu kandidat "
                "lagi. Isi ulang untuk terus mengundang kandidat."
            ),
        ],
        "rows": {
            "company": "{company} · kredit tersedia: {available}",
        },
        "button": "Isi ulang",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Menunggu kandidat",
        "preheader": "Undang kandidat lewat email atau bagikan tautan wawancaranya.",
        "heading": "Menunggu kandidat",
        "lines": [
            (
                "Wawancara ini sudah siap sejak beberapa hari lalu, tetapi belum ada yang "
                "diundang. Undang kandidat lewat email atau bagikan tautan wawancaranya."
            ),
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "Undang kandidat",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Topikmu menunggu ditinjau",
        "preheader": "Konfirmasi topiknya, lalu pertanyaan akan dibuat.",
        "heading": "Tinjau topikmu",
        "lines": [
            (
                "Topik wawancara yang kamu mulai sedang menunggu tinjauanmu. Setelah kamu "
                "mengonfirmasinya, pertanyaan akan dibuat. Tinjauan yang dibiarkan terbuka "
                "selama 14 hari akan dibatalkan."
            ),
        ],
        "rows": {
            "interview": "{company} · hari menunggu: {days}",
        },
        "button": "Tinjau topik",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Ketentuan layanan baru mulai {date}",
        "preheader": "Ketentuan layanan yang baru berlaku mulai {date}.",
        "heading": "Kami memperbarui ketentuan layanan kami",
        "lines": [
            (
                "Kami telah menerbitkan versi baru ketentuan layanan prepza. Versi ini berlaku "
                "mulai {date}; sampai saat itu, ketentuan yang sekarang tetap berlaku."
            ),
            (
                "Dengan menggunakan prepza setelah {date}, kamu menerima ketentuan yang baru. "
                "Jika tidak, kamu bisa menghapus akunmu di Pengaturan sebelum tanggal itu."
            ),
        ],
        "button": "Baca ketentuan yang baru",
        "footer": (
            "Email ini dikirim ke {email} karena kamu punya akun prepza. Ini pemberitahuan "
            "tentang ketentuan layanan kami, jadi selalu dikirim apa pun pengaturan emailmu."
        ),
    },
    "legal_privacy": {
        "subject": "Kebijakan privasi baru mulai {date}",
        "preheader": "Kebijakan privasi yang baru berlaku mulai {date}.",
        "heading": "Kami memperbarui kebijakan privasi kami",
        "lines": [
            (
                "Kami telah menerbitkan versi baru kebijakan privasi prepza, yang menjelaskan "
                "cara kami menggunakan datamu. Versi ini berlaku mulai {date}; sampai saat itu, "
                "versi yang sekarang tetap berlaku."
            ),
            "Kamu bisa mengunduh atau menghapus datamu di Pengaturan kapan saja.",
        ],
        "button": "Baca kebijakan privasi yang baru",
        "footer": (
            "Email ini dikirim ke {email} karena kamu punya akun prepza. Ini pemberitahuan "
            "tentang cara kami menggunakan datamu, jadi selalu dikirim apa pun pengaturan "
            "emailmu."
        ),
    },
    "legal_dpa": {
        "subject": "Perjanjian pemrosesan data baru mulai {date}",
        "preheader": "Perjanjian yang baru berlaku untuk perusahaanmu mulai {date}.",
        "heading": "Kami memperbarui perjanjian pemrosesan data kami",
        "lines": [
            (
                "Kami telah menerbitkan versi baru perjanjian pemrosesan data yang menjadi dasar "
                "prepza memproses data kandidatmu. Versi ini berlaku mulai {date}; sampai saat "
                "itu, versi yang sekarang tetap berlaku."
            ),
            (
                "Perusahaan yang keberatan dengan alasan perlindungan data yang wajar dapat "
                "berhenti menggunakan prepza dan menghapus perusahaannya sebelum tanggal itu."
            ),
        ],
        "button": "Baca perjanjian yang baru",
        "footer": (
            "Email ini dikirim ke {email} karena kamu pemilik atau admin sebuah perusahaan di "
            "prepza. Ini pemberitahuan tentang perjanjian kami dengan perusahaanmu, jadi "
            "selalu dikirim apa pun pengaturan emailmu."
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
        "open_site": "Buka prepza",
        "footer": (
            "Email ini dikirim ke {email} karena kamu memilih menerima pembaruan produk dan berita"
            " dari prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Buka prepza",
        "footer": (
            "Email ini dikirim ke {email} karena kamu memilih menerima penawaran dan promosi dari"
            " prepza."
        ),
    },
    # An important notice: a service email about prepza itself (a security incident, planned
    # downtime, a change to how it works), whatever the email settings; never a promotion.
    "notices": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Buka prepza",
        "footer": (
            "Email ini dikirim ke {email} karena kamu punya akun prepza. Ini pemberitahuan"
            " penting tentang layanan, seperti keamanan atau ketersediaannya, jadi selalu"
            " dikirim apa pun pengaturan emailmu."
        ),
    },
    "top_up_failed": {
        "subject": "Isi ulang otomatis gagal: {company}",
        "preheader": "Kartu tidak dapat ditagih. Isi ulang untuk terus mengundang kandidat.",
        "heading": "Isi ulang otomatis gagal",
        "lines": [
            (
                "Isi ulang otomatis gagal menagih kartu untuk {company}, jadi tidak ada "
                "kredit yang ditambahkan."
            ),
            (
                "Isi ulang untuk terus mengundang kandidat. Isi ulang otomatis akan mencoba"
                " kartu itu lagi nanti."
            ),
        ],
        "button": "Isi ulang",
        "footer": (
            "Email ini dikirim ke {email} karena kamu pemilik atau admin {company} di "
            "prepza. Email ini tentang penagihan perusahaanmu, jadi selalu dikirim apa pun "
            "pengaturan emailmu."
        ),
    },
    "top_up_paused": {
        "subject": "Isi ulang otomatis dijeda: {company}",
        "preheader": "Kartu ditolak. Perbarui kartu untuk menyalakan lagi isi ulang otomatis.",
        "heading": "Isi ulang otomatis dijeda",
        "lines": [
            (
                "Kartu untuk isi ulang otomatis {company} ditolak, dan mencoba lagi tidak akan "
                "membantu, jadi isi ulang otomatis dijeda dan tidak akan menagih kartu itu."
            ),
            (
                "Perbarui kartu di halaman tagihan untuk menyalakan lagi isi ulang otomatis. "
                "Sementara itu, isi ulang secara manual untuk terus mengundang kandidat."
            ),
        ],
        "button": "Perbarui kartu",
        "footer": (
            "Email ini dikirim ke {email} karena kamu pemilik atau admin {company} di "
            "prepza. Email ini tentang penagihan perusahaanmu, jadi selalu dikirim apa pun "
            "pengaturan emailmu."
        ),
    },
    "top_up_on": {
        "subject": "Isi ulang otomatis menyala: {company}",
        "preheader": (
            "{price} ditambah pajak setiap kali saldo tersedia turun di bawah {threshold, "
            "plural, other {# kredit}}."
        ),
        "heading": "Isi ulang otomatis menyala",
        "lines": [
            (
                "Isi ulang otomatis sekarang menyala untuk {company}. Setiap kali saldo "
                "tersedianya turun di bawah {threshold, plural, other {# kredit}}, kartu yang "
                "tersimpan ditagih {price}, ditambah PPN atau pajak penjualan jika berlaku, "
                "sampai isi ulang otomatis dimatikan."
            ),
            (
                "Setiap tagihan dikirim lewat email ke pemilik dan admin perusahaan, dan Paddle, "
                "penjual kembali kami, mengirim tanda terimanya lewat email."
            ),
            (
                "Untuk mematikannya, buka isi ulang otomatis di halaman tagihan lalu pilih "
                "“Matikan”. Isi ulang otomatis langsung berhenti, dan tidak ada tagihan lagi."
            ),
        ],
        "button": "Buka tagihan",
        "footer": (
            "Email ini dikirim ke {email} karena kamu pemilik atau admin {company} di prepza. "
            "Email ini tentang penagihan perusahaanmu, jadi selalu dikirim apa pun pengaturan "
            "emailmu."
        ),
    },
    "top_up_charged": {
        "subject": "Isi ulang otomatis menagih: {company}",
        "preheader": "{price} untuk {credits, plural, other {# kredit}} pada {date}.",
        "heading": "Isi ulang otomatis menagih kartu",
        "lines": [
            (
                "Pada {date}, isi ulang otomatis menagih kartu untuk {company} sebesar {price}, "
                "termasuk pajak, dan menambahkan {credits, plural, other {# kredit}}. {company} "
                "sekarang memiliki {available, plural, other {# kredit tersedia}}."
            ),
            "Paddle, penjual kembali kami, mengirim tanda terimanya lewat email.",
            (
                "Untuk menghentikan tagihan ini, buka isi ulang otomatis di halaman tagihan lalu "
                "pilih “Matikan”. Isi ulang otomatis langsung berhenti, dan tidak ada tagihan "
                "lagi."
            ),
        ],
        "button": "Buka tagihan",
        "footer": (
            "Email ini dikirim ke {email} karena kamu pemilik atau admin {company} di prepza. "
            "Email ini tentang penagihan perusahaanmu, jadi selalu dikirim apa pun pengaturan "
            "emailmu."
        ),
    },
    "top_up_price_change": {
        "subject": "Harga isi ulang baru untuk {company}",
        "preheader": "Mulai {date}, setiap isi ulang otomatis berharga {new_price}, bukan {price}.",
        "heading": "Harga isi ulang otomatis berubah",
        "lines": [
            (
                "Mulai {date}, setiap isi ulang otomatis untuk {company} berharga {new_price}, "
                "bukan {price}, ditambah PPN atau pajak penjualan jika berlaku. Jumlah "
                "kandidatnya tetap sama."
            ),
            (
                "Tagihan sebelum tanggal itu tetap {price}. Jika kamu ingin jumlah lain, ubah "
                "atau matikan isi ulang otomatis di halaman tagihan sebelum {date}."
            ),
        ],
        "button": "Buka tagihan",
        "footer": (
            "Email ini dikirim ke {email} karena kamu pemilik atau admin {company} di "
            "prepza. Email ini tentang penagihan perusahaanmu, jadi selalu dikirim apa pun "
            "pengaturan emailmu."
        ),
    },
    "footer": "Email ini dikirim ke {email} karena seseorang mengundang alamat ini di prepza. "
    "Jika kamu tidak mengharapkannya, abaikan saja.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza belum memverifikasi {company}.",
    "paste_link": "Atau tempel tautan ini di browsermu",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Berhenti berlangganan",
    "email_settings": "Ubah pengaturan email",
    "stop_reminders": "Jangan kirimi saya pengingat untuk wawancara ini",
    "stop_company": "Jangan kirimi saya email dari {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza dijalankan oleh {name}, {address}.",
}
