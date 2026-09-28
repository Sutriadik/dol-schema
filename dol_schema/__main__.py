"""CLI dol-schema: bangkitkan artefak dari model, atau periksa apakah artefak sudah basi.

    python -m dol_schema --emit          # tulis ulang generated/
    python -m dol_schema --check         # gagal bila generated/ tidak sesuai model
    python -m dol_schema --tables        # ringkasan tabel
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dol_schema import (
    ALL_TABLES,
    SCHEMA_VERSION,
    generate_ddl,
    to_json,
    to_nocodb_fields,
    to_schema_dict,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "generated"


def _artifacts() -> dict[Path, str]:
    return {
        OUT / "schema.sql": generate_ddl(),
        OUT / "schema.json": to_json(to_schema_dict()),
        OUT / "nocodb_fields.json": to_json(to_nocodb_fields()),
    }


def cmd_emit() -> int:
    OUT.mkdir(exist_ok=True)
    for path, content in _artifacts().items():
        path.write_text(content, encoding="utf-8")
        print(f"  ditulis  {path.relative_to(ROOT)}  ({len(content):,} byte)")
    print(f"\nSkema {SCHEMA_VERSION} — {len(ALL_TABLES)} tabel.")
    return 0


def cmd_check() -> int:
    basi = [p.name for p, isi in _artifacts().items()
            if not p.exists() or p.read_text(encoding="utf-8") != isi]
    if basi:
        print("Artefak tidak sesuai model: " + ", ".join(basi))
        print("Jalankan: python -m dol_schema --emit")
        return 1
    print(f"generated/ sesuai model ({SCHEMA_VERSION}).")
    return 0


def cmd_tables() -> int:
    print(f"Skema {SCHEMA_VERSION} — {len(ALL_TABLES)} tabel\n")
    for t in ALL_TABLES:
        penulis = "MANUSIA" if t.written_by == "human" else "mesin"
        fk = [c.fk.split(".")[0] for c in t.columns if c.fk]
        rujuk = f"  -> {', '.join(fk)}" if fk else ""
        print(f"  {t.name:<18} {len(t.columns):>2} kolom   ditulis {penulis}{rujuk}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(prog="dol_schema", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emit", action="store_true", help="tulis ulang generated/")
    ap.add_argument("--check", action="store_true", help="periksa generated/ vs model")
    ap.add_argument("--tables", action="store_true", help="ringkasan tabel")
    args = ap.parse_args()

    if args.emit:
        sys.exit(cmd_emit())
    if args.check:
        sys.exit(cmd_check())
    if args.tables:
        sys.exit(cmd_tables())
    ap.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
