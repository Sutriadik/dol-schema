"""
Ekspor definisi skema ke format yang bisa dibaca konsumen non-Python.

Kenapa ada: n8n (RPA Engineer) dan compiler lampiran BAST (Network Engineer) tidak bisa
meng-import `model.py`. Mereka membaca `generated/schema.json`. Tanpa ini, nama kolom akan
ditulis ulang di tiap repo — persis penyakit yang membuat exporter lama tidak terawat.

Tipe NocoDB diturunkan dari tipe yang DIDEKLARASIKAN di model, bukan ditebak dari nama kolom.
Ini menutup satu kelas bug: exporter lama menebak tipe dari nama, sehingga kolom bernama
numerik yang isinya teks ("1/1000", "30 hari kalender") gagal masuk NocoDB tanpa pesan jelas.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from dol_schema.model import (
    ALL_TABLES, AUDIT_COLUMNS, OWNERS, SCHEMA_VERSION, Column, Table,
    insert_order, natural_key, parent_refs,
)

# Kolom prosa: dirender sebagai area teks di UI NocoDB supaya PM bisa membacanya utuh.
_LONG_TEXT = {
    "markdown", "description", "specification", "remarks", "work_title", "project_name",
    "acceptance_statement", "org_address_text", "payment_mechanism", "penalty_terms",
    "bast_terms", "evidence_quote", "ai_value_text", "final_value_text",
    "reviewed_ai_value_text", "reviewer_note", "value_text",
    "validation_notes", "requirement_text", "review_note", "auto_check_notes",
}
_MONEY_SUFFIX = ("_value", "_price", "_total")

# Aturan yang harus diikuti SETIAP pengirim data (n8n, dol-parser, compiler BAST).
CONVENTIONS = {
    "upsert": "Cari baris dengan upsert_key; bila ada -> PATCH, bila tidak -> POST. "
              "Tabel tanpa upsert_key: hapus anak lama milik induk yang sama lalu isi ulang.",
    "foreign_keys": "Baris anak membawa placeholder `_<induk>_ref` berisi nilai kunci induk. "
                    "Pengirim menukarnya dengan Id baris induk yang baru dibuat, mengikuti "
                    "insert_order (induk dulu).",
    "human_columns": "Kolom di human_columns HANYA diisi PM lewat UI NocoDB. Pengirim mesin "
                     "tidak boleh menyertakannya sama sekali, termasuk saat sinkron ulang.",
    "dates": "Kolom date = string 'YYYY-MM-DD'; timestamptz = ISO 8601 dengan zona waktu.",
    "money": "Nominal dalam mata uang kolom currency (bawaan IDR), angka tanpa pemisah ribuan.",
    "mybhakti_refs": "Kolom mybhakti_*_ref diisi n8n dari API MyBhakti (read-only); bukan FK.",
}


def nocodb_type(col: Column) -> str:
    if col.enum:
        return "SingleSelect"
    if col.type == "text":
        return "LongText" if col.name in _LONG_TEXT else "SingleLineText"
    if col.type == "char3":
        return "SingleLineText"
    if col.type == "int":
        return "Number"
    if col.type == "numeric":
        # Skor disimpan 0-1. Tipe Percent NocoDB berskala 0-100 dan menampilkan 0,876 sebagai
        # "0,876%" -- PM membaca 87,6% sebagai kurang dari 1%.
        if col.name.endswith(_MONEY_SUFFIX):
            return "Currency"
        return "Decimal"
    if col.type == "coord":
        return "Decimal"
    if col.type == "date":
        return "Date"
    if col.type == "timestamptz":
        return "DateTime"
    raise ValueError(f"Tipe tak dikenal '{col.type}' pada kolom {col.name}")


def _column_dict(col: Column) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "name": col.name,
        "type": col.type,
        "nocodb_type": nocodb_type(col),
        "required": not col.null,
    }
    if col.unique:
        out["unique"] = True
    if col.fk:
        out["fk"] = col.fk
        out["on_delete"] = col.fk_on_delete
    if col.enum:
        out["enum"] = list(col.enum)
    if col.check:
        out["check"] = col.check
    if col.default:
        out["default"] = col.default.strip("'")
    if col.written_by == "human":
        out["written_by"] = "human"
    if col.note:
        out["note"] = col.note
    return out


def _table_dict(t: Table) -> Dict[str, Any]:
    key = natural_key(t)
    out: Dict[str, Any] = {
        "name": t.name,
        "domain": t.domain,
        "owner": OWNERS[t.owner],
        "written_by": t.written_by,
        "in_nocodb": t.nocodb,
        "display_column": t.display,
        "upsert_key": list(key) if key else None,
        "parent_refs": parent_refs(t),
        "human_columns": t.human_columns(),
        "columns": [_column_dict(c) for c in t.columns],
    }
    if t.unique_together:
        out["unique_together"] = [list(k) for k in t.unique_together]
    if t.note:
        out["note"] = t.note
    return out


def to_schema_dict() -> Dict[str, Any]:
    """Kontrak data untuk semua pengirim & pembaca (n8n, compiler BAST, dol-parser)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "insert_order": insert_order(),
        "conventions": CONVENTIONS,
        "tables": [_table_dict(t) for t in ALL_TABLES],
    }


def _nocodb_field(t: Table, c: Column) -> Dict[str, Any]:
    out: Dict[str, Any] = {"title": c.name, "uidt": nocodb_type(c)}
    if c.enum:
        out["options"] = list(c.enum)
    description = c.note
    if c.written_by == "human" or t.written_by == "human":
        description = f"Diisi PM. {description}".strip()
    if description:
        out["description"] = description
    if c.name == t.display:
        out["pv"] = True          # judul baris di UI NocoDB: PM melihat nomor kontrak, bukan Id
    return out


def to_nocodb_fields() -> Dict[str, Any]:
    """Spesifikasi kolom siap pakai untuk membuat tabel lewat API NocoDB.

    `id`, `created_at`, `updated_at` tidak disertakan: NocoDB membuatnya sendiri.
    Tabel bertanda `nocodb=False` juga tidak disertakan sama sekali.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "tables": {
            t.name: [_nocodb_field(t, c) for c in t.columns if c.name not in AUDIT_COLUMNS]
            for t in ALL_TABLES if t.nocodb
        },
    }


def to_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
