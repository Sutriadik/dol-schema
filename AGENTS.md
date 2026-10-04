# AGENTS.md — panduan untuk agen AI yang bekerja di dol-schema

Repo ini menjawab satu pertanyaan: **bentuk data Delivery Ops Layer seperti apa.** Tidak ada
logika pengisian di sini. Yang mengisi: dol-parser (AI Engineer), dol-n8n (RPA Engineer),
dol-bast-compiler (Network Engineer). Satu perubahan di sini menyentuh ketiganya.

Baca dulu: `README.md`, `generated/KAMUS_DATA.md`, `CHANGELOG.md`, dan
`docs/WORKSHOP_SKEMA.md` (keputusan yang masih terbuka). Dokumen proyek lengkap (PRD, SRS,
SDD) ada di repo sejajar `../dol-parser/docs/proyek/`.

## Perintah

```bash
python -m dol_schema --emit      # bangkitkan ulang generated/ dari model.py
python -m dol_schema --check     # gagal bila generated/ basi
python -m pytest tests           # invarian skema
python -m dol_schema --tables    # ringkasan tabel
```

Paket ini tanpa dependensi. Di mesin pengguna, interpreter yang dipakai biasanya
`../dol-parser/.venv311/bin/python`.

## Aturan

1. **`dol_schema/model.py` satu-satunya tempat nama tabel & kolom ditulis.** Semua di
   `generated/` dibangkitkan; jangan diedit tangan (kecuali `schema.dbdiagram`, tata letak
   diagram dari ekstensi).
2. **Setiap perubahan bentuk data menaikkan `SCHEMA_VERSION`** (tabel, kolom, tipe, pilihan
   nilai, label, status, relasi), lalu `--emit`, lalu entri `CHANGELOG.md` dengan dampak bagi
   konsumen (aman / perlu penyesuaian / perlu migrasi data), lalu commit model + `generated/`
   bersama. Buat tag git dengan nama versi (`companion-YYYY.MM.N`).
3. **Dua lapis nama.** Nama teknis Inggris tidak diubah demi tampilan. Yang dilihat orang
   kantor (label, pilihan nilai di NocoDB) bahasa Indonesia, huruf/angka/spasi saja — label
   dipakai sebagai kunci API NocoDB.
4. **Tabel `ditunda` tidak diaktifkan sendirian.** BAST dibahas bersama RPA, evidence bersama
   Network Engineer. Ubah status hanya setelah keputusan workshop tercatat.
5. **Tidak ada tabel milik MyBhakti** (klien, vendor, proyek, PO) — hanya kolom
   `mybhakti_*_ref`, sengaja bukan FK (briefing hlm. 7).
6. **Kolom milik PM** ditandai `written_by="human"`; tabel berlaku yang ditulis mesin wajib
   punya kunci anti-dobel. Tes menjaga keduanya — jangan melonggarkan tesnya.
7. **Jangan menambah kolom tanpa bukti** bahwa nilainya memang ada di dokumen nyata.
8. **Tanpa atribusi AI di commit.** Commit atas nama pengguna.

Setelah versi naik, dol-parser harus menyesuaikan pemeta dan `DOL_SCHEMA_VERSION`, dan base
NocoDB biasanya perlu dibuat ulang (`../dol-parser/scripts/nocodb_setup.py --create-base`).
