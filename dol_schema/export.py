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

from dol_schema.model import ALL_TABLES, SCHEMA_VERSION, Column, Table, insert_order

# Kolom prosa: dirender sebagai area teks di UI NocoDB supaya PM bisa membacanya utuh.
_LONG_TEXT = {
    "markdown", "description", "specification", "remarks", "work_title", "project_name",
    "acceptance_statement", "org_address_text", "payment_mechanism", "penalty_terms",
    "bast_terms", "evidence_quote", "ai_value_text", "final_value_text",
    "reviewed_ai_value_text", "reviewer_note", "value_text",
}
_MONEY_SUFFIX = ("_value", "_price", "_total")


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
        if col.name.endswith("_score"):
            return "Percent"
        if col.name.endswith(_MONEY_SUFFIX):
            return "Currency"
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
    if col.note:
        out["note"] = col.note
    return out


def _table_dict(t: Table) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "name": t.name,
        "written_by": t.written_by,
        "columns": [_column_dict(c) for c in t.columns],
    }
    if t.unique_together:
        out["unique_together"] = [list(k) for k in t.unique_together]
    if t.note:
        out["note"] = t.note
    return out


def to_schema_dict() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "insert_order": insert_order(),
        "tables": [_table_dict(t) for t in ALL_TABLES],
    }


def to_nocodb_fields() -> Dict[str, Any]:
    """Spesifikasi kolom siap pakai untuk membuat tabel lewat API NocoDB.

    `id`, `created_at`, `updated_at` tidak disertakan: NocoDB membuatnya sendiri.
    """
    auto = {"created_at", "updated_at"}
    return {
        "schema_version": SCHEMA_VERSION,
        "tables": {
            t.name: [
                {"title": c.name, "uidt": nocodb_type(c),
                 **({"options": list(c.enum)} if c.enum else {})}
                for c in t.columns if c.name not in auto
            ]
            for t in ALL_TABLES
        },
    }


def to_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
