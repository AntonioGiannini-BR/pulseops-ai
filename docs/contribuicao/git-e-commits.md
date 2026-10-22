# Guia de Git e commits — PulseOps AI (Windows + VS Code)

Este guia explica **como criar seu repositório, registrar a Parte 1 no GitHub e trabalhar com commits nas próximas etapas**.

## 1. O que é um commit?

Um **commit** é um registro versionado de alterações. Idealmente, cada commit representa uma unidade de trabalho compreensível (por exemplo: criação de um endpoint, teste de uma regra ou ajuste da documentação). `git add` prepara alterações; `git commit` grava um registro **local**; `git push` envia commits ao GitHub.

## 2. Criar o repositório local

1. Extraia o ZIP atualizado do PulseOps AI.
2. Abra o VS Code e selecione **Arquivo > Abrir Pasta > PulseOpsAI-Parte1**.
3. Abra **Terminal > Novo Terminal** e confirme que está na pasta que contém `README.md`.
4. Execute no PowerShell:

```powershell
git --version
git init -b main
git status
```

Se o Git avisar que precisa de uma identidade, configure **seu próprio nome e o e-mail cadastrado no GitHub** (pode usar endereço `noreply` do GitHub para privacidade):

```powershell
git config --global user.name "SEU NOME"
git config --global user.email "SEU-EMAIL-DO-GITHUB"
```

> Nunca coloque sua senha do GitHub nem tokens em commits ou arquivos públicos.

## 3. Registrar a Parte 1 (caminho recomendado)

Como os arquivos da Parte 1 já foram preparados em conjunto, um commit inicial é a forma mais fiel e simples de registrar essa base. Execute:

```powershell
git add .
git status
git diff --cached --check
git commit -m "feat: adiciona base inicial do PulseOps AI"
git log --oneline -5
```

**Confira no `git status`:** `.env` não deve aparecer nos arquivos preparados. Esse arquivo contém sua senha local e já está listado no `.gitignore`. `.env.example` pode ser enviado: ele contém apenas campos de exemplo.

Este primeiro commit contém planejamento, documentação, diagramas, SQL, Docker e protótipo; não significa que as etapas futuras já foram desenvolvidas.

## 4. Criar o repositório no GitHub e enviar

1. Entre em [github.com/new](https://github.com/new) com sua conta.
2. Nome sugerido: `pulseops-ai`.
3. Para portfólio, prefira **Public** apenas se o repositório não tiver dados privados, segredos ou materiais de terceiros não autorizados.
4. **Não marque** “Add a README file”, “Add .gitignore” nem licença nessa criação inicial, pois os arquivos locais já existem.
5. No terminal do projeto, troque `SEU-USUARIO` pelo seu login do GitHub:

```powershell
git remote add origin https://github.com/SEU-USUARIO/pulseops-ai.git
git remote -v
git push -u origin main
```

O GitHub pode solicitar autenticação pelo navegador ou gerenciador de credenciais. Não compartilhe credenciais em mensagens ou arquivos.

Se o remote `origin` já existir, confira com `git remote -v`; para corrigir a URL use:

```powershell
git remote set-url origin https://github.com/SEU-USUARIO/pulseops-ai.git
```

## 5. Como fazer commits nas próximas partes

Não espere juntar uma semana inteira de código. Faça commits pequenos quando uma mudança estiver funcionando ou quando a documentação da mudança estiver pronta.

**Exemplo para a Parte 2, após criar `backend/`:**

```powershell
git switch -c feat/backend-inicial
git add backend/
git diff --cached --check
git commit -m "feat(api): cria estrutura inicial do FastAPI"
git push -u origin feat/backend-inicial
```

Depois, ao criar os modelos e as rotas:

```powershell
git add backend/
git commit -m "feat(api): implementa modelos e CRUD de chamados"
git push
```

Ao adicionar testes:

```powershell
git add backend/
git commit -m "test(api): cobre criacao e listagem de chamados"
git push
```

No GitHub, abra um **Pull Request** de `feat/backend-inicial` para `main`. Após revisar, faça o merge e continue na próxima tarefa.

## 6. Padrão de mensagens de commit

Usaremos uma convenção simples inspirada em *Conventional Commits*:

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat(tickets): permite criar chamado` |
| `fix` | Correção de defeito | `fix(sla): corrige calculo de vencimento` |
| `docs` | Somente documentação | `docs: detalha arquitetura do backend` |
| `test` | Testes automatizados | `test(db): adiciona testes de integridade` |
| `refactor` | Melhorias sem alterar comportamento | `refactor(api): separa servicos e rotas` |
| `chore` | Configuração e manutenção | `chore(ci): configura workflow de testes` |

Prefira mensagens objetivas que expliquem **o que mudou**. Não crie commits fictícios para sugerir uma cronologia de trabalho que não ocorreu.

## 7. Alternativa: commits temáticos da Parte 1

Se **ainda não fez o primeiro commit**, pode separar o pacote em commits por temas para facilitar revisão. Isso apenas divide o conteúdo atual por assunto; não representa etapas realizadas em datas diferentes.

```powershell
# Planejamento e modelagem
 git add .gitignore README.md DOCUMENTACAO.md llms.txt llms-full.txt docs/planejamento/ docs/requisitos/ docs/arquitetura/ docs/banco-de-dados/ docs/api/ docs/uml/
 git commit -m "docs: define requisitos e arquitetura do PulseOps AI"

# Esquema e dados
 git add db/
 git commit -m "feat(db): cria esquema relacional e dados demonstrativos"

# Infraestrutura local
 git add .env.example compose.yaml scripts/
 git commit -m "chore(docker): prepara PostgreSQL e testes locais"

# Interface inicial
 git add prototype/ docs/imagens/dashboard-preview.png
 git commit -m "feat(ui): adiciona prototipo de dashboard offline"

# Guia de Git
 git add docs/contribuicao/git-e-commits.md
 git commit -m "docs: inclui guia de commits e publicacao"
```

Após o último commit, confira `git status` e envie com `git push -u origin main` depois de criar o repositório remoto. **Não use a alternativa temática depois de já ter feito o commit inicial**: nesse caso, continue normalmente com novos commits.

## 8. Comandos úteis para o dia a dia

```powershell
git status                          # Arquivos alterados e preparados
git diff                            # Mudancas ainda nao preparadas
git diff --cached                   # Mudancas do proximo commit
git log --oneline --graph --all      # Historico compacto
git branch                          # Branch atual
git pull --ff-only                  # Atualiza sem merge automatico inesperado
```

Se aparecer `nothing to commit, working tree clean`, significa que não há alterações pendentes. Se `git` não for reconhecido, instale [Git for Windows](https://git-scm.com/downloads/win), reinicie o VS Code e tente novamente.

Se precisar tirar um arquivo **da área de preparação sem apagá-lo**, use `git restore --staged NOME_DO_ARQUIVO`.

## 9. Checklist antes de dar push

- [ ] `git status` mostra somente arquivos esperados.
- [ ] `.env`, senhas, tokens e dados pessoais não estão no commit.
- [ ] `git diff --cached --check` não mostra erros de espaços ou conflitos.
- [ ] README e documentação descrevem o estado real do projeto.
- [ ] Testes executados são informados corretamente; testes ainda não executados não são apresentados como aprovados.
- [ ] Mensagem de commit descreve a alteração.

## Commit recomendado desta reorganização

Se o projeto já está publicado, copie a estrutura nova integralmente para o diretório Git (removendo os arquivos antigos que foram movidos) e confira o `git status` antes de confirmar. **Não basta sobrescrever as pastas:** a reorganização inclui movimentações de arquivos.

```powershell
git status
git add -A
git diff --cached --check
git diff --cached --stat
git commit -m "docs: reorganiza documentacao para leitura por LLMs"
git push origin main
```

O `git add -A` registra os arquivos movidos e as exclusões dos caminhos antigos. Antes do commit, confira se arquivos locais confidenciais não foram incluídos.
