-- Delivery Ops Layer — skema companion (tabel yang BERLAKU)
-- Dibangkitkan dari dol_schema/model.py (versi companion-2026.10.3).
-- JANGAN diedit tangan: ubah model.py lalu bangkitkan ulang.

-- Menjaga updated_at tetap benar tanpa bergantung pada aplikasi yang menulis.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Dokumen
-- Setiap berkas yang masuk, apa pun jenisnya.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS document (
    id                         bigserial PRIMARY KEY,
    content_hash               text NOT NULL UNIQUE,
    doc_type                   text NOT NULL,
    source_filename            text NOT NULL,
    page_count                 integer,
    markdown                   text,
    validation_notes           text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT document_doc_type_valid CHECK (doc_type IN ('kontrak', 'sph', 'bast')),
    CONSTRAINT document_page_count_check CHECK (page_count > 0)
);
DROP TRIGGER IF EXISTS trg_document_updated_at ON document;
CREATE TRIGGER trg_document_updated_at BEFORE UPDATE ON document
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE document IS 'Dokumen -- Setiap berkas yang masuk, apa pun jenisnya.';
COMMENT ON COLUMN document.content_hash IS 'Sidik Berkas -- sha256 isi berkas -- kunci anti-dobel; berkas yang sama diproses ulang memperbarui baris yang sama';
COMMENT ON COLUMN document.doc_type IS 'Jenis Dokumen';
COMMENT ON COLUMN document.source_filename IS 'Nama Berkas';
COMMENT ON COLUMN document.page_count IS 'Jumlah Halaman';
COMMENT ON COLUMN document.markdown IS 'Isi Dokumen -- teks hasil pembacaan sistem, agar PM bisa membaca tanpa membuka PDF. Bagian yang rusak OCR bisa sudah dipoles mesin: PDF asli tetap acuan';
COMMENT ON COLUMN document.validation_notes IS 'Catatan Validasi -- peringatan tingkat dokumen, mis. salinan ganda atau jumlah item tidak sama dengan total';
COMMENT ON COLUMN document.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN document.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Kontrak
-- Kontrak/SPK pelanggan dalam bentuk apa pun -- dibaca sekali, dipakai sepanjang proyek (hlm.
-- 11).
-- Sumber kebenaran BAST pelanggan.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS contract (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL UNIQUE REFERENCES document(id) ON DELETE CASCADE,
    mybhakti_project_ref       text,
    contract_type              text,
    contract_number            text,
    contract_number_internal   text,
    work_title                 text,
    location_text              text,
    contract_date_text         text,
    contract_date              date,
    start_date_text            text,
    start_date                 date,
    end_date_text              text,
    end_date                   date,
    duration_text              text,
    contract_value             numeric(18,2),
    subtotal_value             numeric(18,2),
    vat_value                  numeric(18,2),
    vat_percentage             text,
    currency                   char(3) NOT NULL DEFAULT 'IDR',
    payment_mechanism          text,
    penalty_terms              text,
    bast_terms                 text,
    bank_name                  text,
    bank_account_number        text,
    bank_account_name          text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT contract_contract_type_valid CHECK (contract_type IN ('nota_pesanan', 'surat_pesanan', 'spk', 'kontrak_kerja_sama', 'pks', 'lainnya')),
    CONSTRAINT contract_contract_value_check CHECK (contract_value >= 0),
    CONSTRAINT contract_subtotal_value_check CHECK (subtotal_value >= 0),
    CONSTRAINT contract_vat_value_check CHECK (vat_value >= 0)
);
DROP TRIGGER IF EXISTS trg_contract_updated_at ON contract;
CREATE TRIGGER trg_contract_updated_at BEFORE UPDATE ON contract
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE contract IS 'Kontrak -- Kontrak/SPK pelanggan dalam bentuk apa pun -- dibaca sekali, dipakai sepanjang proyek (hlm. 11). Sumber kebenaran BAST pelanggan.';
COMMENT ON COLUMN contract.document_id IS 'ID Dokumen -- satu kontrak = satu dokumen';
COMMENT ON COLUMN contract.mybhakti_project_ref IS 'Rujukan Proyek MyBhakti -- proyek/deal di MyBhakti, diisi n8n -- pengikat semua dokumen satu proyek; sengaja bukan relasi (hlm. 7)';
COMMENT ON COLUMN contract.contract_type IS 'Jenis Kontrak -- bentuk dokumen dasar';
COMMENT ON COLUMN contract.contract_number IS 'Nomor Kontrak -- nomor resmi kontrak / SPK / PKS';
COMMENT ON COLUMN contract.contract_number_internal IS 'Nomor Registrasi Internal -- nomor registrasi internal BUT';
COMMENT ON COLUMN contract.work_title IS 'Nama Pekerjaan -- judul pengadaan / lingkup pekerjaan';
COMMENT ON COLUMN contract.location_text IS 'Lokasi -- kota/lokasi seperti tertulis di kontrak (tempat dibuat atau pelaksanaan)';
COMMENT ON COLUMN contract.contract_date_text IS 'Tanggal Kontrak Tertulis -- apa adanya di dokumen';
COMMENT ON COLUMN contract.contract_date IS 'Tanggal Kontrak -- hasil baca; kosong bila ragu';
COMMENT ON COLUMN contract.start_date_text IS 'Tanggal Mulai Tertulis';
COMMENT ON COLUMN contract.start_date IS 'Tanggal Mulai';
COMMENT ON COLUMN contract.end_date_text IS 'Tanggal Selesai Tertulis';
COMMENT ON COLUMN contract.end_date IS 'Tanggal Selesai';
COMMENT ON COLUMN contract.duration_text IS 'Jangka Waktu -- mis. ''30 hari kalender''';
COMMENT ON COLUMN contract.contract_value IS 'Nilai Kontrak -- total termasuk PPN bila dokumen menyebutnya begitu';
COMMENT ON COLUMN contract.subtotal_value IS 'Subtotal';
COMMENT ON COLUMN contract.vat_value IS 'Nilai PPN';
COMMENT ON COLUMN contract.vat_percentage IS 'Persentase PPN -- apa adanya di dokumen';
COMMENT ON COLUMN contract.currency IS 'Mata Uang';
COMMENT ON COLUMN contract.payment_mechanism IS 'Cara Pembayaran';
COMMENT ON COLUMN contract.penalty_terms IS 'Ketentuan Denda';
COMMENT ON COLUMN contract.bast_terms IS 'Syarat Lampiran BAST -- ringkasan; rincian per syarat ada di tabel Syarat Kontrak';
COMMENT ON COLUMN contract.bank_name IS 'Nama Bank';
COMMENT ON COLUMN contract.bank_account_number IS 'Nomor Rekening';
COMMENT ON COLUMN contract.bank_account_name IS 'Nama Pemilik Rekening';
COMMENT ON COLUMN contract.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN contract.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Pihak Kontrak
-- Pihak penandatangan kontrak seperti tertulis saat diteken -- bukan data master.
-- Satu orang bisa muncul di banyak baris karena menandatangani banyak dokumen.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS contract_party (
    id                         bigserial PRIMARY KEY,
    contract_id                integer NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    role                       text NOT NULL,
    party_label_text           text,
    org_name_text              text NOT NULL,
    signer_name                text,
    signer_title               text,
    org_address_text           text,
    mybhakti_party_ref         text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (contract_id, role),
    CONSTRAINT contract_party_role_valid CHECK (role IN ('pemberi_kerja', 'pelaksana'))
);
CREATE INDEX IF NOT EXISTS idx_contract_party_contract_id ON contract_party(contract_id);
DROP TRIGGER IF EXISTS trg_contract_party_updated_at ON contract_party;
CREATE TRIGGER trg_contract_party_updated_at BEFORE UPDATE ON contract_party
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE contract_party IS 'Pihak Kontrak -- Pihak penandatangan kontrak seperti tertulis saat diteken -- bukan data master. Satu orang bisa muncul di banyak baris karena menandatangani banyak dokumen.';
COMMENT ON COLUMN contract_party.contract_id IS 'ID Kontrak';
COMMENT ON COLUMN contract_party.role IS 'Peran -- pemberi_kerja = pelanggan; pelaksana = BUT. Ditentukan dari nama instansi, bukan dari sebutan ''Pihak Pertama/Kedua''';
COMMENT ON COLUMN contract_party.party_label_text IS 'Sebutan di Dokumen -- mis. ''PIHAK PERTAMA'' -- sebutan ini bisa terbalik antar-format kontrak, karena itu disimpan terpisah dari peran';
COMMENT ON COLUMN contract_party.org_name_text IS 'Nama Instansi';
COMMENT ON COLUMN contract_party.signer_name IS 'Nama Penandatangan -- kosong bila tidak terbaca';
COMMENT ON COLUMN contract_party.signer_title IS 'Jabatan Penandatangan';
COMMENT ON COLUMN contract_party.org_address_text IS 'Alamat';
COMMENT ON COLUMN contract_party.mybhakti_party_ref IS 'Rujukan Pihak MyBhakti -- diisi n8n';
COMMENT ON COLUMN contract_party.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN contract_party.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Rincian Kontrak
-- BoQ kontrak = kewajiban ke pelanggan (hlm.
-- 7).
-- Sumber tunggal rincian pekerjaan untuk BAST pelanggan.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS contract_item (
    id                         bigserial PRIMARY KEY,
    contract_id                integer NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    line_no                    integer NOT NULL,
    category                   text,
    description                text NOT NULL,
    specification              text,
    quantity                   numeric(18,2),
    unit                       text,
    period                     text,
    unit_price                 numeric(18,2),
    line_total                 numeric(18,2),
    remarks                    text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (contract_id, line_no),
    CONSTRAINT contract_item_line_no_check CHECK (line_no > 0),
    CONSTRAINT contract_item_quantity_check CHECK (quantity >= 0),
    CONSTRAINT contract_item_unit_price_check CHECK (unit_price >= 0),
    CONSTRAINT contract_item_line_total_check CHECK (line_total >= 0)
);
CREATE INDEX IF NOT EXISTS idx_contract_item_contract_id ON contract_item(contract_id);
DROP TRIGGER IF EXISTS trg_contract_item_updated_at ON contract_item;
CREATE TRIGGER trg_contract_item_updated_at BEFORE UPDATE ON contract_item
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE contract_item IS 'Rincian Kontrak -- BoQ kontrak = kewajiban ke pelanggan (hlm. 7). Sumber tunggal rincian pekerjaan untuk BAST pelanggan.';
COMMENT ON COLUMN contract_item.contract_id IS 'ID Kontrak';
COMMENT ON COLUMN contract_item.line_no IS 'No Urut -- urutan baca di dokumen';
COMMENT ON COLUMN contract_item.category IS 'Kelompok';
COMMENT ON COLUMN contract_item.description IS 'Uraian';
COMMENT ON COLUMN contract_item.specification IS 'Spesifikasi';
COMMENT ON COLUMN contract_item.quantity IS 'Volume';
COMMENT ON COLUMN contract_item.unit IS 'Satuan';
COMMENT ON COLUMN contract_item.period IS 'Periode';
COMMENT ON COLUMN contract_item.unit_price IS 'Harga Satuan -- selalu dikonfirmasi PM (hlm. 20)';
COMMENT ON COLUMN contract_item.line_total IS 'Jumlah Harga';
COMMENT ON COLUMN contract_item.remarks IS 'Keterangan';
COMMENT ON COLUMN contract_item.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN contract_item.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Syarat Kontrak
-- Aturan dari kontrak, bukan angka: lampiran wajib, syarat serah terima, boleh parsial (hlm.
-- 11).
-- Baris lampiran wajib adalah separuh checklist gabungan BAST.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS contract_requirement (
    id                         bigserial PRIMARY KEY,
    contract_id                integer NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    line_no                    integer NOT NULL,
    requirement_type           text NOT NULL,
    requirement_text           text NOT NULL,
    clause_ref                 text,
    evidence_page              integer,
    evidence_quote             text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (contract_id, line_no),
    CONSTRAINT contract_requirement_line_no_check CHECK (line_no > 0),
    CONSTRAINT contract_requirement_requirement_type_valid CHECK (requirement_type IN ('lampiran_wajib', 'syarat_serah_terima', 'boleh_parsial'))
);
CREATE INDEX IF NOT EXISTS idx_contract_requirement_contract_id ON contract_requirement(contract_id);
DROP TRIGGER IF EXISTS trg_contract_requirement_updated_at ON contract_requirement;
CREATE TRIGGER trg_contract_requirement_updated_at BEFORE UPDATE ON contract_requirement
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE contract_requirement IS 'Syarat Kontrak -- Aturan dari kontrak, bukan angka: lampiran wajib, syarat serah terima, boleh parsial (hlm. 11). Baris lampiran wajib adalah separuh checklist gabungan BAST.';
COMMENT ON COLUMN contract_requirement.contract_id IS 'ID Kontrak';
COMMENT ON COLUMN contract_requirement.line_no IS 'No Urut';
COMMENT ON COLUMN contract_requirement.requirement_type IS 'Jenis Syarat -- lampiran wajib / syarat serah terima / boleh parsial';
COMMENT ON COLUMN contract_requirement.requirement_text IS 'Isi Syarat -- mis. ''Berita Acara Uji Terima''';
COMMENT ON COLUMN contract_requirement.clause_ref IS 'Pasal Rujukan -- mis. ''Pasal 9 ayat 2''';
COMMENT ON COLUMN contract_requirement.evidence_page IS 'Halaman -- halaman tempat syarat ini ditemukan';
COMMENT ON COLUMN contract_requirement.evidence_quote IS 'Kutipan Dokumen -- kutipan pendek agar PM tidak perlu membaca ulang kontrak (hlm. 11)';
COMMENT ON COLUMN contract_requirement.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN contract_requirement.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- SPH Vendor
-- Surat penawaran harga dari vendor (rantai hulu) -- lahir dari kebutuhan kontrak.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS sph (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL UNIQUE REFERENCES document(id) ON DELETE CASCADE,
    mybhakti_project_ref       text,
    mybhakti_vendor_ref        text,
    sph_number                 text,
    sph_date_text              text,
    sph_date                   date,
    project_name               text,
    client_name                text,
    vendor_name                text,
    subtotal_value             numeric(18,2),
    vat_percentage             text,
    vat_value                  numeric(18,2),
    total_price                numeric(18,2),
    validity_text              text,
    payment_mechanism          text,
    currency                   char(3) NOT NULL DEFAULT 'IDR',
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT sph_subtotal_value_check CHECK (subtotal_value >= 0),
    CONSTRAINT sph_vat_value_check CHECK (vat_value >= 0),
    CONSTRAINT sph_total_price_check CHECK (total_price >= 0)
);
DROP TRIGGER IF EXISTS trg_sph_updated_at ON sph;
CREATE TRIGGER trg_sph_updated_at BEFORE UPDATE ON sph
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE sph IS 'SPH Vendor -- Surat penawaran harga dari vendor (rantai hulu) -- lahir dari kebutuhan kontrak.';
COMMENT ON COLUMN sph.document_id IS 'ID Dokumen';
COMMENT ON COLUMN sph.mybhakti_project_ref IS 'Rujukan Proyek MyBhakti -- diisi n8n';
COMMENT ON COLUMN sph.mybhakti_vendor_ref IS 'Rujukan Vendor MyBhakti -- diisi n8n';
COMMENT ON COLUMN sph.sph_number IS 'Nomor SPH';
COMMENT ON COLUMN sph.sph_date_text IS 'Tanggal SPH Tertulis';
COMMENT ON COLUMN sph.sph_date IS 'Tanggal SPH';
COMMENT ON COLUMN sph.project_name IS 'Perihal -- perihal / nama pekerjaan yang ditawarkan';
COMMENT ON COLUMN sph.client_name IS 'Ditujukan Kepada -- instansi yang dituju surat';
COMMENT ON COLUMN sph.vendor_name IS 'Nama Vendor -- penerbit SPH seperti tertulis';
COMMENT ON COLUMN sph.subtotal_value IS 'Subtotal';
COMMENT ON COLUMN sph.vat_percentage IS 'Persentase PPN -- apa adanya di dokumen';
COMMENT ON COLUMN sph.vat_value IS 'Nilai PPN';
COMMENT ON COLUMN sph.total_price IS 'Total Penawaran -- grand total';
COMMENT ON COLUMN sph.validity_text IS 'Masa Berlaku -- masa berlaku penawaran';
COMMENT ON COLUMN sph.payment_mechanism IS 'Cara Pembayaran';
COMMENT ON COLUMN sph.currency IS 'Mata Uang';
COMMENT ON COLUMN sph.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN sph.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Rincian SPH
-- Baris penawaran vendor.
-- Relasi ke barang yang dibeli (procurement item) untuk tabel banding harga dirancang di Bulan 5 -- belum ada di sini.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS sph_item (
    id                         bigserial PRIMARY KEY,
    sph_id                     integer NOT NULL REFERENCES sph(id) ON DELETE CASCADE,
    line_no                    integer NOT NULL,
    category                   text,
    description                text NOT NULL,
    specification              text,
    brand                      text,
    part_number                text,
    quantity                   numeric(18,2),
    unit                       text,
    period                     text,
    unit_price                 numeric(18,2),
    line_total                 numeric(18,2),
    remarks                    text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (sph_id, line_no),
    CONSTRAINT sph_item_line_no_check CHECK (line_no > 0),
    CONSTRAINT sph_item_quantity_check CHECK (quantity >= 0),
    CONSTRAINT sph_item_unit_price_check CHECK (unit_price >= 0),
    CONSTRAINT sph_item_line_total_check CHECK (line_total >= 0)
);
CREATE INDEX IF NOT EXISTS idx_sph_item_sph_id ON sph_item(sph_id);
DROP TRIGGER IF EXISTS trg_sph_item_updated_at ON sph_item;
CREATE TRIGGER trg_sph_item_updated_at BEFORE UPDATE ON sph_item
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE sph_item IS 'Rincian SPH -- Baris penawaran vendor. Relasi ke barang yang dibeli (procurement item) untuk tabel banding harga dirancang di Bulan 5 -- belum ada di sini.';
COMMENT ON COLUMN sph_item.sph_id IS 'ID SPH';
COMMENT ON COLUMN sph_item.line_no IS 'No Urut -- urutan baca, bukan kolom ''No'' di dokumen';
COMMENT ON COLUMN sph_item.category IS 'Kelompok';
COMMENT ON COLUMN sph_item.description IS 'Uraian';
COMMENT ON COLUMN sph_item.specification IS 'Spesifikasi';
COMMENT ON COLUMN sph_item.brand IS 'Merek';
COMMENT ON COLUMN sph_item.part_number IS 'Nomor Part';
COMMENT ON COLUMN sph_item.quantity IS 'Volume';
COMMENT ON COLUMN sph_item.unit IS 'Satuan';
COMMENT ON COLUMN sph_item.period IS 'Periode';
COMMENT ON COLUMN sph_item.unit_price IS 'Harga Satuan -- selalu dikonfirmasi PM (hlm. 20)';
COMMENT ON COLUMN sph_item.line_total IS 'Jumlah Harga';
COMMENT ON COLUMN sph_item.remarks IS 'Keterangan';
COMMENT ON COLUMN sph_item.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN sph_item.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Hasil Ekstraksi
-- Satu baris per field: nilai terbaca + bukti.
-- Antrean kerja PM.
-- Ditulis mesin saja; dokumen yang sudah mulai diperiksa PM tidak ditimpa otomatis.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS extracted_field (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    field_path                 text NOT NULL,
    ai_value_text              text,
    evidence_page              integer,
    evidence_quote             text,
    evidence_score             numeric(18,2),
    system_status              text NOT NULL,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, field_path),
    CONSTRAINT extracted_field_system_status_valid CHECK (system_status IN ('bukti_kuat', 'bukti_cukup', 'perlu_dicek', 'tidak_ada_di_dokumen', 'bertentangan', 'kosong'))
);
CREATE INDEX IF NOT EXISTS idx_extracted_field_document_id ON extracted_field(document_id);
DROP TRIGGER IF EXISTS trg_extracted_field_updated_at ON extracted_field;
CREATE TRIGGER trg_extracted_field_updated_at BEFORE UPDATE ON extracted_field
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE extracted_field IS 'Hasil Ekstraksi -- Satu baris per field: nilai terbaca + bukti. Antrean kerja PM. Ditulis mesin saja; dokumen yang sudah mulai diperiksa PM tidak ditimpa otomatis.';
COMMENT ON COLUMN extracted_field.document_id IS 'ID Dokumen';
COMMENT ON COLUMN extracted_field.field_path IS 'Nama Field -- mis. ''Nomor Kontrak Kerja'' atau ''List Item/Barang[0].Harga Satuan''';
COMMENT ON COLUMN extracted_field.ai_value_text IS 'Nilai Terbaca Sistem';
COMMENT ON COLUMN extracted_field.evidence_page IS 'Halaman Bukti -- dihitung sistem, bukan ditulis LLM';
COMMENT ON COLUMN extracted_field.evidence_quote IS 'Kutipan Bukti -- potongan teks dokumen tempat nilai ditemukan';
COMMENT ON COLUMN extracted_field.evidence_score IS 'Skor Bukti -- 0-1: seberapa persis nilai ditemukan di teks dokumen';
COMMENT ON COLUMN extracted_field.system_status IS 'Status Bukti -- saran sistem, BUKAN persetujuan. Yang diperiksa sistem hanya apakah nilai ada di dokumen, bukan apakah perannya benar';
COMMENT ON COLUMN extracted_field.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN extracted_field.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Keputusan PM
-- Keputusan PM per field (hlm.
-- 11 & 20).
-- Pipeline tidak pernah menulis ke sini.
-- Nilai yang boleh dipakai dokumen hilir hanya yang ada keputusannya di sini.
-- Ditulis oleh: MANUSIA (PM) · pemilik: PM
CREATE TABLE IF NOT EXISTS field_review (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL REFERENCES document(id) ON DELETE RESTRICT,
    field_path                 text NOT NULL,
    reviewed_ai_value_text     text,
    decision                   text NOT NULL,
    final_value_text           text,
    reviewed_by                text NOT NULL,
    reviewed_at                timestamptz NOT NULL,
    reviewer_note              text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, field_path),
    CONSTRAINT field_review_decision_valid CHECK (decision IN ('benar', 'dikoreksi', 'ditolak'))
);
CREATE INDEX IF NOT EXISTS idx_field_review_document_id ON field_review(document_id);
DROP TRIGGER IF EXISTS trg_field_review_updated_at ON field_review;
CREATE TRIGGER trg_field_review_updated_at BEFORE UPDATE ON field_review
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE field_review IS 'Keputusan PM -- Keputusan PM per field (hlm. 11 & 20). Pipeline tidak pernah menulis ke sini. Nilai yang boleh dipakai dokumen hilir hanya yang ada keputusannya di sini.';
COMMENT ON COLUMN field_review.document_id IS 'ID Dokumen -- dokumen dengan keputusan PM tidak boleh terhapus diam-diam';
COMMENT ON COLUMN field_review.field_path IS 'Nama Field';
COMMENT ON COLUMN field_review.reviewed_ai_value_text IS 'Nilai Sistem Saat Diperiksa -- nilai yang DILIHAT PM saat memutuskan; bila nilai sistem berubah, keputusan lama tidak berlaku untuk nilai baru';
COMMENT ON COLUMN field_review.decision IS 'Keputusan';
COMMENT ON COLUMN field_review.final_value_text IS 'Nilai Final -- wajib diisi bila dikoreksi';
COMMENT ON COLUMN field_review.reviewed_by IS 'Diperiksa Oleh';
COMMENT ON COLUMN field_review.reviewed_at IS 'Waktu Diperiksa';
COMMENT ON COLUMN field_review.reviewer_note IS 'Catatan PM';
COMMENT ON COLUMN field_review.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN field_review.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Riwayat Pemrosesan
-- Jejak tiap pemrosesan -- dasar bukti 'Terukur' (hlm.
-- 21).
-- Hanya di PostgreSQL.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS extraction_run (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    ocr_engine                 text,
    llm_model                  text,
    prompt_version             text,
    schema_version             text,
    llm_call_count             integer,
    parse_seconds              numeric(18,2),
    extract_seconds            numeric(18,2),
    validation_status          text,
    started_at                 timestamptz,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_extraction_run_document_id ON extraction_run(document_id);
DROP TRIGGER IF EXISTS trg_extraction_run_updated_at ON extraction_run;
CREATE TRIGGER trg_extraction_run_updated_at BEFORE UPDATE ON extraction_run
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE extraction_run IS 'Riwayat Pemrosesan -- Jejak tiap pemrosesan -- dasar bukti ''Terukur'' (hlm. 21). Hanya di PostgreSQL.';
COMMENT ON COLUMN extraction_run.document_id IS 'ID Dokumen';
COMMENT ON COLUMN extraction_run.ocr_engine IS 'Mesin OCR';
COMMENT ON COLUMN extraction_run.llm_model IS 'Model LLM';
COMMENT ON COLUMN extraction_run.prompt_version IS 'Versi Prompt';
COMMENT ON COLUMN extraction_run.schema_version IS 'Versi Skema';
COMMENT ON COLUMN extraction_run.llm_call_count IS 'Jumlah Panggilan LLM';
COMMENT ON COLUMN extraction_run.parse_seconds IS 'Detik Pembacaan';
COMMENT ON COLUMN extraction_run.extract_seconds IS 'Detik Ekstraksi';
COMMENT ON COLUMN extraction_run.validation_status IS 'Status Validasi';
COMMENT ON COLUMN extraction_run.started_at IS 'Mulai';
COMMENT ON COLUMN extraction_run.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN extraction_run.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- ---------------------------------------------------------------- verifikasi PM
-- Status verifikasi TIDAK disimpan sebagai kolom: ia turunan dari field_review.
-- Menyimpannya berarti ada dua sumber kebenaran yang bisa berbeda.

-- Keputusan PM yang basi: nilai sistem berubah setelah PM memutuskan.
CREATE OR REPLACE VIEW field_review_stale AS
SELECT fr.document_id, fr.field_path,
       fr.reviewed_ai_value_text AS value_saat_dikonfirmasi,
       ef.ai_value_text          AS value_sekarang,
       fr.reviewed_by, fr.reviewed_at
FROM field_review fr
JOIN extracted_field ef
  ON ef.document_id = fr.document_id AND ef.field_path = fr.field_path
WHERE ef.ai_value_text IS DISTINCT FROM fr.reviewed_ai_value_text;

-- Status per dokumen. Keputusan yang basi TIDAK dihitung: dokumen yang nilainya berubah
-- setelah dikonfirmasi kembali menjadi 'sedang_direview', bukan tetap 'terverifikasi_pm'.
CREATE OR REPLACE VIEW document_review_status AS
SELECT
    d.id                                            AS document_id,
    d.source_filename,
    d.doc_type,
    count(ef.id)                                    AS field_count,
    count(fr.id) FILTER (WHERE fr.decision = 'benar'
                         AND ef.ai_value_text IS NOT DISTINCT FROM fr.reviewed_ai_value_text)
                                                    AS confirmed_count,
    count(fr.id) FILTER (WHERE fr.decision = 'dikoreksi'
                         AND ef.ai_value_text IS NOT DISTINCT FROM fr.reviewed_ai_value_text)
                                                    AS corrected_count,
    count(fr.id) FILTER (WHERE ef.ai_value_text IS DISTINCT FROM fr.reviewed_ai_value_text)
                                                    AS stale_count,
    CASE
        WHEN count(ef.id) = 0 THEN 'belum_ada_field'
        WHEN count(fr.id) = 0 THEN 'draf_sistem'
        WHEN count(fr.id) FILTER (WHERE ef.ai_value_text IS NOT DISTINCT FROM
                                        fr.reviewed_ai_value_text) < count(ef.id)
             THEN 'sedang_direview'
        ELSE 'terverifikasi_pm'
    END                                             AS review_status
FROM document d
LEFT JOIN extracted_field ef ON ef.document_id = d.id
LEFT JOIN field_review   fr ON fr.document_id = d.id AND fr.field_path = ef.field_path
GROUP BY d.id, d.source_filename, d.doc_type;

-- Satu-satunya sumber nilai untuk dokumen hilir (mis. penyusunan BAST): hanya field yang
-- sudah diputuskan PM dan keputusannya belum basi. Field yang ditolak atau belum diperiksa
-- TIDAK muncul -- konsumen harus menganggapnya kosong, bukan memakai nilai sistem.
CREATE OR REPLACE VIEW nilai_terverifikasi AS
SELECT fr.document_id, fr.field_path,
       CASE fr.decision WHEN 'dikoreksi' THEN fr.final_value_text
                        ELSE ef.ai_value_text END AS nilai,
       fr.decision, fr.reviewed_by, fr.reviewed_at
FROM field_review fr
JOIN extracted_field ef
  ON ef.document_id = fr.document_id AND ef.field_path = fr.field_path
WHERE fr.decision IN ('benar', 'dikoreksi')
  AND ef.ai_value_text IS NOT DISTINCT FROM fr.reviewed_ai_value_text;
