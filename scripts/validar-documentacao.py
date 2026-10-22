#!/usr/bin/env python3
"""Valida links Markdown locais e presença de imagens/fontes UML sem bibliotecas extras."""
from pathlib import Path
import os, re, sys, urllib.parse

ROOT = Path(__file__).resolve().parents[1]
regex = re.compile(r'!?\[[^\]\n]*\]\(([^)\n]+)\)')
issues = []
seen = 0
for md in [*sorted(ROOT.rglob('*.md')), ROOT / 'llms.txt']:
    if '.git' in md.parts: continue
    source = md.relative_to(ROOT)
    text = md.read_text(encoding='utf-8')
    for match in regex.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith('<') and '>' in raw: raw=raw[1:raw.index('>')]
        else: raw=raw.split(' "',1)[0]
        if raw.startswith(('https://','http://','mailto:','data:','//','#')): continue
        if raw.startswith('/'): issues.append(f'{source}: caminho absoluto proibido: {raw}'); continue
        route=urllib.parse.unquote(raw.split('#',1)[0].split('?',1)[0])
        if not route: continue
        target=(md.parent/route).resolve()
        seen+=1
        if not target.is_relative_to(ROOT.resolve()): issues.append(f'{source}: link fora da raiz: {raw}')
        elif not target.exists(): issues.append(f'{source}: link quebrado: {raw}')

uml=list((ROOT/'docs/uml/diagramas').glob('*.puml'))
for p in uml:
    if not (ROOT/'docs/uml/imagens'/ (p.stem+'.png')).is_file():
        issues.append(f'Imagem UML faltando: {p.stem}.png')
    if not (ROOT/'docs/uml/imagens'/ (p.stem+'.svg')).is_file():
        issues.append(f'Imagem UML faltando: {p.stem}.svg')
for fname in ['llms.txt','llms-full.txt','docs/00-indice.md']:
    if not (ROOT/fname).is_file(): issues.append(f'Arquivo exigido faltando: {fname}')
print(f'Documentação: {len(list(ROOT.rglob("*.md")))} Markdown, {seen} links locais, {len(uml)} fontes PlantUML')
if issues:
    for item in issues: print('ERRO:',item)
    sys.exit(1)
print('OK: links internos, imagens UML e arquivos-base presentes.')
