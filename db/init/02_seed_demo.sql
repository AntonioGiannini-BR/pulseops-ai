-- DADOS FICTÍCIOS. NENHUMA CONTA ABAIXO CONSEGUE AUTENTICAR.
-- Todas têm is_active = false e password_hash = 'DISABLED_DEMO_ACCOUNT'.
-- A autenticação real será implementada na semana 2.
BEGIN;

INSERT INTO departments (name) VALUES
  ('Tecnologia'), ('Financeiro'), ('Comercial'), ('Operações');

INSERT INTO categories (name, description) VALUES
  ('Infraestrutura', 'Redes, servidores, acessos e disponibilidade'),
  ('Sistemas', 'Aplicações e integrações internas'),
  ('Acessos', 'Permissões e credenciais'),
  ('Equipamentos', 'Computadores, periféricos e dispositivos'),
  ('Outros', 'Demais solicitações operacionais');

INSERT INTO sla_policies (priority, resolution_minutes) VALUES
  ('critica', 60), ('alta', 240), ('media', 1440), ('baixa', 4320);

INSERT INTO app_users (department_id, full_name, email, password_hash, role, is_active) VALUES
  ((SELECT id FROM departments WHERE name='Tecnologia'), 'Marina Oliveira', 'marina@pulseops.example', 'DISABLED_DEMO_ACCOUNT', 'admin', false),
  ((SELECT id FROM departments WHERE name='Tecnologia'), 'Rafael Costa', 'rafael@pulseops.example', 'DISABLED_DEMO_ACCOUNT', 'analista', false),
  ((SELECT id FROM departments WHERE name='Tecnologia'), 'Bruna Nascimento', 'bruna@pulseops.example', 'DISABLED_DEMO_ACCOUNT', 'analista', false),
  ((SELECT id FROM departments WHERE name='Comercial'), 'Ana Lima', 'ana@pulseops.example', 'DISABLED_DEMO_ACCOUNT', 'solicitante', false),
  ((SELECT id FROM departments WHERE name='Financeiro'), 'Pedro Souza', 'pedro@pulseops.example', 'DISABLED_DEMO_ACCOUNT', 'solicitante', false),
  ((SELECT id FROM departments WHERE name='Operações'), 'Camila Alves', 'camila@pulseops.example', 'DISABLED_DEMO_ACCOUNT', 'solicitante', false);

-- Horários relativos à inicialização: os indicadores de SLA mudarão com a passagem do tempo.
INSERT INTO tickets (title, description, requester_id, assignee_id, department_id, category_id, priority, status, opened_at, due_at, resolved_at, closed_at) VALUES
  ('Sistema de vendas indisponível', 'Usuários não conseguem finalizar pedidos na filial.',
    (SELECT id FROM app_users WHERE email='ana@pulseops.example'),
    (SELECT id FROM app_users WHERE email='rafael@pulseops.example'),
    (SELECT id FROM departments WHERE name='Comercial'),
    (SELECT id FROM categories WHERE name='Sistemas'),
    'critica','em_atendimento', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', NULL, NULL),
  ('Erro de acesso ao portal financeiro', 'Equipe recebe mensagem de permissão negada.',
    (SELECT id FROM app_users WHERE email='pedro@pulseops.example'),
    (SELECT id FROM app_users WHERE email='bruna@pulseops.example'),
    (SELECT id FROM departments WHERE name='Financeiro'),
    (SELECT id FROM categories WHERE name='Acessos'),
    'alta','em_triagem', NOW() - INTERVAL '1 hour', NOW() + INTERVAL '3 hours', NULL, NULL),
  ('Impressora do setor não responde', 'O dispositivo deixou de aparecer na rede.',
    (SELECT id FROM app_users WHERE email='camila@pulseops.example'),
    (SELECT id FROM app_users WHERE email='rafael@pulseops.example'),
    (SELECT id FROM departments WHERE name='Operações'),
    (SELECT id FROM categories WHERE name='Equipamentos'),
    'baixa','aberto', NOW() - INTERVAL '2 hours', NOW() + INTERVAL '70 hours', NULL, NULL),
  ('Oscilação na rede corporativa', 'Conexões intermitentes em estações de trabalho.',
    (SELECT id FROM app_users WHERE email='ana@pulseops.example'),
    (SELECT id FROM app_users WHERE email='rafael@pulseops.example'),
    (SELECT id FROM departments WHERE name='Comercial'),
    (SELECT id FROM categories WHERE name='Infraestrutura'),
    'alta','resolvido', NOW() - INTERVAL '9 hours', NOW() - INTERVAL '5 hours', NOW() - INTERVAL '6 hours', NULL),
  ('Integração do ERP falhando', 'Sincronização de pedidos interrompida.',
    (SELECT id FROM app_users WHERE email='pedro@pulseops.example'),
    (SELECT id FROM app_users WHERE email='bruna@pulseops.example'),
    (SELECT id FROM departments WHERE name='Financeiro'),
    (SELECT id FROM categories WHERE name='Sistemas'),
    'media','resolvido', NOW() - INTERVAL '30 hours', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '4 hours', NULL),
  ('Solicitação de novo monitor', 'Substituir monitor com defeito.',
    (SELECT id FROM app_users WHERE email='camila@pulseops.example'),
    NULL,
    (SELECT id FROM departments WHERE name='Operações'),
    (SELECT id FROM categories WHERE name='Equipamentos'),
    'baixa','aberto', NOW() - INTERVAL '3 hours', NOW() + INTERVAL '69 hours', NULL, NULL),
  ('Conta bloqueada no sistema interno', 'Solicitante precisa recuperar acesso ao portal.',
    (SELECT id FROM app_users WHERE email='ana@pulseops.example'),
    (SELECT id FROM app_users WHERE email='bruna@pulseops.example'),
    (SELECT id FROM departments WHERE name='Comercial'),
    (SELECT id FROM categories WHERE name='Acessos'),
    'media','fechado', NOW() - INTERVAL '20 hours', NOW() + INTERVAL '4 hours', NOW() - INTERVAL '18 hours', NOW() - INTERVAL '17 hours'),
  ('Painel operacional sem atualização', 'Indicadores não refletem os dados mais recentes.',
    (SELECT id FROM app_users WHERE email='camila@pulseops.example'),
    NULL,
    (SELECT id FROM departments WHERE name='Operações'),
    (SELECT id FROM categories WHERE name='Sistemas'),
    'alta','aberto', NOW() - INTERVAL '1 hour', NOW() + INTERVAL '3 hours', NULL, NULL);

INSERT INTO ticket_comments (ticket_id, author_id, body, is_internal)
SELECT t.id, u.id, 'Falha reproduzida em homologação; investigação em andamento.', true
FROM tickets t CROSS JOIN app_users u
WHERE t.title='Sistema de vendas indisponível' AND u.email='rafael@pulseops.example';

INSERT INTO ticket_history (ticket_id, actor_id, action, old_value, new_value, details)
SELECT t.id, u.id, 'mudanca_status', 'aberto', 'em_atendimento', '{"origem":"seed_demo"}'::jsonb
FROM tickets t CROSS JOIN app_users u
WHERE t.title='Sistema de vendas indisponível' AND u.email='rafael@pulseops.example';

INSERT INTO ai_suggestions (ticket_id, suggested_category_id, suggested_priority, summary, rationale, model_name, review_status)
SELECT t.id, c.id, 'critica',
  'Interrupção no sistema de vendas impede a conclusão de pedidos.',
  'Sugestão FICTÍCIA para demonstração. O modelo ainda não foi integrado.',
  'demo-sem-modelo', 'pendente'
FROM tickets t CROSS JOIN categories c
WHERE t.title='Sistema de vendas indisponível' AND c.name='Sistemas';

COMMIT;
