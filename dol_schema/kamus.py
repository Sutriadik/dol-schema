"""
Kamus data berbahasa Indonesia, dibangkitkan dari model -> generated/KAMUS_DATA.md.

Untuk PM dan ketiga tim (briefing hlm. 21: "orang lain bisa memahami, menjalankan, dan
mengubahnya tanpa bertanya"). Ditulis dari model, bukan tangan, supaya tidak pernah berbeda
dari tabel yang sebenarnya; `python -m dol_schema --check` gagal bila kamus ini basi.
"""

from __future__ import annotations

from dol_schema.model import (
    ALL_TABLES,
    AUDIT_COLUMNS,
    DOMAINS,
    OWNERS,
    SCHEMA_VERSION,
    Column,
    Table,
    insert_order,
    natural_key,
    tables_with_status,
)

_TYPE_LABEL = {
    "text": "teks",
    "int": "angka bulat",
    "numeric": "angka",
    "coord": "koordinat GPS",
    "date": "tanggal",
    "timestamptz": "tanggal & jam",
    "char3": "kode 3 huruf",
}
_DOMAIN_INTRO = {
    "dokumen": "Setiap berkas PDF yang masuk.",
    "kontrak": (
        "Kontrak/SPK pelanggan — sumber semua BoQ dan aturan serah terima (briefing hlm. 3 & 11)."
    ),
    "sph": "Penawaran vendor yang lahir dari kebutuhan kontrak (rantai hulu).",
    "bast": "Serah terima. BAST pelanggan dibaca dari kontrak; nomor & render oleh RPA.",
    "evidence": "Foto bukti lapangan dari ODK Central (wilayah Network Engineer).",
    "verifikasi": "Nilai yang dibaca sistem beserta buktinya, dan keputusan PM per field.",
    "audit": "Jejak teknis pemrosesan — hanya di PostgreSQL, tidak tampil di NocoDB.",
}
_ALUR_PM = """\
## Cara PM memakai tabel ini di NocoDB

1. Buka **Hasil Ekstraksi**, saring per dokumen. Urutkan **Status Bukti**: kerjakan
   `bertentangan`, `tidak_ada_di_dokumen`, dan `perlu_dicek` lebih dulu.
2. `bukti_kuat` artinya nilai itu **ditemukan** di dokumen — bukan berarti benar. Nomor
   kontrak yang salah bisa tetap `bukti_kuat` bila nomor lain di dokumen kebetulan sama.
   Harga dan klausul tetap wajib diperiksa (briefing hlm. 20).
3. Catat setiap keputusan di **Keputusan PM**: `benar`, `dikoreksi` (isi **Nilai Final**),
   atau `ditolak`. Isi **Nilai Sistem Saat Diperiksa** dengan nilai yang Anda lihat.
4. Begitu sebuah dokumen punya Keputusan PM, sistem tidak lagi menimpanya otomatis.

## Nilai yang boleh dipakai dokumen hilir

Penyusunan BAST (nanti) hanya membaca nilai yang sudah diputuskan PM `benar` atau
`dikoreksi` dan belum basi. Di PostgreSQL tersedia view `nilai_terverifikasi` untuk itu;
field yang belum diperiksa dianggap kosong, bukan diambil dari nilai sistem.
"""


def _column_row(t: Table, c: Column) -> str:
    wajib = "ya" if not c.null else ""
    pengisi = "PM" if (c.written_by == "human" or t.written_by == "human") else "sistem"
    keterangan = c.note.replace("|", "/")
    if c.fk:
        induk = c.fk.split(".")[0]
        keterangan = (
            f"→ {next(x.label for x in ALL_TABLES if x.name == induk)}. {keterangan}".strip()
        )
    if c.enum:
        keterangan = f"{keterangan} Pilihan: {', '.join(f'`{v}`' for v in c.enum)}.".strip()
    if c.unique:
        keterangan = f"unik. {keterangan}".strip()
    return (
        f"| **{c.label}** | `{c.name}` | {_TYPE_LABEL[c.type]} | {wajib} | {pengisi} | "
        f"{keterangan} |"
    )


def _table_section(t: Table) -> list[str]:
    key = natural_key(t)
    induk = sorted({c.fk.split(".")[0] for c in t.columns if c.fk})
    label_induk = [next(x.label for x in ALL_TABLES if x.name == n) for n in induk]
    if t.in_nocodb:
        di_nocodb = "ya" + (f", judul baris = **{t.column(t.display).label}**" if t.display else "")
    elif t.status == "ditunda":
        di_nocodb = "belum — tabel usulan"
    else:
        di_nocodb = "tidak (hanya PostgreSQL)"
    lines = [
        f"### {t.label} (`{t.name}`)",
        "",
        t.note,
        "",
        f"- **Status:** {t.status}",
        f"- **Pemilik:** {OWNERS[t.owner]}",
        f"- **Diisi oleh:** {'PM (manusia)' if t.written_by == 'human' else 'sistem'}"
        + (
            f"; kolom milik PM: {', '.join(t.column(c).label for c in t.human_columns())}"
            if t.human_columns() and t.written_by != "human"
            else ""
        ),
        f"- **Tampil di NocoDB:** {di_nocodb}",
        "- **Kunci anti-dobel:** "
        + (" + ".join(t.column(k).label for k in key) if key else "— (belum ada)"),
        f"- **Induk:** {', '.join(label_induk) if label_induk else '—'}",
        "",
        "| Judul (NocoDB) | Nama teknis | Tipe | Wajib | Diisi | Keterangan |",
        "|---|---|---|---|---|---|",
    ]
    lines += [_column_row(t, c) for c in t.columns if c.name not in AUDIT_COLUMNS]
    return lines + [""]


def _sections(tables: list[Table]) -> list[str]:
    out: list[str] = []
    for d in DOMAINS:
        members = [t for t in tables if t.domain == d]
        if not members:
            continue
        out += [f"### Kelompok: {d}", "", _DOMAIN_INTRO[d], ""]
        for t in members:
            out += _table_section(t)
    return out


def to_kamus() -> str:
    berlaku = tables_with_status("berlaku")
    ditunda = tables_with_status("ditunda")
    out = [
        "# Kamus Data — Delivery Ops Layer",
        "",
        f"Versi skema **{SCHEMA_VERSION}**. Dibangkitkan dari `dol_schema/model.py` — "
        "jangan diedit tangan; ubah model lalu jalankan `python -m dol_schema --emit`.",
        "",
        "Setiap tabel punya dua nama: **judul** berbahasa Indonesia (yang tampil di NocoDB) dan",
        "**nama teknis** (dipakai kode, SQL, dan n8n). Setiap tabel juga punya kolom `id`,",
        "`created_at`, `updated_at` yang diisi otomatis.",
        "",
        "Data master klien, vendor, proyek, dan PO **tidak** ada di sini — sumbernya MyBhakti",
        "(briefing hlm. 7); yang disimpan hanya kolom rujukan `mybhakti_*_ref`.",
        "",
        "## Daftar tabel",
        "",
        "| Tabel | Nama teknis | Status | Pemilik | Diisi oleh | Di NocoDB |",
        "|---|---|---|---|---|---|",
    ]
    for t in ALL_TABLES:
        out.append(
            f"| **{t.label}** | `{t.name}` | {t.status} | {OWNERS[t.owner]} | "
            f"{'PM' if t.written_by == 'human' else 'sistem'} | "
            f"{'ya' if t.in_nocodb else 'tidak'} |"
        )
    urutan = [n for n in insert_order() if any(t.name == n for t in berlaku)]
    out += [
        "",
        "Urutan pengisian tabel yang berlaku (induk dulu): "
        + " → ".join(next(t.label for t in berlaku if t.name == n) for n in urutan),
        "",
        _ALUR_PM,
        "## Tabel yang berlaku",
        "",
    ]
    out += _sections(berlaku)
    out += [
        "## Tabel usulan (ditunda)",
        "",
        "Belum dibuat di NocoDB. Menunggu kesepakatan bersama RPA Engineer (nomor & render",
        "BAST) dan Network Engineer (evidence & lampiran). DDL-nya ada di",
        "`generated/schema_usulan.sql` untuk dibahas di workshop skema.",
        "Pilihan nilainya sengaja belum diterjemahkan: diputuskan saat disepakati.",
        "",
    ]
    out += _sections(ditunda)
    return "\n".join(out).rstrip() + "\n"
