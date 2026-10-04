"""
Pembangkit DDL PostgreSQL dari dol_schema/model.py.

Dua berkas, sesuai status tabel:

- `generate_ddl()`         -> tabel yang BERLAKU + view-nya          (generated/schema.sql)
- `generate_ddl_usulan()`  -> tabel yang DITUNDA + view-nya, untuk dibahas di workshop
                              (generated/schema_usulan.sql). Dijalankan SETELAH schema.sql.

Kenapa DDL di PostgreSQL, bukan hanya membuat tabel lewat UI NocoDB: tabel yang dibuat lewat
API NocoDB tidak punya UNIQUE, CHECK, foreign key, maupun view. Integritas di bawah ini hanya
berlaku bila PostgreSQL ini yang dipakai (NocoDB sebagai tampilan di atasnya).
"""

from __future__ import annotations

from dol_schema.model import (
    ALL_TABLES,
    OWNERS,
    SCHEMA_VERSION,
    Table,
    insert_order,
    tables_with_status,
)

_PG_TYPE = {
    "text": "text",
    "int": "integer",
    "numeric": "numeric(18,2)",
    "coord": "numeric(9,6)",  # GPS: 6 desimal ~ 11 cm; numeric(18,2) akan memotongnya
    "date": "date",
    "timestamptz": "timestamptz",
    "char3": "char(3)",
}

_UPDATED_AT_FN = """-- Menjaga updated_at tetap benar tanpa bergantung pada aplikasi yang menulis.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;"""


def _sql_str(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _column_sql(t: Table, c) -> str:
    parts = [f"    {c.name:26} {_PG_TYPE[c.type]}"]
    if c.name in ("created_at", "updated_at"):
        parts.append("NOT NULL DEFAULT now()")
    else:
        if not c.null:
            parts.append("NOT NULL")
        if c.default:
            parts.append(f"DEFAULT {c.default}")
    if c.unique:
        parts.append("UNIQUE")
    if c.fk:
        ref_table, ref_col = c.fk.split(".")
        parts.append(f"REFERENCES {ref_table}({ref_col}) ON DELETE {c.fk_on_delete}")
    return " ".join(parts)


def _table_sql(t: Table) -> str:
    lines: list[str] = [f"-- {t.label}"]
    if t.note:
        for ln in t.note.split(". "):
            if ln.strip():
                lines.append(f"-- {ln.strip().rstrip('.')}.")
    lines.append(
        f"-- Ditulis oleh: {'MANUSIA (PM)' if t.written_by == 'human' else 'mesin (pipeline)'}"
        f" · pemilik: {OWNERS[t.owner]}"
    )
    if t.human_columns() and t.written_by != "human":
        lines.append(f"-- Kolom yang HANYA diisi PM: {', '.join(t.human_columns())}")
    lines.append(f"CREATE TABLE IF NOT EXISTS {t.name} (")

    body = ["    id                         bigserial PRIMARY KEY"]
    for c in t.columns:
        body.append(_column_sql(t, c))
    for cols in t.unique_together:
        body.append(f"    UNIQUE ({', '.join(cols)})")
    for c in t.columns:
        if c.enum:
            allowed = ", ".join(f"'{v}'" for v in c.enum)
            body.append(f"    CONSTRAINT {t.name}_{c.name}_valid CHECK ({c.name} IN ({allowed}))")
        if c.check:
            body.append(f"    CONSTRAINT {t.name}_{c.name}_check CHECK ({c.check})")
    lines.append(",\n".join(body))
    lines.append(");")

    # Index untuk kolom FK: NocoDB & n8n sering memfilter baris anak berdasarkan induknya.
    for c in t.columns:
        if c.fk and not c.unique:
            lines.append(f"CREATE INDEX IF NOT EXISTS idx_{t.name}_{c.name} ON {t.name}({c.name});")
    lines.append(
        f"DROP TRIGGER IF EXISTS trg_{t.name}_updated_at ON {t.name};\n"
        f"CREATE TRIGGER trg_{t.name}_updated_at BEFORE UPDATE ON {t.name}\n"
        f"    FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )
    # Label Indonesia ikut tersimpan di database: alat apa pun yang membaca katalog
    # PostgreSQL (NocoDB sebagai sumber eksternal, DBeaver) melihat nama yang sama.
    lines.append(f"COMMENT ON TABLE {t.name} IS {_sql_str(t.label + ' -- ' + t.note)};")
    for c in t.columns:
        teks = f"{c.label} -- {c.note}" if c.note else c.label
        lines.append(f"COMMENT ON COLUMN {t.name}.{c.name} IS {_sql_str(teks)};")
    return "\n".join(lines)


_VIEWS_BERLAKU = """-- ---------------------------------------------------------------- verifikasi PM
-- Status verifikasi TIDAK disimpan sebagai kolom: ia turunan dari field_review.
-- Menyimpannya berarti ada dua sumber kebenaran yang bisa berbeda.

-- Keputusan PM yang basi: nilai sistem berubah setelah PM memutuskan.
CREATE OR REPLACE VIEW field_review_stale AS
SELECT fr.document_id, fr.field_path,
       fr.reviewed_ai_value_text AS value_saat_dikonfirmasi,
       ef.ai_value_text          AS value_sekarang,
       fr.reviewed_by, fr.reviewed_at
FROM field_review fr
JOIN extracted_field ef
  ON ef.document_id = fr.document_id AND ef.field_path = fr.field_path
WHERE ef.ai_value_text IS DISTINCT FROM fr.reviewed_ai_value_text;

-- Status per dokumen. Keputusan yang basi TIDAK dihitung: dokumen yang nilainya berubah
-- setelah dikonfirmasi kembali menjadi 'sedang_direview', bukan tetap 'terverifikasi_pm'.
CREATE OR REPLACE VIEW document_review_status AS
SELECT
    d.id                                            AS document_id,
    d.source_filename,
    d.doc_type,
    count(ef.id)                                    AS field_count,
    count(fr.id) FILTER (WHERE fr.decision = 'benar'
                         AND ef.ai_value_text IS NOT DISTINCT FROM fr.reviewed_ai_value_text)
                                                    AS confirmed_count,
    count(fr.id) FILTER (WHERE fr.decision = 'dikoreksi'
                         AND ef.ai_value_text IS NOT DISTINCT FROM fr.reviewed_ai_value_text)
                                                    AS corrected_count,
    count(fr.id) FILTER (WHERE ef.ai_value_text IS DISTINCT FROM fr.reviewed_ai_value_text)
                                                    AS stale_count,
    CASE
        WHEN count(ef.id) = 0 THEN 'belum_ada_field'
        WHEN count(fr.id) = 0 THEN 'draf_sistem'
        WHEN count(fr.id) FILTER (WHERE ef.ai_value_text IS NOT DISTINCT FROM
                                        fr.reviewed_ai_value_text) < count(ef.id)
             THEN 'sedang_direview'
        ELSE 'terverifikasi_pm'
    END                                             AS review_status
FROM document d
LEFT JOIN extracted_field ef ON ef.document_id = d.id
LEFT JOIN field_review   fr ON fr.document_id = d.id AND fr.field_path = ef.field_path
GROUP BY d.id, d.source_filename, d.doc_type;

-- Satu-satunya sumber nilai untuk dokumen hilir (mis. penyusunan BAST): hanya field yang
-- sudah diputuskan PM dan keputusannya belum basi. Field yang ditolak atau belum diperiksa
-- TIDAK muncul -- konsumen harus menganggapnya kosong, bukan memakai nilai sistem.
CREATE OR REPLACE VIEW nilai_terverifikasi AS
SELECT fr.document_id, fr.field_path,
       CASE fr.decision WHEN 'dikoreksi' THEN fr.final_value_text
                        ELSE ef.ai_value_text END AS nilai,
       fr.decision, fr.reviewed_by, fr.reviewed_at
FROM field_review fr
JOIN extracted_field ef
  ON ef.document_id = fr.document_id AND ef.field_path = fr.field_path
WHERE fr.decision IN ('benar', 'dikoreksi')
  AND ef.ai_value_text IS NOT DISTINCT FROM fr.reviewed_ai_value_text;"""  # noqa: E501 (SQL apa adanya)


_VIEWS_USULAN = """-- ---------------------------------------------------------------- penyusunan BAST (usulan)
-- Rincian BAST: uraian, spesifikasi, harga DARI KONTRAK bila baris BAST menunjuk
-- contract_item. Volume diambil dari BAST lebih dulu: serah terima parsial menyerahkan
-- volume yang lebih kecil dari kontrak.
CREATE OR REPLACE VIEW bast_rincian AS
SELECT bi.bast_id, b.contract_id, bi.line_no,
       COALESCE(ci.description, bi.description) AS description,
       ci.specification,
       COALESCE(bi.quantity, ci.quantity)       AS quantity,
       COALESCE(ci.unit, bi.unit)               AS unit,
       COALESCE(ci.unit_price, bi.unit_price)   AS unit_price,
       bi.activation_date, bi.service_order_ref, bi.service_id, bi.location, bi.test_result
FROM bast_item bi
JOIN bast b                ON b.id = bi.bast_id
LEFT JOIN contract_item ci ON ci.id = bi.contract_item_id;

-- Lampiran evidence: HANYA foto yang sudah disetujui PM, dikelompokkan per baris BoQ.
CREATE OR REPLACE VIEW evidence_siap_lampiran AS
SELECT ci.contract_id, ci.line_no, ci.description AS item_description,
       ep.component_label, ep.photo_type, ep.serial_number,
       ep.photo_url, ep.taken_at, ep.gps_lat, ep.gps_lon
FROM evidence_photo ep
JOIN contract_item ci ON ci.id = ep.contract_item_id
WHERE ep.review_status = 'approved';

-- Checklist gabungan (hlm. 15): tiap lampiran wajib kontrak + status buktinya.
CREATE OR REPLACE VIEW checklist_gabungan AS
SELECT cr.contract_id, cr.line_no, cr.requirement_text, cr.clause_ref,
       count(ep.id) FILTER (WHERE ep.review_status = 'approved') AS bukti_disetujui,
       count(ep.id) FILTER (WHERE ep.review_status = 'pending')  AS bukti_menunggu,
       CASE WHEN count(ep.id) FILTER (WHERE ep.review_status = 'approved') > 0
            THEN 'terpenuhi' ELSE 'belum' END                     AS status
FROM contract_requirement cr
LEFT JOIN evidence_photo ep ON ep.requirement_id = cr.id
WHERE cr.requirement_type = 'lampiran_wajib'
GROUP BY cr.contract_id, cr.line_no, cr.requirement_text, cr.clause_ref;"""  # noqa: E501 (SQL apa adanya)


def _ordered(tables: list[Table]) -> list[Table]:
    order = insert_order()
    return sorted(tables, key=lambda t: order.index(t.name))


def generate_ddl() -> str:
    out = [
        "-- Delivery Ops Layer — skema companion (tabel yang BERLAKU)",
        f"-- Dibangkitkan dari dol_schema/model.py (versi {SCHEMA_VERSION}).",
        "-- JANGAN diedit tangan: ubah model.py lalu bangkitkan ulang.",
        "",
        _UPDATED_AT_FN,
        "",
    ]
    for t in _ordered(tables_with_status("berlaku")):
        out.append(_table_sql(t))
        out.append("")
    out.append(_VIEWS_BERLAKU)
    return "\n".join(out) + "\n"


def generate_ddl_usulan() -> str:
    usulan = tables_with_status("ditunda")
    out = [
        "-- Delivery Ops Layer — tabel USULAN (status: ditunda)",
        f"-- Dibangkitkan dari dol_schema/model.py (versi {SCHEMA_VERSION}).",
        "-- Untuk dibahas bersama RPA & Network Engineer. Jalankan SETELAH schema.sql.",
        f"-- Tabel: {', '.join(t.name for t in _ordered(usulan))}",
        "",
    ]
    for t in _ordered(usulan):
        out.append(_table_sql(t))
        out.append("")
    out.append(_VIEWS_USULAN)
    return "\n".join(out) + "\n"


__all__ = ["generate_ddl", "generate_ddl_usulan", "ALL_TABLES"]
