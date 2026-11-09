# SLA de chamados — PulseOps AI

## Regras do MVP

- O prazo de resolução usa **horas corridas**, calculadas em PostgreSQL a partir de `opened_at`.
- A duração por prioridade vem de `sla_policies.resolution_minutes` (não de valores fixos no frontend).
- Ao abrir um chamado pela API, `due_at = opened_at + resolution_minutes`.
- Ao alterar a prioridade, o prazo é recalculado **desde a abertura original** do chamado. O histórico de prioridade continua sendo registrado.
- Se a prioridade não tiver política configurada, a API responde com HTTP 422 e não salva a criação/alteração.
- A API expõe `due_at`, `resolved_at` e `sla_status` na listagem e no detalhe. O status é derivado da view `v_ticket_sla`.
- O dashboard exibe `cumprimento_sla_pct`, a porcentagem de chamados concluídos com prazo definido que foram resolvidos até `due_at`. Sem chamados elegíveis, o valor é `null` (mostrado como travessão).
- O indicador **Fora do SLA** inclui chamados pendentes atrasados e chamados concluídos após o prazo.
- Mudanças em `sla_policies` **não** recalculam automaticamente chamados já abertos; uma nova mudança de prioridade aplica a política vigente.

## Situações possíveis

| Situação | Regra |
|---|---|
| `sem_prazo` | `due_at IS NULL` |
| `em_dia` | Ainda não resolvido e o prazo não venceu |
| `atrasado` | Ainda não resolvido e o prazo venceu |
| `dentro_do_prazo` | Resolvido até o vencimento |
| `fora_do_prazo` | Resolvido após o vencimento |

## Atualizar chamados legados

Os chamados criados antes desta funcionalidade podem ter `due_at IS NULL`. O arquivo `db/migrations/20261109_backfill_ticket_sla.sql` preenche **somente** esses casos, sem sobrescrever prazos existentes.

1. Faça backup do banco e confira os valores de `sla_policies`.
2. Execute o script SQL no banco correto (por exemplo, no Query Tool do pgAdmin ou no `psql`).
3. Confira o resultado com:

```sql
SELECT id, priority, opened_at, due_at
FROM tickets
ORDER BY id DESC;
```

A migração é opcional para dados históricos, mas necessária para que todos os chamados legados tenham SLA calculado. Não execute `db/init/01_schema.sql` sobre um banco já existente.

## Validação

```bash
cd backend
.venv/bin/python -m pytest tests/test_sla.py -q
```

Os testes de integração precisam de PostgreSQL inicializado com as políticas de SLA e uma configuração de ambiente de teste. Nunca use credenciais de produção em testes.
