# bagueDev AI Toolkit v1 – Das Handbuch

> Stand: Juni 2026 · Version 1.0

---

## Inhaltsverzeichnis

1. [Warum dieses Toolkit?](#1-warum-dieses-toolkit)
2. [Low‑Budget Philosophie](#2-low-budget-philosophie)
3. [Die Hardware‑Realität 2024–2026: Die RAM‑Krise](#3-die-hardware-realitat-20242026-die-ramkrise)
4. [Die KI‑Hardware‑Blase & der Wertverlust](#4-die-kihardwareblase--der-wertverlust)
5. [Was dieses Toolkit IST (und was nicht)](#5-was-dieses-toolkit-ist-und-was-nicht)
6. [Die Bausteine](#6-die-bausteine)
7. [Datenschutz & Kontrolle](#7-datenschutz--kontrolle)
8. [Loslegen](#8-loslegen)
9. [Developer Notes](#9-developer-notes)

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

## 6. Die Bausteine

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
Keine Cloud, keine API‑Kosten.Erstaunlich gut. 

---

## 7. Datenschutz & Kontrolle

- 100% lokal
- Keine Cloud
- Keine Telemetrie
- Keine API‑Keys
- Keine versteckten Calls

Du behältst die Kontrolle.
Nicht Big Tech.

---

## 8. Loslegen

### Kurzanleitung:

```bash
# 1. Repository klonen
git clone https://github.com/bagueDev/bagueDev-ai-toolkit
cd bagueDev-ai-toolkit

# 2. Venv erstellen
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt
playwright install chromium

# 4. Launcher starten
python3 llama-launcher.py

# 5. Im Browser öffnen
# → http://localhost:9999

# 6. Modell auswählen und starten
# → Chat öffnen, Tools aktivieren, fertig.
```

Das war's. Kein Docker, kein Kubernetes, kein 10‑Seiten‑Setup.

---

## 9. Developer Notes

### Projektstruktur

| Datei | Zweck |
|---|---|
| `llama-launcher.py` | WebUI Launcher (Port 9999) + Chat. Single-File, stdlib only. |
| `mcp_server.py` | V.I.N.C.E.N.T. MCP Server (Port 8000). 50+ Tools, ChromaDB, h11. |
| `start.sh` | Startet Launcher + MCP in zwei Terminal-Tabs. |
| `requirements.txt` | Python-Dependencies für den MCP Server. |
| `AGENTS.md` | KI-Assistenten-Konfiguration (File Writing Strategy, Regeln). |
| `HANDBUCH.md` | Dieses Handbuch. |

### Coding Conventions

- **Single-File**: Wo möglich alles in einer Datei (`llama-launcher.py`).
- **stdlib only**: Launcher hat null Dependencies. MCP Server nutzt Drittanbieter-Pakete nur wo nötig.
- **Keine Type Hints**: Nicht erwünscht, ausser explizit angefragt.
- **Keine HTML/CSS-Kommentare**: UI-Code wird nicht kommentiert.
- **Raw Strings**: Eingebettetes HTML in Python mit `r"""..."""`.
- **Fehlermeldungen**: Auf Deutsch für den User.
- **Konstanten am Dateianfang**: `LLAMA_SERVER`, `SERVER_PORT`, `DEFAULT_MODELS`.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Dein Browser                        │
│  http://localhost:9999 (Launcher + Chat)             │
└──────────┬──────────────────────────┬────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────────┐
│  llama-launcher.py   │   │   mcp_server.py          │
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

### File Writing Strategy

Dateien > 5000 Zeichen werden in zwei Schritten geschrieben:
1. Platzhalter setzen (`def func1(): pass` / `<!-- section1 -->`)
2. Abschnitt für Abschnitt mit echtem Inhalt befüllen

Limit pro `write_file` / `append_to_file`: 16.000 Zeichen.

### Wichtige Flags (llama-server)

| Flag | Wirkung |
|---|---|
| `--jinja` | Chat-Template direkt aus Modell (kein manuelles Template) |
| `--no-cont-batching` | Kein Continuous Batching – GPU wird nach Antwort sofort frei |
| `--slot-keepalive 0` | Slot wird nicht warmgehalten |
| `--flash-attn 1` | Flash Attention für längeren Kontext |
| `--cache-type-k q8_0` | KV-Cache-Kompression spart VRAM |
| `--cache-type-v q8_0` | KV-Cache-Kompression spart VRAM |

### Bekannte Issues

- **llama.cpp PEG Parser**: Kann keine mehreren `<tool_call>`-Blöcke in einer Antwort verarbeiten (Issue #20260).
- **llama.cpp JSON Parser**: Limit bei ~8 KB/13 KB Tool-Call-Argumenten (Issue #20359). Workaround: `--n-predict 16768`.
- **GPU Dauernutzung**: Nach Chat-Antwort hält `--cont-batching` den KV-Cache warm. Workaround: `--no-cont-batching` + `--slot-keepalive 0` (seit v1 Standard).

### Version History

| Version | Datum | Änderungen |
|---|---|---|
| v1.0 | Juni 2026 | Erstveröffentlichung. Launcher, Chat, V.I.N.C.E.N.T. MCP Server, ChromaDB, Handbuch. |

---

> **bagueDev AI Toolkit v1** – Lokal. Leicht. Fair.
>
> MIT License · Copyright © 2026 bagueDev
>
> GitHub: [github.com/bagueDev](https://github.com/bagueDev)
> YouTube: [youtube.com/@bagueDev](https://youtube.com/@bagueDev)
