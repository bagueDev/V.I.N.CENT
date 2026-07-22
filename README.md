![OS](https://img.shields.io/badge/os-linux-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![llama.cpp](https://img.shields.io/badge/llama.cpp-b9664-orange)
![License](https://img.shields.io/badge/license-MIT-green)
# bagueDev LLAMA.CPP WEB UI LAUNCHER

**bagueDev AI Toolkit** · **V.I.N.C.E.N.T. MCP Server**

> Virtual Information Network · Centralized Executive Neural Terminal

---

**EN** — Local AI toolkit built around `llama.cpp`. A GUI launcher so you never type 50 flags again, plus a 50+ tool MCP server that works standalone or embedded in Claude CLI, VS Code / any MCP client.

**DE** — Lokales KI-Toolkit rund um `llama.cpp`. Ein GUI-Launcher, damit du nie wieder 50 Flags tippen musst, plus ein 50+ Tool MCP Server – eigenständig oder eingebettet in Claude CLI , VS Code / jeden MCP-Client.

---
<img width="1280" height="720" alt="Bildschirmfoto vom 2026-06-18 17-38-20" src="https://github.com/user-attachments/assets/acd892bf-0f38-430e-a117-a8792e74dd92" />

<img width="1280" height="720" alt="Bildschirmfoto vom 2026-06-18 17-36-34" src="https://github.com/user-attachments/assets/14e23b98-d155-4d66-a648-b1185bcb0224" />


---

## Quick Start

```bash
git clone https://github.com/bagueDev/V.I.N.CENT
cd bagueDev/V.I.N.CENT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Optional:
playwright install chromium
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
cp config.example.json config.json
# → config.json öffnen und Pfade anpassen (llama-server, Modelle, Workspace)

# MCP Server (standalone, port 8000)
python3 VINCET_MCP.py

# Launcher UI (port 9999)
python3 bagueDEV_Launcher.py

# Hinweis zu venv: Der Launcher (bagueDEV_Launcher.py) braucht kein venv –
# er kommt mit der Python-Standardbibliothek aus.
# Das venv (requirements.txt, playwright install chromium) wird nur für den MCP Server (VINCENT_MCP.py) benötigt – genauer: für externe Tools wie Playwright, crawl4ai, ChromaDB.
# Wer diese Tools nicht nutzt, kann den MCP auch ohne venv starten
# (es fehlen dann halt die entsprechenden Funktionen). Das start.sh aktiviert das venv automatisch, wenn es existiert.
```

---
---

## Why not just Ollama / LM Studio?

**EN** — Fair question. Here is what you get here that you **cannot** get from Ollama or LM Studio:

| Capability | bagueDev Toolkit | Ollama | LM Studio |
|---|---|---|---|
| **MCP Server (50+ tools)** | ✅ built-in — file ops, browser, search, memory, diagram, sandbox | ❌ | ❌ |
| **Browser automation** | ✅ dedicated Playwright subprocess (click, type, tabs, screenshots) | ❌ | ❌ |
| **ChromaDB memory** | ✅ semantic long-term memory + skill learning | ❌ | ❌ |
| **Live hardware telemetry** | ✅ GPU temp, junction, fan, PPT power draw during inference | ❌ | ❌ |
| **Claude Code CLI** | ✅ works with local models (Qwen, Gemma via template fixes) | ❌ | ❌ |
| **MCP Proxy** | ✅ proxy tool calls to other MCP servers | ❌ | ❌ |
| **Web UI from any device** | ✅ browser-based, accessible on your LAN | ❌ (CLI only) | ✅ (desktop only) |
| **Telemetry** | **none** — zero, not even opt-in | ⚠️ on by default | ⚠️ limited |
| **Model download** | ❌ manual GGUF placement | ✅ `ollama pull` | ✅ built-in |
| **Model library** | ❌ no curated gallery | ✅ large | ✅ large |

Ollama is great if you want to **manage 20 models** and pull them from a library.
LM Studio is great if you want a **polished desktop GUI**.
This toolkit is for you if you want **MCP tools, browser automation, memory, and hardware telemetry** — all local, all free, no accounts.

**DE** — Gute Frage. Hier siehst du, was du **nur** hier bekommst:

| Funktion | bagueDev Toolkit | Ollama | LM Studio |
|---|---|---|---|
| **MCP Server (50+ Tools)** | ✅ integriert — Dateien, Browser, Suche, Memory, Diagramme, Sandbox | ❌ | ❌ |
| **Browser-Automation** | ✅ eigener Playwright-Prozess (klicken, tippen, Tabs, Screenshots) | ❌ | ❌ |
| **ChromaDB Memory** | ✅ semantisches Langzeitgedächtnis + Skill-Learning | ❌ | ❌ |
| **Live-Hardware-Telemetrie** | ✅ GPU-Temp, Junction, Lüfter, PPT während der Inference | ❌ | ❌ |
| **Claude Code CLI** | ✅ funktioniert mit lokalen Modellen (Qwen, Gemma via Template-Fixes) | ❌ | ❌ |
| **MCP Proxy** | ✅ Tool-Aufrufe an andere MCP-Server weiterleiten | ❌ | ❌ |
| **WebUI von jedem Gerät** | ✅ browserbasiert, via LAN erreichbar | ❌ (nur CLI) | ✅ (nur Desktop) |
| **Telemetrie** | **keine** — null, nicht mal opt-in | ⚠️ standardmässig an | ⚠️ eingeschränkt |
| **Modell-Download** | ❌ manuelle GGUF-Platzierung | ✅ `ollama pull` | ✅ integriert |
| **Modell-Bibliothek** | ❌ keine kuratierte Galerie | ✅ gross | ✅ gross |

Ollama ist gut, wenn du **20 Modelle verwalten** und aus einer Bibliothek ziehen willst.
LM Studio ist gut, wenn du eine **policerte Desktop-Oberfläche** willst.
Dieses Toolkit ist für dich, wenn du **MCP-Tools, Browser-Automation, Memory und Hardware-Telemetrie** brauchst — alles lokal, alles kostenlos, ohne Accounts.

---

## Launcher

**EN** — A web UI that takes the pain out of `llama.cpp`. Pick a model from your folders, set parameters with your mouse (ctx, layers, threads, flash-attn, MTP, MCP proxy, sampling presets), and hit start. During inference you get live hardware telemetry: GPU temperature, junction temp, fan speed, PPT power draw, CPU temp, and token throughput.

Three ways to interact with your model:

| Interface | Purpose |
|---|---|
| **bagueDev Chat** | Quick tests, clean chat UI with live metrics |
| **Native llama.cpp WebUI** | Agentic tasks via MCP proxy, chat history |
| **Continue.dev (VS Code)** | Same local model inside your editor |

**DE** — Eine WebUI, die `llama.cpp` endlich bedienbar macht. Wähle ein Modell aus deinen Ordnern, setze Parameter mit der Maus (ctx, layers, threads, flash-attn, MTP, MCP proxy, Sampling-Presets), und starte. Während der Inference siehst du Live-Hardware-Daten: GPU-Temperatur, Junction-Temp, Lüfterdrehzahl, PPT-Leistung, CPU-Temp und Token-Durchsatz.

---

## V.I.N.C.E.N.T. MCP Server

**EN** — 50+ tools exposed via the [Model Context Protocol](https://modelcontextprotocol.io). Runs standalone on port 8000, pluggable into any MCP client (VS Code, Continue.dev, Claude Desktop, …).

Categories:

| Category | Tools |
|---|---|
| File Operations | read, write, append, search, grep, patch, delete, … |
| Web Scraping | crawl4ai single-page & deep recursive crawl |
| Browser | persistent Chrome, click, type, screenshot, tabs, … |
| Trends | YouTube, GitHub, Hacker News, Reddit, Google Trends, IMDB, Weather, News |
| Search | DuckDuckGo (web + images), Tavily (web + news + deep) |
| Memory | ChromaDB long-term memory, semantic search |
| Learning | Skill learning by example, usage stats |
| Diagrams | Mermaid: architecture, workflows, flowcharts, sequence, mindmaps |
| Project Analysis | RAG indexing, codebase analysis |
| Utilities | Python sandbox, safe command execution (hyperframes, ffmpeg, …) |

Full list → [VINCET_Tools](https://github.com/bagueDev/V.I.N.CENT/blob/main/V.I.N.C.E.N.T.%20MCP%20Server.md)

**DE** — 50+ Tools bereitgestellt via [Model Context Protocol](https://modelcontextprotocol.io). Läuft eigenständig auf Port 8000, einsteckbar in jeden MCP-Client (VS Code, Continue.dev, Claude Desktop, …).

Vollständige Liste → [V.I.N.CENT_tools.html](V.I.N.C.E.N.T. MCP Server.md).

---

## Technical Highlights

| | |
|---|---|
| **Single-File Launcher** | `llama-launcher.py` – stdlib only, zero dependencies |
| **Streamable HTTP** | h11 instead of httptools, no payload limits |
| **Self-Chunking** | Files >16KB are transparently split for writing |
| **Graceful Fallbacks** | ChromaDB optional, DDGS auto-fallback for Reddit/News |
| **Browser Subprocess** | `browser_subprocess.py` – dedicated Playwright process, crash-safe via stdin/stdout |
| **Session Persistence** | Chrome keeps logins across restarts |
| **Jinja Templates** | `--jinja` only, no chat-template file juggling |
| **Qwen/Gemma CLI Fix** | `qwen_fixed.jinja` + `gemma_fixed.jinja` für Claude Code CLI-Kompatibilität |
| **Sampling-Presets** | Chat/Creative/Code-Presets + Custom-Modus mit Extra Flags |
| **Execute-Whitelist** | `npx`/`ffmpeg`/`node`/`npm`/`pip`/`python3` für kontrollierte Command-Ausführung |
| **Config extern** | `config.json` → Pfade, Ports, erlaubte Verzeichnisse (alle Skripte lesen zentral) |
| **Portable Pfade** | `config.example.json` mit Platzhaltern → kopieren, anpassen, starten |

---

## Privacy & Data Protection

**EN** — Everything runs **100% locally** on your machine. No data ever leaves your computer. No API calls to OpenAI, Anthropic, or any cloud service. No telemetry, no tracking, no user accounts. The only optional external call is Tavily search (if you configure an API key) — everything else works fully offline.

You own your models, your data, and your privacy. **Zero API costs. Zero subscriptions.**

**DE** — Alles läuft **zu 100% lokal** auf deinem Rechner. Keine Daten verlassen jemals deinen Computer. Keine API-Calls an OpenAI, Anthropic oder andere Cloud-Dienste. Kein Telemetrie, kein Tracking, keine Benutzerkonten. Der einzige optionale externe Aufruf ist die Tavily-Suche (wenn du einen API-Key konfigurierst) — alles andere funktioniert komplett offline.

Du behältst die Kontrolle über deine Modelle, deine Daten und deine Privatsphäre. **Keine API-Kosten. Keine Abos.**

---

## Requirements

- Python 3.10+
- [llama.cpp](https://github.com/ggerganov/llama.cpp) build (`llama-server` binary)
- Vulkan-capable GPU recommended (CPU works)
- Optional: Tavily API key for enhanced search

Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
crawl4ai-setup   # optional, for deep web scraping
```

> `sentence-transformers` (~400 MB) wird automatisch installiert und lädt beim ersten Skill-Aufruf ein Embedding-Modell herunter.

---

## License

MIT License — Copyright (c) 2026 bagueDev

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Links

- GitHub: [github.com/bagueDev](https://github.com/bagueDev)
- YouTube: [youtube.com/@bagueDev](https://youtube.com/@bagueDev)
