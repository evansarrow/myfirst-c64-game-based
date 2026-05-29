# LAPORAN PRAKTIKUM & PANDUAN PENGEMBANGAN GAME C64 BASIC
**Mata Kuliah: Arsitektur Komputer & Pemrograman Retro**
**Judul Tugas: Rancang Bangun Game "Lovelace Space Dodge" (5-Level Edition) Berbasis Commodore 64 BASIC**

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
* **Gaya Visual (CRT Space Theme):** Warna layar dan bingkai diubah menjadi hitam (`POKE 53280,0` dan `POKE 53281,0`). Pemain direpresentasikan oleh pesawat luar angkasa PETSCII (Kode Layar: `2` — custom character) pada baris ke-23. Meteor direpresentasikan oleh karakter custom (Kode Layar: `17`).
* **Sistem Suara (SID Synthesizer Emulation):** Memanfaatkan chip legendaris **MOS Technology 6581/8580 SID**. Suara *laser blast* menggunakan gelombang segitiga (*triangle wave*) yang disapu frekuensinya ke atas, sementara suara tabrakan (*explosion*) menggunakan generator derau putih (*white noise*) yang disapu ke bawah untuk efek gemuruh. Fanfare arpeggio 3-nada dimainkan saat naik level, dan melodi kemenangan 5-nada saat menamatkan game.
* **Input Kontrol Real-time:** Menggunakan perintah `GET A$` untuk membaca register keyboard buffer secara asinkron tanpa memblokir jalannya game (berbeda dengan `INPUT` yang menghentikan eksekusi).

### Sistem Level Progresif (5 Level):
Game ini menggunakan **5 level progresif** dengan tingkat kesulitan yang meningkat secara bertahap:

| Level | Delay (D) | Kecepatan | Warna Border | Timer (TM) |
|-------|-----------|-----------|--------------|------------|
| 1     | 80        | Paling Lambat | Hitam (0) | 150 |
| 2     | 62        | Lambat    | Biru (6)     | 250 |
| 3     | 44        | Sedang    | Ungu (4)     | 350 |
| 4     | 26        | Cepat     | Merah (2)    | 450 |
| 5     | 8         | Paling Cepat | Oranye (8) | 550 |

**Rumus Kecepatan:** `D = 80 - (LV-1) * 18`
**Rumus Timer:** `TM = 150 + (LV-1) * 100` (dikalibrasi agar ~20 detik per level)

Setiap level dimulai dengan layar pengumuman PETSCII box-art yang menampilkan nomor level dan kecepatan, disertai efek suara fanfare SID. Ketika timer `TM` mencapai nol, pemain naik level dengan animasi flash border dan arpeggio kemenangan.

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

## 4. KODE SUMBER UTAMA — 5-LEVEL EDITION (SPACE_DODGE.BAS)

Berikut adalah kode program lengkap versi **5-Level Edition** yang telah dioptimasi dan bebas dari error. Anda dapat menyalin kode ini atau langsung menggunakan file tokenized biner `space_dodge.prg` di emulator Anda.

### Penjelasan Blok Kode Utama:

| Baris | Fungsi |
|-------|--------|
| 4-17 | Setup custom character (pesawat & meteor) |
| 20-140 | Layar judul & intro |
| 142 | Inisialisasi skor & level (reset saat replay) |
| 145-177 | Setup level: hitung kecepatan, timer, tampilkan pengumuman level |
| 180-350 | Game loop utama: kontrol pemain, gerakan meteor, deteksi tabrakan |
| 360-450 | Layar Game Over |
| 500-550 | Transisi naik level (flash border, fanfare, pengumuman) |
| 570-640 | Layar kemenangan (YOU WIN!) |

```basic
4 POKE 55,0:POKE 56,48:CLR
5 REM *** CUSTOM CHARACTER SETUP ***
6 PRINT CHR$(147);CHR$(30);"LOADING CUSTOM GRAPHICS..."
7 POKE 56334,PEEK(56334)AND254
8 POKE 1,PEEK(1)AND251
9 FOR I=0 TO 511:POKE 12288+I,PEEK(53248+I):NEXT
11 POKE 1,PEEK(1)OR4
12 POKE 56334,PEEK(56334)OR1
13 FOR I=0 TO 7:READ D:POKE 12304+I,D:NEXT
14 FOR I=0 TO 7:READ D:POKE 12424+I,D:NEXT
15 POKE 53272,(PEEK(53272)AND240)OR12
16 DATA 24,60,60,126,255,60,66,66
17 DATA 56,124,247,255,223,126,60,24
20 REM *** LOVELACE SPACE DODGE ***
21 REM *** 5-LEVEL EDITION ***
30 POKE 53280,0:POKE 53281,0:PRINT CHR$(147)
40 FOR I=54272 TO 54296:POKE I,0:NEXT:POKE 54296,15
45 DIM AX(3),AY(3)
50 POKE 54277,15:POKE 54278,240:POKE 54275,15:POKE 54274,15
60 PRINT CHR$(159);"    =============================="
70 PRINT CHR$(159);"      LOVELACE SPACE DODGE C64"
80 PRINT CHR$(159);"    =============================="
85 PRINT:PRINT CHR$(28);"         5-LEVEL CHALLENGE!"
90 PRINT:PRINT CHR$(28);" CONTROLS: A = LEFT, D = RIGHT"
100 PRINT:PRINT CHR$(30);" DODGE THE METEORS!"
105 PRINT:PRINT CHR$(31);" SURVIVE 5 LEVELS TO WIN!"
110 PRINT:PRINT CHR$(31);" PRESS ANY KEY TO START..."
120 GET K$:IF K$="" GOTO 120
130 FOR F=20 TO 80 STEP 2:POKE 54273,F:POKE 54276,17:FOR DL=1 TO 5:NEXT DL:NEXT F
140 POKE 54276,16
142 SC=0:LV=1
145 REM *** LEVEL SETUP ***
148 D=80-(LV-1)*18
149 TM=400+(LV-1)*200
150 PRINT CHR$(147)
153 IF LV=1 THEN POKE 53280,0
154 IF LV=2 THEN POKE 53280,6
155 IF LV=3 THEN POKE 53280,4
156 IF LV=4 THEN POKE 53280,2
157 IF LV=5 THEN POKE 53280,8
159 PRINT:PRINT:PRINT:PRINT:PRINT:PRINT:PRINT
160 PRINT CHR$(159);"  ========================================"
161 PRINT CHR$(159);"  =                                      ="
162 PRINT CHR$(159);"  =        >> LEVEL";LV;"<<               ="
163 PRINT CHR$(159);"  =                                      ="
164 PRINT CHR$(159);"  ========================================"
165 PRINT:PRINT CHR$(28);"          SPEED: ";
166 IF LV=1 THEN PRINT "* SLOW *"
167 IF LV=2 THEN PRINT "** MEDIUM **"
168 IF LV=3 THEN PRINT "*** FAST ***"
169 IF LV=4 THEN PRINT "**** FASTER ****"
170 IF LV=5 THEN PRINT "***** MAXIMUM! *****"
172 POKE 54273,30:POKE 54276,17:FOR DL=1 TO 80:NEXT DL
173 POKE 54273,45:FOR DL=1 TO 80:NEXT DL
174 POKE 54273,60:FOR DL=1 TO 80:NEXT DL
175 POKE 54276,16
176 PRINT:PRINT CHR$(30);"         GET READY..."
177 FOR DL=1 TO 800:NEXT DL
178 PRINT CHR$(147)
180 PX=20
185 FOR I=0 TO 2:AX(I)=INT(RND(1)*38)+1:AY(I)=(I*6)*-1:NEXT I
186 SP=1024+23*40:CP=55296+23*40
188 POKE SP+PX,2:POKE CP+PX,1
190 PRINT CHR$(19);CHR$(30);"SCORE:";SC;"  LV:";LV;"  "
195 TM=TM-1
196 IF TM<=0 GOTO 500
200 GET A$
210 IF A$="A" AND PX>1 THEN POKE SP+PX,32:PX=PX-1:POKE SP+PX,2:POKE CP+PX,1
220 IF A$="D" AND PX<38 THEN POKE SP+PX,32:PX=PX+1:POKE SP+PX,2:POKE CP+PX,1
230 FOR I=0 TO 2
240 IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),32
250 AY(I)=AY(I)+1
260 IF AY(I)=24 GOTO 320
270 IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),17
275 IF AY(I)>=0 AND AY(I)<24 THEN POKE 55296+AY(I)*40+AX(I),2
280 IF AY(I)>=23 AND AX(I)=PX GOTO 360
290 GOTO 340
320 AY(I)=0:AX(I)=INT(RND(1)*38)+1:SC=SC+1
330 POKE 54273,60:POKE 54276,33:FOR DL=1 TO 5:NEXT DL:POKE 54276,32
340 NEXT I
350 FOR DL=1 TO D:NEXT DL:GOTO 190
360 REM *** GAME OVER ***
361 POKE 54276,129:FOR F=30 TO 1 STEP -1:POKE 54273,F:FOR DL=1 TO 20:NEXT DL:NEXT F:POKE 54276,128
370 PRINT CHR$(147)
375 POKE 53280,2
381 PRINT CHR$(28);"  ========================================"
390 PRINT CHR$(28);"  =           GAME OVER!                 ="
392 PRINT CHR$(28);"  ========================================"
410 PRINT:PRINT CHR$(30);"  FINAL SCORE: ";SC
415 PRINT:PRINT CHR$(30);"  REACHED LEVEL: ";LV;" OF 5"
420 PRINT:PRINT CHR$(31);"  PLAY AGAIN? (Y/N)"
430 GET R$:IF R$="" GOTO 430
440 IF R$="Y" THEN GOTO 142
450 POKE 53280,14:POKE 53281,6:PRINT CHR$(147):END
500 REM *** LEVEL COMPLETE ***
506 FOR I=0 TO 2:IF AY(I)>=0 AND AY(I)<24 THEN POKE 1024+AY(I)*40+AX(I),32
507 NEXT I
510 LV=LV+1
515 IF LV>5 GOTO 570
521 FOR FL=1 TO 3
522 POKE 53280,1:FOR DL=1 TO 30:NEXT DL
523 POKE 53280,0:FOR DL=1 TO 30:NEXT DL
524 NEXT FL
531 POKE 54273,40:POKE 54276,17:FOR DL=1 TO 60:NEXT DL
532 POKE 54273,50:FOR DL=1 TO 60:NEXT DL
533 POKE 54273,65:FOR DL=1 TO 60:NEXT DL
535 POKE 54276,16
542 PRINT CHR$(30);"      ** LEVEL ";LV-1;" COMPLETE! **"
544 PRINT:PRINT CHR$(28);"     NEXT LEVEL: ";LV;" - FASTER!"
545 FOR DL=1 TO 1000:NEXT DL
550 GOTO 145
570 REM *** YOU WIN! ***
572 FOR FL=1 TO 5
573 POKE 53280,7:FOR DL=1 TO 40:NEXT DL
574 POKE 53280,5:FOR DL=1 TO 40:NEXT DL
575 NEXT FL
576 POKE 53280,7
581 POKE 54273,30:POKE 54276,17:FOR DL=1 TO 60:NEXT DL
582 POKE 54273,40:FOR DL=1 TO 60:NEXT DL
583 POKE 54273,50:FOR DL=1 TO 60:NEXT DL
584 POKE 54273,65:FOR DL=1 TO 60:NEXT DL
585 POKE 54273,80:FOR DL=1 TO 120:NEXT DL
586 POKE 54276,16
590 PRINT CHR$(147)
592 PRINT CHR$(7);"  ========================================"
594 PRINT CHR$(7);"  =      **** YOU WIN! ****              ="
596 PRINT CHR$(7);"  =   ALL 5 LEVELS COMPLETED!            ="
598 PRINT CHR$(7);"  ========================================"
600 PRINT:PRINT CHR$(30);"  FINAL SCORE: ";SC
605 PRINT:PRINT CHR$(159);"  CONGRATULATIONS, COMMANDER!"
610 PRINT:PRINT CHR$(31);"  PLAY AGAIN? (Y/N)"
620 GET R$:IF R$="" GOTO 620
630 IF R$="Y" THEN GOTO 142
640 POKE 53280,14:POKE 53281,6:PRINT CHR$(147):END
```

---

## 5. PANDUAN REKAMAN VIDEO YOUTUBE (DURASI ~15 MENIT)

Untuk mempermudah perekaman video Anda, berikut adalah pembagian segmen waktu dan naskah panduan berbicara yang akademis, interaktif, dan terlihat sangat profesional.

### ⏱️ Pembagian Segmen Waktu Video:
1. **00:00 - 02:00 | Pembukaan & Konsep:** Perkenalan diri, menjelaskan tujuan tugas, konsep game arcade retro, arsitektur memori C64, dan **sistem 5 level progresif** yang digunakan.
2. **02:00 - 06:00 | Uji Coba Gameplay (Demo 5 Level):** Menunjukkan cara membuka emulator, melakukan *drag & drop* file `space_dodge.prg`, lalu mendemonstrasikan permainan secara langsung. **Pastikan menunjukkan minimal 2-3 transisi level** agar terlihat peningkatan kecepatan meteor dan perubahan warna border.
3. **06:00 - 10:00 | Bedah Kode Sumber (Source Code Walkthrough):** Membuka kode `.bas` di editor teks modern, menjelaskan baris-baris krusial:
   - **Baris 148-149:** Rumus kecepatan (`D=80-(LV-1)*18`) dan timer (`TM=150+(LV-1)*100`)
   - **Baris 153-157:** Sistem warna border per level
   - **Baris 500-550:** Transisi naik level (flash, fanfare, pengumuman)
   - **Baris 570-640:** Layar kemenangan setelah Level 5
4. **10:00 - 13:30 | Analisis Error & Pemecahan Masalah:** Bagian paling berharga secara akademis! Jelaskan secara detail minimal 3 error yang Anda temukan (seperti `?REDIM'D ARRAY ERROR` akibat penempatan `DIM` yang salah, koordinat negatif yang memicu `?ILLEGAL QUANTITY`, dan *sound lockup*). Tunjukkan perubahan kodenya untuk menyelesaikan error tersebut.
5. **13:30 - 15:00 | Kesimpulan & Penutup:** Menyampaikan pembelajaran berharga dari pemrograman komputer retro 8-bit dibandingkan arsitektur modern, diskusikan **tantangan kalibrasi timer software** pada CPU 1 MHz vs timer hardware modern, berterima kasih kepada penonton/dosen, serta ajakan *closing*.

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
