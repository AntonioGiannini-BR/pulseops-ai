-- Backfill idempotente: calcula prazos apenas para chamados legados sem due_at.
-- Execute somente após conferir as politicas de sla_policies e realizar backup.
-- Não altera prazos que já foram definidos nem a prioridade dos chamados.
BEGIN;

UPDATE tickets AS t
SET due_at = t.opened_at + p.resolution_minutes * INTERVAL '1 minute'
FROM sla_policies AS p
WHERE t.priority = p.priority
  AND t.due_at IS NULL;

COMMIT;
