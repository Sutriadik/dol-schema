-- Open ADE — Companion data model untuk NocoDB
-- Dibangkitkan dari app/companion/model.py (versi companion-2026.09.1).
-- JANGAN diedit tangan: ubah model.py lalu bangkitkan ulang.

-- Menjaga updated_at tetap benar tanpa bergantung pada aplikasi yang menulis.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Supertipe: setiap berkas yang masuk, apa pun jenisnya.
-- Ditulis oleh: mesin (pipeline)
CREATE TABLE IF NOT EXISTS document (
    id                         bigserial PRIMARY KEY,
    content_hash               text NOT NULL UNIQUE,
    doc_type                   text NOT NULL,
    source_filename            text NOT NULL,
    page_count                 integer,
    markdown                   text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT document_doc_type_valid CHECK (doc_type IN ('contract', 'sph', 'bast')),
    CONSTRAINT document_page_count_check CHECK (page_count > 0)
);
DROP TRIGGER IF EXISTS trg_document_updated_at ON document;
CREATE TRIGGER trg_document_updated_at BEFORE UPDATE ON document
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Subtipe Kontrak/SPK/PKS sebagai sumber data utama penyusunan draf BAST.
-- Ditulis oleh: mesin (pipeline)
CREATE TABLE IF NOT EXISTS contract (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL UNIQUE REFERENCES document(id) ON DELETE CASCADE,
    contract_number            text,
    contract_number_internal   text,
    work_title                 text NOT NULL,
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
    CONSTRAINT contract_contract_value_check CHECK (contract_value >= 0),
    CONSTRAINT contract_subtotal_value_check CHECK (subtotal_value >= 0),
    CONSTRAINT contract_vat_value_check CHECK (vat_value >= 0)
);
DROP TRIGGER IF EXISTS trg_contract_updated_at ON contract;
CREATE TRIGGER trg_contract_updated_at BEFORE UPDATE ON contract
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Pihak penandatangan dalam kontrak.
-- Ditulis oleh: mesin (pipeline)
CREATE TABLE IF NOT EXISTS contract_party (
    id                         bigserial PRIMARY KEY,
    contract_id                integer NOT NULL REFERENCES contract(id) ON DELETE CASCADE,
    role                       text NOT NULL,
    org_name_text              text NOT NULL,
    signer_name                text NOT NULL,
    signer_title               text,
    org_address_text           text,
    npwp                       text,
    mybhakti_party_ref         text,
    created_at                 timestamptz NOT NULL DEFAULT now(),
    updated_at                 timestamptz NOT NULL DEFAULT now(),
    UNIQUE (contract_id, role),
    CONSTRAINT contract_party_role_valid CHECK (role IN ('first_party', 'second_party', 'client', 'contractor'))
);
CREATE INDEX IF NOT EXISTS idx_contract_party_contract_id ON contract_party(contract_id);
DROP TRIGGER IF EXISTS trg_contract_party_updated_at ON contract_party;
CREATE TRIGGER trg_contract_party_updated_at BEFORE UPDATE ON contract_party
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Tabel Rincian Pekerjaan / BoQ Kontrak.
-- Disimpan untuk direplikasi 1-to-1 persis ke BAST.
-- Ditulis oleh: mesin (pipeline)
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

-- Ekstraksi Surat Penawaran Harga (SPH) sebagai dokumen hulu.
-- Ditulis oleh: mesin (pipeline)
CREATE TABLE IF NOT EXISTS sph (
    id                         bigserial PRIMARY KEY,
    document_id                integer NOT NULL UNIQUE REFERENCES document(id) ON DELETE CASCADE,
    sph_number                 text,
    sph_date_text              text,
    sph_date                   date,
    project_name               text,
    client_name                text,
    vendor_name                text,
    vendor_npwp                text,
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

-- BoQ penawaran vendor.
-- Dasar price matching & tabel banding antar-vendor (briefing hlm.
-- 14, Bulan 3 & 5) -- tanpa tabel ini, perbandingan harga per baris tidak mungkin dilakukan.
-- Ditulis oleh: mesin (pipeline)
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

-- Jejak tiap pemrosesan -- dasar bukti 'Terukur' (briefing hlm.
-- 21).
-- Tetap di PostgreSQL untuk audit internal, TIDAK pernah dikirim ke NocoDB: arahan Delivery Ops, NocoDB hanya memuat nilai ekstraksi + confidence score, bukan metadata teknis AI (engine OCR, model LLM, runtime).
-- Ditulis oleh: mesin (pipeline)
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

-- Subtipe BAST.
-- Kolom di sini hanya butir Tier 1-2 (selalu/hampir selalu ada).
-- Ditulis oleh: mesin (pipeline)
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
    work_title                 text NOT NULL,
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

-- Tepat 2 baris per BAST.
-- Cuplikan saat penandatanganan -- jabatan berubah, dokumen yang sudah diteken tidak boleh ikut berubah.
-- Ditulis oleh: mesin (pipeline)
CREATE TABLE IF NOT EXISTS bast_party (
    id                         bigserial PRIMARY KEY,
    bast_id                    integer NOT NULL REFERENCES bast(id) ON DELETE CASCADE,
    role                       text NOT NULL,
    org_name_text              text NOT NULL,
    signer_name                text NOT NULL,
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

-- Harga boleh NULL: format kampus/vendor/instansi tidak memuatnya.
-- Ditulis oleh: mesin (pipeline)
CREATE TABLE IF NOT EXISTS bast_item (
    id                         bigserial PRIMARY KEY,
    bast_id                    integer NOT NULL REFERENCES bast(id) ON DELETE CASCADE,
    line_no                    integer NOT NULL,
    description                text NOT NULL,
    quantity                   numeric(18,2),
    unit                       text,
    unit_price                 numeric(18,2),
    line_total                 numeric(18,2),
    test_result                text,
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
DROP TRIGGER IF EXISTS trg_bast_item_updated_at ON bast_item;
CREATE TRIGGER trg_bast_item_updated_at BEFORE UPDATE ON bast_item
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Fakta Tier 3 sebagai BARIS.
-- Fakta baru = nilai condition_type baru, bukan kolom baru.
-- Ditulis oleh: mesin (pipeline)
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

-- Ditulis MESIN saja.
-- Nilai terbaru per field.
-- Ditulis oleh: mesin (pipeline)
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
    CONSTRAINT extracted_field_system_status_valid CHECK (system_status IN ('auto_verified', 'auto_accepted', 'review_required', 'unsupported', 'conflict', 'missing'))
);
CREATE INDEX IF NOT EXISTS idx_extracted_field_document_id ON extracted_field(document_id);
DROP TRIGGER IF EXISTS trg_extracted_field_updated_at ON extracted_field;
CREATE TRIGGER trg_extracted_field_updated_at BEFORE UPDATE ON extracted_field
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Ditulis MANUSIA saja.
-- Pipeline tidak pernah menulis ke sini (hlm.
-- 11 & 20).
-- Ditulis oleh: MANUSIA (PM)
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
    CONSTRAINT field_review_decision_valid CHECK (decision IN ('confirmed', 'corrected', 'rejected'))
);
CREATE INDEX IF NOT EXISTS idx_field_review_document_id ON field_review(document_id);
DROP TRIGGER IF EXISTS trg_field_review_updated_at ON field_review;
CREATE TRIGGER trg_field_review_updated_at BEFORE UPDATE ON field_review
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Draf BAST yang di-generate otomatis dari data Kontrak/SPH setelah diverifikasi PM.
-- Ditulis oleh: mesin (pipeline)
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

-- Status verifikasi TIDAK disimpan sebagai kolom: ia turunan dari field_review.
-- Menyimpannya berarti ada dua sumber kebenaran yang bisa berbeda.
CREATE OR REPLACE VIEW document_review_status AS
SELECT
    d.id                                            AS document_id,
    d.source_filename,
    d.doc_type,
    count(ef.id)                                    AS field_count,
    count(fr.id) FILTER (WHERE fr.decision = 'confirmed') AS confirmed_count,
    count(fr.id) FILTER (WHERE fr.decision = 'corrected') AS corrected_count,
    CASE
        WHEN count(ef.id) = 0 THEN 'no_fields'
        WHEN count(fr.id) = 0 THEN 'draft_ai'
        WHEN count(fr.id) < count(ef.id) THEN 'in_review'
        ELSE 'verified_by_pm'
    END                                             AS review_status
FROM document d
LEFT JOIN extracted_field ef ON ef.document_id = d.id
LEFT JOIN field_review   fr ON fr.document_id = d.id AND fr.field_path = ef.field_path
GROUP BY d.id, d.source_filename, d.doc_type;

-- Field yang konfirmasinya basi: nilai AI berubah setelah PM memutuskan.
CREATE OR REPLACE VIEW field_review_stale AS
SELECT fr.document_id, fr.field_path,
       fr.reviewed_ai_value_text AS value_saat_dikonfirmasi,
       ef.ai_value_text          AS value_sekarang,
       fr.reviewed_by, fr.reviewed_at
FROM field_review fr
JOIN extracted_field ef
  ON ef.document_id = fr.document_id AND ef.field_path = fr.field_path
WHERE ef.ai_value_text IS DISTINCT FROM fr.reviewed_ai_value_text;
