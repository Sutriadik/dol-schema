"""
Invarian skema yang dipegang tiga repo (dol-parser, dol-n8n, dol-bast-compiler).

Tes ini menjaga hal-hal yang tidak boleh rusak diam-diam saat model.py diubah: rujukan FK
selalu ke tabel yang ada, kolom milik PM tidak bisa diisi mesin, judul NocoDB berbahasa
Indonesia dan aman dipakai di API, tabel usulan tidak bocor ke NocoDB, dan artefak generated/
selalu sesuai model.
"""

import re

from dol_schema import (
    ALL_TABLES,
    SCHEMA_VERSION,
    from_nocodb_record,
    generate_ddl,
    generate_ddl_usulan,
    insert_order,
    natural_key,
    table,
    tables_with_status,
    to_nocodb_fields,
    to_nocodb_record,
    to_schema_dict,
    validate_payload,
)
from dol_schema.__main__ import _artifacts
from dol_schema.model import DOMAINS, OWNERS, STATUSES

# Judul kolom dipakai sebagai kunci JSON dan di klausa where NocoDB: koma dan kurung adalah
# sintaks where, titik dipakai untuk field bersarang. Cukup huruf, angka, dan spasi.
_JUDUL_AMAN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ]*$")
_JUDUL_SISTEM_NOCODB = {"Id", "CreatedAt", "UpdatedAt", "nc_order"}


# --------------------------------------------------------------------- struktur
def test_setiap_fk_menunjuk_tabel_dan_kolom_yang_ada():
    for t in ALL_TABLES:
        for c in t.columns:
            if c.fk:
                parent, col = c.fk.split(".")
                assert col == "id", f"{t.name}.{c.name} harus menunjuk id"
                table(parent)  # KeyError bila tabel induk tidak ada


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


def test_pemilik_domain_status_dan_judul_baris_valid():
    for t in ALL_TABLES:
        assert t.owner in OWNERS and t.domain in DOMAINS and t.status in STATUSES, t.name
        if t.in_nocodb:
            assert t.display and t.column(t.display), f"{t.name}: judul baris NocoDB"


def test_tabel_berlaku_tidak_bergantung_pada_usulan():
    """Tabel berlaku harus bisa dibuat sendiri, tanpa menunggu usulan disepakati."""
    ditunda = {t.name for t in tables_with_status("ditunda")}
    for t in tables_with_status("berlaku"):
        for c in t.columns:
            if c.fk:
                assert c.fk.split(".")[0] not in ditunda, f"{t.name}.{c.name} -> usulan"


def test_tabel_yang_disinkron_ulang_punya_kunci_anti_dobel():
    """Tanpa kunci alami, sinkron ulang menggandakan baris -- atau, dengan strategi hapus-isi
    ulang, menghapus kolom yang sudah diisi PM."""
    for t in tables_with_status("berlaku"):
        if t.written_by == "machine" and t.nocodb:
            assert natural_key(t), t.name


# --------------------------------------------------------------------- bahasa Indonesia
def test_setiap_tabel_dan_kolom_punya_label_indonesia():
    for t in ALL_TABLES:
        assert t.label, t.name
        for c in t.columns:
            assert c.label, f"{t.name}.{c.name}"


def test_judul_nocodb_unik_dan_aman_untuk_api():
    judul_tabel = [t.label for t in ALL_TABLES]
    assert len(judul_tabel) == len(set(judul_tabel))
    for t in ALL_TABLES:
        labels = [c.label for c in t.columns]
        assert len(labels) == len(set(labels)), t.name
        for c in t.columns:
            assert _JUDUL_AMAN.match(c.label), f"{t.name}.{c.name}: '{c.label}'"
            assert c.label not in _JUDUL_SISTEM_NOCODB, f"{t.name}.{c.name}"


def test_status_sistem_tidak_menyebut_terverifikasi():
    """Sistem hanya memeriksa keberadaan nilai di dokumen; kata 'verified/terverifikasi'
    membuat PM melewati field yang tetap wajib dicek (briefing hlm. 20)."""
    for v in table("extracted_field").column("system_status").enum:
        assert "verif" not in v


def test_terjemahan_judul_bolak_balik():
    baris = {"contract_number": "K/1", "work_title": "Pengadaan", "Id": 7}
    rekaman = to_nocodb_record("contract", baris)
    assert rekaman == {"Nomor Kontrak": "K/1", "Nama Pekerjaan": "Pengadaan", "Id": 7}
    assert from_nocodb_record("contract", dict(rekaman, CreatedAt="x")) == baris


# --------------------------------------------------------------------- tabel usulan
def test_tabel_usulan_tidak_dibuat_di_nocodb_maupun_schema_sql():
    usulan = {t.name for t in tables_with_status("ditunda")}
    assert {"bast", "bast_draft", "evidence_photo"} <= usulan
    assert usulan.isdisjoint(to_nocodb_fields()["tables"])
    sql, sql_usulan = generate_ddl(), generate_ddl_usulan()
    for n in usulan:
        assert f"CREATE TABLE IF NOT EXISTS {n} (" not in sql
        assert f"CREATE TABLE IF NOT EXISTS {n} (" in sql_usulan


def test_rincian_bast_parsial_memakai_volume_yang_diserahkan():
    assert "COALESCE(bi.quantity, ci.quantity)" in generate_ddl_usulan()


def test_status_dokumen_tidak_menghitung_keputusan_basi():
    sql = generate_ddl()
    assert "stale_count" in sql and "CREATE OR REPLACE VIEW nilai_terverifikasi" in sql


# --------------------------------------------------------------------- kolom milik PM
def test_payload_mesin_tidak_boleh_mengisi_kolom_pm():
    payload = {
        "evidence_photo": [
            {
                "odk_instance_id": "uuid:1",
                "_contract_item_ref": "x",
                "photo_type": "item",
                "photo_url": "http://x/1.jpg",
                "taken_at": "2026-01-02T10:53:00+07:00",
                "review_status": "approved",
            }
        ]
    }
    masalah = validate_payload(payload)
    assert any("review_status" in m and "milik PM" in m for m in masalah)


def test_pipeline_tidak_boleh_menulis_keputusan_pm():
    masalah = validate_payload({"field_review": [{"field_path": "x", "decision": "benar"}]})
    assert any("milik manusia" in m for m in masalah)


# --------------------------------------------------------------------- artefak untuk tim lain
def test_schema_json_memuat_kontrak_untuk_n8n():
    d = to_schema_dict()
    assert d["schema_version"] == SCHEMA_VERSION and d["conventions"]
    assert "judul_nocodb" in d["conventions"]
    assert all(table(n).status == "berlaku" for n in d["insert_order"])
    kontrak = next(t for t in d["tables"] if t["name"] == "contract")
    assert kontrak["label"] == "Kontrak" and kontrak["upsert_key"] == ["document_id"]
    assert (
        next(c for c in kontrak["columns"] if c["name"] == "contract_number")["label"]
        == "Nomor Kontrak"
    )


def test_nocodb_fields_judul_indonesia_tanpa_tabel_audit():
    tables = to_nocodb_fields()["tables"]
    assert "extraction_run" not in tables
    ef = tables["extracted_field"]
    assert ef["title"] == "Hasil Ekstraksi"
    skor = next(f for f in ef["columns"] if f["column_name"] == "evidence_score")
    assert skor["title"] == "Skor Bukti" and skor["uidt"] == "Decimal"
    assert sum(1 for f in tables["contract"]["columns"] if f.get("pv")) == 1


def test_artefak_generated_sesuai_model():
    basi = [
        p.name
        for p, isi in _artifacts().items()
        if not p.exists() or p.read_text(encoding="utf-8") != isi
    ]
    assert basi == [], f"jalankan `python -m dol_schema --emit`: {basi}"


def test_npwp_tidak_disimpan():
    """Keputusan 2026.10.3: NPWP tidak dipakai BAST maupun verifikasi PM, jadi tidak disimpan.
    Menambahkannya lagi harus disengaja (ubah tes ini), bukan terbawa diam-diam."""
    for t in ALL_TABLES:
        for c in t.columns:
            assert "npwp" not in c.name.lower(), f"{t.name}.{c.name}"
