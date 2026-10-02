# dol-schema

Definisi skema data **Delivery Ops Layer (DOL)** PT Bhakti Unggul Teknovasi.

Repo ini menjawab satu pertanyaan saja: **bentuk datanya seperti apa.** Cara mengisinya
bukan urusan repo ini — itu milik `dol-parser` (ekstraksi AI), `dol-n8n` (orkestrasi), dan
`dol-bast-compiler` (lampiran BAST).

## Kenapa dipisah dari dol-parser

Tiga repo memakai bentuk data yang sama. Kalau nama kolom didefinisikan di masing-masing
repo, ketiganya akan berbeda diam-diam dan baru ketahuan saat data gagal masuk NocoDB.
Briefing magang hlm. 20 juga mewajibkan skema NocoDB hidup di Git, bukan hanya di UI.

Di sini nama kolom **hanya ditulis satu kali**, di `dol_schema/model.py`. Semua yang lain
dibangkitkan darinya:

| Artefak | Untuk siapa |
|---|---|
| `generated/KAMUS_DATA.md` | **mulai dari sini** — kamus data berbahasa Indonesia untuk PM & ketiga tim |
| `generated/schema.json` | n8n & compiler BAST: kolom, kunci upsert, cara mengisi FK, kolom milik PM |
| `generated/schema.sql` | PostgreSQL — tabel, constraint, dan view penyusunan BAST |
| `generated/nocodb_fields.json` | pembuatan tabel NocoDB (tipe, pilihan, keterangan kolom, judul baris) |
| `generated/schema.dbml` | diagram skema (dbdiagram.io / ekstensi dbdiagram) |
| `docs/ERD.md` | penjelasan desain & lembar persetujuan untuk PM dan mentor |

Semua berkas di `generated/` dibangkitkan — jangan diedit tangan; ubah `model.py` lalu `--emit`.

## Untuk tiap tim

**RPA Engineer (n8n, numbering, render)** — baca `generated/schema.json`:
- `insert_order`: urutan kirim tabel (induk dulu).
- per tabel `upsert_key`: cari dengan kunci ini, PATCH bila ada, POST bila tidak.
- per tabel `parent_refs`: baris anak membawa `_<induk>_ref`; tukar dengan Id induk.
- per tabel `human_columns`: **jangan pernah dikirim** — milik PM.
- blok `conventions`: aturan format tanggal, uang, dan rujukan MyBhakti.
- Nomor BAST internal (`bast.bast_number_internal`) berasal dari numbering service.

**Network Engineer (ODK, compiler lampiran)** — tabel `evidence_photo` (usulan, mohon ditinjau):
- satu baris per foto ODK, kunci anti-dobel `odk_instance_id`;
- wajib menunjuk `contract_item_id` (baris BoQ yang dibuktikan), opsional `requirement_id`
  (lampiran wajib kontrak yang dipenuhi) — dua sambungan inilah yang membentuk checklist gabungan;
- kolom `review_*` milik PM; n8n hanya mengirim foto yang lolos pemeriksaan otomatis.

**PM (NocoDB)**:
- antrean kerja: `extracted_field` dengan filter `system_status` (`conflict`, `unsupported`,
  `review_required` lebih dulu); keputusan dicatat di `field_review`;
- peringatan per dokumen (mis. salinan ganda) ada di `document.validation_notes`;
- foto evidence disetujui/ditolak lewat `evidence_photo.review_status`;
- arahkan kursor ke judul kolom untuk melihat keterangannya.

**Penyusunan BAST** — lihat bagian "Cara menyusun BAST" di `generated/KAMUS_DATA.md`. Di
PostgreSQL tersedia view `bast_rincian`, `evidence_siap_lampiran`, dan `checklist_gabungan`.

### Melihat diagram

- **dbdiagram.io:** buka <https://dbdiagram.io/d>, tempel seluruh isi `generated/schema.dbml`.
- **VS Code / Antigravity:** ekstensi resmi *dbdiagram*, buka `generated/schema.dbml`, lalu
  *DBML: Open Preview to the Side*.

Warna header = pemilik: **biru** AI Engineer, **ungu** Network Engineer, **hijau** RPA
Engineer, **oranye** PM, **abu-abu** hanya PostgreSQL. Kolom bertanda `[DIISI PM]` hanya diubah PM.

## Pakai

```bash
python -m dol_schema --tables    # ringkasan tabel
python -m dol_schema --emit      # tulis ulang generated/
python -m dol_schema --check     # gagal bila generated/ basi (dipakai di CI)
python -m pytest tests           # invarian skema: FK, urutan insert, kolom milik PM
```

Dari repo lain:

```bash
pip install -e ../dol-schema
```

```python
from dol_schema import ALL_TABLES, generate_ddl, validate_payload, insert_order
```

Konsumen non-Python cukup membaca `generated/schema.json` — tidak perlu install apa pun.

## Aturan yang ditegakkan struktur, bukan kedisiplinan

- **Satu penulis per tabel.** `extracted_field` ditulis mesin; `field_review` ditulis
  manusia (PM). Karena terpisah tabel, memproses ulang dokumen secara struktural tidak bisa
  menimpa keputusan PM. Briefing hlm. 11 & 20.
- **Mentah vs terparse.** Nilai apa adanya di dokumen ada di kolom `*_text`; hasil parse
  bertipe date/numeric di kolom tanpa akhiran dan boleh NULL. OCR yang merusak tanggal tidak
  membuat barisnya gagal masuk.
- **Tipe dideklarasikan, bukan ditebak dari nama kolom.** Exporter lama menebak tipe dari
  nama, jadi kolom bernama numerik yang isinya teks (`"1/1000"`, `"30 hari kalender"`) gagal
  masuk NocoDB tanpa pesan jelas. Di sini `Column.type` eksplisit, jadi kelas bug itu tidak
  bisa muncul lagi.
- **Tidak menyimpan yang bisa dihitung.** Status verifikasi dokumen adalah VIEW.
- **Batas kepemilikan data.** Tidak ada tabel klien/vendor/PO — itu milik MyBhakti dan
  read-only bagi kita (briefing hlm. 7). Rujukannya berupa kolom `*_ref` opak, sengaja
  BUKAN foreign key.

## Mengubah skema

1. Ubah `dol_schema/model.py` dan naikkan `SCHEMA_VERSION` — setiap perubahan tabel,
   kolom, tipe, pilihan nilai, atau relasi, termasuk penambahan.
2. `python -m dol_schema --emit`
3. Commit model **dan** `generated/` dalam satu commit — supaya artefak tidak pernah
   berbeda dari modelnya.
4. Catat di [CHANGELOG.md](CHANGELOG.md) beserta dampaknya untuk konsumen
   (aman / perlu penyesuaian / perlu migrasi data).

Aturan versi dan riwayat lengkapnya ada di [CHANGELOG.md](CHANGELOG.md).
