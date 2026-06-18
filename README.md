![OS](https://img.shields.io/badge/os-linux-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![llama.cpp](https://img.shields.io/badge/llama.cpp-b9664-orange)
![License](https://img.shields.io/badge/license-MIT-green)
# bagueDev LLAMA.CPP WEB UI LAUNCHER

**bagueDev AI Toolkit** · **V.I.N.C.E.N.T. MCP Server**

> Virtual Information Network · Centralized Executive Neural Terminal

---

**EN** — Local AI toolkit built around `llama.cpp`. A GUI launcher so you never type 50 flags again, plus a 50+ tool MCP server that works standalone or embedded in VS Code / any MCP client.

**DE** — Lokales KI-Toolkit rund um `llama.cpp`. Ein GUI-Launcher, damit du nie wieder 50 Flags tippen musst, plus ein 50+ Tool MCP Server – eigenständig oder eingebettet in VS Code / jeden MCP-Client.

---
<img width="1280" height="720" alt="Bildschirmfoto vom 2026-06-18 17-38-20" src="https://github.com/user-attachments/assets/acd892bf-0f38-430e-a117-a8792e74dd92" />

<img width="1280" height="720" alt="Bildschirmfoto vom 2026-06-18 17-36-34" src="https://github.com/user-attachments/assets/14e23b98-d155-4d66-a648-b1185bcb0224" />


---

## Quick Start

```bash
git clone https://github.com/bagueDev/bagueDev-ai-toolkit
cd /deinProjekt
pip install -r requirements.txt
playwright install chromium    # Browser-Automation
crawl4ai-setup                  # Deep-Web-Scraping (optional, ~500MB)

# venv aktivieren
source venv/bin/activate

# MCP Server (standalone, port 8000)
python3 mcp_server.py

# Launcher UI (port 9999)
python3 llama-launcher.py
```

---

## Launcher

**EN** — A web UI that takes the pain out of `llama.cpp`. Pick a model from your folders, set parameters with your mouse (ctx, layers, threads, flash-attn, MTP, MCP proxy), and hit start. During inference you get live hardware telemetry: GPU temperature, junction temp, fan speed, PPT power draw, CPU temp, and token throughput.

Three ways to interact with your model:

| Interface | Purpose |
|---|---|
| **bagueDev Chat** | Quick tests, clean chat UI with live metrics |
| **Native llama.cpp WebUI** | Agentic tasks via MCP proxy, chat history |
| **Continue.dev (VS Code)** | Same local model inside your editor |

**DE** — Eine WebUI, die `llama.cpp` endlich bedienbar macht. Wähle ein Modell aus deinen Ordnern, setze Parameter mit der Maus (ctx, layers, threads, flash-attn, MTP, MCP proxy), und starte. Während der Inference siehst du Live-Hardware-Daten: GPU-Temperatur, Junction-Temp, Lüfterdrehzahl, PPT-Leistung, CPU-Temp und Token-Durchsatz.

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

Full list → [jarvis_tools.html](jarvis_tools.html)

**DE** — 50+ Tools bereitgestellt via [Model Context Protocol](https://modelcontextprotocol.io). Läuft eigenständig auf Port 8000, einsteckbar in jeden MCP-Client (VS Code, Continue.dev, Claude Desktop, …).

Vollständige Liste → [jarvis_tools.html](jarvis_tools.html)

---

## Technical Highlights

| | |
|---|---|
| **Single-File Launcher** | `llama-launcher.py` – stdlib only, zero dependencies |
| **Streamable HTTP** | h11 instead of httptools, no payload limits |
| **Self-Chunking** | Files >16KB are transparently split for writing |
| **Graceful Fallbacks** | ChromaDB optional, DDGS auto-fallback for Reddit/News |
| **Session Persistence** | Chrome keeps logins across restarts |
| **Jinja Templates** | `--jinja` only, no chat-template file juggling |

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
