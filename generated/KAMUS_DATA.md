# Kamus Data — Delivery Ops Layer

Versi skema **companion-2026.10.1**. Dibangkitkan dari `dol_schema/model.py` — jangan diedit tangan; ubah model lalu jalankan `python -m dol_schema --emit`.

Setiap tabel juga punya kolom `id`, `created_at`, `updated_at` yang diisi otomatis.
Data master klien, vendor, proyek, dan PO **tidak** ada di sini — sumbernya MyBhakti
(briefing hlm. 7); yang disimpan hanya kolom rujukan `mybhakti_*_ref`.

## Daftar tabel

| Kelompok | Tabel | Pemilik | Diisi oleh | Di NocoDB |
|---|---|---|---|---|
| dokumen | `document` | AI Engineer | sistem | ya |
| kontrak | `contract` | AI Engineer | sistem | ya |
| kontrak | `contract_party` | AI Engineer | sistem | ya |
| kontrak | `contract_item` | AI Engineer | sistem | ya |
| kontrak | `contract_requirement` | AI Engineer | sistem | ya |
| sph | `sph` | AI Engineer | sistem | ya |
| sph | `sph_item` | AI Engineer | sistem | ya |
| bast | `bast` | AI Engineer | sistem | ya |
| bast | `bast_party` | AI Engineer | sistem | ya |
| bast | `bast_item` | AI Engineer | sistem | ya |
| bast | `bast_condition` | AI Engineer | sistem | ya |
| bast | `bast_draft` | RPA Engineer | sistem | ya |
| evidence | `evidence_photo` | Network Engineer | sistem | ya |
| verifikasi | `extracted_field` | AI Engineer | sistem | ya |
| verifikasi | `field_review` | PM | PM | ya |
| audit | `extraction_run` | AI Engineer | sistem | tidak |

Urutan pengisian (induk dulu): `document` → `contract` → `contract_party` → `contract_item` → `contract_requirement` → `sph` → `sph_item` → `bast` → `bast_party` → `bast_item` → `bast_condition` → `bast_draft` → `evidence_photo` → `extracted_field` → `field_review` → `extraction_run`

## Cara menyusun BAST pelanggan dari nomor kontrak

Sistem tidak menyalin data ke BAST. Ia mengikuti relasi dari satu nomor kontrak:

| Bagian BAST | Diambil dari | Syarat |
|---|---|---|
| Nomor kontrak, nama pekerjaan, nilai | `contract` | field sudah dikonfirmasi PM di `field_review` |
| Pihak & penandatangan | `contract_party` (lewat `contract_id`) | |
| Rincian pekerjaan | `contract_item` + info serah terima di `bast_item` | uraian & harga dari kontrak, tidak disalin |
| Lampiran evidence | `evidence_photo` (lewat `contract_item_id`) | hanya `review_status = approved` |
| Checklist kelengkapan | `contract_requirement` + `evidence_photo` | semua lampiran wajib terpenuhi |
| Nomor BAST internal | numbering service (RPA) | sequence database, bukan NocoDB |

Bila memakai PostgreSQL, tiga view siap pakai sudah ada di `schema.sql`:
`bast_rincian`, `evidence_siap_lampiran`, dan `checklist_gabungan`.

## Dokumen

Setiap berkas PDF yang masuk.

### `document`

Supertipe: setiap berkas yang masuk, apa pun jenisnya.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `source_filename`
- **Kunci anti-dobel:** `content_hash`
- **Induk:** —

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `content_hash` | teks | ya | sistem | unik. sha1 isi berkas -- kunci idempotensi; proses ulang = UPDATE |
| `doc_type` | teks | ya | sistem | Pilihan: `contract`, `sph`, `bast`. |
| `source_filename` | teks | ya | sistem |  |
| `page_count` | angka bulat |  | sistem |  |
| `markdown` | teks |  | sistem | markdown utuh; PM membaca tanpa membuka PDF |
| `validation_notes` | teks |  | sistem | [2026.10.1] peringatan tingkat dokumen untuk PM, mis. salinan ganda atau jumlah item tidak sama dengan total |

## Kontrak

Kontrak/SPK pelanggan — sumber semua BoQ dan aturan serah terima (briefing hlm. 3 & 11).

### `contract`

Kontrak/SPK pelanggan dalam bentuk apa pun -- dibaca sekali, dipakai sepanjang proyek (hlm. 11). Sumber utama penyusunan draf BAST.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `contract_number`
- **Kunci anti-dobel:** `document_id`
- **Induk:** `document`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `document_id` | angka bulat | ya | sistem | unik. → `document.id`. UNIQUE -> 1:1 dengan document |
| `mybhakti_project_ref` | teks |  | sistem | [2026.10.1] proyek/deal di MyBhakti, diisi n8n -- kunci pengikat semua dokumen satu proyek; SENGAJA bukan FK (hlm. 7) |
| `contract_type` | teks |  | sistem | [2026.10.1] bentuk dokumen dasar: nota pesanan, surat pesanan, SPK, kontrak kerja sama, PKS Pilihan: `nota_pesanan`, `surat_pesanan`, `spk`, `kontrak_kerja_sama`, `pks`, `other`. |
| `contract_number` | teks |  | sistem | nomor kontrak resmi / SPK / PKS |
| `contract_number_internal` | teks |  | sistem | nomor registrasi internal BUT |
| `work_title` | teks | ya | sistem | judul pengadaan / lingkup pekerjaan |
| `contract_date_text` | teks |  | sistem |  |
| `contract_date` | tanggal |  | sistem |  |
| `start_date_text` | teks |  | sistem |  |
| `start_date` | tanggal |  | sistem |  |
| `end_date_text` | teks |  | sistem |  |
| `end_date` | tanggal |  | sistem |  |
| `duration_text` | teks |  | sistem |  |
| `contract_value` | angka |  | sistem |  |
| `subtotal_value` | angka |  | sistem |  |
| `vat_value` | angka |  | sistem |  |
| `vat_percentage` | teks |  | sistem |  |
| `currency` | kode 3 huruf | ya | sistem | default IDR |
| `payment_mechanism` | teks |  | sistem |  |
| `penalty_terms` | teks |  | sistem |  |
| `bast_terms` | teks |  | sistem |  |
| `bank_name` | teks |  | sistem |  |
| `bank_account_number` | teks |  | sistem |  |
| `bank_account_name` | teks |  | sistem |  |

### `contract_party`

Pihak penandatangan kontrak -- CUPLIKAN seperti tertulis, bukan data master. Satu orang muncul di banyak baris karena menandatangani banyak dokumen.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `org_name_text`
- **Kunci anti-dobel:** `contract_id` + `role`
- **Induk:** `contract`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `contract_id` | angka bulat | ya | sistem | → `contract.id`. |
| `role` | teks | ya | sistem | first_party/client (pemberi kerja) vs second_party/contractor (pelaksana) Pilihan: `first_party`, `second_party`, `client`, `contractor`. |
| `org_name_text` | teks | ya | sistem |  |
| `signer_name` | teks | ya | sistem |  |
| `signer_title` | teks |  | sistem |  |
| `org_address_text` | teks |  | sistem |  |
| `npwp` | teks |  | sistem |  |
| `mybhakti_party_ref` | teks |  | sistem |  |

### `contract_item`

BoQ kontrak = kewajiban ke pelanggan (hlm. 7). SUMBER TUNGGAL rincian pekerjaan: SPH vendor, BAST, dan evidence menunjuk ke sini, tidak menyalin.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `description`
- **Kunci anti-dobel:** `contract_id` + `line_no`
- **Induk:** `contract`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `contract_id` | angka bulat | ya | sistem | → `contract.id`. |
| `line_no` | angka bulat | ya | sistem |  |
| `category` | teks |  | sistem |  |
| `description` | teks | ya | sistem |  |
| `specification` | teks |  | sistem |  |
| `quantity` | angka |  | sistem |  |
| `unit` | teks |  | sistem |  |
| `period` | teks |  | sistem |  |
| `unit_price` | angka |  | sistem | selalu diverifikasi PM (hlm. 20) |
| `line_total` | angka |  | sistem |  |
| `remarks` | teks |  | sistem |  |

### `contract_requirement`

[2026.10.1] Aturan dari kontrak, bukan angka: lampiran wajib, syarat serah terima, boleh parsial (hlm. 11). Baris lampiran wajib adalah separuh CHECKLIST GABUNGAN; separuh lainnya evidence teknis milik Network Engineer (hlm. 15).

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `requirement_text`
- **Kunci anti-dobel:** `contract_id` + `line_no`
- **Induk:** `contract`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `contract_id` | angka bulat | ya | sistem | → `contract.id`. |
| `line_no` | angka bulat | ya | sistem |  |
| `requirement_type` | teks | ya | sistem | lampiran wajib / syarat serah terima / boleh parsial Pilihan: `mandatory_attachment`, `handover_condition`, `partial_delivery`. |
| `requirement_text` | teks | ya | sistem | mis. 'Berita Acara Uji Terima' |
| `clause_ref` | teks |  | sistem | pasal rujukan, mis. 'Pasal 9 ayat 2' |
| `evidence_quote` | teks |  | sistem | kutipan pendek agar PM tidak perlu membaca ulang kontrak (hlm. 11) |

## Sph

Penawaran vendor yang lahir dari kebutuhan kontrak (rantai hulu).

### `sph`

SPH vendor (rantai hulu) -- lahir DARI kebutuhan kontrak, bukan dasar kontrak.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `sph_number`
- **Kunci anti-dobel:** `document_id`
- **Induk:** `document`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `document_id` | angka bulat | ya | sistem | unik. → `document.id`. |
| `mybhakti_project_ref` | teks |  | sistem | [2026.10.1] proyek yang pengadaannya ditawar; diisi n8n |
| `mybhakti_vendor_ref` | teks |  | sistem | [2026.10.1] vendor penerbit di MyBhakti; diisi n8n |
| `sph_number` | teks |  | sistem |  |
| `sph_date_text` | teks |  | sistem |  |
| `sph_date` | tanggal |  | sistem |  |
| `project_name` | teks |  | sistem | perihal / nama pekerjaan yang ditawarkan |
| `client_name` | teks |  | sistem | instansi yang dituju surat |
| `vendor_name` | teks |  | sistem | penerbit SPH seperti tertulis |
| `vendor_npwp` | teks |  | sistem |  |
| `subtotal_value` | angka |  | sistem |  |
| `vat_percentage` | teks |  | sistem | apa adanya di dokumen; sering berupa frasa |
| `vat_value` | angka |  | sistem |  |
| `total_price` | angka |  | sistem | grand total |
| `validity_text` | teks |  | sistem | masa berlaku penawaran, mis. '30 hari' |
| `payment_mechanism` | teks |  | sistem |  |
| `currency` | kode 3 huruf | ya | sistem | default IDR |

### `sph_item`

Baris penawaran vendor. Beberapa vendor menawar item kontrak yang sama -> dibandingkan lewat contract_item_id.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `description`
- **Kunci anti-dobel:** `sph_id` + `line_no`
- **Induk:** `contract_item`, `sph`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `sph_id` | angka bulat | ya | sistem | → `sph.id`. |
| `line_no` | angka bulat | ya | sistem |  |
| `contract_item_id` | angka bulat |  | sistem | → `contract_item.id`. [2026.10.1] item kontrak yang dipenuhi baris ini -- kunci price matching & tabel banding antar-vendor (Bulan 5) |
| `category` | teks |  | sistem |  |
| `description` | teks | ya | sistem |  |
| `specification` | teks |  | sistem |  |
| `brand` | teks |  | sistem |  |
| `part_number` | teks |  | sistem |  |
| `quantity` | angka |  | sistem |  |
| `unit` | teks |  | sistem |  |
| `period` | teks |  | sistem |  |
| `unit_price` | angka |  | sistem |  |
| `line_total` | angka |  | sistem |  |
| `remarks` | teks |  | sistem |  |

## Bast

Serah terima. BAST pelanggan dibaca dari kontrak; nomor & render oleh RPA.

### `bast`

BAST (hasil ekstraksi atau hasil generate). Pihak & nilai BAST pelanggan dibaca dari kontrak lewat contract_id. Kolom di sini hanya butir yang selalu/hampir selalu ada.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `bast_number_customer`
- **Kunci anti-dobel:** `document_id`
- **Induk:** `contract`, `document`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `document_id` | angka bulat | ya | sistem | unik. → `document.id`. UNIQUE -> 1:1 dengan document |
| `direction` | teks | ya | sistem | customer = kita->pelanggan (acuan: kontrak); vendor = vendor->kita (acuan: PO) -- hlm. 10 Pilihan: `customer`, `vendor`, `unknown`. |
| `contract_id` | angka bulat |  | sistem | → `contract.id`. hanya untuk direction=customer |
| `mybhakti_po_ref` | teks |  | sistem | rujukan opak ke MyBhakti, diisi n8n -- SENGAJA bukan FK (hlm. 7) |
| `bast_number_customer` | teks |  | sistem | nomor versi pelanggan |
| `bast_number_internal` | teks |  | sistem | nomor versi BUT -- dari numbering service milik RPA (hlm. 20) |
| `handover_date_text` | teks |  | sistem | apa adanya di dokumen |
| `handover_date` | tanggal |  | sistem | hasil parse; NULL kalau gagal |
| `handover_city` | teks |  | sistem |  |
| `work_title` | teks | ya | sistem |  |
| `basis_doc_type` | teks |  | sistem | Pilihan: `contract`, `pks`, `spk`, `order_note`, `purchase_order`, `other`. |
| `basis_doc_number` | teks |  | sistem | seperti tercetak |
| `basis_doc_date_text` | teks |  | sistem |  |
| `basis_doc_date` | tanggal |  | sistem |  |
| `basis_doc_value` | angka |  | sistem |  |
| `basis_doc_value_vat` | teks |  | sistem | Pilihan: `included`, `excluded`, `unstated`. |
| `currency` | kode 3 huruf | ya | sistem | default IDR |
| `acceptance_statement` | teks |  | sistem |  |

### `bast_party`

Tepat 2 baris per BAST. Cuplikan saat penandatanganan -- jabatan berubah, dokumen yang sudah diteken tidak boleh ikut berubah.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `org_name_text`
- **Kunci anti-dobel:** `bast_id` + `role`
- **Induk:** `bast`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `bast_id` | angka bulat | ya | sistem | → `bast.id`. |
| `role` | teks | ya | sistem | peran, BUKAN 'Pihak Pertama/Kedua' -- label itu terbalik antar-format Pilihan: `handover`, `receiver`. |
| `org_name_text` | teks | ya | sistem | nama seperti ditandatangani |
| `signer_name` | teks | ya | sistem |  |
| `signer_title` | teks |  | sistem |  |
| `org_address_text` | teks |  | sistem |  |
| `mybhakti_party_ref` | teks |  | sistem | opak, diisi n8n |

### `bast_item`

Baris serah terima. Kolom [2026.10.1] adalah informasi yang baru ada di tahap serah terima (tanggal aktif, AO/SID, lokasi). Harga boleh NULL: format kampus/vendor/instansi tidak memuatnya.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `description`
- **Kunci anti-dobel:** `bast_id` + `line_no`
- **Induk:** `bast`, `contract_item`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `bast_id` | angka bulat | ya | sistem | → `bast.id`. |
| `line_no` | angka bulat | ya | sistem |  |
| `contract_item_id` | angka bulat |  | sistem | → `contract_item.id`. [2026.10.1] baris BoQ kontrak yang diserahkan -- bila terisi, uraian & harga DIBACA dari contract_item, sehingga pasti sama dengan kontrak |
| `description` | teks | ya | sistem |  |
| `quantity` | angka |  | sistem |  |
| `unit` | teks |  | sistem |  |
| `unit_price` | angka |  | sistem |  |
| `line_total` | angka |  | sistem |  |
| `test_result` | teks |  | sistem |  |
| `activation_date_text` | teks |  | sistem | [2026.10.1] 'Tanggal Aktif' apa adanya |
| `activation_date` | tanggal |  | sistem | [2026.10.1] hasil parse |
| `service_order_ref` | teks |  | sistem | [2026.10.1] 'No. AO' layanan |
| `service_id` | teks |  | sistem | [2026.10.1] 'SID' layanan |
| `location` | teks |  | sistem | [2026.10.1] lokasi pemasangan / layanan |
| `remarks` | teks |  | sistem |  |

### `bast_condition`

Fakta tambahan BAST sebagai BARIS. Fakta baru = nilai condition_type baru, bukan kolom baru.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `condition_type`
- **Kunci anti-dobel:** — (diganti utuh per induk)
- **Induk:** `bast`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `bast_id` | angka bulat | ya | sistem | → `bast.id`. |
| `condition_type` | teks | ya | sistem | Pilihan: `progress_percent`, `service_active_since`, `acceptance_test_ref`, `delivery_reconciliation_ref`, `supporting_document`, `amount_in_words`. |
| `value_text` | teks |  | sistem |  |
| `value_number` | angka |  | sistem |  |
| `value_date` | tanggal |  | sistem |  |

### `bast_draft`

Draf BAST pelanggan dari kontrak terverifikasi. Nomor dari numbering service, render oleh dol-render (RPA), lampiran oleh compiler BAST (Network).

- **Pemilik:** RPA Engineer
- **Diisi oleh:** sistem; kolom milik PM: `approved_by`, `approved_at`
- **Tampil di NocoDB:** ya, judul baris = `work_title`
- **Kunci anti-dobel:** — (diganti utuh per induk)
- **Induk:** `bast`, `contract`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `contract_id` | angka bulat | ya | sistem | → `contract.id`. |
| `draft_bast_number` | teks |  | sistem |  |
| `work_title` | teks | ya | sistem |  |
| `handover_date_text` | teks |  | sistem |  |
| `handover_date` | tanggal |  | sistem |  |
| `handover_city` | teks |  | sistem |  |
| `status` | teks | ya | sistem | Pilihan: `draft`, `pending_review`, `approved`, `generated`, `rejected`. |
| `template_name` | teks |  | sistem | format_telkom / format_kampus / format_instansi |
| `acceptance_statement` | teks |  | sistem |  |
| `generated_doc_url` | teks |  | sistem |  |
| `generated_bast_id` | angka bulat |  | sistem | → `bast.id`. terisi saat status=generated; tanpa ini, kontrak yang di-generate ulang membuat PM tidak tahu draf mana menghasilkan BAST yang mana |
| `approved_by` | teks |  | PM | HANYA diisi manusia (PM) |
| `approved_at` | tanggal & jam |  | PM | HANYA diisi manusia (PM) |

## Evidence

Foto bukti lapangan dari ODK Central (wilayah Network Engineer).

### `evidence_photo`

[2026.10.1] USULAN untuk disepakati dengan Network Engineer (wilayah dol-odk & dol-bast-compiler, hlm. 15). Foto masuk lewat n8n dari ODK Central SETELAH lolos pemeriksaan otomatis (GPS ada, dalam radius lokasi, dalam masa kontrak); PM lalu menyetujui/menolak di NocoDB. Lampiran BAST hanya memakai review_status=approved.

- **Pemilik:** Network Engineer
- **Diisi oleh:** sistem; kolom milik PM: `review_status`, `reviewed_by`, `reviewed_at`, `review_note`
- **Tampil di NocoDB:** ya, judul baris = `component_label`
- **Kunci anti-dobel:** `odk_instance_id`
- **Induk:** `contract_item`, `contract_requirement`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `odk_instance_id` | teks | ya | sistem | unik. ID submission ODK Central -- sinkron ulang = update, bukan baris kembar |
| `contract_item_id` | angka bulat | ya | sistem | → `contract_item.id`. baris BoQ kontrak yang dibuktikan foto ini |
| `requirement_id` | angka bulat |  | sistem | → `contract_requirement.id`. lampiran wajib kontrak yang dipenuhi (bila ada) -- sambungan checklist gabungan |
| `component_label` | teks |  | sistem | mis. '4 Unit Switch', '1 Unit Router' |
| `photo_type` | teks | ya | sistem | foto barang / label serial number / pemasangan / tangkapan layar Pilihan: `item`, `serial_label`, `installation`, `screenshot`. |
| `serial_number` | teks |  | sistem | wajib untuk foto label SN; bahan registry aset & garansi (Bulan 6) |
| `photo_url` | teks | ya | sistem |  |
| `taken_at` | tanggal & jam | ya | sistem | waktu pengambilan foto |
| `gps_lat` | koordinat GPS |  | sistem | lintang, mis. -7.347824 |
| `gps_lon` | koordinat GPS |  | sistem | bujur, mis. 108.232318 |
| `auto_check_notes` | teks |  | sistem | catatan pemeriksaan otomatis n8n, mis. 'jarak 120 m dari lokasi proyek' |
| `review_status` | teks | ya | PM | pending = belum dicek. HANYA PM yang mengubah Pilihan: `pending`, `approved`, `rejected`. |
| `reviewed_by` | teks |  | PM | HANYA diisi PM |
| `reviewed_at` | tanggal & jam |  | PM | HANYA diisi PM |
| `review_note` | teks |  | PM | alasan bila ditolak, mis. 'SN tidak terbaca' |

## Verifikasi

Nilai hasil ekstraksi beserta skor & buktinya, dan keputusan PM per field.

### `extracted_field`

Satu baris per field: nilai ekstraksi + skor + bukti. Antrean kerja PM. Ditulis mesin saja; nilai terbaru per field.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** ya, judul baris = `field_path`
- **Kunci anti-dobel:** `document_id` + `field_path`
- **Induk:** `document`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `document_id` | angka bulat | ya | sistem | → `document.id`. |
| `field_path` | teks | ya | sistem | mis. contract.Nomor Kontrak Kerja |
| `ai_value_text` | teks |  | sistem |  |
| `evidence_page` | angka bulat |  | sistem | dihitung deterministik, BUKAN ditulis LLM |
| `evidence_quote` | teks |  | sistem | potongan teks dokumen yang cocok |
| `evidence_score` | angka |  | sistem | 0-1: seberapa persis nilai ditemukan di teks dokumen |
| `system_status` | teks | ya | sistem | saran sistem, BUKAN persetujuan Pilihan: `auto_verified`, `auto_accepted`, `review_required`, `unsupported`, `conflict`, `missing`. |

### `field_review`

Keputusan PM per field (hlm. 11 & 20). Pipeline tidak pernah menulis ke sini.

- **Pemilik:** PM
- **Diisi oleh:** PM (manusia)
- **Tampil di NocoDB:** ya, judul baris = `field_path`
- **Kunci anti-dobel:** `document_id` + `field_path`
- **Induk:** `document`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `document_id` | angka bulat | ya | PM | → `document.id`. RESTRICT: dokumen dengan keputusan PM tidak boleh terhapus diam-diam |
| `field_path` | teks | ya | PM |  |
| `reviewed_ai_value_text` | teks |  | PM | nilai AI yang DILIHAT PM saat memutuskan; kalau nilai AI berubah, konfirmasi lama tidak berlaku untuk nilai baru |
| `decision` | teks | ya | PM | Pilihan: `confirmed`, `corrected`, `rejected`. |
| `final_value_text` | teks |  | PM |  |
| `reviewed_by` | teks | ya | PM |  |
| `reviewed_at` | tanggal & jam | ya | PM |  |
| `reviewer_note` | teks |  | PM |  |

## Audit

Jejak teknis pemrosesan — hanya di PostgreSQL, tidak tampil di NocoDB.

### `extraction_run`

Jejak tiap pemrosesan -- dasar bukti 'Terukur' (hlm. 21). Hanya di PostgreSQL: NocoDB hanya memuat nilai ekstraksi + confidence, bukan metadata teknis AI.

- **Pemilik:** AI Engineer
- **Diisi oleh:** sistem
- **Tampil di NocoDB:** tidak (hanya PostgreSQL)
- **Kunci anti-dobel:** — (diganti utuh per induk)
- **Induk:** `document`

| Kolom | Tipe | Wajib | Diisi | Keterangan |
|---|---|---|---|---|
| `document_id` | angka bulat | ya | sistem | → `document.id`. |
| `ocr_engine` | teks |  | sistem |  |
| `llm_model` | teks |  | sistem |  |
| `prompt_version` | teks |  | sistem |  |
| `schema_version` | teks |  | sistem |  |
| `llm_call_count` | angka bulat |  | sistem |  |
| `parse_seconds` | angka |  | sistem |  |
| `extract_seconds` | angka |  | sistem |  |
| `validation_status` | teks |  | sistem |  |
| `started_at` | tanggal & jam |  | sistem |  |
