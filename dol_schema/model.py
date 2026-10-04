"""
dol-schema — definisi model data companion Delivery Ops Layer (SATU sumber kebenaran).

Semua yang lain dibangkitkan dari file ini: DDL PostgreSQL, schema.json untuk n8n & compiler
BAST, spesifikasi kolom NocoDB, diagram DBML, dan kamus data. Nama kolom hanya ditulis di sini.

Dua lapis nama, sengaja dipisah:

- **Nama teknis** (`name`, bahasa Inggris, snake_case) dipakai kode, SQL, dan n8n. Tidak
  pernah diubah demi tampilan, karena mengubahnya memutus setiap konsumen.
- **Label** (`label`, bahasa Indonesia) adalah yang dilihat orang kantor: judul kolom di
  NocoDB, kamus data, diagram. Pilihan nilai (enum) yang tampil di sel NocoDB juga bahasa
  Indonesia, karena NocoDB menyimpan dan menampilkan nilai yang sama.

Status tabel:

- **berlaku**  — disepakati & dipakai sekarang; dibuat di NocoDB.
- **ditunda**  — usulan yang menunggu kesepakatan tim (BAST bersama RPA, evidence bersama
  Network Engineer). Tetap didefinisikan di sini supaya bisa dibahas, tapi TIDAK dibuat di
  NocoDB dan DDL-nya terpisah (`generated/schema_usulan.sql`).

Prinsip yang ditegakkan struktur, bukan kedisiplinan:

- **Satu penulis per kolom.** Kolom milik manusia ditandai `written_by="human"` (per kolom)
  atau seluruh tabel (`Table.written_by`). Validator menolak payload mesin yang mengisinya.
- **Mentah vs terparse.** Nilai apa adanya di dokumen di kolom `*_text`; hasil parse di kolom
  tanpa akhiran dan boleh NULL. Kolom yang bisa tidak terbaca dari dokumen boleh NULL, supaya
  pengirim tidak terdorong mengarang nilai pengisi.
- **Batas kepemilikan data (hlm. 7).** Klien, vendor, proyek, PO milik MyBhakti: di sini hanya
  kolom rujukan `mybhakti_*_ref` yang diisi n8n — sengaja BUKAN foreign key.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

SCHEMA_VERSION = "companion-2026.10.3"

# Pemilik tabel menurut briefing hlm. 12-15. Yang merancang & memelihara isi tabelnya.
OWNERS = {
    "ai": "AI Engineer",
    "network": "Network Engineer",
    "rpa": "RPA Engineer",
    "pm": "PM",
}
DOMAINS = ("dokumen", "kontrak", "sph", "bast", "evidence", "verifikasi", "audit")
STATUSES = ("berlaku", "ditunda")


@dataclass(frozen=True)
class Column:
    name: str
    type: str                      # text | int | numeric | coord | date | timestamptz | char3
    label: str = ""                # judul berbahasa Indonesia (NocoDB, kamus, diagram)
    null: bool = True
    unique: bool = False           # UNIQUE satu kolom
    fk: Optional[str] = None       # "tabel.kolom"
    fk_on_delete: str = "CASCADE"  # RESTRICT untuk baris yang dirujuk keputusan manusia
    enum: Optional[tuple] = None   # nilai yang diizinkan -> CHECK di DB, SingleSelect di NocoDB
    check: Optional[str] = None    # ekspresi CHECK tambahan
    default: Optional[str] = None  # nilai bawaan (literal SQL), mis. "'IDR'"
    written_by: Optional[str] = None   # "human" = hanya PM; None = ikut tabel
    note: str = ""


@dataclass(frozen=True)
class Table:
    name: str
    columns: List[Column]
    domain: str
    owner: str
    label: str = ""                # nama tabel berbahasa Indonesia
    unique_together: tuple = ()    # ((kolom, kolom), ...)
    note: str = ""
    written_by: str = "machine"    # machine | human
    nocodb: bool = True            # False = hanya PostgreSQL, tidak pernah dikirim ke NocoDB
    status: str = "berlaku"        # berlaku | ditunda
    display: Optional[str] = None  # kolom yang dipakai NocoDB sebagai judul baris

    def column(self, name: str) -> Optional[Column]:
        return next((c for c in self.columns if c.name == name), None)

    def human_columns(self) -> List[str]:
        """Kolom yang hanya boleh ditulis manusia (seluruh kolom bila tabelnya milik manusia)."""
        if self.written_by == "human":
            return [c.name for c in self.columns if c.name not in AUDIT_COLUMNS]
        return [c.name for c in self.columns if c.written_by == "human"]

    @property
    def in_nocodb(self) -> bool:
        """Dibuat & diisi di NocoDB: hanya tabel yang berlaku dan bukan khusus PostgreSQL."""
        return self.nocodb and self.status == "berlaku"


# Kolom audit yang dimiliki semua tabel. Waktu selalu UTC.
AUDIT_COLUMNS = ("created_at", "updated_at")
_AUDIT = [
    Column("created_at", "timestamptz", "Dibuat", null=False, note="UTC"),
    Column("updated_at", "timestamptz", "Diperbarui", null=False, note="UTC, diperbarui trigger"),
]

# --------------------------------------------------------------------------- pilihan nilai
# Yang tampil di NocoDB: bahasa Indonesia, huruf kecil, garis bawah sebagai spasi.
DOC_TYPES = ("kontrak", "sph", "bast")
CONTRACT_TYPES = ("nota_pesanan", "surat_pesanan", "spk", "kontrak_kerja_sama", "pks", "lainnya")
CONTRACT_PARTY_ROLES = ("pemberi_kerja", "pelaksana")
REQUIREMENT_TYPES = ("lampiran_wajib", "syarat_serah_terima", "boleh_parsial")
# Status bukti dari sistem. Sengaja TIDAK memakai kata "terverifikasi": yang diperiksa sistem
# hanya apakah nilainya ada di dokumen, bukan apakah nilainya benar (briefing hlm. 20).
SYSTEM_STATUSES = ("bukti_kuat", "bukti_cukup", "perlu_dicek", "tidak_ada_di_dokumen",
                   "bertentangan", "kosong")
REVIEW_DECISIONS = ("benar", "dikoreksi", "ditolak")

# Pilihan nilai tabel yang DITUNDA belum diterjemahkan: diputuskan bersama saat disepakati.
BAST_DIRECTIONS = ("customer", "vendor", "unknown")
BAST_DRAFT_STATUSES = ("draft", "pending_review", "approved", "generated", "rejected")
PARTY_ROLES = ("handover", "receiver")
BASIS_DOC_TYPES = ("contract", "pks", "spk", "order_note", "purchase_order", "other")
VAT_MODES = ("included", "excluded", "unstated")
CONDITION_TYPES = (
    "progress_percent", "service_active_since", "acceptance_test_ref",
    "delivery_reconciliation_ref", "supporting_document", "amount_in_words",
)
PHOTO_TYPES = ("item", "serial_label", "installation", "screenshot")
EVIDENCE_REVIEW_STATUSES = ("pending", "approved", "rejected")


# =========================================================================== 1. DOKUMEN
DOCUMENT = Table(
    "document",
    [
        Column("content_hash", "text", "Sidik Berkas", null=False, unique=True,
               note="sha256 isi berkas -- kunci anti-dobel; berkas yang sama diproses ulang "
                    "memperbarui baris yang sama"),
        Column("doc_type", "text", "Jenis Dokumen", null=False, enum=DOC_TYPES),
        Column("source_filename", "text", "Nama Berkas", null=False),
        Column("page_count", "int", "Jumlah Halaman", check="page_count > 0"),
        Column("markdown", "text", "Isi Dokumen",
               note="teks hasil pembacaan sistem, agar PM bisa membaca tanpa membuka PDF. "
                    "Bagian yang rusak OCR bisa sudah dipoles mesin: PDF asli tetap acuan"),
        Column("validation_notes", "text", "Catatan Validasi",
               note="peringatan tingkat dokumen, mis. salinan ganda atau jumlah item tidak "
                    "sama dengan total"),
        *_AUDIT,
    ],
    domain="dokumen", owner="ai", label="Dokumen", display="source_filename",
    note="Setiap berkas yang masuk, apa pun jenisnya.",
)

# =========================================================================== 2. KONTRAK
CONTRACT = Table(
    "contract",
    [
        Column("document_id", "int", "ID Dokumen", null=False, unique=True, fk="document.id",
               note="satu kontrak = satu dokumen"),
        Column("mybhakti_project_ref", "text", "Rujukan Proyek MyBhakti",
               note="proyek/deal di MyBhakti, diisi n8n -- pengikat semua dokumen satu proyek; "
                    "sengaja bukan relasi (hlm. 7)"),
        Column("contract_type", "text", "Jenis Kontrak", enum=CONTRACT_TYPES,
               note="bentuk dokumen dasar"),
        Column("contract_number", "text", "Nomor Kontrak", note="nomor resmi kontrak / SPK / PKS"),
        Column("contract_number_internal", "text", "Nomor Registrasi Internal",
               note="nomor registrasi internal BUT"),
        Column("work_title", "text", "Nama Pekerjaan", note="judul pengadaan / lingkup pekerjaan"),
        Column("location_text", "text", "Lokasi",
               note="kota/lokasi seperti tertulis di kontrak (tempat dibuat atau pelaksanaan)"),
        Column("contract_date_text", "text", "Tanggal Kontrak Tertulis",
               note="apa adanya di dokumen"),
        Column("contract_date", "date", "Tanggal Kontrak", note="hasil baca; kosong bila ragu"),
        Column("start_date_text", "text", "Tanggal Mulai Tertulis"),
        Column("start_date", "date", "Tanggal Mulai"),
        Column("end_date_text", "text", "Tanggal Selesai Tertulis"),
        Column("end_date", "date", "Tanggal Selesai"),
        Column("duration_text", "text", "Jangka Waktu", note="mis. '30 hari kalender'"),
        Column("contract_value", "numeric", "Nilai Kontrak", check="contract_value >= 0",
               note="total termasuk PPN bila dokumen menyebutnya begitu"),
        Column("subtotal_value", "numeric", "Subtotal", check="subtotal_value >= 0"),
        Column("vat_value", "numeric", "Nilai PPN", check="vat_value >= 0"),
        Column("vat_percentage", "text", "Persentase PPN", note="apa adanya di dokumen"),
        Column("currency", "char3", "Mata Uang", null=False, default="'IDR'"),
        Column("payment_mechanism", "text", "Cara Pembayaran"),
        Column("penalty_terms", "text", "Ketentuan Denda"),
        Column("bast_terms", "text", "Syarat Lampiran BAST",
               note="ringkasan; rincian per syarat ada di tabel Syarat Kontrak"),
        Column("bank_name", "text", "Nama Bank"),
        Column("bank_account_number", "text", "Nomor Rekening"),
        Column("bank_account_name", "text", "Nama Pemilik Rekening"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", label="Kontrak", display="contract_number",
    note="Kontrak/SPK pelanggan dalam bentuk apa pun -- dibaca sekali, dipakai sepanjang "
         "proyek (hlm. 11). Sumber kebenaran BAST pelanggan.",
)

CONTRACT_PARTY = Table(
    "contract_party",
    [
        Column("contract_id", "int", "ID Kontrak", null=False, fk="contract.id"),
        Column("role", "text", "Peran", null=False, enum=CONTRACT_PARTY_ROLES,
               note="pemberi_kerja = pelanggan; pelaksana = BUT. Ditentukan dari nama "
                    "instansi, bukan dari sebutan 'Pihak Pertama/Kedua'"),
        Column("party_label_text", "text", "Sebutan di Dokumen",
               note="mis. 'PIHAK PERTAMA' -- sebutan ini bisa terbalik antar-format kontrak, "
                    "karena itu disimpan terpisah dari peran"),
        Column("org_name_text", "text", "Nama Instansi", null=False),
        Column("signer_name", "text", "Nama Penandatangan", note="kosong bila tidak terbaca"),
        Column("signer_title", "text", "Jabatan Penandatangan"),
        Column("org_address_text", "text", "Alamat"),
        Column("mybhakti_party_ref", "text", "Rujukan Pihak MyBhakti", note="diisi n8n"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", label="Pihak Kontrak", display="org_name_text",
    unique_together=(("contract_id", "role"),),
    note="Pihak penandatangan kontrak seperti tertulis saat diteken -- bukan data master. "
         "Satu orang bisa muncul di banyak baris karena menandatangani banyak dokumen.",
)

CONTRACT_ITEM = Table(
    "contract_item",
    [
        Column("contract_id", "int", "ID Kontrak", null=False, fk="contract.id"),
        Column("line_no", "int", "No Urut", null=False, check="line_no > 0",
               note="urutan baca di dokumen"),
        Column("category", "text", "Kelompok"),
        Column("description", "text", "Uraian", null=False),
        Column("specification", "text", "Spesifikasi"),
        Column("quantity", "numeric", "Volume", check="quantity >= 0"),
        Column("unit", "text", "Satuan"),
        Column("period", "text", "Periode"),
        Column("unit_price", "numeric", "Harga Satuan", check="unit_price >= 0",
               note="selalu dikonfirmasi PM (hlm. 20)"),
        Column("line_total", "numeric", "Jumlah Harga", check="line_total >= 0"),
        Column("remarks", "text", "Keterangan"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", label="Rincian Kontrak", display="description",
    unique_together=(("contract_id", "line_no"),),
    note="BoQ kontrak = kewajiban ke pelanggan (hlm. 7). Sumber tunggal rincian pekerjaan "
         "untuk BAST pelanggan.",
)

CONTRACT_REQUIREMENT = Table(
    "contract_requirement",
    [
        Column("contract_id", "int", "ID Kontrak", null=False, fk="contract.id"),
        Column("line_no", "int", "No Urut", null=False, check="line_no > 0"),
        Column("requirement_type", "text", "Jenis Syarat", null=False, enum=REQUIREMENT_TYPES,
               note="lampiran wajib / syarat serah terima / boleh parsial"),
        Column("requirement_text", "text", "Isi Syarat", null=False,
               note="mis. 'Berita Acara Uji Terima'"),
        Column("clause_ref", "text", "Pasal Rujukan", note="mis. 'Pasal 9 ayat 2'"),
        Column("evidence_page", "int", "Halaman", note="halaman tempat syarat ini ditemukan"),
        Column("evidence_quote", "text", "Kutipan Dokumen",
               note="kutipan pendek agar PM tidak perlu membaca ulang kontrak (hlm. 11)"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", label="Syarat Kontrak", display="requirement_text",
    unique_together=(("contract_id", "line_no"),),
    note="Aturan dari kontrak, bukan angka: lampiran wajib, syarat serah terima, boleh parsial "
         "(hlm. 11). Baris lampiran wajib adalah separuh checklist gabungan BAST.",
)

# =========================================================================== 3. SPH VENDOR
SPH = Table(
    "sph",
    [
        Column("document_id", "int", "ID Dokumen", null=False, unique=True, fk="document.id"),
        Column("mybhakti_project_ref", "text", "Rujukan Proyek MyBhakti", note="diisi n8n"),
        Column("mybhakti_vendor_ref", "text", "Rujukan Vendor MyBhakti", note="diisi n8n"),
        Column("sph_number", "text", "Nomor SPH"),
        Column("sph_date_text", "text", "Tanggal SPH Tertulis"),
        Column("sph_date", "date", "Tanggal SPH"),
        Column("project_name", "text", "Perihal", note="perihal / nama pekerjaan yang ditawarkan"),
        Column("client_name", "text", "Ditujukan Kepada", note="instansi yang dituju surat"),
        Column("vendor_name", "text", "Nama Vendor", note="penerbit SPH seperti tertulis"),
        Column("subtotal_value", "numeric", "Subtotal", check="subtotal_value >= 0"),
        Column("vat_percentage", "text", "Persentase PPN", note="apa adanya di dokumen"),
        Column("vat_value", "numeric", "Nilai PPN", check="vat_value >= 0"),
        Column("total_price", "numeric", "Total Penawaran", check="total_price >= 0",
               note="grand total"),
        Column("validity_text", "text", "Masa Berlaku", note="masa berlaku penawaran"),
        Column("payment_mechanism", "text", "Cara Pembayaran"),
        Column("currency", "char3", "Mata Uang", null=False, default="'IDR'"),
        *_AUDIT,
    ],
    domain="sph", owner="ai", label="SPH Vendor", display="sph_number",
    note="Surat penawaran harga dari vendor (rantai hulu) -- lahir dari kebutuhan kontrak.",
)

SPH_ITEM = Table(
    "sph_item",
    [
        Column("sph_id", "int", "ID SPH", null=False, fk="sph.id"),
        Column("line_no", "int", "No Urut", null=False, check="line_no > 0",
               note="urutan baca, bukan kolom 'No' di dokumen"),
        Column("category", "text", "Kelompok"),
        Column("description", "text", "Uraian", null=False),
        Column("specification", "text", "Spesifikasi"),
        Column("brand", "text", "Merek"),
        Column("part_number", "text", "Nomor Part"),
        Column("quantity", "numeric", "Volume", check="quantity >= 0"),
        Column("unit", "text", "Satuan"),
        Column("period", "text", "Periode"),
        Column("unit_price", "numeric", "Harga Satuan", check="unit_price >= 0",
               note="selalu dikonfirmasi PM (hlm. 20)"),
        Column("line_total", "numeric", "Jumlah Harga", check="line_total >= 0"),
        Column("remarks", "text", "Keterangan"),
        *_AUDIT,
    ],
    domain="sph", owner="ai", label="Rincian SPH", display="description",
    unique_together=(("sph_id", "line_no"),),
    note="Baris penawaran vendor. Relasi ke barang yang dibeli (procurement item) untuk tabel "
         "banding harga dirancang di Bulan 5 -- belum ada di sini.",
)

# =========================================================================== 4. BAST (DITUNDA)
_DITUNDA_BAST = ("DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer "
                 "(lampiran) di workshop skema. ")

BAST = Table(
    "bast",
    [
        Column("document_id", "int", "ID Dokumen", null=False, unique=True, fk="document.id"),
        Column("direction", "text", "Arah", null=False, enum=BAST_DIRECTIONS,
               note="customer = kita->pelanggan (acuan: kontrak); vendor = vendor->kita "
                    "(acuan: PO) -- hlm. 10"),
        Column("contract_id", "int", "ID Kontrak", fk="contract.id", fk_on_delete="RESTRICT",
               note="hanya untuk BAST pelanggan"),
        Column("mybhakti_po_ref", "text", "Rujukan PO MyBhakti", note="diisi n8n; bukan relasi"),
        Column("bast_number_customer", "text", "Nomor BAST Pelanggan"),
        Column("bast_number_internal", "text", "Nomor BAST Internal",
               note="dari numbering service milik RPA (hlm. 20)"),
        Column("handover_date_text", "text", "Tanggal Serah Terima Tertulis"),
        Column("handover_date", "date", "Tanggal Serah Terima"),
        Column("handover_city", "text", "Kota Serah Terima"),
        Column("work_title", "text", "Nama Pekerjaan"),
        Column("basis_doc_type", "text", "Jenis Dokumen Dasar", enum=BASIS_DOC_TYPES),
        Column("basis_doc_number", "text", "Nomor Dokumen Dasar"),
        Column("basis_doc_date_text", "text", "Tanggal Dokumen Dasar Tertulis"),
        Column("basis_doc_date", "date", "Tanggal Dokumen Dasar"),
        Column("basis_doc_value", "numeric", "Nilai Dokumen Dasar", check="basis_doc_value >= 0"),
        Column("basis_doc_value_vat", "text", "PPN Nilai Dasar", enum=VAT_MODES),
        Column("currency", "char3", "Mata Uang", null=False, default="'IDR'"),
        Column("acceptance_statement", "text", "Pernyataan Penerimaan"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", label="BAST", display="bast_number_customer", status="ditunda",
    note=_DITUNDA_BAST + "BAST hasil ekstraksi dokumen lama atau hasil susunan sistem.",
)

BAST_PARTY = Table(
    "bast_party",
    [
        Column("bast_id", "int", "ID BAST", null=False, fk="bast.id"),
        Column("role", "text", "Peran", null=False, enum=PARTY_ROLES,
               note="peran, BUKAN 'Pihak Pertama/Kedua' -- label itu terbalik antar-format"),
        Column("org_name_text", "text", "Nama Instansi", null=False),
        Column("signer_name", "text", "Nama Penandatangan", note="kosong bila tidak terbaca"),
        Column("signer_title", "text", "Jabatan Penandatangan"),
        Column("org_address_text", "text", "Alamat"),
        Column("mybhakti_party_ref", "text", "Rujukan Pihak MyBhakti"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", label="Pihak BAST", display="org_name_text", status="ditunda",
    unique_together=(("bast_id", "role"),),
    note=_DITUNDA_BAST + "Tepat 2 baris per BAST: penyerah dan penerima.",
)

BAST_ITEM = Table(
    "bast_item",
    [
        Column("bast_id", "int", "ID BAST", null=False, fk="bast.id"),
        Column("line_no", "int", "No Urut", null=False, check="line_no > 0"),
        Column("contract_item_id", "int", "ID Rincian Kontrak", fk="contract_item.id",
               fk_on_delete="RESTRICT",
               note="baris BoQ kontrak yang diserahkan; uraian & harga dibaca dari kontrak"),
        Column("description", "text", "Uraian", null=False),
        Column("quantity", "numeric", "Volume", check="quantity >= 0",
               note="volume yang DISERAHKAN -- bisa lebih kecil dari kontrak bila parsial"),
        Column("unit", "text", "Satuan"),
        Column("unit_price", "numeric", "Harga Satuan", check="unit_price >= 0"),
        Column("line_total", "numeric", "Jumlah Harga", check="line_total >= 0"),
        Column("test_result", "text", "Hasil Uji", note="diisi setelah uji, bukan sebelumnya"),
        Column("activation_date_text", "text", "Tanggal Aktif Tertulis"),
        Column("activation_date", "date", "Tanggal Aktif"),
        Column("service_order_ref", "text", "Nomor AO"),
        Column("service_id", "text", "SID"),
        Column("location", "text", "Lokasi"),
        Column("remarks", "text", "Keterangan"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", label="Rincian BAST", display="description", status="ditunda",
    unique_together=(("bast_id", "line_no"),),
    note=_DITUNDA_BAST + "Baris serah terima.",
)

BAST_CONDITION = Table(
    "bast_condition",
    [
        Column("bast_id", "int", "ID BAST", null=False, fk="bast.id"),
        Column("condition_type", "text", "Jenis Kondisi", null=False, enum=CONDITION_TYPES),
        Column("value_text", "text", "Nilai Teks"),
        Column("value_number", "numeric", "Nilai Angka"),
        Column("value_date", "date", "Nilai Tanggal"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", label="Kondisi BAST", display="condition_type", status="ditunda",
    note=_DITUNDA_BAST + "Fakta tambahan BAST sebagai baris, bukan kolom baru.",
)

BAST_DRAFT = Table(
    "bast_draft",
    [
        Column("contract_id", "int", "ID Kontrak", null=False, fk="contract.id"),
        Column("draft_bast_number", "text", "Nomor Draf"),
        Column("work_title", "text", "Nama Pekerjaan", null=False),
        Column("handover_date_text", "text", "Tanggal Serah Terima Tertulis"),
        Column("handover_date", "date", "Tanggal Serah Terima"),
        Column("handover_city", "text", "Kota Serah Terima"),
        Column("status", "text", "Status", null=False, enum=BAST_DRAFT_STATUSES),
        Column("template_name", "text", "Template"),
        Column("acceptance_statement", "text", "Pernyataan Penerimaan"),
        Column("generated_doc_url", "text", "Tautan Dokumen"),
        Column("generated_bast_id", "int", "ID BAST Tercetak", fk="bast.id",
               fk_on_delete="RESTRICT"),
        Column("approved_by", "text", "Disetujui Oleh", written_by="human"),
        Column("approved_at", "timestamptz", "Waktu Disetujui", written_by="human"),
        *_AUDIT,
    ],
    domain="bast", owner="rpa", label="Draf BAST", display="work_title", status="ditunda",
    note=_DITUNDA_BAST + "Belum punya kunci anti-dobel: wajib diputuskan sebelum berlaku, "
         "karena tanpa kunci, pengiriman ulang menghapus persetujuan PM.",
)

# =========================================================================== 5. EVIDENCE (DITUNDA)
EVIDENCE_PHOTO = Table(
    "evidence_photo",
    [
        Column("odk_instance_id", "text", "ID Kiriman ODK", null=False, unique=True,
               note="sinkron ulang = pembaruan, bukan baris kembar"),
        Column("contract_item_id", "int", "ID Rincian Kontrak", null=False,
               fk="contract_item.id", fk_on_delete="RESTRICT"),
        Column("requirement_id", "int", "ID Syarat Kontrak", fk="contract_requirement.id",
               fk_on_delete="RESTRICT"),
        Column("component_label", "text", "Komponen", note="mis. '4 Unit Switch'"),
        Column("photo_type", "text", "Jenis Foto", null=False, enum=PHOTO_TYPES),
        Column("serial_number", "text", "Nomor Seri"),
        Column("photo_url", "text", "Tautan Foto", null=False),
        Column("taken_at", "timestamptz", "Waktu Foto", null=False),
        Column("gps_lat", "coord", "Lintang"),
        Column("gps_lon", "coord", "Bujur"),
        Column("auto_check_notes", "text", "Catatan Cek Otomatis"),
        Column("review_status", "text", "Status Review", null=False,
               enum=EVIDENCE_REVIEW_STATUSES, default="'pending'", written_by="human"),
        Column("reviewed_by", "text", "Diperiksa Oleh", written_by="human"),
        Column("reviewed_at", "timestamptz", "Waktu Diperiksa", written_by="human"),
        Column("review_note", "text", "Catatan Review", written_by="human"),
        *_AUDIT,
    ],
    domain="evidence", owner="network", label="Foto Evidence", display="component_label",
    status="ditunda",
    note="DITUNDA: usulan untuk disepakati dengan Network Engineer (dol-odk & "
         "dol-bast-compiler, hlm. 15). Lampiran wajib kontrak sering berupa DOKUMEN (BA uji "
         "terima, surat jalan), bukan foto -- bentuk tabel bukti perlu dibahas bersama.",
)

# =========================================================================== 6. VERIFIKASI
EXTRACTED_FIELD = Table(
    "extracted_field",
    [
        Column("document_id", "int", "ID Dokumen", null=False, fk="document.id"),
        Column("field_path", "text", "Nama Field", null=False,
               note="mis. 'Nomor Kontrak Kerja' atau 'List Item/Barang[0].Harga Satuan'"),
        Column("ai_value_text", "text", "Nilai Terbaca Sistem"),
        Column("evidence_page", "int", "Halaman Bukti", note="dihitung sistem, bukan ditulis LLM"),
        Column("evidence_quote", "text", "Kutipan Bukti",
               note="potongan teks dokumen tempat nilai ditemukan"),
        Column("evidence_score", "numeric", "Skor Bukti",
               note="0-1: seberapa persis nilai ditemukan di teks dokumen"),
        Column("system_status", "text", "Status Bukti", null=False, enum=SYSTEM_STATUSES,
               note="saran sistem, BUKAN persetujuan. Yang diperiksa sistem hanya apakah nilai "
                    "ada di dokumen, bukan apakah perannya benar"),
        *_AUDIT,
    ],
    domain="verifikasi", owner="ai", label="Hasil Ekstraksi", display="field_path",
    unique_together=(("document_id", "field_path"),),
    note="Satu baris per field: nilai terbaca + bukti. Antrean kerja PM. Ditulis mesin saja; "
         "dokumen yang sudah mulai diperiksa PM tidak ditimpa otomatis.",
)

FIELD_REVIEW = Table(
    "field_review",
    [
        Column("document_id", "int", "ID Dokumen", null=False, fk="document.id",
               fk_on_delete="RESTRICT",
               note="dokumen dengan keputusan PM tidak boleh terhapus diam-diam"),
        Column("field_path", "text", "Nama Field", null=False),
        Column("reviewed_ai_value_text", "text", "Nilai Sistem Saat Diperiksa",
               note="nilai yang DILIHAT PM saat memutuskan; bila nilai sistem berubah, "
                    "keputusan lama tidak berlaku untuk nilai baru"),
        Column("decision", "text", "Keputusan", null=False, enum=REVIEW_DECISIONS),
        Column("final_value_text", "text", "Nilai Final", note="wajib diisi bila dikoreksi"),
        Column("reviewed_by", "text", "Diperiksa Oleh", null=False),
        Column("reviewed_at", "timestamptz", "Waktu Diperiksa", null=False),
        Column("reviewer_note", "text", "Catatan PM"),
        *_AUDIT,
    ],
    domain="verifikasi", owner="pm", label="Keputusan PM", display="field_path",
    written_by="human", unique_together=(("document_id", "field_path"),),
    note="Keputusan PM per field (hlm. 11 & 20). Pipeline tidak pernah menulis ke sini. "
         "Nilai yang boleh dipakai dokumen hilir hanya yang ada keputusannya di sini.",
)

# =========================================================================== 7. AUDIT
EXTRACTION_RUN = Table(
    "extraction_run",
    [
        Column("document_id", "int", "ID Dokumen", null=False, fk="document.id"),
        Column("ocr_engine", "text", "Mesin OCR"),
        Column("llm_model", "text", "Model LLM"),
        Column("prompt_version", "text", "Versi Prompt"),
        Column("schema_version", "text", "Versi Skema"),
        Column("llm_call_count", "int", "Jumlah Panggilan LLM"),
        Column("parse_seconds", "numeric", "Detik Pembacaan"),
        Column("extract_seconds", "numeric", "Detik Ekstraksi"),
        Column("validation_status", "text", "Status Validasi"),
        Column("started_at", "timestamptz", "Mulai"),
        *_AUDIT,
    ],
    domain="audit", owner="ai", label="Riwayat Pemrosesan", nocodb=False,
    note="Jejak tiap pemrosesan -- dasar bukti 'Terukur' (hlm. 21). Hanya di PostgreSQL.",
)

# Urutan alur bisnis. Urutan INSERT (induk dulu) dihitung terpisah oleh insert_order().
ALL_TABLES: List[Table] = [
    DOCUMENT,
    CONTRACT, CONTRACT_PARTY, CONTRACT_ITEM, CONTRACT_REQUIREMENT,
    SPH, SPH_ITEM,
    BAST, BAST_PARTY, BAST_ITEM, BAST_CONDITION, BAST_DRAFT,
    EVIDENCE_PHOTO,
    EXTRACTED_FIELD, FIELD_REVIEW,
    EXTRACTION_RUN,
]


def table(name: str) -> Table:
    t = next((t for t in ALL_TABLES if t.name == name), None)
    if t is None:
        raise KeyError(f"Tabel '{name}' tidak ada di model. Ada: {[t.name for t in ALL_TABLES]}")
    return t


def tables_with_status(status: str) -> List[Table]:
    return [t for t in ALL_TABLES if t.status == status]


def insert_order() -> List[str]:
    """Urutan aman untuk insert: induk sebelum anak (topological sort atas FK)."""
    done, order = set(), []
    remaining = list(ALL_TABLES)
    while remaining:
        maju = False
        for t in list(remaining):
            deps = {c.fk.split(".")[0] for c in t.columns if c.fk} - {t.name}
            if deps <= done:
                order.append(t.name)
                done.add(t.name)
                remaining.remove(t)
                maju = True
        if not maju:
            raise ValueError(f"Siklus FK terdeteksi pada: {[t.name for t in remaining]}")
    return order


def natural_key(t: Table) -> Optional[Tuple[str, ...]]:
    """Kunci upsert: UNIQUE gabungan, atau satu kolom UNIQUE. None = tabel tanpa kunci alami."""
    if t.unique_together:
        return tuple(t.unique_together[0])
    uniq = [c.name for c in t.columns if c.unique]
    return (uniq[0],) if uniq else None


def parent_refs(t: Table) -> List[dict]:
    """
    Cara mengisi kolom FK saat mengirim payload: baris anak membawa `_<induk>_ref` (nilai kunci
    induk), lalu pengirim menukarnya dengan Id baris induk yang baru dibuat.
    """
    return [
        {"column": c.name, "references": c.fk, "placeholder": f"_{c.fk.split('.')[0]}_ref",
         "required": not c.null, "on_delete": c.fk_on_delete}
        for c in t.columns if c.fk
    ]
