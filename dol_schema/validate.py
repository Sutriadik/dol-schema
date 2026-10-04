"""
Validasi payload companion terhadap definisi model.

Dijalankan SEBELUM payload menyentuh NocoDB. Pada exporter lama, kolom bertipe salah membuat
baris gagal masuk tanpa pesan yang jelas -- yang hilang justru baris yang paling perlu
dikoreksi manusia. Di sini setiap pelanggaran disebutkan tabel, baris, kolom, dan sebabnya.

Tabel berstatus 'ditunda' tetap divalidasi (supaya usulan bisa diuji dengan data nyata),
tetapi pengirim tidak boleh mengirimnya ke NocoDB.
"""

from __future__ import annotations

import re
from typing import Any

from dol_schema.model import ALL_TABLES, Column, table

_NUMERIC_OK = (int, float)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _type_ok(col: Column, value: Any) -> bool:
    if value is None:
        return True
    if col.type == "text":
        return isinstance(value, str)
    if col.type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if col.type in ("numeric", "coord"):
        return isinstance(value, _NUMERIC_OK) and not isinstance(value, bool)
    if col.type == "date":
        return isinstance(value, str) and bool(_ISO_DATE.match(value))
    if col.type == "timestamptz":
        return isinstance(value, str)
    if col.type == "char3":
        return isinstance(value, str) and len(value) == 3
    return True


def validate_payload(payload: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Kembalikan daftar masalah. Kosong = payload siap dikirim."""
    problems: list[str] = []
    known = {t.name for t in ALL_TABLES}

    for table_name, rows in payload.items():
        if table_name not in known:
            problems.append(f"{table_name}: tabel tidak ada di model")
            continue
        t = table(table_name)
        if t.written_by == "human" and rows:
            problems.append(
                f"{table_name}: pipeline mengisi tabel milik manusia "
                f"({len(rows)} baris). Hanya PM yang boleh menulis ke sini."
            )
        col_names = {c.name for c in t.columns}
        human_cols = set(t.human_columns()) if t.written_by != "human" else set()
        seen_unique: dict[tuple, set] = {}

        for i, row in enumerate(rows, 1):
            for key, value in row.items():
                if key.startswith("_"):  # referensi antar-tabel sebelum id nyata ada
                    continue
                if key not in col_names:
                    problems.append(f"{table_name}[{i}].{key}: kolom tidak ada di model")
                    continue
                col = t.column(key)
                if key in human_cols:
                    # Sengaja ditolak walau nilainya None: menyertakan kolom ini saja sudah
                    # berarti PATCH bisa menimpa keputusan PM saat sinkron ulang.
                    problems.append(
                        f"{table_name}[{i}].{key}: kolom milik PM, pengirim mesin tidak boleh "
                        f"menyertakannya"
                    )
                    continue
                if not _type_ok(col, value):
                    problems.append(
                        f"{table_name}[{i}].{key}: tipe {col.type} tapi nilainya "
                        f"{type(value).__name__} ({value!r:.60})"
                    )
                if col.enum and value is not None and value not in col.enum:
                    problems.append(
                        f"{table_name}[{i}].{key}: '{value}' bukan nilai sah ({'|'.join(col.enum)})"
                    )
            for col in t.columns:
                if col.null or col.name in ("created_at", "updated_at") or col.name in human_cols:
                    continue
                if col.default and col.name not in row:
                    continue  # database mengisi nilai bawaan
                if col.fk and f"_{col.fk.split('.')[0]}_ref" in row:
                    continue  # FK akan diisi saat insert, rujukannya ada
                if row.get(col.name) is None:
                    problems.append(f"{table_name}[{i}].{col.name}: NOT NULL tapi kosong")

            for cols in t.unique_together:
                key = tuple(row.get(c) for c in cols)
                bucket = seen_unique.setdefault(cols, set())
                if key in bucket:
                    problems.append(f"{table_name}[{i}]: duplikat pada UNIQUE {cols} = {key}")
                bucket.add(key)

    # Aturan khusus BAST yang tidak bisa dinyatakan lewat constraint satu tabel.
    parties = payload.get("bast_party") or []
    if payload.get("bast") and len(parties) != 2:
        problems.append(
            f"bast_party: ada {len(parties)} baris, seharusnya tepat 2 (handover + receiver)"
        )
    roles = sorted(p.get("role") for p in parties)
    if parties and roles != ["handover", "receiver"]:
        problems.append(f"bast_party: peran harus handover+receiver, sekarang {roles}")

    for b in payload.get("bast") or []:
        if b.get("direction") == "customer" and b.get("mybhakti_po_ref"):
            problems.append("bast: direction=customer tidak boleh punya mybhakti_po_ref")
        if b.get("direction") == "vendor" and b.get("contract_id"):
            problems.append("bast: direction=vendor tidak boleh punya contract_id")
    return problems
