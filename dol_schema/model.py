"""
dol-schema — definisi model data companion Delivery Ops Layer (SATU sumber kebenaran).

Semua yang lain dibangkitkan dari file ini: DDL PostgreSQL, schema.json untuk n8n & compiler
BAST, spesifikasi kolom NocoDB, diagram DBML, dan kamus data. Nama kolom hanya ditulis di sini.

Urutan file mengikuti alur bisnis (briefing hlm. 3):

    1. DOKUMEN       berkas yang masuk
    2. KONTRAK       Kontrak/SPK pelanggan = sumber semua BoQ           (AI Engineer)
    3. SPH VENDOR    penawaran vendor yang lahir dari kebutuhan kontrak  (AI Engineer)
    4. BAST          serah terima; nomor & render oleh RPA              (AI + RPA)
    5. EVIDENCE      foto lapangan dari ODK Central                     (Network Engineer)
    6. VERIFIKASI    nilai ekstraksi + skor, dan keputusan PM per field (AI + PM)
    7. AUDIT         jejak teknis pemrosesan, hanya di PostgreSQL

Prinsip yang ditegakkan struktur, bukan kedisiplinan:

- **Satu penulis per kolom.** Kolom milik manusia ditandai `written_by="human"` (per kolom)
  atau seluruh tabel (`Table.written_by`). Validator menolak payload mesin yang mengisinya,
  jadi sinkron ulang dari pipeline/n8n tidak mungkin menimpa keputusan PM.
- **Mentah vs terparse.** Nilai apa adanya di dokumen di kolom `*_text`; hasil parse di kolom
  tanpa akhiran dan boleh NULL.
- **Menunjuk, bukan menyalin.** BAST dan evidence menunjuk baris BoQ kontrak lewat FK, jadi
  rincian BAST tidak mungkin berbeda dari kontrak.
- **Batas kepemilikan data (hlm. 7).** Klien, vendor, proyek, PO milik MyBhakti: di sini hanya
  kolom rujukan `mybhakti_*_ref` yang diisi n8n — sengaja BUKAN foreign key.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

SCHEMA_VERSION = "companion-2026.10.1"

# Pemilik tabel menurut briefing hlm. 12-15. Yang merancang & memelihara isi tabelnya.
OWNERS = {
    "ai": "AI Engineer",
    "network": "Network Engineer",
    "rpa": "RPA Engineer",
    "pm": "PM",
}
DOMAINS = ("dokumen", "kontrak", "sph", "bast", "evidence", "verifikasi", "audit")


@dataclass(frozen=True)
class Column:
    name: str
    type: str                      # text | int | numeric | coord | date | timestamptz | char3
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
    unique_together: tuple = ()    # ((kolom, kolom), ...)
    note: str = ""
    written_by: str = "machine"    # machine | human
    nocodb: bool = True            # False = hanya PostgreSQL, tidak pernah dikirim ke NocoDB
    display: Optional[str] = None  # kolom yang dipakai NocoDB sebagai judul baris

    def column(self, name: str) -> Optional[Column]:
        return next((c for c in self.columns if c.name == name), None)

    def human_columns(self) -> List[str]:
        """Kolom yang hanya boleh ditulis manusia (seluruh kolom bila tabelnya milik manusia)."""
        if self.written_by == "human":
            return [c.name for c in self.columns if c.name not in AUDIT_COLUMNS]
        return [c.name for c in self.columns if c.written_by == "human"]


# Kolom audit yang dimiliki semua tabel. Waktu selalu UTC.
AUDIT_COLUMNS = ("created_at", "updated_at")
_AUDIT = [
    Column("created_at", "timestamptz", null=False, note="UTC"),
    Column("updated_at", "timestamptz", null=False, note="UTC, diperbarui trigger"),
]

# --------------------------------------------------------------------------- pilihan nilai
DOC_TYPES = ("contract", "sph", "bast")
CONTRACT_TYPES = ("nota_pesanan", "surat_pesanan", "spk", "kontrak_kerja_sama", "pks", "other")
CONTRACT_PARTY_ROLES = ("first_party", "second_party", "client", "contractor")
REQUIREMENT_TYPES = ("mandatory_attachment", "handover_condition", "partial_delivery")
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
SYSTEM_STATUSES = ("auto_verified", "auto_accepted", "review_required", "unsupported",
                   "conflict", "missing")
REVIEW_DECISIONS = ("confirmed", "corrected", "rejected")


# =========================================================================== 1. DOKUMEN
DOCUMENT = Table(
    "document",
    [
        Column("content_hash", "text", null=False, unique=True,
               note="sha1 isi berkas -- kunci idempotensi; proses ulang = UPDATE"),
        Column("doc_type", "text", null=False, enum=DOC_TYPES),
        Column("source_filename", "text", null=False),
        Column("page_count", "int", check="page_count > 0"),
        Column("markdown", "text", note="markdown utuh; PM membaca tanpa membuka PDF"),
        Column("validation_notes", "text",
               note="[2026.10.1] peringatan tingkat dokumen untuk PM, mis. salinan ganda "
                    "atau jumlah item tidak sama dengan total"),
        *_AUDIT,
    ],
    domain="dokumen", owner="ai", display="source_filename",
    note="Supertipe: setiap berkas yang masuk, apa pun jenisnya.",
)

# =========================================================================== 2. KONTRAK
CONTRACT = Table(
    "contract",
    [
        Column("document_id", "int", null=False, unique=True, fk="document.id",
               note="UNIQUE -> 1:1 dengan document"),
        Column("mybhakti_project_ref", "text",
               note="[2026.10.1] proyek/deal di MyBhakti, diisi n8n -- kunci pengikat semua "
                    "dokumen satu proyek; SENGAJA bukan FK (hlm. 7)"),
        Column("contract_type", "text", enum=CONTRACT_TYPES,
               note="[2026.10.1] bentuk dokumen dasar: nota pesanan, surat pesanan, SPK, "
                    "kontrak kerja sama, PKS"),
        Column("contract_number", "text", note="nomor kontrak resmi / SPK / PKS"),
        Column("contract_number_internal", "text", note="nomor registrasi internal BUT"),
        Column("work_title", "text", null=False, note="judul pengadaan / lingkup pekerjaan"),
        Column("contract_date_text", "text"),
        Column("contract_date", "date"),
        Column("start_date_text", "text"),
        Column("start_date", "date"),
        Column("end_date_text", "text"),
        Column("end_date", "date"),
        Column("duration_text", "text"),
        Column("contract_value", "numeric", check="contract_value >= 0"),
        Column("subtotal_value", "numeric", check="subtotal_value >= 0"),
        Column("vat_value", "numeric", check="vat_value >= 0"),
        Column("vat_percentage", "text"),
        Column("currency", "char3", null=False, default="'IDR'", note="default IDR"),
        Column("payment_mechanism", "text"),
        Column("penalty_terms", "text"),
        Column("bast_terms", "text"),
        Column("bank_name", "text"),
        Column("bank_account_number", "text"),
        Column("bank_account_name", "text"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", display="contract_number",
    note="Kontrak/SPK pelanggan dalam bentuk apa pun -- dibaca sekali, dipakai sepanjang "
         "proyek (hlm. 11). Sumber utama penyusunan draf BAST.",
)

CONTRACT_PARTY = Table(
    "contract_party",
    [
        Column("contract_id", "int", null=False, fk="contract.id"),
        Column("role", "text", null=False, enum=CONTRACT_PARTY_ROLES,
               note="first_party/client (pemberi kerja) vs second_party/contractor (pelaksana)"),
        Column("org_name_text", "text", null=False),
        Column("signer_name", "text", null=False),
        Column("signer_title", "text"),
        Column("org_address_text", "text"),
        Column("npwp", "text"),
        Column("mybhakti_party_ref", "text"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", display="org_name_text",
    unique_together=(("contract_id", "role"),),
    note="Pihak penandatangan kontrak -- CUPLIKAN seperti tertulis, bukan data master. Satu "
         "orang muncul di banyak baris karena menandatangani banyak dokumen.",
)

CONTRACT_ITEM = Table(
    "contract_item",
    [
        Column("contract_id", "int", null=False, fk="contract.id"),
        Column("line_no", "int", null=False, check="line_no > 0"),
        Column("category", "text"),
        Column("description", "text", null=False),
        Column("specification", "text"),
        Column("quantity", "numeric", check="quantity >= 0"),
        Column("unit", "text"),
        Column("period", "text"),
        Column("unit_price", "numeric", check="unit_price >= 0",
               note="selalu diverifikasi PM (hlm. 20)"),
        Column("line_total", "numeric", check="line_total >= 0"),
        Column("remarks", "text"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", display="description",
    unique_together=(("contract_id", "line_no"),),
    note="BoQ kontrak = kewajiban ke pelanggan (hlm. 7). SUMBER TUNGGAL rincian pekerjaan: "
         "SPH vendor, BAST, dan evidence menunjuk ke sini, tidak menyalin.",
)

CONTRACT_REQUIREMENT = Table(
    "contract_requirement",
    [
        Column("contract_id", "int", null=False, fk="contract.id"),
        Column("line_no", "int", null=False, check="line_no > 0"),
        Column("requirement_type", "text", null=False, enum=REQUIREMENT_TYPES,
               note="lampiran wajib / syarat serah terima / boleh parsial"),
        Column("requirement_text", "text", null=False,
               note="mis. 'Berita Acara Uji Terima'"),
        Column("clause_ref", "text", note="pasal rujukan, mis. 'Pasal 9 ayat 2'"),
        Column("evidence_quote", "text",
               note="kutipan pendek agar PM tidak perlu membaca ulang kontrak (hlm. 11)"),
        *_AUDIT,
    ],
    domain="kontrak", owner="ai", display="requirement_text",
    unique_together=(("contract_id", "line_no"),),
    note="[2026.10.1] Aturan dari kontrak, bukan angka: lampiran wajib, syarat serah terima, "
         "boleh parsial (hlm. 11). Baris lampiran wajib adalah separuh CHECKLIST GABUNGAN; "
         "separuh lainnya evidence teknis milik Network Engineer (hlm. 15).",
)

# =========================================================================== 3. SPH VENDOR
SPH = Table(
    "sph",
    [
        Column("document_id", "int", null=False, unique=True, fk="document.id"),
        Column("mybhakti_project_ref", "text",
               note="[2026.10.1] proyek yang pengadaannya ditawar; diisi n8n"),
        Column("mybhakti_vendor_ref", "text",
               note="[2026.10.1] vendor penerbit di MyBhakti; diisi n8n"),
        Column("sph_number", "text"),
        Column("sph_date_text", "text"),
        Column("sph_date", "date"),
        Column("project_name", "text", note="perihal / nama pekerjaan yang ditawarkan"),
        Column("client_name", "text", note="instansi yang dituju surat"),
        Column("vendor_name", "text", note="penerbit SPH seperti tertulis"),
        Column("vendor_npwp", "text"),
        Column("subtotal_value", "numeric", check="subtotal_value >= 0"),
        Column("vat_percentage", "text", note="apa adanya di dokumen; sering berupa frasa"),
        Column("vat_value", "numeric", check="vat_value >= 0"),
        Column("total_price", "numeric", check="total_price >= 0", note="grand total"),
        Column("validity_text", "text", note="masa berlaku penawaran, mis. '30 hari'"),
        Column("payment_mechanism", "text"),
        Column("currency", "char3", null=False, default="'IDR'", note="default IDR"),
        *_AUDIT,
    ],
    domain="sph", owner="ai", display="sph_number",
    note="SPH vendor (rantai hulu) -- lahir DARI kebutuhan kontrak, bukan dasar kontrak.",
)

SPH_ITEM = Table(
    "sph_item",
    [
        Column("sph_id", "int", null=False, fk="sph.id"),
        Column("line_no", "int", null=False, check="line_no > 0"),
        Column("contract_item_id", "int", fk="contract_item.id", fk_on_delete="RESTRICT",
               note="[2026.10.1] item kontrak yang dipenuhi baris ini -- kunci price matching "
                    "& tabel banding antar-vendor (Bulan 5)"),
        Column("category", "text"),
        Column("description", "text", null=False),
        Column("specification", "text"),
        Column("brand", "text"),
        Column("part_number", "text"),
        Column("quantity", "numeric", check="quantity >= 0"),
        Column("unit", "text"),
        Column("period", "text"),
        Column("unit_price", "numeric", check="unit_price >= 0"),
        Column("line_total", "numeric", check="line_total >= 0"),
        Column("remarks", "text"),
        *_AUDIT,
    ],
    domain="sph", owner="ai", display="description",
    unique_together=(("sph_id", "line_no"),),
    note="Baris penawaran vendor. Beberapa vendor menawar item kontrak yang sama -> "
         "dibandingkan lewat contract_item_id.",
)

# =========================================================================== 4. BAST
BAST = Table(
    "bast",
    [
        Column("document_id", "int", null=False, unique=True, fk="document.id",
               note="UNIQUE -> 1:1 dengan document"),
        Column("direction", "text", null=False, enum=BAST_DIRECTIONS,
               note="customer = kita->pelanggan (acuan: kontrak); vendor = vendor->kita "
                    "(acuan: PO) -- hlm. 10"),
        Column("contract_id", "int", fk="contract.id", fk_on_delete="RESTRICT",
               note="hanya untuk direction=customer"),
        Column("mybhakti_po_ref", "text",
               note="rujukan opak ke MyBhakti, diisi n8n -- SENGAJA bukan FK (hlm. 7)"),
        Column("bast_number_customer", "text", note="nomor versi pelanggan"),
        Column("bast_number_internal", "text",
               note="nomor versi BUT -- dari numbering service milik RPA (hlm. 20)"),
        Column("handover_date_text", "text", note="apa adanya di dokumen"),
        Column("handover_date", "date", note="hasil parse; NULL kalau gagal"),
        Column("handover_city", "text"),
        Column("work_title", "text", null=False),
        Column("basis_doc_type", "text", enum=BASIS_DOC_TYPES),
        Column("basis_doc_number", "text", note="seperti tercetak"),
        Column("basis_doc_date_text", "text"),
        Column("basis_doc_date", "date"),
        Column("basis_doc_value", "numeric", check="basis_doc_value >= 0"),
        Column("basis_doc_value_vat", "text", enum=VAT_MODES),
        Column("currency", "char3", null=False, default="'IDR'", note="default IDR"),
        Column("acceptance_statement", "text"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", display="bast_number_customer",
    note="BAST (hasil ekstraksi atau hasil generate). Pihak & nilai BAST pelanggan dibaca dari "
         "kontrak lewat contract_id. Kolom di sini hanya butir yang selalu/hampir selalu ada.",
)

BAST_PARTY = Table(
    "bast_party",
    [
        Column("bast_id", "int", null=False, fk="bast.id"),
        Column("role", "text", null=False, enum=PARTY_ROLES,
               note="peran, BUKAN 'Pihak Pertama/Kedua' -- label itu terbalik antar-format"),
        Column("org_name_text", "text", null=False, note="nama seperti ditandatangani"),
        Column("signer_name", "text", null=False),
        Column("signer_title", "text"),
        Column("org_address_text", "text"),
        Column("mybhakti_party_ref", "text", note="opak, diisi n8n"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", display="org_name_text",
    unique_together=(("bast_id", "role"),),
    note="Tepat 2 baris per BAST. Cuplikan saat penandatanganan -- jabatan berubah, "
         "dokumen yang sudah diteken tidak boleh ikut berubah.",
)

BAST_ITEM = Table(
    "bast_item",
    [
        Column("bast_id", "int", null=False, fk="bast.id"),
        Column("line_no", "int", null=False, check="line_no > 0"),
        Column("contract_item_id", "int", fk="contract_item.id", fk_on_delete="RESTRICT",
               note="[2026.10.1] baris BoQ kontrak yang diserahkan -- bila terisi, uraian & "
                    "harga DIBACA dari contract_item, sehingga pasti sama dengan kontrak"),
        Column("description", "text", null=False),
        Column("quantity", "numeric", check="quantity >= 0"),
        Column("unit", "text"),
        Column("unit_price", "numeric", check="unit_price >= 0"),
        Column("line_total", "numeric", check="line_total >= 0"),
        Column("test_result", "text"),
        Column("activation_date_text", "text", note="[2026.10.1] 'Tanggal Aktif' apa adanya"),
        Column("activation_date", "date", note="[2026.10.1] hasil parse"),
        Column("service_order_ref", "text", note="[2026.10.1] 'No. AO' layanan"),
        Column("service_id", "text", note="[2026.10.1] 'SID' layanan"),
        Column("location", "text", note="[2026.10.1] lokasi pemasangan / layanan"),
        Column("remarks", "text"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", display="description",
    unique_together=(("bast_id", "line_no"),),
    note="Baris serah terima. Kolom [2026.10.1] adalah informasi yang baru ada di tahap serah "
         "terima (tanggal aktif, AO/SID, lokasi). Harga boleh NULL: format kampus/vendor/instansi "
         "tidak memuatnya.",
)

BAST_CONDITION = Table(
    "bast_condition",
    [
        Column("bast_id", "int", null=False, fk="bast.id"),
        Column("condition_type", "text", null=False, enum=CONDITION_TYPES),
        Column("value_text", "text"),
        Column("value_number", "numeric"),
        Column("value_date", "date"),
        *_AUDIT,
    ],
    domain="bast", owner="ai", display="condition_type",
    note="Fakta tambahan BAST sebagai BARIS. Fakta baru = nilai condition_type baru, bukan kolom baru.",
)

BAST_DRAFT = Table(
    "bast_draft",
    [
        Column("contract_id", "int", null=False, fk="contract.id"),
        Column("draft_bast_number", "text"),
        Column("work_title", "text", null=False),
        Column("handover_date_text", "text"),
        Column("handover_date", "date"),
        Column("handover_city", "text"),
        Column("status", "text", null=False, enum=BAST_DRAFT_STATUSES),
        Column("template_name", "text", note="format_telkom | format_kampus | format_instansi"),
        Column("acceptance_statement", "text"),
        Column("generated_doc_url", "text"),
        Column("generated_bast_id", "int", fk="bast.id", fk_on_delete="RESTRICT",
               note="terisi saat status=generated; tanpa ini, kontrak yang di-generate "
                    "ulang membuat PM tidak tahu draf mana menghasilkan BAST yang mana"),
        Column("approved_by", "text", written_by="human", note="HANYA diisi manusia (PM)"),
        Column("approved_at", "timestamptz", written_by="human", note="HANYA diisi manusia (PM)"),
        *_AUDIT,
    ],
    domain="bast", owner="rpa", display="work_title",
    note="Draf BAST pelanggan dari kontrak terverifikasi. Nomor dari numbering service, render "
         "oleh dol-render (RPA), lampiran oleh compiler BAST (Network).",
)

# =========================================================================== 5. EVIDENCE
EVIDENCE_PHOTO = Table(
    "evidence_photo",
    [
        Column("odk_instance_id", "text", null=False, unique=True,
               note="ID submission ODK Central -- sinkron ulang = update, bukan baris kembar"),
        Column("contract_item_id", "int", null=False, fk="contract_item.id",
               fk_on_delete="RESTRICT", note="baris BoQ kontrak yang dibuktikan foto ini"),
        Column("requirement_id", "int", fk="contract_requirement.id", fk_on_delete="RESTRICT",
               note="lampiran wajib kontrak yang dipenuhi (bila ada) -- sambungan checklist gabungan"),
        Column("component_label", "text", note="mis. '4 Unit Switch', '1 Unit Router'"),
        Column("photo_type", "text", null=False, enum=PHOTO_TYPES,
               note="foto barang / label serial number / pemasangan / tangkapan layar"),
        Column("serial_number", "text",
               note="wajib untuk foto label SN; bahan registry aset & garansi (Bulan 6)"),
        Column("photo_url", "text", null=False),
        Column("taken_at", "timestamptz", null=False, note="waktu pengambilan foto"),
        Column("gps_lat", "coord", note="lintang, mis. -7.347824"),
        Column("gps_lon", "coord", note="bujur, mis. 108.232318"),
        Column("auto_check_notes", "text",
               note="catatan pemeriksaan otomatis n8n, mis. 'jarak 120 m dari lokasi proyek'"),
        Column("review_status", "text", null=False, enum=EVIDENCE_REVIEW_STATUSES,
               default="'pending'", written_by="human",
               note="pending = belum dicek. HANYA PM yang mengubah"),
        Column("reviewed_by", "text", written_by="human", note="HANYA diisi PM"),
        Column("reviewed_at", "timestamptz", written_by="human", note="HANYA diisi PM"),
        Column("review_note", "text", written_by="human",
               note="alasan bila ditolak, mis. 'SN tidak terbaca'"),
        *_AUDIT,
    ],
    domain="evidence", owner="network", display="component_label",
    note="[2026.10.1] USULAN untuk disepakati dengan Network Engineer (wilayah dol-odk & "
         "dol-bast-compiler, hlm. 15). Foto masuk lewat n8n dari ODK Central SETELAH lolos "
         "pemeriksaan otomatis (GPS ada, dalam radius lokasi, dalam masa kontrak); PM lalu "
         "menyetujui/menolak di NocoDB. Lampiran BAST hanya memakai review_status=approved.",
)

# =========================================================================== 6. VERIFIKASI
EXTRACTED_FIELD = Table(
    "extracted_field",
    [
        Column("document_id", "int", null=False, fk="document.id"),
        Column("field_path", "text", null=False, note="mis. contract.Nomor Kontrak Kerja"),
        Column("ai_value_text", "text"),
        Column("evidence_page", "int", note="dihitung deterministik, BUKAN ditulis LLM"),
        Column("evidence_quote", "text", note="potongan teks dokumen yang cocok"),
        Column("evidence_score", "numeric",
               note="0-1: seberapa persis nilai ditemukan di teks dokumen"),
        Column("system_status", "text", null=False, enum=SYSTEM_STATUSES,
               note="saran sistem, BUKAN persetujuan"),
        *_AUDIT,
    ],
    domain="verifikasi", owner="ai", display="field_path",
    unique_together=(("document_id", "field_path"),),
    note="Satu baris per field: nilai ekstraksi + skor + bukti. Antrean kerja PM. Ditulis mesin "
         "saja; nilai terbaru per field.",
)

FIELD_REVIEW = Table(
    "field_review",
    [
        Column("document_id", "int", null=False, fk="document.id", fk_on_delete="RESTRICT",
               note="RESTRICT: dokumen dengan keputusan PM tidak boleh terhapus diam-diam"),
        Column("field_path", "text", null=False),
        Column("reviewed_ai_value_text", "text",
               note="nilai AI yang DILIHAT PM saat memutuskan; kalau nilai AI berubah, "
                    "konfirmasi lama tidak berlaku untuk nilai baru"),
        Column("decision", "text", null=False, enum=REVIEW_DECISIONS),
        Column("final_value_text", "text"),
        Column("reviewed_by", "text", null=False),
        Column("reviewed_at", "timestamptz", null=False),
        Column("reviewer_note", "text"),
        *_AUDIT,
    ],
    domain="verifikasi", owner="pm", display="field_path", written_by="human",
    unique_together=(("document_id", "field_path"),),
    note="Keputusan PM per field (hlm. 11 & 20). Pipeline tidak pernah menulis ke sini.",
)

# =========================================================================== 7. AUDIT
EXTRACTION_RUN = Table(
    "extraction_run",
    [
        Column("document_id", "int", null=False, fk="document.id"),
        Column("ocr_engine", "text"),
        Column("llm_model", "text"),
        Column("prompt_version", "text"),
        Column("schema_version", "text"),
        Column("llm_call_count", "int"),
        Column("parse_seconds", "numeric"),
        Column("extract_seconds", "numeric"),
        Column("validation_status", "text"),
        Column("started_at", "timestamptz"),
        *_AUDIT,
    ],
    domain="audit", owner="ai", nocodb=False,
    note="Jejak tiap pemrosesan -- dasar bukti 'Terukur' (hlm. 21). Hanya di PostgreSQL: "
         "NocoDB hanya memuat nilai ekstraksi + confidence, bukan metadata teknis AI.",
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
