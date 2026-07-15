#!/usr/bin/env python3
"""Subprocess-based browser for Jarvis MCP server."""
import sys
import os

# Add venv to path
base_dir = os.path.dirname(os.path.abspath(__file__))
venv_lib = os.path.join(base_dir, "venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
sys.path.insert(0, venv_lib)

import json
from playwright.sync_api import sync_playwright

_browser = None
_context = None
_pages = []      # List of all open pages/tabs
_current_tab = 0  # Index of current tab
_pw = None

def _ensure_browser():
    """Ensure browser and context are initialized."""
    global _browser, _context, _pw
    
    if _pw is None:
        _pw = sync_playwright().start()
    
    if _browser is None:
        _browser = _pw.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    
    if _context is None:
        _context = _browser.new_context()
    
    return _context

def _get_current_page():
    """Get the current page/tab."""
    global _pages, _current_tab
    if not _pages:
        return None
    return _pages[_current_tab] if _current_tab < len(_pages) else None

def _ensure_url(url):
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def cmd_open(url):
    global _pages, _current_tab
    
    ctx = _ensure_browser()
    
    url = _ensure_url(url)
    
    # Create new page
    page = ctx.new_page()
    page.set_default_timeout(30000)
    page.goto(url, timeout=30000)
    page.wait_for_load_state("domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)
    
    # Scroll to load dynamic content
    page.evaluate("""() => {
        window.scrollTo(0, document.body.scrollHeight);
    }""")
    page.wait_for_timeout(2000)
    
    # Add to pages list
    _pages.append(page)
    _current_tab = len(_pages) - 1
    
    title = page.title()
    content = page.content()[:200000]
    return {"status": "ok", "title": title, "content": content, "tab_index": _current_tab}

def cmd_new_tab(url=''):
    global _pages, _current_tab
    
    ctx = _ensure_browser()
    
    page = ctx.new_page()
    page.set_default_timeout(30000)
    
    if url:
        url = _ensure_url(url)
        page.goto(url, timeout=30000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)
    
    _pages.append(page)
    _current_tab = len(_pages) - 1
    
    title = page.title()
    return {"status": "ok", "tab_index": _current_tab, "total_tabs": len(_pages), "title": title}

def cmd_switch_tab(index):
    global _current_tab
    
    idx = int(index)
    if 0 <= idx < len(_pages):
        _current_tab = idx
        try:
            title = _pages[_current_tab].title()
            url = _pages[_current_tab].url
            return {"status": "ok", "current_tab": _current_tab, "title": title, "url": url}
        except:
            return {"status": "ok", "current_tab": _current_tab}
    
    return {"status": "error", "message": f"Invalid tab index: {index}"}

def cmd_close_tab(index=None):
    global _pages, _current_tab
    
    idx = int(index) if index is not None else _current_tab
    
    if 0 <= idx < len(_pages):
        try:
            _pages[idx].close()
        except:
            pass
        
        _pages.pop(idx)
        
        # Adjust current tab
        if _current_tab >= len(_pages):
            _current_tab = max(0, len(_pages) - 1)
        
        return {"status": "ok", "remaining_tabs": len(_pages), "current_tab": _current_tab}
    
    return {"status": "error", "message": "No tab to close"}

def cmd_list_tabs():
    global _pages, _current_tab
    
    tabs = []
    for i, page in enumerate(_pages):
        try:
            tabs.append({
                "index": i,
                "title": page.title(),
                "url": page.url,
                "current": i == _current_tab
            })
        except:
            tabs.append({
                "index": i,
                "title": "Unknown",
                "url": "Unknown",
                "current": i == _current_tab
            })
    
    return {"status": "ok", "tabs": tabs, "current": _current_tab}

def cmd_type(selector, text):
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    try:
        page.fill(selector, text)
        page.wait_for_timeout(1000)
        return {"status": "ok", "message": f"Getippt: {text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def cmd_click(text):
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    try:
        page.click(f"text={text}", timeout=3000)
        page.wait_for_timeout(2000)
        return {"status": "ok", "message": f"Geklickt: {text}"}
    except:
        pass
    
    try:
        page.keyboard.press('Enter')
        page.wait_for_timeout(2000)
        return {"status": "ok", "message": "Enter gedrueckt"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def cmd_snapshot():
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    page.wait_for_timeout(2000)
    
    # Get full rendered HTML by scrolling
    page.evaluate("""() => {
        window.scrollTo(0, 0);
        setTimeout(() => {
            window.scrollTo(0, document.body.scrollHeight);
        }, 1000);
    }""")
    page.wait_for_timeout(3000)
    
    return {"status": "ok", "content": page.content()[:200000]}

def cmd_structured():
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    links = page.query_selector_all("a[href]")
    buttons = page.query_selector_all("button")
    inputs = page.query_selector_all("input")
    
    elements = []
    ref = 1
    
    for link in links[:30]:
        try:
            text = link.inner_text().strip()[:50]
            href = link.get_attribute("href") or ""
            if text and href:
                elements.append(f"[{ref}] LINK: {text} -> {href}")
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
    
    return {"status": "ok", "elements": elements[:30] if elements else []}

def cmd_screenshot(path):
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    page.screenshot(path=path)
    return {"status": "ok", "path": path}

def cmd_navigate(url, action="goto"):
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    if action == "back":
        page.go_back()
        return {"status": "ok", "message": "Zurück"}
    elif action == "forward":
        page.go_forward()
        return {"status": "ok", "message": "Vorwärts"}
    else:
        url = _ensure_url(url)
        page.goto(url, timeout=30000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)
        
        # Scroll to load dynamic content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        return {"status": "ok", "url": url}

def cmd_wait_for(selector, timeout=5000):
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    try:
        page.wait_for_selector(selector, timeout=int(timeout))
        return {"status": "ok", "message": f"Element {selector} gefunden"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def cmd_wait_for_load(timeout=30000):
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    try:
        page.wait_for_load_state("domcontentloaded", timeout=int(timeout))
        return {"status": "ok", "message": "Seite geladen"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def cmd_search_products(query, limit=10):
    """Use query_selector_all for product elements."""
    page = _get_current_page()
    
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    
    search_url = f"https://www.amazon.de/s?k={query.replace(' ', '+')}"
    page.goto(search_url, timeout=30000)
    page.wait_for_load_state("domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)
    
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    
    products = []
    
    # Try different selectors for product elements
    selectors = [
        "[data-component-type='s-search-result']",
        ".s-result-item",
        "div[data-asin]"
    ]
    
    for sel in selectors:
        items = page.query_selector_all(sel)
        if items:
            for item in items[:limit]:
                try:
                    # Try to get title from h2
                    h2 = item.query_selector("h2 a")
                    name = h2.inner_text().strip() if h2 else ""
                    
                    # Try to get URL from anchor
                    url = ""
                    if h2:
                        url = h2.get_attribute("href")
                        if url and not url.startswith("http"):
                            url = "https://www.amazon.de" + url
                    
                    # Try to get price
                    price_elem = item.query_selector(".a-price-whole")
                    price = price_elem.inner_text().strip() if price_elem else "?"
                    
                    if name and len(name) > 3:
                        products.append({"name": name[:80], "price": price, "url": url})
                except:
                    pass
            
            if products:
                break
    
    if not products:
        # Fallback: just get any price and use as placeholder
        prices = page.query_selector_all(".a-price-whole")
        for i, p in enumerate(prices[:limit]):
            try:
                price = p.inner_text().strip().replace('\n', '')
                if price:
                    products.append({"name": f"Ergebnis {i+1}", "price": price})
            except:
                pass
    
    return {"status": "ok", "products": products[:limit], "query": query, "total_tabs": len(_pages)}

def cmd_title():
    page = _get_current_page()
    if page is None:
        return {"status": "error", "message": "Bitte zuerst browser_open aufrufen"}
    return {"status": "ok", "title": page.title()}

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            cmd = json.loads(line.strip())
            
            action = cmd.get("action")
            args = cmd.get("args", {})
            
            if action == "open":
                result = cmd_open(args.get("url"))
            elif action == "new_tab":
                result = cmd_new_tab(args.get("url", ""))
            elif action == "switch_tab":
                result = cmd_switch_tab(args.get("index"))
            elif action == "close_tab":
                result = cmd_close_tab(args.get("index"))
            elif action == "list_tabs":
                result = cmd_list_tabs()
            elif action == "type":
                result = cmd_type(args.get("selector"), args.get("text"))
            elif action == "click":
                result = cmd_click(args.get("text"))
            elif action == "snapshot":
                result = cmd_snapshot()
            elif action == "structured":
                result = cmd_structured()
            elif action == "screenshot":
                result = cmd_screenshot(args.get("path"))
            elif action == "navigate":
                result = cmd_navigate(args.get("url"), args.get("action", "goto"))
            elif action == "wait_for":
                result = cmd_wait_for(args.get("selector"), args.get("timeout", 5000))
            elif action == "wait_for_load":
                result = cmd_wait_for_load(args.get("timeout", 30000))
            elif action == "search_products":
                result = cmd_search_products(args.get("query"), args.get("limit", 10))
            elif action == "title":
                result = cmd_title()
            elif action == "quit":
                break
            else:
                result = {"status": "error", "message": f"Unknown action: {action}"}
            
            print(json.dumps(result), flush=True)
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}), flush=True)

if __name__ == "__main__":
    main()
