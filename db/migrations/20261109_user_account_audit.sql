-- PulseOps AI: tabela de auditoria de contas, executavel repetidamente.
-- Para bases ja existentes, aplicar ANTES de subir a API com gestao de contas.
BEGIN;

CREATE TABLE IF NOT EXISTS user_audit_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL,
    target_user_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL,
    action VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_audit_action_valid CHECK (
        action IN ('conta_criada','conta_desativada','conta_reativada','senha_alterada')
    )
);

CREATE INDEX IF NOT EXISTS idx_user_audit_target_date
    ON user_audit_events(target_user_id, created_at DESC);

COMMIT;
