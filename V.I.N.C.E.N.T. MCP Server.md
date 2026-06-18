# 🤖 V.I.N.C.E.N.T. Tool Suite

*Vollständige Dokumentation aller verfügbaren Tools in V.I.N.C.E.N.T.*

## 🌐 Browser & Web-Interaktion

- **browser_open** — Öffnet eine URL im Browser.
- **structured_snapshot** — Holt eine strukturierte Liste aller interaktiven Elemente auf einer Seite.
- **browser_click** — Klickt auf ein Element mittels CSS-Selektor.
- **browser_type** — Gibt Text in ein Eingabefeld ein.
- **browser_screenshot** — Macht einen Screenshot der aktuellen Ansicht.
- **browser_navigate** — Navigiert zwischen Seiten (vor/zurück/URL).
- **browser_new_tab** — Öffnet einen neuen Tab (optional mit URL).
- **browser_switch_tab** — Wechselt zu einem Tab anhand seines Index.
- **browser_close_tab** — Schließt einen Tab.
- **browser_list_tabs** — Listet alle offenen Tabs auf.
- **browser_wait_for** — Wartet auf das Erscheinen eines Elements (CSS-Selektor).
- **browser_wait_for_load** — Wartet, bis eine Seite vollständig geladen ist.
- **auto_click** — Klickt auf Text mit Selbstheilungs-Fallback.
- **web_scrape** — Scrapt eine Seite und gibt sauberes Markdown zurück.
- **deep_scrape** — Crawlt rekursiv, um alle Seiten einer Website zu durchsuchen.
- **tavily_search** — Websuche mit Tavily AI (bessere Ergebnisse).
- **tavily_extract** — Extrahiert Inhalte aus URLs (Markdown oder Text).
- **tavily_map** — Kartiert die Struktur einer Website.

## 🔍 Suche & Trends

- **duckduckgo_search** — Allgemeine Websuche mit DuckDuckGo.
- **duckduckgo_images** — Bildsuche mit DuckDuckGo.
- **tavily_research** — Führt umfassende, mehrquellenbasierte Recherchen durch.
- **google_trends** — Holt Google Trends für spezifische Keywords.
- **reddit_trending** — Holt Trending-Posts von Reddit.
- **hackernews_trending** — Holt Trending-Artikel von Hacker News.
- **youtube_trending** — Sucht nach aktuellen Trending YouTube-Videos.
- **news_headlines** — Holt aktuelle Nachrichten zu einem Topic.
- **imdb_search** — Sucht Filme auf IMDB.
- **weather** — Holt Wetterdaten für einen bestimmten Ort.
- **browser_search_products** — Sucht Produkte auf Amazon.

## 📁 Datei & Projektverwaltung

- **read_file** — Liest den Inhalt einer lokalen Datei.
- **write_file** — Schreibt Inhalt in eine Datei oder erstellt eine neue.
- **append_to_file** — Fügt Inhalt am Ende einer Datei an.
- **list_directory** — Listet den Inhalt eines Verzeichnisses auf.
- **scan_folder** — Scannt einen Ordner rekursiv nach Dateien mit bestimmten Erweiterungen.
- **get_file_info** — Gibt Informationen über eine Datei zurück (Größe, Datum etc.).
- **create_directory** — Erstellt ein neues Verzeichnis.
- **delete_file** — Löscht eine Datei oder ein leeres Verzeichnis.
- **search_files** — Durchsucht Dateien nach einem generischen Pattern (grep-like).
- **grep** — Durchsucht Dateien nach einem Pattern mit Regex-Unterstützung.
- **patch_file** — Ersetzt Zeilen in einer Datei (Zeilenbereich).
- **analyze_project** — Analysiert die Struktur und Abhängigkeiten eines Projekts.
- **add_project_to_rag** — Lädt ein Projekt in den RAG-Index für semantische Suche.
- **clear_project_rag** — Löscht den Projekt-RAG-Index.

## 🧠 KI, System & Lernen

- **save_memory** — Speichert eine Information dauerhaft im Langzeitgedächtnis.
- **search_memory** — Suche in gespeicherten Erinnerungen.
- **list_memory** — Listet alle gespeicherten Erinnerungen.
- **delete_memory** — Löscht einen spezifischen Erinnerungseintrag.
- **list_skills** — Listet alle selbstgelernten Skills auf.
- **learn_skill** — Trainiert V.I.N.C.E.N.T. manuell auf einen Tool-Aufruf.
- **use_skill** — Führt einen gelernten Skill anhand seines Keywords aus.
- **show_tool_usage** — Zeigt Statistiken zur Tool-Nutzung.
- **vincent_status** — Gibt den aktuellen Betriebszustand von V.I.N.C.E.N.T. zurück.
- **create_diagram** — Generiert Mermaid-Diagramme (Architecture, Flowchart, etc.).
- **run_python** — Führt Python-Code aus (mit Sicherheitsbeschränkungen).
- **run_command** — Führt erlaubte Kommandozeilen-Befehle aus.
