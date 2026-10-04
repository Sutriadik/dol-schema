"""
Ekspor definisi skema ke format yang bisa dibaca konsumen non-Python, dan penerjemah nama
kolom <-> judul NocoDB.

Kenapa ada: n8n (RPA Engineer) dan compiler lampiran BAST (Network Engineer) tidak bisa
meng-import `model.py`. Mereka membaca `generated/schema.json`. Tanpa ini, nama kolom akan
ditulis ulang di tiap repo — persis penyakit yang membuat exporter lama tidak terawat.

Judul NocoDB = label bahasa Indonesia. API rekaman NocoDB v2 memakai JUDUL kolom sebagai
kunci JSON dan di klausa `where`, jadi setiap pengirim wajib menerjemahkan nama teknis ke
judul sebelum mengirim. Terjemahannya hanya ada di sini (`to_nocodb_record`,
`nocodb_title`), dan ikut di `schema.json` (`columns[].label`) untuk n8n.
"""

from __future__ import annotations

import json
from typing import Any

from dol_schema.model import (
    ALL_TABLES,
    AUDIT_COLUMNS,
    OWNERS,
    SCHEMA_VERSION,
    Column,
    Table,
    insert_order,
    natural_key,
    parent_refs,
    table,
)

# Kolom prosa: dirender sebagai area teks di UI NocoDB supaya PM bisa membacanya utuh.
_LONG_TEXT = {
    "markdown",
    "description",
    "specification",
    "remarks",
    "work_title",
    "project_name",
    "acceptance_statement",
    "org_address_text",
    "payment_mechanism",
    "penalty_terms",
    "bast_terms",
    "evidence_quote",
    "ai_value_text",
    "final_value_text",
    "reviewed_ai_value_text",
    "reviewer_note",
    "value_text",
    "validation_notes",
    "requirement_text",
    "review_note",
    "auto_check_notes",
}
_MONEY_SUFFIX = ("_value", "_price", "_total")

# Aturan yang harus diikuti SETIAP pengirim data (n8n, dol-parser, compiler BAST).
CONVENTIONS = {
    "status_tabel": "Hanya tabel berstatus 'berlaku' yang dibuat & diisi di NocoDB. Tabel "
    "'ditunda' adalah usulan untuk dibahas; jangan dikirim ke NocoDB.",
    "judul_nocodb": "API rekaman NocoDB memakai JUDUL kolom (columns[].label, bahasa "
    "Indonesia) sebagai kunci JSON dan di klausa where. Terjemahkan nama "
    "teknis ke judul sebelum mengirim; kolom 'Id' tetap 'Id'.",
    "upsert": "Cari baris dengan upsert_key; bila ada -> PATCH, bila tidak -> POST. Baris "
    "anak milik induk yang sama yang tidak ada lagi di kiriman baru dihapus.",
    "dokumen_sudah_direview": "Dokumen yang sudah punya baris di field_review (Keputusan PM) "
    "tidak boleh ditimpa otomatis: proses ulang hanya atas "
    "permintaan PM.",
    "foreign_keys": "Baris anak membawa placeholder `_<induk>_ref` berisi nilai kunci induk. "
    "Pengirim menukarnya dengan Id baris induk yang baru dibuat, mengikuti "
    "insert_order (induk dulu).",
    "human_columns": "Kolom di human_columns HANYA diisi PM lewat UI NocoDB. Pengirim mesin "
    "tidak boleh menyertakannya sama sekali, termasuk saat sinkron ulang.",
    "nilai_terverifikasi": "Dokumen hilir (mis. BAST) hanya boleh memakai nilai field yang "
    "punya keputusan PM 'benar' atau 'dikoreksi' dan belum basi "
    "(view nilai_terverifikasi). Nilai sistem saja bukan persetujuan.",
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


# --------------------------------------------------------------------------- judul NocoDB
def nocodb_title(table_name: str, column_name: str) -> str:
    """Nama teknis kolom -> judul kolom di NocoDB. 'Id' (kolom bawaan NocoDB) tetap 'Id'."""
    if column_name == "Id":
        return "Id"
    col = table(table_name).column(column_name)
    if col is None:
        raise KeyError(f"{table_name}.{column_name} tidak ada di model")
    return col.label


def to_nocodb_record(table_name: str, row: dict[str, Any]) -> dict[str, Any]:
    """Satu baris {nama_teknis: nilai} -> {judul_nocodb: nilai}, siap dikirim ke API NocoDB."""
    return {nocodb_title(table_name, k): v for k, v in row.items()}


def from_nocodb_record(table_name: str, record: dict[str, Any]) -> dict[str, Any]:
    """Kebalikan to_nocodb_record. Kolom bawaan NocoDB selain 'Id' dibuang."""
    by_title = {c.label: c.name for c in table(table_name).columns}
    out: dict[str, Any] = {}
    for k, v in record.items():
        if k == "Id":
            out["Id"] = v
        elif k in by_title:
            out[by_title[k]] = v
    return out


# --------------------------------------------------------------------------- schema.json
def _column_dict(col: Column) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": col.name,
        "label": col.label,
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


def _table_dict(t: Table) -> dict[str, Any]:
    key = natural_key(t)
    out: dict[str, Any] = {
        "name": t.name,
        "label": t.label,
        "status": t.status,
        "domain": t.domain,
        "owner": OWNERS[t.owner],
        "written_by": t.written_by,
        "in_nocodb": t.in_nocodb,
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


def to_schema_dict() -> dict[str, Any]:
    """Kontrak data untuk semua pengirim & pembaca (n8n, compiler BAST, dol-parser)."""
    berlaku = [n for n in insert_order() if table(n).status == "berlaku"]
    return {
        "schema_version": SCHEMA_VERSION,
        "insert_order": berlaku,
        "conventions": CONVENTIONS,
        "tables": [_table_dict(t) for t in ALL_TABLES],
    }


# --------------------------------------------------------------------------- nocodb_fields.json
def _nocodb_field(t: Table, c: Column) -> dict[str, Any]:
    out: dict[str, Any] = {"column_name": c.name, "title": c.label, "uidt": nocodb_type(c)}
    if c.enum:
        out["options"] = list(c.enum)
    description = c.note
    if c.written_by == "human" or t.written_by == "human":
        description = f"Diisi PM. {description}".strip()
    if description:
        out["description"] = description
    if c.name == t.display:
        out["pv"] = True  # judul baris di UI NocoDB: PM melihat nomor kontrak, bukan Id
    return out


def to_nocodb_fields() -> dict[str, Any]:
    """Spesifikasi tabel & kolom siap pakai untuk membuat tabel lewat API meta NocoDB.

    `id`, `created_at`, `updated_at` tidak disertakan: NocoDB membuatnya sendiri.
    Hanya tabel `in_nocodb` (berlaku & bukan khusus PostgreSQL).
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "tables": {
            t.name: {
                "title": t.label,
                "description": t.note,
                "columns": [_nocodb_field(t, c) for c in t.columns if c.name not in AUDIT_COLUMNS],
            }
            for t in ALL_TABLES
            if t.in_nocodb
        },
    }


def table_name_for_title(title: str) -> str | None:
    """Judul tabel di NocoDB -> nama teknis (None bila bukan tabel model ini)."""
    return next((t.name for t in ALL_TABLES if t.label == title), None)


def to_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


__all__: list[str] = [
    "CONVENTIONS",
    "nocodb_type",
    "nocodb_title",
    "to_nocodb_record",
    "from_nocodb_record",
    "to_schema_dict",
    "to_nocodb_fields",
    "table_name_for_title",
    "to_json",
]
