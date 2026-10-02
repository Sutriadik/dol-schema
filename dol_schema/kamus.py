"""
Kamus data berbahasa Indonesia, dibangkitkan dari model -> generated/KAMUS_DATA.md.

Untuk PM dan ketiga tim (briefing hlm. 21: "orang lain bisa memahami, menjalankan, dan
mengubahnya tanpa bertanya"). Ditulis dari model, bukan tangan, supaya tidak pernah berbeda
dari tabel yang sebenarnya; `python -m dol_schema --check` gagal bila kamus ini basi.
"""
from __future__ import annotations

from typing import List

from dol_schema.model import (
    ALL_TABLES, AUDIT_COLUMNS, DOMAINS, OWNERS, SCHEMA_VERSION, Column, Table,
    insert_order, natural_key,
)

_TYPE_LABEL = {
    "text": "teks", "int": "angka bulat", "numeric": "angka", "coord": "koordinat GPS",
    "date": "tanggal", "timestamptz": "tanggal & jam", "char3": "kode 3 huruf",
}
_DOMAIN_INTRO = {
    "dokumen": "Setiap berkas PDF yang masuk.",
    "kontrak": "Kontrak/SPK pelanggan — sumber semua BoQ dan aturan serah terima (briefing hlm. 3 & 11).",
    "sph": "Penawaran vendor yang lahir dari kebutuhan kontrak (rantai hulu).",
    "bast": "Serah terima. BAST pelanggan dibaca dari kontrak; nomor & render oleh RPA.",
    "evidence": "Foto bukti lapangan dari ODK Central (wilayah Network Engineer).",
    "verifikasi": "Nilai hasil ekstraksi beserta skor & buktinya, dan keputusan PM per field.",
    "audit": "Jejak teknis pemrosesan — hanya di PostgreSQL, tidak tampil di NocoDB.",
}
_BAST_RECIPE = """\
## Cara menyusun BAST pelanggan dari nomor kontrak

Sistem tidak menyalin data ke BAST. Ia mengikuti relasi dari satu nomor kontrak:

| Bagian BAST | Diambil dari | Syarat |
|---|---|---|
| Nomor kontrak, nama pekerjaan, nilai | `contract` | field sudah dikonfirmasi PM di `field_review` |
| Pihak & penandatangan | `contract_party` (lewat `contract_id`) | |
| Rincian pekerjaan | `contract_item` + info serah terima di `bast_item` | uraian & harga dari kontrak, tidak disalin |
| Lampiran evidence | `evidence_photo` (lewat `contract_item_id`) | hanya `review_status = approved` |
| Checklist kelengkapan | `contract_requirement` + `evidence_photo` | semua lampiran wajib terpenuhi |
| Nomor BAST internal | numbering service (RPA) | sequence database, bukan NocoDB |

Bila memakai PostgreSQL, tiga view siap pakai sudah ada di `schema.sql`:
`bast_rincian`, `evidence_siap_lampiran`, dan `checklist_gabungan`.
"""


def _column_row(t: Table, c: Column) -> str:
    wajib = "ya" if not c.null else ""
    pengisi = "PM" if (c.written_by == "human" or t.written_by == "human") else "sistem"
    keterangan = c.note.replace("|", "/")
    if c.fk:
        keterangan = f"→ `{c.fk}`. {keterangan}".strip()
    if c.enum:
        keterangan = f"{keterangan} Pilihan: {', '.join(f'`{v}`' for v in c.enum)}.".strip()
    if c.unique:
        keterangan = f"unik. {keterangan}".strip()
    return f"| `{c.name}` | {_TYPE_LABEL[c.type]} | {wajib} | {pengisi} | {keterangan} |"


def _table_section(t: Table) -> List[str]:
    key = natural_key(t)
    induk = sorted({c.fk.split(".")[0] for c in t.columns if c.fk})
    lines = [f"### `{t.name}`", "", t.note, "",
             f"- **Pemilik:** {OWNERS[t.owner]}",
             f"- **Diisi oleh:** {'PM (manusia)' if t.written_by == 'human' else 'sistem'}"
             + (f"; kolom milik PM: {', '.join(f'`{c}`' for c in t.human_columns())}"
                if t.human_columns() and t.written_by != "human" else ""),
             f"- **Tampil di NocoDB:** {'ya' if t.nocodb else 'tidak (hanya PostgreSQL)'}"
             + (f", judul baris = `{t.display}`" if t.nocodb and t.display else ""),
             f"- **Kunci anti-dobel:** {' + '.join(f'`{k}`' for k in key) if key else '— (diganti utuh per induk)'}",
             f"- **Induk:** {', '.join(f'`{p}`' for p in induk) if induk else '—'}",
             "",
             "| Kolom | Tipe | Wajib | Diisi | Keterangan |",
             "|---|---|---|---|---|"]
    lines += [_column_row(t, c) for c in t.columns if c.name not in AUDIT_COLUMNS]
    return lines + [""]


def to_kamus() -> str:
    out = [
        "# Kamus Data — Delivery Ops Layer",
        "",
        f"Versi skema **{SCHEMA_VERSION}**. Dibangkitkan dari `dol_schema/model.py` — "
        "jangan diedit tangan; ubah model lalu jalankan `python -m dol_schema --emit`.",
        "",
        "Setiap tabel juga punya kolom `id`, `created_at`, `updated_at` yang diisi otomatis.",
        "Data master klien, vendor, proyek, dan PO **tidak** ada di sini — sumbernya MyBhakti",
        "(briefing hlm. 7); yang disimpan hanya kolom rujukan `mybhakti_*_ref`.",
        "",
        "## Daftar tabel",
        "",
        "| Kelompok | Tabel | Pemilik | Diisi oleh | Di NocoDB |",
        "|---|---|---|---|---|",
    ]
    for t in ALL_TABLES:
        out.append(f"| {t.domain} | `{t.name}` | {OWNERS[t.owner]} | "
                   f"{'PM' if t.written_by == 'human' else 'sistem'} | "
                   f"{'ya' if t.nocodb else 'tidak'} |")
    out += ["", f"Urutan pengisian (induk dulu): {' → '.join(f'`{n}`' for n in insert_order())}",
            "", _BAST_RECIPE]
    for d in DOMAINS:
        members = [t for t in ALL_TABLES if t.domain == d]
        if not members:
            continue
        out += [f"## {d.capitalize()}", "", _DOMAIN_INTRO[d], ""]
        for t in members:
            out += _table_section(t)
    return "\n".join(out).rstrip() + "\n"
