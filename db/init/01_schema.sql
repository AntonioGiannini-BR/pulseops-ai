-- PulseOps AI | Semana 1 | Estrutura do banco PostgreSQL 17
-- Este script é executado APENAS na primeira criação do volume Docker.
-- Execute em um banco novo. Evoluções futuras devem usar migrations.
BEGIN;

CREATE TABLE departments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT departments_name_not_blank CHECK (LENGTH(BTRIM(name)) > 0)
);

CREATE TABLE app_users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'solicitante',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_role_valid CHECK (role IN ('admin', 'analista', 'solicitante')),
    CONSTRAINT users_name_not_blank CHECK (LENGTH(BTRIM(full_name)) > 0),
    CONSTRAINT users_email_not_blank CHECK (LENGTH(BTRIM(email)) > 0)
);
CREATE UNIQUE INDEX app_users_email_lower_uq ON app_users (LOWER(email));
CREATE INDEX idx_app_users_department ON app_users(department_id);

CREATE TABLE categories (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(90) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- SLA inicial usa horas CORRIDAS, não dias úteis. Regra será implementada na API.
CREATE TABLE sla_policies (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    priority VARCHAR(12) NOT NULL UNIQUE,
    resolution_minutes INTEGER NOT NULL,
    CONSTRAINT sla_valid_priority CHECK (priority IN ('baixa','media','alta','critica')),
    CONSTRAINT sla_resolution_positive CHECK (resolution_minutes > 0)
);

CREATE TABLE tickets (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(180) NOT NULL,
    description TEXT NOT NULL,
    requester_id BIGINT NOT NULL REFERENCES app_users(id) ON DELETE RESTRICT,
    assignee_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL,
    department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    priority VARCHAR(12) NOT NULL DEFAULT 'media',
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tickets_priority_valid CHECK (priority IN ('baixa','media','alta','critica')),
    CONSTRAINT tickets_status_valid CHECK (status IN ('aberto','em_triagem','em_atendimento','resolvido','fechado')),
    CONSTRAINT tickets_title_not_blank CHECK (LENGTH(BTRIM(title)) > 0),
    CONSTRAINT tickets_description_not_blank CHECK (LENGTH(BTRIM(description)) > 0),
    CONSTRAINT tickets_due_after_open CHECK (due_at IS NULL OR due_at >= opened_at),
    CONSTRAINT tickets_resolved_after_open CHECK (resolved_at IS NULL OR resolved_at >= opened_at),
    CONSTRAINT tickets_closed_after_resolved CHECK (closed_at IS NULL OR (resolved_at IS NOT NULL AND closed_at >= resolved_at)),
    CONSTRAINT tickets_completed_has_resolution CHECK (
        status NOT IN ('resolvido','fechado') OR resolved_at IS NOT NULL
    ),
    CONSTRAINT tickets_closed_has_close_time CHECK (status <> 'fechado' OR closed_at IS NOT NULL)
);
CREATE INDEX idx_tickets_requester ON tickets(requester_id);
CREATE INDEX idx_tickets_assignee ON tickets(assignee_id);
CREATE INDEX idx_tickets_department ON tickets(department_id);
CREATE INDEX idx_tickets_category ON tickets(category_id);
CREATE INDEX idx_tickets_status_priority ON tickets(status, priority);
CREATE INDEX idx_tickets_opened_at ON tickets(opened_at DESC);
CREATE INDEX idx_tickets_due_at ON tickets(due_at) WHERE status NOT IN ('resolvido','fechado');

CREATE TABLE ticket_comments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES app_users(id) ON DELETE RESTRICT,
    body TEXT NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ticket_comments_not_blank CHECK (LENGTH(BTRIM(body)) > 0)
);
CREATE INDEX idx_comments_ticket_date ON ticket_comments(ticket_id, created_at);

CREATE TABLE ticket_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    actor_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL,
    action VARCHAR(40) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ticket_history_action_not_blank CHECK (LENGTH(BTRIM(action)) > 0)
);
CREATE INDEX idx_history_ticket_date ON ticket_history(ticket_id, created_at);

-- Sugestões da IA nunca são aplicadas automaticamente: revisão por pessoa responsável.
CREATE TABLE ai_suggestions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    suggested_category_id BIGINT REFERENCES categories(id) ON DELETE SET NULL,
    suggested_priority VARCHAR(12),
    summary TEXT,
    rationale TEXT,
    model_name VARCHAR(100),
    review_status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    reviewed_by_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_priority_valid CHECK (suggested_priority IS NULL OR suggested_priority IN ('baixa','media','alta','critica')),
    CONSTRAINT ai_review_status_valid CHECK (review_status IN ('pendente','aprovada','rejeitada')),
    CONSTRAINT ai_review_pair_valid CHECK (
        (review_status = 'pendente' AND reviewed_by_id IS NULL AND reviewed_at IS NULL)
        OR (review_status IN ('aprovada','rejeitada') AND reviewed_by_id IS NOT NULL AND reviewed_at IS NOT NULL)
    )
);
CREATE INDEX idx_ai_suggestions_ticket ON ai_suggestions(ticket_id, created_at DESC);

COMMENT ON TABLE app_users IS 'Contas de usuários; nunca armazenar senhas em texto puro';
COMMENT ON COLUMN tickets.due_at IS 'Prazo calculado pela API usando sla_policies e horas corridas';
COMMENT ON COLUMN ai_suggestions.review_status IS 'Sugestões requerem aprovação humana antes de qualquer mudança';

CREATE VIEW v_ticket_sla AS
SELECT
    t.id, t.title, t.priority, t.status, t.opened_at, t.due_at, t.resolved_at,
    CASE
        WHEN t.due_at IS NULL THEN 'sem_prazo'
        WHEN t.resolved_at IS NOT NULL AND t.resolved_at > t.due_at THEN 'fora_do_prazo'
        WHEN t.resolved_at IS NOT NULL AND t.resolved_at <= t.due_at THEN 'dentro_do_prazo'
        WHEN NOW() > t.due_at THEN 'atrasado'
        ELSE 'em_dia'
    END AS sla_status
FROM tickets t;

CREATE VIEW v_dashboard_kpis AS
SELECT
    COUNT(*) AS total_chamados,
    COUNT(*) FILTER (WHERE status IN ('aberto','em_triagem','em_atendimento')) AS chamados_pendentes,
    COUNT(*) FILTER (WHERE status IN ('resolvido','fechado')) AS chamados_concluidos,
    COUNT(*) FILTER (WHERE sla_status IN ('atrasado','fora_do_prazo')) AS chamados_fora_sla,
    ROUND((AVG(EXTRACT(EPOCH FROM (resolved_at - opened_at)) / 3600.0)
        FILTER (WHERE resolved_at IS NOT NULL))::NUMERIC, 2) AS horas_medias_resolucao
FROM v_ticket_sla;

COMMIT;
