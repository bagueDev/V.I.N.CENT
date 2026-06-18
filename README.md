# bagueDev AI Toolkit

**Vega56 Launcher** · **V.I.N.C.E.N.T. MCP Server**

> Virtual Information Network · Centralized Executive Neural Terminal

---

**EN** — Local AI toolkit built around `llama.cpp`. A GUI launcher so you never type 50 flags again, plus a 50+ tool MCP server that works standalone or embedded in VS Code / any MCP client.

**DE** — Lokales KI-Toolkit rund um `llama.cpp`. Ein GUI-Launcher, damit du nie wieder 50 Flags tippen musst, plus ein 50+ Tool MCP Server – eigenständig oder eingebettet in VS Code / jeden MCP-Client.

---

![Vega56 Launcher](screenshots/launcher.png?raw=true)
![Vega56 Chat](screenshots/chat.png?raw=true)

---

## Quick Start

```bash
git clone https://github.com/bagueDev/bagueDev-ai-toolkit
cd bagueDev-ai-toolkit
pip install -r requirements.txt
playwright install chromium

# MCP Server (standalone, port 8000)
python3 mcp_server.py

# Launcher UI (port 9999)
python3 llama-launcher.py
```

---

## Vega56 Launcher

**EN** — A web UI that takes the pain out of `llama.cpp`. Pick a model from your folders, set parameters with your mouse (ctx, layers, threads, flash-attn, MTP, MCP proxy), and hit start. During inference you get live hardware telemetry: GPU temperature, junction temp, fan speed, PPT power draw, CPU temp, and token throughput.

Three ways to interact with your model:

| Interface | Purpose |
|---|---|
| **Vega56 Chat** | Quick tests, clean chat UI with live metrics |
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
