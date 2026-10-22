# Padrões de desenvolvimento e colaboração

**Objetivo:** manter histórico legível no GitHub e facilitar avaliação técnica do projeto. Esta é uma convenção escolhida para o PulseOps AI, não um padrão obrigatório da Accenture.

## 1. Organização do Git

- `main`: versão integrada e revisada.
- Branch por tarefa: `feat/autenticacao`, `feat/crud-chamados`, `docs/arquitetura`, `fix/sla-vencimento`.
- Pull Request pequeno, ligado à issue; descrever objetivo, alteração, testes e imagens quando houver interface.
- Nunca reescrever a história pública para simular entregas anteriores.
- Antes do push: `git status`, `git diff --cached --check`, conferir `.env`, chaves e arquivos ignorados.

## 2. Conventional Commits (proposta)

| Tipo | Uso | Exemplo |
|---|---|---|
| `feat` | nova funcionalidade | `feat(tickets): cria endpoint de chamados` |
| `fix` | correção | `fix(sla): ajusta calculo para UTC` |
| `docs` | somente texto/diagramas | `docs: adiciona arquitetura e roadmap` |
| `test` | testes | `test(auth): cobre acesso a ticket alheio` |
| `refactor` | reestruturação sem comportamento novo | `refactor(api): separa servicos de rotas` |
| `chore` | manutenção/infra | `chore(ci): configura testes no GitHub Actions` |

Guia com comandos: [05-git-e-commits.md](../contribuicao/git-e-commits.md).

## 3. Convenções de código previstas

- Python: nomes de módulos/funções em `snake_case`, classes `PascalCase`, tipagem estática quando útil; formatador/linter definidos antes de iniciar a API (sugestão: Ruff).
- TypeScript: nomes de variáveis/funções `camelCase`, componentes React `PascalCase`; tipagem explícita de chamadas API; formatter definido na criação do frontend.
- Banco: tabelas e colunas em `snake_case`, nomes de migração descritivos; nunca alterar banco persistente apenas editando `db/init/01_schema.sql` depois de inicializado.
- API: URL com recursos no plural (`/tickets`), versão prefixada (`/api/v1`), nomes JSON consistentes (`snake_case` ou `camelCase`, decidir ao implementar), HTTP sem `200` para erro.
- Segredos e configuração: `.env` local, variáveis de ambiente na hospedagem, valores de exemplo somente em `.env.example`.
- Datas: UTC nos serviços; exibição no fuso configurado pela interface; formato ISO 8601 nos contratos.

## 4. Template de Pull Request

```md
## Objetivo
Explique a necessidade e indique a issue.

## O que mudou
- Módulos e comportamentos alterados

## Como validar
- Comandos executados
- Cenários testados e resultado observado

## Segurança / dados
- [ ] Sem credenciais no commit
- [ ] Permissões avaliadas (quando relevante)
- [ ] Documentação atualizada

## Evidências
Captura de tela, request/response ou log sanitizado
```

## 5. Regras de revisão

- Testes devem verificar comportamento, não só se a função foi chamada.
- Regras de acesso e alterações de SLA exigem revisão cuidadosa e teste negativo.
- Não misturar refatoração não relacionada com correção de bug em um mesmo PR.
- Registrar mudanças de arquitetura no [log de decisões](../planejamento/riscos-e-decisoes.md).
- Para o portfólio, preferir entregas pequenas reais a um grande commit final sem rastreabilidade.

## 6. Checklist de commit de documentação neste pacote

Se **já** publicou a Parte 1 no GitHub, copie os `.md` novos para `docs/`, substitua o `README.md`/`DOCUMENTACAO.md` e execute na raiz:

```powershell
git add README.md DOCUMENTACAO.md docs/
git diff --cached --check
git commit -m "docs: detalha arquitetura roadmap seguranca e testes"
git push
```

Se ainda **não** publicou nada, crie um único commit inicial contendo código e documentação; veja o [guia de Git](../contribuicao/git-e-commits.md).
