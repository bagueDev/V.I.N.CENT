"""Gemeinsame Schutzschicht für run_python (V.I.N.C.E.N.T. MCP-Server).

Die Grenze ist die Sandbox (bubblewrap und ein seccomp-Filter, nur Linux): Der Code sieht vom
Rechner nur das System und die Python-Pakete (nur lesbar), kann keine Dateien anlegen oder ändern,
hat kein Netz und keine Umgebungsvariablen. Ohne diese Sandbox wird nichts ausgeführt.
Nicht begrenzt ist der gesamte Speicherverbrauch, das Speicherlimit gilt je Prozess.

check_python_code() und make_exec_globals() sind KEIN Schutz, den man nicht umgehen könnte
(z. B. führen Bibliotheken selbst Dateizugriffe aus). Sie geben dem Modell nur früh den Hinweis
auf das passende Werkzeug:
Dateien -> read_file/write_file/patch_file, Web -> fetch_url, Shell -> run_command.
"""
import ast
import builtins as _builtins
import os
import re
import shutil
import subprocess
import sys
import tempfile

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

    mem_mb gilt zusätzlich zum bereits belegten Adressraum (Interpreter und geladene Bibliotheken).
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


# --- Sandbox ---------------------------------------------------------------------------------

TIMEOUT_S = 10
OUTPUT_LIMIT = 100_000          # Zeichen, die höchstens zurückkommen
_FILE_LIMIT = 1024 * 1024       # begrenzt stdout/stderr, andere Dateien sind nicht beschreibbar
_CODE_ERROR = 3                 # Rückgabewert: Fehler im ausgeführten Code (nicht in der Sandbox)
_NO_SANDBOX = 4                 # Rückgabewert: Schutz unvollständig, Code nicht ausgeführt
_BOOT = "import sys; sys.path.insert(0, '/sandbox'); import code_guard; sys.exit(code_guard.sandbox_child())"
_INSTALL_HINT = (
    "Dafür braucht es bubblewrap (nur Linux), z. B. mit: sudo apt install bubblewrap. "
    "Ohne diese Sandbox wird kein Code ausgeführt."
)


def _python_dirs() -> list:
    """Ordner außerhalb von /usr, die der Interpreter braucht (z. B. die .venv)."""
    home = os.path.realpath(os.path.expanduser("~"))
    dirs = []
    for d in (sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix,
              os.path.dirname(os.path.realpath(sys.executable))):
        d, real = os.path.abspath(d), os.path.realpath(d)
        if real == "/usr" or real.startswith("/usr/"):
            continue
        if (home + os.sep).startswith(real.rstrip(os.sep) + os.sep):
            raise OSError(f"Der Python-Ordner {real} enthält persönliche Daten und wird nicht freigegeben.")
        dirs += [x for x in (real, d) if x not in dirs]
    return dirs


def sandbox_command(bwrap: str) -> list:
    """bwrap-Aufruf: System und Python nur lesbar, sonst nichts vom Rechner, kein Netz."""
    cmd = [bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
           "--ro-bind", "/usr", "/usr"]
    for d in ("/bin", "/sbin", "/lib", "/lib32", "/lib64"):
        if os.path.islink(d):
            cmd += ["--symlink", os.readlink(d), d]
        elif os.path.isdir(d):
            cmd += ["--ro-bind", d, d]
    for f in ("/etc/ld.so.cache", "/etc/alternatives", "/etc/localtime"):
        cmd += ["--ro-bind-try", f, f]
    cmd += ["--proc", "/proc", "--dev", "/dev"]
    for d in _python_dirs():
        cmd += ["--ro-bind", d, d]
    cmd += ["--ro-bind", os.path.abspath(__file__), "/sandbox/code_guard.py"]
    for key, value in (("PATH", "/usr/bin:/bin"), ("HOME", "/sandbox"), ("LANG", "C.UTF-8"),
                       ("OPENBLAS_NUM_THREADS", "4"), ("OMP_NUM_THREADS", "4"), ("MKL_NUM_THREADS", "4")):
        cmd += ["--setenv", key, value]
    # zuletzt alles schreibgeschützt, damit sich keine Dateien im Arbeitsspeicher ablegen lassen
    cmd += ["--chdir", "/sandbox", "--remount-ro", "/dev", "--remount-ro", "/",
            "--", sys.executable, "-I", "-B", "-c", _BOOT]
    return cmd


def forbid_new_namespaces() -> None:
    """seccomp-Filter für diesen Prozess und alle, die er startet; er lässt sich nicht mehr entfernen.

    Ohne ihn könnte der Code in der Sandbox eigene Namespaces anlegen (unshare), sich darin
    beschreibbare Laufwerke einhängen und viel mehr vom Linux-Kernel erreichen.
    """
    import ctypes
    import errno

    # Prozessor: (Kennung im Filter, Nummern von clone, unshare, setns)
    arch = {"x86_64": (0xC000003E, 56, 272, 308), "aarch64": (0xC00000B7, 220, 97, 268)}.get(os.uname().machine)
    if not arch or sys.maxsize <= 2 ** 32:
        raise OSError(f"Für den Prozessor {os.uname().machine} gibt es keinen Sandbox-Filter.")
    audit, clone, unshare, setns = arch
    clone3 = 435
    namespace_flags = 0x7E020000  # alle CLONE_NEW…-Schalter

    load, equal, at_least, any_bit, ret = 0x20, 0x15, 0x35, 0x45, 0x06  # BPF-Befehle
    allow, deny = 0x7FFF0000, 0x00050000  # SECCOMP_RET_ALLOW, SECCOMP_RET_ERRNO
    rules = [  # (Befehl, Sprung wenn wahr, Sprung wenn falsch, Wert)
        (load, 0, 0, 4),                    # Prozessor-Kennung
        (equal, 1, 0, audit),
        (ret, 0, 0, deny | errno.EPERM),    # fremde Aufrufart (z. B. 32 Bit)
        (load, 0, 0, 0),                    # Nummer des Systemaufrufs
        (at_least, 0, 1, 0x40000000),       # x32-Aufrufe unter x86_64
        (ret, 0, 0, deny | errno.EPERM),
        (equal, 0, 1, clone3),              # Schalter nicht prüfbar: die C-Bibliothek nimmt dann clone
        (ret, 0, 0, deny | errno.ENOSYS),
        (equal, 5, 0, unshare),
        (equal, 4, 0, setns),
        (equal, 0, 2, clone),
        (load, 0, 0, 16),                   # erstes Argument von clone
        (any_bit, 1, 0, namespace_flags),
        (ret, 0, 0, allow),
        (ret, 0, 0, deny | errno.EPERM),
    ]

    class Rule(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]

    class Program(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Rule))]

    program = Program(len(rules), (Rule * len(rules))(*[Rule(*r) for r in rules]))
    libc = ctypes.CDLL(None, use_errno=True)
    zero = ctypes.c_ulong(0)
    # PR_SET_NO_NEW_PRIVS, danach PR_SET_SECCOMP im Filter-Modus
    if (libc.prctl(38, ctypes.c_ulong(1), zero, zero, zero) != 0
            or libc.prctl(22, ctypes.c_ulong(2), ctypes.byref(program), zero, zero) != 0):
        raise OSError(ctypes.get_errno(), "Der Sandbox-Filter lässt sich nicht aktivieren")


def sandbox_child() -> int:
    """Läuft IN der Sandbox: Code von stdin ausführen, Ausgabe oder Fehlertext nach stdout."""
    import io
    import resource
    from contextlib import redirect_stdout

    code = sys.stdin.buffer.read().decode("utf-8")
    try:
        forbid_new_namespaces()
    except Exception as e:
        sys.stdout.buffer.write(f"Die Sandbox ist unvollständig ({e}). Kein Code ausgeführt.".encode("utf-8"))
        return _NO_SANDBOX
    try:
        # wird der Speicher knapp, beendet Linux zuerst diesen Prozess
        with open("/proc/self/oom_score_adj", "w") as f:
            f.write("1000")
    except OSError:
        pass
    limits = [(resource.RLIMIT_FSIZE, _FILE_LIMIT), (resource.RLIMIT_CORE, 0)]
    # Ab Linux 5.14 zählt das Prozess-Limit nur innerhalb der Sandbox, davor alle Prozesse des Benutzers
    release = re.match(r"(\d+)\.(\d+)", os.uname().release)
    if release and (int(release[1]), int(release[2])) >= (5, 14):
        limits.append((resource.RLIMIT_NPROC, 64))
    for limit, value in limits:
        resource.setrlimit(limit, (value, value))
    output = io.StringIO()
    try:
        limit_resources()
        with redirect_stdout(output):
            exec(code, make_exec_globals())
        status, text = 0, output.getvalue()
    except BaseException as e:
        status, text = _CODE_ERROR, str(e) or type(e).__name__
    if len(text) > OUTPUT_LIMIT:
        text = text[:OUTPUT_LIMIT] + "\n… (Ausgabe gekürzt)"
    sys.stdout.buffer.write(text.encode("utf-8", "replace"))
    sys.stdout.flush()
    return status


def run_sandboxed(code: str, timeout: int = TIMEOUT_S):
    """Führt Code in der Sandbox aus. Rückgabe (status, text): ok, error, timeout oder unavailable."""
    bwrap = shutil.which("bwrap") if sys.platform.startswith("linux") else None
    if not bwrap:
        return "unavailable", _INSTALL_HINT
    try:
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            # env: Der erste Prozess der Sandbox ist bwrap selbst, seine Umgebung wäre dort lesbar
            proc = subprocess.run(sandbox_command(bwrap), input=code.encode("utf-8", "replace"),
                                  stdout=out, stderr=err, timeout=timeout, env={"PATH": "/usr/bin:/bin"})
            out.seek(0)
            text = out.read(4 * OUTPUT_LIMIT + 100).decode("utf-8", "replace")
            err.seek(0)
            detail = err.read(4000).decode("utf-8", "replace").strip()
    except subprocess.TimeoutExpired:
        return "timeout", ""
    except OSError as e:
        return "unavailable", str(e)
    # der Code kann auch direkt nach stdout schreiben, an der Kürzung in der Sandbox vorbei
    if len(text) > OUTPUT_LIMIT + 40:
        text = text[:OUTPUT_LIMIT] + "\n… (Ausgabe gekürzt)"
    if proc.returncode == _NO_SANDBOX:
        return "unavailable", text
    if proc.returncode == 0:
        return "ok", text
    if proc.returncode == _CODE_ERROR:
        return "error", text
    if detail.startswith("bwrap:"):
        return "unavailable", f"Die Sandbox startet nicht ({detail.splitlines()[0]}). Kein Code ausgeführt."
    return "error", detail.splitlines()[-1] if detail else f"Prozess beendet (Code {proc.returncode})"


def execute(code: str):
    """Prüfen und in der Sandbox ausführen. Rückgabe (status, Meldung für das Modell)."""
    blocked = check_python_code(code)
    if blocked:
        return "blocked", blocked
    status, text = run_sandboxed(code)
    return status, {
        "ok": f"✅ Code ausgeführt\nOutput:\n{text}",
        "error": f"❌ Fehler: {text}",
        "timeout": f"❌ Timeout ({TIMEOUT_S}s) – Code abgebrochen",
        "unavailable": f"❌ run_python ist nicht verfügbar: {text}",
    }[status]
