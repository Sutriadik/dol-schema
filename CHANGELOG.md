# Changelog — dol-schema

Semua perubahan skema data Delivery Ops Layer dicatat di sini. Tiga repo bergantung pada
skema ini (`dol-parser`, `dol-n8n`, `dol-bast-compiler`), jadi setiap perubahan tabel atau
kolom harus terlihat di sini **sebelum** repo lain ikut menyesuaikan.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.1.0/). Versi skema
adalah nilai `SCHEMA_VERSION` di `dol_schema/model.py`.

## Aturan versi

Format: `companion-TAHUN.BULAN.N`, mis. `companion-2026.10.1`.

Naikkan `SCHEMA_VERSION` **setiap kali** tabel, kolom, tipe, pilihan nilai (enum), atau
relasi berubah — termasuk penambahan. Perubahan yang TIDAK menaikkan versi: dokumentasi,
komentar, dan artefak turunan baru yang tidak mengubah bentuk data.

Setiap entri menyebut **dampak untuk konsumen**:

| Label | Artinya bagi n8n / compiler BAST / dol-parser |
|---|---|
| **aman** | hanya penambahan; payload lama tetap diterima |
| **perlu penyesuaian** | nama/tipe kolom berubah atau kolom wajib baru; konsumen harus diubah |
| **perlu migrasi data** | data yang sudah tersimpan harus diubah atau dipindah |

Langkah setiap perubahan skema:

1. Ubah `dol_schema/model.py`, naikkan `SCHEMA_VERSION`.
2. `python -m dol_schema --emit`, lalu commit `model.py` + `generated/` bersamaan.
3. Tambah entri di berkas ini.
4. Di dol-parser: sesuaikan pemeta, jalankan tes, lalu
   `scripts/nocodb_setup.py --compare-schema` untuk memastikan NocoDB masih sama.
5. Beri tahu pemilik n8n dan compiler BAST bila dampaknya bukan **aman**.

---

## [Belum dirilis]

Belum ada perubahan.

## [companion-2026.10.3] — 2026-10-04

### Dihapus — dampak: **perlu penyesuaian**
- `contract_party.npwp` dan `sph.vendor_npwp`. NPWP tidak dipakai di BAST maupun di
  verifikasi PM, jadi tidak disimpan (keputusan pengguna). dol-parser tetap meminta NPWP
  di prompt LLM: menghapusnya dari prompt diukur menurunkan akurasi field lain (lenient
  0,884 -> 0,858; nilai salah yang lolos 4 -> 8), jadi pemeta yang membuangnya.
  Konsekuensi untuk n8n: pencocokan vendor SPH ke data vendor MyBhakti
  (`sph.mybhakti_vendor_ref`) hanya bisa lewat nama vendor, yang ejaannya sering berbeda
  antar-dokumen. Base NocoDB 2026.10.2 belum pernah dibuat, jadi tidak ada data yang hilang.

## [companion-2026.10.2] — 2026-10-02

Fokus: hanya yang sudah pasti yang berlaku; semua yang terlihat orang kantor berbahasa
Indonesia. **Wajib membuat base NocoDB baru** (judul kolom dan pilihan nilai berubah).

### Diubah — dampak: **perlu migrasi data** (base NocoDB baru)
- **Judul tabel & kolom di NocoDB kini bahasa Indonesia** (`Table.label`, `Column.label`),
  mis. `contract.contract_number` tampil sebagai *Kontrak → Nomor Kontrak*. Nama teknis
  tidak berubah. API rekaman NocoDB memakai **judul** sebagai kunci, jadi setiap pengirim
  menerjemahkan lewat `to_nocodb_record()` / `columns[].label` di schema.json.
- **Pilihan nilai yang tampil di sel NocoDB kini bahasa Indonesia:**
  `doc_type` (`kontrak`/`sph`/`bast`), `contract_type` (`other` → `lainnya`),
  `contract_party.role` (`pemberi_kerja`/`pelaksana`), `requirement_type`
  (`lampiran_wajib`/`syarat_serah_terima`/`boleh_parsial`), `field_review.decision`
  (`benar`/`dikoreksi`/`ditolak`), dan `extracted_field.system_status`
  (`bukti_kuat`, `bukti_cukup`, `perlu_dicek`, `tidak_ada_di_dokumen`, `bertentangan`,
  `kosong`). `auto_verified` diganti karena terbaca "sudah diverifikasi", padahal sistem
  hanya memeriksa keberadaan nilai di dokumen.
- `document.content_hash` = **sha256** isi berkas (dol-parser dulu mengirim sha1 di sini
  sementara `document_id` ke n8n sha256 -- keduanya tidak pernah cocok).
- **Ditunda (status `ditunda`, tidak dibuat di NocoDB):** `bast`, `bast_party`, `bast_item`,
  `bast_condition`, `bast_draft`, `evidence_photo`. Menunggu kesepakatan dengan RPA dan
  Network Engineer. DDL-nya pindah ke `generated/schema_usulan.sql` bersama view
  `bast_rincian`, `evidence_siap_lampiran`, `checklist_gabungan`.
- **Dihapus:** `sph_item.contract_item_id`. Menghubungkan baris SPH langsung ke baris kontrak
  mengandaikan satu barang jual = satu barang beli; briefing hlm. 7 memisahkan contract item
  dan procurement item. Dirancang ulang bersama tabel banding (Bulan 5). Belum pernah diisi.
- `nocodb_fields.json` berbentuk `{tabel: {title, description, columns: [{column_name,
  title, uidt, ...}]}}`; `schema.json` memuat `label` & `status`, dan `insert_order` hanya
  berisi tabel yang berlaku.

### Ditambahkan — dampak: **aman**
- View `nilai_terverifikasi`: satu-satunya sumber nilai untuk dokumen hilir (BAST) --
  hanya field yang diputuskan PM `benar`/`dikoreksi` dan belum basi.
- `contract.location_text` (sudah diekstrak sebagai "Lokasi", dulu tidak tersimpan),
  `contract_party.party_label_text` (sebutan "PIHAK PERTAMA" apa adanya; peran disimpan
  terpisah), `contract_requirement.evidence_page`.
- `COMMENT ON TABLE/COLUMN` di DDL berisi label Indonesia + keterangan.
- Konvensi baru di schema.json: `status_tabel`, `judul_nocodb`, `dokumen_sudah_direview`,
  `nilai_terverifikasi`.
- `docs/WORKSHOP_SKEMA.md` (keputusan yang masih terbuka) dan
  `docs/usulan-alur-bast/TEMUAN_14_BAST.md` (temuan 14 BAST asli), dipindah dari dol-parser.
- Tes invarian: label wajib & aman untuk API NocoDB, tabel berlaku tidak bergantung pada
  usulan, tabel berlaku yang ditulis mesin wajib punya kunci anti-dobel (18 tes).

### Dilonggarkan — dampak: **aman**
- `contract.work_title`, `contract_party.signer_name` (dan pada tabel usulan:
  `bast.work_title`, `bast_party.signer_name`) boleh kosong. Kolom wajib untuk nilai yang
  bisa tidak terbaca mendorong pengirim mengarang pengisi ("(tidak terbaca)", nama berkas
  sebagai judul pekerjaan).

### Diperbaiki
- `document_review_status` tidak lagi menghitung keputusan PM yang basi sebagai
  terverifikasi; ada kolom `stale_count`. Diuji di PostgreSQL 18.
- `bast_rincian` (usulan) memakai volume BAST lebih dulu: serah terima parsial.

## [companion-2026.10.1] — 2026-10-01

Merapikan skema untuk tiga tim dan PM: kontrak data eksplisit untuk n8n, tabel evidence untuk
Network Engineer, tampilan NocoDB yang terbaca PM, dan resep penyusunan BAST. 16 tabel
(15 di NocoDB). **Semua kolom & tabel lama tetap** — diverifikasi dengan membandingkan
schema.json sebelum/sesudah: nol kolom hilang atau berubah tipe.

### Ditambahkan — dampak: **aman** (hanya penambahan)
- Tabel `contract_requirement`: aturan dari kontrak (lampiran wajib, syarat serah terima,
  boleh parsial) beserta pasal & kutipan — separuh *checklist gabungan* (briefing hlm. 11 & 15).
- Tabel `evidence_photo` (pemilik: Network Engineer, **usulan untuk disepakati**): foto ODK
  per baris BoQ, SN, GPS, dan status review PM. Kunci anti-dobel `odk_instance_id`.
- `contract.contract_type`, `contract.mybhakti_project_ref`; `sph.mybhakti_project_ref`,
  `sph.mybhakti_vendor_ref`.
- `sph_item.contract_item_id` — kunci price matching / tabel banding (Bulan 5).
- `bast_item.contract_item_id` + kolom serah terima (`activation_date[_text]`,
  `service_order_ref`, `service_id`, `location`) dari pola BAST Telkom (Tanggal Aktif, AO, SID).
- `document.validation_notes` — peringatan tingkat dokumen (mis. salinan ganda) kini terlihat PM.
- Tipe kolom `coord` → `numeric(9,6)` untuk GPS (numeric(18,2) memotong koordinat).
- View PostgreSQL untuk BAST: `bast_rincian`, `evidence_siap_lampiran`, `checklist_gabungan`
  (diuji di PostgreSQL 16 dengan data contoh BAST Tasikmalaya).
- `generated/KAMUS_DATA.md` — kamus data berbahasa Indonesia, dibangkitkan dari model.
- `schema.json`: `owner`, `domain`, `display_column`, `upsert_key`, `parent_refs`,
  `human_columns` per tabel, dan blok `conventions` (aturan untuk setiap pengirim data).
- `nocodb_fields.json`: keterangan kolom (tooltip di NocoDB) dan judul baris (`pv`).
- Penanda kolom milik PM (`Column.written_by="human"`): `bast_draft.approved_by/approved_at`,
  `evidence_photo.review_*`. Validator **menolak** payload mesin yang menyertakannya.
- `tests/` — 10 tes invarian skema (FK, urutan insert, kolom PM, artefak tidak basi).

### Diubah — dampak: **perlu penyesuaian** (hanya tampilan NocoDB)
- Kolom `*_score` di NocoDB: `Percent` → `Decimal`. Skor disimpan 0–1; tipe Percent
  menampilkan 0,876 sebagai "0,876%". Base NocoDB lama perlu dibangun ulang.
- `model.py` disusun ulang mengikuti alur bisnis; tiap tabel punya `owner` dan `domain`.
  `natural_key()` & `parent_refs()` kini bagian dari paket (dulu disalin di dol-parser).

### Diperbaiki
- dol-parser mengirim `bast_draft.approved_by = None` — memproses ulang kontrak akan
  **menghapus persetujuan PM** saat PATCH. Ditemukan oleh aturan kolom-milik-PM yang baru.
  **Koreksi (2026.10.2):** perbaikan ini tidak lengkap. `bast_draft` tidak punya kunci
  anti-dobel, sehingga pengirim memakai strategi hapus-lalu-isi-ulang dan persetujuan PM
  tetap hilang. Tabelnya kini ditunda; kuncinya wajib diputuskan sebelum berlaku.

### Dokumentasi & diagram (29 Sep 2026)
- `generated/schema.dbml`: diagram skema untuk dbdiagram.io / ekstensi dbdiagram di VS Code
  dan Antigravity, dibangkitkan dari `model.py` lewat `to_dbml()`. `--check` ikut gagal bila
  diagram basi. Warna header menandai penulis tabel (mesin / manusia / hanya PostgreSQL).
- `docs/usulan-v2/`: usulan skema v2 (nama Indonesia, 9 tabel NocoDB). **Ditunda** —
  tim memilih tetap memakai skema sekarang; disimpan sebagai arsip ide.

- README: tabel artefak memuat `schema.dbml` dan cara membuka diagram.
- `docs/ERD.md`: diagram yang berlaku ditegaskan ada di `generated/schema.dbml`; Mermaid di
  dokumen itu hanya ringkasan konseptual.

### Diketahui, belum diperbaiki
- Kolom FK bertipe `integer` sementara PK `id` bertipe `bigint`. PostgreSQL menerimanya dan
  pada volume sekarang tidak bermasalah, tetapi tipe FK seharusnya sama dengan PK.
- `extracted_field` hanya menyimpan `evidence_score`; skor gabungan `confidence` yang
  dihitung dol-parser tidak tersimpan.

## [companion-2026.09.1] — 2026-09-28

Rilis pertama sebagai repo terpisah dari dol-parser. 14 tabel; 13 di antaranya dikirim ke
NocoDB.

### Ditambahkan (`933494f`)
- Definisi skema sebagai satu sumber kebenaran di `dol_schema/model.py`, dipindah dari
  `dol-parser/app/companion/model.py`. Tabel: `document`, `extraction_run`, `bast`,
  `bast_party`, `bast_item`, `bast_condition`, `extracted_field`, `field_review`,
  `contract`, `contract_party`, `contract_item`, `sph`, `bast_draft`.
- Artefak dibangkitkan: `generated/schema.sql` (PostgreSQL), `generated/schema.json`
  (n8n & compiler BAST), `generated/nocodb_fields.json` (pembuatan tabel NocoDB).
- `bast_draft.generated_bast_id` (FK → `bast.id`, RESTRICT): tanpa kolom ini, kontrak yang
  di-generate ulang membuat PM tidak tahu draf mana yang menghasilkan BAST yang mana.
  Dampak: **aman**.

### Ditambahkan (`d3a6403`)
- Tabel `sph_item`: baris penawaran SPH. Sebelumnya hanya grand total yang tersimpan,
  sehingga grid verifikasi SPH dan tabel banding antar-vendor tidak mungkin dibuat.
  Dampak: **aman**.
- `sph.vendor_name`, `sph.vendor_npwp`: SPH datang dari vendor, tetapi sebelumnya hanya
  klien yang tersimpan. Dampak: **aman**.
- Penanda `Table.nocodb`: `extraction_run` (engine OCR, model LLM, durasi) tetap dibuat di
  PostgreSQL tetapi tidak dikirim ke NocoDB, sesuai arahan Delivery Ops. Dampak: **aman**.

> **Catatan:** perubahan `d3a6403` mengubah bentuk data tetapi `SCHEMA_VERSION` tidak
> dinaikkan, sehingga dua bentuk skema berbeda sama-sama bernama `companion-2026.09.1`.
> Konsumen yang membaca versi ini sebaiknya memakai bentuk **setelah** `d3a6403`. Aturan
> versi di atas dibuat supaya ini tidak terulang.
