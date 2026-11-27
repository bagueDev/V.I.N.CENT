"""Statische AST-Analyse fuer Refactoring-Vorschlaege (read-only, keine Ausfuehrung).

Findet strukturelle Probleme, die ein Modell beim Ueberfliegen einer grossen Datei
leicht uebersieht oder falsch einschaetzt: zu komplexe Funktionen, doppelter Code,
unbenutzte Imports/Variablen, bare except, mutable Defaults.

Nutzung: analyze_source(code, filename) -> dict[str, list[str]]
         format_report(findings, filename) -> str
"""
import ast
from collections import defaultdict

MAX_FUNCTION_LINES = 80
MAX_COMPLEXITY = 15
MAX_NESTING = 5
MAX_PARAMS = 6
MIN_DUP_STRING_LEN = 20
MIN_DUP_STRING_COUNT = 3
MIN_DUP_BODY_STATEMENTS = 3
MAX_FINDINGS_PER_CATEGORY = 20

_FUNC_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
_SCOPE_BOUNDARY = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def _func_name(node, class_stack):
    if class_stack:
        return f"{'.'.join(class_stack)}.{node.name}"
    return node.name


def _walk_own_scope(node):
    """Wie ast.walk(), steigt aber nicht in verschachtelte Funktionen/Klassen ab."""
    todo = list(ast.iter_child_nodes(node))
    while todo:
        n = todo.pop()
        yield n
        if not isinstance(n, _SCOPE_BOUNDARY):
            todo.extend(ast.iter_child_nodes(n))


def _complexity(node):
    score = 1
    for n in _walk_own_scope(node):
        if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.Assert)):
            score += 1
        elif isinstance(n, ast.BoolOp):
            score += len(n.values) - 1
        elif isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            score += 1 + sum(len(gen.ifs) for gen in n.generators)
    return score


def _max_nesting(node, depth=0):
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _SCOPE_BOUNDARY):
            continue
        next_depth = depth + 1 if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try)) else depth
        best = max(best, _max_nesting(child, next_depth))
    return best


def _param_count(args):
    names = [a.arg for a in (args.args + args.posonlyargs + args.kwonlyargs) if a.arg not in ("self", "cls")]
    return len(names)


def _mutable_default_findings(node, name):
    out = []
    for default in list(node.args.defaults) + list(node.args.kw_defaults):
        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
            out.append(f"{name} (Zeile {node.lineno}): mutable Default-Argument")
    return out


def _assigned_names(node):
    names = set()
    for n in _walk_own_scope(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            names.add(n.id)
        elif isinstance(n, ast.arg):
            names.add(n.arg)
    return names


def _used_names(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def analyze_source(code: str, filename: str = "<code>") -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"syntaxfehler": [f"{filename}: Zeile {e.lineno}: {e.msg}"]}

    findings = defaultdict(list)
    class_stack = []
    func_bodies = []  # (name, lineno, dump_of_body)
    docstring_values = set()

    def visit(node, in_class_stack):
        if isinstance(node, ast.ClassDef):
            new_stack = in_class_stack + [node.name]
            for child in node.body:
                visit(child, new_stack)
            return

        if isinstance(node, _FUNC_TYPES):
            name = _func_name(node, in_class_stack)
            doc = ast.get_docstring(node)
            if doc:
                docstring_values.add(doc)

            n_lines = (node.end_lineno or node.lineno) - node.lineno + 1
            complexity = _complexity(node)
            nesting = _max_nesting(node)
            problems = []
            if n_lines > MAX_FUNCTION_LINES:
                problems.append(f"{n_lines} Zeilen")
            if complexity > MAX_COMPLEXITY:
                problems.append(f"Komplexitaet {complexity}")
            if nesting > MAX_NESTING:
                problems.append(f"Verschachtelung {nesting}")
            if problems:
                findings["komplexe_funktionen"].append(
                    f"{name} (Zeile {node.lineno}): {', '.join(problems)}"
                )

            n_params = _param_count(node.args)
            if n_params > MAX_PARAMS:
                findings["zu_viele_parameter"].append(
                    f"{name} (Zeile {node.lineno}): {n_params} Parameter"
                )

            findings["mutable_defaults"].extend(_mutable_default_findings(node, name))

            assigned = _assigned_names(node)
            used = _used_names(node)
            unused = sorted(v for v in assigned if v not in used and not v.startswith("_"))
            for v in unused:
                findings["unbenutzte_variablen"].append(f"{name} (Zeile {node.lineno}): '{v}' nie gelesen")

            body_stmts = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))]
            if len(body_stmts) >= MIN_DUP_BODY_STATEMENTS:
                dump = ast.dump(ast.Module(body=body_stmts, type_ignores=[]), annotate_fields=False)
                func_bodies.append((name, node.lineno, dump))

            for n in _walk_own_scope(node):
                if isinstance(n, ast.ExceptHandler) and n.type is None:
                    findings["bare_except"].append(f"{name} (Zeile {n.lineno}): bare 'except:'")

            for child in ast.iter_child_nodes(node):
                visit(child, in_class_stack)
            return

        for child in ast.iter_child_nodes(node):
            visit(child, in_class_stack)

    visit(tree, class_stack)

    # Doppelte Funktionskoerper (gleicher AST-Dump, mehrfach vorhanden)
    seen = defaultdict(list)
    for name, lineno, dump in func_bodies:
        seen[dump].append((name, lineno))
    for dump, occurrences in seen.items():
        if len(occurrences) > 1:
            where = ", ".join(f"{n} (Zeile {l})" for n, l in occurrences)
            findings["doppelte_funktionen"].append(f"{len(occurrences)}x identisch: {where}")

    # Unbenutzte Top-Level-Imports
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported[(a.asname or a.name).split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name != "*":
                    imported[a.asname or a.name] = node.lineno
    used_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used_attrs_base = {n.value.id for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    for alias, lineno in imported.items():
        if alias not in used_names and alias not in used_attrs_base:
            findings["unbenutzte_imports"].append(f"'{alias}' (Zeile {lineno}) wird nirgends verwendet")

    # Doppelte String-Literale (keine Docstrings)
    string_locs = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in docstring_values or len(node.value) < MIN_DUP_STRING_LEN:
                continue
            string_locs[node.value].append(node.lineno)
    for value, lines in string_locs.items():
        if len(lines) >= MIN_DUP_STRING_COUNT:
            preview = value if len(value) <= 50 else value[:47] + "..."
            findings["doppelte_strings"].append(f"{len(lines)}x \"{preview}\" (Zeilen {', '.join(map(str, lines[:6]))})")

    return {k: v[:MAX_FINDINGS_PER_CATEGORY] for k, v in findings.items() if v}


_CATEGORY_LABELS = {
    "syntaxfehler": "🚫 Syntaxfehler",
    "komplexe_funktionen": "🧩 Komplexe Funktionen",
    "zu_viele_parameter": "📋 Zu viele Parameter",
    "mutable_defaults": "⚠️ Mutable Default-Argumente",
    "bare_except": "🕳️ Bare except",
    "doppelte_funktionen": "👯 Doppelte Funktionen",
    "unbenutzte_imports": "📦 Unbenutzte Imports",
    "unbenutzte_variablen": "🗑️ Unbenutzte Variablen",
    "doppelte_strings": "🔁 Doppelte String-Literale",
}

_CATEGORY_ORDER = list(_CATEGORY_LABELS.keys())


def format_report(findings: dict, filename: str = "<code>") -> str:
    if not findings:
        return f"✅ Keine Auffaelligkeiten gefunden in {filename}."

    lines = [f"📊 **Code-Analyse: {filename}**\n"]
    for key in _CATEGORY_ORDER:
        items = findings.get(key)
        if not items:
            continue
        lines.append(f"\n{_CATEGORY_LABELS.get(key, key)} ({len(items)}):")
        for item in items:
            lines.append(f"  - {item}")
    lines.append("\n💡 Dies sind Vorschlaege, keine Garantien - menschliche/fachliche Einschaetzung pruefen.")
    return "\n".join(lines)
