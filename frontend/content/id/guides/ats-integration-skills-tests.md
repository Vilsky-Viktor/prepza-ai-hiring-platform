---
title: "Cara menghubungkan tes keterampilan ke ATS-mu"
seoTitle: "Cara Menghubungkan Tes Keterampilan ke ATS: Panduan Praktis"
description: "Kirim tes keterampilan dan terima hasilnya lewat ATS-mu secara otomatis, biarkan manusia yang memutuskan, dan ketahui apa yang perlu dicek dulu."
updated: "2026-10-21"
---

# Cara menghubungkan tes keterampilan ke ATS-mu

Sebagian besar tim rekrutmen menyimpan data kandidat di applicant tracking system (ATS) dan menjalankan tes keterampilan di alat lain. Tanpa penghubung di antara keduanya, seseorang menyalin email dari ATS, mengirim undangan secara manual, menunggu, lalu menyalin skornya kembali. Untuk lima kandidat, cara ini masih bisa. Untuk lima puluh, undangan terlambat terkirim, hasil tes menumpuk di tab kedua yang tidak pernah dibuka, dan pelamar yang bagus menerima tawaran lain selagi menunggu.

Panduan ini menjelaskan apa yang dilakukan koneksi yang baik antara ATS dan alat tes, apa yang perlu dicek sebelum mengandalkannya, dan cara mengaturnya agar otomatisasi menangani pekerjaan rutin sementara manusia tetap membuat setiap keputusan rekrutmen.

## Kenapa perlu dihubungkan

| Tanpa koneksi | Dengan koneksi |
| --- | --- |
| Seseorang mengekspor atau menyalin email kandidat | Memindahkan kandidat ke suatu tahap langsung mengirim undangan |
| Undangan dikirim saat ada yang sempat | Undangan terkirim beberapa menit setelah kandidat dipindahkan |
| Hasil tes tinggal di alat tes | Hasil tes muncul di data kandidat di ATS |
| Hiring manager bertanya, "Sudah ada yang mengetesnya?" | ATS menunjukkan siapa yang sudah dites dan bagaimana hasilnya |
| Salah ketik di email dan kandidat yang terlewat | ATS menjadi satu-satunya daftar pelamar |

Kecepatan lebih penting daripada kelihatannya. Makin lama jarak antara melamar dan mendapat kabar, makin banyak kandidat yang mundur atau menerima pekerjaan lain. Angka pastinya sangat bervariasi menurut posisi dan pasar, jadi sikapi angka yang dipublikasikan dengan hati-hati, tetapi arahnya selalu sama: proses yang lambat kehilangan orang, dan pelamar terbaik biasanya punya pilihan paling banyak.

## Seperti apa alur yang baik

Integrasi yang baik mengikuti tahap-tahap yang sudah kamu pakai. Ia tidak membuat proses baru.

1. **Kandidat melamar** dan masuk ke ATS-mu seperti biasa.
2. **Seseorang memindahkannya ke tahap tes,** misalnya "Tes keterampilan". Perpindahan itulah pemicunya, jadi tetap manusia yang memutuskan siapa yang dites.
3. **Alat tes mengirim undangan** secara otomatis, untuk tes yang ditautkan ke lowongan itu.
4. **Kandidat mengerjakan tes** kapan pun ia sempat, sebelum tenggat yang kamu tetapkan.
5. **Hasilnya dicatat di data kandidat di ATS:** skor, lulus atau tidak, tanda integritas jika ada, dan tautan ke semua jawabannya.
6. **Seseorang meninjau hasilnya** lalu meloloskan kandidat ke tahap berikutnya, atau tidak.

Ada dua hal yang sengaja tetap manual: memilih siapa yang dites dan memutuskan langkah selanjutnya. Koneksi hanya menghapus pekerjaan menyalin di antaranya.

### Kenapa tidak dipicu oleh setiap lamaran baru?

Beberapa alat mengundang semua orang yang melamar. Itu bisa cocok untuk posisi dengan volume pelamar tinggi yang semua pelamarnya mengerjakan tes yang sama. Namun tahap tempat kamu memindahkan kandidat lebih mudah dikendalikan: kamu bisa melewati pelamar yang jelas tidak memenuhi syarat wajib (tidak punya izin kerja, lokasi tidak sesuai), dan kamu tidak pernah mengetes, atau membayar untuk, orang yang memang akan kamu tolak.

## Apa yang perlu dicek sebelum memilih integrasi

Tidak semua klaim "terintegrasi dengan ATS-mu" berarti sama. Ajukan pertanyaan-pertanyaan ini sebelum menghubungkan apa pun.

| Pertanyaan | Kenapa penting | Jawaban yang baik |
| --- | --- | --- |
| Bagaimana cara menghubungkannya? | Kata sandi bersama dan akun yang dipegang vendor sulit diaudit atau dicabut | Kunci API atau token yang dibuat perusahaanmu dan bisa dihapus kapan saja |
| Apa yang bisa dilakukan kunci itu? | Kunci dengan akses penuh berisiko jika bocor | Izin sesempit mungkin yang dibutuhkan integrasi, tercantum di dokumentasi |
| Apa yang memicu undangan? | Kamu perlu tahu persis kapan kandidat menerima email | Tahap tertentu yang kamu pilih untuk tiap lowongan |
| Di mana hasilnya muncul? | Hasil yang tidak dilihat siapa pun tidak ada gunanya | Di profil kandidat, sebagai catatan atau komentar yang sudah biasa dibaca timmu |
| Apa yang terjadi jika undangan gagal? | Kredit habis, salah ketik, akun dijeda: kandidat tertahan tanpa ada yang tahu | Ada yang diberi tahu, dan kandidat bisa diundang lagi |
| Bisakah satu peristiwa diproses dua kali? | ATS mengirim ulang peristiwa; kandidat tidak boleh mendapat dua undangan | Setiap kandidat diundang sekali per tes, berapa kali pun peristiwanya datang |
| Bagaimana peristiwa yang masuk diverifikasi? | Alamat yang tidak diverifikasi bisa dikirimi peristiwa palsu | Permintaan bertanda tangan yang dicek oleh alat itu |
| Berapa lama data kandidat disimpan? | Undang-undang privasi seperti GDPR mengharuskan masa simpan yang jelas | Batas waktu yang dinyatakan, dan penghapusan saat kamu menghapus lowongan, tes, atau akunmu |
| Berapa biayanya? | Paket per pengguna bisa membuat otomatisasi jadi mahal | Biaya yang bisa kamu perkirakan per kandidat yang dites |

Jika vendor tidak bisa menjawab pertanyaan soal kegagalan dan duplikat dengan jelas, bersiaplah mengetahuinya dengan cara yang sulit.

### Perlindungan data

Menghubungkan dua sistem berarti data kandidat, setidaknya nama dan email, berpindah antara dua perusahaan. Menurut GDPR dan undang-undang serupa, vendor tesmu biasanya berperan sebagai pemroses data, jadi kamu perlu perjanjian pemrosesan data dan sebaiknya memberi tahu kandidat, di pemberitahuan privasi atau di undangan, bahwa tes keterampilan adalah bagian dari proses. Bagikan hanya data yang benar-benar dibutuhkan tes. Untuk sisi hukum tes dan AI dalam rekrutmen, lihat [Apakah rekrutmen dengan AI legal di UE?](/guides/is-ai-hiring-legal-in-the-eu)

## Daftar periksa pengaturan

Sebelum mengaktifkannya untuk lowongan sungguhan:

1. **Buat tahap khusus untuk tes** di ATS-mu, misalnya "Tes keterampilan". Jangan memakai ulang tahap yang punya arti lain, atau kandidat akan terundang tanpa sengaja.
2. **Buat kunci dari akun admin** yang bisa melihat semua lowongan yang ingin kamu tautkan, hanya dengan izin yang tercantum di dokumentasi.
3. **Tautkan setiap lowongan ke tesnya** dan pilih tahap yang memicu undangan.
4. **Atur webhook-nya** jika ATS-mu mengharuskannya secara manual, lalu tempel secret-nya di tempat yang diminta alat itu.
5. **Uji coba dengan dirimu sendiri.** Tambahkan kandidat dengan emailmu sendiri, pindahkan ke tahap itu, kerjakan tesnya, dan cek apakah catatannya muncul di ATS.
6. **Tentukan siapa yang memantau kegagalan:** siapa yang diberi tahu saat undangan tidak bisa dikirim, dan siapa yang membereskannya.
7. **Sepakati cara membaca hasil.** Batas lulus adalah panduan, bukan penolakan otomatis. Putuskan ini sebelum hasil masuk, bukan sesudahnya.

## Kesalahan umum

- **Mengotomatiskan keputusan, bukan pekerjaan administratifnya.** Menolak otomatis semua kandidat di bawah skor tertentu menghilangkan pengecekan manusia yang bisa menangkap soal yang buruk atau kandidat yang mengalami gangguan koneksi. Biarkan skor yang mengurutkan; biarkan manusia yang memutuskan.
- **Memicu dari tahap yang salah.** Tahap yang dipakai rekruter untuk keperluan lain akan mengirim tes ke orang yang seharusnya tidak menerimanya.
- **Satu tes untuk semua lowongan.** Koneksi membuat pengiriman tes yang sama ke mana-mana jadi mudah. Tes paling berguna jika dibuat untuk posisi yang bersangkutan. Lihat [Tes keterampilan vs penyaringan CV](/guides/skills-tests-vs-cv-screening).
- **Tidak ada yang memantau kegagalan.** Jika undangan gagal diam-diam, kandidat menunggu email yang tidak pernah datang, dan kamu mengira ia mengabaikannya.
- **Kunci yang terikat pada orang yang keluar.** Beberapa kunci ATS bertindak atas nama orang yang membuatnya. Saat akun orang itu ditutup, koneksinya berhenti. Gunakan akun yang akan tetap ada, dan hubungkan ulang saat ada pergantian peran.
- **Melupakan kandidat di luar ATS.** Kandidat rujukan dan pelamar langsung yang tidak pernah masuk ATS tetap perlu diundang. Sediakan juga cara manual untuk mengundang mereka.

## Cara prepza melakukannya

prepza terhubung dengan **Workable, Greenhouse, Teamtailor, Recruitee, dan Breezy HR**, dan mengikuti alur di atas.

- **Kuncimu, kendalimu.** Pemilik atau admin menghubungkan ATS di tab Integrasi perusahaan dengan kunci yang dibuat perusahaanmu di ATS. prepza mengeceknya sebelum menyimpan, menyimpannya dalam bentuk terenkripsi, dan tidak pernah menampilkannya lagi. Memutus koneksi langsung menghapus kunci dan lowongan yang ditautkan.
- **Tautkan lowongan ke wawancara.** Pilih lowongan di ATS dan tahap yang memicu undangan, lalu tautkan ke wawancara prepza yang sudah ada atau buat yang baru dari teks lowongan di ATS. Kamu meninjau topiknya sebelum satu soal pun ditulis.
- **Pindahkan kandidat, undangan terkirim.** Setiap kandidat diundang sekali per wawancara, meskipun ATS mengirim peristiwa yang sama dua kali.
- **Hasil kembali ke ATS.** Saat kandidat selesai, prepza menambahkan catatan atau komentar padanya di ATS berisi nilainya, lulus atau tidak, tanda integritas jika ada (meninggalkan halaman, upaya menyalin, jawaban yang dipilih terlalu cepat untuk sempat membaca soal), dan tautan ke scorecard-nya beserta semua jawaban.
- **Kegagalan tidak luput dari perhatian.** Jika kandidat tidak bisa diundang, misalnya karena kredit perusahaan habis, batas email tercapai, atau undangan dijeda sementara oleh prepza, semua anggota perusahaan mendapat notifikasi yang menyebut nama ATS-nya. Kandidat yang tidak terundang karena kredit habis akan diundang otomatis setelah isi ulang, dan kandidat yang menunggu di lowongan mana pun bisa diundang lagi dengan satu klik.
- **Slack, jika kamu memakainya.** prepza bisa mengirim notifikasi, misalnya kandidat yang sudah selesai atau kandidat dari ATS yang tidak bisa diundang, ke channel Slack pilihanmu.
- **Platformmu sendiri.** Jika ATS-mu tidak ada di daftar, [API](/api-docs) prepza memungkinkanmu mengundang kandidat dengan kunci API dan menerima webhook bertanda tangan saat kandidat mulai, selesai, atau dihapus, saat undangannya tidak sampai atau kedaluwarsa, dan saat wawancara siap.
- **Data disimpan untuk jangka waktu tertentu.** Kandidat yang disimpan dari ATS dihapus setelah 365 hari, atau lebih awal bersama wawancara atau perusahaannya.

Beberapa ATS memerlukan satu langkah di sisi mereka. Greenhouse, Teamtailor, dan Recruitee memintamu menambahkan webhook secara manual; dialog Petunjuk di prepza menampilkan alamatnya dan tempat menempel secret-nya. prepza mengatur sendiri webhook Workable dan Breezy HR.

Harganya per kandidat, tanpa langganan: kamu hanya membayar untuk kandidat yang menjawab setidaknya satu soal, $5 per kandidat pada isi ulang $50, $4 mulai dari isi ulang $200, $3 mulai dari isi ulang $600, dan $2 mulai dari isi ulang $1.000. Harga dalam dolar AS, dalam euro di Eropa (angka yang sama), dan dalam pound di Inggris Raya (£4 hingga £1,50); PPN (VAT) atau pajak penjualan ditangani saat checkout. Menghubungkan ATS dan membuat wawancara gratis, dan 3 kandidat pertama dari perusahaan pertamamu gratis. Lihat [harga](/pricing).

## Bacaan terkait

- [Cara menyaring 100 pelamar dalam sehari](/guides/screen-100-applicants-in-a-day)
- [Tes keterampilan vs penyaringan CV](/guides/skills-tests-vs-cv-screening)
- [Tes seleksi karyawan: panduan praktis](/pre-employment-testing)
