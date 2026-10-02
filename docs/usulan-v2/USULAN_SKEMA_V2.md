# Usulan Skema Data v2 — Hasil Ekstraksi Dokumen & Skor Keyakinan

**Status:** usulan, menunggu persetujuan PM & mentor. Belum dipakai sistem.
**Diagram:** `skema_v2.dbml` di folder ini (buka dengan ekstensi dbdiagram, atau tempel ke dbdiagram.io).

---

## 1. Database ini menyimpan apa?

Sistem membaca dokumen proyek (Kontrak/SPK/PKS, SPH, BAST) dengan AI. Untuk **setiap
field** — misalnya *Nomor Kontrak*, *Nilai PPN*, *NPWP Pihak Kedua* — AI mencatat:

1. **nilai** yang ia baca,
2. **di halaman mana** dan **kutipan teks** yang menjadi buktinya,
3. **skor keyakinan** (0–100) seberapa yakin nilai itu benar,
4. **status** yang menyarankan apakah field perlu diperiksa.

PM lalu memeriksa field-field itu dan mencatat keputusannya. Data yang sudah
terverifikasi dipakai untuk menyusun draf BAST.

Yang **tidak** disimpan di sini: data master klien, vendor, proyek, dan PO. Sumbernya
MyBhakti; di sini hanya ada kolom rujukan (`mybhakti_*_ref`) yang diisi n8n.

## 2. Kenapa ada versi 2

| Masalah di versi sekarang | Perbaikan di v2 |
|---|---|
| 13 tabel, nama berbahasa Inggris | **9 tabel** tampil di NocoDB, nama bahasa Indonesia |
| Rincian barang terpecah di 3 tabel (`contract_item`, `sph_item`, `bast_item`) | Satu tabel **`rincian_item`** |
| Para pihak terpecah di 2 tabel + kolom vendor di tabel SPH | Satu tabel **`pihak`** |
| `bast_condition` menyimpan ulang nilai yang sudah ada di hasil ekstraksi | Dihapus — tidak ada data ganda |
| **Skor keyakinan (confidence) tidak tersimpan**, hanya skor bukti | `skor_keyakinan` dan `skor_bukti` dua-duanya disimpan |
| Skor tampil "0,876%" padahal maksudnya 87,6% | Skor disimpan dalam skala 0–100 |
| Uang tampil dengan simbol dolar ($) | Kolom uang diatur ke Rupiah (Rp, format Indonesia) |

## 3. Sembilan tabel yang tampil di NocoDB

| Kelompok | Tabel | Isinya | Siapa yang mengisi |
|---|---|---|---|
| Dokumen masuk | `dokumen` | satu baris per berkas PDF | sistem |
| | `kontrak` | nomor, nama pekerjaan, tanggal, nilai, PPN, rekening, denda | sistem |
| | `sph` | nomor, perihal, masa berlaku, subtotal, PPN, total penawaran | sistem |
| | `bast` | arah BAST, nomor, tanggal serah terima, dokumen dasar, nilai | sistem |
| Isi dokumen | `pihak` | semua pihak: pihak pertama/kedua, vendor/klien, penyerah/penerima | sistem |
| | `rincian_item` | baris barang/pekerjaan (BoQ) dari semua jenis dokumen | sistem |
| **Verifikasi** | **`hasil_ekstraksi`** | **satu baris per field: nilai AI + skor keyakinan + bukti** | sistem |
| | **`review_pm`** | **keputusan PM per field** | **PM saja** |
| Keluaran | `draf_bast` | draf BAST dari kontrak terverifikasi + status persetujuan | sistem, disetujui PM |

Tabel ke-10, `riwayat_proses` (mesin OCR, model AI, durasi), hanya ada di database
untuk keperluan teknis dan **tidak tampil di NocoDB**, sesuai arahan Delivery Ops.

**Kenapa tabel `kontrak`/`sph`/`bast` tidak memuat semua field?** Tabel kepala hanya
memuat kolom yang dipakai proses berikutnya (pembuatan draf BAST, pencocokan harga).
Semua field lain — garansi, jumlah terbilang, lokasi, klausul — tetap tersimpan lengkap
di `hasil_ekstraksi`, satu baris per field, lengkap dengan skor dan buktinya. Tidak ada
yang hilang, dan tidak ada yang tersimpan dua kali.

## 4. Cara membaca skor dan status

**Skor keyakinan (confidence), 0–100**, dihitung sistem dengan rumus tetap — bukan
tebakan AI:

| Komponen | Bobot | Artinya |
|---|---|---|
| Kecocokan dengan teks dokumen | 60% | nilai ditemukan persis/hampir persis di dokumen? |
| Kualitas hasil scan | 15% | teks asli PDF atau hasil OCR |
| Lolos aturan bisnis | 25% | mis. subtotal + PPN = total, tanggal selesai ≥ tanggal mulai |

**Status sistem** — saran, **bukan persetujuan**:

| Status | Kapan | Yang disarankan untuk PM |
|---|---|---|
| `terverifikasi_otomatis` | ditemukan persis di dokumen, lolos semua aturan | cek sekilas |
| `diterima_otomatis` | bukti kuat tapi tidak persis sama | cek sekilas |
| `perlu_review` | bukti lemah, atau ada peringatan aturan | periksa |
| `konflik` | melanggar aturan, mis. total ≠ subtotal + PPN | **periksa lebih dulu** |
| `tidak_ditemukan` | nilai terisi tapi tidak ada di dokumen — kemungkinan karangan AI | **periksa lebih dulu** |
| `kosong` | AI tidak mengisi field ini | isi bila perlu |

**Batas keandalan yang sudah diukur** (eval 25–29 September 2026, sampel masih kecil):
status `terverifikasi_otomatis` benar pada sekitar 93% field (28 dari 30). Artinya status
ini membantu mengurutkan pekerjaan, tetapi **tidak menggantikan pemeriksaan PM** — terutama
untuk harga, yang menurut briefing selalu diverifikasi manusia.

## 5. Prinsip yang dijaga

1. **Satu penulis per tabel.** Sistem menulis `hasil_ekstraksi`; PM menulis `review_pm`.
   Memproses ulang dokumen tidak mungkin menimpa keputusan PM.
2. **Teks asli dan hasil baca dipisah.** `tanggal_kontrak_teks` menyimpan apa adanya di
   dokumen; `tanggal_kontrak` menyimpan hasil baca sistem dan boleh kosong bila sistem
   tidak yakin. Data tidak gagal masuk hanya karena format tanggalnya aneh.
3. **Tidak ada data ganda.** Setiap fakta disimpan di satu tempat.
4. **Dokumen yang sama tidak masuk dua kali.** `hash_file` adalah sidik jari isi berkas;
   mengunggah ulang berkas yang sama memperbarui baris lama.

## 6. Yang perlu diputuskan

| # | Keputusan | Usulan |
|---|---|---|
| 1 | Nama tabel & kolom bahasa Indonesia, istilah kantor (BAST, SPH, PPN, NPWP, BoQ, PO) tetap | setuju |
| 2 | Tabel `pihak` dan `rincian_item` digabung lintas jenis dokumen | setuju |
| 3 | `bast_condition` dihapus (datanya sudah ada di `hasil_ekstraksi`) | setuju |
| 4 | NocoDB di atas PostgreSQL (aturan unik & relasi ditegakkan database), bukan tabel yang dibuat langsung di NocoDB | perlu dibahas dengan mentor |

## 7. Setelah disetujui

1. Isi `skema_v2.dbml` dipindah ke `dol_schema/model.py` (satu-satunya definisi skema).
2. Pemeta di `dol-parser` disesuaikan dengan nama baru; tes diperbarui.
3. Tabel NocoDB dibuat ulang dari skema baru dengan kolom uang Rupiah dan skor persen.
4. Base NocoDB lama tetap disimpan sampai base baru terbukti berjalan.

---

**Lembar persetujuan**

| Peran | Nama | Keputusan | Tanggal |
|---|---|---|---|
| PM | | | |
| Mentor | | | |
| AI Engineer | | | |
