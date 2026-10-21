-- Execute por: docker compose exec -T database psql -U pulseops_dev -d pulseops_db -v ON_ERROR_STOP=1 -f /dev/stdin < db/tests/01_smoke_tests.sql
-- Cada bloco DO interrompe com erro se o requisito não for atendido.
DO $$
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'
      AND table_name IN ('departments','app_users','categories','sla_policies','tickets','ticket_comments','ticket_history','ai_suggestions')) <> 8
  THEN RAISE EXCEPTION 'ERRO: faltam tabelas do domínio'; END IF;
  IF (SELECT COUNT(*) FROM tickets) < 8
  THEN RAISE EXCEPTION 'ERRO: dados de exemplo não foram carregados'; END IF;
  IF (SELECT COUNT(*) FROM v_dashboard_kpis) <> 1
  THEN RAISE EXCEPTION 'ERRO: view dos indicadores ausente'; END IF;
  IF (SELECT COUNT(*) FROM app_users WHERE is_active=true OR password_hash <> 'DISABLED_DEMO_ACCOUNT') <> 0
  THEN RAISE EXCEPTION 'ERRO: usuário de demonstração indevidamente habilitado'; END IF;
  IF (SELECT COUNT(*) FROM tickets WHERE status='fechado' AND closed_at IS NULL) <> 0
  THEN RAISE EXCEPTION 'ERRO: chamado fechado sem data'; END IF;
  RAISE NOTICE 'OK: 8 tabelas, ao menos 8 chamados demo, view e contas de teste desabilitadas';
END $$;

-- Testa uma restrição sem deixar dados alterados.
DO $$
DECLARE
  expected_violation BOOLEAN := FALSE;
BEGIN
  BEGIN
    INSERT INTO sla_policies (priority, resolution_minutes) VALUES ('urgente', -5);
  EXCEPTION WHEN check_violation THEN
    expected_violation := TRUE;
  END;
  IF NOT expected_violation THEN RAISE EXCEPTION 'ERRO: CHECK de SLA não funcionou'; END IF;
  RAISE NOTICE 'OK: constraints barram prioridade/prazo inválidos';
END $$;
