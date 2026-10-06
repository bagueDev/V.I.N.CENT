# bagueDev Community Launcher

**bagueDev Community Launcher** · **V.I.N.C.E.N.T. MCP Server**

> Virtual Information Network · Centralized Executive Neural Terminal

---

**EN** — Local AI toolkit built around `llama.cpp`. A GUI launcher so you never type 50 flags again, plus a 50+ tool MCP server that works standalone or embedded in VS Code / any MCP client.

**DE** — Lokales KI-Toolkit rund um `llama.cpp`. Ein GUI-Launcher, damit du nie wieder 50 Flags tippen musst, plus ein 50+ Tool MCP Server – eigenständig oder eingebettet in VS Code / jeden MCP-Client.

---

![bagueDev Community Launcher](screenshots/launcher.png?raw=true)
![bagueDev Chat](screenshots/chat.png?raw=true)

---

## Quick Start

```bash
git clone https://github.com/bagueDev/community-launcher
cd community-launcher
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp config.example.json config.json
# → config.json öffnen und Pfade anpassen (llama-server, Modelle, Workspace)

# MCP Server (standalone, port 8000)
python3 VINCENT_MCP.py
 
# Launcher UI (port 9999)
python3 bagueDEV_Launcher.py
```

---

## Why not just Ollama / LM Studio?

**EN** — Fair question. Here is what you get here that you **cannot** get from Ollama or LM Studio:

| Capability | Community Launcher | Ollama | LM Studio |
|---|---|---|---|
| **MCP Server (50+ tools)** | ✅ built-in — file ops, browser, search, memory, diagram, sandbox | ❌ (3rd-party bridges only) | ⚠️ host only (3rd-party servers), no built-in tool server |
| **Browser automation** | ✅ dedicated Playwright subprocess (click, type, tabs, screenshots) | ❌ | ⚠️ via MCP server (e.g. playwright-mcp), no built-in browser |
| **ChromaDB memory** | ✅ semantic long-term memory + skill suggestions (human-in-the-loop) | ❌ | ❌ |
| **Live hardware telemetry** | ✅ GPU temp, junction, fan, PPT power draw during inference | ❌ | ⚠️ load/VRAM/tok-s only, no temp/fan/power |
| **Claude Code CLI** | ✅ works with local models (Qwen, Gemma via template fixes) | ❌ | ❌ |
| **MCP Proxy** | ✅ proxy tool calls to other MCP servers | ❌ | ❌ |
| **Web UI from any device** | ✅ browser-based, accessible on your LAN | ❌ (desktop app + CLI, no browser/LAN UI) | ⚠️ desktop only, no browser/LAN access |
| **Telemetry** | **none** — zero, not even opt-in | ⚠️ no usage telemetry, but update/catalog calls (partly non-disableable) | ⚠️ no tracking, but model search via own proxy + update checks |
| **Model download** | ❌ manual GGUF placement | ✅ `ollama pull` | ✅ built-in |
| **Model library** | ❌ no curated gallery | ✅ large | ✅ large |

Ollama is great if you want to **manage 20 models** and pull them from a library.
LM Studio is great if you want a **polished desktop GUI**.
This toolkit is for you if you want **MCP tools, browser automation, memory, and hardware telemetry** — all local, all free, no accounts.

*LM Studio acts as MCP host since v0.3.17 (any 3rd-party server incl. Playwright usable, no built-in tool server). Ollama: no usage telemetry, but hourly update checks + model catalog calls, partly non-disableable.*

**DE** — Gute Frage. Hier siehst du, was du **nur** hier bekommst:

| Funktion | Community Launcher | Ollama | LM Studio |
|---|---|---|---|
| **MCP Server (50+ Tools)** | ✅ integriert — Dateien, Browser, Suche, Memory, Diagramme, Sandbox | ❌ (nur via Dritt-Bridges) | ⚠️ nur Host (fremde Server), kein eigener Tool-Server |
| **Browser-Automation** | ✅ eigener Playwright-Prozess (klicken, tippen, Tabs, Screenshots) | ❌ | ⚠️ via MCP-Server (z.B. playwright-mcp), kein eingebauter Browser |
| **ChromaDB Memory** | ✅ semantisches Langzeitgedächtnis + Skill-Vorschläge (human-in-the-loop) | ❌ | ❌ |
| **Live-Hardware-Telemetrie** | ✅ GPU-Temp, Junction, Lüfter, PPT während der Inference | ❌ | ⚠️ nur Last/VRAM/tok-s, keine Temp/Lüfter/Power |
| **Claude Code CLI** | ✅ funktioniert mit lokalen Modellen (Qwen, Gemma via Template-Fixes) | ❌ | ❌ |
| **MCP Proxy** | ✅ Tool-Aufrufe an andere MCP-Server weiterleiten | ❌ | ❌ |
| **WebUI von jedem Gerät** | ✅ browserbasiert, via LAN erreichbar | ❌ (Desktop-App + CLI, kein Browser-/LAN-UI) | ⚠️ nur Desktop, kein Browser-/LAN-Zugriff |
| **Telemetrie** | **keine** — null, nicht mal opt-in | ⚠️ keine Nutzungs-Telemetrie, aber Update-/Katalog-Calls (teils nicht abschaltbar) | ⚠️ kein Tracking, aber Modell-Suche via eigenem Proxy + Update-Checks |
| **Modell-Download** | ❌ manuelle GGUF-Platzierung | ✅ `ollama pull` | ✅ integriert |
| **Modell-Bibliothek** | ❌ keine kuratierte Galerie | ✅ gross | ✅ gross |

Ollama ist gut, wenn du **20 Modelle verwalten** und aus einer Bibliothek ziehen willst.
LM Studio ist gut, wenn du eine **polierte Desktop-Oberfläche** willst.
Dieses Toolkit ist für dich, wenn du **MCP-Tools, Browser-Automation, Memory und Hardware-Telemetrie** brauchst — alles lokal, alles kostenlos, ohne Accounts.

*LM Studio ist seit v0.3.17 MCP-Host (fremde Server inkl. Playwright nutzbar, kein eigener Tool-Server). Ollama: keine Nutzungs-Telemetrie, aber stündliche Update-Checks + Modell-Katalog-Calls, teils nicht abschaltbar.*

---

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
| Browser | dedicated Playwright subprocess (`browser_subprocess.py`) – click, type, screenshot, tabs, … |
| Trends | YouTube, GitHub, Hacker News, Reddit, Google Trends, IMDB, Weather, News |
| Search | DuckDuckGo (web + images), Tavily (web + news + deep) |
| Memory | ChromaDB long-term memory, semantic search |
| Learning | Skill suggestions with approve/reject workflow, usage stats |
| Diagrams | Mermaid: architecture, workflows, flowcharts, sequence, mindmaps |
| Project Analysis | RAG indexing, codebase analysis |
| Utilities | Python sandbox, safe command execution (hyperframes, ffmpeg, …) |

Full list → [V.I.N.C.E.N.T. MCP Server.md](<V.I.N.C.E.N.T. MCP Server.md>)

**DE** — 50+ Tools bereitgestellt via [Model Context Protocol](https://modelcontextprotocol.io). Läuft eigenständig auf Port 8000, einsteckbar in jeden MCP-Client (VS Code, Continue.dev, Claude Desktop, …).

Vollständige Liste → [V.I.N.C.E.N.T. MCP Server.md](<V.I.N.C.E.N.T. MCP Server.md>)

---

## Technical Highlights

| | |
|---|---|
| **Single-File Launcher** | `bagueDEV_Launcher.py` – stdlib only, zero dependencies |
| **Streamable HTTP** | h11 instead of httptools, no payload limits |
| **Self-Chunking** | Files >16KB are transparently split for writing |
| **Graceful Fallbacks** | ChromaDB optional, DDGS auto-fallback for Reddit/News |
| **Browser Subprocess** | `browser_subprocess.py` – dedicated Playwright process, crash-safe via stdin/stdout |
| **Session Persistence** | Chrome keeps logins across restarts |
| **Jinja Templates** | `--jinja` only, no chat-template file juggling |
| **Qwen/Gemma CLI Fix** | `qwen_fixed.jinja` + `gemma_fixed.jinja` für Claude Code CLI-Kompatibilität |
| **Sampling-Presets** | Chat/Creative/Code-Presets + Custom-Modus mit Extra Flags |
| **Execute-Whitelist** | `npx hyperframes`/`ffmpeg`/`ls`/`cat`/`mkdir` – kein freier Shell-Zugriff |
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
- [llama.cpp](https://github.com/ggerganov/llama.cpp) build (`llama-server` binary) — **b10268+ empfohlen** (nutzt `--reasoning-format`; ältere Builds lecken rohe Reasoning/Tool-Tags in Claude Code)
- Vulkan-capable GPU recommended (CPU works)
- Optional: Tavily API key for enhanced search

Install dependencies:
```bash
# torch CPU-only installieren (spart ~4GB CUDA-Pakete)
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
playwright install chromium
crawl4ai-setup   # optional, for deep web scraping
```

> `sentence-transformers` braucht `torch`. Ohne `--extra-index-url` werden ~4GB CUDA-Pakete mitinstalliert (unnötig für AMD/CPU). CPU-only torch (~200MB) reicht für Embeddings in ChromaDB.

---


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
