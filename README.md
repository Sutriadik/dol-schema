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
| `generated/schema.json` | n8n & compiler BAST: kolom, judul NocoDB, kunci upsert, kolom milik PM |
| `generated/nocodb_fields.json` | pembuatan tabel NocoDB (judul, tipe, pilihan, keterangan) |
| `generated/schema.sql` | PostgreSQL — tabel yang **berlaku**, constraint, view verifikasi |
| `generated/schema_usulan.sql` | PostgreSQL — tabel **usulan** (ditunda), untuk workshop |
| `generated/schema.dbml` | diagram (dbdiagram.io / ekstensi dbdiagram) |
| `docs/ERD.md` | penjelasan desain & lembar persetujuan untuk PM dan mentor |
| `docs/WORKSHOP_SKEMA.md` | keputusan skema yang masih terbuka, untuk dibahas bertiga |
| `AGENTS.md` | aturan untuk agen AI yang mengubah skema |
| `../dol-parser/docs/proyek/` | dokumen proyek lengkap (KAK, PRD, SRS, SDD, rencana uji) |

Semua berkas di `generated/` dibangkitkan — jangan diedit tangan; ubah `model.py` lalu
`--emit`. (`generated/schema.dbdiagram` adalah pengecualian: tata letak diagram yang disimpan
ekstensi dbdiagram, bukan keluaran `--emit`.)

## Dua lapis nama

- **Judul** (bahasa Indonesia) — yang dilihat orang kantor di NocoDB, kamus, dan diagram.
  Pilihan nilai di sel NocoDB juga bahasa Indonesia (`benar`, `dikoreksi`, `bukti_kuat`, …).
- **Nama teknis** (snake_case Inggris) — dipakai kode, SQL, dan n8n. Tidak diubah demi
  tampilan, karena mengubahnya memutus setiap konsumen.

API rekaman NocoDB memakai **judul** sebagai kunci JSON dan di klausa `where`. Pengirim
menerjemahkan dengan `to_nocodb_record()` (Python) atau `columns[].label` di `schema.json`.

## Status tabel

| Status | Arti | Tabel |
|---|---|---|
| **berlaku** | disepakati, dibuat di NocoDB | Dokumen, Kontrak, Pihak Kontrak, Rincian Kontrak, Syarat Kontrak, Ketentuan Pembayaran, SPH Vendor, Rincian SPH, Hasil Ekstraksi, Keputusan PM (+ Riwayat Pemrosesan, hanya PostgreSQL) |
| **ditunda** | usulan, menunggu kesepakatan tim | BAST, Pihak BAST, Rincian BAST, Kondisi BAST, Draf BAST (bersama RPA); Foto Evidence (bersama Network Engineer) |

BAST pelanggan bersumber dari kontrak (briefing hlm. 10). Selama tabel kontrak lengkap dan
terverifikasi PM, penyusun BAST cukup membaca view `nilai_terverifikasi` — tabel BAST tidak
perlu ada lebih dulu.

## Untuk tiap tim

**RPA Engineer (n8n, numbering, render)** — baca `generated/schema.json`:
- `insert_order`: urutan kirim tabel (induk dulu), hanya tabel berlaku.
- per tabel `upsert_key`: cari dengan kunci ini, PATCH bila ada, POST bila tidak.
- per tabel `parent_refs`: baris anak membawa `_<induk>_ref`; tukar dengan Id induk.
- per tabel `human_columns`: **jangan pernah dikirim** — milik PM.
- per kolom `label`: judul NocoDB, dipakai sebagai kunci saat mengirim.
- blok `conventions`: aturan yang berlaku untuk setiap pengirim.

**Network Engineer (ODK, compiler lampiran)** — tabel usulan `evidence_photo` di
`generated/schema_usulan.sql`. Pertanyaan terbuka untuk dibahas: lampiran wajib kontrak
sering berupa dokumen (BA uji terima, surat jalan), bukan foto.

**PM (NocoDB)** — lihat bagian "Cara PM memakai tabel ini" di `generated/KAMUS_DATA.md`.

### Melihat diagram

- **dbdiagram.io:** buka <https://dbdiagram.io/d>, tempel seluruh isi `generated/schema.dbml`.
- **VS Code / Antigravity:** ekstensi resmi *dbdiagram*, buka `generated/schema.dbml`, lalu
  *DBML: Open Preview to the Side*.

Warna header = pemilik: **biru** AI Engineer, **ungu** Network Engineer, **hijau** RPA
Engineer, **oranye** PM, **abu-abu** hanya PostgreSQL, **kuning** usulan yang ditunda.

## Pakai

```bash
python -m dol_schema --tables    # ringkasan tabel
python -m dol_schema --emit      # tulis ulang generated/
python -m dol_schema --check     # gagal bila generated/ basi (dipakai di CI)
python -m pytest tests           # invarian skema
ruff check . && ruff format --check .   # gaya kode PEP 8
```

Dari repo lain:

```bash
pip install -e ../dol-schema
```

```python
from dol_schema import ALL_TABLES, validate_payload, insert_order, to_nocodb_record
```

Konsumen non-Python cukup membaca `generated/schema.json` — tidak perlu install apa pun.

## Aturan yang ditegakkan struktur, bukan kedisiplinan

- **Satu penulis per tabel.** `extracted_field` ditulis mesin; `field_review` ditulis
  manusia (PM). Memproses ulang dokumen tidak bisa menimpa keputusan PM.
- **Nilai hilir hanya dari keputusan PM.** View `nilai_terverifikasi` tidak memuat nilai
  sistem yang belum diperiksa, ditolak, atau keputusannya basi.
- **Mentah vs terparse.** Nilai apa adanya di kolom `*_text`; hasil parse boleh NULL.
  Kolom untuk nilai yang bisa tidak terbaca boleh kosong, supaya tidak ada nilai karangan.
- **Tipe dideklarasikan, bukan ditebak dari nama kolom.**
- **Tidak menyimpan yang bisa dihitung.** Status verifikasi dokumen adalah VIEW.
- **Batas kepemilikan data.** Tidak ada tabel klien/vendor/PO — milik MyBhakti (hlm. 7).

**Penting:** UNIQUE, CHECK, foreign key, dan view hanya berlaku bila tabel dibuat dari
`schema.sql` di PostgreSQL. Tabel yang dibuat lewat API NocoDB (`nocodb_fields.json`) hanya
punya kolom; integritasnya dijaga pengirim (validator + pusher dol-parser).

## Mengubah skema

1. Ubah `dol_schema/model.py` dan naikkan `SCHEMA_VERSION` — setiap perubahan tabel,
   kolom, tipe, pilihan nilai, judul, status, atau relasi.
2. `python -m dol_schema --emit`
3. Commit model **dan** `generated/` dalam satu commit.
4. Catat di [CHANGELOG.md](CHANGELOG.md) beserta dampaknya untuk konsumen.
