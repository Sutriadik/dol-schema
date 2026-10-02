"""
Invarian skema yang dipegang tiga repo (dol-parser, dol-n8n, dol-bast-compiler).

Tes ini menjaga hal-hal yang tidak boleh rusak diam-diam saat model.py diubah: rujukan FK
selalu ke tabel yang ada, kolom milik PM tidak bisa diisi mesin, dan artefak generated/
selalu sesuai model.
"""
from pathlib import Path

from dol_schema import (
    ALL_TABLES, SCHEMA_VERSION, insert_order, natural_key, table, to_nocodb_fields,
    to_schema_dict, validate_payload,
)
from dol_schema.__main__ import _artifacts
from dol_schema.model import DOMAINS, OWNERS

ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------- struktur
def test_setiap_fk_menunjuk_tabel_dan_kolom_yang_ada():
    for t in ALL_TABLES:
        for c in t.columns:
            if c.fk:
                parent, col = c.fk.split(".")
                assert col == "id", f"{t.name}.{c.name} harus menunjuk id"
                table(parent)          # KeyError bila tabel induk tidak ada


def test_urutan_insert_menempatkan_induk_lebih_dulu():
    order = insert_order()
    for t in ALL_TABLES:
        for c in t.columns:
            if c.fk and c.fk.split(".")[0] != t.name:
                assert order.index(c.fk.split(".")[0]) < order.index(t.name)


def test_nama_tabel_dan_kolom_unik():
    names = [t.name for t in ALL_TABLES]
    assert len(names) == len(set(names))
    for t in ALL_TABLES:
        cols = [c.name for c in t.columns]
        assert len(cols) == len(set(cols)), t.name


def test_pemilik_domain_dan_judul_baris_valid():
    for t in ALL_TABLES:
        assert t.owner in OWNERS and t.domain in DOMAINS, t.name
        if t.nocodb:
            assert t.display and t.column(t.display), f"{t.name}: judul baris NocoDB"


def test_tabel_yang_disinkron_ulang_punya_kunci_anti_dobel():
    """Tanpa kunci alami, sinkron ulang dari ODK/pipeline menggandakan baris."""
    for name in ("document", "contract", "contract_item", "contract_requirement",
                 "evidence_photo", "extracted_field"):
        assert natural_key(table(name)), name


# --------------------------------------------------------------------- kolom milik PM
def test_payload_mesin_tidak_boleh_mengisi_kolom_pm():
    payload = {"evidence_photo": [{
        "odk_instance_id": "uuid:1", "_contract_item_ref": "x", "photo_type": "item",
        "photo_url": "http://x/1.jpg", "taken_at": "2026-01-02T10:53:00+07:00",
        "review_status": "approved",
    }]}
    masalah = validate_payload(payload)
    assert any("review_status" in m and "milik PM" in m for m in masalah)


def test_evidence_tanpa_kolom_pm_lolos_validasi():
    payload = {"evidence_photo": [{
        "odk_instance_id": "uuid:1", "_contract_item_ref": "x", "photo_type": "serial_label",
        "serial_number": "225B518001956", "photo_url": "http://x/1.jpg",
        "taken_at": "2026-01-02T10:53:00+07:00", "gps_lat": -7.347824, "gps_lon": 108.232318,
    }]}
    assert validate_payload(payload) == []


# --------------------------------------------------------------------- artefak untuk tim lain
def test_schema_json_memuat_kontrak_untuk_n8n():
    d = to_schema_dict()
    assert d["schema_version"] == SCHEMA_VERSION and d["conventions"]
    ev = next(t for t in d["tables"] if t["name"] == "evidence_photo")
    assert ev["upsert_key"] == ["odk_instance_id"]
    assert "review_status" in ev["human_columns"]
    assert {r["placeholder"] for r in ev["parent_refs"]} == {
        "_contract_item_ref", "_contract_requirement_ref"}


def test_nocodb_fields_tanpa_tabel_audit_dan_skor_bukan_persen():
    fields = to_nocodb_fields()["tables"]
    assert "extraction_run" not in fields
    score = next(f for f in fields["extracted_field"] if f["title"] == "evidence_score")
    assert score["uidt"] == "Decimal"
    assert sum(1 for f in fields["contract"] if f.get("pv")) == 1


def test_artefak_generated_sesuai_model():
    basi = [p.name for p, isi in _artifacts().items()
            if not p.exists() or p.read_text(encoding="utf-8") != isi]
    assert basi == [], f"jalankan `python -m dol_schema --emit`: {basi}"
