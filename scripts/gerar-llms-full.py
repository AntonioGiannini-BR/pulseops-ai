#!/usr/bin/env python3
"""Regenera llms-full.txt a partir dos arquivos Markdown versionados do projeto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    "README.md", "DOCUMENTACAO.md", "docs/00-indice.md",
    "docs/planejamento/plano-geral.md",
    "docs/planejamento/visao-do-produto.md",
    "docs/requisitos/requisitos-e-historias.md",
    "docs/requisitos/regras-de-negocio.md",
    "docs/arquitetura/arquitetura.md",
    "docs/arquitetura/padroes-de-desenvolvimento.md",
    "docs/banco-de-dados/modelagem.md",
    "docs/api/contrato-api.md",
    "docs/uml/README.md",
    "docs/seguranca/seguranca-e-privacidade.md",
    "docs/testes/plano-de-testes.md",
    "docs/planejamento/roadmap-e-sprints.md",
    "docs/planejamento/riscos-e-decisoes.md",
    "docs/arquitetura/galeria-visual.md",
    "docs/contribuicao/git-e-commits.md",
]
header = """# PulseOps AI — Contexto textual completo para LLMs

> Este arquivo é gerado automaticamente. Altere os documentos `.md` originais e execute `python scripts/gerar-llms-full.py`.
> Escopo atual: Parte 1 (protótipo offline, scripts SQL/Docker preparados). APIs, login, React, LLM e deploy são planos futuros, não recursos implementados.
> Diagramas e imagens são referenciados por caminhos relativos no documento de origem, sem reprodução binária.
"""
chunks = [header]
for location in DOCUMENTS:
    file = ROOT / location
    if not file.is_file():
        raise SystemExit(f"Documento ausente: {location}")
    content = file.read_text(encoding="utf-8").strip()
    chunks.append("\n---\n\n## Fonte: `" + location + "`\n\n" + content + "\n")
out = ROOT / "llms-full.txt"
out.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")
print(f"Atualizado: {out.relative_to(ROOT)} ({len(DOCUMENTS)} documentos)")
