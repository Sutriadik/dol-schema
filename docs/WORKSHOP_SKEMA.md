# Workshop Skema Companion — bahan untuk bertiga

**Untuk:** RPA Engineer, Network Engineer, AI Engineer, + mentor
**Durasi:** 90 menit
**Keluar dari ruangan dengan:** keputusan atas tabel yang masih **ditunda**

> Briefing hlm. 12: *"Skema data companion dirancang bertiga di Bulan 2 — itu fondasi yang
> dipakai ketiganya."*

---

## Yang sudah berlaku (tidak perlu diputuskan ulang)

Versi `companion-2026.10.4`. Rinciannya di [`generated/KAMUS_DATA.md`](../generated/KAMUS_DATA.md).

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

## Yang harus diputuskan bersama

### 1. BAST (bersama RPA Engineer) — tabel usulan di `generated/schema_usulan.sql`

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 1a | Kunci anti-dobel **Draf BAST**: per kontrak + nomor termin? | Tanpa kunci, pengiriman ulang menghapus persetujuan PM (terbukti di versi lama). Sejak 2026.10.4 termin tersimpan di *Ketentuan Pembayaran* (`contract_payment_term.line_no`), calon rujukan kunci ini. |
| 1b | Nomor BAST dari numbering service: kapan dipesan — saat draf dibuat atau saat disetujui? | Nomor duplikat tidak bisa diperbaiki setelah terkirim (hlm. 20). |
| 1c | Satu kontrak bisa punya beberapa BAST (termin/parsial)? | Menentukan relasi kontrak → BAST (1:1 atau 1:banyak). |
| 1d | Serah terima sering berupa paket berita acara (BAUT, BARD, BAPB) — satu tabel atau `doc_type` tambahan? | Dari 20 proyek nyata, BAUT pernah 55 halaman. |
| 1e | Siapa yang merender BAST (dol-render) dan dari data apa? | Penyusun data draf sudah ada di dol-parser (`app/companion/generator.py`) dan hanya membaca nilai terverifikasi. |

Bahan: [`docs/usulan-alur-bast/TEMUAN_14_BAST.md`](usulan-alur-bast/TEMUAN_14_BAST.md) —
temuan dari 14 BAST asli (label "Pihak Pertama/Kedua" terbalik antar-format, arah BAST bisa
diturunkan dari peran BUT).

### 2. Evidence (bersama Network Engineer) — tabel usulan `evidence_photo`

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 2a | Lampiran wajib kontrak sering berupa **dokumen** (BA uji terima, surat jalan), bukan foto. Satu tabel bukti untuk keduanya, atau dua? | Checklist gabungan (hlm. 15) harus bisa dipenuhi oleh dokumen. |
| 2b | Bagaimana teknisi di ODK memilih baris BoQ yang dibuktikan, padahal ODK tidak tahu Id baris NocoDB? | Kolom `contract_item_id` wajib di usulan sekarang. |
| 2c | Pemeriksaan otomatis (GPS, radius lokasi, masa kontrak) di n8n atau di ODK? | Menentukan isi `auto_check_notes`. |

### 3. Pengadaan (bersama RPA Engineer) — belum ada di skema

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 3a | Tabel **procurement item** (barang yang dibeli) terpisah dari Rincian Kontrak (barang yang dijual)? | Briefing hlm. 7 memisahkan keduanya; satu baris kontrak bisa butuh beberapa barang beli. Tabel banding harga (Bulan 5) bergantung pada ini. |
| 3b | Tabel **SPPH** (permintaan ke vendor) dan pelacakan balasan (threadId Gmail) — milik siapa? | Diagnosis no. 2 "balasan vendor tak terlacak" (hlm. 5). |

### 4. Infrastruktur (bersama + mentor)

| # | Pertanyaan | Kenapa penting |
|---|---|---|
| 4a | PostgreSQL + NocoDB sebagai sumber eksternal, atau NocoDB murni? | Tabel yang dibuat lewat API NocoDB **tidak punya** UNIQUE, CHECK, FK, maupun view. Integritas hanya dijaga pengirim. |
| 4b | Export skema NocoDB ke Git tiap minggu (hlm. 20) — siapa, bagaimana? | `scripts/nocodb_setup.py --compare-schema` di dol-parser bisa jadi pemeriksanya. |

---

## Kontrak antar-service

| Dari | Ke | Bentuk | Status |
|---|---|---|---|
| n8n | parser | `POST /api/v1/jobs` (multipart + `callback_url`) | ✅ jalan |
| parser | n8n | `companion_payload` (nama teknis) + `companion_catatan` | ✅ jalan |
| n8n/parser | NocoDB | rekaman dengan **judul** kolom (`columns[].label` di schema.json) | ✅ pusher dol-parser; n8n menyesuaikan |
| ODK | n8n | ? | ⬜ keputusan 2 |
| numbering | n8n | ? | ⬜ keputusan 1b |

## Setelah workshop

```bash
# ubah dol_schema/model.py sesuai kesepakatan: status "ditunda" -> "berlaku", naikkan versi
python -m dol_schema --emit && python -m pytest tests
# catat di CHANGELOG.md, lalu buat base NocoDB baru dari dol-parser:
python scripts/nocodb_setup.py --create-base
```
