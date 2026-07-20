#!/usr/bin/env python3
"""
bagueDEV_Launcher — startet llama-server mit Web-UI + Chat
Nutzung: python3 bagueDEV_Launcher.py
Entwickelt bei bagueDev
  GitHub: https://github.com/bagueDev
  YouTube: https://youtube.com/@bagueDev
"""

import http.server
import json
import os
import shlex
import subprocess
import threading
import webbrowser
from pathlib import Path

# ── Konfiguration aus config.json ────────────────────────────
LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(LAUNCHER_DIR, "config.json")

def _load_config():
    defaults = {
        "llama_server": os.path.join(LAUNCHER_DIR, "llama-server"),
        "llama_cpp_dir": os.path.join(LAUNCHER_DIR, "llama.cpp"),
        "models_dir": os.path.join(LAUNCHER_DIR, "models"),
        "launcher_port": 9999,
        "server_port": 8080,
    }
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
            defaults.update(cfg)
    except FileNotFoundError:
        print(f"❌ config.json nicht gefunden unter: {CONFIG_PATH}")
        print("   ℹ️  Kopiere config.example.json nach config.json und passe die Pfade an.")
        sys.exit(1)
    except:
        pass
    return defaults

_cfg = _load_config()
LLAMA_CPP_DIR = _cfg["llama_cpp_dir"]
LLAMA_SERVER = _cfg["llama_server"]
DEFAULT_MODELS = _cfg["models_dir"]
LAUNCHER_PORT = _cfg["launcher_port"]
SERVER_PORT = _cfg["server_port"]
# ──────────────────────────────────────────────────────────────

server_process = None
# Session-Verzeichnisliste (nur im Speicher)
models_dirs = [DEFAULT_MODELS]

HTML_LAUNCHER = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>bagueDev Community Launcher</title>

<style>
  :root {
    --bg:#0a0a0f;--surface:#111118;--border:#1e1e2e;
    --accent:#ff6b35;--accent2:#e040fb;--text:#e8e8f0;
    --muted:#555570;--green:#00e5a0;
    --mono: monospace;--sans: sans-serif;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{background:var(--bg);color:var(--text);font-family:var(--mono);
       min-height:100vh;display:flex;flex-direction:column;align-items:center;
       padding:40px 20px;}
  h1{font-family:var(--sans);font-size:1.6rem;font-weight:800;
     color:var(--accent);margin-bottom:4px;letter-spacing:-0.02em;}
  h1 span{color:var(--text);}
  .sub{font-size:0.7rem;color:var(--muted);margin-bottom:32px;letter-spacing:0.08em;text-transform:uppercase;}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:10px;
        padding:24px;width:100%;max-width:640px;margin-bottom:16px;}
  .section-title{font-size:0.65rem;text-transform:uppercase;letter-spacing:0.12em;
                 color:var(--muted);margin-bottom:12px;}

  /* Verzeichnis-Manager */
  .dir-list{display:flex;flex-direction:column;gap:6px;margin-bottom:10px;}
  .dir-item{display:flex;align-items:center;gap:8px;padding:7px 10px;
            border-radius:5px;border:1px solid var(--border);background:var(--bg);}
  .dir-path{font-size:0.72rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);}
  .dir-remove{background:transparent;border:none;color:var(--muted);cursor:pointer;
              font-size:0.9rem;padding:0 4px;height:auto;min-width:0;
              transition:color .15s;}
  .dir-remove:hover{color:var(--accent);}
  .dir-add-row{display:flex;gap:6px;}
  .dir-input{flex:1;background:var(--bg);border:1px solid var(--border);border-radius:4px;
             color:var(--text);font-family:var(--mono);font-size:0.75rem;
             padding:7px 10px;outline:none;transition:border-color .2s;}
  .dir-input:focus{border-color:var(--accent);}
  .dir-input::placeholder{color:var(--muted);}
  .btn-add{background:var(--accent);color:#000;border:none;border-radius:4px;
           padding:7px 14px;font-family:var(--sans);font-weight:700;font-size:0.75rem;
           cursor:pointer;white-space:nowrap;height:auto;letter-spacing:.03em;}
  .btn-add:hover{opacity:.85;}

  .model-list{display:flex;flex-direction:column;gap:6px;max-height:260px;overflow-y:auto;
              scrollbar-width:thin;scrollbar-color:var(--border) transparent;}
  .model-item{display:flex;align-items:center;gap:10px;padding:10px 12px;
              border-radius:6px;border:1px solid var(--border);cursor:pointer;
              transition:border-color .15s,background .15s;}
  .model-item:hover{background:var(--border);}
  .model-item.selected{border-color:var(--accent);background:rgba(255,107,53,.08);}
  .model-name{font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .model-dir{font-size:0.6rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .model-size{font-size:0.65rem;color:var(--muted);flex-shrink:0;}

  .options{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px;}
  .opt-group{display:flex;flex-direction:column;gap:4px;}
  .opt-label{font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;}
  .opt-input{background:var(--bg);border:1px solid var(--border);border-radius:4px;
             color:var(--text);font-family:var(--mono);font-size:0.8rem;
             padding:7px 10px;outline:none;transition:border-color .2s;}
  .opt-input:focus{border-color:var(--accent);}
  .btn-row{display:flex;gap:8px;margin-top:16px;}
  button{border:none;border-radius:7px;padding:10px 20px;font-family:var(--sans);
         font-weight:700;font-size:0.8rem;cursor:pointer;
         transition:opacity .2s,transform .1s;letter-spacing:.03em;}
  button:active{transform:scale(.97);}
  button:disabled{opacity:.3;cursor:not-allowed;}
  .btn-start{background:var(--green);color:#000;flex:1;}
  .btn-stop{background:var(--accent);color:#000;}
  .btn-chat{background:var(--accent2);color:#000;}
  .btn-llama{background:#60a5fa;color:#000;}
  .btn-reload{background:transparent;color:var(--muted);border:1px solid var(--border);
              font-family:var(--mono);font-weight:400;font-size:0.75rem;}
  .status-bar{display:flex;align-items:center;gap:10px;padding:12px 16px;
              background:var(--bg);border:1px solid var(--border);border-radius:7px;
              margin-top:4px;}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--muted);flex-shrink:0;transition:background .3s;}
  .dot.running{background:var(--green);box-shadow:0 0 8px var(--green);}
  .dot.error{background:var(--accent);box-shadow:0 0 8px var(--accent);}
  .status-txt{font-size:0.75rem;color:var(--muted);flex:1;}
  .status-txt.running{color:var(--green);}
  .status-txt.error{color:var(--accent);}
  .log{background:var(--bg);border:1px solid var(--border);border-radius:6px;
       padding:12px;font-size:0.7rem;line-height:1.7;color:var(--muted);
       max-height:160px;overflow-y:auto;white-space:pre-wrap;word-break:break-all;
       scrollbar-width:thin;scrollbar-color:var(--border) transparent;margin-top:8px;}
  .cmd-preview{font-size:0.68rem;color:var(--muted);background:var(--bg);
               border:1px solid var(--border);border-radius:6px;padding:10px 12px;
               margin-top:10px;white-space:pre-wrap;word-break:break-all;line-height:1.6;}
  .cmd-preview span{color:var(--accent2);}
  .no-models{text-align:center;padding:20px;color:var(--muted);font-size:0.8rem;}
  .dev-notes-bar{display:flex;align-items:center;justify-content:center;gap:8px;padding:16px 0 4px;font-size:0.7rem;color:var(--muted);}
  .dev-notes-bar a{display:inline-flex;align-items:center;gap:5px;color:var(--muted);text-decoration:none;transition:color .15s;}
  .dev-notes-bar a:hover{color:var(--accent2);}
  .dev-sep{color:var(--border);}
  .btn-about{background:transparent;color:var(--muted);border:1px solid var(--border);border-radius:6px;padding:4px 10px;font-family:var(--mono);font-size:.72rem;cursor:pointer;transition:color .2s,border-color .2s;flex-shrink:0;height:30px;}
  .btn-about:hover{color:var(--text);border-color:var(--muted);}
  .overlay{display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.6);backdrop-filter:blur(2px);align-items:center;justify-content:center;}
  .overlay.show{display:flex;}
  .modal{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px 32px;max-width:420px;width:90%;max-height:80vh;overflow-y:auto;position:relative;animation:fadeUp .2s ease;}
  .modal-close{position:absolute;top:12px;right:16px;background:none;border:none;color:var(--muted);font-size:1.2rem;cursor:pointer;padding:4px;line-height:1;}
  .modal-close:hover{color:var(--text);}
  .modal-title{font-family:var(--sans);font-weight:800;font-size:1.1rem;color:var(--accent);margin-bottom:4px;}
  .modal-sub{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;margin-bottom:16px;}
  .modal-section{font-size:.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-top:16px;margin-bottom:8px;}
  .modal-links{display:flex;gap:16px;margin-bottom:12px;}
  .modal-links a{color:var(--muted);text-decoration:none;font-size:.75rem;display:inline-flex;align-items:center;gap:5px;transition:color .15s;}
  .modal-links a:hover{color:var(--accent2);}
  .modal-grid{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;font-size:.72rem;line-height:1.8;}
  .modal-grid .cat{color:var(--muted);white-space:nowrap;}
  .modal-grid .val{color:var(--text);}
</style>
</head>
<body>
<div style="display:flex;align-items:flex-start;gap:16px;width:100%;max-width:640px;">
  <div style="flex:1;">
    <h1>bagueDev Community Launcher</h1>
    <div class="sub">llama.cpp · Vulkan · 🐧 Linux Edition</div>
  </div>
  <button class="btn-about" onclick="showAbout()" title="About">ℹ</button>
</div>

<!-- VERZEICHNISSE -->
<div class="card">
  <div class="section-title">Modell-Verzeichnisse</div>
  <div class="dir-list" id="dirList"></div>
  <div class="dir-add-row">
    <input class="dir-input" id="dirInput" placeholder="/Pfad/zu/gguf/Ordner" />
    <button class="btn-add" onclick="addDir()">+ Hinzufügen</button>
  </div>
</div>

<!-- MODELL PICKER -->
<div class="card">
  <div class="section-title">Modell wählen</div>
  <div class="model-list" id="modelList">
    <div class="no-models">Lade Modelle...</div>
  </div>
  <div class="options">
    <div class="opt-group">
      <div class="opt-label">Kontext</div>
      <input class="opt-input" id="ctxSize" value="4096" type="number" step="512">
    </div>
    <div class="opt-group">
      <div class="opt-label">GPU Layers</div>
      <input class="opt-input" id="ngl" value="99" type="number">
    </div>
    <div class="opt-group">
      <div class="opt-label">Port</div>
      <input class="opt-input" id="port" value="8080" type="number">
    </div>
    <div class="opt-group">
      <div class="opt-label">Threads</div>
      <input class="opt-input" id="threads" value="6" type="number">
    </div>
    <div class="opt-group">
      <div class="opt-label">Cache K</div>
      <select class="opt-input" id="cacheTypeK" style="cursor:pointer;">
        <option value="q4_0">q4_0</option>
        <option value="q5_0">q5_0</option>
        <option value="q8_0">q8_0</option>
        <option value="f16">f16</option>
      </select>
    </div>
    <div class="opt-group">
      <div class="opt-label">Cache V</div>
      <select class="opt-input" id="cacheTypeV" style="cursor:pointer;">
        <option value="q4_0" selected>q4_0</option>
        <option value="q5_0">q5_0</option>
        <option value="q8_0">q8_0</option>
        <option value="f16">f16</option>
      </select>
    </div>
    <div class="opt-group">
      <div class="opt-label">Batch</div>
      <input class="opt-input" id="batchSize" value="512" type="number" step="32">
    </div>
    <div class="opt-group">
      <div class="opt-label">U-Batch</div>
      <input class="opt-input" id="ubatchSize" value="64" type="number" step="8">
    </div>
    <div class="opt-group">
      <div class="opt-label">Max Tokens</div>
      <input class="opt-input" id="maxTokens" value="2048" type="number" step="512">
    </div>
    <div class="opt-group" style="flex-direction:row;align-items:center;gap:8px;padding-top:14px;">
      <input type="checkbox" id="flashAttn" checked style="width:16px;height:16px;cursor:pointer;">
      <span style="font-size:0.7rem;color:var(--muted);">Flash Attn</span>
    </div>
    <div class="opt-group" style="flex-direction:row;align-items:center;gap:8px;padding-top:14px;">
      <input type="checkbox" id="mcpProxy" style="width:16px;height:16px;cursor:pointer;">
      <span style="font-size:0.7rem;color:var(--muted);">MCP Proxy</span>
    </div>
    <div class="opt-group" style="flex-direction:row;align-items:center;gap:8px;padding-top:14px;">
      <input type="checkbox" id="useJinja" checked style="width:16px;height:16px;cursor:pointer;">
      <span style="font-size:0.7rem;color:var(--muted);">Jinja</span>
    </div>
    <div class="opt-group" style="flex-direction:row;align-items:center;gap:8px;padding-top:14px;">
      <input type="radio" name="chatTemplate" id="ctDefault" value="" checked style="width:16px;height:16px;cursor:pointer;">
      <span style="font-size:0.7rem;color:var(--muted);">Default</span>
      <input type="radio" name="chatTemplate" id="ctQwen" value="qwen" style="width:16px;height:16px;cursor:pointer;margin-left:4px;">
      <span style="font-size:0.7rem;color:var(--muted);">Qwen CLI FIX</span>
      <input type="radio" name="chatTemplate" id="ctGemma" value="gemma" style="width:16px;height:16px;cursor:pointer;margin-left:4px;">
      <span style="font-size:0.7rem;color:var(--muted);">Gemma CLI FIX</span>
    </div>
    <div class="opt-group" style="flex-direction:row;align-items:center;gap:8px;padding-top:14px;">
      <input type="checkbox" id="mtp" style="width:16px;height:16px;cursor:pointer;">
      <span style="font-size:0.7rem;color:var(--muted);">MTP</span>
      <input class="opt-input" id="specDraftNMax" value="4" type="number" min="1" max="16" style="width:50px;padding:4px 6px;">
    </div>
    <div class="opt-group" style="grid-column:1/-1;">
      <div class="opt-label">Draft Model (optional)</div>
      <input class="opt-input" id="modelDraft" placeholder="/pfad/zu/mtp-head.gguf – leer lassen für Self-Speculative">
    </div>
    <div class="opt-group" style="grid-column:1/-1;margin-top:8px;">
      <div class="opt-label">Sampling</div>
      <select id="samplingPreset" style="width:100%;padding:6px 8px;border-radius:6px;border:1px solid #333;background:#161618;color:#e4e4e7;font-size:.8rem;">
        <option value="default">Default (llama.cpp-Standard)</option>
        <option value="chat">Chat/Agent</option>
        <option value="creative">Creative</option>
        <option value="code">Code/Precise</option>
        <option value="custom">Custom</option>
      </select>
    </div>
    <div id="samplingCustom" style="display:none;grid-column:1/-1;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;">
        <div class="opt-group">
          <div class="opt-label">Temperature</div>
          <input class="opt-input" id="samplingTemp" value="0.80" type="number" step="0.05" min="0" max="2">
        </div>
        <div class="opt-group">
          <div class="opt-label">Repeat Penalty</div>
          <input class="opt-input" id="samplingRepeat" value="1.00" type="number" step="0.05" min="0" max="2">
        </div>
        <div class="opt-group">
          <div class="opt-label">Top-K</div>
          <input class="opt-input" id="samplingTopK" value="40" type="number" step="1" min="0" max="200">
        </div>
        <div class="opt-group">
          <div class="opt-label">Top-P</div>
          <input class="opt-input" id="samplingTopP" value="0.95" type="number" step="0.05" min="0" max="1">
        </div>
      </div>
      <div class="opt-group" style="margin-top:8px;">
        <div class="opt-label">Extra Flags</div>
        <input class="opt-input" id="samplingExtra" placeholder="--mirostat 0 --seed -1 --presence-penalty 0.1 …">
      </div>
    </div>
  </div>
  <div class="cmd-preview" id="cmdPreview">← Modell wählen</div>
  <div class="btn-row">
    <button class="btn-start" id="btnStart" onclick="startServer()" disabled>▶ Starten</button>
    <button class="btn-stop"  id="btnStop"  onclick="stopServer()"  disabled>■ Stoppen</button>
    <button class="btn-chat"  id="btnChat"  onclick="openChat()"    disabled>Chat →</button>
    <button class="btn-llama"  id="btnLlama" onclick="openLlama()"  disabled>🦙 Llama</button>
    <button class="btn-reload" onclick="loadModels()">⟳</button>
  </div>
</div>

<!-- STATUS -->
<div class="card">
  <div class="section-title">Status</div>
  <div class="status-bar">
    <div class="dot" id="dot"></div>
    <div class="status-txt" id="statusTxt">Server gestoppt</div>
  </div>
  <div class="log" id="log">Bereit.</div>
</div>

<div class="dev-notes-bar">
  <a href="https://github.com/bagueDev" target="_blank" rel="noopener">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
    bagueDev
  </a>
  <span class="dev-sep">·</span>
  <a href="https://youtube.com/@bagueDev" target="_blank" rel="noopener">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
    @bagueDev
  </a>
</div>

<script>
let selectedModel = null;
let pollInterval = null;

// ── Verzeichnis-Manager ──────────────────────────────────────
function renderDirs(dirs) {
  const list = document.getElementById('dirList');
  list.innerHTML = '';
  dirs.forEach(d => {
    const el = document.createElement('div');
    el.className = 'dir-item';
    el.innerHTML =
      '<div class="dir-path">' + d + '</div>' +
      '<button class="dir-remove" onclick="removeDir(\'' + d.replace(/\\/g,'\\\\').replace(/'/g,"\\'") + '\')" title="Entfernen">&#10005;</button>';
    list.appendChild(el);
  });
}

async function loadDirs() {
  const r = await fetch('/api/dirs');
  const dirs = await r.json();
  renderDirs(dirs);
}

async function addDir() {
  const input = document.getElementById('dirInput');
  const path = input.value.trim();
  if (!path) return;
  const r = await fetch('/api/dirs/add', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({path})
  });
  const d = await r.json();
  if (d.ok) {
    input.value = '';
    renderDirs(d.dirs);
    loadModels();
  } else {
    addLog('Fehler: ' + d.error);
  }
}

async function removeDir(path) {
  const r = await fetch('/api/dirs/remove', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({path})
  });
  const d = await r.json();
  renderDirs(d.dirs);
  loadModels();
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('dirInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') addDir();
  });
  updateSamplingFields();
});

// ── Modelle ──────────────────────────────────────────────────
async function loadModels() {
  const list = document.getElementById('modelList');
  list.innerHTML = '<div class="no-models">Lade...</div>';
  try {
    const r = await fetch('/api/models');
    const models = await r.json();
    if (!models.length) {
      list.innerHTML = '<div class="no-models">Keine .gguf Dateien gefunden</div>';
      return;
    }
    list.innerHTML = '';
    models.forEach(m => {
      const el = document.createElement('div');
      el.className = 'model-item';
      el.innerHTML =
        '<div style="flex:1;min-width:0">' +
          '<div class="model-name">' + m.name + '</div>' +
          '<div class="model-dir">' + m.dir + '</div>' +
        '</div>' +
        '<div class="model-size">' + m.size + '</div>';
      el.onclick = () => selectModel(m, el);
      list.appendChild(el);
    });
  } catch(e) {
    list.innerHTML = '<div class="no-models">Fehler beim Laden</div>';
  }
}

function selectModel(m, el) {
  document.querySelectorAll('.model-item').forEach(i => i.classList.remove('selected'));
  el.classList.add('selected');
  selectedModel = m;
  document.getElementById('btnStart').disabled = false;
  updatePreview();
}

const SAMPLING_PRESETS = {
  chat:     { t:0.70, r:1.10, k:40, p:0.90 },
  creative: { t:0.90, r:1.15, k:60, p:0.95 },
  code:     { t:0.50, r:1.15, k:30, p:0.85 },
};

function updateSamplingFields() {
  const sel = document.getElementById('samplingPreset');
  const cust = document.getElementById('samplingCustom');
  cust.style.display = sel.value === 'custom' ? 'block' : 'none';
}

document.getElementById('samplingPreset').addEventListener('change', () => {
  updateSamplingFields();
  updatePreview();
});

function getSamplingFlags() {
  const preset = document.getElementById('samplingPreset').value;
  if (preset === 'default') return '';
  if (preset === 'custom') {
    const t = document.getElementById('samplingTemp').value;
    const r = document.getElementById('samplingRepeat').value;
    const k = document.getElementById('samplingTopK').value;
    const p = document.getElementById('samplingTopP').value;
    const extra = document.getElementById('samplingExtra').value.trim();
    let f = ' --temp ' + t + ' --repeat-penalty ' + r + ' --top-k ' + k + ' --top-p ' + p;
    if (extra) f += ' ' + extra;
    return f;
  }
  const v = SAMPLING_PRESETS[preset];
  return ' --temp ' + v.t + ' --repeat-penalty ' + v.r + ' --top-k ' + v.k + ' --top-p ' + v.p;
}

function updatePreview() {
  if (!selectedModel) return;
  const ctx = document.getElementById('ctxSize').value;
  const ngl = document.getElementById('ngl').value;
  const port = document.getElementById('port').value;
  const threads = document.getElementById('threads').value;
  const cacheTypeK = document.getElementById('cacheTypeK').value;
  const cacheTypeV = document.getElementById('cacheTypeV').value;
  const batch = document.getElementById('batchSize').value;
  const ubatch = document.getElementById('ubatchSize').value;
  const mt = document.getElementById('maxTokens').value;
  const fa = document.getElementById('flashAttn').checked ? ' --flash-attn 1' : '';
  const mcp = document.getElementById('mcpProxy').checked ? ' --webui-mcp-proxy' : '';
  const ct = document.querySelector('input[name="chatTemplate"]:checked');
  const ctFlag = ct && ct.value === 'qwen' ? ' --chat-template-file qwen_fixed.jinja' : ct && ct.value === 'gemma' ? ' --chat-template-file gemma_fixed.jinja' : '';
  const mtp = document.getElementById('mtp').checked;
  const specDraftNMax = document.getElementById('specDraftNMax').value;
  const modelDraft = document.getElementById('modelDraft').value.trim();
  let mtpFlags = '';
  if (mtp) {
    mtpFlags = ' --spec-type draft-mtp --spec-draft-n-max ' + specDraftNMax;
    if (modelDraft) mtpFlags += ' -md ' + modelDraft;
  }
  document.getElementById('cmdPreview').innerHTML =
    '<span>llama-server</span> -m ' + selectedModel.name +
    ' -ngl ' + ngl +
    ' --ctx-size ' + ctx + ' --threads ' + threads + ' --port ' + port +
    ' --cache-type-k ' + cacheTypeK + ' --cache-type-v ' + cacheTypeV +
    ' --batch-size ' + batch + ' --ubatch-size ' + ubatch +
    ' --n-predict ' + mt + fa + mcp + ctFlag + mtpFlags + getSamplingFlags();
}

['ctxSize','ngl','port','threads','batchSize','ubatchSize','maxTokens','specDraftNMax'].forEach(id =>
  document.getElementById(id).addEventListener('input', updatePreview)
);
['cacheTypeK','cacheTypeV'].forEach(id =>
  document.getElementById(id).addEventListener('change', updatePreview)
);
['mcpProxy','flashAttn','useJinja','mtp'].forEach(id =>
  document.getElementById(id).addEventListener('change', updatePreview)
);
document.querySelectorAll('input[name="chatTemplate"]').forEach(el =>
  el.addEventListener('change', updatePreview)
);
document.getElementById('modelDraft').addEventListener('input', updatePreview);
['samplingTemp','samplingRepeat','samplingTopK','samplingTopP','samplingExtra'].forEach(id =>
  document.getElementById(id).addEventListener('input', updatePreview)
);

// ── Server ───────────────────────────────────────────────────
async function startServer() {
  if (!selectedModel) return;
  document.getElementById('btnStart').disabled = true;
  setStatus('starting', 'Starte Server...');
  addLog('Starte: ' + selectedModel.name);
  const body = {
    model: selectedModel.path,
    ctx_size: parseInt(document.getElementById('ctxSize').value),
    ngl: parseInt(document.getElementById('ngl').value),
    port: parseInt(document.getElementById('port').value),
    threads: parseInt(document.getElementById('threads').value),
    cache_type_k: document.getElementById('cacheTypeK').value,
    cache_type_v: document.getElementById('cacheTypeV').value,
    batch_size: parseInt(document.getElementById('batchSize').value),
    ubatch_size: parseInt(document.getElementById('ubatchSize').value),
    max_tokens: parseInt(document.getElementById('maxTokens').value),
    flash_attn: document.getElementById('flashAttn').checked,
    mcp_proxy: document.getElementById('mcpProxy').checked,
    use_jinja: document.getElementById('useJinja').checked,
    chat_template: document.querySelector('input[name="chatTemplate"]:checked')?.value || '',
    mtp: document.getElementById('mtp').checked,
    spec_draft_n_max: parseInt(document.getElementById('specDraftNMax').value),
    model_draft: document.getElementById('modelDraft').value.trim(),
    sampling_preset: document.getElementById('samplingPreset').value,
    sampling_temp: parseFloat(document.getElementById('samplingTemp').value),
    sampling_repeat: parseFloat(document.getElementById('samplingRepeat').value),
    sampling_top_k: parseInt(document.getElementById('samplingTopK').value),
    sampling_top_p: parseFloat(document.getElementById('samplingTopP').value),
    sampling_extra: document.getElementById('samplingExtra').value.trim(),
  };
  try {
    const r = await fetch('/api/start', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const d = await r.json();
    if (d.ok) {
      localStorage.setItem('ctxSize', body.ctx_size);
      localStorage.setItem('maxTokens', body.max_tokens);
      document.getElementById('btnStop').disabled = false;
      document.getElementById('btnChat').disabled = false;
      document.getElementById('btnLlama').disabled = false;
      pollStatus();
    } else {
      setStatus('error', 'Fehler: ' + d.error);
      document.getElementById('btnStart').disabled = false;
    }
  } catch(e) {
    setStatus('error', 'Fehler: ' + e.message);
    document.getElementById('btnStart').disabled = false;
  }
}

async function stopServer() {
  await fetch('/api/stop', {method:'POST'});
  clearInterval(pollInterval);
  setStatus('stopped', 'Server gestoppt');
  addLog('Server gestoppt.');
  document.getElementById('btnStart').disabled = !selectedModel;
  document.getElementById('btnStop').disabled = true;
  document.getElementById('btnChat').disabled = true;
  document.getElementById('btnLlama').disabled = true;
}

function pollStatus() {
  clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const r = await fetch('/api/status');
      const d = await r.json();
      if (d.running) {
        setStatus('running', 'Laeuft · Port ' + d.port + ' · ' + d.model);
        if (d.log_line) addLog(d.log_line);
      } else {
        setStatus('stopped', 'Server gestoppt');
        clearInterval(pollInterval);
        document.getElementById('btnStart').disabled = !selectedModel;
        document.getElementById('btnStop').disabled = true;
        document.getElementById('btnChat').disabled = true;
        document.getElementById('btnLlama').disabled = true;
      }
    } catch {}
  }, 1500);
}

function setStatus(state, text) {
  const dot = document.getElementById('dot');
  const txt = document.getElementById('statusTxt');
  dot.className = 'dot' + (state === 'running' ? ' running' : state === 'error' ? ' error' : '');
  txt.className = 'status-txt' + (state === 'running' ? ' running' : state === 'error' ? ' error' : '');
  txt.textContent = text;
}

function addLog(line) {
  const log = document.getElementById('log');
  log.textContent += '\n' + line;
  log.scrollTop = log.scrollHeight;
}

function openChat() {
  const port = document.getElementById('port').value;
  window.open('/chat?port=' + port, '_blank');
}

function openLlama() {
  const port = document.getElementById('port').value;
  window.open('http://localhost:' + port, '_blank');
}

loadDirs();
loadModels();

function showAbout() { document.getElementById('aboutOverlay').classList.add('show'); }
function hideAbout() { document.getElementById('aboutOverlay').classList.remove('show'); }
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideAbout(); });
</script>

<div class="overlay" id="aboutOverlay" onclick="if(event.target===this)hideAbout()">
  <div class="modal">
    <button class="modal-close" onclick="hideAbout()">✕</button>
    <div class="modal-title">bagueDev Community Launcher</div>
    <div class="modal-sub">Developed by bagueDev</div>
    <div class="modal-links">
      <a href="https://github.com/bagueDev" target="_blank" rel="noopener">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        github.com/bagueDev
      </a>
      <a href="https://youtube.com/@bagueDev" target="_blank" rel="noopener">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
        youtube.com/@bagueDev
      </a>
    </div>
    <div class="modal-section">Frameworks</div>
    <div class="modal-grid">
      <span class="cat">Inference</span><span class="val">llama.cpp</span>
      <span class="cat">Server</span><span class="val">uvicorn · h11</span>
      <span class="cat">MCP</span><span class="val">MCP Python SDK</span>
      <span class="cat">HTTP</span><span class="val">requests · http.server</span>
      <span class="cat">Scraping</span><span class="val">beautifulsoup4 · crawl4ai</span>
      <span class="cat">Media</span><span class="val">yt-dlp</span>
      <span class="cat">Trends</span><span class="val">pytrends · ddgs</span>
      <span class="cat">Browser</span><span class="val">Playwright</span>
      <span class="cat">Database</span><span class="val">ChromaDB</span>
    </div>
  </div>
</div>
</body>
</html>"""

HTML_CHAT = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>bagueDev Chat</title>

<style>
  :root {
    --bg: #0a0a0f;--surface: #111118;--border: #1e1e2e;--accent: #ff6b35;
    --accent2: #e040fb;--text: #e8e8f0;--muted: #555570;--green: #00e5a0;
    --mono: monospace;--sans: sans-serif;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);color: var(--text);font-family: var(--mono);
    height: 100vh;display: grid;
    grid-template-rows: auto 1fr auto;grid-template-columns: 1fr 280px;
    grid-template-areas: "header header" "chat sidebar" "input sidebar";
    overflow: hidden;
  }
  header {
    grid-area: header;padding: 14px 24px;border-bottom: 1px solid var(--border);
    display: flex;align-items: center;gap: 12px;background: var(--surface);
  }
  .back-btn {
    background: transparent;color: var(--muted);border: 1px solid var(--border);
    border-radius: 6px;padding: 6px 12px;font-family: var(--mono);font-size: 0.72rem;
    cursor: pointer;height: 30px;transition: color .2s,border-color .2s;
  }
  .back-btn:hover { color: var(--text); border-color: var(--muted); }
  .logo { font-family: var(--sans);font-weight: 800;font-size: 1.1rem;color: var(--accent);letter-spacing: -0.02em; }
  .logo span { color: var(--text); }
  .status-dot { width: 8px;height: 8px;border-radius: 50%;background: var(--muted);transition: background .3s;flex-shrink: 0; }
  .status-dot.online { background: var(--green);box-shadow: 0 0 8px var(--green); }
  .status-dot.error { background: var(--accent); }
  .status-text { font-size: 0.7rem;color: var(--muted);letter-spacing: .05em;text-transform: uppercase; }
  .model-badge { margin-left: auto;font-size: 0.65rem;color: var(--muted);background: var(--border);padding: 4px 10px;border-radius: 4px;max-width: 300px;overflow: hidden;text-overflow: ellipsis;white-space: nowrap; }
  #chat { grid-area: chat;overflow-y: auto;padding: 20px 24px;display: flex;flex-direction: column;gap: 16px;scrollbar-width: thin;scrollbar-color: var(--border) transparent; }
  .msg { display: flex;gap: 12px;animation: fadeUp 0.2s ease; }
  @keyframes fadeUp { from { opacity: 0;transform: translateY(6px); } to { opacity: 1;transform: translateY(0); } }
  .msg-role { font-size: 0.6rem;text-transform: uppercase;letter-spacing: .1em;padding-top: 3px;flex-shrink: 0;width: 40px; }
  .msg.user .msg-role { color: var(--accent); }
  .msg.assistant .msg-role { color: var(--accent2); }
  .msg.system .msg-role { color: var(--muted); }
  .msg-content { font-size: 0.85rem;line-height: 1.7;color: var(--text);flex: 1;white-space: pre-wrap;word-break: break-word; }
  .msg.user .msg-content { color: #c8c8e0; }
  .cursor { display: inline-block;width: 2px;height: 1em;background: var(--accent2);animation: blink .8s infinite;vertical-align: text-bottom;margin-left: 2px; }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
  .input-area { grid-area: input;padding: 16px 24px 20px;border-top: 1px solid var(--border);background: var(--surface);display: flex;gap: 10px;align-items: flex-end; }
  textarea { flex: 1;background: var(--bg);border: 1px solid var(--border);border-radius: 8px;color: var(--text);font-family: var(--mono);font-size: 0.85rem;padding: 10px 14px;resize: none;min-height: 44px;max-height: 140px;outline: none;transition: border-color .2s;line-height: 1.5; }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--muted); }
  button { background: var(--accent);color: #000;border: none;border-radius: 8px;padding: 10px 18px;font-family: var(--sans);font-weight: 700;font-size: 0.8rem;cursor: pointer;transition: opacity .2s,transform .1s;white-space: nowrap;height: 44px;letter-spacing: .03em; }
  button:hover { opacity: .85; }
  button:active { transform: scale(.97); }
  button:disabled { opacity: .3;cursor: not-allowed; }
  .btn-clear { background: transparent;color: var(--muted);border: 1px solid var(--border);font-family: var(--mono);font-weight: 400;font-size: .75rem; }
  aside { grid-area: sidebar;border-left: 1px solid var(--border);background: var(--surface);padding: 20px 16px;overflow-y: auto;display: flex;flex-direction: column;gap: 20px;scrollbar-width: thin;scrollbar-color: var(--border) transparent; }
  .section-title { font-family: var(--sans);font-size: .65rem;text-transform: uppercase;letter-spacing: .12em;color: var(--muted);margin-bottom: 10px; }
  .stat-grid { display: grid;grid-template-columns: 1fr 1fr;gap: 8px; }
  .stat-card { background: var(--bg);border: 1px solid var(--border);border-radius: 6px;padding: 10px 12px; }
  .stat-label { font-size: .6rem;color: var(--muted);text-transform: uppercase;letter-spacing: .08em;margin-bottom: 4px; }
  .stat-value { font-size: 1.1rem;font-weight: 600;color: var(--text); }
  .stat-value.green { color: var(--green); }
  .stat-value.orange { color: var(--accent); }
  .stat-value.purple { color: var(--accent2); }
  .stat-value.blue { color: #60a5fa; }
  .token-bar-wrap { background: var(--bg);border: 1px solid var(--border);border-radius: 6px;padding: 10px 12px; }
  .token-bar-label { display: flex;justify-content: space-between;font-size: .65rem;color: var(--muted);margin-bottom: 6px; }
  .token-bar { height: 4px;background: var(--border);border-radius: 2px;overflow: hidden; }
  .token-bar-fill { height: 100%;background: linear-gradient(90deg,var(--green),var(--accent2));border-radius: 2px;transition: width .3s;width: 0%; }
  .api-block { background: var(--bg);border: 1px solid var(--border);border-radius: 6px;padding: 10px 12px; }
  .api-url { font-size: .7rem;color: var(--green);word-break: break-all;margin-bottom: 8px; }
  .api-snippet { font-size: .62rem;color: var(--muted);line-height: 1.6;white-space: pre;overflow-x: auto; }
  .dev-links { display: flex;flex-direction: column;gap: 8px; }
  .dev-link { display: flex;align-items: center;gap: 8px;color: var(--muted);text-decoration: none;font-size: .7rem;padding: 6px 8px;border-radius: 6px;background: var(--bg);border: 1px solid var(--border);transition: color .15s,border-color .15s; }
  .dev-link:hover { color: var(--fg);border-color: var(--accent); }
  .dev-icon { width: 16px;height: 16px;flex-shrink: 0; }
  .empty-state { text-align: center;padding: 40px 20px;color: var(--muted);font-size: .8rem;line-height: 1.8; }
  .empty-state .big { font-size: 2rem;margin-bottom: 8px; }
  .sysprompt { width: 100%;height: 80px;background: var(--bg);border: 1px solid var(--border);border-radius: 6px;color: var(--text);font-family: var(--mono);font-size: .72rem;padding: 8px 10px;resize: vertical;outline:none;transition: border-color .2s; }
  .sysprompt:focus { border-color: var(--accent); }
  .sensor-grid { display: grid;grid-template-columns: 1fr 1fr;gap: 6px; }
  .sensor-card { background: var(--bg);border: 1px solid var(--border);border-radius: 6px;padding: 8px 10px; }
  .sensor-label { font-size: .55rem;color: var(--muted);text-transform: uppercase;letter-spacing: .08em;margin-bottom: 2px; }
  .sensor-value { font-size: .85rem;font-weight: 600;color: var(--text); }
  .sensor-value.hot { color: var(--accent); }
  .sensor-value.cool { color: var(--green); }
  .btn-about{background:transparent;color:var(--muted);border:1px solid var(--border);border-radius:6px;padding:4px 10px;font-family:var(--mono);font-size:.72rem;cursor:pointer;transition:color .2s,border-color .2s;flex-shrink:0;height:30px;}
  .btn-about:hover{color:var(--text);border-color:var(--muted);}
  .overlay{display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.6);backdrop-filter:blur(2px);align-items:center;justify-content:center;}
  .overlay.show{display:flex;}
  .modal{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px 32px;max-width:420px;width:90%;max-height:80vh;overflow-y:auto;position:relative;animation:fadeUp .2s ease;}
  .modal-close{position:absolute;top:12px;right:16px;background:none;border:none;color:var(--muted);font-size:1.2rem;cursor:pointer;padding:4px;line-height:1;}
  .modal-close:hover{color:var(--text);}
  .modal-title{font-family:var(--sans);font-weight:800;font-size:1.1rem;color:var(--accent);margin-bottom:4px;}
  .modal-sub{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;margin-bottom:16px;}
  .modal-section{font-size:.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-top:16px;margin-bottom:8px;}
  .modal-links{display:flex;gap:16px;margin-bottom:12px;}
  .modal-links a{color:var(--muted);text-decoration:none;font-size:.75rem;display:inline-flex;align-items:center;gap:5px;transition:color .15s;}
  .modal-links a:hover{color:var(--accent2);}
  .modal-grid{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;font-size:.72rem;line-height:1.8;}
  .modal-grid .cat{color:var(--muted);white-space:nowrap;}
  .modal-grid .val{color:var(--text);}
</style>
</head>
<body>

<header>
  <button class="back-btn" onclick="window.location.href='/'">&#8592; Launcher</button>
  <div class="logo">bagueDev<span> Chat</span></div>
  <div class="status-dot" id="statusDot"></div>
  <div class="status-text" id="statusText">verbinde...</div>
  <div class="model-badge" id="modelBadge">&#8212;</div>
  <button class="btn-about" onclick="showAbout()" title="About">ℹ</button>
</header>

<div id="chat">
  <div class="empty-state"><div class="big">&#9889;</div>Verbinde mit llama-server...</div>
</div>

<div class="input-area">
  <textarea id="input" placeholder="Nachricht... (Enter = senden, Shift+Enter = Zeilenumbruch)" rows="1"></textarea>
  <button class="btn-clear" onclick="clearChat()">Leeren</button>
  <button class="btn-clear" onclick="exportChat()">Export MD</button>
  <button id="sendBtn" onclick="sendMessage()" disabled>Senden</button>
</div>

<aside>
  <div>
    <div class="section-title">Token Monitor</div>
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-label">Tokens/s</div><div class="stat-value green" id="statTps">&#8212;</div></div>
      <div class="stat-card"><div class="stat-label">Gesamt</div><div class="stat-value orange" id="statTotal">0</div></div>
      <div class="stat-card"><div class="stat-label">Prompt</div><div class="stat-value" id="statPrompt">0</div></div>
      <div class="stat-card"><div class="stat-label">Antwort</div><div class="stat-value purple" id="statCompletion">0</div></div>
      <div class="stat-card"><div class="stat-label">Letzte Antwort</div><div class="stat-value blue" id="statTime">&#8212;</div></div>
      <div class="stat-card"><div class="stat-label">Gesamt Zeit</div><div class="stat-value" id="statTimeTotal">0s</div></div>
    </div>
    <div style="margin-top:8px">
      <div class="token-bar-wrap">
        <div class="token-bar-label"><span>Kontext</span><span id="ctxUsed">0 / 4096</span></div>
        <div class="token-bar"><div class="token-bar-fill" id="ctxBar"></div></div>
      </div>
    </div>
  </div>

  <div>
    <div class="section-title">System Prompt</div>
    <textarea class="sysprompt" id="sysprompt" placeholder="Optional: Rolle / Anweisung..."></textarea>
  </div>

  <div>
    <div class="section-title">Continue.dev</div>
    <div class="api-block">
      <div class="api-url" id="apiUrl">&#8212;</div>
      <div class="api-snippet" id="apiSnippet">Verbinde zuerst...</div>
    </div>
  </div>

  <div>
    <div class="section-title">Sensoren</div>
    <div class="sensor-grid" id="sensors">
      <div class="sensor-card"><div class="sensor-label">GPU</div><div class="sensor-value" id="senGpu">--</div></div>
      <div class="sensor-card"><div class="sensor-label">Junction</div><div class="sensor-value" id="senJunc">--</div></div>
      <div class="sensor-card"><div class="sensor-label">Fan GPU</div><div class="sensor-value" id="senFan">--</div></div>
      <div class="sensor-card"><div class="sensor-label">PPT</div><div class="sensor-value" id="senPpt">--</div></div>
      <div class="sensor-card"><div class="sensor-label">CPU</div><div class="sensor-value" id="senCpu">--</div></div>
      <div class="sensor-card"><div class="sensor-label">Fan CPU</div><div class="sensor-value" id="senFanCpu">--</div></div>
    </div>
  </div>

  <div>
    <div class="section-title">Dev Notes</div>
    <div class="dev-links">
      <a class="dev-link" href="https://github.com/bagueDev" target="_blank" rel="noopener">
        <svg class="dev-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        <span>github.com/bagueDev</span>
      </a>
      <a class="dev-link" href="https://youtube.com/@bagueDev" target="_blank" rel="noopener">
        <svg class="dev-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
        <span>youtube.com/@bagueDev</span>
      </a>
    </div>
  </div>
</aside>

<script>
  const params = new URLSearchParams(window.location.search);
  const SERVER_PORT = params.get('port') || 8080;
  const SERVER_URL  = 'http://localhost:' + SERVER_PORT;
  let messages = [], totalPromptTokens = 0, totalCompletionTokens = 0;
  let ctxLimit = parseInt(localStorage.getItem('ctxSize')) || 4096, isConnected = false;
  document.getElementById('ctxUsed').textContent = '0 / ' + ctxLimit;
  let totalElapsed = 0;
  let timerInterval = null;

  const chatEl  = document.getElementById('chat');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');

  inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
  });
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (!sendBtn.disabled) sendMessage(); }
  });

  async function connect() {
    try {
      const r = await fetch(SERVER_URL + '/v1/models', {signal: AbortSignal.timeout(4000)});
      if (!r.ok) throw new Error();
      const data = await r.json();
      const modelName = data.data?.[0]?.id || 'local';
      document.getElementById('statusDot').className = 'status-dot online';
      document.getElementById('statusText').textContent = 'verbunden';
      document.getElementById('modelBadge').textContent = modelName;
      document.getElementById('apiUrl').textContent = SERVER_URL + '/v1';
      document.getElementById('apiSnippet').textContent =
        '- name: bagueDev\n  provider: openai\n  model: ' + modelName + '\n  apiBase: ' + SERVER_URL + '/v1\n  apiKey: none';
      isConnected = true;
      sendBtn.disabled = false;
      addSystemMsg('Verbunden: ' + modelName + ' auf Port ' + SERVER_PORT);
    } catch {
      document.getElementById('statusDot').className = 'status-dot error';
      document.getElementById('statusText').textContent = 'fehler';
      addSystemMsg('Kein Server auf Port ' + SERVER_PORT);
      setTimeout(connect, 4000);
    }
  }

  function addSystemMsg(text) {
    if (chatEl.querySelector('.empty-state')) chatEl.innerHTML = '';
    const el = document.createElement('div'); el.className = 'msg system';
    el.innerHTML = '<div class="msg-role">sys</div><div class="msg-content">' + text + '</div>';
    chatEl.appendChild(el); chatEl.scrollTop = chatEl.scrollHeight;
  }

  function escHtml(t) { return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || !isConnected) return;
    inputEl.value = ''; inputEl.style.height = 'auto'; sendBtn.disabled = true;
    messages.push({role: 'user', content: text});

    const uel = document.createElement('div'); uel.className = 'msg user';
    uel.innerHTML = '<div class="msg-role">du</div><div class="msg-content">' + escHtml(text) + '</div>';
    chatEl.appendChild(uel);

    const ael = document.createElement('div'); ael.className = 'msg assistant';
    const cur = document.createElement('span'); cur.className = 'cursor';
    const ac  = document.createElement('div');  ac.className  = 'msg-content'; ac.appendChild(cur);
    ael.innerHTML = '<div class="msg-role">ki</div>'; ael.appendChild(ac);
    chatEl.appendChild(ael); chatEl.scrollTop = chatEl.scrollHeight;

  // Einfache Token-Zaehlung (approximativ)
  function countTokens(text) {
    if (!text) return 0;
    const words = text.split(/\s+/).filter(w => w.length > 0).length;
    const chars = text.replace(/\s/g, '').length;
    return Math.max(1, Math.round((words * 1.3 + chars) / 4));
  }

  let response = '', ct = 0, t0 = Date.now();
  const sp = document.getElementById('sysprompt').value.trim();
  
  // Qwen-Format Nachrichten mit <|im_start|> tokens
  // Qwen3 verwendet Standardmessages-Format, nur System wird eingebettet
  const modelBadge = document.getElementById('modelBadge').textContent.toLowerCase();
  const isQwen = modelBadge.includes('qwen');
  const isLlama = modelBadge.includes('llama') || modelBadge.includes('meta');
  
  let apiMsgs;
  if (isQwen) {
    apiMsgs = [];
    const sysContent = sp || 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.';
    apiMsgs.push({role: 'system', content: '<|im_start|>system\n' + sysContent + '<|im_end|>\n'});
    messages.forEach(m => {
      const role = m.role === 'user' ? 'user' : 'assistant';
      apiMsgs.push({role: role, content: '<|im_start|>' + role + '\n' + m.content + '<|im_end|>\n'});
    });
    // KEINE prefilled assistant message bei Qwen3 mit Thinking
  } else if (isLlama) {
    // Llama 3/4 Format mit special tokens
    apiMsgs = [];
    if (sp) {
      apiMsgs.push({role: 'system', content: sp});
    }
    messages.forEach(m => {
      apiMsgs.push(m);
    });
    apiMsgs.push({role: 'assistant', content: ''});
  } else {
    apiMsgs = [...(sp ? [{role:'system', content:sp}] : []), ...messages];
  }

  // Debug: log what's being sent
  console.log('Model:', modelBadge);
  console.log('Messages:', JSON.stringify(apiMsgs, null, 2));
  
  // Zähle Prompt-Token VOR dem Senden
  const promptText = apiMsgs.map(m => m.content).join('\n');
  totalPromptTokens = countTokens(promptText);
  document.getElementById('statPrompt').textContent = totalPromptTokens;

  // Hole Modelldetails fuer Kontextgroesse
  try {
    const mr = await fetch(SERVER_URL + '/v1/models', {signal: AbortSignal.timeout(4000)});
    if (mr.ok) {
      const mdata = await mr.json();
      const model = mdata.data?.[0];
      if (model?.permission?.[0]?.max_model_len) {
        ctxLimit = model.permission[0].max_model_len;
        document.getElementById('ctxUsed').textContent = '0 / ' + ctxLimit;
      }
    }
  } catch {}

  // Live-Timer
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const s = ((Date.now() - t0) / 1000).toFixed(1);
    document.getElementById('statTime').textContent = s + 's';
  }, 100);

    try {
      const r = await fetch(SERVER_URL + '/v1/chat/completions', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          model: 'local', 
          messages: apiMsgs, 
          stream: true, 
          max_tokens: parseInt(document.getElementById('maxTokens')?.value) || 2048
        })
      });
      if (!r.ok) {
        const errText = await r.text();
        throw new Error('Server responded with ' + r.status + ': ' + errText.slice(0, 200));
      }
      const reader = r.body.getReader(), decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const {done, value} = await reader.read(); 
        if (done) break;
        buffer += decoder.decode(value, {stream: true});
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const d = line.slice(6).trim(); if (d === '[DONE]') continue;
          try {
            const j = JSON.parse(d);
            const delta = j.choices?.[0]?.delta?.content || '';
            response += delta; ct++;
            ac.textContent = response; ac.appendChild(cur); 
            if (chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight < 100) {
              chatEl.scrollTop = chatEl.scrollHeight;
            }
            const el = (Date.now() - t0) / 1000;
            document.getElementById('statTps').textContent = el > 0 ? (ct/el).toFixed(1) : '--';
            document.getElementById('statCompletion').textContent = ct;
            // Context-Bar immer aktualisieren
            const used = totalPromptTokens + ct;
            document.getElementById('ctxUsed').textContent = used + ' / ' + ctxLimit;
            document.getElementById('ctxBar').style.width = Math.min(used/ctxLimit*100, 100) + '%';
            document.getElementById('statTotal').textContent = totalPromptTokens + ct;
            if (j.usage) {
              totalPromptTokens = j.usage.prompt_tokens || totalPromptTokens;
              document.getElementById('statPrompt').textContent = totalPromptTokens;
            }
          } catch (e) {
            console.error('Parse error:', e, 'data:', d);
          }
        }
      }

      // Timer stoppen, Endergebnis
      clearInterval(timerInterval);
      const elapsed = (Date.now() - t0) / 1000;
      totalElapsed += elapsed;
      document.getElementById('statTime').textContent = elapsed.toFixed(1) + 's';
      document.getElementById('statTimeTotal').textContent = totalElapsed.toFixed(1) + 's';

      cur.remove(); messages.push({role: 'assistant', content: response});
      totalCompletionTokens += ct;
      document.getElementById('statTps').textContent = elapsed > 0 ? (ct/elapsed).toFixed(1) : '--';
      document.getElementById('statTotal').textContent = totalPromptTokens + totalCompletionTokens;
      document.getElementById('statPrompt').textContent = totalPromptTokens;
      document.getElementById('statCompletion').textContent = totalCompletionTokens;
    } catch(e) {
      clearInterval(timerInterval);
      cur.remove(); ac.textContent = 'Fehler: ' + e.message;
    }
    sendBtn.disabled = false; inputEl.focus();
  }

  function clearChat() {
    messages = []; totalPromptTokens = 0; totalCompletionTokens = 0; totalElapsed = 0;
    clearInterval(timerInterval);
    chatEl.innerHTML = '<div class="empty-state"><div class="big">&#9889;</div>Chat geleert.</div>';
    document.getElementById('statTps').textContent = '--';
    document.getElementById('statTotal').textContent = '0';
    document.getElementById('statPrompt').textContent = '0';
    document.getElementById('statCompletion').textContent = '0';
    document.getElementById('statTime').textContent = '--';
    document.getElementById('statTimeTotal').textContent = '0s';
    document.getElementById('ctxUsed').textContent = '0 / ' + ctxLimit;
    document.getElementById('ctxBar').style.width = '0%';
  }

  function exportChat() {
    if (!messages.length) { alert('Keine Nachrichten zum Exportieren.'); return; }
    let md = '# bagueDev Chat Export\n\n';
    md += '**Datum:** ' + new Date().toLocaleString('de-DE') + '\n\n';
    md += '## Token Statistik\n\n';
    md += '- **Prompt Tokens:** ' + totalPromptTokens + '\n';
    md += '- **Completion Tokens:** ' + totalCompletionTokens + '\n';
    md += '- **Gesamt:** ' + (totalPromptTokens + totalCompletionTokens) + '\n';
    md += '- **Zeit:** ' + totalElapsed.toFixed(1) + 's\n\n';
    md += '## Chatverlauf\n\n';
    const allMsgs = chatEl.querySelectorAll('.msg');
    allMsgs.forEach(m => {
      const role = m.classList.contains('user') ? 'du' : m.classList.contains('assistant') ? 'KI' : 'sys';
      const content = m.querySelector('.msg-content').textContent;
      md += '### ' + role + '\n\n' + content + '\n\n';
    });
    const blob = new Blob([md], {type: 'text/markdown'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'chat-' + Date.now() + '.md';
    a.click();
  }

  connect();
  setInterval(loadSensors, 4000);
  loadSensors();

  async function loadSensors() {
    try {
      const r = await fetch('/api/sensors', {signal: AbortSignal.timeout(5000)});
      const d = await r.json();
      if (!d.ok || !d.output) return;
      const out = d.output;
      
      const amd = out.split('amdgpu-pci-0300')[1] || '';
       
      const t = amd.match(/edge:\s+([+-]?[\d.]+)/);
      const gpuVal = t ? parseFloat(t[1]) : null;
      const gpuEl = document.getElementById('senGpu');
      gpuEl.textContent = gpuVal ? gpuVal + '°C' : '--';
      gpuEl.className = 'sensor-value' + (gpuVal && gpuVal > 75 ? ' hot' : gpuVal && gpuVal < 50 ? ' cool' : '');
      
      const j = amd.match(/junction:\s+([+-]?[\d.]+)/);
      const juncVal = j ? parseFloat(j[1]) : null;
      const juncEl = document.getElementById('senJunc');
      juncEl.textContent = juncVal ? juncVal + '°C' : '--';
      juncEl.className = 'sensor-value' + (juncVal && juncVal > 95 ? ' hot' : juncVal && juncVal < 60 ? ' cool' : '');
      
      const gf = amd.match(/fan1:\s+(\d+)\s+RPM/);
      document.getElementById('senFan').textContent = gf && gf[1] > 0 ? gf[1] + ' RPM' : '--';
      
      const p = amd.match(/PPT:\s+([\d.]+)\s+W/);
      document.getElementById('senPpt').textContent = p ? p[1] + ' W' : '--';
      
      const c = out.match(/Package id 0:\s+([+-]?[\d.]+)/);
      const cpuVal = c ? parseFloat(c[1]) : null;
      const cpuEl = document.getElementById('senCpu');
      cpuEl.textContent = cpuVal ? cpuVal + '°C' : '--';
      cpuEl.className = 'sensor-value' + (cpuVal && cpuVal > 80 ? ' hot' : cpuVal && cpuVal < 45 ? ' cool' : '');
      
      const cf = out.match(/fan2:\s+(\d+)\s+RPM/);
      document.getElementById('senFanCpu').textContent = cf && cf[1] > 0 ? cf[1] + ' RPM' : '--';
    } catch {}
  }

function showAbout() { document.getElementById('aboutOverlay').classList.add('show'); }
function hideAbout() { document.getElementById('aboutOverlay').classList.remove('show'); }
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideAbout(); });
</script>

<div class="overlay" id="aboutOverlay" onclick="if(event.target===this)hideAbout()">
  <div class="modal">
    <button class="modal-close" onclick="hideAbout()">✕</button>
    <div class="modal-title">bagueDev Chat</div>
    <div class="modal-sub">Developed by bagueDev</div>
    <div class="modal-links">
      <a href="https://github.com/bagueDev" target="_blank" rel="noopener">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        github.com/bagueDev
      </a>
      <a href="https://youtube.com/@bagueDev" target="_blank" rel="noopener">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
        youtube.com/@bagueDev
      </a>
    </div>
    <div class="modal-section">Frameworks</div>
    <div class="modal-grid">
      <span class="cat">Inference</span><span class="val">llama.cpp</span>
      <span class="cat">Server</span><span class="val">uvicorn · h11</span>
      <span class="cat">MCP</span><span class="val">MCP Python SDK</span>
      <span class="cat">HTTP</span><span class="val">requests · http.server</span>
      <span class="cat">Scraping</span><span class="val">beautifulsoup4 · crawl4ai</span>
      <span class="cat">Media</span><span class="val">yt-dlp</span>
      <span class="cat">Trends</span><span class="val">pytrends · ddgs</span>
      <span class="cat">Browser</span><span class="val">Playwright</span>
      <span class="cat">Database</span><span class="val">ChromaDB</span>
    </div>
  </div>
</div>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/":
            body = HTML_LAUNCHER.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/chat":
            body = HTML_CHAT.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/models":
            global models_dirs
            models = []
            seen = set()
            for d in models_dirs:
                p = Path(d)
                if p.exists():
                    for f in sorted(p.glob("*.gguf")):
                        if f.name not in seen:
                            seen.add(f.name)
                            size_mb = f.stat().st_size / (1024 * 1024)
                            size_str = f"{size_mb/1024:.1f} GB" if size_mb >= 1024 else f"{size_mb:.0f} MB"
                            models.append({"name": f.name, "path": str(f), "size": size_str, "dir": d})
            self.send_json(models)

        elif path == "/api/dirs":
            self.send_json(models_dirs)

        elif path == "/api/status":
            global server_process
            running = server_process is not None and server_process.poll() is None
            log_line = ""
            if running and server_process.stderr:
                try:
                    import select
                    if select.select([server_process.stderr], [], [], 0)[0]:
                        log_line = server_process.stderr.readline().decode(errors="replace").strip()
                except Exception:
                    pass
            self.send_json({
                "running": running,
                "port": SERVER_PORT,
                "model": Path(models_dirs[0]).name if running and models_dirs else "",
                "log_line": log_line,
            })

        elif self.path == "/api/sensors":
            try:
                result = subprocess.run(["sensors"], capture_output=True, text=True, timeout=5)
                data = {"ok": True, "output": result.stdout}
            except Exception as e:
                data = {"ok": False, "error": str(e)}
            self.send_json(data)

        elif self.path == "/api/config":
            self.send_json({"models_dirs": models_dirs})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global server_process, SERVER_PORT, models_dirs

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if self.path == "/api/start":
            if server_process and server_process.poll() is None:
                server_process.terminate()
                server_process.wait()
            SERVER_PORT = body.get("port", 8080)
            cache_type_k = body.get("cache_type_k", "q4_0")
            cache_type_v = body.get("cache_type_v", "q4_0")
            flash_attn = body.get("flash_attn", True)
            batch_size = body.get("batch_size", 512)
            ubatch_size = body.get("ubatch_size", 64)
            mcp_proxy = body.get("mcp_proxy", False)
            mcp_flag = ["--webui-mcp-proxy"] if mcp_proxy else []
            mtp = body.get("mtp", False)
            mtp_flag = []
            if mtp:
                mtp_flag += ["--spec-type", "draft-mtp", "--spec-draft-n-max", str(body.get("spec_draft_n_max", 4))]
                model_draft = body.get("model_draft", "")
                if model_draft:
                    mtp_flag += ["-md", model_draft]
            use_jinja = body.get("use_jinja", True)
            cmd = [
                LLAMA_SERVER,
                "-m",             body["model"],
                "-ngl",           str(body.get("ngl", 99)),
                "--ctx-size",     str(body.get("ctx_size", 4096)),
                "--threads",      str(body.get("threads", 6)),
                "--port",         str(SERVER_PORT),
                "--host",         "0.0.0.0",               
                "--cache-type-k", cache_type_k,
                "--cache-type-v", cache_type_v,
                "--batch-size",   str(batch_size),
                "--ubatch-size",  str(ubatch_size),
                "--n-predict", str(body.get("max_tokens", 2048)),
            ] + mcp_flag + mtp_flag
            chat_template = body.get("chat_template", "")
            base = os.path.dirname(os.path.abspath(__file__))
            if chat_template == "qwen":
                cmd += ["--chat-template-file", os.path.join(base, "qwen_fixed.jinja")]
            elif chat_template == "gemma":
                cmd += ["--chat-template-file", os.path.join(base, "gemma_fixed.jinja")]
            elif use_jinja:
                cmd += ["--jinja"]
            sampling_preset = body.get("sampling_preset", "default")
            if sampling_preset == "custom":
                cmd += ["--temp", str(body.get("sampling_temp", 0.80)),
                        "--repeat-penalty", str(body.get("sampling_repeat", 1.00)),
                        "--top-k", str(body.get("sampling_top_k", 40)),
                        "--top-p", str(body.get("sampling_top_p", 0.95))]
                extra = body.get("sampling_extra", "").strip()
                if extra:
                    cmd += shlex.split(extra)
            elif sampling_preset != "default":
                _sp = {
                    "chat":     (0.70, 1.10, 40,  0.90),
                    "creative": (0.90, 1.15, 60,  0.95),
                    "code":     (0.50, 1.15, 30,  0.85),
                }
                if sampling_preset in _sp:
                    t, r, k, p = _sp[sampling_preset]
                    cmd += ["--temp", str(t), "--repeat-penalty", str(r), "--top-k", str(k), "--top-p", str(p)]
            if flash_attn:
                cmd += ["--flash-attn", "1"]
            try:
                server_process = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE, cwd=LLAMA_CPP_DIR,
                )
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)

        elif self.path == "/api/stop":
            if server_process and server_process.poll() is None:
                server_process.terminate()
                server_process.wait()
            self.send_json({"ok": True})

        elif self.path == "/api/dirs/add":
            path = body.get("path", "").strip()
            if not path:
                self.send_json({"ok": False, "error": "Kein Pfad angegeben"})
                return
            p = Path(path)
            if not p.exists():
                self.send_json({"ok": False, "error": "Verzeichnis nicht gefunden: " + path})
                return
            if path not in models_dirs:
                models_dirs.append(path)
            self.send_json({"ok": True, "dirs": models_dirs})

        elif self.path == "/api/dirs/remove":
            path = body.get("path", "")
            if path in models_dirs and len(models_dirs) > 1:
                models_dirs.remove(path)
            self.send_json({"ok": True, "dirs": models_dirs})

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    print(f"bagueDev Community Launcher  ->  http://localhost:{LAUNCHER_PORT}")
    print(f"Modelle: {DEFAULT_MODELS}")
    print(f"llama-server: {LLAMA_SERVER}")
    print("Ctrl+C zum Beenden\n")

    httpd = http.server.HTTPServer(("localhost", LAUNCHER_PORT), Handler)

    def open_browser():
        import time
        time.sleep(0.8)
        webbrowser.open(f"http://localhost:{LAUNCHER_PORT}")

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nBeende...")
        global server_process
        if server_process and server_process.poll() is None:
            server_process.terminate()
        httpd.server_close()


if __name__ == "__main__":
    main()
