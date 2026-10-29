---
title: "Agen AI, MCP, dan API: apa itu dan cara memakainya dalam rekrutmen"
seoTitle: "Agen AI, MCP, dan API dalam Rekrutmen: Cara Memakainya"
description: "Apa itu agen AI, MCP, dan API, cara memakainya dengan aman di rekrutmen, dan cara menjalankan prepza dari asisten AI-nya, Claude, ChatGPT, atau platformmu."
updated: "2026-10-22"
---

# Agen AI, MCP, dan API: apa itu dan cara memakainya dalam rekrutmen

Kebanyakan orang pertama kali mengenal AI sebagai jendela chat: kamu bertanya, AI menjawab. Agen AI melangkah lebih jauh. Agen bisa mencari informasi di alat-alat yang kamu pakai dan, saat kamu memintanya, melakukan sesuatu di sana: membuat wawancara, mengundang sederet kandidat, memberi tahu siapa yang nilainya tertinggi minggu lalu. Model Context Protocol (MCP) adalah standar yang memungkinkan chat AI yang sudah kamu pakai, seperti Claude atau ChatGPT, terhubung ke alat-alat seperti itu. Sementara API adalah cara yang lebih lama dan lebih presisi bagi satu perangkat lunak untuk berkomunikasi dengan perangkat lunak lain, tanpa AI di tengahnya.

Panduan ini menjelaskan ketiganya dengan bahasa sederhana: apa gunanya dalam rekrutmen, apa yang perlu diwaspadai, dan cara memakainya bersama prepza.

## Apa itu agen AI

Chatbot hanya menulis teks. Agen adalah model bahasa yang dilengkapi **alat (tools)**: tindakan kecil yang jelas batasannya dan boleh dipanggilnya, seperti "tampilkan kandidat di wawancara ini" atau "undang email ini". Saat kamu bertanya, agen memutuskan alat mana yang dipakai, membaca hasilnya, lalu menjawab berdasarkan hasil itu, bukan dari ingatannya.

| Chatbot | Agen AI |
| --- | --- |
| Menjawab dari apa yang dipelajarinya saat pelatihan | Menjawab dari datamu yang terkini, dibaca lewat alat |
| Hanya bisa menjelaskan cara melakukan sesuatu | Bisa melakukannya, saat kamu meminta dan mengizinkannya |
| Menebak saat tidak tahu | Mencarinya, atau mengatakan bahwa ia tidak bisa |
| Hidup di satu jendela | Bekerja di dalam alat-alat yang kamu hubungkan dengannya |

Alat-alat itulah yang membuat agen berguna, dan juga yang menentukan apakah agen aman atau tidak. Agen yang baik hanya bisa memakai alat yang diberikan kepadanya, hanya dengan izin yang kamu miliki, dan hanya melakukan apa yang kamu minta.

## Apa itu MCP

Model Context Protocol adalah standar terbuka yang diperkenalkan Anthropic pada akhir 2024 dan kini didukung oleh Claude, ChatGPT, serta banyak aplikasi AI dan alat pengembang lainnya. MCP sering diibaratkan port USB-C untuk AI: alih-alih setiap aplikasi AI membangun koneksinya sendiri ke setiap alat, sebuah alat menyediakan satu **server MCP**, dan aplikasi AI mana pun yang mendukung MCP bisa memakainya.

Server MCP memberi tahu aplikasi AI tiga hal:

1. **Alat apa saja yang ada**, dengan nama, deskripsi, dan detail yang dibutuhkan masing-masing.
2. **Alat mana yang hanya membaca** dan mana yang mengubah sesuatu, agar aplikasi AI bisa bertanya kepadamu sebelum ada perubahan.
3. **Siapa kamu**, lewat proses masuk yang kamu setujui sekali, sehingga setiap panggilan berjalan atas namamu, dengan izinmu.

Bagimu, artinya kamu bisa bekerja dengan sebuah alat dari chat yang sudah kamu pakai, tanpa menyalin data dari satu jendela ke jendela lain.

## Apa itu API, dan apa bedanya

API (application programming interface) adalah sekumpulan permintaan tetap yang bisa dikirim satu program ke program lain: "tampilkan kandidat di wawancara ini", "undang email ini". Developer-mu menulis kode yang mengirimkannya. Tidak ada AI yang terlibat: permintaan yang sama selalu menghasilkan hal yang sama, dan itulah yang kamu butuhkan untuk otomatisasi yang berjalan sendiri.

| | Mira, asisten AI (di aplikasi) | MCP (di Claude atau ChatGPT) | API |
| --- | --- | --- | --- |
| Siapa yang memakainya | Kamu, di prepza | Kamu, di chat AI-mu | Kode platformmu |
| Cara meminta | Dengan kata-katamu sendiri | Dengan kata-katamu sendiri | Permintaan tetap yang ditulis developer |
| Siapa yang menyetujui perubahan | Kamu, di sebuah kartu | Kamu, di aplikasi AI-mu | Kodemu, sesuai yang ditulis |
| Paling cocok untuk | Pertanyaan dan tugas singkat | Menggabungkan prepza dengan alat dan file lainnya | Otomatisasi yang berjalan tanpa ada yang mengawasi |
| Masuk sebagai | Kamu | Kamu | Kunci perusahaan |

Pakai Mira atau MCP saat ada orang yang terlibat langsung. Pakai API saat sistemmu sendiri perlu mengundang kandidat dan mengumpulkan hasil secara mandiri, misalnya dari situs karier atau alat HR internal.

## Apa gunanya dalam rekrutmen

Rekrutmen terdiri dari banyak langkah kecil yang berulang dan tersebar di berbagai alat. Justru di situlah agen unggul:

- **Pertanyaan tentang pipeline-mu.** "Kandidat Senior Backend mana yang lulus minggu ini?", "Siapa yang belum memulai wawancaranya?", "Berapa rata-rata nilai kita untuk posisi data analyst?"
- **Menyiapkan sesuatu.** "Buat wawancara dari deskripsi pekerjaan ini", "Atur batas lulus ke 70%", "Beri kandidat ini tambahan waktu 50%."
- **Pekerjaan massal.** "Undang 12 orang ini ke wawancara frontend", langsung ditempel dari email atau spreadsheet.
- **Menggabungkan sumber.** Di Claude atau ChatGPT, kamu bisa memadukan prepza dengan alat dan file lain yang terhubung: membandingkan deskripsi pekerjaan di dokumenmu dengan topik wawancara, atau menyusun draf pesan untuk kandidat yang masuk shortlist.

Yang tidak boleh dilakukannya adalah membuat keputusan rekrutmen. Nilai mendukung penilaian seseorang, bukan menggantikannya. Mintalah agen untuk mengurutkan, merangkum, dan menyiapkan, dan biarkan keputusan tetap di tangan manusia. Lihat [Apakah rekrutmen dengan AI legal di UE?](/guides/is-ai-hiring-legal-in-the-eu) untuk alasan mengapa hal itu juga penting secara hukum.

## Apa yang perlu diwaspadai

Menghubungkan AI ke data rekrutmenmu perlu kehati-hatian yang sama seperti memberi akses kepada rekan kerja.

| Risiko | Yang membantu |
| --- | --- |
| Agen melakukan sesuatu yang tidak kamu maksud | Perubahan perlu persetujuanmu dulu, dan agen hanya melakukan apa yang kamu minta |
| Agen melihat lebih dari yang seharusnya | Agen bertindak atas namamu: ia melihat apa yang kamu lihat, tidak lebih |
| Instruksi tersembunyi di dalam data | Nama, jawaban, dan dokumen kandidat adalah data, bukan instruksi untuk diikuti |
| Rahasia masuk ke chat | Kunci API dan kata sandi tidak pernah lewat chat |
| Kesalahan yang tidak bisa dibatalkan | Menghapus akun atau perusahaan tetap dilakukan di aplikasi, dengan konfirmasinya sendiri |
| Data keluar dari alat-alatmu | Data sampai ke aplikasi AI yang kamu hubungkan, sesuai ketentuan aplikasi itu: hubungkan hanya aplikasi yang diizinkan perusahaanmu |
| Pemakaian yang tidak terkendali | Batas jumlah tindakan yang bisa dijalankan per jam |

Sebelum menghubungkan aplikasi AI apa pun ke data kerja, cek kebijakan perusahaanmu tentang alat AI, dan beri tahu kandidat di pemberitahuan privasimu layanan apa saja yang memproses data mereka.

## Tiga cara bekerja dengan prepza di luar halamannya

### 1. Mira, asisten AI bawaan

Pilih **tanya Mira** di header halaman mana pun. Mira, asisten AI prepza, mengenal perusahaan, wawancara, kandidat, kredit, dan integrasimu, serta cara kerja prepza. Ia menjawab dalam bahasamu, dan kamu bisa mengetik atau berbicara.

- **Ia menjawab dari datamu**, dengan akses yang sama seperti kamu: admin melihat apa yang dilihat admin, pelihat melihat apa yang dilihat pelihat.
- **Ia tahu halaman yang sedang kamu buka.** Tanyakan "Apa yang bisa saya lakukan di halaman ini?" untuk panduan halaman itu, atau "Siapa yang terbaik di sini?" di kandidat sebuah wawancara, dan ia menjawab tentang wawancara itu tanpa bertanya yang mana.
- **Ia menyiapkan perubahan, kamu yang mengonfirmasi.** Saat diminta mengundang kandidat, ia menampilkan kartu berisi persis apa yang akan terjadi, misalnya "Undang 12 kandidat ke Backend developer". Tidak ada yang dijalankan sampai kamu memilih konfirmasi.
- **Ia menunjukkan sumbernya.** Di bawah jawaban, kamu melihat kandidat atau wawancara yang dipakainya dan tautan ke halaman asalnya.
- **Ia tetap pada topik.** Ia menjawab tentang prepza dan rekrutmen dengan prepza, dan menolak hal lainnya.

### 2. prepza di Claude atau ChatGPT, lewat MCP

Kalau kamu sudah bekerja di Claude atau ChatGPT, kamu bisa membawa prepza ke sana. Server MCP prepza menyediakan alat yang sama dengan Mira, asisten bawaan.

**Cara menghubungkan:**

1. Di prepza, buka tab **Integrasi** sebuah perusahaan dan pilih **Aplikasi AI**. Salin alamat servernya: `https://prepza.ai/mcp`.
2. **Di Claude:** buka Settings, lalu Connectors, dan tambahkan custom connector dengan alamat itu. **Di Claude Code:** jalankan `claude mcp add --transport http prepza https://prepza.ai/mcp`. **Di ChatGPT:** tambahkan sebagai custom connector di pengaturan aplikasi dan konektornya.
3. Aplikasi AI-mu membuka halaman masuk prepza. Masuk, cek aplikasi mana yang meminta akses, lalu pilih **Izinkan**. Agar aplikasi ini hanya bisa membaca, matikan dulu **Izinkan perubahan**.

Setelah itu, bertanyalah di chat seperti kamu bertanya kepada rekan kerja: "Di prepza, siapa tiga kandidat teratas untuk Product designer?" Sebagian besar aplikasi AI bertanya kepadamu sebelum melakukan perubahan, dan memperingatkanmu sebelum melakukan apa pun yang tidak bisa dibatalkan: prepza memberi tahu aplikasi tersebut tindakan mana yang mengubah atau menghapus sesuatu.

**Yang tetap sama seperti di aplikasi:**

- **Izinmu.** Ia bertindak atas namamu, di setiap perusahaan tempatmu bergabung, dengan peranmu di masing-masing.
- **Kredit dan batas.** Mengundang kandidat biayanya sama seperti di aplikasi, dan batas email yang sama berlaku.
- **Catatan.** Semua yang dilakukan aplikasi AI untukmu muncul di log tindakan perusahaan sebagai dilakukan melalui aplikasi AI, mulai dari menyetujui topik dan melihat hasil hingga memberi waktu tambahan atau mencabut kandidat. Pemilik perusahaan membacanya di tab **Log tindakan** perusahaan.
- **Perusahaan yang menentukan.** Pemilik dan admin bisa menghentikan aplikasi AI memakai data perusahaan dengan **Izinkan aplikasi AI di perusahaan ini** di halaman aplikasi AI perusahaan.
- **Yang tidak bisa dilakukannya.** Ia tidak bisa melihat kata sandi atau kunci API-mu, dan tidak bisa menghapus akunmu atau perusahaan. Hal-hal itu tetap di aplikasi.

**Untuk memutuskan,** hapus konektornya di aplikasi AI-mu, atau pilih **Putuskan** di sebelahnya di bagian **Aplikasi AI** pada tab Integrasi. Koneksinya langsung berhenti.

**Aplikasi lain dan agenmu sendiri.** [Tab MCP](/api-docs?tab=mcp) di dokumentasi pengembang berisi langkah-langkah untuk Gemini CLI, Cursor, VS Code, dan Le Chat, serta contoh agen lengkap dalam Python dan TypeScript. Agen yang berjalan di server, tanpa ada orang yang menyetujui proses masuk, memakai kunci API perusahaan dengan hak akses **Pakai dengan agen AI (MCP)**: agen itu hanya bekerja di perusahaan tersebut, dan hanya dengan alat yang diizinkan oleh hak akses lain pada kunci itu.

### 3. Platformmu sendiri, lewat API

Untuk otomatisasi tanpa AI, prepza punya API, yang dijelaskan di [dokumentasi pengembang](/api-docs)-nya.

1. Pemilik atau admin membuka tab **Integrasi** sebuah perusahaan, lalu **API**, dan memilih **Kunci baru**. Beri nama sesuai platform yang akan memakainya, pilih kapan kunci itu kedaluwarsa, dan centang hanya yang dibutuhkannya: kunci dasbor hanya membaca, kunci situs karier juga mengundang. Hak akses bisa ditambah atau dikurangi nanti. Kunci hanya ditampilkan sekali; simpan di tempat yang aman.
2. Platformmu mengirim permintaan dengan kunci itu: menampilkan daftar wawancara perusahaan, menampilkan daftar atau membaca kandidat beserta nilainya, lulus atau tidak, dan tanda integritasnya, serta mengundang kandidat.
3. Tambahkan **webhook**: alamat di platformmu yang dipanggil prepza, dengan tanda tangan, saat kandidat mulai, selesai, atau dihapus, saat undangannya tidak sampai atau kedaluwarsa, dan saat wawancara siap, sehingga kamu tidak perlu terus-menerus bertanya. Halaman API dapat mengirim event uji ke webhook ini dan menampilkan log pengirimannya.

Setiap kandidat dilengkapi tautan ke hasil lengkapnya di prepza dan, sampai ia selesai, tautan undangannya sendiri, sehingga platformmu bisa mengirimkannya lewat pesannya sendiri jika kamu mau. Jika platformmu sudah tahu siapa kandidatnya, undang ia tanpa login: prepza tidak mengirim email apa pun, dan kandidat mengikuti wawancara dari tautan itu tanpa login ke prepza, jadi kirim tautannya hanya kepadanya. Undangan juga bisa membawa kandidat kembali ke situsmu lewat tombol di halaman selesai, dan mengatur tema terang atau gelap dengan warna perusahaanmu. Dengan SDK prepza, halamanmu sendiri bisa menampilkan wawancaranya langsung. Membawa kandidat kembali dan menampilkan wawancara di situsmu memerlukan perusahaan yang terverifikasi, dan hanya berfungsi di domain situs webnya.

Aturannya sama seperti di tempat lain: nilai mendukung keputusan seseorang, jadi jangan menolak kandidat secara otomatis berdasarkan nilai itu.

## Kapan memakai yang mana

Mulailah dari siapa yang mengerjakannya dan seberapa sering.

| Situasimu | Pakai |
| --- | --- |
| Kamu sedang di prepza dan ingin jawaban cepat: siapa yang lulus, siapa yang belum mulai, berapa kredit yang tersisa | Mira, asisten bawaan |
| Kamu ingin menyiapkan sesuatu dengan beberapa kata: wawancara dari deskripsi pekerjaan, batas lulus, tambahan waktu | Mira, asisten bawaan |
| Kamu sudah bekerja di Claude atau ChatGPT seharian dan ingin prepza ada di sana juga | MCP |
| Tugasnya butuh prepza plus hal lain: dokumenmu, draf email, alat lain yang terhubung | MCP |
| Rekruter yang sedang di perjalanan ingin mengecek pipeline dari aplikasi AI di ponselnya | MCP |
| Situs karier atau sistem HR-mu perlu mengundang kandidat sendiri, tanpa ada yang mengklik | API |
| Hasil perlu masuk ke database atau dasbormu sendiri begitu kandidat selesai | API, dengan webhook |
| ATS-mu termasuk yang terhubung dengan prepza (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Bukan salah satunya: hubungkan ATS di tab Integrasi. Lihat [Cara menghubungkan tes keterampilan ke ATS-mu](/guides/ats-integration-skills-tests) |

Patokan sederhananya:

- **Seseorang bertanya, dan mengecek setiap perubahan:** Mira di prepza, atau MCP kalau orang itu sehari-hari bekerja di Claude atau ChatGPT.
- **Perangkat lunak bertindak sendiri, dengan cara yang sama setiap kali:** API.
- **Baru mulai:** coba Mira, asisten bawaan, dulu. Tidak perlu pengaturan apa pun, dan apa yang kamu pelajari juga berlaku di MCP.

Ketiganya juga bisa dipakai bersama. Sebuah tim bisa mengirim undangan dari sistem HR-nya lewat API, sementara rekruter bertanya tentang hasilnya kepada Mira atau chat AI mereka.

## Agar hasilnya bagus

- **Sebut namanya.** "Wawancara Senior Backend" lebih baik daripada "wawancara itu".
- **Minta satu langkah sekaligus** kalau hal itu penting. Cek hasilnya, lalu minta langkah berikutnya.
- **Baca permintaan persetujuan sebelum mengizinkannya.** Di situ tertulis persis apa yang akan dijalankan.
- **Tanyakan dari mana sebuah angka berasal.** Agen yang baik bisa menunjukkan kandidat atau halaman di baliknya.
- **Biarkan keputusan tetap di tangan manusia.** Pakai agen untuk mencari, mengurutkan, dan menyiapkan; putuskan sendiri.

## Harga

Mira, koneksi MCP, dan API gratis dipakai. Kamu hanya membayar untuk kandidat, seperti biasa: per kandidat yang menjawab setidaknya satu soal, tanpa langganan. Lihat [harga](/pricing).

## Bacaan terkait

- [Cara menghubungkan tes keterampilan ke ATS-mu](/guides/ats-integration-skills-tests)
- [Mewawancarai engineer di era AI: apa yang perlu diuji sekarang](/guides/interviewing-in-the-age-of-ai)
- [Apakah rekrutmen dengan AI legal di UE?](/guides/is-ai-hiring-legal-in-the-eu)
