# Kamus Data — Delivery Ops Layer

Versi skema **companion-2026.10.3**. Dibangkitkan dari `dol_schema/model.py` — jangan diedit tangan; ubah model lalu jalankan `python -m dol_schema --emit`.

Setiap tabel punya dua nama: **judul** berbahasa Indonesia (yang tampil di NocoDB) dan
**nama teknis** (dipakai kode, SQL, dan n8n). Setiap tabel juga punya kolom `id`,
`created_at`, `updated_at` yang diisi otomatis.

Data master klien, vendor, proyek, dan PO **tidak** ada di sini — sumbernya MyBhakti
(briefing hlm. 7); yang disimpan hanya kolom rujukan `mybhakti_*_ref`.

## Daftar tabel

| Tabel | Nama teknis | Status | Pemilik | Diisi oleh | Di NocoDB |
|---|---|---|---|---|---|
| **Dokumen** | `document` | berlaku | AI Engineer | sistem | ya |
| **Kontrak** | `contract` | berlaku | AI Engineer | sistem | ya |
| **Pihak Kontrak** | `contract_party` | berlaku | AI Engineer | sistem | ya |
| **Rincian Kontrak** | `contract_item` | berlaku | AI Engineer | sistem | ya |
| **Syarat Kontrak** | `contract_requirement` | berlaku | AI Engineer | sistem | ya |
| **SPH Vendor** | `sph` | berlaku | AI Engineer | sistem | ya |
| **Rincian SPH** | `sph_item` | berlaku | AI Engineer | sistem | ya |
| **BAST** | `bast` | ditunda | AI Engineer | sistem | tidak |
| **Pihak BAST** | `bast_party` | ditunda | AI Engineer | sistem | tidak |
| **Rincian BAST** | `bast_item` | ditunda | AI Engineer | sistem | tidak |
| **Kondisi BAST** | `bast_condition` | ditunda | AI Engineer | sistem | tidak |
| **Draf BAST** | `bast_draft` | ditunda | RPA Engineer | sistem | tidak |
| **Foto Evidence** | `evidence_photo` | ditunda | Network Engineer | sistem | tidak |
| **Hasil Ekstraksi** | `extracted_field` | berlaku | AI Engineer | sistem | ya |
| **Keputusan PM** | `field_review` | berlaku | PM | PM | ya |
| **Riwayat Pemrosesan** | `extraction_run` | berlaku | AI Engineer | sistem | tidak |

Urutan pengisian tabel yang berlaku (induk dulu): Dokumen → Kontrak → Pihak Kontrak → Rincian Kontrak → Syarat Kontrak → SPH Vendor → Rincian SPH → Hasil Ekstraksi → Keputusan PM → Riwayat Pemrosesan

## Cara PM memakai tabel ini di NocoDB

1. Buka **Hasil Ekstraksi**, saring per dokumen. Urutkan **Status Bukti**: kerjakan
   `bertentangan`, `tidak_ada_di_dokumen`, dan `perlu_dicek` lebih dulu.
2. `bukti_kuat` artinya nilai itu **ditemukan** di dokumen — bukan berarti benar. Nomor
   kontrak yang salah bisa tetap `bukti_kuat` bila nomor lain di dokumen kebetulan sama.
   Harga dan klausul tetap wajib diperiksa (briefing hlm. 20).
3. Catat setiap keputusan di **Keputusan PM**: `benar`, `dikoreksi` (isi **Nilai Final**),
   atau `ditolak`. Isi **Nilai Sistem Saat Diperiksa** dengan nilai yang Anda lihat.
4. Begitu sebuah dokumen punya Keputusan PM, sistem tidak lagi menimpanya otomatis.

## Nilai yang boleh dipakai dokumen hilir

Penyusunan BAST (nanti) hanya membaca nilai yang sudah diputuskan PM `benar` atau
`dikoreksi` dan belum basi. Di PostgreSQL tersedia view `nilai_terverifikasi` untuk itu;
field yang belum diperiksa dianggap kosong, bukan diambil dari nilai sistem.

## Tabel yang berlaku

### Kelompok: dokumen

Setiap berkas PDF yang masuk.

### Dokumen (`document`)

Setiap berkas yang masuk, apa pun jenisnya.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Nama Berkas**
- **Kunci anti-dobel:** Sidik Berkas
- **Induk:** —

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **Sidik Berkas** | `content_hash` | teks | ya | sistem | unik. sha256 isi berkas -- kunci anti-dobel; berkas yang sama diproses ulang memperbarui baris yang sama |
| **Jenis Dokumen** | `doc_type` | teks | ya | sistem | Pilihan: `kontrak`, `sph`, `bast`. |
| **Nama Berkas** | `source_filename` | teks | ya | sistem |  |
| **Jumlah Halaman** | `page_count` | angka bulat |  | sistem |  |
| **Isi Dokumen** | `markdown` | teks |  | sistem | teks hasil pembacaan sistem, agar PM bisa membaca tanpa membuka PDF. Bagian yang rusak OCR bisa sudah dipoles mesin: PDF asli tetap acuan |
| **Catatan Validasi** | `validation_notes` | teks |  | sistem | peringatan tingkat dokumen, mis. salinan ganda atau jumlah item tidak sama dengan total |

### Kelompok: kontrak

Kontrak/SPK pelanggan — sumber semua BoQ dan aturan serah terima (briefing hlm. 3 & 11).

### Kontrak (`contract`)

Kontrak/SPK pelanggan dalam bentuk apa pun -- dibaca sekali, dipakai sepanjang proyek (hlm. 11). Sumber kebenaran BAST pelanggan.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Nomor Kontrak**
- **Kunci anti-dobel:** ID Dokumen
- **Induk:** Dokumen

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Dokumen** | `document_id` | angka bulat | ya | sistem | unik. → Dokumen. satu kontrak = satu dokumen |
| **Rujukan Proyek MyBhakti** | `mybhakti_project_ref` | teks |  | sistem | proyek/deal di MyBhakti, diisi n8n -- pengikat semua dokumen satu proyek; sengaja bukan relasi (hlm. 7) |
| **Jenis Kontrak** | `contract_type` | teks |  | sistem | bentuk dokumen dasar Pilihan: `nota_pesanan`, `surat_pesanan`, `spk`, `kontrak_kerja_sama`, `pks`, `lainnya`. |
| **Nomor Kontrak** | `contract_number` | teks |  | sistem | nomor resmi kontrak / SPK / PKS |
| **Nomor Registrasi Internal** | `contract_number_internal` | teks |  | sistem | nomor registrasi internal BUT |
| **Nama Pekerjaan** | `work_title` | teks |  | sistem | judul pengadaan / lingkup pekerjaan |
| **Lokasi** | `location_text` | teks |  | sistem | kota/lokasi seperti tertulis di kontrak (tempat dibuat atau pelaksanaan) |
| **Tanggal Kontrak Tertulis** | `contract_date_text` | teks |  | sistem | apa adanya di dokumen |
| **Tanggal Kontrak** | `contract_date` | tanggal |  | sistem | hasil baca; kosong bila ragu |
| **Tanggal Mulai Tertulis** | `start_date_text` | teks |  | sistem |  |
| **Tanggal Mulai** | `start_date` | tanggal |  | sistem |  |
| **Tanggal Selesai Tertulis** | `end_date_text` | teks |  | sistem |  |
| **Tanggal Selesai** | `end_date` | tanggal |  | sistem |  |
| **Jangka Waktu** | `duration_text` | teks |  | sistem | mis. '30 hari kalender' |
| **Nilai Kontrak** | `contract_value` | angka |  | sistem | total termasuk PPN bila dokumen menyebutnya begitu |
| **Subtotal** | `subtotal_value` | angka |  | sistem |  |
| **Nilai PPN** | `vat_value` | angka |  | sistem |  |
| **Persentase PPN** | `vat_percentage` | teks |  | sistem | apa adanya di dokumen |
| **Mata Uang** | `currency` | kode 3 huruf | ya | sistem |  |
| **Cara Pembayaran** | `payment_mechanism` | teks |  | sistem |  |
| **Ketentuan Denda** | `penalty_terms` | teks |  | sistem |  |
| **Syarat Lampiran BAST** | `bast_terms` | teks |  | sistem | ringkasan; rincian per syarat ada di tabel Syarat Kontrak |
| **Nama Bank** | `bank_name` | teks |  | sistem |  |
| **Nomor Rekening** | `bank_account_number` | teks |  | sistem |  |
| **Nama Pemilik Rekening** | `bank_account_name` | teks |  | sistem |  |

### Pihak Kontrak (`contract_party`)

Pihak penandatangan kontrak seperti tertulis saat diteken -- bukan data master. Satu orang bisa muncul di banyak baris karena menandatangani banyak dokumen.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Nama Instansi**
- **Kunci anti-dobel:** ID Kontrak + Peran
- **Induk:** Kontrak

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Kontrak** | `contract_id` | angka bulat | ya | sistem | → Kontrak. |
| **Peran** | `role` | teks | ya | sistem | pemberi_kerja = pelanggan; pelaksana = BUT. Ditentukan dari nama instansi, bukan dari sebutan 'Pihak Pertama/Kedua' Pilihan: `pemberi_kerja`, `pelaksana`. |
| **Sebutan di Dokumen** | `party_label_text` | teks |  | sistem | mis. 'PIHAK PERTAMA' -- sebutan ini bisa terbalik antar-format kontrak, karena itu disimpan terpisah dari peran |
| **Nama Instansi** | `org_name_text` | teks | ya | sistem |  |
| **Nama Penandatangan** | `signer_name` | teks |  | sistem | kosong bila tidak terbaca |
| **Jabatan Penandatangan** | `signer_title` | teks |  | sistem |  |
| **Alamat** | `org_address_text` | teks |  | sistem |  |
| **Rujukan Pihak MyBhakti** | `mybhakti_party_ref` | teks |  | sistem | diisi n8n |

### Rincian Kontrak (`contract_item`)

BoQ kontrak = kewajiban ke pelanggan (hlm. 7). Sumber tunggal rincian pekerjaan untuk BAST pelanggan.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Uraian**
- **Kunci anti-dobel:** ID Kontrak + No Urut
- **Induk:** Kontrak

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Kontrak** | `contract_id` | angka bulat | ya | sistem | → Kontrak. |
| **No Urut** | `line_no` | angka bulat | ya | sistem | urutan baca di dokumen |
| **Kelompok** | `category` | teks |  | sistem |  |
| **Uraian** | `description` | teks | ya | sistem |  |
| **Spesifikasi** | `specification` | teks |  | sistem |  |
| **Volume** | `quantity` | angka |  | sistem |  |
| **Satuan** | `unit` | teks |  | sistem |  |
| **Periode** | `period` | teks |  | sistem |  |
| **Harga Satuan** | `unit_price` | angka |  | sistem | selalu dikonfirmasi PM (hlm. 20) |
| **Jumlah Harga** | `line_total` | angka |  | sistem |  |
| **Keterangan** | `remarks` | teks |  | sistem |  |

### Syarat Kontrak (`contract_requirement`)

Aturan dari kontrak, bukan angka: lampiran wajib, syarat serah terima, boleh parsial (hlm. 11). Baris lampiran wajib adalah separuh checklist gabungan BAST.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Isi Syarat**
- **Kunci anti-dobel:** ID Kontrak + No Urut
- **Induk:** Kontrak

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Kontrak** | `contract_id` | angka bulat | ya | sistem | → Kontrak. |
| **No Urut** | `line_no` | angka bulat | ya | sistem |  |
| **Jenis Syarat** | `requirement_type` | teks | ya | sistem | lampiran wajib / syarat serah terima / boleh parsial Pilihan: `lampiran_wajib`, `syarat_serah_terima`, `boleh_parsial`. |
| **Isi Syarat** | `requirement_text` | teks | ya | sistem | mis. 'Berita Acara Uji Terima' |
| **Pasal Rujukan** | `clause_ref` | teks |  | sistem | mis. 'Pasal 9 ayat 2' |
| **Halaman** | `evidence_page` | angka bulat |  | sistem | halaman tempat syarat ini ditemukan |
| **Kutipan Dokumen** | `evidence_quote` | teks |  | sistem | kutipan pendek agar PM tidak perlu membaca ulang kontrak (hlm. 11) |

### Kelompok: sph

Penawaran vendor yang lahir dari kebutuhan kontrak (rantai hulu).

### SPH Vendor (`sph`)

Surat penawaran harga dari vendor (rantai hulu) -- lahir dari kebutuhan kontrak.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Nomor SPH**
- **Kunci anti-dobel:** ID Dokumen
- **Induk:** Dokumen

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Dokumen** | `document_id` | angka bulat | ya | sistem | unik. → Dokumen. |
| **Rujukan Proyek MyBhakti** | `mybhakti_project_ref` | teks |  | sistem | diisi n8n |
| **Rujukan Vendor MyBhakti** | `mybhakti_vendor_ref` | teks |  | sistem | diisi n8n |
| **Nomor SPH** | `sph_number` | teks |  | sistem |  |
| **Tanggal SPH Tertulis** | `sph_date_text` | teks |  | sistem |  |
| **Tanggal SPH** | `sph_date` | tanggal |  | sistem |  |
| **Perihal** | `project_name` | teks |  | sistem | perihal / nama pekerjaan yang ditawarkan |
| **Ditujukan Kepada** | `client_name` | teks |  | sistem | instansi yang dituju surat |
| **Nama Vendor** | `vendor_name` | teks |  | sistem | penerbit SPH seperti tertulis |
| **Subtotal** | `subtotal_value` | angka |  | sistem |  |
| **Persentase PPN** | `vat_percentage` | teks |  | sistem | apa adanya di dokumen |
| **Nilai PPN** | `vat_value` | angka |  | sistem |  |
| **Total Penawaran** | `total_price` | angka |  | sistem | grand total |
| **Masa Berlaku** | `validity_text` | teks |  | sistem | masa berlaku penawaran |
| **Cara Pembayaran** | `payment_mechanism` | teks |  | sistem |  |
| **Mata Uang** | `currency` | kode 3 huruf | ya | sistem |  |

### Rincian SPH (`sph_item`)

Baris penawaran vendor. Relasi ke barang yang dibeli (procurement item) untuk tabel banding harga dirancang di Bulan 5 -- belum ada di sini.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Uraian**
- **Kunci anti-dobel:** ID SPH + No Urut
- **Induk:** SPH Vendor

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID SPH** | `sph_id` | angka bulat | ya | sistem | → SPH Vendor. |
| **No Urut** | `line_no` | angka bulat | ya | sistem | urutan baca, bukan kolom 'No' di dokumen |
| **Kelompok** | `category` | teks |  | sistem |  |
| **Uraian** | `description` | teks | ya | sistem |  |
| **Spesifikasi** | `specification` | teks |  | sistem |  |
| **Merek** | `brand` | teks |  | sistem |  |
| **Nomor Part** | `part_number` | teks |  | sistem |  |
| **Volume** | `quantity` | angka |  | sistem |  |
| **Satuan** | `unit` | teks |  | sistem |  |
| **Periode** | `period` | teks |  | sistem |  |
| **Harga Satuan** | `unit_price` | angka |  | sistem | selalu dikonfirmasi PM (hlm. 20) |
| **Jumlah Harga** | `line_total` | angka |  | sistem |  |
| **Keterangan** | `remarks` | teks |  | sistem |  |

### Kelompok: verifikasi

Nilai yang dibaca sistem beserta buktinya, dan keputusan PM per field.

### Hasil Ekstraksi (`extracted_field`)

Satu baris per field: nilai terbaca + bukti. Antrean kerja PM. Ditulis mesin saja; dokumen yang sudah mulai diperiksa PM tidak ditimpa otomatis.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = **Nama Field**
- **Kunci anti-dobel:** ID Dokumen + Nama Field
- **Induk:** Dokumen

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Dokumen** | `document_id` | angka bulat | ya | sistem | → Dokumen. |
| **Nama Field** | `field_path` | teks | ya | sistem | mis. 'Nomor Kontrak Kerja' atau 'List Item/Barang[0].Harga Satuan' |
| **Nilai Terbaca Sistem** | `ai_value_text` | teks |  | sistem |  |
| **Halaman Bukti** | `evidence_page` | angka bulat |  | sistem | dihitung sistem, bukan ditulis LLM |
| **Kutipan Bukti** | `evidence_quote` | teks |  | sistem | potongan teks dokumen tempat nilai ditemukan |
| **Skor Bukti** | `evidence_score` | angka |  | sistem | 0-1: seberapa persis nilai ditemukan di teks dokumen |
| **Status Bukti** | `system_status` | teks | ya | sistem | saran sistem, BUKAN persetujuan. Yang diperiksa sistem hanya apakah nilai ada di dokumen, bukan apakah perannya benar Pilihan: `bukti_kuat`, `bukti_cukup`, `perlu_dicek`, `tidak_ada_di_dokumen`, `bertentangan`, `kosong`. |

### Keputusan PM (`field_review`)

Keputusan PM per field (hlm. 11 & 20). Pipeline tidak pernah menulis ke sini. Nilai yang boleh dipakai dokumen hilir hanya yang ada keputusannya di sini.

- **Status:** berlaku
- **Pemilik:** PM
- **Diisi oleh:** PM (manusia)
- **Tampil di NocoDB:** ya, judul baris = **Nama Field**
- **Kunci anti-dobel:** ID Dokumen + Nama Field
- **Induk:** Dokumen

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Dokumen** | `document_id` | angka bulat | ya | PM | → Dokumen. dokumen dengan keputusan PM tidak boleh terhapus diam-diam |
| **Nama Field** | `field_path` | teks | ya | PM |  |
| **Nilai Sistem Saat Diperiksa** | `reviewed_ai_value_text` | teks |  | PM | nilai yang DILIHAT PM saat memutuskan; bila nilai sistem berubah, keputusan lama tidak berlaku untuk nilai baru |
| **Keputusan** | `decision` | teks | ya | PM | Pilihan: `benar`, `dikoreksi`, `ditolak`. |
| **Nilai Final** | `final_value_text` | teks |  | PM | wajib diisi bila dikoreksi |
| **Diperiksa Oleh** | `reviewed_by` | teks | ya | PM |  |
| **Waktu Diperiksa** | `reviewed_at` | tanggal & jam | ya | PM |  |
| **Catatan PM** | `reviewer_note` | teks |  | PM |  |

### Kelompok: audit

Jejak teknis pemrosesan — hanya di PostgreSQL, tidak tampil di NocoDB.

### Riwayat Pemrosesan (`extraction_run`)

Jejak tiap pemrosesan -- dasar bukti 'Terukur' (hlm. 21). Hanya di PostgreSQL.

- **Status:** berlaku
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** tidak (hanya PostgreSQL)
- **Kunci anti-dobel:** — (belum ada)
- **Induk:** Dokumen

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Dokumen** | `document_id` | angka bulat | ya | sistem | → Dokumen. |
| **Mesin OCR** | `ocr_engine` | teks |  | sistem |  |
| **Model LLM** | `llm_model` | teks |  | sistem |  |
| **Versi Prompt** | `prompt_version` | teks |  | sistem |  |
| **Versi Skema** | `schema_version` | teks |  | sistem |  |
| **Jumlah Panggilan LLM** | `llm_call_count` | angka bulat |  | sistem |  |
| **Detik Pembacaan** | `parse_seconds` | angka |  | sistem |  |
| **Detik Ekstraksi** | `extract_seconds` | angka |  | sistem |  |
| **Status Validasi** | `validation_status` | teks |  | sistem |  |
| **Mulai** | `started_at` | tanggal & jam |  | sistem |  |

## Tabel usulan (ditunda)

Belum dibuat di NocoDB. Menunggu kesepakatan bersama RPA Engineer (nomor & render
BAST) dan Network Engineer (evidence & lampiran). DDL-nya ada di
`generated/schema_usulan.sql` untuk dibahas di workshop skema.
Pilihan nilainya sengaja belum diterjemahkan: diputuskan saat disepakati.

### Kelompok: bast

Serah terima. BAST pelanggan dibaca dari kontrak; nomor & render oleh RPA.

### BAST (`bast`)

DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. BAST hasil ekstraksi dokumen lama atau hasil susunan sistem.

- **Status:** ditunda
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** belum — tabel usulan
- **Kunci anti-dobel:** ID Dokumen
- **Induk:** Kontrak, Dokumen

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Dokumen** | `document_id` | angka bulat | ya | sistem | unik. → Dokumen. |
| **Arah** | `direction` | teks | ya | sistem | customer = kita->pelanggan (acuan: kontrak); vendor = vendor->kita (acuan: PO) -- hlm. 10 Pilihan: `customer`, `vendor`, `unknown`. |
| **ID Kontrak** | `contract_id` | angka bulat |  | sistem | → Kontrak. hanya untuk BAST pelanggan |
| **Rujukan PO MyBhakti** | `mybhakti_po_ref` | teks |  | sistem | diisi n8n; bukan relasi |
| **Nomor BAST Pelanggan** | `bast_number_customer` | teks |  | sistem |  |
| **Nomor BAST Internal** | `bast_number_internal` | teks |  | sistem | dari numbering service milik RPA (hlm. 20) |
| **Tanggal Serah Terima Tertulis** | `handover_date_text` | teks |  | sistem |  |
| **Tanggal Serah Terima** | `handover_date` | tanggal |  | sistem |  |
| **Kota Serah Terima** | `handover_city` | teks |  | sistem |  |
| **Nama Pekerjaan** | `work_title` | teks |  | sistem |  |
| **Jenis Dokumen Dasar** | `basis_doc_type` | teks |  | sistem | Pilihan: `contract`, `pks`, `spk`, `order_note`, `purchase_order`, `other`. |
| **Nomor Dokumen Dasar** | `basis_doc_number` | teks |  | sistem |  |
| **Tanggal Dokumen Dasar Tertulis** | `basis_doc_date_text` | teks |  | sistem |  |
| **Tanggal Dokumen Dasar** | `basis_doc_date` | tanggal |  | sistem |  |
| **Nilai Dokumen Dasar** | `basis_doc_value` | angka |  | sistem |  |
| **PPN Nilai Dasar** | `basis_doc_value_vat` | teks |  | sistem | Pilihan: `included`, `excluded`, `unstated`. |
| **Mata Uang** | `currency` | kode 3 huruf | ya | sistem |  |
| **Pernyataan Penerimaan** | `acceptance_statement` | teks |  | sistem |  |

### Pihak BAST (`bast_party`)

DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Tepat 2 baris per BAST: penyerah dan penerima.

- **Status:** ditunda
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** belum — tabel usulan
- **Kunci anti-dobel:** ID BAST + Peran
- **Induk:** BAST

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID BAST** | `bast_id` | angka bulat | ya | sistem | → BAST. |
| **Peran** | `role` | teks | ya | sistem | peran, BUKAN 'Pihak Pertama/Kedua' -- label itu terbalik antar-format Pilihan: `handover`, `receiver`. |
| **Nama Instansi** | `org_name_text` | teks | ya | sistem |  |
| **Nama Penandatangan** | `signer_name` | teks |  | sistem | kosong bila tidak terbaca |
| **Jabatan Penandatangan** | `signer_title` | teks |  | sistem |  |
| **Alamat** | `org_address_text` | teks |  | sistem |  |
| **Rujukan Pihak MyBhakti** | `mybhakti_party_ref` | teks |  | sistem |  |

### Rincian BAST (`bast_item`)

DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Baris serah terima.

- **Status:** ditunda
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** belum — tabel usulan
- **Kunci anti-dobel:** ID BAST + No Urut
- **Induk:** BAST, Rincian Kontrak

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID BAST** | `bast_id` | angka bulat | ya | sistem | → BAST. |
| **No Urut** | `line_no` | angka bulat | ya | sistem |  |
| **ID Rincian Kontrak** | `contract_item_id` | angka bulat |  | sistem | → Rincian Kontrak. baris BoQ kontrak yang diserahkan; uraian & harga dibaca dari kontrak |
| **Uraian** | `description` | teks | ya | sistem |  |
| **Volume** | `quantity` | angka |  | sistem | volume yang DISERAHKAN -- bisa lebih kecil dari kontrak bila parsial |
| **Satuan** | `unit` | teks |  | sistem |  |
| **Harga Satuan** | `unit_price` | angka |  | sistem |  |
| **Jumlah Harga** | `line_total` | angka |  | sistem |  |
| **Hasil Uji** | `test_result` | teks |  | sistem | diisi setelah uji, bukan sebelumnya |
| **Tanggal Aktif Tertulis** | `activation_date_text` | teks |  | sistem |  |
| **Tanggal Aktif** | `activation_date` | tanggal |  | sistem |  |
| **Nomor AO** | `service_order_ref` | teks |  | sistem |  |
| **SID** | `service_id` | teks |  | sistem |  |
| **Lokasi** | `location` | teks |  | sistem |  |
| **Keterangan** | `remarks` | teks |  | sistem |  |

### Kondisi BAST (`bast_condition`)

DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Fakta tambahan BAST sebagai baris, bukan kolom baru.

- **Status:** ditunda
- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** belum — tabel usulan
- **Kunci anti-dobel:** — (belum ada)
- **Induk:** BAST

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID BAST** | `bast_id` | angka bulat | ya | sistem | → BAST. |
| **Jenis Kondisi** | `condition_type` | teks | ya | sistem | Pilihan: `progress_percent`, `service_active_since`, `acceptance_test_ref`, `delivery_reconciliation_ref`, `supporting_document`, `amount_in_words`. |
| **Nilai Teks** | `value_text` | teks |  | sistem |  |
| **Nilai Angka** | `value_number` | angka |  | sistem |  |
| **Nilai Tanggal** | `value_date` | tanggal |  | sistem |  |

### Draf BAST (`bast_draft`)

DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Belum punya kunci anti-dobel: wajib diputuskan sebelum berlaku, karena tanpa kunci, pengiriman ulang menghapus persetujuan PM.

- **Status:** ditunda
- **Pemilik:** RPA Engineer
- **Diisi oleh:** sistem; kolom milik PM: Disetujui Oleh, Waktu Disetujui
- **Tampil di NocoDB:** belum — tabel usulan
- **Kunci anti-dobel:** — (belum ada)
- **Induk:** BAST, Kontrak

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Kontrak** | `contract_id` | angka bulat | ya | sistem | → Kontrak. |
| **Nomor Draf** | `draft_bast_number` | teks |  | sistem |  |
| **Nama Pekerjaan** | `work_title` | teks | ya | sistem |  |
| **Tanggal Serah Terima Tertulis** | `handover_date_text` | teks |  | sistem |  |
| **Tanggal Serah Terima** | `handover_date` | tanggal |  | sistem |  |
| **Kota Serah Terima** | `handover_city` | teks |  | sistem |  |
| **Status** | `status` | teks | ya | sistem | Pilihan: `draft`, `pending_review`, `approved`, `generated`, `rejected`. |
| **Template** | `template_name` | teks |  | sistem |  |
| **Pernyataan Penerimaan** | `acceptance_statement` | teks |  | sistem |  |
| **Tautan Dokumen** | `generated_doc_url` | teks |  | sistem |  |
| **ID BAST Tercetak** | `generated_bast_id` | angka bulat |  | sistem | → BAST. |
| **Disetujui Oleh** | `approved_by` | teks |  | PM |  |
| **Waktu Disetujui** | `approved_at` | tanggal & jam |  | PM |  |

### Kelompok: evidence

Foto bukti lapangan dari ODK Central (wilayah Network Engineer).

### Foto Evidence (`evidence_photo`)

DITUNDA: usulan untuk disepakati dengan Network Engineer (dol-odk & dol-bast-compiler, hlm. 15). Lampiran wajib kontrak sering berupa DOKUMEN (BA uji terima, surat jalan), bukan foto -- bentuk tabel bukti perlu dibahas bersama.

- **Status:** ditunda
- **Pemilik:** Network Engineer
- **Diisi oleh:** sistem; kolom milik PM: Status Review, Diperiksa Oleh, Waktu Diperiksa, Catatan Review
- **Tampil di NocoDB:** belum — tabel usulan
- **Kunci anti-dobel:** ID Kiriman ODK
- **Induk:** Rincian Kontrak, Syarat Kontrak

| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|---|
| **ID Kiriman ODK** | `odk_instance_id` | teks | ya | sistem | unik. sinkron ulang = pembaruan, bukan baris kembar |
| **ID Rincian Kontrak** | `contract_item_id` | angka bulat | ya | sistem | → Rincian Kontrak. |
| **ID Syarat Kontrak** | `requirement_id` | angka bulat |  | sistem | → Syarat Kontrak. |
| **Komponen** | `component_label` | teks |  | sistem | mis. '4 Unit Switch' |
| **Jenis Foto** | `photo_type` | teks | ya | sistem | Pilihan: `item`, `serial_label`, `installation`, `screenshot`. |
| **Nomor Seri** | `serial_number` | teks |  | sistem |  |
| **Tautan Foto** | `photo_url` | teks | ya | sistem |  |
| **Waktu Foto** | `taken_at` | tanggal & jam | ya | sistem |  |
| **Lintang** | `gps_lat` | koordinat GPS |  | sistem |  |
| **Bujur** | `gps_lon` | koordinat GPS |  | sistem |  |
| **Catatan Cek Otomatis** | `auto_check_notes` | teks |  | sistem |  |
| **Status Review** | `review_status` | teks | ya | PM | Pilihan: `pending`, `approved`, `rejected`. |
| **Diperiksa Oleh** | `reviewed_by` | teks |  | PM |  |
| **Waktu Diperiksa** | `reviewed_at` | tanggal & jam |  | PM |  |
| **Catatan Review** | `review_note` | teks |  | PM |  |
