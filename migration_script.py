#!/usr/bin/env python3
"""
Quick extractor for FastAPI routes, Pydantic/SQLModel models and basic DB relationships.
This is a best-effort tool — it uses AST to find decorators like @app.get, @router.post, etc.
It also parses class defs that subclass SQLModel or BaseModel to extract fields.
Outputs a Markdown summary.

Run from repository root:
python scripts/extract_fastapi_spec.py > MIGRATION_SPEC_DRAFT.md
"""

import ast
import os
import sys
from typing import List, Tuple, Dict, Optional

ROUTE_DECORATORS = {"get","post","put","delete","patch","options","head"}

def find_py_files(root="."):
    for dirpath, _, filenames in os.walk(root):
        # skip venv and .git
        if "venv" in dirpath or ".venv" in dirpath or ".git" in dirpath:
            continue
        for f in filenames:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)

def parse_file(path: str):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
            tree = ast.parse(content, filename=path)
            return tree, content
    except Exception as e:
        return None, None

def extract_routes(tree: ast.AST, content: str, path: str):
    routes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for deco in node.decorator_list:
                # decorator like @router.get("/path")
                if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                    attr = deco.func
                    name = attr.attr  # get/post/...
                    if name in ROUTE_DECORATORS:
                        # Extract path arg if available
                        route_path = None
                        if deco.args and isinstance(deco.args[0], ast.Constant):
                            route_path = deco.args[0].value
                        # Get response_model kwarg if present
                        resp = None
                        deps = []
                        for kw in deco.keywords:
                            if kw.arg == "response_model":
                                resp = ast.unparse(kw.value) if hasattr(ast, "unparse") else None
                            if kw.arg == "dependencies":
                                deps = ast.unparse(kw.value) if hasattr(ast, "unparse") else None
                        routes.append({
                            "method": name.upper(),
                            "path": route_path or "(dynamic/path)",
                            "handler": node.name,
                            "file": path,
                            "lineno": node.lineno,
                            "response_model": resp,
                            "dependencies": deps
                        })
    return routes

def extract_models(tree: ast.AST, path: str):
    models = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [getattr(b, "id", getattr(getattr(b, "attr", None), "id", None)) for b in node.bases]
            # heuristic: SQLModel or BaseModel in bases
            if any(b in ("SQLModel", "BaseModel", "pydantic.BaseModel") for b in bases if b):
                fields = []
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign):
                        name = stmt.target.id if isinstance(stmt.target, ast.Name) else None
                        ann = ast.unparse(stmt.annotation) if hasattr(ast, "unparse") else None
                        default = None
                        if stmt.value:
                            try:
                                default = ast.literal_eval(stmt.value)
                            except Exception:
                                default = ast.unparse(stmt.value) if hasattr(ast, "unparse") else "<expr>"
                        fields.append({"name": name, "annotation": ann, "default": default})
                models.append({"class": node.name, "bases": bases, "fields": fields, "file": path})
    return models

def main():
    pyfiles = list(find_py_files("."))
    all_routes = []
    all_models = []
    for f in pyfiles:
        tree, content = parse_file(f)
        if not tree:
            continue
        all_routes.extend(extract_routes(tree, content, f))
        all_models.extend(extract_models(tree, f))

    # Simple markdown output
    output = ("# MIGRATION_SPEC_DRAFT\n")
    output += ("## Scanned files summary")
    output += (f"- Python files scanned: {len(pyfiles)}\n")

    output += ("## Endpoints index\n")
    output += ("| Method | Path | Handler | File:Line | Response model | Dependencies |")
    output += ("|---|---|---|---|---|---|")
    for r in sorted(all_routes, key=lambda x: x["path"] or ""):
        output += (f"| {r['method']} | {r['path']} | {r['handler']} | {r['file']}:{r['lineno']} | {r.get('response_model') or ''} | {r.get('dependencies') or ''} |")

    output += ("\n## Endpoint details\n")
    for r in all_routes:
        output += (f"### {r['method']} {r['path']} — {r['file']}:{r['lineno']}\n")
        output += (f"- Handler: `{r['handler']}`\n- Response model: `{r.get('response_model')}`\n- Dependencies: `{r.get('dependencies')}`\n")

    output += ("\n## Models (SQLModel/Pydantic) discovered\n")
    for m in all_models:
        output += (f"### {m['class']} — file: {m['file']}\n")
        for fld in m["fields"]:
            output += (f"- `{fld['name']}`: `{fld['annotation']}` (default={fld['default']})")
        output += ("\n")

    output += ("\n## Notes\n")
    output += ("- This is a best-effort draft. Dynamic route registration, response models assigned at runtime, or models created by factory functions may not be fully detected.")
    output += ("- Run a deeper static analysis or use runtime instrumentation (start the app and read `app.routes`) for complete results.")
    return output

if __name__ == "__main__":
    # Write the output into a .md file
    with open("MIGRATION_SPEC_DRAFT.txt", "w") as f:
        f.write(main())