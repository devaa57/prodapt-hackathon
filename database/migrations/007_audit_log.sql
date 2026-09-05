-- Migration 007: Audit Log
-- ============================================================================
-- Append-only table — no UPDATE or DELETE should ever be allowed.
-- Captures who did what, to which entity, and when.
--
-- Design decisions:
--   • old_values / new_values stored as JSONB so any entity change
--     can be audited without schema coupling.
--   • entity_id is a plain UUID (not a FK) because it can reference
--     any table — a polymorphic reference.
--   • No soft-delete on audit_logs: they are immutable records.

BEGIN;

CREATE TABLE audit_logs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID                 REFERENCES organizations(id) ON DELETE SET NULL,
    user_id         UUID                 REFERENCES users(id)         ON DELETE SET NULL,
    action          VARCHAR(100)    NOT NULL,   -- e.g. 'create', 'update', 'delete', 'login'
    entity_type     VARCHAR(100)    NOT NULL,   -- e.g. 'candidate', 'job', 'screening_result'
    entity_id       UUID,                       -- polymorphic; not a FK
    old_values      JSONB,
    new_values      JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- Prevent accidental updates/deletes via a trigger rule.
-- The application should never modify audit rows, but this is a safety net.
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only: UPDATE and DELETE are prohibited';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_no_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

CREATE TRIGGER trg_audit_no_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

COMMIT;
