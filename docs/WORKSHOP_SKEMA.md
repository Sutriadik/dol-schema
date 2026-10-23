# Workshop Skema Companion: bahan untuk bertiga

**Untuk:** RPA Engineer, Network Engineer, AI Engineer, + mentor
**Durasi:** 90 menit
**Keluar dari ruangan dengan:** keputusan atas tabel yang masih **ditunda**

> Briefing hlm. 12: *"Skema data companion dirancang bertiga di Bulan 2 — itu fondasi yang
> dipakai ketiganya."*

> **Pembaruan 2026-10-09.** Ditambahkan usulan dari permintaan tabel RPA Engineer (BoQ
> permintaan, SPPH, balasan vendor, vendor, proyek), usulan struktur evidence untuk Network
> Engineer, penyesuaian SPH Vendor, dan alur BAST dengan human in the loop. Semuanya **usulan**:
> `model.py` belum diubah. Contoh diambil dari dokumen nyata yang disamarkan (lihat
> [Bahan bukti](#bahan-bukti)); nama klien, nomor seri, koordinat, dan nominal tidak ditulis
> karena repo ini publik.

> **Pembaruan 2026-10-10.** Ditambahkan bagian 6: tiga BoQ (permintaan, penawaran, kontrak) dan
> mana yang menjadi acuan BAST, pemeriksaan PM per baris untuk rincian, tempat tabel asli dan
> judulnya, serta daftar field yang dibutuhkan draf BAST. Semuanya **usulan**.
---

## Yang sudah berlaku (tidak perlu diputuskan ulang)

Versi `companion-2026.10.5`. Rinciannya di [`generated/KAMUS_DATA.md`](../generated/KAMUS_DATA.md).

| Tabel (judul NocoDB) | Isi | Penulis |
|---|---|---|
| Dokumen | setiap PDF yang masuk | sistem |
| Kontrak, Pihak Kontrak, Rincian Kontrak, Syarat Kontrak, Ketentuan Pembayaran | kontrak/SPK pelanggan, BoQ (dengan jenis biaya OTC/MRC), lampiran wajib, termin | sistem |
| SPH Vendor, Rincian SPH | penawaran vendor per baris | sistem |
| Hasil Ekstraksi | nilai terbaca + bukti, antrean PM | sistem |
| Keputusan PM | konfirmasi per field | **PM saja** |

Keputusan yang sudah diambil:

- **Bahasa:** nama teknis Inggris (untuk kode, SQL, n8n), **judul dan pilihan nilai bahasa
  Indonesia** (yang dilihat orang kantor di NocoDB). Satu sumber: `dol_schema/model.py`.
- **Kunci anti-dobel:** dokumen = sidik isi berkas (`doc-` + sha256); anak = induk + nomor urut.
- **Nilai untuk dokumen hilir** hanya dari Keputusan PM yang belum basi
  (view `nilai_terverifikasi`).
- **Dokumen yang sudah diperiksa PM tidak ditimpa otomatis** oleh proses ulang.
- Skrip ERD lama dan exporter 13 tabel sudah dihapus dari dol-parser.

---

## Bahan bukti

Usulan di bawah merujuk dokumen nyata dengan kode, bukan nama (aturan 7 AGENTS.md: kolom baru
harus punya bukti di dokumen nyata).

| Kode | Dokumen | Dipakai untuk |
|---|---|---|
| A | BAST + lampiran pengadaan perangkat untuk satu kampus (24 hlm). Satu baris BoQ "1 Paket" berisi 12 unit dari 5 jenis | BoQ paket vs unit, pola 3 foto |
| B | BAST + lampiran perangkat jaringan untuk banyak OPD di satu kabupaten (138 hlm, 15 baris BoQ, 149 SN tertulis) | GPS, tanggal, SN, jasa instalasi |
| C | BAST + BAUT vendor pengadaan mesin (vendor → BUT) | aturan checker |
| D | BAST layanan managed service 6 bulan | bukti berupa laporan bulanan |
| E | template SPPH, SPH, BAKN, SPK, dan dua BAST dari bahan magang | kolom SPPH & vendor, aturan checker |
| F | SPH di golden set dol-parser (3 dokumen) | arah SPH |
| K | katalog checklist evidence ODK dari Network Engineer | aturan evidence |

---

## Yang harus diputuskan bersama

### 1. BAST (bersama RPA Engineer): tabel usulan di `generated/schema_usulan.sql`

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 1a | Kunci anti-dobel **Draf BAST**: per kontrak + nomor termin? | Tanpa kunci, pengiriman ulang menghapus persetujuan PM (terbukti di versi lama). Sejak 2026.10.4 termin tersimpan di *Ketentuan Pembayaran* (`contract_payment_term.line_no`), calon rujukan kunci ini. |
| 1b | Nomor BAST dari numbering service: kapan dipesan: saat draf dibuat atau saat disetujui? | Nomor duplikat tidak bisa diperbaiki setelah terkirim (hlm. 20). Usul: **setelah disetujui** (lihat alur di bawah). |
| 1c | Satu kontrak bisa punya beberapa BAST (termin/parsial)? | Menentukan relasi kontrak → BAST (1:1 atau 1:banyak). |
| 1d | Serah terima sering berupa paket berita acara (BAUT, BARD, BAPB): satu tabel atau `doc_type` tambahan? | Dari 20 proyek nyata, BAUT pernah 55 halaman. |
| 1e | Siapa yang merender BAST (dol-render) dan dari data apa? | Penyusun data draf sudah ada di dol-parser (`app/companion/generator.py`) dan hanya membaca nilai terverifikasi. |
| 1f | Human in the loop: *checker* dan *judge* orang yang sama atau berbeda? | Menentukan kolom milik manusia di Draf BAST. |
| 1g | Syarat gerbang sebelum draf boleh dibuat | Usul di bawah. |

Bahan: [`docs/usulan-alur-bast/TEMUAN_14_BAST.md`](usulan-alur-bast/TEMUAN_14_BAST.md):
temuan dari 14 BAST asli (label "Pihak Pertama/Kedua" terbalik antar-format, arah BAST bisa
diturunkan dari peran BUT).

#### Usulan alur BAST

1. **Gerbang (mesin).** Draf hanya dibuat bila (a) semua field kontrak yang dipakai BAST ada di
   `nilai_terverifikasi`, dan (b) checklist gabungan lengkap: setiap Syarat Kontrak berjenis
   `lampiran_wajib` terpenuhi, Aturan Evidence untuk setiap baris yang diserahkan terpenuhi,
   dan evidence-nya sudah disetujui PM (bagian 2).
2. **Draf (mesin).** Data dari `app/companion/generator.py` di dol-parser. Dokumen dirender dari
   template per format pelanggan; di arsip ada minimal empat format (BAST + lampiran + BARD +
   BAUT + evidence; BAST + BAUT dengan kode barang; BA penyelesaian + BAST; BAST vendor).
   **LLM tidak menulis isi BAST.**
3. **Checker (mesin, lalu manusia).** Mesin menjalankan aturan konsistensi di bawah dan menulis
   laporannya; manusia memeriksa laporan itu dan PDF draf berwatermark DRAF.
4. **Judge (PM).** Setuju, atau tolak dengan catatan → kembali ke langkah 2.
5. **Nomor dan tanda tangan.** Nomor dipesan dari numbering service setelah disetujui. Bila
   dipesan saat draf, setiap draf yang ditolak membuang satu nomor. Lalu render final, tanda
   tangan, unggah hasil pindai.

Aturan checker yang diusulkan, dengan contoh yang benar-benar ditemukan:

| Aturan | Contoh nyata |
|---|---|
| Nama hari cocok dengan tanggal | E: "Senin" untuk tanggal yang jatuh hari Sabtu |
| Urutan tanggal: kontrak/PO ≤ uji terima ≤ BAST | C: BAST bertanggal 7 hari sebelum PO dan 24 hari sebelum uji terima. E: BAST 1 hari sebelum nota pesanan; uji terima 9 hari sebelum SPK |
| Volume BAST = volume BAUT ≤ volume kontrak | C: BAST 1 unit, BAUT 2 unit |
| Nama pihak di blok tanda tangan = nama pihak di badan dokumen | C: blok tanda tangan memuat nama perusahaan lain (sisa template) |
| Jumlah baris = total; terbilang = angka | — |
| SN unik; tanggal evidence dalam periode | lihat bagian 2 |

Usul penyesuaian `bast_draft`:

- Status berbahasa Indonesia, lebih rinci dari `BAST_DRAFT_STATUSES` sekarang: `draf`,
  `menunggu_cek`, `menunggu_keputusan`, `disetujui`, `ditolak`, `bernomor`, `ditandatangani`.
- Kolom mesin `check_report` (*Laporan Cek*): hasil aturan checker.
- Kolom milik manusia (`written_by="human"`): `checked_by`, `checked_at` (*Diperiksa Oleh*,
  *Waktu Diperiksa*), `approved_by`, `approved_at` (sudah ada), `decision_note`
  (*Catatan Keputusan*).

### 2. Evidence (bersama Network Engineer): tabel usulan `evidence_photo`

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 2a | Lampiran wajib kontrak sering berupa **dokumen** (BA uji terima, surat jalan), bukan foto. Satu tabel bukti untuk keduanya, atau dua? | Checklist gabungan (hlm. 15) harus bisa dipenuhi oleh dokumen. Usul: satu tabel berkas (lihat `evidence_file`). |
| 2b | Bagaimana teknisi di ODK memilih baris BoQ yang dibuktikan, padahal ODK tidak tahu Id baris NocoDB? | Kolom `contract_item_id` wajib di usulan sekarang. Usul: daftar pilihan dari n8n (lihat di bawah). |
| 2c | Pemeriksaan otomatis (GPS, radius lokasi, masa kontrak) di n8n atau di ODK? | Menentukan isi `auto_check_notes`. Usul: n8n (lihat di bawah). |
| 2d | Tabel terpisah untuk pengadaan, instalasi, dan pemeliharaan? | Usul: **tidak**. Kolomnya sama; yang berbeda hanya aturan fotonya. Satu SN melewati ketiganya (dikirim → dipasang → dirawat), dan registry aset (Network Bulan 6) butuh jejak itu di satu tempat. |
| 2e | Foto sebagai kolom tetap (`foto_1`, `foto_2`, `foto_3`) atau satu baris per foto? | Usul: satu baris per foto. Jumlah dan jenis foto berbeda per jenis baris (tabel di bawah), dan "foto 2" artinya lain antara pengadaan dan instalasi. |
| 2f | Definisi "tanggal sesuai kontrak" dan radius "GPS sesuai lokasi" | Temuan B di bawah. |
| 2g | Berkas foto disimpan di mana: ODK Central, Drive, atau kolom lampiran NocoDB? | Menentukan isi `file_url`. Model belum punya tipe lampiran. |

#### Temuan dari BAST nyata

| Jenis baris | Bukti yang dilampirkan |
|---|---|
| Perangkat ber-SN (switch, AP, router, firewall): A, B | 3 foto per unit: label kardus (ada barcode SN), label perangkat (SN), unit di kardus bersama kelengkapannya |
| Rak (rackmount): A | 3 foto per unit, tanpa SN |
| Kabel per roll: B | 2 foto per roll: label kemasan + isi |
| Konektor 10 box: B | 1 foto untuk semua box |
| Jasa instalasi: B | ±20 foto kegiatan pemasangan, dikelompokkan per lokasi (OPD), tanpa unit atau SN |
| Lisensi: A | 1 screenshot dasbor, tanpa GPS |
| Managed service: D | "reporting pekerjaan bulanan, 1x per bulan": dokumen, bukan foto |

Katalog K mencampur pengadaan (foto kelengkapan dus) dan instalasi (foto rak, foto testing)
tanpa menyebut kapan masing-masing wajib, belum punya foto label kardus, dan meminta
`id_proyek` diketik tangan.

#### Usulan struktur (menggantikan `evidence_photo`)

Empat tabel. Aturan foto menjadi **data** (tabel Aturan Evidence) yang dirawat Network
Engineer, bukan struktur tabel. Pilihan nilai memakai bahasa Indonesia, jadi "maintenance"
ditulis `pemeliharaan`.

**`site_visit` — Kunjungan Lapangan.** Satu kiriman ODK per lokasi per kunjungan.

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `odk_instance_id` | ID Kiriman ODK | text, unik, wajib | kunci anti-dobel |
| `mybhakti_project_ref` | Rujukan Proyek MyBhakti | text, wajib | |
| `contract_id` | ID Kontrak | int, FK | kosong bila kontrak belum ada |
| `activity_type` | Jenis Kegiatan | enum, wajib | `pengadaan`, `instalasi`, `pemeliharaan` |
| `site_name` | Nama Lokasi | text | B mengelompokkan evidence per OPD |
| `gps_lat`, `gps_lon` | Lintang, Bujur | coord | geopoint ODK, **bukan** stempel yang tercetak di foto |
| `gps_accuracy_m` | Akurasi GPS | numeric | meter, dari ODK |
| `visited_at` | Waktu Kunjungan | timestamptz, wajib | |
| `technician_name` | Teknisi | text | |
| `pic_name` | PIC Lokasi | text | K: foto bersama PIC + TTD PIC |
| `technician_signature_url`, `pic_signature_url` | TTD Teknisi, TTD PIC | text | |
| `auto_check_notes` | Catatan Cek Otomatis | text | |

**`evidence_unit` — Unit Evidence.** Satu baris per unit atau objek yang dibuktikan (satu
perangkat, satu roll, satu lisensi, satu periode layanan).

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `site_visit_id` | ID Kunjungan | int, FK, wajib | |
| `odk_row_id` | ID Baris ODK | text, unik, wajib | kunci anti-dobel: ID baris *repeat group* di ODK |
| `procurement_item_id` | ID BoQ Permintaan | int, FK | lihat bagian 3 |
| `contract_item_id` | ID Rincian Kontrak | int, FK | minimal satu dari dua kolom ini terisi; jasa yang dikerjakan sendiri tidak punya BoQ Permintaan |
| `component_label` | Komponen | text | mis. "Switch 5 port" |
| `serial_number` | Nomor Seri | text | hasil scan barcode di ODK, tidak diketik |
| `service_period` | Periode Layanan | text | untuk pemeliharaan/layanan berkala, mis. "2026-03" |
| `auto_check_notes` | Catatan Cek Otomatis | text | |
| `review_status`, `reviewed_by`, `reviewed_at`, `review_note` | Status Review, Diperiksa Oleh, Waktu Diperiksa, Catatan Review | | milik PM (`written_by="human"`), sama seperti di `evidence_photo` |

**`evidence_file` — Berkas Evidence.** Satu baris per foto atau berkas.

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `site_visit_id` | ID Kunjungan | int, FK, wajib | |
| `evidence_unit_id` | ID Unit Evidence | int, FK | kosong untuk foto kegiatan per lokasi (jasa instalasi di B) |
| `odk_attachment_name` | Nama Lampiran ODK | text, wajib | kunci anti-dobel bersama `site_visit_id` |
| `shot_type` | Jenis Foto | enum, wajib | `label_kardus`, `label_sn`, `kelengkapan`, `terpasang`, `proses_pasang`, `hasil_uji`, `lokasi_luas`, `bersama_pic`, `screenshot`, `laporan` |
| `file_url` | Tautan Berkas | text, wajib | lihat 2g |
| `file_sha256` | Sidik Berkas | text | foto yang sama dipakai untuk dua unit langsung terlihat |
| `taken_at` | Waktu Ambil | timestamptz | |
| `exif_lat`, `exif_lon` | Lintang EXIF, Bujur EXIF | coord | sering kosong: aplikasi pesan membuang EXIF |
| `decoded_sn` | SN Terbaca dari Foto | text | hasil decode barcode, dibandingkan dengan `serial_number` |
| `auto_check_notes` | Catatan Cek Otomatis | text | |

Jenis `laporan` dengan berkas PDF menjawab sebagian 2a: laporan bulanan (D) masuk ke tabel yang
sama. Berita acara yang dibuat BUT sendiri (BAUT, BARD) tetap keluaran BAST, bukan evidence.

**`evidence_rule` — Aturan Evidence.** Seluruh tabel ditulis Network Engineer
(`written_by="human"`).

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `activity_type` | Jenis Kegiatan | enum, wajib | |
| `evidence_kind` | Jenis Bukti | enum | sama dengan `procurement_item.evidence_kind`; kosong untuk aturan per lokasi |
| `shot_type` | Jenis Foto | enum, wajib | kunci: (`activity_type`, `evidence_kind`, `shot_type`) |
| `scope` | Berlaku Per | enum, wajib | `unit`, `lokasi`, `periode` |
| `min_count` | Jumlah Minimal | int, wajib | |
| `guidance` | Panduan | text | kalimat untuk teknisi, mis. "barcode SN harus terbaca" |

Contoh isi awal, untuk disepakati dengan Network Engineer:

| Kegiatan | Jenis bukti | Foto wajib | Per |
|---|---|---|---|
| pengadaan | perangkat_ber_sn | label_kardus, label_sn, kelengkapan | unit |
| pengadaan | material | label_kardus, kelengkapan | unit (roll/box) |
| pengadaan | lisensi | screenshot | unit |
| instalasi | perangkat_ber_sn | label_sn, proses_pasang, terpasang | unit |
| instalasi | jasa | proses_pasang | lokasi |
| semua kegiatan | (kosong) | bersama_pic | lokasi |
| pemeliharaan | layanan_berkala | laporan | periode |
| pemeliharaan | perangkat_ber_sn | belum diketahui | belum ada contoh nyata |

#### Usulan cek otomatis (jawaban 2c)

Dijalankan di n8n setelah kiriman ODK masuk; hasilnya ditulis ke `auto_check_notes`. Mesin
hanya menandai, PM yang memutuskan.

1. **Kelengkapan:** berkas yang masuk dibandingkan dengan Aturan Evidence.
2. **Lokasi:** jarak geopoint ODK ke titik lokasi kontrak ≤ radius yang disepakati (2f). Titik
   lokasi di-pin sekali per lokasi dan dikonfirmasi PM. Alamat teks tidak bisa dicocokkan: di A,
   nama jalan di stempel foto berbeda dengan alamat di kontrak, walau nomor dan kelurahannya
   sama.
3. **Koordinat kembar:** di B, foto dengan lebih dari 10 label lokasi berbeda, diambil selama
   9 hari, berkoordinat persis sama sampai 6 desimal. GPS sungguhan tidak sepresisi itu; hampir
   pasti lokasi di aplikasi kamera diisi manual. Karena itu stempel lokasi yang tercetak di foto
   tidak dipakai sebagai bukti, dan koordinat identik di lokasi berbeda ditandai.
4. **Tanggal:** tanggal kontrak ≤ waktu foto ≤ tanggal BAST. Foto pengadaan/instalasi yang lebih
   baru dari "tanggal aktif" di BAST menjadi peringatan, bukan penolakan. Di B, tanggal aktif yang
   ditulis BAST 8–16 hari lebih awal dari seluruh foto pengadaan dan pemasangan. Di A, tanggal
   foto = tanggal nota pesanan = tanggal aktif.
5. **SN:** format sesuai seri dan unik lintas proyek. Di B (149 SN tertulis), 1 SN tercatat di
   dua baris BoQ, dan 2 SN diketik dengan huruf "I" menggantikan angka "1". Keduanya tidak
   terjadi bila SN diambil dari scan dan dicek keunikannya.
6. **SN dari foto:** barcode di foto label kardus dan label perangkat di-decode, lalu
   dibandingkan dengan SN hasil scan. Pemeriksaan deterministik, bukan tebakan LLM.
7. **Foto dipakai ulang:** `file_sha256` yang sama muncul di dua unit.

Usul jawaban 2b: n8n membangkitkan daftar baris BoQ per proyek sebagai berkas CSV atau Entity
di ODK Central, sehingga teknisi memilih dari daftar dan tidak mengetik ID.

### 3. Pengadaan (bersama RPA Engineer): usulan dari permintaan RPA

Permintaan RPA (2026-10-09): tabel Vendor, BoQ Permintaan, Proyek (id_leads), Spesialisasi
Vendor, dan tabel penerima balasan. BoQ Permintaan menjawab 3a; SPPH dan balasan menjawab 3b.

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 3a | Tabel **procurement item** (barang yang dibeli) terpisah dari Rincian Kontrak (barang yang dijual)? | Briefing hlm. 7 memisahkan keduanya; satu baris kontrak bisa butuh beberapa barang beli. Tabel banding harga (Bulan 5) bergantung pada ini. Usul: ya, sebagai BoQ Permintaan. |
| 3b | Tabel **SPPH** (permintaan ke vendor) dan pelacakan balasan (threadId Gmail): milik siapa? | Diagnosis no. 2 "balasan vendor tak terlacak" (hlm. 5). Usul: milik RPA, tabel SPPH, Isi SPPH, Balasan Vendor. |
| 3c | Tabel **Vendor** dan **Proyek** yang diminta RPA bertentangan dengan aturan 5 (data vendor & proyek milik MyBhakti). Dibuat sebagai pelengkap berkunci `mybhakti_*_ref`, atau dibaca langsung dari MyBhakti? | Jawabannya bergantung pada isi endpoint MyBhakti (inventaris RPA Bulan 1). |
| 3d | Calon vendor yang belum pernah menerima PO: sudah ada di MyBhakti? Kalau belum, apa kuncinya? | `mybhakti_vendor_ref` tidak bisa jadi kunci untuk vendor yang belum terdaftar. |
| 3e | Satu SPPH = satu vendor (satu nomor, satu penerima), atau satu nomor untuk banyak vendor? | Template SPPH (E): satu surat, satu nama penerima, satu nomor. Menentukan kunci `spph`. |

#### 3c lebih dulu: batas MyBhakti

Aturan 5 di AGENTS.md (briefing hlm. 7): vendor dan proyek milik MyBhakti. Usul:

- Endpoint vendor MyBhakti sudah punya email, HP, dan PIC → **tidak** ada tabel Vendor. n8n
  membaca MyBhakti saat mengirim SPPH, dan baris SPPH menyimpan salinan penerima.
- Tidak punya → tabel Vendor sebagai **pelengkap**: kunci `mybhakti_vendor_ref`, kolom yang
  berasal dari MyBhakti adalah salinan sinkron n8n dan tidak diedit tangan.
- Tabel Proyek hanya dibuat bila Kategori Bisnis tidak ada di MyBhakti. Kontrak dan SPH Vendor
  sudah membawa `mybhakti_project_ref`, jadi tabel yang berlaku tidak berubah.
- Bila salah satu disetujui, aturan 5 perlu dirumuskan ulang (mis. "tidak ada tabel yang
  **menduplikasi** data MyBhakti"), supaya AGENTS.md, README, dan pembahasan berikutnya tetap
  konsisten.

#### Usulan tabel

**`procurement_item` — BoQ Permintaan** (jawaban 3a). Menjembatani ketiga tim: RPA meminta harga
per baris ini, AI mencocokkan baris SPH ke sini (tabel banding Bulan 5), Network memotret per
baris ini.

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `mybhakti_project_ref` | Rujukan Proyek MyBhakti | text, wajib | id_leads; pengikat |
| `line_no` | No Urut | int, wajib | kunci anti-dobel: (`mybhakti_project_ref`, `line_no`) |
| `description` | Uraian | text, wajib | |
| `specification` | Spesifikasi | text | |
| `quantity` | Volume | numeric | |
| `unit` | Satuan | text | |
| `period` | Periode | text | layanan per bulan (B: masa layanan dalam bulan; D: 6 bulan) |
| `item_category` | Kategori Barang | enum | taksonomi yang sama dengan spesialisasi vendor, jadi n8n bisa memilih vendor otomatis |
| `evidence_kind` | Jenis Bukti | enum | `perangkat_ber_sn`, `material`, `lisensi`, `jasa`, `layanan_berkala`; dipakai Aturan Evidence (bagian 2) |
| `contract_item_id` | ID Rincian Kontrak | int, FK | boleh kosong; diisi setelah kontrak ada |

Kenapa terpisah dari Rincian Kontrak: di A, kontrak menulis satu baris "1 Paket", tapi yang
dibeli dan difoto adalah 12 unit dari 5 jenis. Kenapa `contract_item_id` boleh kosong: di A, SPH
BUT ke pelanggan terbit 2 hari sebelum nota pesanan, jadi permintaan harga ke vendor terjadi
sebelum Rincian Kontrak ada.

Draf daftar Kategori Barang (dari ±25 nama proyek di arsip, disepakati RPA): `perangkat_jaringan`,
`perangkat_keamanan`, `server_penyimpanan`, `kabel_material`, `lisensi_perangkat_lunak`,
`layanan_cloud`, `jasa_instalasi`, `layanan_terkelola`, `pelatihan`, `konsultasi`,
`tenaga_ahli`, `pengembangan_aplikasi`, `lainnya`.

**`project` — Proyek** (hanya bila 3c memutuskan perlu)

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `mybhakti_project_ref` | Rujukan Proyek MyBhakti | text, unik, wajib | id_leads |
| `work_title` | Nama Pekerjaan | text | salinan dari MyBhakti |
| `business_category` | Kategori Bisnis | enum | `perangkat_infrastruktur`, `solusi_teknologi`, `konsultasi` |

**`vendor` — Vendor** (hanya bila 3c memutuskan perlu)

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `mybhakti_vendor_ref` | Rujukan Vendor MyBhakti | text, unik | kunci; lihat 3d |
| `vendor_type` | Jenis Vendor | enum | `badan_usaha`, `perorangan`. E: SPK dan BAKN ditujukan ke perorangan |
| `company_name` | Nama Perusahaan | text | kosong untuk perorangan |
| `pic_name` | Nama Perwakilan | text | yang ditulis sebagai "Kepada Yth." di SPPH |
| `pic_title` | Jabatan Perwakilan | text | |
| `email` | Email | text | |
| `email_cc` | Email CC | text | |
| `phone` | No HP | text | kop SPH vendor di F memuat 2 nomor telepon dan 2 email |
| `address_text` | Alamat | text | |
| `status` | Status | enum | `aktif`, `nonaktif` (model belum punya tipe boolean) |

**`vendor_specialization` — Spesialisasi Vendor** (usulan no. 4 RPA)

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `vendor_id` | ID Vendor | int, FK, wajib | atau `mybhakti_vendor_ref` bila tabel Vendor tidak dibuat |
| `item_category` | Kategori Barang | enum, wajib | kunci: (`vendor_id`, `item_category`) |
| `note` | Keterangan | text | mis. "distributor resmi merek X" |

Alternatifnya kolom pilihan ganda (MultiSelect) di tabel Vendor: lebih praktis di NocoDB, tapi
model belum punya tipe itu, dan nilainya tersimpan sebagai teks dipisah koma yang tidak bisa
dijaga CHECK di PostgreSQL. Tabel kecil ini tidak butuh tipe baru.

**`spph` — SPPH** (jawaban 3b). Satu baris per surat (lihat 3e).

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `spph_number` | Nomor SPPH | text, unik, wajib | dari numbering service; kunci anti-dobel |
| `mybhakti_project_ref` | Rujukan Proyek MyBhakti | text, wajib | |
| `mybhakti_vendor_ref` | Rujukan Vendor MyBhakti | text | atau `vendor_id` bila tabel Vendor dibuat |
| `spph_date` | Tanggal SPPH | date | |
| `subject` | Perihal | text | |
| `recipient_name` | Kepada | text | salinan saat kirim: PIC vendor bisa berganti, surat yang terkirim tidak |
| `recipient_email` | Email Tujuan | text | salinan saat kirim |
| `reply_deadline` | Batas Balasan | date | E: "7 hari kerja sejak surat diterbitkan" |
| `gmail_thread_id` | ID Thread Gmail | text | |
| `sent_at` | Waktu Kirim | timestamptz | |
| `status` | Status | enum, wajib | `draf`, `terkirim`, `dibalas`, `menolak`, `tidak_membalas`, `batal` |
| `reminder_count` | Jumlah Pengingat | int | |
| `doc_url` | Tautan Berkas | text | PDF hasil render |

**`spph_item` — Isi SPPH**

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `spph_id` | ID SPPH | int, FK, wajib | |
| `procurement_item_id` | ID BoQ Permintaan | int, FK, wajib | |
| `line_no` | No Urut | int, wajib | urutan di surat; kunci: (`spph_id`, `line_no`) |

Diperlukan karena vendor kabel tidak dimintai harga switch, renderer SPPH butuh daftar baris per
surat, dan tabel banding harus bisa membedakan "tidak diminta" dari "diminta tapi tidak
ditawar".

**`vendor_reply` — Balasan Vendor** (usulan no. 5 RPA). Satu baris per email masuk; isi email
tidak disimpan, hanya metadata.

| Kolom | Judul | Tipe | Catatan |
|---|---|---|---|
| `gmail_message_id` | ID Pesan Gmail | text, unik, wajib | kunci anti-dobel: polling tiap 5–15 menit (hlm. 9) membaca pesan yang sama berulang kali |
| `gmail_thread_id` | ID Thread Gmail | text | |
| `spph_id` | ID SPPH | int, FK | dicocokkan lewat thread; kosong bila email datang di luar thread |
| `received_at` | Waktu Terima | timestamptz, wajib | |
| `from_email` | Pengirim | text | |
| `subject` | Subjek | text | |
| `reply_type` | Jenis Balasan | enum | `sph`, `pertanyaan`, `menolak`, `balasan_otomatis`, `lainnya` |
| `attachment_count` | Jumlah Lampiran | int | |
| `document_id` | ID Dokumen | int, FK | lampiran PDF yang diproses dol-parser |
| `handling_status` | Status Tindak Lanjut | enum, wajib | `baru`, `diproses_parser`, `perlu_dibaca_manusia`, `selesai` |

Dengan ini "balasan vendor tak terlacak" (hlm. 5) menjadi satu query: SPPH berstatus
`terkirim` yang sudah lewat Batas Balasan tanpa Balasan Vendor.

### 4. Infrastruktur (bersama + mentor)

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 4a | PostgreSQL + NocoDB sebagai sumber eksternal, atau NocoDB murni? | Tabel yang dibuat lewat API NocoDB **tidak punya** UNIQUE, CHECK, FK, maupun view. Integritas hanya dijaga pengirim. |
| 4b | Export skema NocoDB ke Git tiap minggu (hlm. 20): siapa, bagaimana? | `scripts/nocodb_setup.py --compare-schema` di dol-parser bisa jadi pemeriksanya. |

### 5. SPH Vendor (AI Engineer): penyesuaian untuk alur SPPH

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 5a | Tabel SPH Vendor perlu kolom arah: SPH masuk dari vendor vs SPH yang diterbitkan BUT ke pelanggan? | 2 dari 3 SPH di golden set (F) adalah SPH terbitan BUT. Tanpa pembeda, SPH BUT ikut masuk tabel banding harga vendor. Usul kolom `direction` (*Arah*): `masuk_dari_vendor`, `keluar_ke_pelanggan`. Golden set juga perlu ditambah SPH vendor. |
| 5b | Hubungkan SPH ke SPPH: `sph.spph_id` (diisi n8n dari thread Gmail) + `sph.spph_number_ref_text` (*Nomor SPPH Dirujuk*, dibaca parser)? | Template SPH (E) menulis "Merujuk Surat Permintaan Penawaran Harga Nomor …"; SPH vendor di F tidak. Bila dua sumber berbeda → tanda untuk PM. |
| 5c | Simpan kontak vendor dari kop SPH: `vendor_address_text`, `vendor_contact_text`? | dol-parser sudah mengekstraknya (`app/schemas/sph.py`: Alamat Vendor, Kontak / Email), tapi pemeta hanya menyimpan Nama Vendor. Bisa jadi usulan isi tabel Vendor, dikonfirmasi PM. |
| 5d | `sph_item.procurement_item_id` untuk tabel banding (Bulan 5)? | Menggantikan relasi `sph_item.contract_item_id` yang dihapus di 2026.10.2 karena mengandaikan 1 barang jual = 1 barang beli. |

Catatan pendukung desain sekarang: di A, harga SPH BUT ke pelanggan lebih tinggi daripada nilai
nota pesanan (turun setelah negosiasi). Ini menegaskan BAST bersumber dari kontrak, bukan SPH
(view `nilai_terverifikasi`).

### 6. Tiga BoQ dan cara PM memeriksa (AI Engineer, bersama RPA): usulan 2026-10-10

Pemicu: uji jalur `POST /api/v1/jobs` + push pada 10 Oktober 2026. Satu SPH dua halaman dengan
18 baris penawaran menjadi **238 baris** di NocoDB: Dokumen 1, SPH Vendor 1, Rincian SPH 18,
Hasil Ekstraksi 218. Dari 218 itu, 198 adalah sel rincian (18 baris × 11 kolom) yang ditulis
ulang satu per satu. Yang terbaca sebagai database wajar hanya 20 baris pertama.

Bahan tambahan, belum masuk tabel [Bahan bukti](#bahan-bukti): **G** = lampiran rincian
pekerjaan sebuah kontrak layanan; **H** = BAST + lampiran + BAUT satu pekerjaan perangkat
pendukung; **I** = lampiran rincian sebuah SPH jasa dengan baris berkelompok. G dan H berasal
dari proyek yang berbeda, jadi keduanya tidak bisa dibandingkan baris per baris.

#### Tiga BoQ, satu yang mengikat

| BoQ | Datang dari | Sifat | Harga | Tabel | Dipakai untuk |
|---|---|---|---|---|---|
| Permintaan | SPPH | belum final; masih bisa berubah selama negosiasi di PMO | **belum ada**: justru ini yang ditanyakan | BoQ Permintaan (`procurement_item`, usulan bagian 3) | meminta harga |
| Penawaran | SPH, sebagai balasan atas SPPH | catatan; bisa lebih dari satu (per vendor, per putaran negosiasi) | harga yang ditawarkan | Rincian SPH | tabel banding, jejak negosiasi |
| Kontrak | kontrak, SPK, nota pesanan, atau PKS yang sudah ditandatangani | final; disepakati kedua pihak | harga yang disepakati | Rincian Kontrak | **satu-satunya acuan BAST** |

Aturan yang diusulkan:

1. **BAST hanya dibangun dari BoQ Kontrak yang sudah dikunci PM.** BoQ Permintaan dan BoQ
   Penawaran tidak pernah mengisi BAST, walau isinya mirip. Catatan di bagian 5 (harga SPH lebih
   tinggi dari nilai nota pesanan) adalah buktinya.
2. **Ketiganya disimpan dan tidak saling menimpa.** SPH revisi setelah negosiasi adalah berkas
   baru dengan sidik berkas lain, jadi masuk sebagai SPH baru; yang lama tetap sebagai catatan.
3. **Nomor urut hanya bermakna di dalam induknya** (kunci: induk + No Urut, sudah berlaku).
   Baris antar-BoQ dihubungkan lewat kolom relasi (`sph_item.procurement_item_id` di 5d,
   `procurement_item.contract_item_id` di bagian 3), bukan lewat kesamaan nomor urut.
4. Tiga tahap ini berlaku untuk dua arah (BUT dengan pelanggan, BUT dengan vendor); pembeda
   arahnya ada di 5a.
5. **BoQ Permintaan tidak punya kolom harga**, dan usulan `procurement_item` di bagian 3 memang
   tidak memuatnya. Harga baru muncul di Rincian SPH. Karena itu tabel banding (Bulan 5) dibaca
   per baris BoQ Permintaan: satu baris permintaan, satu harga dari tiap vendor yang membalas.
   Pasangannya adalah `sph.spph_id` (surat mana yang dibalas, 5b) dan
   `sph_item.procurement_item_id` (baris mana yang dijawab, 5d).
6. **Balasan vendor tidak selalu sebaris dengan permintaan.** Vendor bisa menawar volume, merek,
   atau spesifikasi yang berbeda, menggabung beberapa baris menjadi satu paket, menambah baris
   yang tidak diminta, atau melewati baris yang diminta. Jadi pasangan baris diusulkan
   dol-parser dan dikonfirmasi PM, bukan dicocokkan otomatis lewat nomor urut. Baris SPH tanpa
   pasangan tetap disimpan dengan `procurement_item_id` kosong. Daftar variasi ini masih
   dugaan: belum ada pasangan SPPH dan SPH balasannya di bahan bukti, dan golden set baru punya
   satu SPH vendor (5a).

#### Yang harus diputuskan

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 6a | Rincian SPH dan Rincian Kontrak diperiksa PM **per baris**, bukan per sel? | Briefing hlm. 11 meminta konfirmasi per field untuk "15–20 field administratif" kontrak; hlm. 14 (Bulan 3) menyebut "grid verifikasi SPH". Konfirmasi per sel untuk rincian tidak diminta, dan 198 baris per SPH tidak akan dibaca. Usul: ya. |
| 6b | Hasil Ekstraksi hanya memuat field kepala dokumen? | Mengikuti 6a. SPH contoh turun dari 238 ke 40 baris. Bukti per sel tetap utuh di `.extract.json`. Usul: ya. |
| 6c | Keputusan PM per baris disimpan di mana? | Usul: kolom milik manusia di baris rincian, pola yang sama dengan Unit Evidence (bagian 2): `review_status` (`benar`, `dikoreksi`, `ditolak`), `reviewed_by`, `reviewed_at`, `review_note`. Ditambah kolom mesin ringkasan per baris: `system_status` (status terburuk dari sel-selnya), `evidence_score_min`, `evidence_page`. |
| 6d | Koreksi PM atas nilai sebuah baris: diketik langsung di selnya, atau di kolom koreksi terpisah? | Langsung di sel paling mudah bagi PM, tapi melanggar "satu penulis per kolom" dan butuh kunci per baris supaya proses ulang tidak menimpanya. Kolom terpisah menjaga prinsip itu, tapi menggandakan lebar tabel. Usul: langsung di sel, dan baris yang sudah punya `review_status` tidak ditimpa pusher. View `nilai_terverifikasi` harus ikut membaca baris rincian. |
| 6e | "Harga selalu diverifikasi manusia" (hlm. 20) terpenuhi dengan grid per baris? | Usul: ya, dengan syarat setiap baris harus punya `review_status` sebelum dipakai dokumen hilir, apa pun status buktinya. |
| 6f | Tabel asli dan judul tabel untuk lampiran BAST disimpan di mana? | Lampiran BAST memuat tabel rincian beserta judulnya (H), dan judul serupa ada di lampiran kontrak (G). Bentuk tabel berbeda-beda: kolom harga terpecah OTC/MRC (G), baris berkelompok dengan sel gabungan (I), kolom spesifikasi terpisah dari jumlah (H). Kolom inti Rincian Kontrak tidak bisa mencetak ulang bentuk itu. dol-parser sudah menghasilkan "Daftar Tabel Terstruktur", tapi skema belum punya tempatnya. Usul: tabel **Tabel Kontrak** (`contract_table`): `contract_id`, `line_no`, `table_title`, `headers_text`, `rows_text` (JSON sebagai teks; model belum punya tipe JSON), `evidence_page`. |
| 6g | Kolom lampiran BAST yang tidak berasal dari kontrak: siapa yang mengisi, dan kapan? | H memuat tanggal aktif, nomor order dan ID layanan, serta lokasi per baris. Salah satu tanggal aktifnya empat bulan setelah tanggal nota pesanan, jadi hampir pasti bukan isi kontrak (kontrak H sendiri belum dilihat). Rincian BAST (ditunda) sudah punya kolomnya; yang belum ada adalah sumber datanya. |
| 6h | Penanda tangan BAST boleh berbeda dari penanda tangan kontrak? | Belum ada pasangan kontrak dan BAST dari proyek yang sama untuk membuktikannya. Usul sementara: Pihak BAST diisi usulan dari Pihak Kontrak, lalu dikonfirmasi PM di draf. Perlu satu pasangan dokumen nyata sebelum diputuskan. |
| 6i | "Nilai Pekerjaan" di BAST: nilai sebelum atau sesudah PPN? | H menulis nilai "belum termasuk PPN". Kontrak menyimpan Subtotal dan Nilai Kontrak. Usul: mengikuti template pelanggan dan dikonfirmasi PM di draf; tidak ditebak mesin. |
| 6j | Rujukan proyek: diisi siapa, dan kapan? | dol-parser tidak tahu proyeknya; `mybhakti_project_ref` diisi n8n. Pada uji 10 Oktober, baris masuk tanpa rujukan, sehingga PM yang memegang beberapa proyek paralel tidak bisa menyaringnya. Usul: aturan tetap (n8n yang mengisi), segera setelah push; tampilan PM menaruh dokumen tanpa rujukan di antrean tersendiri. |

#### Field yang dibutuhkan draf BAST, dan asalnya

Daftar dari AI Engineer (2026-10-10). "Ditunda" berarti tabelnya masih usulan.

| # | Field | Asal | Tempat di skema |
|---|---|---|---|
| 1 | Nama pekerjaan | kontrak, dikunci PM | `contract.work_title` |
| 2 | Nomor kontrak | kontrak, dikunci PM | `contract.contract_number` |
| 3 | Nomor BAST BUT | numbering service (1b) | `bast.bast_number_internal` (ditunda) |
| 4 | Nomor BAST pelanggan | pelanggan | `bast.bast_number_customer` (ditunda) |
| 5 | Tanggal kontrak | kontrak, dikunci PM | `contract.contract_date`, `contract_date_text` |
| 6 | Nilai pekerjaan | kontrak, dikunci PM | `contract.subtotal_value` atau `contract_value` (6i) |
| 7, 8 | Pihak pertama dan kedua: nama, jabatan, instansi, alamat | kontrak, dikunci PM | `contract_party` |
| 9 | Waktu dan tanggal serah terima | diisi PM saat serah terima | `bast_draft.handover_date`, `handover_date_text` (ditunda) |
| 10 | Jumlah terbilang | kontrak; dicek terhadap angkanya (aturan checker bagian 1) | belum punya kolom di Kontrak; hanya jenis kondisi `amount_in_words` di Kondisi BAST (ditunda) |
| 11 | Tabel rincian, sama dengan kontrak | BoQ Kontrak, diperiksa PM per baris | `contract_item` + tabel asli (6f) |
| 12 | Judul tabel | kontrak | belum ada (6f) |
| 13 | Skema pembayaran | kontrak, dikunci PM | `contract.payment_mechanism`, `contract_payment_term` |
| 14 | Penanda tangan kedua pihak | usulan dari kontrak, dikonfirmasi PM (6h) | `bast_party` (ditunda) |
| 15 | Lampiran rincian dengan foto evidence | lapangan, lewat ODK | bagian 2 |
| 16 | Nomor seri tiap unit | lapangan, lewat ODK | `evidence_unit.serial_number` (usulan bagian 2) |

Belum ada di daftar, tapi tertulis di badan BAST (H): tanggal berita acara uji terima dan
tanggal berita acara rekonsiliasi delivery. Kondisi BAST (ditunda) sudah punya jenisnya
(`acceptance_test_ref`, `delivery_reconciliation_ref`).

#### Bila disetujui

- **dol-schema:** kolom review dan ringkasan di `sph_item` dan `contract_item` (6c), tabel
  `contract_table` (6f), kolom terbilang di Kontrak (field 10); versi naik.
- **dol-parser:** pemeta berhenti mengirim sel rincian ke Hasil Ekstraksi, mengisi ringkasan
  per baris, dan mengirim tabel asli; pusher tidak menimpa baris yang sudah diputuskan PM;
  `TAMPILAN_PM` di `scripts/nocodb_setup.py` disesuaikan.
- **n8n:** mengisi rujukan proyek segera setelah push (6j) dan membaca keputusan per baris.

---

## Kontrak antar-service

| Dari | Ke | Bentuk | Status |
|---|---|---|---|
| n8n | parser | `POST /api/v1/jobs` (multipart + `callback_url`) | ✅ jalan |
| parser | n8n | `companion_payload` (nama teknis) + `companion_catatan` | ✅ jalan |
| n8n/parser | NocoDB | rekaman dengan **judul** kolom (`columns[].label` di schema.json) | ✅ pusher dol-parser; n8n menyesuaikan |
| MyBhakti | n8n | baca vendor & proyek (read-only) | ⬜ keputusan 3c |
| n8n | Gmail | kirim SPPH, baca balasan (`gmail_thread_id`, `gmail_message_id`) | ⬜ keputusan 3b |
| n8n | ODK | daftar baris BoQ per proyek (CSV/Entity) | ⬜ keputusan 2b |
| ODK | n8n | kiriman per kunjungan; unit = *repeat group* | ⬜ keputusan 2 |
| numbering | n8n | nomor SPPH & BAST; nomor BAST dipesan setelah disetujui | ⬜ keputusan 1b |

## Setelah workshop

```bash
# ubah dol_schema/model.py sesuai kesepakatan: status "ditunda" -> "berlaku", naikkan versi
python -m dol_schema --emit && python -m pytest tests
# catat di CHANGELOG.md, lalu buat base NocoDB baru dari dol-parser:
python scripts/nocodb_setup.py --create-base
```

Bila usulan 2026-10-09 disetujui, ada pekerjaan tambahan di luar `model.py`:

- Tipe kolom lampiran (foto, TTD) belum ada di `ddl.py`/`export.py`; tergantung keputusan 2g.
- Aturan 5 di AGENTS.md dan README dirumuskan ulang bila tabel Vendor/Proyek disetujui (3c).
- dol-parser: pemeta SPH untuk kolom 5a–5c, dan golden set SPH vendor.
