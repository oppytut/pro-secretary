from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def _walk_python_files(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".py":
        return [root]
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _defined_function_names(tree: ast.AST) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _top_level_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def check_telegram_bot_handlers(root: Path) -> list[tuple[Path, str, int]]:
    files = _walk_python_files(root)
    if not files:
        return []

    package_funcs: set[str] = set()
    parsed: list[tuple[Path, ast.AST]] = []
    for path in files:
        tree = ast.parse(path.read_text(), filename=str(path))
        parsed.append((path, tree))
        package_funcs |= _defined_function_names(tree)

    missing: list[tuple[Path, str, int]] = []
    for path, tree in parsed:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            fname = (
                func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name)
                else None
            )
            if fname == "CommandHandler" and len(node.args) >= 2:
                target = node.args[1]
                if isinstance(target, ast.Name) and target.id not in package_funcs:
                    missing.append((path, target.id, target.lineno))
            elif fname in {"run_daily", "run_repeating", "run_once"} and node.args:
                cb = node.args[0]
                if isinstance(cb, ast.Name) and cb.id not in package_funcs:
                    missing.append((path, cb.id, cb.lineno))

    return missing


def check_langgraph_main_cross_module(app_dir: Path) -> list[tuple[str, str, int]]:
    main_file = app_dir / "main.py"
    if not main_file.exists():
        return []

    tree = ast.parse(main_file.read_text(), filename=str(main_file))

    local_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is None:
            for alias in node.names:
                local_modules.add(alias.asname or alias.name)

    refs: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if not isinstance(node.value, ast.Name):
            continue
        if node.value.id not in local_modules:
            continue
        refs.append((node.value.id, node.attr, node.lineno))

    cache: dict[str, set[str]] = {}
    seen: set[tuple[str, str]] = set()
    missing: list[tuple[str, str, int]] = []
    for module, attr, lineno in refs:
        if module not in cache:
            sibling = app_dir / f"{module}.py"
            cache[module] = _top_level_names(ast.parse(sibling.read_text())) if sibling.exists() else set()
        if attr not in cache[module] and (module, attr) not in seen:
            seen.add((module, attr))
            missing.append((module, attr, lineno))
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot-package", default="telegram-bot", type=Path)
    parser.add_argument("--agent-app", default="langgraph-agent/app", type=Path)
    args = parser.parse_args(argv)

    bot_missing = check_telegram_bot_handlers(args.bot_package)
    if bot_missing:
        print(f"ORPHAN REFERENCES in {args.bot_package}:")
        for path, name, lineno in bot_missing:
            print(f"  {path}:{lineno}: '{name}' is referenced but never defined")

    agent_missing = check_langgraph_main_cross_module(args.agent_app)
    if agent_missing:
        print(f"ORPHAN REFERENCES in {args.agent_app}/main.py:")
        for module, attr, lineno in agent_missing:
            print(f"  line {lineno}: '{module}.{attr}' referenced but not defined in {module}.py")

    if bot_missing or agent_missing:
        return 1

    bot_files = _walk_python_files(args.bot_package)
    bot_func_count = sum(
        len(_defined_function_names(ast.parse(p.read_text())))
        for p in bot_files
    )
    print(f"OK: telegram-bot package clean ({len(bot_files)} files, {bot_func_count} functions)")
    print(f"OK: langgraph-agent main.py cross-module refs all resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
