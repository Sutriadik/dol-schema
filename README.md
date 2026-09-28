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
| `generated/schema.sql` | PostgreSQL — sumber data eksternal NocoDB |
| `generated/schema.json` | n8n & compiler BAST (tidak bisa import Python) |
| `generated/nocodb_fields.json` | pembuatan tabel lewat API NocoDB |
| `docs/ERD.md` | diagram ERD + kamus data untuk PM & mentor |

## Pakai

```bash
python -m dol_schema --tables    # ringkasan tabel
python -m dol_schema --emit      # tulis ulang generated/
python -m dol_schema --check     # gagal bila generated/ basi (dipakai di CI)
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

1. Ubah `dol_schema/model.py`.
2. `python -m dol_schema --emit`
3. Commit model **dan** `generated/` dalam satu commit — supaya artefak tidak pernah
   berbeda dari modelnya.
4. Naikkan `SCHEMA_VERSION` bila perubahannya memutus kompatibilitas.
