# Changelog – V.I.N.C.E.N.T.

## [1.6] – 2026-11-04 (Router-Modus)

### Launcher
- **Router-Modus** (Checkbox im UI): startet `llama-server` mit `--models-dir`, `--models-max` und `--models-preset`, statt ein einzelnes Modell zu laden. Modelle werden bei Bedarf geladen und gewechselt.
- **Max. gleichzeitige Modelle** (`--models-max`, Default 1, 0 = unbegrenzt) und optionales Preset-Feld (Pfad zu einer eigenen `modelfile.ini`).
- **`modelfile.ini` wird automatisch generiert**, wenn kein Preset angegeben ist: scannt alle `models_dir`-Pfade rekursiv und übernimmt die aktuellen UI-Einstellungen (Reasoning-Format, `n-cpu-moe`, Spec-Typ inkl. `spec-draft-n-max` und ngram-Parameter).
- **MTP-Erkennung:** neuer Endpoint `/api/mtp-models` listet `mtp-*.gguf` aus allen Modellordnern; der Spec-Typ wird passend vorgeschlagen. Warnung, wenn `draft-mtp` mit einem Draft-Modell ohne „mtp“ im Namen kombiniert wird.
- Status-Anzeige zeigt im Router-Modus „Router-Modus“ statt eines Modellnamens.
- Mehrere `models_dir`-Pfade werden durchgängig unterstützt (nicht nur der erste).

### MCP-Server
- **Self-Learning:** neuer `@_recorded`-Decorator zeichnet Tool-Aufrufe automatisch auf (Browser-, Skill-, Status- und Diagramm-Tools); Datei-Tools protokollieren Erfolg und Fehler.
- **`delete_file`:** Neuer Parameter `force`. Dateien oder Verzeichnisse über 1 MB werden nur mit `force=True` gelöscht.
- **Dateischreiben:** `write_file` schreibt atomar (Temp-Datei + `os.replace`), legt bei vorhandener Datei ein `.bak` an; der Chunk-Workaround für das JSON-Parser-Limit ist entfallen. `append_to_file` meldet nicht existierende Dateien verständlich.
- **`run_command`:** Prefix-Prüfung jetzt tokenbasiert statt per String-Prefix (verhindert Umgehung).
- **Browser-Subprocess:** 10-s-Timeout bei ausbleibender Antwort.
- Interner Wrapper `_is_path_allowed` entfernt, einzige Implementierung ist `is_path_allowed`.
- Backups bei Edit-Operationen mit Zeitstempel (`.bak_YYYYMMDD_HHMMSS`).

### Config / Doku
- `config.example.json`: `models_dir` als Liste von Pfaden.
- README: Abschnitt „Known Open Issues“. HANDBUCH: Vorlesen EN/DE (Stimmen Thorsten, Martin, Victoria).

---

## [1.5] – 2026-09 (Oktober-Stand)

### Security-Härtung
- Dateizugriff: Home-Verzeichnis nicht mehr pauschal erlaubt – nur noch `config.json` (`allowed_base` + `allowed_paths`); `~/.ssh`, `/etc/passwd`, `/tmp` u.ä. blockiert; doppelter Pfad-Check vereint.
- Prompt-Injection: alle 18 externen Tools markieren Fremd-Content als `[UNTRUSTED WEB]`; Fehlermeldungen bleiben lesbar.
- Memory-Vergiftung: auffällige Inhalte (`ignore previous`, Fake-System-Tags, Tool-Aufrufe) landen 30 Tage in Quarantäne (`review_quarantine`, `purge_memory`); Skill-Vorschläge zeigen volle Args, auffällige nur mit `force=True`.
- Netzwerk: Launcher (`:9999`) und MCP (`:8000`) nur localhost (Origin-Check, kein CORS-`*`); MCP-Port aus `config.json`; iPad (`:8080`) unverändert.
- `run_command`: `shlex.split()`, Pfad-Prüfung für `cat`/`ls`/`mkdir`, alle Aufrufe geloggt, Timeout 5–300 s.
- Fehlender `sys`-Import im Launcher ergänzt.

### Features
- CUDA-Sensoren (RTX 3060): GPU-Temp, Power, Fan %, Util, VRAM in Chat-Sidebar.
- GPT-OSS-Jinja-Fix (`gptoss_fixed.jinja`) für Claude-CLI-500er.
- CPU-MoE-Flag im Launcher (`--n-cpu-moe`, Default 15).
- UI-Grid-Overflow-Fix.
- Chat-TTS via Kokoro (`/api/tts`, satzweise, EN-only, Gradio `:7865`).

### Fixes
- Browser-navigate-Bug (`action`→`nav_action`, back/forward ohne URL); Playwright-Chromium nachinstalliert.
- MTP-Unterstützung im Launcher (`--spec-type draft-mtp`, optionales `-md`-Feld); Spec-Typ-Wahl (draft-mtp/draft/ngram/ngram-mod) + Auto-Erkennung von `mtp-<name>.gguf`.
- `models_dir` als String oder Liste.

### Unverändert
- Keine neuen Pflicht-Setup-Schritte, keine Cloud, keine Accounts.
- `config.json` abwärtskompatibel (`tavily_api_key` optional, `models_dir` als String oder Liste).

---

## [1.4-rc2] – 2026-08-07

## [1.4-rc2] – 2026-08-07

### llama.cpp b10295 Reasoning fix

- **Reasoning-Dropdown von `On/Off` auf `--reasoning-format` umgestellt** (`auto` / `deepseek` / `deepseek-legacy` / `none`, Default `deepseek`). Die alten Flags `--reasoning on/off` steuern in b10268+ das Parsing nicht mehr sauber – dadurch leckten rohe Reasoning-/Tool-Tags (` response`, `<tool_call>`, `<|im_start|>`/`<|im_end|>`) in den sichtbaren Chat-Output von Claude Code.
  - `deepseek` extrahiert Reasoning sauber nach `reasoning_content` und Tool-Calls als strukturierte `tool_calls`.
- **Verifiziert gegen `llama-b10295`** mit `Qwen3.5-9B-Q4_K_M.gguf` und `gemma-4-E4B-it-Q5_K_M.gguf`: strukturierte `tool_calls` + leeres `content`, keine gelachten Tags.
- Template-Wahl (`Default` / `Qwen CLI FIX` / `Gemma CLI FIX`) bleibt als optionaler `--jinja`-Fallback erhalten, wird aber nicht mehr erzwungen.

---

## [1.4-rc1] – 2026-07-28

Release-Fokus: Self-Learning system sinnvoll gemacht + toter Code beseitigt.

### Self-Learning überarbeitet

Das alte System hat automatisch Skills erstellt – oft Unsinn (z.B. "3× hackernews_trending"). Das neue System schlägt Kandidaten vor, aber **kein Skill wird ohne Bestätigung angelegt**.

- **Threshold 3 → 6:** Erst nach 6 gleichen Aufrufen wird ein Muster als Kandidat vorgeschlagen (vorher 3 → zu viel Rauschen).
- **Skill-Kandidaten-Whitelist:** Nur Trends/Search/Web-Tools (`browser_open`, `google_trends`, `tavily_search`, etc.) werden überhaupt als Kandidaten in Betracht gezogen. Datei-/Code-Tools sind bewusst ausgeschlossen – zu variabel, ergeben keine sinnvollen Skills.
- **Separate Vorschlags-Collection:** Neue ChromaDB-Collection `jarvis_skill_suggestions` speichert Kandidaten. Erst `approve_skill(id)` macht sie zu echten Skills in `jarvis_skills`.
- **Neue Tools:**
  - `review_learned_patterns()` – Zeigt alle offenen Skill-Vorschläge
  - `approve_skill(pattern_id)` – Bestätigt einen Vorschlag und erstellt den Skill
  - `reject_skill(pattern_id)` – Verwirft einen Vorschlag

### Aufgeräumt

- **Async-Referenzblock komplett entfernt** (~162 Zeilen): `async def _async_browser_open` (inkl. Duplikat), `_async_browser_snapshot`, `_async_structured_snapshot`, `_async_browser_click`, `_async_auto_click`, `_async_browser_type`, `_async_browser_screenshot`, `_async_browser_navigate` – nie verbundener Referenzcode.
- **`_deprecated_navigate`** entfernt – Wrapper, nirgends aufgerufen.
- **`_sync_browser_close`** entfernt – wird nicht genutzt.
- **`_sync_browser_snapshot`** entfernt – wird nicht genutzt.

---

## [1.1.0-rc1] – 2026-07-24/25

### Sicherheit

- **`run_python` isoliert:** Führt Code jetzt in einem separaten `multiprocessing.Process` statt direkt im Hauptprozess aus. Neue Hilfsfunktion `_exec_in_process` übernimmt `exec()` inklusive korrektem `redirect_stdout`. Harter 10-Sekunden-Timeout verhindert, dass Endlosschleifen den Server blockieren.
  - Behebt zusätzlich einen Funktions-Bug: `print()`-Ausgaben landeten vorher nie im zurückgegebenen Output (`io.StringIO()` wurde nie mit `redirect_stdout` verbunden).
  - Der bisherige String-Blocklist-Check (`forbidden = ["import os", ...]`) entfernt – war durch simple Umgehungen (`__import__`, String-Konkatenation) wirkungslos und ist durch die Prozessisolation ersetzt.

- **`run_command`-Whitelist verschärft:** `_SAFE_COMMANDS` bereinigt – Interpreter-Prefixe (`python3`, `python`, `node`, `npm`, `pip`) und `rm` entfernt, da diese als Prefix-Whitelist praktisch unbeschränkten Code-/Dateizugriff erlaubten. Verbleibend: `npx hyperframes`, `npx skills` (+ `--yes`-Varianten), `ffmpeg`, `ls`, `cat`, `mkdir`.

- **SSRF-Schutz für Browser-Navigation:** Neue Funktion `_is_safe_url()` prüft Schema (nur `http`/`https`) und löst den Hostnamen auf, um private/interne IP-Adressen zu blocken (schützt u. a. vor Zugriffen auf `169.254.169.254`, `127.0.0.1`, private Netzbereiche). In `_ensure_url()` eingebaut, wirft `ValueError` bei unsicheren URLs. Alle Aufrufer (`_sync_browser_open`, `_sync_browser_navigate`) fangen das jetzt mit `try/except` ab.

### Aufgeräumt (toter Code + Duplikate entfernt)

Datei um insgesamt **290 Zeilen** geschrumpft (3160 → 2870). Bereinigt wurden:

- **Async-Referenzblock komplett entfernt** (162 Zeilen): `async def _async_browser_open` (inkl. Duplikat), `_async_browser_snapshot`, `_async_structured_snapshot`, `_async_browser_click`, `_async_auto_click`, `_async_browser_type`, `_async_browser_screenshot`, `_async_browser_navigate` – nie verbundener Referenzcode, Browser-System arbeitet komplett synchron via subprocess.
- **`_deprecated_navigate`** entfernt – Wrapper zu `_sync_browser_navigate`, nirgends aufgerufen.
- **`_sync_browser_close`** entfernt – wird nicht genutzt (Tabs werden über `browser_close_tab`-Tool geschlossen).
- **`_sync_browser_snapshot`** entfernt – wird nicht genutzt (`browser_snapshot`-Tool nutzt `structured_snapshot` direkt).

- `_sync_browser_navigate` (2× → 1×)
- `browser_search_products` (2× → 1×, dabei das bessere `_record_tool_call`-Logging aus der toten Kopie in die aktive Version übernommen statt verloren zu geben)
- `_deprecated_snapshot` (3 Generationen → komplett entfernt, inkl. der zugehörigen `_sync_browser_snapshot`-Implementierung, die dadurch verwaist war)
- `_deprecated_structured` (3 Generationen → komplett entfernt; die mittlere Generation war zudem defekt, referenzierte eine nicht existierende Variable `url`)
- `_deprecated_click`, `_deprecated_auto_click`, `_deprecated_type`, `_deprecated_screenshot` (je 2× → 1×)
- `browser_navigate` (Tool-Ebene, 2× → 1×)
- `browser_screenshot` (Tool-Ebene, 2× → 1×; die bessere Version mit `filepath`/`path`-Kompatibilität blieb erhalten)
- `_sync_structured_snapshot`, `_sync_browser_click` (je 2× → 1×, beide weiterhin aktiv genutzte Implementierungen)

### Neue Funktionalität

- **`get_memory(memory_id)`** hinzugefügt – ruft den vollständigen, ungekürzten Inhalt einer einzelnen Erinnerung per ID ab. Bisher gab es nur `list_memory`/`search_memory`, die den Inhalt auf 100 Zeichen kürzen.

### Bugfix

- **ID-Anzeige in `list_memory` korrigiert:** Die Zeile `mem_id[:20]...` hängte immer ein `...` an die ID an, unabhängig davon, ob die ID (immer exakt 16 Zeichen: `mem_` + 12 Hex-Zeichen) überhaupt gekürzt wurde. Das führte dazu, dass beim Weiterreichen der augenscheinlich „gekürzten“ ID an `get_memory` bzw. `delete_memory` die drei Punkte mit übergeben wurden und die ID dadurch nie gefunden wurde. Fix: `(ID: {mem_id})` ohne Kürzung und ohne `...`-Suffix. Behebt damit den Abruf über `get_memory` **und** das Löschen über `delete_memory` gleichermaßen, da beide vom selben Anzeigefehler betroffen waren.

### Bekannt, noch offen

- `run_command` nutzt weiterhin `cmd_str.split()` statt `shlex.split()` – kein Escaping/Quoting-Handling.
- `_is_path_allowed()` ist doppelt definiert (Zeile 69 mit `ALLOWED_PATHS`, Zeile 1343 mit `config.json`). Die zweite überschreibt die erste – alte Version ist toter Code.
- `web_scrape` / `deep_scrape` laufen weiterhin ohne Zeit-/Ressourcenlimit (kein Sicherheitsrisiko mehr seit SSRF-Fix, aber ein hängender Crawl kann den Server länger blockieren).
- Status-Endpoint zeigt einen hartkodierten `"tools_count": 52` an, der nicht mit der echten Anzahl übereinstimmte.
