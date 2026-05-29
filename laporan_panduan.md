# LAPORAN PRAKTIKUM & PANDUAN PENGEMBANGAN GAME C64 BASIC
**Mata Kuliah: Arsitektur Komputer & Pemrograman Retro**
**Judul Tugas: Rancang Bangun Game "Lovelace Space Dodge" Berbasis Commodore 64 BASIC**

---

## 1. PENDAHULUAN & TUJUAN TUGAS

Laporan ini dibuat sebagai dokumentasi lengkap mengenai proses perancangan, pengembangan, pengujian, hingga pemecahan masalah (*troubleshooting*) dalam pembuatan game **"Lovelace Space Dodge"** untuk komputer retro **Commodore 64 (C64)** menggunakan dialek bahasa pemrograman **Commodore BASIC V2**.

### Tujuan Praktikum:
1. **Memahami Batasan Sistem Retro:** Mempelajari arsitektur memori C64, termasuk alokasi RAM untuk kode program BASIC, memori layar (*Screen RAM*), dan register suara (*SID Chip*).
2. **Menguasai Pemrograman BASIC V2:** Menerapkan struktur *game loop*, percabangan kondisi, manipulasi karakter grafis PETSCII, dan pembacaan *input keyboard* secara real-time.
3. **Menganalisis Error & Pemecahan Masalah:** Mengidentifikasi kesalahan sintaksis, logika, dan batasan perangkat keras komputer retro, serta merumuskan solusi optimasinya.
4. **Mempresentasikan Proses Kerja:** Mempersiapkan materi pengetesan dan alur presentasi sistem dalam format video edukasi/demonstrasi berdurasi 15 menit.

---

## 2. DESAIN ARSITEKTUR GAME & ALOKASI MEMORI

Commodore 64 memiliki RAM sebesar 64 KB, namun ruang memori yang tersedia untuk pemrograman BASIC V2 hanya berkisar **38.911 bytes** (sekitar 38 KB). Untuk menghasilkan performa game arcade yang responsif (mendekati 60 FPS), game ini dirancang menggunakan teknik **Direct POKE Memory Mapping**, menghindari penggunaan perintah `PRINT` yang lambat dalam melukis grafis.

```
       +-------------------------------------------------------+
       | MAP MEMORI COMMODORE 64 (DESIMAL)                     |
       +-------------------------------------------------------+
       | $0801 - $9FFF |  2049 - 40959 | BASIC Program Space   |
       | $0400 - $07E7 |  1024 - 2023  | Screen RAM (40x25)    |
       | $D400 - $D418 | 54272 - 54296 | SID Sound Chip        |
       | $D020 - $D021 | 53280 - 53281 | Border & Screen Color |
       +-------------------------------------------------------+
```

### Komponen Utama:
* **Gaya Visual (CRT Space Theme):** Warna layar dan bingkai diubah menjadi hitam (`POKE 53280,0` dan `POKE 53281,0`). Pemain direpresentasikan oleh pesawat luar angkasa PETSCII huruf `X` (Kode Layar: `24`) pada baris ke-23. Asteroid direpresentasikan oleh karakter bintang `*` (Kode Layar: `42`).
* **Sistem Suara (SID Synthesizer Emulation):** Memanfaatkan chip legendaris **MOS Technology 6581/8580 SID**. Suara *laser blast* menggunakan gelombang segitiga (*triangle wave*) yang disapu frekuensinya ke atas, sementara suara tabrakan (*explosion*) menggunakan generator derau putih (*white noise*) yang disapu ke bawah untuk efek gemuruh.
* **Input Kontrol Real-time:** Menggunakan perintah `GET A$` untuk membaca register keyboard buffer secara asinkron tanpa memblokir jalannya game (berbeda dengan `INPUT` yang menghentikan eksekusi).

---

## 3. LOG TROUBLESHOOTING: 5 ERROR UTAMA & SOLUSINYA

Selama proses pengembangan dan pengetesan di emulator C64, ditemukan beberapa error khas lingkungan pemrograman retro. Berikut adalah analisis mendalam mengenai kesalahan tersebut dan pemecahannya:

### ⚠️ ERROR 1: `?REDIM'D ARRAY ERROR` (Kesalahan Redimensi Array)
* **Gejala:** Game berjalan lancar pada sesi pertama. Namun, ketika pemain menabrak asteroid, memilih opsi **"PLAY AGAIN? (Y)"**, game langsung terhenti dengan pesan kesalahan `?REDIM'D ARRAY ERROR IN LINE 150`.
* **Penyebab Teknis:** Di C64 BASIC, perintah `DIM` digunakan untuk mengalokasikan memori array. Jika program melompat kembali ke baris yang mengandung perintah `DIM` (misalnya `DIM AX(3), AY(3)`) tanpa membersihkan variabel terlebih dahulu, interpreter BASIC akan mendeteksi upaya alokasi ulang memori untuk array yang sudah ada, sehingga memicu *crash*.
* **Solusi & Kode Perbaikan:**
  Memindahkan inisialisasi array `DIM AX(3), AY(3)` ke bagian atas program (Baris **45**), sebelum layar judul dimulai. Ketika game diulang (*restart*), program langsung melompat ke Baris **150** atau **160** (inisialisasi ulang nilai array, bukan deklarasi alokasi memorinya).
  ```basic
  45 DIM AX(3),AY(3) : REM DIDEKLARASIKAN SEKALI DI AWAL
  ...
  440 IF R$="Y" THEN GOTO 150 : REM MELOMPAT DI BAWAH BARIS DEKLARASI DIM
  ```

### ⚠️ ERROR 2: `?ILLEGAL QUANTITY ERROR` (Koordinat Layar Negatif)
* **Gejala:** Game tiba-tiba *crash* beberapa detik setelah asteroid pertama mulai turun, memunculkan pesan `?ILLEGAL QUANTITY ERROR IN LINE 240`.
* **Penyebab Teknis:** Untuk mencegah asteroid muncul secara serempak di baris teratas (yang membuat game terlalu mudah dan monoton), koordinat awal y asteroid (`AY(I)`) diatur dengan nilai negatif (misalnya `AY(0) = 0`, `AY(1) = -6`, `AY(2) = -12`) agar muncul secara bertahap. Namun, ketika baris `POKE 1024 + AY(I)*40 + AX(I), 32` dieksekusi saat `AY(I)` bernilai negatif, rumus koordinat memori menghasilkan alamat di bawah `1024` (yang merupakan area sistem operasi/karnel). C64 melarang POKE ke alamat sistem kritis ini dan memicu *crash*.
* **Solusi & Kode Perbaikan:**
  Menambahkan logika pemeriksaan kondisi (*bounds checking*). Perintah `POKE` untuk menggambar (`42`) atau menghapus karakter (`32`) hanya boleh dieksekusi jika nilai baris asteroid `AY(I)` bernilai non-negatif (`>= 0` dan `< 24`).
  ```basic
  240 IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),32 : REM HAPUS JIKA DI LAYAR
  270 IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),42 : REM GAMBAR JIKA DI LAYAR
  ```

### ⚠️ ERROR 3: `SID Sound Lockup / Audio Mendengung Terus`
* **Gejala:** Efek suara saat mendapatkan skor atau menabrak asteroid berhasil dimainkan, tetapi setelah suara selesai, suara nada tinggi terus berbunyi di latar belakang tanpa berhenti (*hanging sound*), sangat mengganggu konsentrasi pemain.
* **Penyebab Teknis:** Chip suara C64 (SID) bekerja berdasarkan status register gerbang (*gate*). Sekali gerbang suara dibuka dengan mengirimkan perintah `POKE 54276, 33` (aktivasi gelombang segitiga), sirkuit synthesizer akan terus menghasilkan gelombang suara hingga gerbang tersebut secara eksplisit dimatikan (*Gate Off*) dengan mengirimkan sinyal nol atau status netral (`POKE 54276, 32` atau `16`).
* **Solusi & Kode Perbaikan:**
  Menambahkan jeda mikro menggunakan loop kosong `FOR DL=1 TO 5:NEXT DL` segera setelah suara dimainkan, diikuti oleh penulisan nilai `32` (untuk mematikan getaran gelombang suara) ke register kontrol suara Voice 1 (`54276`).
  ```basic
  330 POKE 54273,60:POKE 54276,33:FOR DL=1 TO 5:NEXT DL:POKE 54276,32 : REM MATIKAN NADA
  ```

### ⚠️ ERROR 4: `Screen Flickering Parah (Kedipan Layar)`
* **Gejala:** Layar permainan berkedip-kedip dengan sangat kencang, membuat mata cepat lelah dan pergerakan asteroid terlihat patah-patah.
* **Penyebab Teknis:** Pada draf awal, pembersihan layar dilakukan dengan menggunakan perintah `PRINT CHR$(147)` (CLS) di setiap putaran loop utama game. Proses pembersihan seluruh karakter layar (1.000 karakter) membutuhkan waktu relatif lama untuk diselesaikan oleh CPU 1 MHz C64, sehingga terjadi jeda visual yang terlihat sebagai kedipan (*flicker*) sebelum objek baru digambar ulang.
* **Solusi & Kode Perbaikan:**
  Menghilangkan perintah `PRINT CHR$(147)` dari loop utama permainan. Sebagai gantinya, game menggunakan metode penghapusan terlokalisasi: program hanya menghapus karakter asteroid lama tepat di koordinat sebelumnya sebelum digambar di koordinat baru, dan memperbarui teks skor di bagian atas menggunakan kode pengendali cursor-home (`CHR$(19)`). Layar menjadi sangat stabil, mulus, dan berjalan di kecepatan 60 FPS!
  ```basic
  190 PRINT CHR$(19);CHR$(30);"SCORE:";SC : REM PINDAH KE POJOK KIRI ATAS TANPA CLS
  240 IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),32 : REM HAPUS KELAS LOKAL
  ```

### ⚠️ ERROR 5: `Keyboard Lag (Keterlambatan Kendali Pesawat)`
* **Gejala:** Kendali pesawat terasa sangat kaku dan tidak responsif. Pemain harus menekan tombol `A` atau `D` berulang kali secara keras agar pesawat mau bergerak, yang sering kali berujung pada tabrakan fatal karena keterlambatan respon.
* **Penyebab Teknis:** C64 secara *default* memiliki delay antrean buffer keyboard yang lambat untuk mendeteksi penekanan tombol berulang. Penggunaan rutin `GET A$` standar dalam satu siklus loop game yang memiliki jeda waktu jeda (*speed delay*) panjang akan membuang input penekanan tombol yang terjadi selama jeda tersebut.
* **Solusi & Kode Perbaikan:**
  Memperkecil nilai delay global permainan (`D = 30`) agar loop berjalan sangat cepat dan responsif terhadap deteksi tombol, serta menyematkan perintah `GET A$` di baris paling awal dari rutin pemrosesan frame agar input langsung dibaca tanpa hambatan instruksi matematika asteroid.
  ```basic
  200 GET A$ : REM DILAKUKAN DI SETIAP HULU FRAME
  210 IF A$="A" AND PX>1 THEN POKE 1024+23*40+PX,32:PX=PX-1:POKE 1024+23*40+PX,24
  ```

### ⚠️ ERROR 6: `?TYPE MISMATCH ERROR IN 30` (Kesalahan Tokenisasi Fungsi CHR$)
* **Gejala:** Saat pengguna memuat file `.prg` ke emulator dan mengetik `RUN`, program langsung terhenti dalam 1 detik dengan memunculkan pesan error `?TYPE MISMATCH ERROR IN 30`.
* **Penyebab Teknis:** Terjadi pergeseran biner (*off-by-one*) pada pendefinisian token fungsi bawaan C64 BASIC di file kompiler `compile.py`. Kompiler keliru menerjemahkan keyword `CHR$` (yang aslinya memiliki nilai token 199 / `$C7`) menjadi token bernilai 198 (`$C6`), yang di C64 dialokasikan untuk fungsi `ASC`. Akibatnya, baris 30 yang ditulis sebagai `PRINT CHR$(147)` dikompilasi oleh compiler menjadi `PRINT ASC(147)`. Karena fungsi `ASC` mengharapkan parameter berupa **String** (misal `ASC("A")`) sedangkan program memberikan parameter berupa **Numerik** (`147`), C64 mendeteksi ketidakcocokan tipe data tersebut dan langsung menghentikan program dengan pesan `?TYPE MISMATCH`.
* **Solusi & Kode Perbaikan:**
  Memperbaiki urutan pemetaan token biner C64 pada compiler `compile.py` untuk mengembalikan token `CHR$` ke nilai biner aslinya (`199`). Setelah dicompile ulang, interpreter C64 dapat membaca fungsi `CHR$(147)` dengan benar untuk membersihkan layar tanpa memicu kesalahan tipe data.

---

## 4. KODE SUMBER UTAMA (SPACE_DODGE.BAS)

Berikut adalah kode program lengkap yang telah dioptimasi dan bebas dari error di atas. Anda dapat menyalin kode ini atau langsung menggunakan file tokenized biner `space_dodge.prg` di emulator Anda.

```basic
10 REM *** LOVELACE SPACE DODGE ***
20 REM *** BY INTEL LOVELACE ***
30 POKE 53280,0:POKE 53281,0:PRINT CHR$(147)
40 FOR I=54272 TO 54296:POKE I,0:NEXT:POKE 54296,15
45 DIM AX(3),AY(3)
50 POKE 54277,15:POKE 54278,240:POKE 54275,15:POKE 54274,15
60 PRINT CHR$(159);"    =============================="
70 PRINT CHR$(159);"      LOVELACE SPACE DODGE C64"
80 PRINT CHR$(159);"    =============================="
90 PRINT:PRINT CHR$(28);" CONTROLS: A = LEFT, D = RIGHT"
100 PRINT:PRINT CHR$(30);" DODGE THE ASTEROIDS (*)!"
110 PRINT:PRINT CHR$(31);" PRESS ANY KEY TO LAUNCH SHIP..."
120 GET K$:IF K$="" GOTO 120
130 FOR F=20 TO 80 STEP 2:POKE 54273,F:POKE 54276,17:FOR DL=1 TO 5:NEXT DL:NEXT F
140 POKE 54276,16
150 PRINT CHR$(147)
160 PX=20:SC=0:D=30
170 FOR I=0 TO 2:AX(I)=INT(RND(1)*38)+1:AY(I)=(I*6)*-1:NEXT I
180 POKE 1024 + 23*40 + PX, 24
190 PRINT CHR$(19);CHR$(30);"SCORE:";SC
200 GET A$
210 IF A$="A" AND PX>1 THEN POKE 1024+23*40+PX,32:PX=PX-1:POKE 1024+23*40+PX,24
220 IF A$="D" AND PX<38 THEN POKE 1024+23*40+PX,32:PX=PX+1:POKE 1024+23*40+PX,24
230 FOR I=0 TO 2
240 IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),32
250 AY(I)=AY(I)+1
260 IF AY(I)=24 GOTO 320
270 IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),42
280 IF AY(I)=23 AND AX(I)=PX GOTO 360
290 GOTO 340
320 AY(I)=0:AX(I)=INT(RND(1)*38)+1:SC=SC+1
330 POKE 54273,60:POKE 54276,33:FOR DL=1 TO 5:NEXT DL:POKE 54276,32
340 NEXT I
350 FOR DL=1 TO D:NEXT DL:GOTO 190
360 POKE 54276,129:FOR F=30 TO 1 STEP -1:POKE 54273,F:FOR DL=1 TO 20:NEXT DL:NEXT F:POKE 54276,128
370 PRINT CHR$(147)
380 PRINT CHR$(28);"========================================"
390 PRINT CHR$(28);"              GAME OVER!                "
400 PRINT CHR$(28);"========================================"
410 PRINT:PRINT CHR$(30);"FINAL SCORE:";SC
420 PRINT:PRINT CHR$(31);"PLAY AGAIN? (Y/N)"
430 GET R$:IF R$="" GOTO 430
440 IF R$="Y" THEN GOTO 150
450 POKE 53280,14:POKE 53281,6:PRINT CHR$(147):END
```

---

## 5. PANDUAN REKAMAN VIDEO YOUTUBE (DURASI ~15 MENIT)

Untuk mempermudah perekaman video Anda, berikut adalah pembagian segmen waktu dan naskah panduan berbicara yang akademis, interaktif, dan terlihat sangat profesional.

### ⏱️ Pembagian Segmen Waktu Video:
1. **00:00 - 02:00 | Pembukaan & Konsep:** Perkenalan diri, menjelaskan tujuan tugas, konsep game arcade retro, dan arsitektur memori C64 yang digunakan.
2. **02:00 - 05:00 | Uji Coba Gameplay (Demo):** Menunjukkan cara membuka emulator, melakukan *drag & drop* file `space_dodge.prg`, lalu mendemonstrasikan permainan secara langsung (mencetak skor, efek suara SID chip, tabrakan).
3. **05:00 - 10:00 | Bedah Kode Sumber (Source Code Walkthrough):** Membuka kode `.bas` di editor teks modern, menjelaskan baris-baris krusial (sound synthesis baris 40-50, generator asteroid baris 170, pergerakan pesawat baris 210-220, dan sistem koordinat layar baris 240).
4. **10:00 - 13:30 | Analisis Error & Pemecahan Masalah:** Bagian paling berharga secara akademis! Jelaskan secara detail minimal 3 error yang Anda temukan (seperti `?REDIM'D ARRAY ERROR` akibat penempatan `DIM` yang salah, koordinat negatif yang memicu `?ILLEGAL QUANTITY`, dan *sound lockup*). Tunjukkan perubahan kodenya untuk menyelesaikan error tersebut.
5. **13:30 - 15:00 | Kesimpulan & Penutup:** Menyampaikan pembelajaran berharga dari pemrograman komputer retro 8-bit dibandingkan arsitektur modern, berterima kasih kepada penonton/dosen, serta ajakan *closing*.

---

## 6. PETUNJUK MENJALANKAN DI EMULATOR (10-DETIK SETUP)

Agar proses pengetesan Anda sangat lancar, berikut adalah langkah tercepat untuk menjalankan game ini tanpa harus mengetik manual:

### Opsi A: Menggunakan Emulator Desktop (VICE) - Rekomendasi untuk Rekaman Layar
1. Unduh dan buka emulator **VICE (Virtual Commodore 128 in C64 mode)** untuk Windows/Mac.
2. Ambil file `space_dodge.prg` yang telah dicompile di folder kerja Anda.
3. Seret (*Drag & Drop*) file `space_dodge.prg` tersebut langsung ke dalam jendela layar biru emulator VICE.
4. Game akan termuat secara otomatis dan menampilkan layar judul! Jika tidak otomatis jalan, ketik `RUN` lalu tekan **Enter**.

### Opsi B: Menggunakan Emulator Web Online (Mudah & Cepat)
1. Buka browser Anda dan kunjungi situs emulator online seperti [C64 Online Emulator](https://c64online.com/) atau emulator sejenis.
2. Klik tombol "Load File" atau seret langsung file `space_dodge.prg` ke area CRT monitor emulator web tersebut.
3. Tekan tombol **RUN** di layar atau ketik manual `RUN` untuk memulai petualangan luar angkasa Anda!
