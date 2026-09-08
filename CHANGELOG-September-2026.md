# Changelog – September 2026 (Security-Härtung)

## Dateizugriff
- Home-Verzeichnis nicht mehr pauschal erlaubt – nur noch `config.json` (`allowed_base` + `allowed_paths`)
- `~/.ssh`, `/etc/passwd`, `/tmp` u.ä. werden blockiert (`read_file`, `cat`, `ls`, `mkdir`)
- Doppelter Pfad-Check zu einem vereint

## Prompt-Injection: Web-Inhalte markiert
- Alle 18 externen Tools (Suche, Trends, News, Wetter, Browser, Scraper, Tavily, DuckDuckGo, Amazon) kennzeichnen Fremd-Content als `[UNTRUSTED WEB]`
- Modell wird angewiesen, darin enthaltene Befehle zu ignorieren
- Fehlermeldungen bleiben unverändert lesbar

## Memory-Vergiftung: Quarantäne
- Auffällige Inhalte (`ignore previous`, Fake-System-Tags, Tool-Aufrufe) landen 30 Tage in Quarantäne statt im Langzeitgedächtnis
- Neue Tools: `review_quarantine()` prüfen, `purge_memory()` löschen
- Skill-Vorschläge zeigen volle Argumente; auffällige nur mit `force=True` übernehmbar
- Gespeicherte Inhalte + Projekt-RAG tragen Herkunfts-Kennzeichnung

## Netzwerk: nur noch localhost
- Launcher (`:9999`) und MCP (`:8000`) akzeptieren keine fremden Webseiten mehr (Origin-Check, kein CORS-`*`)
- MCP-Port kommt aus `config.json`
- iPad-Zugriff via LAN (`:8080`) unverändert

## Robustheit
- `run_command`: korrektes Quoting, Pfad-Prüfung für `cat`/`ls`/`mkdir`, alle Aufrufe geloggt, Timeout begrenzt (5–300 s)
- Fehlender `sys`-Import im Launcher ergänzt

## Unverändert
- Keine neuen Pflicht-Setup-Schritte, keine Cloud, keine Accounts
- `config.json`-Format abwärtskompatibel (nur `tavily_api_key` als optionales Feld ergänzt)
