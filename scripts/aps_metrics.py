"""Métricas estáticas APS: CC (AST), CBO aproximado e LCOM4.

Uso: python scripts/aps_metrics.py backend/app/services/triage_patterns.py
CC considera if/for/while/except/ifexpr, booleans e filtros de comprehension.
CBO conta classes conhecidas referenciadas sintaticamente no corpo da classe.
LCOM4 conta componentes de métodos conectados por atributos self compartilhados.
São aproximações explícitas; não representam cobertura de testes.
"""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
from statistics import mean


def complexity(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    score = 1
    stack = list(function.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler)):
            score += 1
        elif isinstance(node, ast.BoolOp):
            score += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            score += len(node.ifs)
        stack.extend(ast.iter_child_nodes(node))
    return score


def self_attributes(method: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {n.attr for n in ast.walk(method)
            if isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Name) and n.value.id == "self"}


def lcom4(cls: ast.ClassDef) -> int:
    methods = [m for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
               and not any(isinstance(d, ast.Name) and d.id in ("staticmethod", "classmethod")
                           for d in m.decorator_list)]
    if len(methods) <= 1:
        return 1
    attrs = [self_attributes(m) for m in methods]
    parents = list(range(len(methods)))
    def find(i):
        while parents[i] != i:
            i = parents[i]
        return i
    for i in range(len(methods)):
        for j in range(i+1, len(methods)):
            if attrs[i] & attrs[j]:
                parents[find(j)] = find(i)
    return len({find(i) for i in range(len(methods))})


def inspect_file(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    known_classes = {c.name for c in classes} | {
        "GeneratedProposal", "InvalidProviderResponse", "ProviderUnavailable", "TriageProposal"
    }
    all_functions = {f.name: complexity(f) for f in functions}
    class_stats = {}
    for cls in classes:
        methods = [m for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for m in methods:
            all_functions[f"{cls.name}.{m.name}"] = complexity(m)
        refs = sorted({n.id for n in ast.walk(cls)
                       if isinstance(n, ast.Name) and n.id in known_classes and n.id != cls.name})
        class_stats[cls.name] = {
            "cbo_classes_referenced": len(refs), "dependencies": refs, "lcom4": lcom4(cls)
        }
    return {
        "path": str(path),
        "functions": all_functions,
        "mean_cyclomatic_complexity": round(mean(all_functions.values()), 2) if all_functions else None,
        "max_cyclomatic_complexity": max(all_functions.values()) if all_functions else None,
        "classes": class_stats,
        "mean_cbo": round(mean(c["cbo_classes_referenced"] for c in class_stats.values()), 2) if classes else None,
        "mean_lcom4": round(mean(c["lcom4"] for c in class_stats.values()), 2) if classes else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Métricas estáticas do projeto APS")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, help="Salva JSON em disco")
    args = parser.parse_args()
    result = {"method": "Python ast (CC, CBO aproximado, LCOM4)",
              "files": [inspect_file(p) for p in args.files]}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output+"\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
