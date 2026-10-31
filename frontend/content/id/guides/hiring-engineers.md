---
title: "Cara merekrut engineer: proses terstruktur dari deskripsi pekerjaan hingga penawaran"
seoTitle: "Cara Rekrut Software Engineer: Proses Rekrutmen Terstruktur"
description: "Langkah merekrut software engineer: profil jabatan, penyaringan, tes pengetahuan, coding, system design, wawancara terstruktur, dan penawaran kerja."
updated: "2026-10-29"
---

# Cara merekrut engineer: proses terstruktur dari deskripsi pekerjaan hingga penawaran

Merekrut engineer itu mahal dengan cara yang mudah terlewat: sebagian besar biayanya adalah waktu engineer-mu sendiri. Setiap jam yang mereka habiskan untuk mewawancarai orang yang tidak menguasai stack-nya adalah satu jam yang tidak mereka pakai untuk membangun produk. Proses yang baik menaruh pemeriksaan yang murah dan luas di awal, dan menyimpan pemeriksaan yang mahal dan mendalam untuk sedikit orang yang kemungkinan besar berhasil.

Panduan ini membahas proses tersebut langkah demi langkah. Panduan ini bersandar pada riset rekrutmen di bagian yang risetnya jelas, dan menyebutkannya saat risetnya belum jelas.

## Gambaran singkat prosesnya

| Tahap | Apa yang diperiksa | Siapa yang meluangkan waktu |
| --- | --- | --- |
| 1. Profil jabatan dan deskripsi pekerjaan | Apa yang benar-benar dibutuhkan pekerjaan | Hiring manager, seorang senior engineer |
| 2. Penyaringan CV atau lamaran | Hanya syarat wajib | Rekruter atau hiring manager |
| 3. Tes pengetahuan | Apa yang diketahui kandidat tentang stack-mu | Kandidat; kamu membaca hasilnya |
| 4. Take-home atau live coding | Apakah mereka bisa menulis kode yang berjalan | Satu atau dua engineer |
| 5. System design (posisi senior) | Cara mereka bernalar tentang sistem yang lebih besar | Seorang senior engineer |
| 6. Wawancara perilaku terstruktur | Cara mereka bekerja dengan orang lain | Hiring manager, rekan setim |
| 7. Pemeriksaan referensi | Mengonfirmasi apa yang sudah kamu dengar | Hiring manager |
| 8. Keputusan dan penawaran | Keputusan yang adil dan terdokumentasi | Tim rekrutmen |

## Apa kata riset

Tinjauan besar atas riset rekrutmen membandingkan metode berdasarkan seberapa kuat hasilnya berkaitan dengan kinerja kerja di kemudian hari. Tinjauan besar terbaru, oleh Sackett, Zhang, Berry, dan Lievens (2022), merevisi perkiraan sebelumnya ke bawah dan menemukan bahwa prediktor terkuat secara rata-rata semuanya adalah ukuran yang spesifik untuk pekerjaan ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Perkiraan mereka, pada skala di mana 0 berarti tidak ada hubungan dan 1 berarti hubungan sempurna:

| Metode | Perkiraan validitas |
| --- | --- |
| Wawancara terstruktur | .42 |
| Tes pengetahuan kerja | .40 |
| Tes sampel kerja | .33 |
| Wawancara tidak terstruktur | .19 |
| Lama pengalaman kerja | .07 |

Ada tiga pelajaran untuk rekrutmen engineering:

- **Struktur lebih penting daripada format.** Wawancara yang sama dengan pertanyaan yang ditetapkan dan panduan penilaian jauh lebih prediktif daripada percakapan tidak terstruktur.
- **Lama pengalaman saja tidak banyak bicara.** "Lima tahun Java" adalah sinyal lemah dibandingkan apa yang benar-benar diketahui dan bisa dilakukan seseorang.
- **Gabungkan metode.** Tidak ada satu metode pun yang cukup prediktif untuk berdiri sendiri.

Ini adalah rata-rata dari banyak pekerjaan dan studi, bukan jaminan untuk posisimu. Para penulis juga mencatat bahwa tes pengetahuan dan sampel kerja cocok untuk posisi yang kandidatnya diharapkan sudah punya pelatihan atau pengalaman. Itu sesuai dengan sebagian besar rekrutmen engineering, tetapi tidak untuk program magang.

## Langkah 1: Tulis profil jabatan dan deskripsi pekerjaan yang jelas

Sebelum memasang lowongan apa pun, tuliskan apa yang akan dikerjakan orang itu dalam enam bulan pertamanya dan apa yang wajib ia ketahui di hari pertama. Buat spesifik:

- **Wajib tahu:** "Menulis dan meninjau query PostgreSQL, termasuk join dan index" bisa diuji. "Kemampuan database yang kuat" tidak.
- **Akan dipelajari sambil bekerja:** alat internal, domain bisnismu, bagian stack yang akan kamu ajarkan.
- **Level:** apa yang membedakan rekrutan level menengah dari senior di timmu, seperti memegang satu layanan secara penuh atau memimpin keputusan desain.

Sepakati ini dengan semua orang yang terlibat dalam rekrutmen. Lalu tulis deskripsi pekerjaan berdasarkan itu. Deskripsi pekerjaan yang sesuai dengan pekerjaan nyata menarik orang yang tepat dan membuat setiap langkah berikutnya lebih mudah disiapkan, karena setiap tes dan wawancara bisa ditelusuri kembali ke sana.

Buat daftar "nilai plus" tetap pendek. Daftar persyaratan yang panjang membuat orang yang memenuhi syarat mundur karena tidak mencentang semua kotak.

## Langkah 2: Saring CV hanya untuk syarat wajib

Gunakan CV atau lamaran untuk pemeriksaan ya-atau-tidak: izin kerja, lokasi atau zona waktu kalau posisinya membutuhkannya, bahasa yang disyaratkan, dan syarat wajib lain yang memang tidak bisa ditawar.

Jangan memeringkat orang berdasarkan CV mereka. Jabatan, nama perusahaan sebelumnya, dan lama pengalaman adalah prediktor yang lemah, dan CV sulit dibandingkan secara adil: CV yang kuat bisa mencerminkan kemampuan menulis yang baik sama besarnya dengan kerja yang baik. Perlakukan CV sebagai filter untuk hal-hal yang tidak bisa diuji, dan teruskan semua yang lolos ke tes pengetahuan.

## Langkah 3: Jalankan tes pengetahuan singkat

Inilah langkah yang paling banyak menghemat waktu engineer-mu. Sebelum siapa pun menghabiskan satu jam dalam wawancara langsung, periksa apa yang diketahui setiap kandidat tentang stack-mu.

Tes pengetahuan yang baik itu:

- **Spesifik untuk pekerjaan:** menguji bahasa pemrograman, framework, database, dan praktik dalam profil jabatanmu, bukan pengetahuan umum yang remeh.
- **Singkat:** beberapa topik dengan sekitar 10 soal masing-masing, supaya kandidat kuat yang punya tawaran lain tetap menyelesaikannya.
- **Sama untuk semua orang:** topik yang sama, jumlah soal yang sama, dan batas waktu yang sama.

Di sinilah testee berperan. testee mengubah deskripsi pekerjaanmu menjadi wawancara pengetahuan pilihan ganda berbatas waktu. Kamu meninjau topik yang diusulkan sebelum ada soal yang ditulis, jadi tesnya mencakup stack-mu dan bukan yang lain. Untuk posisi engineering, itu bisa mencakup:

- **Soal membaca kode:** potongan kode singkat dengan pertanyaan tentang apa yang dicetak atau dikembalikannya, apa fungsinya, kenapa gagal, atau perubahan mana yang memperbaikinya.
- **SQL:** tabel kecil dan sebuah query, dengan pertanyaan baris mana yang dikembalikan.
- **Pengetahuan arsitektur dan framework:** trade-off, perilaku sebuah framework, apa yang bermasalah saat beban tinggi.

Setiap kandidat mendapat set soal acaknya sendiri dengan hitung mundur di setiap soal. Kamu melihat scorecard dengan setiap jawaban dan berapa lama waktunya, plus tanda untuk jawaban yang terlalu cepat, meninggalkan halaman, percobaan menyalin, dan pola yang tidak biasa dalam jawaban serta waktunya. Tanda adalah alasan untuk melihat lebih teliti, bukan bukti apa pun. Laporannya juga menyarankan soal yang dijawab benar oleh kandidat untuk ditanyakan di wawancara berikutnya.

Yang tidak dilakukan testee: kandidat tidak menulis, menjalankan, atau men-debug kode di testee. Membaca kode dan menulisnya adalah keterampilan yang berbeda, jadi langkah berikutnya tetap penting. Lihat [tes keterampilan per posisi](/tests) untuk tes siap pakai sebagai titik awal.

## Langkah 4: Take-home atau live coding

Sekarang periksa apakah kandidat bisa menulis kode yang berjalan. Ini adalah tahap untuk menulis, menjalankan, dan men-debug kode, baik dengan latihanmu sendiri maupun di platform developer. Lihat [alternatif HackerRank](/compare/hackerrank-alternatives) untuk melihat bagaimana tes pengetahuan dan platform coding saling melengkapi.

Dua format yang umum:

- **Tugas take-home:** realistis dan minim tekanan, tetapi menyita waktu malam kandidat. Batasi paling lama beberapa jam, sebutkan berapa lama seharusnya, dan tinjau dengan rubrik tertulis.
- **Live coding:** lebih singkat dan lebih sulit dialihdayakan ke orang lain, tetapi lebih menegangkan. Kerjakan bersama masalah yang realistis, biarkan kandidat memakai bahasa yang paling mereka kuasai, dan nilai cara mereka bernalar, bukan hanya apakah mereka selesai.

Format mana pun, nilai berdasarkan kriteria yang disepakati sebelumnya: kebenaran, keterbacaan, tes, cara menangani kasus tepi (edge case). Karena tes pengetahuan sudah menyaring kelompoknya, kamu menjalankan langkah ini dengan segelintir orang, bukan semua orang.

## Langkah 5: System design untuk posisi senior

Untuk senior engineer, tambahkan diskusi desain: "Bagaimana kamu akan membangun layanan yang melakukan X?" Perhatikan cara mereka mengklarifikasi kebutuhan, memilih di antara trade-off, dan menemukan titik-titik kegagalan. Jarang ada satu jawaban yang benar, jadi rubrik sangat penting. Tuliskan seperti apa jawaban yang lemah, cukup, dan kuat sebelum wawancara pertama.

Lewati langkah ini untuk posisi junior, karena di sana lebih banyak menguji rasa percaya diri daripada keterampilan.

## Langkah 6: Wawancara perilaku terstruktur dengan rubrik

Wawancara terstruktur adalah prediktor tunggal terkuat dalam Sackett dkk. (2022). Terstruktur berarti:

- **Pertanyaan yang sama untuk setiap kandidat,** terkait dengan profil jabatan: "Ceritakan saat kamu tidak setuju dengan sebuah keputusan desain. Apa yang kamu lakukan?"
- **Rubrik penilaian untuk setiap pertanyaan,** dengan contoh jawaban yang lemah, cukup, dan kuat.
- **Skor independen:** setiap pewawancara memberi skor sebelum berdiskusi dengan yang lain, supaya pendapat yang paling lantang tidak menentukan hasil.

Gunakan tahap ini untuk hal-hal yang tidak bisa ditunjukkan tes: kolaborasi, rasa kepemilikan, menerima masukan, berkomunikasi dengan orang non-engineer.

## Langkah 7: Pemeriksaan referensi

Referensi bisa mengonfirmasi apa yang sudah kamu pelajari dan memunculkan kekhawatiran, tetapi perlakukan sebagai pemeriksaan terakhir, bukan tes penentu. Sackett dkk. tidak menghasilkan perkiraan validitas untuk pemeriksaan referensi karena riset yang tersedia terlalu sedikit, jadi bukti tentang seberapa baik referensi memprediksi kinerja masih minim. Kalau kamu melakukannya, ajukan beberapa pertanyaan yang sama tentang perilaku spesifik kepada setiap pemberi referensi.

## Langkah 8: Pengalaman kandidat dan waktu hingga penawaran

Engineer yang kuat sering menjalani beberapa proses rekrutmen sekaligus. Proses yang lambat atau membingungkan membuatmu kehilangan mereka.

- **Jelaskan seluruh proses kepada kandidat sejak awal:** tahapannya, berapa lama masing-masing, dan kapan mereka akan mendapat kabar.
- **Buat tetap singkat.** Jadwalkan tahap-tahap akhir berdekatan, dan putuskan segera setelah wawancara terakhir.
- **Hargai waktu mereka.** Tes pengetahuan singkat di awal berarti lebih sedikit orang yang menjalani wawancara panjang yang kecil kemungkinannya mereka lewati.
- **Beri jawaban tepat waktu kepada semua orang,** termasuk yang tidak kamu lanjutkan.

## Keadilan di sepanjang proses

Proses yang terstruktur juga lebih adil, tetapi hanya kalau dijalankan secara konsisten:

- **Pertanyaan yang konsisten** di setiap tahap, untuk setiap kandidat pada posisi yang sama.
- **Rubrik ditulis sebelumnya,** supaya orang dinilai dengan kriteria yang sama.
- **Akomodasi:** tawarkan tambahan waktu atau format lain kepada kandidat yang memintanya, misalnya karena disabilitas. Di testee, kamu bisa memberi kandidat tambahan waktu sebelum mereka mulai.
- **Pantau hasilnya.** Metode yang berbeda menunjukkan selisih skor antarkelompok yang berbeda. Sackett dkk. menemukan perbedaan rata-rata yang lebih besar untuk tes pengetahuan kerja dan sampel kerja dibanding wawancara terstruktur, yang menjadi satu alasan lagi untuk menggabungkan metode. Pantau tingkat kelulusan di setiap tahap.
- **Manusia yang memutuskan.** Skor mendukung keputusan; skor tidak membuat keputusan. Lihat jawabannya sebelum kamu menolak siapa pun.

Untuk dasar-dasar hukumnya, termasuk AI Act UE (EU AI Act) dan aturan AS tentang tingkat seleksi, lihat [Tes seleksi karyawan](/pre-employment-testing).

## Ringkasan

Taruh pemeriksaan yang luas dan murah di awal, dan yang mendalam dan mahal di akhir. Saring CV untuk syarat wajib, jalankan tes pengetahuan singkat, lalu gunakan waktu engineer untuk coding, desain, dan wawancara terstruktur dengan sedikit orang yang tersisa. Nilai berdasarkan rubrik yang ditulis sebelumnya, dan jaga proses tetap cepat dan jelas.

## Sumber

- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection: Addressing systematic overcorrection for restriction of range. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Bacaan terkait

- [Tes keterampilan per posisi](/tests)
- [Alternatif HackerRank](/compare/hackerrank-alternatives)
- [Panduan tes seleksi karyawan](/pre-employment-testing)
- [Tes keterampilan vs penyaringan CV](/guides/skills-tests-vs-cv-screening)
- [Mewawancarai engineer di era AI](/guides/interviewing-in-the-age-of-ai)
