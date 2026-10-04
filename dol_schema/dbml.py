"""
Ekspor skema ke DBML -- bahasa diagram dbdiagram.io (dan ekstensi VS Code-nya).

Kenapa dibangkitkan, bukan digambar tangan: diagram yang dirawat terpisah dari model pasti
lama-lama berbeda darinya, dan orang yang membaca diagram lalu mengira itulah skemanya.
Dengan DBML sebagai artefak `generated/`, `python -m dol_schema --check` ikut gagal saat
diagram basi -- sama seperti schema.sql.

Yang sengaja ikut digambar karena itu keputusan desain, bukan detail:
- **Penulis tabel.** Tabel milik manusia (`field_review`) diberi warna berbeda; pipeline
  tidak pernah menulis ke sana.
- **Tabel di luar NocoDB.** `extraction_run` hanya hidup di PostgreSQL.
- **Tabel usulan (ditunda).** Warna kuning: belum disepakati tim, belum dibuat di NocoDB.
- **Aksi ON DELETE.** RESTRICT menandai baris yang tidak boleh ikut terhapus diam-diam.
- **Kolom `*_ref` MyBhakti** tampil sebagai kolom biasa, TANPA garis relasi: sengaja bukan FK.
"""

from __future__ import annotations

from dol_schema.ddl import _PG_TYPE
from dol_schema.model import ALL_TABLES, DOMAINS, OWNERS, SCHEMA_VERSION, Column, Table

# Warna header = PEMILIK tabel (briefing hlm. 12-15).
_OWNER_COLOR = {"ai": "#3498DB", "network": "#8E44AD", "rpa": "#27AE60", "pm": "#E67E22"}
_COLOR_INTERNAL = "#7F8C8D"
_COLOR_DITUNDA = "#F1C40F"


def _q(text: str) -> str:
    """String DBML satu baris ber-kutip tunggal."""
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _enum_name(t: Table, c: Column) -> str:
    return f"{t.name}_{c.name}"


def _column_line(t: Table, c: Column) -> str:
    settings: list[str] = []
    if not c.null:
        settings.append("not null")
    if c.unique:
        settings.append("unique")
    if c.name in ("created_at", "updated_at"):
        settings.append("default: `now()`")
    elif c.default:
        settings.append(f"default: {c.default}")
    note = f"{c.label}. {c.note}".strip() if c.note else c.label
    if c.written_by == "human":
        note = f"[DIISI PM] {note}".strip()
    if c.check:
        note = f"{note}; CHECK ({c.check})" if note else f"CHECK ({c.check})"
    if note:
        settings.append(f"note: {_q(note)}")
    col_type = _enum_name(t, c) if c.enum else _PG_TYPE[c.type].replace(" ", "")
    suffix = f" [{', '.join(settings)}]" if settings else ""
    return f"  {c.name} {col_type}{suffix}"


def _table_block(t: Table) -> str:
    if t.written_by == "human":
        penulis = "MANUSIA (PM) -- pipeline tidak pernah menulis ke sini"
    elif t.status == "ditunda":
        penulis = "USULAN, belum dibuat di NocoDB"
    elif not t.nocodb:
        penulis = "mesin -- hanya PostgreSQL, TIDAK dikirim ke NocoDB"
    else:
        penulis = "mesin (pipeline)"
    if t.status == "ditunda":
        color = _COLOR_DITUNDA
    else:
        color = _OWNER_COLOR[t.owner] if t.nocodb else _COLOR_INTERNAL
    penulis = f"{penulis}. Pemilik: {OWNERS[t.owner]}"
    lines = [f"Table {t.name} [headercolor: {color}] {{", "  id bigint [pk, increment]"]
    lines += [_column_line(t, c) for c in t.columns]
    if t.unique_together:
        lines.append("")
        lines.append("  indexes {")
        for cols in t.unique_together:
            lines.append(f"    ({', '.join(cols)}) [unique]")
        lines.append("  }")
    lines.append("")
    catatan = f"{t.label}. " + (f"{t.note} " if t.note else "") + f"Ditulis oleh: {penulis}"
    lines.append(f"  Note: {_q(catatan)}")
    lines.append("}")
    return "\n".join(lines)


def _refs() -> list[str]:
    out = []
    for t in ALL_TABLES:
        for c in t.columns:
            if not c.fk:
                continue
            # UNIQUE pada kolom FK berarti 1:1 (mis. bast.document_id); selain itu banyak-ke-satu.
            arrow = "-" if c.unique else ">"
            ref_table, ref_col = c.fk.split(".")
            out.append(
                f"Ref: {t.name}.{c.name} {arrow} {ref_table}.{ref_col} "
                f"[delete: {c.fk_on_delete.lower()}]"
            )
    return out


def _enums() -> list[str]:
    out = []
    for t in ALL_TABLES:
        for c in t.columns:
            if c.enum:
                out.append(
                    f"Enum {_enum_name(t, c)} {{\n" + "\n".join(f"  {v}" for v in c.enum) + "\n}"
                )
    return out


def _groups() -> list[str]:
    groups: dict[str, list[str]] = {
        d: [t.name for t in ALL_TABLES if t.domain == d] for d in DOMAINS
    }
    return [
        f"TableGroup {g} {{\n" + "\n".join(f"  {n}" for n in members) + "\n}"
        for g, members in groups.items()
        if members
    ]


_PROJECT_NOTE = (
    "Warna header = pemilik tabel: biru = AI Engineer, ungu = Network Engineer, hijau = RPA "
    "Engineer, oranye = PM, abu-abu = hanya PostgreSQL (tidak dikirim ke NocoDB), kuning = "
    "usulan yang ditunda. Kolom "
    "bertanda [DIISI PM] hanya diubah PM. Kolom *_ref MyBhakti sengaja BUKAN foreign key "
    "(briefing hlm. 7)."
)


def to_dbml() -> str:
    parts = [
        "// Open ADE — Delivery Ops Layer: skema companion NocoDB",
        f"// Dibangkitkan dari dol_schema/model.py (versi {SCHEMA_VERSION}).",
        "// JANGAN diedit tangan: ubah model.py lalu jalankan `python -m dol_schema --emit`.",
        "// Buka di dbdiagram.io (tempel isi berkas ini) atau ekstensi DBML di VS Code.",
        "",
        "Project dol_schema {",
        "  database_type: 'PostgreSQL'",
        f"  Note: {_q(_PROJECT_NOTE)}",
        "}",
        "",
    ]
    parts += [_table_block(t) + "\n" for t in ALL_TABLES]
    parts += ["// ---------------------------------------------------------------- relasi"]
    parts += _refs()
    parts += [
        "",
        "// ---------------------------------------------------------------- pilihan nilai",
    ]
    parts += [e + "\n" for e in _enums()]
    parts += ["// ---------------------------------------------------------------- kelompok"]
    parts += [g + "\n" for g in _groups()]
    return "\n".join(parts).rstrip() + "\n"
