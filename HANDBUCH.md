# bagueDev Community Launcher v1 – Das Handbuch

> Stand: Oktober 2026 · Version 1.2-RC1

---

## Inhaltsverzeichnis

1. [Warum dieses Toolkit?](#1-warum-dieses-toolkit)
2. [Low‑Budget Philosophie](#2-low-budget-philosophie)
3. [Die Hardware‑Realität 2024–2026: Die RAM‑Krise](#3-die-hardware-realitat-20242026-die-ramkrise)
4. [Die Hardware, die wirklich zählt](#4-die-hardware-die-wirklich-zahlt)
5. [Was dieses Toolkit IST (und was nicht)](#5-was-dieses-toolkit-ist-und-was-nicht)
6. [Abgrenzung zu anderen Tools](#6-abgrenzung-zu-anderen-tools)
7. [Die Bausteine](#7-die-bausteine)
8. [Datenschutz & Kontrolle](#8-datenschutz--kontrolle)
9. [Loslegen](#9-loslegen)
10. [Developer Notes](#10-developer-notes)

> **Springe direkt zu:** [Developer Notes](#10-developer-notes)

---

## 1. Warum dieses Toolkit?

### Kurzfassung:
Die KI‑Welt ist explodiert. Frameworks, Wrapper, Layer, Plugins, 1000 Flags, 20 Startskripte, 50 inkompatible Versionen.
Die meisten User wollen aber einfach nur ein Modell starten, nicht ein halbes DevOps‑Studium absolvieren.

### Unser Ansatz:
Weniger Overhead, weniger Magie, weniger Chaos.
Mehr Kontrolle, mehr Übersicht, mehr Fokus.

### Kernproblem:
Die KI‑Industrie baut Tools für Rechenzentren, nicht für Menschen.
Wir bauen Tools für Menschen.

---

## 2. Low‑Budget Philosophie

### Die Realität:
Nicht jeder hat eine 5090, 128 GB RAM oder ein KI‑Cluster.
Viele haben ältere Laptops, gebrauchte Workstations oder Mini‑PCs.

### Unsere Philosophie:

- Läuft auf alter Hardware
- Läuft ohne GPU
- Läuft ohne Cloud
- Läuft ohne 20 GB Dependencies
- Läuft auch noch in 10 Jahren

### Warum das wichtig ist:
Software wird jedes Jahr schwerer, nicht leichter.
Wir drehen den Trend um.

---

## 3. Die Hardware‑Realität 2024–2026: Die RAM‑Krise

Die KI‑Industrie hat eine neue Form von Inflation geschaffen:
🔥 RAM ist das neue Gold

- 2020: 32 GB RAM = Luxus
- 2024: 64–128 GB RAM = „Einsteiger‑KI‑Setup“
- 2026: 256 GB RAM = „für ernsthafte Modelle“

Das ist absurd.

🔥 Warum RAM so teuer wurde

- KI‑Rechenzentren kaufen weltweit alles leer
- HBM‑Produktion ist limitiert
- Nachfrage explodiert schneller als die Fertigung
- Consumer‑Hardware wird künstlich verknappt

→ Ergebnis: Preise steigen, Verfügbarkeit sinkt.

🔥 Und trotzdem: Lokale Modelle brauchen NICHT so viel

Ein 7B‑Modell läuft auf:

- 8 GB RAM
- 4 GB VRAM
- einem alten ThinkPad

Wenn die Software effizient ist.
Genau deshalb existiert dieses Toolkit.

---

## 4. Die Hardware, die wirklich zählt

Während die Industrie ihre H100-Cluster hochzieht, sieht die Realität für normale Menschen anders aus.

### Gebrauchte Hardware ist der beste Deal

VRAM ist der limitierende Faktor – und gebrauchte GPUs liefern genau das, oft zum halben Preis:

| GPU | VRAM | Neupreis | Gebraucht 2026 | Perfekt für |
|---|---|---|---|---|
| **RTX 3060 12GB** | 12 GB | ~330 € | ~150–200 € | 7B Modelle, Einsteiger |
| **RTX 3080** | 10 GB | ~700 € | ~350–400 € | 7B–13B, solide |
| **RTX 3090** | 24 GB | ~1.500 € | ~800–900 € | 13B–34B, bester Deal |
| **RX 6800 XT** | 16 GB | ~650 € | ~300–350 € | 7B–13B, AMD-Alternative |
| **RTX 4070 Ti** | 12 GB | ~800 € | ~600–650 € | 7B Modelle, effizient |
| **RTX 4090** | 24 GB | ~1.800 € | ~1.700–2.200 € | 34B–70B, High-End |

Was uns das sagt: Eine gebrauchte RTX 3090 für ~800 € schlägt fast jede Neukarte – doppelter VRAM zum halben Preis. Und wer gar keine GPU hat, startet einfach mit CPU-only. llama.cpp läuft auf jeder CPU.

**Deshalb ist dieses Toolkit darauf ausgelegt, genau diese gebrauchten, aber leistungsfähigen Konfigurationen maximal auszulasten.** Kein Overhead, keine unnötigen Libraries – nur Software, die macht was sie soll.

### Klassische Computer altern nicht

Während KI-GPUs im Wert verfallen, bleibt ein normaler PC stabil:

- Ein gebrauchter **ThinkPad X280** für 150 € läuft heute noch alles
- Ein **Dell Precision Workstation** für 300 € reicht für 7B–13B Modelle
- Ein **selbstgebauter PC von 2015** ist heute noch genau so brauchbar

Die Vorstellung, man müsse alle zwei Jahre upgraden, kommt von der Industrie – nicht von der Realität.

### Der Trend zu Small Language Models

Die spannendste Entwicklung im KI-Bereich ist aktuell: **Modelle werden kleiner, nicht grösser.**

- **Gemma 4B** von Google – performt auf dem Niveau von älteren 7B–13B Modellen, braucht aber nur 4 GB VRAM
- **Qwen 2.5 7B** – läuft auf jeder Mittelklasse-GPU und liefert beeindruckende Ergebnisse
- **MoE (Mixture of Experts)** – Modelle wie Qwen 3.6 MoE oder Mixtral aktivieren nur einen Bruchteil ihrer Parameter pro Token. Eine 14B MoE kann auf einer 8 GB GPU laufen
- **Phi-3 / Phi-4** von Microsoft – unter 4B Parametern, aber nah an grossen Modellen

Was das bedeutet: In naher Zukunft werden **Small Language Models (SLMs)** die meiste Arbeit erledigen. Du wirst kein 70B Modell mehr brauchen – ein gut trainiertes 7B oder 9B MoE reicht für 90 % aller Aufgaben.

Und genau deshalb werden **Gamer-GPUs** mit 8–16 GB VRAM zur idealen Plattform: günstig gebraucht, leistungsfähig genug, und für die kommende Generation effizienter Modelle perfekt dimensioniert.

Wir optimieren für das, was Menschen wirklich haben:

- Alte GPUs (GTX 1080, Vega 56, RTX 2070)
- Gebrauchte Workstations und Laptops
- Mini-PCs mit iGPUs
- Reine CPU-Systeme

**Eine RTX 3090 gebraucht + ein 12B Modell + dieses Toolkit = lokale KI für unter 1.000 €.**

Die beste Hardware ist die, die du schon hast. Mit der richtigen Software.

---

## 5. Was dieses Toolkit IST (und was nicht)

✔️ Was es IST

- Ein schlanker Launcher für lokale Modelle
- Ein 50‑Tool‑MCP‑Server für echte Automatisierung
- Ein Werkzeugkasten für Entwickler, Bastler und Low‑Budget‑User
- Ein System, das auch auf alter Hardware funktioniert

❌ Was es NICHT ist

- Kein Ersatz für OpenAI
- Kein Framework‑Friedhof
- Keine 500‑MB‑Electron‑App
- Kein „wir installieren 20 Libraries für eine simple Aufgabe“

---

## 6. Abgrenzung zu anderen Tools

Ja, es gibt bereits Tools wie **Ollama**, **LM Studio** oder **GPT4All**.
Und ja, viele davon haben mehr Komfort-Features – aber hier ist, was **nur wir** können:

### Feature-Vergleich

| Funktion | Community Launcher | Ollama | LM Studio |
|---|---|---|---|
| **MCP Server (50+ Tools)** | ✅ integriert | ❌ (nur via Dritt-Bridges) | ⚠️ nur Host (fremde Server), kein eigener Tool-Server |
| **Browser-Automation** | ✅ Playwright (klicken, tippen, Tabs, Screenshots) | ❌ | ⚠️ via MCP-Server (z.B. playwright-mcp), kein eingebauter Browser |
| **ChromaDB Memory** | ✅ semantisches Langzeitgedächtnis + Skill-Vorschläge (human-in-the-loop) | ❌ | ❌ |
| **Live-Hardware-Telemetrie** | ✅ GPU-Temp, Junction, Lüfter, PPT | ❌ | ⚠️ nur Last/VRAM/tok-s, keine Temp/Lüfter/Power |
| **Claude Code CLI Support** | ✅ Qwen+Gemma Template-Fixes | ❌ | ❌ |
| **MCP Proxy** | ✅ Tool-Calls an andere MCP-Server | ❌ | ❌ |
| **WebUI von jedem Gerät** | ✅ browserbasiert, LAN | ❌ (Desktop-App + CLI, kein Browser-/LAN-UI) | ⚠️ nur Desktop, kein Browser-/LAN-Zugriff |
| **Telemetrie** | **keine** | ⚠️ keine Nutzungs-Telemetrie, aber Update-/Katalog-Calls (teils nicht abschaltbar) | ⚠️ kein Tracking, aber Modell-Suche via eigenem Proxy + Update-Checks |
| **Modell-Download** | ❌ manuell | ✅ `ollama pull` | ✅ integriert |
| **Modell-Bibliothek** | ❌ keine Galerie | ✅ gross | ✅ gross |

*LM Studio ist seit v0.3.17 MCP-Host (fremde Server inkl. Playwright nutzbar, kein eigener Tool-Server). Ollama: keine Nutzungs-Telemetrie, aber stündliche Update-Checks + Modell-Katalog-Calls, teils nicht abschaltbar.*

### Philosophie

Ollama ist gut, wenn du **20 Modelle automatisch verwalten** willst.
LM Studio ist gut, wenn du eine **polierte Desktop-Oberfläche** willst.

Wir sind gut, wenn du:
- Einen **MCP-Server mit 50+ Tools** brauchst (Browser, Memory, Dateien, Web-Scraping, Trends)
- **Hardware überwachen** willst (GPU-Temperatur, Lüfter, Stromverbrauch)
- **Claude Code CLI** mit lokalen Modellen nutzen willst (Qwen & Gemma funktionieren out-of-the-box)
- **100% offline** arbeiten willst – kein Telemetrie, kein Account, keine Cloud
- Ein **einzelnes Modell** starten willst und es soll **einfach funktionieren**

Beide Ansätze sind legitim.
Wir haben uns für den einfachen, local-first Weg entschieden.

---

## 7. Die Bausteine

### Launcher (Port 9999)

Startet llama.cpp ohne Flag‑Hölle.
Einfach Modell auswählen → starten → fertig.

### Chat UI

- Live‑Metriken
- Token‑Speed
- RAM‑Verbrauch
- GPU‑Offload
- Model‑Switching

### V.I.N.C.E.N.T. MCP Server (Port 8000)

50+ Tools für:

- Filesystem
- Web
- Shell
- Parsing
- Automatisierung
- Developer‑Workflows

### Continue.dev / VS Code Integration

Gleiches Modell im Editor.
Keine Cloud, keine API‑Kosten.

---

## 8. Datenschutz & Kontrolle

- 100% lokal
- Keine Cloud
- Keine Telemetrie
- Keine API‑Keys
- Keine versteckten Calls

Du behältst die Kontrolle.
Nicht Big Tech.

---

## 9. Loslegen

### Kurzanleitung:

```bash
# 1. Repository klonen
git clone https://github.com/bagueDev/community-launcher
cd community-launcher

# 2. Venv erstellen
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt
playwright install chromium

# 4. Config anlegen und Pfade anpassen
cp config.example.json config.json
# → config.json öffnen: llama-server-Pfad, Modelle-Verzeichnis, Workspace eintragen

# 5. Launcher starten
python3 bagueDEV_Launcher.py

# 6. Im Browser öffnen
# → http://localhost:9999

# 7. Modell auswählen und starten
# → Chat öffnen, Tools aktivieren, fertig.
# → Vorlesen (EN): 🔊-Haken + Stimme (Liam/Heart/Bella/Emma) → Antwort wird via Kokoro
#   auf :7865 vertont (CPU-Modus, Gradio muss laufen). WAV per Player downloadbar.
#
# VRAM-Recipe (CUDA, RTX 3060 12GB): ngl ist ABSOLUT (Layer), kein Prozent!
# → ngl ≈ Layer × (VRAM frei − ~2 GB Reserve) / Modell-GB (z.B. 26B/30L → ngl 15)
# → Passt es nicht: ngl halbieren, dann ctx 4096→2048. Ohne -ngl fittet llama selbst.
#
# MoE-Recipe (26B/30L, 12GB, Sweet Spot Stufe 15, gemessen):
# → -ot ".ffn_.*_exps.=CPU" = alle Experten CPU, max. Reserve (~4 GB belegt).
# → --n-cpu-moe 15 (ohne -ot!) = ~10,2 GB, ~30 t/s Gen, ~115 t/s Prompt (Startwert: 17/55 Full-CPU).
# → Faustformel: Experten ≈ 420 MB/Layer; ngl 99 lassen, nur n-cpu-moe variieren (20→15→10 testen).
# → Eng am Limit: bei OOM/spontanen Abbrüchen auf 16/17 zurück. ctx 8192 nur mit mehr CPU-Anteil.
```

Das war's. Kein Docker, kein Kubernetes, kein 10‑Seiten‑Setup.

---

## 10. Developer Notes

### Projektstruktur

| Datei | Zweck |
|---|---|---|
| `bagueDEV_Launcher.py` | WebUI Launcher (Port 9999) + Chat. Single-File, stdlib only. |
| `VINCENT_MCP.py` | V.I.N.C.E.N.T. MCP Server (Port 8000). 50+ Tools, ChromaDB, h11. |
| `start.sh` | Startet Launcher + MCP in zwei Terminal-Tabs. |
| `config.json` | Lokale Konfiguration (Pfade, Ports, erlaubte Verzeichnisse). Nicht im Repo. |
| `config.example.json` | Vorlage mit Platzhaltern → kopieren, anpassen, starten. |
| `requirements.txt` | Python-Dependencies (u.a. `sentence-transformers` für Skills). |
| `browser_subprocess.py` | Playwright-Browser-Prozess (stdin/stdout). Wird vom MCP Server automatisch gestartet. |
| `AGENTS.md` | KI-Assistenten-Konfiguration (File Writing Strategy, Regeln). |
| `qwen_fixed.jinja` | Qwen Chat-Template ohne system-first-Prüfung (Fix für Claude Code CLI). |
| `gemma_fixed.jinja` | Gemma Chat-Template mit Pre-Scan für spätere System-Messages (Fix für Claude Code CLI). |
| `HANDBUCH.md` | Dieses Handbuch. |

### Coding Conventions

- **Single-File**: Wo möglich alles in einer Datei (`bagueDEV_Launcher.py`).
- **stdlib only**: Launcher hat null Dependencies. MCP Server nutzt Drittanbieter-Pakete nur wo nötig.
- **Keine Type Hints**: Nicht erwünscht, ausser explizit angefragt.
- **Keine HTML/CSS-Kommentare**: UI-Code wird nicht kommentiert.
- **Raw Strings**: Eingebettetes HTML in Python mit `r"""..."""`.
- **Fehlermeldungen**: Auf Deutsch für den User.
- **Konfiguration extern**: Alle Pfade, Ports und Berechtigungen in `config.json` (zentral, von beiden Skripten gelesen). `config.example.json` als Vorlage im Repo.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Dein Browser                        │
│  http://localhost:9999 (Launcher + Chat)             │
└──────────┬──────────────────────────┬────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────────┐
│  bagueDEV_Launcher.py   │   │   VINCENT_MCP.py          │
│  (stdlib, single)    │   │   (h11, 50+ Tools)       │
│  Port 9999           │   │   Port 8000              │
└──────────┬───────────┘   └───────────┬──────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────┐   ┌──────────────────────────┐
│  llama-server        │   │   ChromaDB (.chroma/)    │
│  (llama.cpp binary)  │   │   (Memory + Skills)      │
│  Port 8080           │   │                          │
└──────────────────────┘   └──────────────────────────┘
```

### Qwen Jinja-Template Fix

**Problem:** Claude Code CLI sendet System-Messages nicht ausschliesslich an Position 0, sondern auch später im Kontext. Das originale Qwen-Template in llama.cpp (`--jinja`) wirft dann `System message must be at the beginning of the message list.` und bricht ab.

**Lösung:** `qwen_fixed.jinja` ist ein leicht modifiziertes Qwen-Chat-Template, das die system-first-Prüfung entfernt hat. Aktivierung im Launcher über die Checkbox «Qwen Chat-Template» (setzt `--chat-template-file qwen_fixed.jinja`). Ohne Checkbox wird das normale llama.cpp-`--jinja`-Template verwendet (Default).

**Hintergrund:** Qwen-Modelle verwenden das ChatML-Format (`<|im_start|>system/...`), das prinzipiell System-Messages an jeder Position erlaubt. Die Prüfung im originalen Template war eine unnötige Restriktion. `--chat-template chatml` funktioniert als Workaround, produziert aber nicht das volle Qwen-Template mit Tools- und Reasoning-Unterstützung.

### Gemma Jinja-Template Fix

**Problem:** Das originale Gemma-4-Template in llama.cpp (`--jinja`) verarbeitet System-Messages **nur an Position 0**. Claude Code CLI sendet System-Messages auch später im Kontext → das Template rendert sie als isolierten `<|turn>system...<turn|>`-Block, den Gemma nicht interpretieren kann. Folge: fehlerhafte Tool-Calls, `write_file`-Fallback.

**Lösung:** `gemma_fixed.jinja` scannt vor dem Rendern **alle** Messages nach `system`/`developer`-Rollen, sammelt deren Content und fügt ihn in den initialen System-Block ein. Alle System-Messages werden aus der Message-Schleife entfernt.

**Launcher:** Radio-Buttons «Default» / «Qwen CLI FIX» / «Gemma CLI FIX» im Optionsbereich (ersetzen die alte Qwen-Checkbox). Nur eine Auswahl gleichzeitig aktiv.

### GPT-OSS Jinja-Template Fix

**Problem:** `gpt-oss-20b` nutzt OpenAI-Harmony (Kanäle `analysis`/`commentary`/`final`) statt ChatML. Das Stock-Template rendert Tool-Schemas per Makro `render_typescript_type` ohne Typ-Prüfung – Claude-Schemas mit Sonderformen lassen Minja crashen: `500 While executing If at line 13 ... Function is not a bool value`. GUI (ohne Tools) läuft, Claude CLI (immer mit Built-in-Tools) nicht.

**Lösung:** `gptoss_fixed.jinja` = Stock-Template + `is mapping`-Guards an allen `.type`/`.items()`/`.oneOf`-Zugriffen. Nicht-Dict-Schemas fallen auf `any` zurück statt 500. Launcher-Radio «GPT-OSS FIX» setzt `--chat-template-file gptoss_fixed.jinja` und Reasoning auto-`none` (Harmony hat keine `<think>`-Tags, Denken kommt aus dem `analysis`-Kanal).

**Modell-Template-Matrix:**

| Modell | Template-Radio | Reasoning |
|---|---|---|
| Qwen | Qwen CLI FIX | deepseek |
| Gemma | Gemma CLI FIX | deepseek |
| `gpt-oss-20b` | GPT-OSS FIX | `none` (auto) |
| `Nemotron-3-Nano` | Default | deepseek (`<think>`-Tags) |
| Rest | Default | deepseek |

### Reasoning-Format (llama.cpp ≥ b10268)

**Problem:** Mit llama.cpp b10268+ leckten rohe Reasoning-/Tool-Tags (` response`, `<tool_call>`, `<|im_start|>`/`<|im_end|>`) in den sichtbaren Chat-Output von Claude Code. Ursache: das alte Flag `--reasoning on/off` steuert das Parsing in neueren Builds nicht mehr sauber, sodass Tool-Calls im Thinking-Block landeten und nicht als strukturierte `tool_calls` extrahiert wurden.

**Lösung:** Das Reasoning-Dropdown im Launcher setzt jetzt `--reasoning-format`:

| Wert | Verhalten |
|------|-----------|
| **deepseek** (Default) | Reasoning → `reasoning_content`, Tool-Calls → strukturierte `tool_calls`. Empfohlen für Qwen 3.5 + Gemma 4 mit Claude Code. |
| auto | llama.cpp-Erkennung (in b10295 faktisch = deepseek) |
| deepseek-legacy | Älteres Deepseek-Parsing |
| none | Kein Reasoning-Parsing (tags bleiben ggf. sichtbar) |

Verifiziert gegen `llama-b10295` mit `Qwen3.5-9B-Q4_K_M.gguf` und `gemma-4-E4B-it-Q5_K_M.gguf`: saubere `tool_calls`, leeres `content`, keine gelachten Tags.

### Sampling-Presets

Der Launcher bietet vier Presets plus einen Custom-Modus für Sampling-Parameter:

| Preset | `--temp` | `--repeat-penalty` | `--top-k` | `--top-p` |
|--------|----------|-------------------|-----------|-----------|
| **Default** | llama.cpp-Standard (0.80) | – | – | – |
| **Chat/Agent** | 0.70 | 1.10 | 40 | 0.90 |
| **Creative** | 0.90 | 1.15 | 60 | 0.95 |
| **Code/Precise** | 0.50 | 1.15 | 30 | 0.85 |
| **Custom** | frei wählbar | frei wählbar | frei wählbar | frei wählbar |

Bei «Custom» erscheinen vier Eingabefelder (Temp, Repeat, Top-K, Top-P) plus ein Textfeld **Extra Flags** für beliebige weitere llama.cpp-Parameter (`--mirostat`, `--seed`, `--presence-penalty`, …). Die Extra Flags werden via `shlex.split()` geparst.

Die Einstellungen haben keine Auswirkung auf die Chat-UI – dort gelten die Defaults des Servers.

### Version History

| Version | Datum | Änderungen |
|---|---|---|
| v1.1-rc1 | Juli 2026 | Konfiguration extern: `config.json`, Sicherheit: Prozess-Isolation `run_python`, SSRF-Schutz, Whitelist verschärft, 134 Zeilen Cleanup, `get_memory()`, `list_memory` ID-Fix. |
| v1.4-rc1 | 28.07.2026 | Self-Learning überarbeitet: Threshold 3→6, Whitelist für Kandidaten, human-in-the-loop (`approve_skill`/`reject_skill`), ~178 Zeilen toter Code entfernt (Async-Referenzblock, Deprecated-Wrappers). |
| v1.4-rc2 | 07.08.2026 | llama.cpp b10295-Reasoning-Fix: Dropdown `On/Off` → `--reasoning-format` (`auto`/`deepseek`/`deepseek-legacy`/`none`, Default `deepseek`). Behebt rohe ` response`/`<tool_call>`/`<|im_start|>`-Tags im Claude-Code-Output. Verifiziert mit `llama-b10295` + Qwen3.5/Gemma 4. |

---

> **bagueDev Community Launcher v1** – Lokal. Leicht. Fair.
>
> MIT License · Copyright © 2026 bagueDev
>
> GitHub: [github.com/bagueDev](https://github.com/bagueDev)
> YouTube: [youtube.com/@bagueDev](https://youtube.com/@bagueDev)
