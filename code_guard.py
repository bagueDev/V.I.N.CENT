"""Gemeinsame Schutzschicht für run_python (V.I.N.C.E.N.T. MCP-Server).

Das ist KEINE echte Sandbox, sondern Schutz vor Fehlgriffen des Modells:
  1. check_python_code(): statische AST-Prüfung vor der Ausführung
  2. make_exec_globals(): Laufzeit-Schutz (gesperrte Builtins, geprüfter __import__)
  3. limit_resources():   Speicher-/CPU-Limits im Kindprozess

Dateien -> read_file/write_file/patch_file, Web -> fetch_url, Shell -> run_command.
"""
import ast
import builtins as _builtins

# Module, die Dateisystem, Netzwerk, Prozesse oder Interpreter-Interna berühren
BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "ssl", "ctypes", "importlib",
    "builtins", "pathlib", "glob", "fileinput", "tempfile", "io", "pickle", "marshal",
    "shelve", "multiprocessing", "threading", "signal", "pty", "resource", "gc",
    "inspect", "code", "codeop", "runpy", "pkgutil", "zipimport",
    "requests", "urllib", "urllib3", "http", "httpx", "aiohttp", "ftplib",
    "smtplib", "telnetlib", "xmlrpc", "webbrowser", "asyncio",
}

# Aufrufe/Namen, die Code nachladen, ausführen oder Dateien öffnen
BLOCKED_NAMES = {
    "eval", "exec", "compile", "open", "__import__", "breakpoint", "input",
    "exit", "quit", "globals", "locals", "vars", "memoryview",
}

_SAFE_DUNDER = {"__name__", "__doc__", "__len__", "__str__", "__repr__", "__init__"}

_HINT = (
    "Dateien: read_file/write_file/patch_file · Web: fetch_url · "
    "Shell: run_command. run_python ist nur für reine Berechnungen gedacht."
)


def _top(module: str) -> str:
    return (module or "").split(".")[0]


def check_python_code(code: str):
    """Gibt None zurück, wenn der Code ok ist, sonst eine Fehlermeldung (str)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"❌ Syntaxfehler: {e.msg} (Zeile {e.lineno})"

    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if _top(a.name) in BLOCKED_MODULES:
                    problems.append(f"Import '{a.name}' (Zeile {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            if node.level or _top(node.module or "") in BLOCKED_MODULES:
                problems.append(f"Import 'from {node.module or '.'}' (Zeile {node.lineno})")
        elif isinstance(node, ast.Name):
            if node.id in BLOCKED_NAMES:
                problems.append(f"'{node.id}' (Zeile {node.lineno})")
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            if attr in BLOCKED_NAMES:
                problems.append(f"'.{attr}' (Zeile {node.lineno})")
            elif attr.startswith("__") and attr.endswith("__") and attr not in _SAFE_DUNDER:
                problems.append(f"Zugriff auf '{attr}' (Zeile {node.lineno})")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("getattr", "setattr", "delattr"):
            arg = node.args[1] if len(node.args) > 1 else None
            if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                    and not arg.value.startswith("_")):
                problems.append(f"{node.func.id}() mit dynamischem/privatem Namen (Zeile {node.lineno})")

    if problems:
        uniq = list(dict.fromkeys(problems))[:8]
        return "❌ Code blockiert (nicht erlaubt in run_python): " + ", ".join(uniq) + f"\n💡 {_HINT}"
    return None


def make_exec_globals() -> dict:
    """Globals für exec(): gesperrte Builtins entfernt, __import__ prüft Modulnamen zur Laufzeit."""
    safe = {k: v for k, v in vars(_builtins).items() if k not in BLOCKED_NAMES}
    real_import = _builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level or _top(name) in BLOCKED_MODULES:
            raise ImportError(f"Import '{name}' ist in run_python nicht erlaubt. {_HINT}")
        return real_import(name, globals, locals, fromlist, level)

    safe["__import__"] = guarded_import
    return {"__builtins__": safe}


def limit_resources(mem_mb: int = 1024, cpu_s: int = 10) -> None:
    """Im Kindprozess aufrufen, bevor der Code läuft (Linux).

    mem_mb gilt zusätzlich zum bereits belegten Adressraum: Der Kindprozess erbt ihn vom Server,
    und mit geladenem torch liegt allein dieser schon bei mehreren GB.
    """
    try:
        import resource
        try:
            with open("/proc/self/statm") as f:
                used = int(f.read().split()[0]) * resource.getpagesize()
        except (OSError, ValueError):
            used = 0
        limit = used + mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s + 2, cpu_s + 2))
    except Exception:
        pass
