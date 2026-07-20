#!/usr/bin/env python3
"""
V.I.N.C.E.N.T. MCP Server - Model Context Protocol Server

Dieser Server exponiert V.I.N.C.E.N.T.-Tools für andere MCP-Clients (z.B. llama.cpp WebUI).
Entwickelt bei bagueDev
  GitHub: https://github.com/bagueDev
  YouTube: https://youtube.com/@bagueDev

Verwendung:
    python VINCENT_MCP.py
    
Der Server läuft standardmäßig auf http://127.0.0.1:8000/mcp
"""

import sys
import os
import shutil
import warnings
# Suppress the RequestsDependencyWarning to prevent UI confusion
try:
    from requests.exceptions import RequestsDependencyWarning
    warnings.filterwarnings("ignore", category=RequestsDependencyWarning)
except ImportError:
    pass
from typing import List, Optional

# Pfad zum Jarvis-Verzeichnis hinzufügen
JARVIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, JARVIS_DIR)
CHROMA_DIR = os.path.join(JARVIS_DIR, ".chroma")

from mcp.server.fastmcp import FastMCP
import json
import time
import requests
import subprocess

# Diagram generation uses llama-server on 127.0.0.1:8080 (no Ollama needed)

# MCP Server erstellen
mcp = FastMCP("V.I.N.C.E.N.T.")

# ── Konfiguration aus config.json ──────────────────────────
CONFIG_PATH = os.path.join(JARVIS_DIR, "config.json")

def _load_config() -> dict:
    """Liest config.json. Falls nicht vorhanden, leeres Dict."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except:
        return {}

def _get_allowed_paths() -> list:
    """Gibt die Liste erlaubter Pfade aus config.json + JARVIS_DIR zurück."""
    paths = [JARVIS_DIR]
    cfg = _load_config()
    for key in ("allowed_base", "allowed_paths"):
        val = cfg.get(key)
        if isinstance(val, str):
            val = [val]
        if isinstance(val, list):
            for p in val:
                p = os.path.abspath(os.path.expanduser(p))
                if p not in paths:
                    paths.append(p)
    return paths

def get_workspace_dir() -> str:
    """Lädt den Workspace-Pfad aus config.json (allowed_base) oder JARVIS_DIR."""
    cfg = _load_config()
    allowed = cfg.get("allowed_base")
    if allowed:
        return os.path.abspath(os.path.expanduser(allowed))
    return JARVIS_DIR

def resolve_path(path: str) -> str:
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.join(get_workspace_dir(), path)

def is_path_allowed(path: str) -> bool:
    if not path:
        return True
    abs_path = os.path.abspath(os.path.realpath(path))
    for allowed in _get_allowed_paths():
        abs_allowed = os.path.abspath(os.path.realpath(allowed))
        if os.path.commonpath([abs_path, abs_allowed]) == abs_allowed:
            return True
    return False

# llama.cpp JSON-Parser sicherer Grenzwert
CHUNK_SIZE = 4000

def _chunked_write(path: str, content: str, mode: str = 'w'):
    """Schreibt/appendet Content in Chunks, um llama.cpp JSON-Parser-Limit zu umgehen."""
    if len(content) <= CHUNK_SIZE:
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
        return
    first = content[:CHUNK_SIZE]
    rest = content[CHUNK_SIZE:]
    with open(path, mode, encoding='utf-8') as f:
        f.write(first)
    with open(path, 'a', encoding='utf-8') as f:
        for i in range(0, len(rest), CHUNK_SIZE):
            f.write(rest[i:i+CHUNK_SIZE])

# ========== TOOL DEFINITIONS ==========

@mcp.tool()
def read_file(filepath: str = None, path: str = None, max_chars: int = 10000) -> str:
    """Liest den Inhalt einer Datei.
    
    Args:
        filepath: Pfad zur Datei
        path: Alternativer Parametername für Pfad
        max_chars: Maximale Anzahl Zeichen (Standard: 10000)
    """
    actual_path = resolve_path(filepath or path)
    if not actual_path:
        return "❌ Fehler: 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        if not os.path.exists(actual_path):
            return f"❌ Datei nicht gefunden: {actual_path}"
        
        with open(actual_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if len(content) > max_chars:
            return f"[Datei gekürzt auf {max_chars} Zeichen]\n\n{content[:max_chars]}..."
        
        return content
    except Exception as e:
        return f"❌ Fehler beim Lesen: {str(e)}"

@mcp.tool()
def write_file(filepath: str = None, path: str = None, content: str = "", base64_content: str = None) -> str:
    """Schreibt Inhalt in eine Datei oder erstellt eine neue.
    Content wird bei Bedarf automatisch in Chunks geschrieben.
    
    Args:
        filepath: Pfad zur Datei
        path: Alternativer Parametername für Pfad
        content: Inhalt (max 16000 Zeichen). Bei >5000 Zeichen aufteilen: (1) write_file mit Platzhaltern wie "def func1(): pass" / "<!-- section1 -->", (2) append_to_file für echten Inhalt pro Abschnitt
        base64_content: Base64-kodierter Inhalt
    """
    actual_path = resolve_path(filepath or path)
    if not actual_path:
        return "❌ Fehler: 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        if base64_content:
            import base64
            try:
                content = base64.b64decode(base64_content).decode('utf-8')
            except Exception as e:
                return f"❌ Fehler beim Dekodieren von base64_content: {str(e)}"
        
        if not content:
            return "❌ Warnung: Inhalt ist leer. Nichts zu schreiben."
        
        if len(content) > 16000:
            return f"❌ Content zu groß ({len(content)} Zeichen). Max 16000 Zeichen.\nAufteilen:\n1. write_file(filepath=\"...\", content=\"# section1\\n# section2\\n...\")\n2. append_to_file(filepath=\"...\", content=\"# section1\\n...\")\n3. append_to_file(filepath=\"...\", content=\"# section2\\n...\")"
        
        os.makedirs(os.path.dirname(actual_path) or '.', exist_ok=True)
        _chunked_write(actual_path, content, 'w')
        
        return f"✅ Datei geschrieben: {actual_path} ({len(content)} Zeichen)"
    except Exception as e:
        return f"❌ Fehler beim Schreiben: {str(e)}"

@mcp.tool()
def append_to_file(filepath: str = None, path: str = None, content: str = "", base64_content: str = None) -> str:
    """Fügt Content am Ende einer Datei an. Content wird bei Bedarf automatisch in Chunks geschrieben.
    
    Args:
        filepath: Pfad zur Datei
        path: Alternativer Parametername für Pfad
        content: Inhalt (max 16000 Zeichen). Bei >5000 Zeichen aufteilen: (1) write_file mit Platzhaltern, (2) append_to_file für echten Inhalt pro Abschnitt
        base64_content: Base64-kodierter Inhalt
    """
    actual_path = resolve_path(filepath or path)
    if not actual_path:
        return "❌ Fehler: 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    if not os.path.exists(actual_path):
        return f"❌ Datei existiert nicht: {actual_path}. Nutze write_file um sie zu erstellen."
    
    try:
        if base64_content:
            import base64
            try:
                content = base64.b64decode(base64_content).decode('utf-8')
            except Exception as e:
                return f"❌ Fehler beim Dekodieren von base64_content: {str(e)}"
        
        if not content:
            return "❌ Warnung: Inhalt ist leer. Nichts anzuhängen."
        
        if len(content) > 16000:
            return f"❌ Content zu groß ({len(content)} Zeichen). Max 16000 Zeichen.\nAufteilen:\n1. write_file(filepath=\"...\", content=\"# section1\\n# section2\\n...\")\n2. append_to_file(filepath=\"...\", content=\"# section1\\n...\")\n3. append_to_file(filepath=\"...\", content=\"# section2\\n...\")"
        
        _chunked_write(actual_path, content, 'a')
        return f"✅ Content angehängt an: {actual_path} ({len(content)} Zeichen)"
    except Exception as e:
        return f"❌ Fehler beim Anhängen: {str(e)}"

@mcp.tool()
def list_directory(filepath: str = None, path: str = ".", dir_only: bool = False) -> str:
    """Listet den Inhalt eines Verzeichnisses auf."""
    actual_path = resolve_path(filepath or path)
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        if not os.path.exists(actual_path):
            return f"❌ Verzeichnis nicht gefunden: {actual_path}"
        
        if not os.path.isdir(actual_path):
            return f"❌ Ist kein Verzeichnis: {actual_path}"
        
        items = []
        for item in sorted(os.listdir(actual_path)):
            full_path = os.path.join(actual_path, item)
            if os.path.isdir(full_path):
                items.append(f"📁 {item}/")
            elif not dir_only:
                size = os.path.getsize(full_path)
                items.append(f"📄 {item} ({size} bytes)")
        
        return "\n".join(items) if items else "Leer"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def search_files(filepath: str = None, path: str = None, pattern: str = "", file_type: str = "*") -> str:
    """Durchsucht Dateien nach einem Pattern (grep-like)."""
    actual_path = resolve_path(filepath or path)
    if not actual_path:
        return "❌ Fehler: 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        import glob
        
        results = []
        search_pattern = os.path.join(actual_path, "**", file_type)
        
        for file_path in glob.glob(search_pattern, recursive=True):
            if not os.path.isfile(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if pattern.lower() in line.lower():
                            results.append(f"{file_path}:{i}: {line.strip()[:100]}")
            except:
                continue
        
        if not results:
            return f"Keine Treffer für '{pattern}' gefunden."
        
        return "\n".join(results[:50])
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def grep(pattern: str = "", filepath: str = None, path: str = ".", file_glob: str = "*.py") -> str:
    """Durchsucht Dateien nach einem Pattern mit Regex-Unterstützung."""
    actual_path = resolve_path(filepath or path)
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        import glob
        import re
        
        matches = []
        search_pattern = os.path.join(actual_path, "**", file_glob)
        
        for file_path in glob.glob(search_pattern, recursive=True):
            if not os.path.isfile(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            matches.append(f"{file_path}:{line_num}: {line.rstrip()}")
            except:
                continue
        
        if not matches:
            return f"❌ Keine Treffer für '{pattern}' in {actual_path}/{file_glob}"
        
        result = "\n".join(matches[:100])
        if len(matches) > 100:
            result += f"\n... und {len(matches) - 100} weitere Treffer"
        return f"🔍 {len(matches)} Treffer für '{pattern}':\n{result}"
    except Exception as e:
        return f"❌ Fehler bei grep: {str(e)}"

@mcp.tool()
def get_file_info(filepath: str = None, path: str = None) -> str:
    """Gibt Informationen über eine Datei zurück."""
    actual_path = resolve_path(filepath or path)
    if not actual_path:
        return "❌ Fehler: 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        if not os.path.exists(actual_path):
            return f"❌ Nicht gefunden: {actual_path}"
        
        stat = os.stat(actual_path)
        
        info = {
            "Pfad": actual_path,
            "Typ": "Verzeichnis" if os.path.isdir(actual_path) else "Datei",
            "Größe": f"{stat.st_size} bytes",
            "Erstellt": str(stat.st_ctime),
            "Geändert": str(stat.st_mtime),
            "Zugegriffen": str(stat.st_atime)
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def create_directory(filepath: str = None, path: str = None) -> str:
    """Erstellt ein neues Verzeichnis."""
    actual_path = resolve_path(filepath or path)
    if not actual_path:
        return "❌ Fehler: 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        os.makedirs(actual_path, exist_ok=True)
        return f"✅ Verzeichnis erstellt: {actual_path}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def delete_file(filepath: str = None, path: str = None) -> str:
    """Löscht eine Datei oder ein leeres Verzeichnis."""
    actual_path = resolve_path(filepath or path)
    if not actual_path:
        return "❌ Fehler: 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    
    try:
        if not os.path.exists(actual_path):
            return f"❌ Nicht gefunden: {actual_path}"
        
        if os.path.isdir(actual_path):
            os.rmdir(actual_path)
        else:
            os.remove(actual_path)
        
        return f"✅ Gelöscht: {actual_path}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"


@mcp.tool()
def web_scrape(url: str) -> str:
    """Scrapes a website using crawl4ai and returns clean Markdown.
    
    Args:
        url: URL of the webpage to scrape
    """
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        from concurrent.futures import ThreadPoolExecutor
        
        async def scrape():
            browser_cfg = BrowserConfig()
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(url)
                if result.success and result.markdown:
                    return result.markdown
                elif result.success and result.html:
                    return f"[HTML Content - no markdown available]\n\n{result.html[:5000]}"
                else:
                    return f"❌ Scrape failed: {getattr(result, 'error_message', 'Unknown error')}"
        
        with ThreadPoolExecutor() as executor:
            loop = asyncio.new_event_loop()
            return executor.submit(loop.run_until_complete, scrape()).result()
    except ImportError:
        return "❌ crawl4ai nicht installiert. Bitte: pip install crawl4ai"
    except Exception as e:
        _record_tool_call("web_scrape", {"url": url}, False, str(e))
        return f"❌ Web Scrape Fehler: {str(e)}"

@mcp.tool()
def deep_scrape(url: str, max_pages: int = 10, max_depth: int = 2) -> str:
    """Recursively crawls a website up to N pages and returns all content.
    
    Args:
        url: Starting URL for deep crawl
        max_pages: Maximum pages to crawl (default 10, max 50)
        max_depth: Maximum link depth (default 2, max 5)
    """
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, BFSDeepCrawlStrategy
        from concurrent.futures import ThreadPoolExecutor
        
        max_pages = min(max_pages, 50)
        max_depth = min(max_depth, 5)
        
        async def scrape():
            browser_cfg = BrowserConfig()
            deep_crawl_strategy = BFSDeepCrawlStrategy(
                max_depth=max_depth,
                max_pages=max_pages,
                include_external=False
            )
            config = CrawlerRunConfig(deep_crawl_strategy=deep_crawl_strategy)
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                results = await crawler.arun(url, config=config)
                
                if not results or len(results) == 0:
                    return "❌ Keine Seiten gefunden"
                
                output = [f"# Deep Scrape: {url}\n"]
                output.append(f"Gecrawlte Seiten: {len(results)}\n")
                output.append("---\n")
                
                for i, result in enumerate(results, 1):
                    if result.success and result.markdown:
                        title = result.metadata.get('title', 'Ohne Titel') if result.metadata else 'Ohne Titel'
                        output.append(f"## {i}. {title}\n")
                        output.append(f"URL: {result.url}\n\n")
                        output.append(result.markdown[:3000])
                        output.append("\n\n---\n\n")
                    else:
                        output.append(f"## {i}. {result.url}\n❌ Fehlgeschlagen\n---\n\n")
                
                result_str = "\n".join(output)
                _record_tool_call("deep_scrape", {"url": url, "max_pages": max_pages, "max_depth": max_depth}, True, result_str[:100])
                return result_str
        
        with ThreadPoolExecutor() as executor:
            loop = asyncio.new_event_loop()
            return executor.submit(loop.run_until_complete, scrape()).result()
    except ImportError:
        return "❌ crawl4ai nicht installiert. Bitte: pip install crawl4ai"
    except Exception as e:
        _record_tool_call("deep_scrape", {"url": url, "max_pages": max_pages, "max_depth": max_depth}, False, str(e))
        return f"❌ Deep Scrape Fehler: {str(e)}"

# ===== BROWSER STATE =====
_browser_page = None
_browser_instance = None
_browser_playwright = None

from subprocess import Popen, PIPE
import threading

_browser_subprocess = None
_browser_lock = threading.Lock()

def _ensure_url(url: str) -> str:
    """Ensure URL has proper scheme."""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def _get_browser_subprocess():
    """Get or start browser subprocess."""
    global _browser_subprocess
    if _browser_subprocess is None or _browser_subprocess.poll() is not None:
        _browser_subprocess = Popen(
            ['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'browser_subprocess.py')],
            stdin=PIPE, stdout=PIPE, stderr=PIPE,
            text=True, bufsize=1
        )
    return _browser_subprocess

def _send_browser_cmd(action: str, **kwargs) -> dict:
    """Send command to browser subprocess with error handling."""
    import json
    try:
        proc = _get_browser_subprocess()
        with _browser_lock:
            cmd = json.dumps({"action": action, "args": kwargs}) + "\n"
            proc.stdin.write(cmd)
            proc.stdin.flush()
            response_line = proc.stdout.readline()
            return json.loads(response_line)
    except Exception as e:
        return {"status": "error", "message": f"Communication error: {str(e)[:50]}"}

def _sync_browser_open(url: str) -> str:
    """Open URL via subprocess browser."""
    url = _ensure_url(url)
    result = _send_browser_cmd("open", url=url)
    if result.get("status") == "ok":
        title = result.get("title", "")
        content = result.get("content", "")
        return f"✅ {title}\n\n{content[:3000]}"
    return f"❌ Fehler: {result.get('message', 'Unbekannt')}"

def _search_amazon_products(query: str, limit: int = 10) -> str:
    """Suche auf Amazon und zeige Produkte - mit Recursion-Schutz."""
    try:
        # First ensure we have a page open - with timeout protection
        try:
            open_result = _send_browser_cmd("open", url="https://www.amazon.de")
        except Exception as open_err:
            return f"❌ Verbindungsfehler: {str(open_err)[:80]}"
        
        if open_result.get("status") != "ok":
            return f"❌ Öffnen fehlgeschlagen: {open_result.get('message', 'unbekannt')[:50]}"
        
        # Then search - with separate try for timeout
        try:
            result = _send_browser_cmd("search_products", query=query, limit=limit)
        except Exception as search_err:
            return f"❌ Suchfehler: {str(search_err)[:80]}"
        
        if result.get("status") != "ok":
            return f"❌ {result.get('message', 'Suche fehlgeschlagen')[:80]}"
        
        products = result.get("products", [])
        
        if not products:
            return f"❌ Keine Produkte gefunden für: {query}"
        
        output = [f"🛒 **Amazon: {query}** ({len(products)} Ergebnisse)\n"]
        for i, p in enumerate(products[:limit], 1):
            name = p.get('name', 'Unbekannt')
            price = p.get('price', '?')
            url = p.get('url', '')
            
            output.append(f"\n{i}. **{name}**")
            if price and price != '?':
                output.append(f"   💰 {price}")
            if url:
                output.append(f"   🔗 {url}")
        
        return "\n".join(output)
    except RecursionError:
        return "❌ Systemfehler: Bitte erneut versuchen"
    except Exception as e:
        return f"❌ Fehler: {str(e)[:80]}"

def browser_search_products(query: str, limit: int = 10) -> str:
    """Sucht auf Amazon und zeigt Produkte - wrapper mit Fehlerhandling."""
    try:
        result = _search_amazon_products(query, limit)
        _record_tool_call("browser_search_products", {"query": query, "limit": limit}, True, result[:100])
        return result
    except RecursionError:
        return "❌ Bitte erneut versuchen"
    except Exception as e:
        _record_tool_call("browser_search_products", {"query": query, "limit": limit}, False, str(e))
        return f"❌ Fehler: {str(e)[:80]}"

def _deprecated_snapshot() -> str:
    """Get current page content."""
    result = _send_browser_cmd("snapshot")
    if result.get("status") == "ok":
        return f"# Snapshot\n\n{result.get('content', '')[:10000]}"
    return f"❌ {result.get('message', 'Fehler')}"

def _deprecated_structured() -> str:
    """Get structured elements."""
    result = _send_browser_cmd("structured")
    if result.get("status") == "ok":
        elements = result.get("elements", [])
        if elements:
            return "# Interaktive Elemente:\n\n" + "\n".join(elements)
        return "❌ Keine Elemente"
    return f"❌ {result.get('message', 'Fehler')}"

def _deprecated_click() -> str:
    """Click selector."""
    result = _send_browser_cmd("click", text=selector)
    if result.get("status") == "ok":
        return f"✅ {result.get('message', 'Geklickt')}"
    return f"❌ {result.get('message', 'Fehler')}"

def _deprecated_auto_click() -> str:
    """Auto-click with fallback."""
    result = _send_browser_cmd("click", text=text)
    if result.get("status") == "ok":
        return f"✅ {result.get('message', 'Geklickt')}"
    return f"❌ {result.get('message', 'Fehler')}"

def _deprecated_type() -> str:
    """Type into selector."""
    result = _send_browser_cmd("type", selector=selector, text=text)
    if result.get("status") == "ok":
        return f"✅ {result.get('message', 'Getippt')}"
    return f"❌ {result.get('message', 'Fehler')}"

def _deprecated_screenshot() -> str:
    """Take screenshot."""
    result = _send_browser_cmd("screenshot", path=path)
    if result.get("status") == "ok":
        return f"✅ Gespeichert: {path}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_navigate(url: str, action: str = "goto") -> str:
    """Navigate to URL."""
    url = _ensure_url(url)
    result = _send_browser_cmd("navigate", url=url, action=action)
    if result.get("status") == "ok":
        return f"✅ {url}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_close() -> None:
    """Close browser subprocess."""
    global _browser_subprocess
    if _browser_subprocess:
        try:
            _browser_subprocess.stdin.write('{"action": "quit"}\n')
            _browser_subprocess.stdin.flush()
            _browser_subprocess.terminate()
        except:
            pass
    _browser_subprocess = None

def _deprecated_snapshot() -> str:
    """Get current page content."""
    global _browser_page
    if _browser_page is None:
        return "❌ Bitte zuerst browser_open aufrufen"
    _browser_page.wait_for_timeout(1000)
    return f"# Snapshot\n\n{_browser_page.content()[:10000]}"

def _deprecated_structured() -> str:
    """Get structured elements."""
    global _browser_page
    if _browser_page is None:
        if url:
            return _sync_browser_open(url)
        return "❌ Bitte zuerst browser_open aufrufen"
    
    if url:
        _browser_page.goto(url, timeout=30000)
        _browser_page.wait_for_load_state("domcontentloaded", timeout=15000)
        _browser_page.wait_for_timeout(3000)
    
    try:
        search = _browser_page.query_selector('#twotabsearchtextbox')
        if search:
            return "# Suchfeld gefunden! Nutze: browser_type('#twotabsearchtextbox', 'SUCHBEGRIFF')"
    except:
        pass
    
    links = _browser_page.query_selector_all("a[href]")
    buttons = _browser_page.query_selector_all("button")
    inputs = _browser_page.query_selector_all("input")
    
    elements = []
    ref = 1
    
    for link in links[:30]:
        try:
            text = link.inner_text()
            href = link.get_attribute("href")
            if text.strip() and len(text.strip()) < 80:
                elements.append(f"[{ref}] LINK: {text.strip()[:50]} → {href}")
                ref += 1
        except:
            pass
    
    for btn in buttons[:15]:
        try:
            text = btn.inner_text()
            if text.strip():
                elements.append(f"[{ref}] BUTTON: {text.strip()[:50]}")
                ref += 1
        except:
            pass
    
    for inp in inputs[:10]:
        try:
            name = inp.get_attribute("name") or inp.get_attribute("id") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            if name or placeholder:
                elements.append(f"[{ref}] INPUT: name={name}, placeholder={placeholder}")
                ref += 1
        except:
            pass
    
    if elements:
        return "# Interaktive Elemente:\n\n" + "\n".join(elements[:30])
    return "❌ Keine Elemente"

# Deprecated stubs - redirect to working implementations
def _deprecated_click(selector: str) -> str:
    return _sync_browser_click(selector)

def _deprecated_auto_click(text: str, url: str = None) -> str:
    return _sync_auto_click(text, url)

def _deprecated_snapshot() -> str:
    return _sync_browser_snapshot()

def _deprecated_structured(url: str = None) -> str:
    return _sync_structured_snapshot(url)

def _deprecated_type(selector: str, text: str) -> str:
    return _sync_browser_type(selector, text)

def _deprecated_screenshot(path: str) -> str:
    return _sync_browser_screenshot(path)

def _deprecated_navigate(url: str, action: str = "goto") -> str:
    return _sync_browser_navigate(url, action)

# ===== ASYNC VERSIONS (not currently used but kept for reference) =====

async def _async_browser_open(url: str) -> str:
    """Open URL (async version)."""
    return _sync_browser_open(url)

# ===== ADDITIONAL BROWSER FUNCTIONS =====

def _sync_browser_type(selector: str, text: str) -> str:
    """Type into selector."""
    result = _send_browser_cmd("type", selector=selector, text=text)
    if result.get("status") == "ok":
        return f"✅ {result.get('message', 'Getippt')}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_snapshot() -> str:
    """Get current page content."""
    result = _send_browser_cmd("snapshot")
    if result.get("status") == "ok":
        return f"# Snapshot\n\n{result.get('content', '')[:10000]}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_structured_snapshot(url: str = None) -> str:
    """Get structured elements."""
    result = _send_browser_cmd("structured")
    if result.get("status") == "ok":
        elements = result.get("elements", [])
        if elements:
            return "# Interaktive Elemente:\n\n" + "\n".join(elements)
        return "❌ Keine Elemente"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_click(selector: str) -> str:
    """Click selector."""
    result = _send_browser_cmd("click", text=selector)
    if result.get("status") == "ok":
        return f"✅ {result.get('message', 'Geklickt')}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_auto_click(text: str, url: str = None) -> str:
    """Auto-click with fallback."""
    result = _send_browser_cmd("click", text=text)
    if result.get("status") == "ok":
        return f"✅ {result.get('message', 'Geklickt')}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_screenshot(path: str) -> str:
    """Take screenshot."""
    result = _send_browser_cmd("screenshot", path=path)
    if result.get("status") == "ok":
        return f"✅ Gespeichert: {path}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_navigate(url: str, action: str = "goto") -> str:
    """Navigate to URL."""
    url = _ensure_url(url)
    result = _send_browser_cmd("navigate", url=url, action=action)
    if result.get("status") == "ok":
        return f"✅ {url}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_snapshot() -> str:
    """Get current page content."""
    result = _send_browser_cmd("snapshot")
    if result.get("status") == "ok":
        return f"# Snapshot\n\n{result.get('content', '')[:10000]}"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_structured_snapshot(url: str = None) -> str:
    """Get structured elements."""
    result = _send_browser_cmd("structured")
    if result.get("status") == "ok":
        elements = result.get("elements", [])
        if elements:
            return "# Interaktive Elemente:\n\n" + "\n".join(elements)
        return "❌ Keine Elemente"
    return f"❌ {result.get('message', 'Fehler')}"

def _sync_browser_click(selector: str) -> str:
    """Click selector."""
    result = _send_browser_cmd("click", text=selector)
    if result.get("status") == "ok":
        return f"✅ {result.get('message', 'Geklickt')}"
    return f"❌ {result.get('message', 'Fehler')}"

async def _async_browser_open(url: str):
    page = _browser_page()
    await page.goto(url)
    title = await page.title()
    content = await page.content()
    return f"✅ {title}\n\n{content[:3000]}"

async def _async_browser_snapshot():
    page = _browser_page()
    content = await page.content()
    return f"# Snapshot\n\n{content[:10000]}"

async def _async_structured_snapshot(url: str = None):
    page = _browser_page()
    
    if url:
        await page.goto(url)
    
    links = await page.query_selector_all("a[href]")
    buttons = await page.query_selector_all("button")
    inputs = await page.query_selector_all("input, select, textarea")
    navs = await page.query_selector_all("nav a")
    
    elements = []
    ref = 1
    
    for nav in navs[:20]:
        try:
            text = await nav.inner_text()
            href = await nav.get_attribute("href")
            if text.strip():
                elements.append(f"[{ref}] LINK: {text.strip()} → {href}")
                ref += 1
        except:
                pass
        
        for link in links[:30]:
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                if text.strip() and len(text.strip()) < 100:
                    elements.append(f"[{ref}] LINK: {text.strip()[:50]} → {href}")
                    ref += 1
            except:
                pass
        
        for btn in buttons[:15]:
            try:
                text = await btn.inner_text()
                if text.strip():
                    elements.append(f"[{ref}] BUTTON: {text.strip()[:50]}")
                    ref += 1
            except:
                pass
        
        for inp in inputs[:10]:
            try:
                name = await inp.get_attribute("name") or await inp.get_attribute("id") or "unknown"
                placeholder = await inp.get_attribute("placeholder") or ""
                input_type = await inp.get_attribute("type") or "text"
                elements.append(f"[{ref}] INPUT ({input_type}): name={name}, placeholder={placeholder[:30]}")
                ref += 1
            except:
                pass
        
        await browser.close()
        
        if elements:
            return "# Interaktive Elemente:\n\n" + "\n".join(elements)
        return "❌ Keine interaktiven Elemente gefunden"

@mcp.tool()
def browser_open(url: str) -> str:
    """Opens a URL in the persistent browser."""
    try:
        result = _sync_browser_open(url)
        _record_tool_call("browser_open", {"url": url}, "✅" in result, result[:100])
        return result
    except Exception as e:
        _record_tool_call("browser_open", {"url": url}, False, str(e))
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_search_products(query: str, limit: int = 10) -> str:
    """Sucht auf Amazon und zeigt Produkte mit Name, Preis und Link."""
    try:
        return _search_amazon_products(query, limit)
    except RecursionError:
        return "❌ Bitte erneut versuchen"
    except Exception as e:
        return f"❌ Fehler: {str(e)[:80]}"

@mcp.tool()
def structured_snapshot(url: str = "") -> str:
    """Gets a structured list of all interactive elements."""
    try:
        return _sync_structured_snapshot(url if url else None)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_click(selector: str) -> str:
    """Clicks an element by CSS selector."""
    try:
        return _sync_browser_click(selector)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_type(selector: str, text: str) -> str:
    """Types text into field."""
    try:
        return _sync_browser_type(selector, text)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_screenshot(path: str = "screenshot.png") -> str:
    """Takes a screenshot."""
    try:
        return _sync_browser_screenshot(path)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_navigate(url: str, action: str = "goto") -> str:
    """Navigate back, forward, or to URL."""
    try:
        return _sync_browser_navigate(url, action)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

async def _async_browser_click(selector: str):
    page = _browser_page()
    try:
        await page.click(selector, timeout=3000)
        return f"✅ Geklickt: {selector}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

async def _async_auto_click(text: str, url: str = None):
    page = _browser_page()
    
    if url:
        await page.goto(url)
    
    # Strategy 1: Exact text
    try:
        await page.click(f"text={text}", timeout=2000)
        return f"✅ Geklickt: {text}"
    except:
        pass
    
    # Strategy 2: Link contains text
    try:
        await page.click(f"a:has-text('{text}')", timeout=2000)
        return f"✅ Geklickt: {text}"
    except:
        pass
    
    # Strategy 3: Self-healing - search all elements
    try:
        links = await page.query_selector_all("a")
        for link in links:
            try:
                link_text = await link.inner_text()
                if text.lower() in link_text.lower():
                    await link.click()
                    return f"✅ Self-Healed: {link_text.strip()}"
            except:
                continue
    except:
        pass
    
    return f"❌ Auto-Click fehlgeschlagen für '{text}'"

async def _async_browser_type(selector: str, text: str):
    page = _browser_page()
    try:
        await page.fill(selector, text)
        return f"✅ Getippt: {text}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

async def _async_browser_screenshot(path: str):
    page = _browser_page()
    try:
        await page.screenshot(path=path)
        return f"✅ Gespeichert: {path}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

async def _async_browser_navigate(url: str, action: str):
    page = _browser_page()
    if action == "back":
        await page.go_back()
        return "✅ Zurück"
    elif action == "forward":
        await page.go_forward()
        return "✅ Vorwärts"
    else:
        await page.goto(url)
        return f"✅ {url}"

@mcp.tool()
def auto_click(text: str, url: str = "https://example.com") -> str:
    """Clicks by text with self-healing fallback."""
    try:
        return _sync_auto_click(text, url)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"


@mcp.tool()
def browser_screenshot(filepath: str = None, path: str = "screenshot.png") -> str:
    """Takes a screenshot and saves it to a file.
    
    Args:
        filepath: Pfad zum Speichern des Screenshots (bevorzugt)
        path: Alternativer Parametername (für Abwärtskompatibilität, Standard: screenshot.png)
    """
    actual_path = filepath or path
    try:
        return _sync_browser_screenshot(actual_path)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_navigate(url: str, action: str = "goto") -> str:
    """Navigate back, forward, or to URL."""
    try:
        return _sync_browser_navigate(url, action)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_new_tab(url: str = "") -> str:
    """Öffnet einen neuen Tab (optional mit URL)."""
    try:
        result = _send_browser_cmd("new_tab", url=url)
        if result.get("status") == "ok":
            return f"✅ Neuer Tab {result.get('tab_index')} von {result.get('total_tabs')} Tabs"
        return f"❌ {result.get('message', 'Fehler')}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_switch_tab(index: int) -> str:
    """Wechselt zu Tab mit Index (0-basiert)."""
    try:
        result = _send_browser_cmd("switch_tab", index=index)
        if result.get("status") == "ok":
            title = result.get('title', '')
            url = result.get('url', '')
            return f"✅ Zu Tab {index} gewechselt\n{title}\n{url}"
        return f"❌ {result.get('message', 'Fehler')}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_close_tab(index: int = None) -> str:
    """Schließt Tab (aktueller wenn None)."""
    try:
        result = _send_browser_cmd("close_tab", index=index)
        if result.get("status") == "ok":
            return f"✅ Tab geschlossen, noch {result.get('remaining_tabs')} Tabs"
        return f"❌ {result.get('message', 'Fehler')}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_list_tabs() -> str:
    """Listet alle offenen Tabs auf."""
    try:
        result = _send_browser_cmd("list_tabs")
        if result.get("status") == "ok":
            tabs = result.get("tabs", [])
            if not tabs:
                return "❌ Keine Tabs offen"
            output = [f"📑 {len(tabs)} Tabs offen:\n"]
            for tab in tabs:
                marker = "→ " if tab.get("current") else "  "
                output.append(f"{marker}[{tab.get('index')}] {tab.get('title', '')[:40]}")
                output.append(f"     {tab.get('url', '')}")
            return "\n".join(output)
        return f"❌ {result.get('message', 'Fehler')}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_wait_for(selector: str, timeout: int = 5000) -> str:
    """Wartet auf Element (CSS-Selektor)."""
    try:
        result = _send_browser_cmd("wait_for", selector=selector, timeout=timeout)
        if result.get("status") == "ok":
            return f"✅ {result.get('message')}"
        return f"❌ {result.get('message', 'Fehler')}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def browser_wait_for_load(timeout: int = 30000) -> str:
    """Wartet bis Seite geladen ist."""
    try:
        result = _send_browser_cmd("wait_for_load", timeout=timeout)
        if result.get("status") == "ok":
            return f"✅ {result.get('message')}"
        return f"❌ {result.get('message', 'Fehler')}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

# ========== SELF-LEARNING SYSTEM ==========

_tool_usage_collection = None
_tool_chain_history = []  # Speichert Tool-Aufruf-Ketten
_PATTERNS_THRESHOLD = 3  # Nach 3 Aufrufen -> Pattern erkennen
_MAX_HISTORY = 100  # Max chain history

def _init_chroma_usage():
    """Initialisiere ChromaDB für Tool Usage Tracking."""
    global _tool_usage_collection
    
    if _tool_usage_collection is not None:
        return _tool_usage_collection
    
    try:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _tool_usage_collection = client.get_or_create_collection(name="jarvis_tool_usage")
        return _tool_usage_collection
    except Exception as e:
        print(f"Usage DB init error: {e}")
        return None

def _args_to_hash(args: dict) -> str:
    """Erstelle deterministischen Hash aus Args."""
    import hashlib
    import json
    args_str = json.dumps(args, sort_keys=True)
    return hashlib.md5(args_str.encode()).hexdigest()[:12]

def _record_tool_call(tool_name: str, args, success: bool, output = "") -> None:
    """Record einen Tool-Aufruf für Self-Learning - nur primitive Typen."""
    global _tool_chain_history
    
    collection = _init_chroma_usage()
    if not collection:
        return
    
    # Serialize args safely - only primitive types
    try:
        import hashlib
        args_json = json.dumps(args, sort_keys=True, default=str)
        args_hash = hashlib.md5(args_json.encode()).hexdigest()[:12]
    except:
        args_hash = "invalid"
    
    doc_id = f"{tool_name}_{args_hash}"
    
    # Ensure output is string
    if output is None:
        output = ""
    output_str = str(output)[:500] if output else ""
    
    try:
        existing = collection.get(ids=[doc_id])
        if existing and existing.get('documents'):
            data = json.loads(existing['documents'][0])
            data['count'] = data.get('count', 0) + 1
            if success:
                data['success_count'] = data.get('success_count', 0) + 1
            data['last_output'] = output_str
            # Store primitive args only
            data['last_args'] = {"_serialized": args_json[:200]} if args_json else {}
            collection.update(
                ids=[doc_id],
                documents=[json.dumps(data)]
            )
        else:
            data = {
                "tool": tool_name,
                "args": {"_serialized": args_json[:200]} if args_json else {},
                "count": 1,
"success_count": 1 if success else 0,
                "last_output": output_str
            }
            collection.add(
                ids=[doc_id],
                documents=[json.dumps(data)],
                metadatas=[{"tool": tool_name}]
            )
    except Exception as e:
        pass
    
    # Also update in-memory history (but keep it simple)
    if hasattr(_tool_chain_history, 'append'):
        _tool_chain_history.append({
            "tool": tool_name,
            "success": success,
            "ts": __import__("time").time()
        })
        if len(_tool_chain_history) > 100:
            _tool_chain_history = _tool_chain_history[-100:]
    
    # Auto-pattern creation disabled: noisily creates useless skills
    # (e.g. "3x hackernews_trending") and desyncs .chroma/ vs chroma_db/.

def _detect_patterns() -> list:
    """Erkenne wiederholte Tool-Ketten als Patterns."""
    global _tool_chain_history
    
    if len(_tool_chain_history) < _PATTERNS_THRESHOLD:
        return []
    
    tool_sequence = [h['tool'] for h in _tool_chain_history[-20:]]  # Check last 20
    
    patterns = []
    seq_len = len(tool_sequence)
    
    # Check for single tool repetition (e.g., browser_open x 3+)
    from collections import Counter
    tool_counts = Counter(tool_sequence)
    for tool, count in tool_counts.items():
        if count >= _PATTERNS_THRESHOLD:
            # Find consecutive runs
            consecutive_count = 0
            max_consecutive = 0
            for t in tool_sequence:
                if t == tool:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
            
            if max_consecutive >= _PATTERNS_THRESHOLD:
                patterns.append({
                    "chain": [tool] * _PATTERNS_THRESHOLD,
                    "count": max_consecutive,
                    "start_idx": 0,
                    "type": "repetition"
                })
    
    # Check for consecutive patterns of length 2+
    if not patterns:  # Only check chains if no single tool pattern found
        for length in range(2, min(seq_len + 1, 6)):
            for i in range(seq_len - length + 1):
                chain = tuple(tool_sequence[i:i+length])
                # Count consecutive occurrences
                count = 0
                j = 0
                while j <= seq_len - length:
                    if tuple(tool_sequence[j:j+length]) == chain:
                        count += 1
                        j += length
                    else:
                        j += 1
                if count >= _PATTERNS_THRESHOLD:
                    patterns.append({
                        "chain": list(chain),
                        "count": count,
                        "start_idx": i,
                        "type": "chain"
                    })
                    break
    
    return patterns

def _create_skill_from_pattern(pattern: dict) -> None:
    """Erstelle einen Skill aus einem erkannten Pattern."""
    skills_collection = _init_chroma_skills()
    if not skills_collection:
        return
    
    chain = pattern.get("chain", [])
    if not chain:
        return
    
    # Create a unique skill ID from the pattern
    import hashlib
    chain_str = "->".join(chain)
    skill_id = f"auto_pattern_{hashlib.md5(chain_str.encode()).hexdigest()[:12]}"
    
    # Check if skill already exists
    try:
        existing = skills_collection.get(ids=[skill_id])
        if existing and existing.get('documents'):
            return  # Skill already exists
    except:
        pass
    
    # Create skill data
    skill_data = {
        "name": f"auto_{chain[0]}_pattern",
        "description": f"Automatisch gelerntes Pattern: {' -> '.join(chain)}",
        "tool_chain": chain,
        "auto_created": True,
        "usage_count": pattern.get("count", 0),
        "created_at": __import__("time").time()
    }
    
    try:
        skills_collection.add(
            ids=[skill_id],
            documents=[json.dumps(skill_data)],
            metadatas=[{"source": "auto_pattern", "tools": ",".join(chain[:3])}]
        )
        print(f"✅ Skill aus Pattern erstellt: {skill_id}")
    except Exception as e:
        print(f"Fehler beim Erstellen des Pattern-Skills: {e}")

def _check_and_create_skill(tool_name: str, args: dict, success: bool) -> None:
    """Prüfe ob Skill erstellt werden soll."""
    if not success:
        return
    
    collection = _init_chroma_usage()
    if not collection:
        return
    
    args_hash = _args_to_hash(args)
    doc_id = f"{tool_name}_{args_hash}"
    
    try:
        existing = collection.get(ids=[doc_id])
        if existing and existing.get('documents'):
            raw_data = existing['documents'][0]
            if isinstance(raw_data, str):
                data = json.loads(raw_data)
            else:
                data = raw_data
            count = data.get('count', 0)
            
            if count >= _PATTERNS_THRESHOLD:
                _create_learned_skill(tool_name, args, data)
    except Exception as e:
        print(f"Pattern check error: {e}")
        pass

def _create_learned_skill(tool_name: str, base_args: dict, usage_data: dict) -> str:
    """Erstelle automatisch einen Skill aus erkanntem Pattern."""
    skills_collection = _init_chroma_skills()
    if not skills_collection:
        return "❌ ChromaDB nicht verfügbar"
    
    keyword_parts = []
    for k, v in base_args.items():
        if isinstance(v, str) and len(v) < 20:
            keyword_parts.append(v)
    
    keyword = "_".join(keyword_parts[:3]) if keyword_parts else tool_name
    skill_id = f"auto_{tool_name}_{_args_to_hash(base_args)}"
    
    skill_data = {
        "tool": tool_name,
        "args": base_args,
        "auto_created": True,
        "usage_count": usage_data.get('count', 0),
        "description": f"Automatisch gelernt: {tool_name}"
    }
    
    try:
        skills_collection.add(
            ids=[skill_id],
            documents=[json.dumps(skill_data)],
            metadatas=[{"keyword": keyword, "tool": tool_name}]
        )
        return f"✅ Skill erstellt: {keyword}"
    except Exception as e:
        return f"❌ Skill erstellen fehlgeschlagen: {e}"

@mcp.tool()
def learn_skill(tool_name: str, skill_keyword: str, description: str = "") -> str:
    """Trainiere V.I.N.C.E.N.T. manuell auf einen Tool mit Argumenten (z.B. 'learn_skill browser_open amazon.de amazon_suche')."""
    try:
        args = {}
        parts = skill_keyword.split()
        
        if "amazon" in skill_keyword.lower():
            if "search" in skill_keyword.lower() or "suche" in skill_keyword.lower():
                if len(parts) > 1:
                    args = {"query": " ".join(parts[1:])}
                    tool_name = "browser_search_products"
                else:
                    args = {"url": parts[0] if parts else "amazon.de"}
                    tool_name = "browser_open"
        elif tool_name == "browser_open":
            args = {"url": skill_keyword}
        
        skill_data = {
            "tool": tool_name,
            "args": args,
            "description": description or f"Manuell gelernt: {skill_keyword}",
            "manual": True
        }
        
        skills_collection = _init_chroma_skills()
        if skills_collection:
            skills_collection.add(
                ids=[f"manual_{skill_keyword}"],
                documents=[json.dumps(skill_data)],
                metadatas=[{"keyword": skill_keyword, "tool": tool_name}]
            )
            return f"✅ Skill trainiert: {skill_keyword} -> {tool_name}"
        
        return "❌ ChromaDB Fehler"
    except Exception as e:
        return f"❌ Lern-Fehler: {str(e)}"

@mcp.tool()
def show_tool_usage() -> str:
    """Zeige Tool-Nutzungsstatistiken."""
    collection = _init_chroma_usage()
    if not collection:
        return "❌ Usage DB nicht verfügbar"
    
    try:
        all_data = collection.get()
        if not all_data.get('ids'):
            return "Noch keine Tool-Nutzung aufgezeichnet."
        
        stats = {}
        for i, doc in enumerate(all_data['documents']):
            data = json.loads(doc)
            tool = data.get('tool', 'unknown')
            if tool not in stats:
                stats[tool] = {"count": 0, "success": 0}
            stats[tool]['count'] += data.get('count', 0)
            stats[tool]['success'] += data.get('success_count', 0)
        
        lines = ["📊 Tool-Nutzung:", ""]
        for tool, s in sorted(stats.items(), key=lambda x: -x[1]['count']):
            lines.append(f"- {tool}: {s['count']}x (erfolgreich: {s['success']})")
        
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

# ========== EXISTING SKILLS CODE ==========

_chroma_client = None
_skills_collection = None
_memory_collection = None

def _init_chroma_skills():
    global _chroma_client, _skills_collection

    if _skills_collection is not None:
        return _skills_collection

    try:
        import chromadb
        from chromadb.config import Settings
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        _skills_collection = _chroma_client.get_or_create_collection(name="jarvis_skills")
        return _skills_collection
    except Exception as e:
        print(f"Skills init error: {e}")
        return None

def _init_chroma_memory():
    """Initialisiert ChromaDB für Langzeit-Gedächtnis."""
    global _chroma_client, _memory_collection
    if _memory_collection is not None:
        return _memory_collection
    try:
        import chromadb
        if _chroma_client is None:
            os.makedirs(CHROMA_DIR, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        _memory_collection = _chroma_client.get_or_create_collection(name="jarvis_memory")
        return _memory_collection
    except Exception as e:
        print(f"Memory init error: {e}")
        return None

def _init_chroma():
    """Alias für RAG-Tools – nutzt gleiche ChromaDB wie Memory."""
    return _init_chroma_memory()

def _detect_project_type(root_path: str) -> dict:
    """Erkennt Projekt-Typ, Sprachen und Frameworks."""
    result = {"type": None, "languages": [], "frameworks": []}
    
    # Check for specific files
    files = os.listdir(root_path) if os.path.isdir(root_path) else []
    
    # Python
    if any(f in files for f in ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]):
        result["type"] = "python"
        result["languages"].append("Python")
        if "requirements.txt" in files:
            try:
                with open(os.path.join(root_path, "requirements.txt"), 'r') as f:
                    content = f.read().lower()
                    if "django" in content:
                        result["frameworks"].append("Django")
                    if "flask" in content:
                        result["frameworks"].append("Flask")
                    if "fastapi" in content:
                        result["frameworks"].append("FastAPI")
            except:
                pass
    
    # JavaScript/Node
    if "package.json" in files:
        result["type"] = "node" if result["type"] is None else result["type"]
        result["languages"].append("JavaScript/TypeScript")
        try:
            with open(os.path.join(root_path, "package.json"), 'r') as f:
                import json
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "react" in deps:
                    result["frameworks"].append("React")
                if "vue" in deps:
                    result["frameworks"].append("Vue")
                if "next" in deps:
                    result["frameworks"].append("Next.js")
        except:
            pass
    
    # HTML
    if any(f.endswith(('.html', '.htm')) for f in files):
        if result["type"] is None:
            result["type"] = "html"
    
    return result

@mcp.tool()
def list_skills() -> str:
    """Listet alle selbstgelernten Skills auf."""
    try:
        collection = _init_chroma_skills()
        if not collection:
            return "❌ ChromaDB nicht verfügbar"
        
        results = collection.get(include=["documents", "metadatas"])
        
        if not results or not results.get('documents'):
            return "❌ Noch keine Skills gelernt."
        
        import json
        output = ["# Selbstgelernte Skills:\n"]
        for i, doc in enumerate(results['documents']):
            # Handle both string and list of strings
            if isinstance(doc, list):
                doc = doc[0] if doc else ''
            if not doc or not isinstance(doc, str):
                output.append(f"\n{i+1}. **Invalid skill data (not a string)**")
                continue
            doc = doc.strip()
            if not doc:
                output.append(f"\n{i+1}. **Empty skill data**")
                continue
            try:
                data = json.loads(doc)
                # Use name, fallback to tool, then 'Unnamed'
                name = data.get('name') or data.get('tool', 'Unnamed')
                tool = data.get('tool', 'N/A')
                keywords = data.get('keywords', 'N/A')
                success_count = data.get('success_count', 0)
                auto = data.get('auto_created', False)
                manual = data.get('manual', False)
                
                output.append(f"\n{i+1}. **{name}**")
                output.append(f"   - Tool: {tool}")
                if keywords != 'N/A':
                    output.append(f"   - Keywords: {keywords}")
                output.append(f"   - Erfolge: {success_count}")
                if auto:
                    output.append(f"   - Typ: 🤖 Auto-gelernt")
                if manual:
                    output.append(f"   - Typ: ✋ Manuell")
            except json.JSONDecodeError as e:
                output.append(f"\n{i+1}. **Invalid skill data (JSON error: {str(e)})**")
                continue
        
        return "\n".join(output)
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def use_skill(keyword: str) -> str:
    """Führt einen Skill aus (anhand von Keyword)."""
    try:
        collection = _init_chroma_skills()
        if not collection:
            return "❌ ChromaDB nicht verfügbar"
        
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        q_embedding = model.encode(keyword).tolist()
        
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=1,
            include=["documents", "metadatas"]
        )
        
        if not results or not results.get('documents'):
            return f"❌ Kein Skill gefunden für '{keyword}'"
        
        import json
        # Fix: Handle both string and dict cases
        raw_data = results['documents'][0][0]
        if isinstance(raw_data, str):
            skill_data = json.loads(raw_data)
        else:
            skill_data = raw_data
        tool_name = skill_data.get('tool', '')
        # Fix: Handle args that might already be a dict
        raw_args = skill_data.get('args', '{}')
        if isinstance(raw_args, str):
            args = json.loads(raw_args)
        else:
            args = raw_args
        
        # Execute the tool based on tool_name
        if tool_name == 'browser_open':
            return browser_open(args.get('url', ''))
        elif tool_name == 'youtube_trending':
            return youtube_trending(args.get('language', ''), args.get('limit', 10))
        elif tool_name == 'save_memory':
            return save_memory(args.get('fact', ''), args.get('importance', 'normal'))
        elif tool_name == 'browser_search_products':
            return browser_search_products(args.get('query', ''), args.get('limit', 10))
        elif tool_name == 'web_scrape':
            return web_scrape(args.get('url', ''))
        else:
            # Try to call the tool dynamically
            try:
                import inspect
                # Get all available functions
                all_tools = {name: obj for name, obj in globals().items() 
                            if callable(obj) and hasattr(obj, '_is_tool')}
                if tool_name in all_tools:
                    # Call with args
                    if isinstance(args, dict):
                        return all_tools[tool_name](**args)
                    else:
                        return all_tools[tool_name](args)
            except:
                pass
            return f"❌ Tool {tool_name} nicht unterstützt"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def save_memory(fact: str, importance: str = "normal") -> str:
    """Speichere eine Information dauerhaft im Gedächtnis.
    
    Args:
        fact: Die Information die gespeichert werden soll
        importance: Wichtigkeit (low, normal, high) - default: normal
    """
    global _chroma_client, _memory_collection
    
    try:
        import chromadb
        import uuid
        import datetime
        import os
        
        if _memory_collection is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            chroma_dir = os.path.join(base_dir, ".chroma")
            _chroma_client = chromadb.PersistentClient(path=chroma_dir)
            _memory_collection = _chroma_client.get_or_create_collection(name="jarvis_memory")
        
        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        
        _memory_collection.add(
            ids=[mem_id],
            documents=[fact],
            metadatas=[{
                "type": "fact",
                "importance": importance,
                "timestamp": datetime.datetime.now().isoformat()
            }]
        )
        _record_tool_call("save_memory", {"fact": fact, "importance": importance}, True, fact[:100])
        return f"✅ Gespeichert: {fact[:80]}{'...' if len(fact) > 80 else ''}"
    except Exception as e:
        _record_tool_call("save_memory", {"fact": fact, "importance": importance}, False, str(e))
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def search_memory(query: str, limit: int = 5) -> str:
    """Suche in gespeicherten Erinnerungen.
    
    Args:
        query: Die Suchanfrage
        limit: Maximale Anzahl Ergebnisse - default: 5
    """
    global _chroma_client, _memory_collection
    
    try:
        import chromadb
        import os
        
        if _memory_collection is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            chroma_dir = os.path.join(base_dir, ".chroma")
            _chroma_client = chromadb.PersistentClient(path=chroma_dir)
            _memory_collection = _chroma_client.get_or_create_collection(name="jarvis_memory")
        
        results = _memory_collection.get(include=["documents", "metadatas"])
        
        if not results or not results.get('documents'):
            return "❌ Noch keine Erinnerungen gespeichert."
        
        matches = []
        query_lower = query.lower()
        for i, doc in enumerate(results['documents']):
            if query_lower in doc.lower():
                meta = results['metadatas'][i] if i < len(results['metadatas']) else {}
                importance = meta.get('importance', 'normal')
                matches.append({
                    "fact": doc,
                    "importance": importance,
                    "meta": meta
                })
        
        if not matches:
            return f"❌ Keine Ergebnisse für: {query}"
        
        output = [f"# Erinnerungen zu '{query}' ({len(matches)} Treffer):\n"]
        for i, m in enumerate(matches[:limit], 1):
            imp_emoji = {"high": "⭐", "normal": "💡", "low": "📝"}.get(m['importance'], "💡")
            output.append(f"\n{i}. {imp_emoji} {m['fact'][:100]}")
        
        result_str = "\n".join(output)
        _record_tool_call("search_memory", {"query": query, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("search_memory", {"query": query, "limit": limit}, False, str(e))
        return f"❌ Fehler: {str(e)}"

@mcp.tool()
def run_python(code: str) -> str:
    """Führt Python-Code aus (safety limited). Max 8000 Zeichen.
    
    Args:
        code: Python-Code zum Ausführen (max 8000 Zeichen)
    """
    if len(code) > 8000:
        return f"❌ Code zu groß ({len(code)} Zeichen). Maximal 8000 Zeichen pro Aufruf."
    # Sicherheitscheck - nur bestimmte Module erlaubt
    forbidden = ["import os", "import sys", "subprocess", "socket", "requests"]
    for f in forbidden:
        if f in code:
            return f"❌ Nicht erlaubt: {f}"
    
    try:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        exec(code, {"__builtins__": __builtins__})
        
        return f"✅ Code ausgeführt\nOutput:\n{output.getvalue()}"
    except Exception as e:
        _record_tool_call("run_python", {"code": code[:100]}, False, str(e))
        return f"❌ Fehler: {str(e)}"

# ========== PROJECT & RAG TOOLS ==========

@mcp.tool()
def analyze_project(root_path: str = None, filepath: str = None, path: str = None, max_files: int = 50) -> str:
    """Analysiert ein Projekt und gibt eine strukturierte Übersicht zurück.
    
    Args:
        root_path: Pfad zum Projekt-Ordner (bevorzugt)
        filepath: Alternativer Parametername (für Abwärtskompatibilität)
        path: Alternativer Parametername (für Abwärtskompatibilität)
        max_files: Maximale Anzahl Dateien für Analyse (Standard: 50)
    """
    actual_path = root_path or filepath or path
    if not actual_path:
        return "❌ Fehler: 'root_path', 'filepath' oder 'path' Parameter erforderlich"
    
    try:
        from os import walk
        from os.path import join, basename, relpath, isdir
        
        if not is_path_allowed(actual_path):
            return "❌ Zugriff verweigert: Pfad außerhalb der Whitelist."
        if not isdir(actual_path):
            return "❌ Angegebener Pfad ist kein Ordner."
        
        # Detect project type
        project_info = _detect_project_type(actual_path)
        
        # Count files by type
        file_stats = {"python": 0, "javascript": 0, "html": 0, "css": 0, "other": 0}
        all_files = []
        
        for dirpath, dirnames, filenames in walk(root_path):
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv', 'env']]
            for f in filenames:
                if not f.startswith('.'):
                    fpath = join(dirpath, f)
                    all_files.append(fpath)
                    if f.endswith('.py'):
                        file_stats["python"] += 1
                    elif f.endswith(('.js', '.ts', '.jsx', '.tsx')):
                        file_stats["javascript"] += 1
                    elif f.endswith(('.html', '.htm')):
                        file_stats["html"] += 1
                    elif f.endswith('.css'):
                        file_stats["css"] += 1
                    else:
                        file_stats["other"] += 1
        
        lines = []
        lines.append("=" * 50)
        lines.append(f"📊 PROJEKT-ANALYSE: {basename(actual_path)}")
        lines.append("=" * 50)
        
        proj_type = project_info["type"].upper() if project_info["type"] else "UNKNOWN"
        lines.append(f"\n🔹 Typ: {proj_type}")
        if project_info["languages"]:
            lines.append(f"🔹 Sprachen: {', '.join(project_info['languages'])}")
        if project_info["frameworks"]:
            lines.append(f"🔹 Frameworks: {', '.join(project_info['frameworks'])}")
        
        lines.append(f"\n📁 Dateien gesamt: {len(all_files)}")
        lines.append(f"  - Python: {file_stats['python']}")
        lines.append(f"  - JavaScript/TypeScript: {file_stats['javascript']}")
        lines.append(f"  - HTML: {file_stats['html']}")
        lines.append(f"  - CSS: {file_stats['css']}")
        lines.append(f"  - Sonstige: {file_stats['other']}")
        
        result = "\n".join(lines)
        _record_tool_call("analyze_project", {"root_path": actual_path, "max_files": max_files}, True, result[:100])
        return result
        
    except Exception as e:
        _record_tool_call("analyze_project", {"root_path": actual_path, "max_files": max_files}, False, str(e))
        return f"❌ Fehler bei Projekt-Analyse: {str(e)}"

@mcp.tool()
def add_project_to_rag(root_path: str = None, filepath: str = None, path: str = None, max_files: int = 50, force_reload: bool = False) -> str:
    """Lädt ein Projekt in den RAG-Index für semantische Suche.
    
    Args:
        root_path: Pfad zum Projekt-Ordner (bevorzugt)
        filepath: Alternativer Parametername (für Abwärtskompatibilität)
        path: Alternativer Parametername (für Abwärtskompatibilität)
        max_files: Maximale Anzahl Dateien (Standard: 50)
        force_reload: Bestehenden Index löschen und neu laden
    """
    actual_path = root_path or filepath or path
    if not actual_path:
        return "❌ Fehler: 'root_path', 'filepath' oder 'path' Parameter erforderlich"
    
    try:
        collection = _init_chroma()
        if collection is None:
            return "❌ ChromaDB nicht verfügbar."
        
        if force_reload:
            try:
                collection.delete(where={"source": "project"})
            except:
                pass
        
        if not is_path_allowed(actual_path):
            return "❌ Zugriff verweigert."
        if not isdir(actual_path):
            return "❌ Angegebener Pfad ist kein Ordner."
        
        # Collect files
        all_files = []
        for dirpath, dirnames, filenames in walk(actual_path):
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv', 'env']]
            for f in filenames:
                if not f.startswith('.'):
                    fpath = join(dirpath, f)
                    all_files.append(fpath)
        
        all_files = all_files[:max_files]
        
        # Load into RAG (simplified - reuse existing _load_document logic)
        loaded = 0
        for fpath in all_files:
            try:
                # Read file content
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Simple chunking
                chunks = [content[i:i+500] for i in range(0, len(content), 500)]
                for i, chunk in enumerate(chunks[:10]):  # Limit chunks per file
                    doc_id = f"project_{fpath}_{i}"
                    collection.add(
                        ids=[doc_id],
                        documents=[chunk],
                        metadatas=[{"source": "project", "file": fpath, "chunk": i}]
                    )
                    loaded += 1
            except:
                pass
        
        result = f"✅ Projekt in RAG geladen: {loaded} Chunks"
        _record_tool_call("add_project_to_rag", {"root_path": root_path, "max_files": max_files, "force_reload": force_reload}, True, result)
        return result
        
    except Exception as e:
        _record_tool_call("add_project_to_rag", {"root_path": root_path, "max_files": max_files}, False, str(e))
        return f"❌ Fehler beim Laden in RAG: {str(e)}"

@mcp.tool()
def clear_project_rag() -> str:
    """Löscht den Projekt-RAG-Index."""
    try:
        collection = _init_chroma()
        if collection:
            collection.delete(where={"source": "project"})
        _record_tool_call("clear_project_rag", {}, True, "Project RAG cleared")
        return "✅ Projekt-RAG gelöscht."
    except Exception as e:
        _record_tool_call("clear_project_rag", {}, False, str(e))
        return f"❌ Fehler beim Löschen: {str(e)}"

@mcp.tool()
def patch_file(file_path: str = None, filepath: str = None, path: str = None, start_line: int = 1, end_line: int = 1, new_content: str = "", base64_content: str = None) -> str:
    """Ersetzt Zeilen in einer Datei (1-basiert, inklusiv)."""
    actual_path = resolve_path(file_path or filepath or path)
    if not actual_path:
        return "❌ Fehler: 'file_path', 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return f"❌ Zugriff verweigert: {actual_path}"
    if not os.path.isfile(actual_path):
        return f"❌ Datei nicht gefunden: {actual_path}"
    
    try:
        # Decode base64 if provided
        if base64_content:
            import base64
            try:
                decoded = base64.b64decode(base64_content).decode('utf-8')
                new_content = decoded
            except Exception as e:
                return f"❌ Fehler beim Dekodieren von base64_content: {str(e)}"
        
        with open(actual_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Convert to 0-based index
        idx_start = max(start_line - 1, 0)
        idx_end = min(end_line, len(lines))
        
        patch_lines = new_content.splitlines(keepends=True)
        if patch_lines and not patch_lines[-1].endswith('\n'):
            patch_lines[-1] += '\n'
        
        new_lines = lines[:idx_start] + patch_lines + lines[idx_end:]
        
        # Backup
        backup_path = actual_path + ".bak"
        shutil.copy2(actual_path, backup_path)
        
        with open(actual_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        _record_tool_call("patch_file", {"file_path": actual_path, "start_line": start_line, "end_line": end_line}, True, f"Patched {actual_path}")
        return f"✅ Datei gepatcht: {actual_path} ({len(new_content)} Zeichen, Backup: {backup_path})"
        
    except Exception as e:
        _record_tool_call("patch_file", {"file_path": actual_path, "start_line": start_line, "end_line": end_line}, False, str(e))
        return f"❌ Fehler beim Patchen: {str(e)}"

@mcp.tool()
def scan_folder(root_path: str = None, filepath: str = None, path: str = None, extensions: Optional[List[str]] = None) -> str:
    """Scannt einen Ordner rekursiv nach Dateien mit den gegebenen Erweiterungen."""
    actual_path = resolve_path(root_path or filepath or path)
    if not actual_path:
        return "❌ Fehler: 'root_path', 'filepath' oder 'path' Parameter erforderlich"
    
    if not is_path_allowed(actual_path):
        return "❌ Zugriff verweigert: Ordner außerhalb der Whitelist."
    if not os.path.isdir(actual_path):
        return "❌ Angegebener Pfad ist kein Ordner."
    
    if extensions is None:
        extensions = [".py", ".js", ".ts", ".html", ".htm", ".css", ".json", ".txt", ".md", ".yaml", ".yml"]
    
    try:
        tree_lines = []
        file_contents = {}
        
        for dirpath, dirnames, filenames in os.walk(actual_path):
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'dist', 'build']]
            rel_dir = os.path.relpath(dirpath, actual_path)
            indent = "  " * rel_dir.count(os.sep) if rel_dir != "." else ""
            
            if rel_dir != ".":
                tree_lines.append(f"{indent}{os.path.basename(dirpath)}/")
            
            for f in sorted(filenames):
                if any(f.lower().endswith(ext) for ext in extensions):
                    fpath = os.path.join(dirpath, f)
                    rel_file = os.path.relpath(fpath, actual_path)
                    indent_file = "  " * (rel_dir.count(os.sep) + (1 if rel_dir != "." else 0)) + "- "
                    tree_lines.append(f"{indent_file}{f}")
        
        result = "\n".join(tree_lines[:100])  # Limit output
        _record_tool_call("scan_folder", {"root_path": actual_path, "extensions": extensions}, True, result[:100])
        return f"📁 Ordner-Scan: {actual_path}\n\n{result}"
        
    except Exception as e:
        _record_tool_call("scan_folder", {"root_path": actual_path}, False, str(e))
        return f"❌ Fehler beim Scannen: {str(e)}"

@mcp.tool()
def list_memory(limit: int = 50) -> str:
    """Listet alle Erinnerungen mit IDs und Metadaten.
    
    Args:
        limit: Maximale Anzahl Ergebnisse (Standard: 50)
    """
    try:
        collection = _init_chroma_memory()
        if collection is None:
            return "❌ Memory-Kollektion nicht verfügbar."
        
        results = collection.get(include=["documents", "metadatas"], limit=limit)
        ids = results.get("ids", [])
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])
        
        if not ids:
            return "📭 Keine Erinnerungen gespeichert."
        
        output = [f"📚 **Erinnerungen ({len(ids)})**:\n"]
        for i, (mem_id, doc, meta) in enumerate(zip(ids, docs, metas), 1):
            importance = meta.get("importance", "?") if meta else "?"
            output.append(f"{i}. **[{importance}]** {doc[:100]}... (ID: {mem_id[:20]}...)")
        
        result = "\n".join(output)
        _record_tool_call("list_memory", {"limit": limit}, True, result[:100])
        return result
        
    except Exception as e:
        _record_tool_call("list_memory", {"limit": limit}, False, str(e))
        return f"❌ Fehler beim Laden: {str(e)}"

@mcp.tool()
def delete_memory(memory_id: str) -> str:
    """Löscht einen spezifischen Eintrag aus dem Langzeitgedächtnis.
    
    Args:
        memory_id: Die ID der zu löschenden Erinnerung
    """
    try:
        collection = _init_chroma_memory()
        if collection is None:
            return "❌ Memory-Kollektion nicht verfügbar."
        
        collection.delete(ids=[memory_id])
        _record_tool_call("delete_memory", {"memory_id": memory_id}, True, f"Deleted {memory_id}")
        return f"✓ Erinnerung gelöscht: {memory_id}"
        
    except Exception as e:
        _record_tool_call("delete_memory", {"memory_id": memory_id}, False, str(e))
        return f"❌ Fehler beim Löschen: {str(e)}"

@mcp.tool()
def vincent_status() -> str:
    """Gibt den Status von V.I.N.C.E.N.T. zurück."""
    return json.dumps({
        "status": "online",
        "tools_count": 52,
        "available_tools": [
            "read_file", "write_file", "append_to_file", "list_directory",
            "search_files", "grep", "get_file_info", "create_directory",
            "delete_file", "web_scrape", "deep_scrape", 
            "browser_open", "browser_snapshot", "structured_snapshot", "auto_click", 
            "browser_click", "browser_type", "browser_screenshot", "browser_navigate",
            "browser_new_tab", "browser_switch_tab", "browser_close_tab", "browser_list_tabs",
            "browser_wait_for", "browser_wait_for_load", "browser_search_products",
            "list_skills", "use_skill", "learn_skill", "show_tool_usage",
            "run_python", "vincent_status",
            "youtube_trending", "github_trending", "hackernews_trending",
            "google_trends", "reddit_trending", "weather", "imdb_search", "news_headlines",
            "duckduckgo_search", "duckduckgo_images",
            "tavily_search", "tavily_news", "tavily_deep_search",
            "save_memory", "search_memory", "list_memory", "delete_memory",
            "analyze_project", "add_project_to_rag", "clear_project_rag",
            "patch_file", "scan_folder",
            "create_diagram"
        ],
        "version": "3.1"
    }, indent=2)

# ========== TRENDS & INFO TOOLS ==========

@mcp.tool()
def youtube_trending(query: str = "", limit: int = 10) -> str:
    """Sucht nach trending YouTube Videos.
    
    Args:
        query: Suchbegriff (leer für allgemeine Trends)
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        import subprocess
        search_query = query if query else "trending"
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            f"--playlist-end={limit}",
            "--print", "%(title)s|%(view_count)s|%(uploader)s|%(duration)s",
            f"ytsearch{limit}:{search_query}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return f"❌ YouTube Fehler: {result.stderr[:200]}"
        lines = [l for l in result.stdout.strip().split("\n") if l]
        if not lines:
            return f"❌ Keine Ergebnisse für: {search_query}"
        output = [f"📺 **YouTube: {search_query}** (Top {len(lines)})\n"]
        for i, line in enumerate(lines[:limit], 1):
            parts = line.split("|")
            if len(parts) >= 3:
                title = parts[0][:70]
                views = parts[1] if len(parts) > 1 and parts[1] != "None" else "?"
                channel = parts[2][:30] if len(parts) > 2 else "?"
                duration = parts[3] if len(parts) > 3 and parts[3] != "None" else "?"
                try:
                    views_fmt = f"{int(views):,}" if views and views.isdigit() else views
                except:
                    views_fmt = views
                output.append(f"{i}. **{title}**")
                output.append(f"   👁 {views_fmt} | 📺 {channel} | ⏱ {duration}s")
        result_str = "\n".join(output)
        _record_tool_call("youtube_trending", {"query": query, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        err_str = str(e)
        _record_tool_call("youtube_trending", {"query": query, "limit": limit}, False, err_str)
        if "Timeout" in err_str:
            return "❌ YouTube Timeout"
        return f"❌ YouTube Fehler: {err_str}"

@mcp.tool()
def github_trending(language: str = "", limit: int = 10) -> str:
    """Holt trending GitHub Repositories.
    
    Args:
        language: Programmiersprache (z.B. "python", "javascript", leer für alle)
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        url = f"https://github.com/trending" + (f"/{language}" if language else "")
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        repos = soup.select("article.Box-row")
        output = [f"🐙 **GitHub Trending**" + (f" ({language})" if language else "") + f"\n"]
        for i, repo in enumerate(repos[:limit], 1):
            title_el = repo.select_one("h2 a")
            if title_el:
                title = title_el.get_text(strip=True).replace("\n", "").replace(" ", "")
                stars_el = repo.select_one("a[href$='/stargazers']")
                stars = stars_el.get_text(strip=True) if stars_el else "?"
                desc_el = repo.select_one("p")
                desc = desc_el.get_text(strip=True)[:100] if desc_el else "Keine Beschreibung"
                output.append(f"{i}. **{title}** ⭐ {stars}")
                output.append(f"   {desc}")
        result_str = "\n".join(output)
        _record_tool_call("github_trending", {"language": language, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("github_trending", {"language": language, "limit": limit}, False, str(e))
        return f"❌ GitHub Fehler: {str(e)}"

@mcp.tool()
def hackernews_trending(limit: int = 10) -> str:
    """Holt trending Hacker News.
    
    Args:
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        import requests
        from urllib.parse import urlparse
        resp = requests.get(f"https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={limit}", timeout=10)
        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            return "❌ Keine Ergebnisse"
        output = [f"📰 **Hacker News Top {len(hits)}**\n"]
        for i, hit in enumerate(hits[:limit], 1):
            title = hit.get("title", "?")
            url = hit.get("url", "")
            points = hit.get("points", 0)
            comments = hit.get("num_comments", 0)
            domain = urlparse(url).netloc if url else "?"
            output.append(f"{i}. **{title}**")
            output.append(f"   ⬆ {points} pts | 💬 {comments} | {domain}")
        result_str = "\n".join(output)
        _record_tool_call("hackernews_trending", {"limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("hackernews_trending", {"limit": limit}, False, str(e))
        return f"❌ Hacker News Fehler: {str(e)}"

@mcp.tool()
def google_trends(keywords: str = "", country: str = "DE") -> str:
    """Holt Google Trends.
    
    Args:
        keywords: Suchbegriffe (kommagetrennt, leer für allgemeine Trends)
        country: Ländercode (Standard: DE)
    """
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="de-DE", tz=360, timeout=15)
        pytrends.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        })
        time.sleep(3)
        for attempt in range(3):
            try:
                if keywords:
                    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
                    if not kw_list:
                        kw_list = ["Trending"]
                    pytrends.build_payload(kw_list, cat=0, timeframe="now 1-d", geo=country)
                    data = pytrends.related_queries()
                    output = [f"📈 **Google Trends: {keywords}** ({country})\n"]
                    for kw, d in data.items():
                        top = d.get("top")
                        if top is not None and len(top) > 0:
                            output.append(f"\n🔍 **{kw}** - Verwandte Suchen:")
                            for _, row in top.head(5).iterrows():
                                val = row.get("value", "?")
                                output.append(f"   • {row.get('query', '?')} ({val})")
                    result = "\n".join(output) if len(output) > 1 else f"📈 **Google Trends: {keywords}**\nKeine verwandten Suchen gefunden."
                    _record_tool_call("google_trends", {"keywords": keywords, "country": country}, True, result[:100])
                    return result
                else:
                    pytrends.build_payload(["Tech"], cat=0, timeframe="now 1-d", geo=country)
                    data = pytrends.trending_searches(pn="germany")
                    output = [f"📈 **Google Trends Deutschland**\n"]
                    for i, kw in enumerate(data[0][:10], 1):
                        output.append(f"{i}. {kw}")
                    result = "\n".join(output)
                    _record_tool_call("google_trends", {"keywords": keywords, "country": country}, True, result[:100])
                    return result
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
    except Exception as e:
        _record_tool_call("google_trends", {"keywords": keywords, "country": country}, False, str(e))
        return f"❌ Google Trends Fehler: {str(e)}\n💡 Alternativ: 'news_headlines' oder 'tavily_news' für aktuelle Nachrichten."

@mcp.tool()
def reddit_trending(subreddit: str = "popular", limit: int = 10) -> str:
    """Holt trending Reddit Posts via DuckDuckGo Suche (umgeht 403-Fehler).
    
    Args:
        subreddit: Subreddit (Standard: "popular")
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        query = f"site:reddit.com/r/{subreddit} hot"
        
        results = []
        with DDGS() as ddgs:
            ddgs_results = list(ddgs.text(query, max_results=limit))
            for r in ddgs_results:
                results.append(r)
        
        if not results:
            return f"❌ Keine aktuellen Trends für r/{subreddit} über Suche gefunden."
            
        output = [f"🤖 **Reddit Trends: r/{subreddit}** (via DDG-Suche)\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "?").replace(f" : r/{subreddit}", "").replace(" - Reddit", "")
            snippet = r.get("body", "")[:150]
            url = r.get("href", "#")
            output.append(f"{i}. **{title}**")
            output.append(f"   📝 {snippet}")
            output.append(f"   🔗 {url}\n")
            
        result_str = "\n".join(output).strip()
        _record_tool_call("reddit_trending", {"subreddit": subreddit, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("reddit_trending", {"subreddit": subreddit, "limit": limit}, False, str(e))
        return f"❌ Reddit Fehler (Suche): {str(e)}"

@mcp.tool()
def weather(location: str, days: int = 3) -> str:
    """Holt Wetter für einen Ort.
    
    Args:
        location: Städtename (z.B. "Berlin", "München")
        days: Anzahl der Vorhersage-Tage (Standard: 3, max: 7)
    """
    try:
        import requests
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": location, "count": 1, "language": "de", "format": "json"}
        geo_r = requests.get(geo_url, params=geo_params, timeout=10)
        geo_data = geo_r.json()
        if not geo_data.get("results"):
            return f"❌ Ort nicht gefunden: {location}"
        loc = geo_data["results"][0]
        lat, lon, city = loc["latitude"], loc["longitude"], loc["name"]
        country = loc.get("country_code", "")
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "forecast_days": min(days, 7),
            "timezone": "auto"
        }
        w_r = requests.get(weather_url, params=weather_params, timeout=10)
        w_data = w_r.json()
        current = w_data.get("current", {})
        daily = w_data.get("daily", {})
        output = [f"🌤️ **Wetter: {city}, {country}**\n"]
        output.append(f"**Aktuell:** {current.get('temperature_2m', '?')}°C, Wind {current.get('wind_speed_10m', '?')} km/h")
        output.append(f"Feuchtigkeit: {current.get('relative_humidity_2m', '?')}%\n")
        output.append("**Vorhersage:**")
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        prec = daily.get("precipitation_sum", [])
        codes = daily.get("weather_code", [])
        icons = {0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️", 51: "🌧️", 53: "🌧️", 55: "🌧️", 61: "🌧️", 63: "🌧️", 65: "🌧️", 80: "🌦️", 81: "🌦️", 82: "🌦️", 95: "⛈️"}
        for i, date in enumerate(dates[:days]):
            code = codes[i] if i < len(codes) else 0
            icon = icons.get(code, "🌡️")
            output.append(f"  {date}: {icon} {min_temps[i] if i < len(min_temps) else '?'}°C - {max_temps[i] if i < len(max_temps) else '?'}°C, Regen: {prec[i] if i < len(prec) else '?'}mm")
        result_str = "\n".join(output)
        _record_tool_call("weather", {"location": location, "days": days}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("weather", {"location": location, "days": days}, False, str(e))
        return f"❌ Wetter Fehler: {str(e)}"

@mcp.tool()
def imdb_search(query: str, limit: int = 10) -> str:
    """Sucht Filme auf IMDB.
    
    Args:
        query: Suchbegriff (Filmtitel)
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        import requests
        headers = {"User-Agent": "Mozilla/5.0"}
        encoded = query.replace(" ", "+")
        r = requests.get(f"https://v2.sg.media-imdb.com/suggestion/x/{encoded}.json", headers=headers, timeout=10)
        if r.status_code != 200:
            return f"❌ IMDB Suche fehlgeschlagen (Rate-limited)"
        data = r.json()
        items = data.get("d", [])
        if not items:
            return f"❌ Keine Filme gefunden für: {query}"
        output = [f"🎬 **IMDB: {query}**\n"]
        for i, item in enumerate(items[:limit], 1):
            title = item.get("l", "?")
            year = item.get("y", "?")
            actors = ", ".join(item.get("s", "?")[:50] for _ in [1] if item.get("s"))
            output.append(f"{i}. **{title}** ({year})")
            if actors and actors != "?":
                output.append(f"   👤 {actors}")
        result_str = "\n".join(output)
        _record_tool_call("imdb_search", {"query": query, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("imdb_search", {"query": query, "limit": limit}, False, str(e))
        return f"❌ IMDB Fehler: {str(e)}"

@mcp.tool()
def news_headlines(source: str = "all", limit: int = 10) -> str:
    """Holt aktuelle Nachrichten über DuckDuckGo.
    
    Args:
        source: Suchbegriff/Topic (z.B. "tech news", "sports", "breaking news")
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        query = source if source != "all" else "latest news"
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=limit))
        if not results:
            return f"❌ Keine Nachrichten für: {source}"
        output = [f"📰 **Nachrichten: {source}** (Top {len(results)})\n"]
        for i, r in enumerate(results[:limit], 1):
            title = r.get("title", "?")
            url = r.get("url", "")
            desc = r.get("description", "")[:100]
            output.append(f"{i}. **{title}**")
            output.append(f"   🔗 {url}")
            if desc:
                output.append(f"   {desc}...")
        result_str = "\n".join(output)
        _record_tool_call("news_headlines", {"source": source, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("news_headlines", {"source": source, "limit": limit}, False, str(e))
        return f"❌ News Fehler: {str(e)}"

@mcp.tool()
def duckduckgo_search(query: str, limit: int = 10) -> str:
    """Websuche mit DuckDuckGo.
    
    Args:
        query: Suchbegriff
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=limit))
        if not results:
            return f"❌ Keine Ergebnisse für: {query}"
        output = [f"🔍 **DuckDuckGo: {query}** (Top {len(results)})\n"]
        for i, r in enumerate(results[:limit], 1):
            title = r.get("title", "?")[:80]
            url = r.get("url", "")
            desc = r.get("description", "")[:120]
            output.append(f"{i}. **{title}**")
            output.append(f"   🔗 {url}")
            if desc:
                output.append(f"   {desc}...")
        result_str = "\n".join(output)
        _record_tool_call("duckduckgo_search", {"query": query, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("duckduckgo_search", {"query": query, "limit": limit}, False, str(e))
        return f"❌ DuckDuckGo Fehler: {str(e)}"

@mcp.tool()
def duckduckgo_images(query: str, limit: int = 10) -> str:
    """Bildsuche mit DuckDuckGo.
    
    Args:
        query: Suchbegriff
        limit: Anzahl der Ergebnisse (Standard: 10)
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=limit))
        if not results:
            return f"❌ Keine Bilder für: {query}"
        output = [f"🖼️ **Bilder: {query}** (Top {len(results)})\n"]
        for i, r in enumerate(results[:limit], 1):
            title = r.get("title", "?")[:60]
            image_url = r.get("image", "")
            page_url = r.get("url", "")
            output.append(f"{i}. **{title}**")
            output.append(f"   🔗 {page_url}")
        result_str = "\n".join(output)
        _record_tool_call("duckduckgo_images", {"query": query, "limit": limit}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("duckduckgo_images", {"query": query, "limit": limit}, False, str(e))
        return f"❌ Bildsuche Fehler: {str(e)}"

# ========== TAVILY SEARCH TOOLS ==========

def _load_tavily_key():
    import json, os
    # 1. Check environment variable first (most secure)
    env_key = os.environ.get("TAVILY_API_KEY")
    if env_key:
        return env_key
    # 2. Fallback to config.json
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path) as f:
            key = json.load(f).get("tavily_api_key")
            if key:
                return key
    except Exception:
        pass
    # 3. Try .env file
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(dotenv_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("TAVILY_API_KEY="):
                    return line.split("=", 1)[1].strip("\"' ")
    except Exception:
        pass
    return None

TAVILY_API_KEY = _load_tavily_key()

@mcp.tool()
def tavily_search(query: str, search_depth: str = "basic", max_results: int = 10) -> str:
    """Websuche mit Tavily AI (bietet bessere Ergebnisse als DuckDuckGo).
    
    Args:
        query: Suchbegriff
        search_depth: "basic" oder "advanced" (Standard: "basic")
        max_results: Anzahl der Ergebnisse (Standard: 10, max: 20)
    """
    if not TAVILY_API_KEY:
        return "⚠️ Tavily API Key nicht konfiguriert. Setze TAVILY_API_KEY als Umgebungsvariable, in .env-Datei, oder in config.json."
    try:
        import httpx
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        data = {
            "query": query,
            "search_depth": search_depth,
            "max_results": min(max_results, 20),
            "include_answer": True,
            "include_raw_content": False
        }
        resp = httpx.post("https://api.tavily.com/search", json=data, headers=headers, timeout=20)
        resp.raise_for_status()
        result = resp.json()
        
        answer = result.get("answer", "")
        results = result.get("results", [])
        
        if not results:
            return f"❌ Keine Ergebnisse für: {query}"
        
        output = [f"🔍 **Tavily: {query}** ({len(results)} Ergebnisse)\n"]
        
        if answer:
            output.append(f"💡 **Antwort:** {answer}\n")
        
        for i, r in enumerate(results[:max_results], 1):
            title = r.get("title", "?")[:80]
            url = r.get("url", "")
            desc = r.get("content", "")[:150]
            output.append(f"{i}. **{title}**")
            output.append(f"   🔗 {url}")
            if desc:
                output.append(f"   {desc}...")
            output.append("")
        
        result_str = "\n".join(output).strip()
        _record_tool_call("tavily_search", {"query": query, "search_depth": search_depth, "max_results": max_results}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("tavily_search", {"query": query, "search_depth": search_depth, "max_results": max_results}, False, str(e))
        return f"❌ Tavily Suche Fehler: {str(e)}"

@mcp.tool()
def tavily_news(topic: str = "latest news", max_results: int = 10) -> str:
    """Aktuelle Nachrichten mit Tavily AI.
    
    Args:
        topic: Nachrichtenthema (z.B. "AI news", "technology", "sports")
        max_results: Anzahl der Ergebnisse (Standard: 10, max: 20)
    """
    if not TAVILY_API_KEY:
        return "⚠️ Tavily API Key nicht konfiguriert. Setze TAVILY_API_KEY als Umgebungsvariable, in .env-Datei, oder in config.json."
    try:
        import httpx
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        data = {
            "query": topic,
            "search_depth": "basic",
            "max_results": min(max_results, 20),
            "include_answer": False,
            "topic": "news"
        }
        resp = httpx.post("https://api.tavily.com/search", json=data, headers=headers, timeout=20)
        resp.raise_for_status()
        result = resp.json()
        results = result.get("results", [])
        
        if not results:
            return f"❌ Keine Nachrichten für: {topic}"
        
        output = [f"📰 **Tavily News: {topic}** ({len(results)} Artikel)\n"]
        for i, r in enumerate(results[:max_results], 1):
            title = r.get("title", "?")[:80]
            url = r.get("url", "")
            published = r.get("published_date", "")
            output.append(f"{i}. **{title}**")
            if published:
                output.append(f"   📅 {published}")
            output.append(f"   🔗 {url}")
            output.append("")
        
        result_str = "\n".join(output).strip()
        _record_tool_call("tavily_news", {"topic": topic, "max_results": max_results}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("tavily_news", {"topic": topic, "max_results": max_results}, False, str(e))
        return f"❌ Tavily News Fehler: {str(e)}"

@mcp.tool()
def tavily_deep_search(query: str, max_results: int = 20) -> str:
    """Tiefe Websuche mit Tavily (advance search depth).
    
    Args:
        query: Suchbegriff
        max_results: Anzahl der Ergebnisse (Standard: 20, max: 30)
    """
    if not TAVILY_API_KEY:
        return "⚠️ Tavily API Key nicht konfiguriert. Setze TAVILY_API_KEY als Umgebungsvariable, in .env-Datei, oder in config.json."
    try:
        import httpx
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        data = {
            "query": query,
            "search_depth": "advanced",
            "max_results": min(max_results, 30),
            "include_answer": True,
            "include_raw_content": True
        }
        resp = httpx.post("https://api.tavily.com/search", json=data, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        
        answer = result.get("answer", "")
        results = result.get("results", [])
        
        if not results:
            return f"❌ Keine Ergebnisse für: {query}"
        
        output = [f"🔬 **Tavily Deep: {query}** ({len(results)} Ergebnisse)\n"]
        
        if answer:
            output.append(f"💡 **Antwort:** {answer}\n")
        
        for i, r in enumerate(results[:max_results], 1):
            title = r.get("title", "?")[:80]
            url = r.get("url", "")
            score = r.get("score", 0)
            output.append(f"{i}. **{title}** (Relevanz: {score:.2f})")
            output.append(f"   🔗 {url}")
            output.append("")
        
        result_str = "\n".join(output).strip()
        _record_tool_call("tavily_deep_search", {"query": query, "max_results": max_results}, True, result_str[:100])
        return result_str
    except Exception as e:
        _record_tool_call("tavily_deep_search", {"query": query, "max_results": max_results}, False, str(e))
        return f"❌ Tavily Deep Search Fehler: {str(e)}"

@mcp.tool()
def create_diagram(
    diagram_type: str,
    description: str,
    save_to: str = None
) -> str:
    """Generiert Mermaid-Diagramme für Architecture, Workflow, Flowchart, Sequence, Timeline, Prices oder Mindmap.
    
    Args:
        diagram_type: Typ des Diagramms (architecture, workflow, flowchart, sequence, timeline, prices, mindmap)
        description: Was soll visualisiert werden
        save_to: Optionaler Dateipfad zum Speichern
    """
    type_prompts = {
        "architecture": """Generate a Mermaid architecture diagram for: {description}

IMPORTANT RULES:
- Start with 'architecture' keyword (NOT 'archDiagram')
- Use square brackets [Component] for components
- Use --> for connections
- NO semicolons at line ends
- NO JavaScript comments like /* */

Format:
architecture
  direction LR
  [Web UI] --> [API Gateway]
  [API Gateway] --> [Backend]""",
        
        "workflow": """Generate a Mermaid flowchart diagram for the workflow: {description}

IMPORTANT RULES:
- Start with 'flowchart TD' (top-down)
- Use square brackets [Step description] for process nodes
- Use curly brackets {Question} for decision nodes
- Use --> for arrows
- Use --> |label| for labeled paths
- NO semicolons at line ends
- NO JavaScript comments like /* */

Format:
flowchart TD
    A[Start] --> B{Question}
    B --> |yes| C[Process]
    B --> |no| D[Other]""",
        
        "flowchart": """Generate a Mermaid flowchart with decision logic: {description}

IMPORTANT RULES:
- Start with 'flowchart TD' or 'flowchart LR'
- Use {{}} for decision diamonds
- Use --> |yes/no| for branching paths
- NO semicolons at line ends
- NO comments

Format:
flowchart TD
    A --> B{{Is valid?}}
    B --> |yes| C[OK]
    B --> |no| D[Error]""",
        
        "sequence": """Generate a Mermaid sequence diagram: {description}

IMPORTANT RULES:
- Start with 'sequenceDiagram'
- Use 'participant X as Name' for participants
- Use ->> for solid arrows
- Use -->> for dotted arrows
- NO semicolons at line ends

Format:
sequenceDiagram
  participant U as User
  participant J as V.I.N.C.E.N.T.
  U->>J: Request
  J-->>U: Response""",
        
        "timeline": """Generate a Mermaid timeline diagram: {description}

IMPORTANT RULES:
- Start with 'timeline'
- Use 'title' for the title
- Use 'period : event' format
- NO semicolons at line ends

Format:
timeline
  title Project Timeline
  2024-01 : Start
  2024-06 : Milestone""",
        
        "prices": """Generate a Mermaid flowchart for pricing tiers: {description}

IMPORTANT RULES:
- Start with 'flowchart LR'
- Use [Tier $Price] format
- Use --> for progression
- NO semicolons at line ends

Format:
flowchart LR
    A[Basic $10] --> B[Pro $20] --> C[Enterprise $50]""",
        
        "mindmap": """Generate a Mermaid mindmap diagram: {description}
        
IMPORTANT RULES:
- Start with 'mindmap'
- Use 'root' for central idea
- Indent sub-items with spaces
- NO semicolons at line ends

Format:
mindmap
  root((Central Topic))
    Branch 1
      Detail A
      Detail B
    Branch 2""",
        
        "pie": """Generate a Mermaid pie chart: {description}

IMPORTANT RULES:
- Start with 'pie title TITLE'
- Use '"LABEL" : VALUE' format (quotes around labels)
- NO semicolons at line ends
- Values must be numbers

Format:
pie title YouTube Performance
    "Gaming" : 45
    "macOS" : 25
    "Linux" : 30""",
        
        "gantt": """Generate a Mermaid gantt chart for project planning: {description}

IMPORTANT RULES:
- Start with 'gantt'
- Use 'title' for the title
- Use 'section' for sections
- Use 'TASK_NAME : crit, YYYY-MM-DD, Nd' format
- NO semicolons at line ends

Format:
gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
    Task 1 : a1, 2024-01-01, 30d
    section Phase 2
    Task 2 : a2, after a1, 20d""",
        
        "state": """Generate a Mermaid state diagram: {description}

IMPORTANT RULES:
- Start with 'stateDiagram-v2'
- Use '[*] --> StateName' for start
- Use 'StateName --> [*]' for end
- NO semicolons at line ends

Format:
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : Start
    Processing --> Success : OK
    Processing --> Error : Fail
    Success --> [*]
    Error --> Idle : Retry""",
        
        "journey": """Generate a Mermaid user journey: {description}

IMPORTANT RULES:
- Start with 'journey'
- Use 'title' for the title
- Use 'section SectionName' for sections
- Use 'Task : N : Person' format (N = score 1-5)
- NO semicolons at line ends

Format:
journey
    title User Journey
    section Visit
      Page Load : 5 : User
      Browse : 4 : User
    section Buy
      Add to Cart : 3 : User
      Checkout : 2 : User""",
        
        "git": """Generate a Mermaid git graph: {description}

IMPORTANT RULES:
- Start with 'gitGraph'
- Use 'commit' for commits
- Use 'branch BRANCH_NAME' for branches
- NO semicolons at line ends

Format:
gitGraph
    commit
    branch develop
    checkout develop
    commit
    checkout main
    merge develop"""
    }
    
    # Predefined diagrams for common use cases
    predefined = {
        "weather": """flowchart TD
    A[User: Wetter für Ort?] --> B[NLP analysiert Anfrage]
    B --> C{Ort bekannt?}
    C -- Nein --> D[Nachfrage: Welcher Ort?]
    D --> A
    C -- Ja --> E[API: Wetter aufrufen]
    E --> F[Daten empfangen]
    F --> G[Antwort formatieren]
    G --> H[User: Ergebnis zeigen]
    H --> I[Ende]""",
        
        "jarvis": """flowchart TD
    A[User Anfrage] --> B[V.I.N.C.E.N.T. empfängt]
    B --> C[NLP/Intent erkannt]
    C --> D{Tool benötigt?}
    D -- Nein --> E[Direkte Antwort]
    D -- Ja --> F[Tool aufrufen]
    F --> G[Ergebnis verarbeiten]
    G --> H[Antwort formatieren]
    H --> I[User: Ergebnis]
    I --> J[Ende]"""
    }
    
    diagram_type = diagram_type.lower().strip()
    desc_lower = description.lower()
    
    # Check for predefined diagrams or keywords
    if "weather" in desc_lower or "wetter" in desc_lower:
        mermaid_code = predefined.get("weather", "")
    elif "jarvis" in desc_lower and ("architektur" in desc_lower or "system" in desc_lower):
        mermaid_code = predefined.get("jarvis", "")
    elif diagram_type not in type_prompts:
        available = ", ".join(type_prompts.keys())
        return f"❌ Unbekannter Diagramm-Typ: {diagram_type}\nVerfügbare Typen: {available}"
    else:
        prompt = type_prompts[diagram_type].format(description=description)
        try:
            resp = requests.post("http://127.0.0.1:8080/v1/chat/completions", json={
                "model": "model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1024
            }, timeout=120)
            resp.raise_for_status()
            mermaid_code = resp.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.ConnectionError:
            return "❌ Diagramm-Fehler: llama-server läuft nicht auf 127.0.0.1:8080. Bitte zuerst ein Modell laden."
        except Exception as e:
            return f"❌ Diagramm-Fehler: {str(e)}"
    
    # Clean up common syntax errors
    mermaid_code = mermaid_code.strip()
    if mermaid_code.startswith("```mermaid"):
        mermaid_code = mermaid_code[9:]
    if mermaid_code.startswith("```"):
        mermaid_code = mermaid_code[3:]
    if mermaid_code.endswith("```"):
        mermaid_code = mermaid_code[:-3]
    
    # Fix common errors: remove semicolons, fix comments
    lines = mermaid_code.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.rstrip()
        line = line.rstrip(';')
        line = line.rstrip(',')
        if '/*' in line or '*/' in line:
            line = line.replace('/*', '%%').replace('*/', '')
        cleaned_lines.append(line)
    mermaid_code = '\n'.join(cleaned_lines).strip()
    
    if save_to:
        import os
        os.makedirs(os.path.dirname(save_to) if os.path.dirname(save_to) else ".", exist_ok=True)
        with open(save_to, "w", encoding="utf-8") as f:
            f.write(f"```mermaid\n{mermaid_code}\n```\n")
        return f"✅ Diagramm gespeichert: {save_to}\n\n```mermaid\n{mermaid_code}\n```"
    
    return f"```mermaid\n{mermaid_code}\n```"

# ========== HYPERFRAMES TOOLS ==========

_SAFE_COMMANDS = ["npx hyperframes", "npx skills", "npx --yes hyperframes", "npx --yes skills", "ffmpeg", "node", "npm", "pip", "python3", "python", "ls", "cat", "mkdir", "rm"]

@mcp.tool()
def run_command(
    command: str,
    workdir: str = None,
    timeout: int = 120
) -> str:
    """Führt ein erlaubtes Kommando aus (Whitelist: npx, ffmpeg, node, npm, pip, python3, ls, cat, mkdir, rm).
    
    Args:
        command: Das auszuführende Kommando (z.B. 'npx hyperframes init', 'pip install sentence-transformers')
        workdir: Arbeitsverzeichnis (Standard: aktuelles Verzeichnis)
        timeout: Timeout in Sekunden (Standard: 120)
    """
    cmd_str = command.strip()
    allowed = any(cmd_str.startswith(prefix) for prefix in _SAFE_COMMANDS)
    if not allowed:
        return f"❌ Kommando nicht erlaubt. Erlaubte Prefixe: {', '.join(_SAFE_COMMANDS)}"
    
    try:
        cwd = os.path.abspath(workdir) if workdir else _get_allowed_paths()[0]
        if workdir and not is_path_allowed(cwd):
            return f"❌ Zugriff verweigert: {cwd} ist nicht in den erlaubten Pfaden"
        run_env = os.environ.copy()
        run_env["npm_config_yes"] = "true"
        run_env["PIP_REQUIRE_VIRTUALENV"] = "0"
        r = subprocess.run(
            cmd_str.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=run_env
        )
        out = r.stdout[:2000]
        err = r.stderr[:1000]
        result = f"✅ Exit-Code: {r.returncode}\n"
        if out:
            result += f"\n--- STDOUT ---\n{out}\n"
        if err:
            result += f"\n--- STDERR ---\n{err}\n"
        if not out and not err:
            result += "(keine Ausgabe)"
        return result
    except subprocess.TimeoutExpired:
        return f"❌ Timeout ({timeout}s) – Kommando abgebrochen: {cmd_str}"
    except Exception as e:
        return f"❌ Fehler: {str(e)}"


# ========== RESOURCES ==========

@mcp.resource("vincent://status")
def vincent_status_resource() -> str:
    """Gibt V.I.N.C.E.N.T.-Status als Resource zurück."""
    return vincent_status()

@mcp.resource("vincent://tools")
def vincent_tools_resource() -> str:
    """Liste aller verfügbaren Tools."""
    tools = [
        {"name": "read_file", "description": "Liest eine Datei", "icon": "📄", "category": "file"},
        {"name": "write_file", "description": "Schreibt eine Datei", "icon": "✍️", "category": "file"},
        {"name": "append_to_file", "description": "Hängt Text an Datei an", "icon": "📎", "category": "file"},
        {"name": "list_directory", "description": "Listet Verzeichnisinhalt", "icon": "📁", "category": "file"},
        {"name": "search_files", "description": "Durchsucht Dateien", "icon": "🔍", "category": "file"},
        {"name": "get_file_info", "description": "Dateiinformationen", "icon": "ℹ️", "category": "file"},
        {"name": "create_directory", "description": "Erstellt Verzeichnis", "icon": "📂", "category": "file"},
        {"name": "delete_file", "description": "Löscht Datei/Verzeichnis", "icon": "🗑️", "category": "file"},
        {"name": "analyze_project", "description": "Analysiert Projekt-Struktur", "icon": "🔬", "category": "system"},
        {"name": "patch_file", "description": "Ändert Code-Stellen gezielt", "icon": "🧵", "category": "file"},
        {"name": "scan_folder", "description": "Scannt Verzeichnis rekursiv", "icon": "🔭", "category": "file"},
        {"name": "add_project_to_rag", "description": "Projekt zu RAG hinzufügen", "icon": "📥", "category": "system"},
        {"name": "clear_project_rag", "description": "Projekt-RAG löschen", "icon": "🧹", "category": "system"},
        {"name": "create_diagram", "description": "Generiert Mermaid-Diagramme", "icon": "📊", "category": "util"},
        {"name": "web_scrape", "description": "Scraped Webseite mit crawl4ai (1 Seite)", "icon": "🕷️", "category": "web"},
        {"name": "deep_scrape", "description": "Deep Crawl (mehrere Seiten)", "icon": "🕸️", "category": "web"},
        {"name": "browser_open", "description": "URL im Browser öffnen", "icon": "🌍", "category": "web"},
        {"name": "browser_snapshot", "description": "Seiten-Inhalt lesen", "icon": "📸", "category": "web"},
        {"name": "structured_snapshot", "description": "Strukturierte Clickable Elements", "icon": "🖱️", "category": "web"},
        {"name": "auto_click", "description": "Click mit Self-Healing", "icon": "👆", "category": "web"},
        {"name": "browser_click", "description": "Element klicken", "icon": "🔲", "category": "web"},
        {"name": "browser_type", "description": "Text eingeben", "icon": "⌨️", "category": "web"},
        {"name": "browser_screenshot", "description": "Screenshot machen", "icon": "📷", "category": "web"},
{"name": "browser_navigate", "description": "Navigieren", "icon": "➡️", "category": "web"},
        {"name": "browser_new_tab", "description": "Öffnet neuen Tab", "icon": "🗎", "category": "web"},
        {"name": "browser_switch_tab", "description": "Wechselt Tab", "icon": "🔀", "category": "web"},
        {"name": "browser_close_tab", "description": "Schließt Tab", "icon": "❌", "category": "web"},
        {"name": "browser_list_tabs", "description": "Listet Tabs auf", "icon": "🗋", "category": "web"},
        {"name": "browser_wait_for", "description": "Wartet auf Element", "icon": "⏳", "category": "web"},
        {"name": "browser_wait_for_load", "description": "Wartet auf Laden", "icon": "⏱️", "category": "web"},
        {"name": "save_memory", "description": "Fakt speichern", "icon": "💾", "category": "memory"},
        {"name": "list_memory", "description": "Gedächtnis auflisten", "icon": "📋", "category": "memory"},
        {"name": "delete_memory", "description": "Gedächtnis löschen", "icon": "🗑️", "category": "memory"},
        {"name": "search_memory", "description": "Erinnerungen durchsuchen", "icon": "🔎", "category": "memory"},
        {"name": "list_skills", "description": "Selbstgelernte Skills anzeigen", "icon": "🧠", "category": "system"},
        {"name": "learn_skill", "description": "Skill manuell trainieren", "icon": "🎓", "category": "system"},
        {"name": "use_skill", "description": "Skill per Keyword ausführen", "icon": "⚡", "category": "system"},
        {"name": "show_tool_usage", "description": "Tool-Nutzung anzeigen", "icon": "📈", "category": "system"},
        {"name": "run_python", "description": "Führt Python-Code aus", "icon": "🐍", "category": "util"},
        {"name": "vincent_status", "description": "V.I.N.C.E.N.T. Status", "icon": "🤖", "category": "system"},
        {"name": "youtube_trending", "description": "YouTube Trends", "icon": "▶️", "category": "trends"},
        {"name": "github_trending", "description": "GitHub Trends", "icon": "🐙", "category": "trends"},
        {"name": "hackernews_trending", "description": "Hacker News", "icon": "💻", "category": "trends"},
        {"name": "google_trends", "description": "Google Trends", "icon": "📊", "category": "trends"},
        {"name": "reddit_trending", "description": "Reddit Trends", "icon": "🔴", "category": "trends"},
        {"name": "weather", "description": "Wetter für Ort", "icon": "🌤️", "category": "info"},
        {"name": "imdb_search", "description": "Filme suchen", "icon": "🎥", "category": "info"},
        {"name": "news_headlines", "description": "Nachrichten (DuckDuckGo)", "icon": "📰", "category": "trends"},
        {"name": "duckduckgo_search", "description": "Websuche mit DuckDuckGo", "icon": "🦆", "category": "search"},
        {"name": "duckduckgo_images", "description": "Bildsuche mit DuckDuckGo", "icon": "🖼️", "category": "search"},
        {"name": "tavily_search", "description": "Websuche mit Tavily AI", "icon": "🔎", "category": "search"},
        {"name": "tavily_news", "description": "Nachrichten mit Tavily AI", "icon": "📰", "category": "trends"},
        {"name": "tavily_deep_search", "description": "Tiefe Suche mit Tavily", "icon": "🔍", "category": "search"},
        {"name": "browser_search_products", "description": "Amazon Produktsuche", "icon": "🛒", "category": "search"},
    ]
    if not TAVILY_API_KEY:
        tools = [t for t in tools if not t["name"].startswith("tavily_")]
    return json.dumps(tools, indent=2)

# ========== MAIN ==========

if __name__ == "__main__":
    print("🚀 Starte V.I.N.C.E.N.T. MCP Server...")
    print(f"📁 Arbeitsverzeichnis: {JARVIS_DIR}")
    print("🔧 Verfügbare Tools: read_file, write_file, list_directory, search_files, ...")
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ config.json nicht gefunden unter: {CONFIG_PATH}")
        print("   ℹ️  Kopiere config.example.json nach config.json und passe die Pfade an.")
        sys.exit(1)
    cfg = _load_config()
    mcp_port = cfg.get("mcp_port", 8000)
    print(f"🌐 Server läuft auf: http://127.0.0.1:{mcp_port}/mcp")
    print("\nDrücke Ctrl+C zum Beenden\n")
    
    # Server starten mit h11 + CORS + stateless session mode
    import anyio
    from starlette.middleware.cors import CORSMiddleware

    mcp.settings.stateless_http = True
    mcp.settings.json_response = True
    mcp.settings.port = mcp_port

    async def run_with_h11():
        import uvicorn
        app = mcp.streamable_http_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        config = uvicorn.Config(app, host=mcp.settings.host, port=mcp.settings.port,
                                http="h11", log_level=mcp.settings.log_level.lower(),
                                h11_max_incomplete_event_size=10*1024*1024)
        await uvicorn.Server(config).serve()

    anyio.run(run_with_h11)
