"""Prüfung der Argumente für das Tool run_command (V.I.N.C.E.N.T. MCP-Server).

run_command startet Programme ohne Shell. Hier wird zusätzlich geprüft, dass die Datei-Argumente
im erlaubten Bereich liegen. Wie bei code_guard.py gilt: Das ist ein Schutz gegen Fehler des
Modells und gegen Prompt-Injection, keine vollständige Sandbox (ffmpeg kann z. B. aus Playlisten
heraus weitere Dateien öffnen).
"""
import os
import re

# Befehle, deren Argumente (außer Optionen) Pfade sind
PATH_COMMANDS = ("ls", "cat", "mkdir", "rm")

SHELL_OPERATORS = {"|", "||", "&", "&&", ";", ">", ">>", "<", "1>", "2>", "2>&1", "&>"}

# ffmpeg-Protokolle, die Netzwerk oder versteckte Dateizugriffe ermöglichen
_FFMPEG_PROTOCOLS = re.compile(r"^(concat|concatf|subfile|crypto|data|tcp|udp|rtp|unix|fd):", re.IGNORECASE)
# Pfade innerhalb von Filter-Ausdrücken, z. B. movie=/pfad oder drawtext=textfile=../x
_EMBEDDED_PATH = re.compile(r"""(?:[=:,;\[|'"])\s*((?:/|~/|\.\./)[^:,;'"\[\]|]*)""")
_ALWAYS_ALLOWED = ("/dev/null",)
_ALWAYS_ALLOWED_DIRS = ("/usr/share/fonts/",)


def check_args(argv: list, cwd: str, is_allowed, protected=()):
    """Prüft die Argumente eines zerlegten Kommandos.

    argv: Ergebnis von shlex.split, argv[0] ist der (bereits erlaubte) Befehl
    is_allowed: Funktion(pfad) -> bool
    protected: Ordner, die 'rm' weder selbst noch über einen übergeordneten Ordner löschen darf

    Rückgabe: (argv, None) mit aufgelöstem '~', oder (None, Fehlermeldung).
    """
    name, args = argv[0], argv[1:]
    if name not in PATH_COMMANDS and name != "ffmpeg":
        return argv, None

    operator = next((a for a in args if a in SHELL_OPERATORS), None)
    if operator:
        return None, (f"❌ '{operator}' funktioniert nicht: run_command startet keine Shell "
                      "(keine Pipes, Umleitungen oder verketteten Befehle). Befehle einzeln ausführen.")

    def full_path(p):
        return os.path.join(cwd, os.path.expanduser(p))

    def denied(p):
        return f"❌ Zugriff verweigert: {p} ist nicht im erlaubten Bereich"

    if name == "ffmpeg":
        for arg in args:
            if arg == "-safe":
                return None, "❌ ffmpeg-Option '-safe' ist nicht erlaubt."
            value = arg[5:] if arg.lower().startswith("file:") else arg
            if "://" in value or _FFMPEG_PROTOCOLS.match(value):
                return None, f"❌ ffmpeg: Netzwerk- und Sonderprotokolle sind nicht erlaubt ({arg})."
            candidates = _EMBEDDED_PATH.findall(value)
            if not value.startswith("-"):
                candidates.append(value)
            for p in candidates:
                if p in _ALWAYS_ALLOWED:
                    continue
                full = full_path(p)
                if os.path.realpath(full).startswith(_ALWAYS_ALLOWED_DIRS):
                    continue
                if not is_allowed(full):
                    return None, denied(p)
        return [name] + [os.path.expanduser(a) for a in args], None

    result = [name]
    options_done = False
    for arg in args:
        if not options_done and arg == "--":
            options_done = True
        elif not options_done and len(arg) > 1 and arg.startswith("-"):
            pass
        else:
            full = full_path(arg)
            if not is_allowed(full):
                return None, denied(arg)
            if name == "rm":
                target = os.path.realpath(full)
                for folder in protected:
                    folder = os.path.realpath(folder)
                    if os.path.commonpath([target, folder]) == target:
                        return None, (f"❌ Zugriff verweigert: '{arg}' würde den Ordner {folder} "
                                      "selbst löschen.")
            arg = os.path.expanduser(arg)
        result.append(arg)
    return result, None
