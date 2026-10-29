# The FAQ in id; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Apa itu prepza?",
        "answer": "Wawancara berbatas waktu yang dibuat dari deskripsi pekerjaanmu, untuk posisi apa pun. Gunakan untuk menyaring kandidat sebelum kamu bertemu mereka, atau sebagai salah satu tahap rekrutmen itu sendiri: dengan cara mana pun, kamu melihat siapa yang benar-benar menguasai pekerjaannya.",
    },
    {
        "key": "roles",
        "question": "Untuk posisi apa saja aku bisa merekrut?",
        "answer": "Posisi apa pun yang membutuhkan pengetahuan: customer support, sales, keuangan, kesehatan, teknisi lapangan, engineering, pemasaran, dan lainnya. Jika kamu bisa menjelaskan pekerjaannya, prepza bisa membuat wawancara untuknya.",
    },
    {
        "key": "hiring",
        "question": "Bagaimana cara kerjanya?",
        "answer": "Tempel deskripsi pekerjaan di beranda, beri nama perusahaanmu, dan periksa topik yang diusulkan prepza. Lalu undang kandidat: ketik email mereka, tempel daftar, atau unggah file. Kandidat yang belum mulai setelah beberapa hari mendapat satu pengingat. Setiap kandidat mendapat soalnya sendiri dengan batas waktu di tiap soal, dan kamu melihat skor serta setiap jawabannya begitu mereka selesai.",
    },
    {
        "key": "link",
        "question": "Bisakah aku memasang wawancara di iklan lowongan?",
        "answer": "Bisa. Aktifkan tautan wawancara yang bisa dibagikan di tab pengaturannya, lalu tempel di iklanmu. Siapa pun yang membukanya masuk dan mengikuti wawancara, dan setiap orang dikenai biaya seperti kandidat yang diundang. Tautan nonaktif saat kamu menandai wawancara dengan status Diterima.",
    },
    {
        "key": "preview",
        "question": "Bisakah aku mencoba wawancara sebelum mengundang siapa pun?",
        "answer": "Bisa. Buka wawancaramu sebagai kandidat dari halamannya, gratis: pratinjau tidak muncul di antara kandidatmu atau di statistik soal. Kamu juga bisa mengikuti wawancara latihan gratis mana pun.",
    },
    {
        "key": "cheating",
        "question": "Bisakah kandidat memakai AI atau mencari jawabannya?",
        "answer": "Setiap kandidat mendapat soal acak sendiri dengan urutan sendiri, dengan [batas waktu di tiap soal](/guides/skills-test-timing-and-extra-time) yang dijaga server kami, jadi hanya ada sedikit waktu untuk mencari jawaban atau bertanya ke AI. Scorecard juga menunjukkan saat kandidat meninggalkan halaman, menyalin teks, atau menjawab terlalu cepat untuk sempat membaca soal. Setelah selesai, halamannya juga menunjukkan pola jawaban yang biasanya muncul saat soal diteruskan ke AI, seperti waktu yang kira-kira sama di setiap soal atau soal sulit benar sementara soal mudah salah, dan menyarankan soal yang dijawab benar oleh kandidat untuk ditanyakan dalam wawancara langsung. Pola adalah alasan untuk bertanya, bukan bukti. Sebelum mulai, setiap kandidat juga mengonfirmasi akan menjawab sendiri, tanpa alat AI atau bantuan orang lain, dan scorecard-nya menunjukkan hal itu.",
    },
    {
        "key": "cost",
        "question": "Berapa biayanya?",
        "answer": "Membuat wawancara gratis. Setiap kandidat yang menjawab setidaknya satu soal seharga {candidate} kredit ({candidate_price}), dan lebih murah dengan kredit dari isi ulang yang lebih besar, hingga {cheapest_price}. Perusahaan pertamamu mendapat {company} kredit gratis, cukup untuk {company_candidates} kandidat pertamanya. [Halaman harga](/pricing) mencantumkan semua harga.",
    },
    {
        "key": "charged",
        "question": "Kapan kandidat dikenai biaya?",
        "answer": "Asalkan ia sudah menjawab setidaknya satu pertanyaan: saat wawancaranya berakhir (ia menyelesaikannya, atau waktunya habis saat ia tidak ada), atau saat kamu mencabutnya. Pertanyaan yang waktunya habis tanpa jawaban yang dipilih tidak dihitung. Kreditnya disisihkan saat kamu mengundangnya, dan kembali jika kamu mencabutnya sebelum ia menjawab apa pun, jika ia tidak pernah mulai, atau jika wawancaranya berakhir tanpa ada yang dijawab.",
    },
    {
        "key": "compare_hiring",
        "question": "Bagaimana harganya dibanding alat asesmen lain?",
        "answer": "Banyak alat asesmen dijual sebagai langganan bulanan atau tahunan yang tetap dibayar meski kamu tidak menguji siapa pun. Di prepza kamu hanya membayar per kandidat: {candidate} kredit ({candidate_price}), tanpa kontrak, tanpa biaya per pengguna, dan tanpa biaya untuk membuat wawancara. Perusahaan yang mengundang {example_candidates} kandidat per bulan membayar sekitar {example_year_price} per tahun. Jika kamu menguji banyak kandidat setiap bulan, langganan bisa lebih murah, jadi bandingkan dengan angkamu sendiri.",
    },
    {
        "key": "expire",
        "question": "Apakah kredit bisa kedaluwarsa?",
        "answer": "Tidak. Kredit tidak pernah kedaluwarsa, dan tidak ada langganan berbayar. Jika Anda menyalakan isi ulang otomatis yang opsional, Paddle menyimpan kartu Anda sebagai langganan {zero_price}; Anda hanya membayar isi ulang yang dilakukannya.",
    },
    {
        "key": "currency",
        "question": "Saya membayar dalam mata uang apa?",
        "answer": "Harga dalam mata uang lokal di Kanada, Australia, Israel, Polandia, Swiss, Jepang, Korea Selatan, Taiwan, Hong Kong, Thailand, Singapura, dan India; dalam euro di negara UE lainnya serta di Islandia, Liechtenstein, dan Norwegia; dalam pound di Inggris; dan dalam dolar AS di tempat lain. Akunmu dan setiap perusahaan tetap memakai mata uang negara tempat mereka dibuat, ke mana pun kamu bepergian: ubah mata uangmu di Pengaturan, dan mata uang perusahaan di samping tombol Isi ulang miliknya (pemilik dan admin). Isi ulang sebuah perusahaan, termasuk yang otomatis, selalu ditagih dalam mata uang perusahaan itu.",
    },
    {
        "key": "refunds",
        "question": "Bisakah aku mendapat pengembalian dana?",
        "answer": "Bisa, untuk kredit yang kamu beli dalam 14 hari terakhir dan belum dipakai: lewat Paddle atau dengan menulis kepada kami. Kredit gratis, seperti hadiah sambutan, tidak dikembalikan. Rinciannya ada di [ketentuan](/terms).",
    },
    {
        "key": "scorecards",
        "question": "Apa yang ditampilkan scorecard?",
        "answer": 'Setiap jawaban, apakah benar, dan berapa lama waktunya. Nilai adalah persentase poin yang diperoleh: setiap soal bernilai satu poin, dan soal "pilih semua yang benar" memberi sebagian poinnya untuk setiap opsi benar yang dicentang, dan nol jika ada opsi salah yang dicentang. Nilai tampil hijau atau merah dibanding nilai lulus yang kamu tetapkan untuk wawancara. Scorecard juga menandai jawaban yang terlalu cepat untuk sempat membaca soal, saat kandidat meninggalkan halaman, dan upaya menyalin.',
    },
    {
        "key": "reports",
        "question": "Bisakah aku membagikan hasil ke hiring manager?",
        "answer": "Bisa. Unduh laporan PDF untuk satu kandidat atau semua kandidat sebuah wawancara, kirim lewat email langsung dari prepza, atau kirim ringkasan singkat di WhatsApp, Telegram, Viber, atau LINE.",
    },
    {
        "key": "action_log",
        "question": "Bisakah aku melihat siapa melakukan apa di perusahaanku?",
        "answer": "Bisa, jika kamu pemilik perusahaan. Tab Log tindakan perusahaan itu mencantumkan semua yang dilakukan anggotanya, dari yang terbaru: mengundang atau menghapus kandidat, melihat hasil, serta mengubah wawancara, tim, tagihan, dan integrasi, lengkap dengan siapa yang melakukannya, kapan, dan apakah asisten, aplikasi AI, atau API yang melakukannya atas nama mereka. Kamu bisa memfilternya berdasarkan anggota, jenis tindakan, dan tanggal. Tindakan disimpan selama 12 bulan.",
    },
    {
        "key": "integrations",
        "question": "Apakah prepza bisa dipakai dengan ATS atau tools lain yang saya gunakan?",
        "answer": "Bisa, tanpa biaya tambahan. Hubungkan Workable, Greenhouse, Teamtailor, Recruitee, atau Breezy HR di tab Integrasi perusahaanmu: kandidat yang kamu pindahkan ke suatu tahap mendapat wawancara, dan hasilnya dikirim kembali ke ATS ([cara menghubungkan tes keterampilan ke ATS-mu](/guides/ats-integration-skills-tests)). Slack bisa memposting notifikasi perusahaanmu ke sebuah channel, dan API memungkinkan platformmu sendiri membuat wawancara, mengundang dan mengelola kandidat, serta menerima hasil mereka, dengan setiap kunci API terbatas pada yang kamu centang untuknya; lihat [Dokumentasi API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Bisakah saya memakai prepza dari Claude, ChatGPT, atau agen AI saya sendiri?",
        "answer": "Bisa. Tambahkan prepza ke Claude atau ChatGPT sebagai konektor (langkah-langkahnya ada di tab Integrasi perusahaanmu), lalu izinkan di prepza. Setelah itu, aplikasi bekerja dengan perusahaan, wawancara, dan hasil kandidatmu atas namamu, dengan hak aksesmu; sebagian besar aplikasi bertanya dulu sebelum mengubah apa pun. Akun atau perusahaan hanya bisa dihapus di prepza. Apa yang dibaca aplikasi sampai ke penyedianya sesuai ketentuan aplikasi tersebut. Kamu bisa memutuskan sambungannya kapan saja di tab yang sama. Aplikasi AI lain dan agen yang kamu buat sendiri juga bisa terhubung: [tab MCP](/api-docs?tab=mcp) di dokumentasi pengembang berisi langkah-langkah dan contoh agen, dan agen di server bisa masuk dengan kunci API yang punya hak akses agen AI. [Panduan tentang agen AI, MCP, dan API](/guides/ai-agents-mcp-and-api) menjelaskan kegunaan masing-masing.",
    },
    {
        "key": "candidates",
        "question": "Apa yang dilihat kandidat?",
        "answer": "Nama dan logo perusahaanmu, dengan warna dan font perusahaanmu (diatur di tab Merek-nya), apa yang bisa diharapkan sebelum mulai, lalu satu soal berbatas waktu setiap kalinya. Mereka tidak pernah melihat skornya atau apakah jawabannya benar.",
    },
    {
        "key": "verified",
        "question": "Apa arti tanda centang terverifikasi?",
        "answer": "Artinya pemilik atau admin perusahaan masuk dengan email kerja di domain situs perusahaan, misalnya you@acme.com, lalu tim kami meninjau perusahaan tersebut. Tambahkan situsnya lewat Verifikasi di header perusahaanmu; layanan email gratis tidak dihitung. Selama masih menunggu peninjauan, timmu melihat ikon jam di samping nama, dan mengganti nama perusahaan mengirimnya untuk ditinjau lagi. Tanda centang tampil di samping nama perusahaanmu, termasuk di undangan.",
    },
    {
        "key": "languages",
        "question": "Bahasa apa saja yang didukung?",
        "answer": "{count} bahasa, untuk situs, wawancara, dan email. Pilih bahasa penulisan wawancara, apa pun bahasa deskripsi pekerjaannya.",
    },
    {
        "key": "privacy",
        "question": "Apa yang terjadi pada deskripsi pekerjaan dan jawaban?",
        "answer": "Deskripsi pekerjaan dipakai untuk membuat wawancara perusahaanmu, dan jawaban kandidat untuk menilainya bagi perusahaanmu. Soal yang dibuat prepza juga dapat digunakan kembali dalam wawancara dan latihan perusahaan lain, tanpa apa pun yang mengidentifikasi kamu, perusahaanmu, atau orang lain; kamu bisa mengecualikan soal suatu wawancara dari hal ini di pengaturannya. prepza juga mempelajari pola umum kualitas soal yang dianonimkan dari cara soal dijawab, untuk meningkatkan cara soal dibuat. [Kebijakan privasi](/privacy) menjelaskan apa yang kami simpan, berapa lama, dan hak setiap orang.",
    },
    {
        "key": "eu_ai_law",
        "question": "Apakah legal memakai AI untuk menyaring kandidat di UE?",
        "answer": "Ya, dengan aturan. Menurut EU AI Act, alat yang menilai kandidat sangat mungkin tergolong berisiko tinggi, dengan kewajiban mulai 2 Desember 2027, dan GDPR sudah berlaku: keputusan perekrutan diambil oleh manusia, kandidat diberi tahu bahwa AI digunakan, dan catatan disimpan. prepza bekerja seperti itu: AI menulis soal, orang-orang di perusahaanmu meninjau hasilnya dan memutuskan, dan kandidat diberi tahu sebelum mulai. Ini bukan nasihat hukum; [Apakah rekrutmen dengan AI legal di UE?](/guides/is-ai-hiring-legal-in-the-eu) menjelaskan aturan dan tanggalnya.",
    },
    {
        "key": "emails",
        "question": "Email apa saja yang dikirim prepza, dan bagaimana cara menghentikannya?",
        "answer": 'Email layanan, seperti undangan, laporan, masalah pembayaran, dan perubahan ketentuan kami, selalu dikirim. Sisanya, seperti ringkasan aktivitas harian, pengingat, dan pembaruan produk, kamu pilih di Pengaturan, bagian Email, atau hentikan dengan tautan "Berhenti berlangganan" di setiap email. Kandidat bisa menghentikan email dari perusahaanmu, atau pengingat sebuah wawancara, lewat tautan di undangan dan pengingat mereka.',
    },
    {
        "key": "delete",
        "question": "Bisakah aku menghapus akunku?",
        "answer": "Bisa, di Pengaturan. Akun dan datamu dihapus, dan sebelumnya kamu bisa mengunduh salinan datamu. Berita prepza muncul di notifikasimu, ikon lonceng di bagian atas; berita penting juga dikirim lewat email sebagai pembaruan produk, hanya selama pengaturan itu aktif.",
    },
    {
        "key": "report",
        "question": "Bagaimana cara melaporkan masalah?",
        "answer": "Tulis pesan kepada kami di [halaman kontak](/contact) dan tempelkan ID hal yang kamu maksud: “salin id” ada di bawah nama perusahaan, wawancara, atau kandidat, dan ID akunmu ada di menu akun serta di Pengaturan. Dengan ID itu, kami langsung menemukannya.",
    },
]
