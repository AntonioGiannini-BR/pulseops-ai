-- Consultas de exemplo, executadas após o banco ser inicializado.

-- 1) Indicadores gerais do dashboard:
SELECT * FROM v_dashboard_kpis;

-- 2) Quantidade de chamados por prioridade:
SELECT priority, COUNT(*) AS quantidade
FROM tickets GROUP BY priority
ORDER BY CASE priority WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END;

-- 3) Chamados por categoria:
SELECT c.name AS categoria, COUNT(t.id) AS quantidade
FROM categories c LEFT JOIN tickets t ON t.category_id = c.id
GROUP BY c.id, c.name ORDER BY quantidade DESC, c.name;

-- 4) Chamados vencidos sem resolução:
SELECT id, title, priority, due_at
FROM v_ticket_sla WHERE sla_status = 'atrasado' ORDER BY due_at;

-- 5) Lista enriquecida para o dashboard:
SELECT t.id, t.title, t.status, t.priority, c.name AS category,
       r.full_name AS requester, COALESCE(a.full_name, 'Não atribuído') AS assignee,
       s.sla_status, t.opened_at
FROM tickets t
JOIN categories c ON c.id=t.category_id
JOIN app_users r ON r.id=t.requester_id
LEFT JOIN app_users a ON a.id=t.assignee_id
JOIN v_ticket_sla s ON s.id=t.id
ORDER BY t.opened_at DESC;
