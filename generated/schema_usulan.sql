-- Delivery Ops Layer — tabel USULAN (status: ditunda)
-- Dibangkitkan dari dol_schema/model.py (versi companion-2026.10.3).
-- Untuk dibahas bersama RPA & Network Engineer. Jalankan SETELAH schema.sql.
-- Tabel: bast, bast_party, bast_item, bast_condition, bast_draft, evidence_photo

-- BAST
-- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema.
-- BAST hasil ekstraksi dokumen lama atau hasil susunan sistem.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS bast (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL UNIQUE REFERENCES document(id) ON DELETE CASCADE,
    direction                  text NOT NULL,
    contract_id                integer REFERENCES contract(id) ON DELETE RESTRICT,
    mybhakti_po_ref            text,
    bast_number_customer       text,
    bast_number_internal       text,
    handover_date_text         text,
    handover_date              date,
    handover_city              text,
    work_title                 text,
    basis_doc_type             text,
    basis_doc_number           text,
    basis_doc_date_text        text,
    basis_doc_date             date,
    basis_doc_value            numeric(18,2),
    basis_doc_value_vat        text,
    currency                   char(3) NOT NULL DEFAULT 'IDR',
    acceptance_statement       text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT bast_direction_valid CHECK (direction IN ('customer', 'vendor', 'unknown')),
    CONSTRAINT bast_basis_doc_type_valid CHECK (basis_doc_type IN ('contract', 'pks', 'spk', 'order_note', 'purchase_order', 'other')),
    CONSTRAINT bast_basis_doc_value_check CHECK (basis_doc_value >= 0),
    CONSTRAINT bast_basis_doc_value_vat_valid CHECK (basis_doc_value_vat IN ('included', 'excluded', 'unstated'))
);
CREATE INDEX IF NOT EXISTS idx_bast_contract_id ON bast(contract_id);
DROP TRIGGER IF EXISTS trg_bast_updated_at ON bast;
CREATE TRIGGER trg_bast_updated_at BEFORE UPDATE ON bast
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE bast IS 'BAST -- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. BAST hasil ekstraksi dokumen lama atau hasil susunan sistem.';
COMMENT ON COLUMN bast.document_id IS 'ID Dokumen';
COMMENT ON COLUMN bast.direction IS 'Arah -- customer = kita->pelanggan (acuan: kontrak); vendor = vendor->kita (acuan: PO) -- hlm. 10';
COMMENT ON COLUMN bast.contract_id IS 'ID Kontrak -- hanya untuk BAST pelanggan';
COMMENT ON COLUMN bast.mybhakti_po_ref IS 'Rujukan PO MyBhakti -- diisi n8n; bukan relasi';
COMMENT ON COLUMN bast.bast_number_customer IS 'Nomor BAST Pelanggan';
COMMENT ON COLUMN bast.bast_number_internal IS 'Nomor BAST Internal -- dari numbering service milik RPA (hlm. 20)';
COMMENT ON COLUMN bast.handover_date_text IS 'Tanggal Serah Terima Tertulis';
COMMENT ON COLUMN bast.handover_date IS 'Tanggal Serah Terima';
COMMENT ON COLUMN bast.handover_city IS 'Kota Serah Terima';
COMMENT ON COLUMN bast.work_title IS 'Nama Pekerjaan';
COMMENT ON COLUMN bast.basis_doc_type IS 'Jenis Dokumen Dasar';
COMMENT ON COLUMN bast.basis_doc_number IS 'Nomor Dokumen Dasar';
COMMENT ON COLUMN bast.basis_doc_date_text IS 'Tanggal Dokumen Dasar Tertulis';
COMMENT ON COLUMN bast.basis_doc_date IS 'Tanggal Dokumen Dasar';
COMMENT ON COLUMN bast.basis_doc_value IS 'Nilai Dokumen Dasar';
COMMENT ON COLUMN bast.basis_doc_value_vat IS 'PPN Nilai Dasar';
COMMENT ON COLUMN bast.currency IS 'Mata Uang';
COMMENT ON COLUMN bast.acceptance_statement IS 'Pernyataan Penerimaan';
COMMENT ON COLUMN bast.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN bast.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Pihak BAST
-- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema.
-- Tepat 2 baris per BAST: penyerah dan penerima.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS bast_party (
    id                         bigserial PRIMARY KEY,
    bast_id                    integer NOT NULL REFERENCES bast(id) ON DELETE CASCADE,
    role                       text NOT NULL,
    org_name_text              text NOT NULL,
    signer_name                text,
    signer_title               text,
    org_address_text           text,
    mybhakti_party_ref         text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bast_id, role),
    CONSTRAINT bast_party_role_valid CHECK (role IN ('handover', 'receiver'))
);
CREATE INDEX IF NOT EXISTS idx_bast_party_bast_id ON bast_party(bast_id);
DROP TRIGGER IF EXISTS trg_bast_party_updated_at ON bast_party;
CREATE TRIGGER trg_bast_party_updated_at BEFORE UPDATE ON bast_party
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE bast_party IS 'Pihak BAST -- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Tepat 2 baris per BAST: penyerah dan penerima.';
COMMENT ON COLUMN bast_party.bast_id IS 'ID BAST';
COMMENT ON COLUMN bast_party.role IS 'Peran -- peran, BUKAN ''Pihak Pertama/Kedua'' -- label itu terbalik antar-format';
COMMENT ON COLUMN bast_party.org_name_text IS 'Nama Instansi';
COMMENT ON COLUMN bast_party.signer_name IS 'Nama Penandatangan -- kosong bila tidak terbaca';
COMMENT ON COLUMN bast_party.signer_title IS 'Jabatan Penandatangan';
COMMENT ON COLUMN bast_party.org_address_text IS 'Alamat';
COMMENT ON COLUMN bast_party.mybhakti_party_ref IS 'Rujukan Pihak MyBhakti';
COMMENT ON COLUMN bast_party.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN bast_party.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Rincian BAST
-- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema.
-- Baris serah terima.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS bast_item (
    id                         bigserial PRIMARY KEY,
    bast_id                    integer NOT NULL REFERENCES bast(id) ON DELETE CASCADE,
    line_no                    integer NOT NULL,
    contract_item_id           integer REFERENCES contract_item(id) ON DELETE RESTRICT,
    description                text NOT NULL,
    quantity                   numeric(18,2),
    unit                       text,
    unit_price                 numeric(18,2),
    line_total                 numeric(18,2),
    test_result                text,
    activation_date_text       text,
    activation_date            date,
    service_order_ref          text,
    service_id                 text,
    location                   text,
    remarks                    text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bast_id, line_no),
    CONSTRAINT bast_item_line_no_check CHECK (line_no > 0),
    CONSTRAINT bast_item_quantity_check CHECK (quantity >= 0),
    CONSTRAINT bast_item_unit_price_check CHECK (unit_price >= 0),
    CONSTRAINT bast_item_line_total_check CHECK (line_total >= 0)
);
CREATE INDEX IF NOT EXISTS idx_bast_item_bast_id ON bast_item(bast_id);
CREATE INDEX IF NOT EXISTS idx_bast_item_contract_item_id ON bast_item(contract_item_id);
DROP TRIGGER IF EXISTS trg_bast_item_updated_at ON bast_item;
CREATE TRIGGER trg_bast_item_updated_at BEFORE UPDATE ON bast_item
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE bast_item IS 'Rincian BAST -- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Baris serah terima.';
COMMENT ON COLUMN bast_item.bast_id IS 'ID BAST';
COMMENT ON COLUMN bast_item.line_no IS 'No Urut';
COMMENT ON COLUMN bast_item.contract_item_id IS 'ID Rincian Kontrak -- baris BoQ kontrak yang diserahkan; uraian & harga dibaca dari kontrak';
COMMENT ON COLUMN bast_item.description IS 'Uraian';
COMMENT ON COLUMN bast_item.quantity IS 'Volume -- volume yang DISERAHKAN -- bisa lebih kecil dari kontrak bila parsial';
COMMENT ON COLUMN bast_item.unit IS 'Satuan';
COMMENT ON COLUMN bast_item.unit_price IS 'Harga Satuan';
COMMENT ON COLUMN bast_item.line_total IS 'Jumlah Harga';
COMMENT ON COLUMN bast_item.test_result IS 'Hasil Uji -- diisi setelah uji, bukan sebelumnya';
COMMENT ON COLUMN bast_item.activation_date_text IS 'Tanggal Aktif Tertulis';
COMMENT ON COLUMN bast_item.activation_date IS 'Tanggal Aktif';
COMMENT ON COLUMN bast_item.service_order_ref IS 'Nomor AO';
COMMENT ON COLUMN bast_item.service_id IS 'SID';
COMMENT ON COLUMN bast_item.location IS 'Lokasi';
COMMENT ON COLUMN bast_item.remarks IS 'Keterangan';
COMMENT ON COLUMN bast_item.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN bast_item.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Kondisi BAST
-- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema.
-- Fakta tambahan BAST sebagai baris, bukan kolom baru.
-- Ditulis oleh: mesin (pipeline) · pemilik: AI Engineer
CREATE TABLE IF NOT EXISTS bast_condition (
    id                         bigserial PRIMARY KEY,
    bast_id                    integer NOT NULL REFERENCES bast(id) ON DELETE CASCADE,
    condition_type             text NOT NULL,
    value_text                 text,
    value_number               numeric(18,2),
    value_date                 date,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT bast_condition_condition_type_valid CHECK (condition_type IN ('progress_percent', 'service_active_since', 'acceptance_test_ref', 'delivery_reconciliation_ref', 'supporting_document', 'amount_in_words'))
);
CREATE INDEX IF NOT EXISTS idx_bast_condition_bast_id ON bast_condition(bast_id);
DROP TRIGGER IF EXISTS trg_bast_condition_updated_at ON bast_condition;
CREATE TRIGGER trg_bast_condition_updated_at BEFORE UPDATE ON bast_condition
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE bast_condition IS 'Kondisi BAST -- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Fakta tambahan BAST sebagai baris, bukan kolom baru.';
COMMENT ON COLUMN bast_condition.bast_id IS 'ID BAST';
COMMENT ON COLUMN bast_condition.condition_type IS 'Jenis Kondisi';
COMMENT ON COLUMN bast_condition.value_text IS 'Nilai Teks';
COMMENT ON COLUMN bast_condition.value_number IS 'Nilai Angka';
COMMENT ON COLUMN bast_condition.value_date IS 'Nilai Tanggal';
COMMENT ON COLUMN bast_condition.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN bast_condition.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Draf BAST
-- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema.
-- Belum punya kunci anti-dobel: wajib diputuskan sebelum berlaku, karena tanpa kunci, pengiriman ulang menghapus persetujuan PM.
-- Ditulis oleh: mesin (pipeline) · pemilik: RPA Engineer
-- Kolom yang HANYA diisi PM: approved_by, approved_at
CREATE TABLE IF NOT EXISTS bast_draft (
    id                         bigserial PRIMARY KEY,
    contract_id                integer NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    draft_bast_number          text,
    work_title                 text NOT NULL,
    handover_date_text         text,
    handover_date              date,
    handover_city              text,
    status                     text NOT NULL,
    template_name              text,
    acceptance_statement       text,
    generated_doc_url          text,
    generated_bast_id          integer REFERENCES bast(id) ON DELETE RESTRICT,
    approved_by                text,
    approved_at                timestamptz,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT bast_draft_status_valid CHECK (status IN ('draft', 'pending_review', 'approved', 'generated', 'rejected'))
);
CREATE INDEX IF NOT EXISTS idx_bast_draft_contract_id ON bast_draft(contract_id);
CREATE INDEX IF NOT EXISTS idx_bast_draft_generated_bast_id ON bast_draft(generated_bast_id);
DROP TRIGGER IF EXISTS trg_bast_draft_updated_at ON bast_draft;
CREATE TRIGGER trg_bast_draft_updated_at BEFORE UPDATE ON bast_draft
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE bast_draft IS 'Draf BAST -- DITUNDA: dirancang bersama RPA (nomor & render) dan Network Engineer (lampiran) di workshop skema. Belum punya kunci anti-dobel: wajib diputuskan sebelum berlaku, karena tanpa kunci, pengiriman ulang menghapus persetujuan PM.';
COMMENT ON COLUMN bast_draft.contract_id IS 'ID Kontrak';
COMMENT ON COLUMN bast_draft.draft_bast_number IS 'Nomor Draf';
COMMENT ON COLUMN bast_draft.work_title IS 'Nama Pekerjaan';
COMMENT ON COLUMN bast_draft.handover_date_text IS 'Tanggal Serah Terima Tertulis';
COMMENT ON COLUMN bast_draft.handover_date IS 'Tanggal Serah Terima';
COMMENT ON COLUMN bast_draft.handover_city IS 'Kota Serah Terima';
COMMENT ON COLUMN bast_draft.status IS 'Status';
COMMENT ON COLUMN bast_draft.template_name IS 'Template';
COMMENT ON COLUMN bast_draft.acceptance_statement IS 'Pernyataan Penerimaan';
COMMENT ON COLUMN bast_draft.generated_doc_url IS 'Tautan Dokumen';
COMMENT ON COLUMN bast_draft.generated_bast_id IS 'ID BAST Tercetak';
COMMENT ON COLUMN bast_draft.approved_by IS 'Disetujui Oleh';
COMMENT ON COLUMN bast_draft.approved_at IS 'Waktu Disetujui';
COMMENT ON COLUMN bast_draft.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN bast_draft.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- Foto Evidence
-- DITUNDA: usulan untuk disepakati dengan Network Engineer (dol-odk & dol-bast-compiler, hlm.
-- 15).
-- Lampiran wajib kontrak sering berupa DOKUMEN (BA uji terima, surat jalan), bukan foto -- bentuk tabel bukti perlu dibahas bersama.
-- Ditulis oleh: mesin (pipeline) · pemilik: Network Engineer
-- Kolom yang HANYA diisi PM: review_status, reviewed_by, reviewed_at, review_note
CREATE TABLE IF NOT EXISTS evidence_photo (
    id                         bigserial PRIMARY KEY,
    odk_instance_id            text NOT NULL UNIQUE,
    contract_item_id           integer NOT NULL REFERENCES contract_item(id) ON DELETE RESTRICT,
    requirement_id             integer REFERENCES contract_requirement(id) ON DELETE RESTRICT,
    component_label            text,
    photo_type                 text NOT NULL,
    serial_number              text,
    photo_url                  text NOT NULL,
    taken_at                   timestamptz NOT NULL,
    gps_lat                    numeric(9,6),
    gps_lon                    numeric(9,6),
    auto_check_notes           text,
    review_status              text NOT NULL DEFAULT 'pending',
    reviewed_by                text,
    reviewed_at                timestamptz,
    review_note                text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT evidence_photo_photo_type_valid CHECK (photo_type IN ('item', 'serial_label', 'installation', 'screenshot')),
    CONSTRAINT evidence_photo_review_status_valid CHECK (review_status IN ('pending', 'approved', 'rejected'))
);
CREATE INDEX IF NOT EXISTS idx_evidence_photo_contract_item_id ON evidence_photo(contract_item_id);
CREATE INDEX IF NOT EXISTS idx_evidence_photo_requirement_id ON evidence_photo(requirement_id);
DROP TRIGGER IF EXISTS trg_evidence_photo_updated_at ON evidence_photo;
CREATE TRIGGER trg_evidence_photo_updated_at BEFORE UPDATE ON evidence_photo
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE evidence_photo IS 'Foto Evidence -- DITUNDA: usulan untuk disepakati dengan Network Engineer (dol-odk & dol-bast-compiler, hlm. 15). Lampiran wajib kontrak sering berupa DOKUMEN (BA uji terima, surat jalan), bukan foto -- bentuk tabel bukti perlu dibahas bersama.';
COMMENT ON COLUMN evidence_photo.odk_instance_id IS 'ID Kiriman ODK -- sinkron ulang = pembaruan, bukan baris kembar';
COMMENT ON COLUMN evidence_photo.contract_item_id IS 'ID Rincian Kontrak';
COMMENT ON COLUMN evidence_photo.requirement_id IS 'ID Syarat Kontrak';
COMMENT ON COLUMN evidence_photo.component_label IS 'Komponen -- mis. ''4 Unit Switch''';
COMMENT ON COLUMN evidence_photo.photo_type IS 'Jenis Foto';
COMMENT ON COLUMN evidence_photo.serial_number IS 'Nomor Seri';
COMMENT ON COLUMN evidence_photo.photo_url IS 'Tautan Foto';
COMMENT ON COLUMN evidence_photo.taken_at IS 'Waktu Foto';
COMMENT ON COLUMN evidence_photo.gps_lat IS 'Lintang';
COMMENT ON COLUMN evidence_photo.gps_lon IS 'Bujur';
COMMENT ON COLUMN evidence_photo.auto_check_notes IS 'Catatan Cek Otomatis';
COMMENT ON COLUMN evidence_photo.review_status IS 'Status Review';
COMMENT ON COLUMN evidence_photo.reviewed_by IS 'Diperiksa Oleh';
COMMENT ON COLUMN evidence_photo.reviewed_at IS 'Waktu Diperiksa';
COMMENT ON COLUMN evidence_photo.review_note IS 'Catatan Review';
COMMENT ON COLUMN evidence_photo.created_at IS 'Dibuat -- UTC';
COMMENT ON COLUMN evidence_photo.updated_at IS 'Diperbarui -- UTC, diperbarui trigger';

-- ---------------------------------------------------------------- penyusunan BAST (usulan)
-- Rincian BAST: uraian, spesifikasi, harga DARI KONTRAK bila baris BAST menunjuk
-- contract_item. Volume diambil dari BAST lebih dulu: serah terima parsial menyerahkan
-- volume yang lebih kecil dari kontrak.
CREATE OR REPLACE VIEW bast_rincian AS
SELECT bi.bast_id, b.contract_id, bi.line_no,
       COALESCE(ci.description, bi.description) AS description,
       ci.specification,
       COALESCE(bi.quantity, ci.quantity)       AS quantity,
       COALESCE(ci.unit, bi.unit)               AS unit,
       COALESCE(ci.unit_price, bi.unit_price)   AS unit_price,
       bi.activation_date, bi.service_order_ref, bi.service_id, bi.location, bi.test_result
FROM bast_item bi
JOIN bast b                ON b.id = bi.bast_id
LEFT JOIN contract_item ci ON ci.id = bi.contract_item_id;

-- Lampiran evidence: HANYA foto yang sudah disetujui PM, dikelompokkan per baris BoQ.
CREATE OR REPLACE VIEW evidence_siap_lampiran AS
SELECT ci.contract_id, ci.line_no, ci.description AS item_description,
       ep.component_label, ep.photo_type, ep.serial_number,
       ep.photo_url, ep.taken_at, ep.gps_lat, ep.gps_lon
FROM evidence_photo ep
JOIN contract_item ci ON ci.id = ep.contract_item_id
WHERE ep.review_status = 'approved';

-- Checklist gabungan (hlm. 15): tiap lampiran wajib kontrak + status buktinya.
CREATE OR REPLACE VIEW checklist_gabungan AS
SELECT cr.contract_id, cr.line_no, cr.requirement_text, cr.clause_ref,
       count(ep.id) FILTER (WHERE ep.review_status = 'approved') AS bukti_disetujui,
       count(ep.id) FILTER (WHERE ep.review_status = 'pending')  AS bukti_menunggu,
       CASE WHEN count(ep.id) FILTER (WHERE ep.review_status = 'approved') > 0
            THEN 'terpenuhi' ELSE 'belum' END                     AS status
FROM contract_requirement cr
LEFT JOIN evidence_photo ep ON ep.requirement_id = cr.id
WHERE cr.requirement_type = 'lampiran_wajib'
GROUP BY cr.contract_id, cr.line_no, cr.requirement_text, cr.clause_ref;
