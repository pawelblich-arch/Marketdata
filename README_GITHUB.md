# 📊 MarketData Infrastructure

Zentrale Marktdaten-Datenbank für Trading-Tools

---

## 🎯 Zweck

Diese Komponente stellt eine **zentrale, projektübergreifende** Marktdaten-Datenbank bereit:
- **Single Source of Truth** für OHLCV-Daten
- **Shared** von mehreren Trading-Tools
- **Automatische Updates** via launchd/Cron
- **Web-GUI** zur Verwaltung

---

## 📂 Struktur

```
MarketData/
├── market_data.db          # Datenbank (NICHT in Git!)
├── schema.sql              # DB-Schema (in Git)
├── config.yaml             # Konfiguration
├── scripts/                # Management-Scripts
│   ├── create_schema.py   # Schema erstellen
│   ├── daily_update.py    # Tägliches Update
│   ├── manage_assets.py   # Asset-Verwaltung (CLI)
│   └── asset_manager_web.py # Asset-Manager (Web-GUI)
├── logs/                   # Update-Logs
└── backups/                # Lokale Backups
```

---

## 🚀 Setup

### 1. Repository klonen

```bash
git clone https://github.com/USERNAME/MarketData-Infrastructure.git
cd MarketData-Infrastructure
```

### 2. Datenbank initialisieren

```bash
python3 scripts/create_schema.py
```

### 3. Erste Daten laden

```bash
# Option A: Migration aus bestehender DB
python3 scripts/migrate_from_old.py

# Option B: Fresh Start
python3 scripts/daily_update.py
```

### 4. Auto-Update einrichten

```bash
# macOS (launchd)
launchctl load ~/Library/LaunchAgents/com.tradingsystem.marketdata.plist

# Linux (cron)
crontab -e
# Füge hinzu: 0 2 * * * /path/to/MarketData/scripts/daily_update.py
```

---

## 🛠️ Nutzung

### Web-GUI starten

```bash
streamlit run scripts/asset_manager_web.py
```

**Funktionen:**
- Assets anzeigen/filtern/suchen
- Assets hinzufügen/deaktivieren
- Metadaten verwalten
- Datenqualität prüfen

### CLI-Verwaltung

```bash
# Assets auflisten
python3 scripts/manage_assets.py list

# Asset hinzufügen
python3 scripts/manage_assets.py add AAPL --type stock --name "Apple Inc"

# Asset-Details
python3 scripts/manage_assets.py show AAPL

# Asset deaktivieren
python3 scripts/manage_assets.py remove XYZ
```

---

## 📊 Datenbank-Schema

### Tabellen

| Tabelle | Zweck | Größe (Beispiel) |
|---------|-------|------------------|
| `price_data` | OHLCV-Rohdaten | ~500 MB |
| `asset_metadata` | Asset-Katalog | ~1 MB |
| `indicators_cache` | Pre-calculated Indikatoren | ~200 MB |
| `data_quality_log` | Qualitäts-Protokoll | ~1 MB |
| `update_log` | Update-Tracking | ~1 MB |

### Schema anzeigen

```bash
./scripts/export_schema.sh
cat schema.sql
```

---

## 🔌 Integration in andere Projekte

### Python

```python
import sqlite3
from pathlib import Path

# Pfad zur zentralen DB
DB_PATH = Path.home() / "Software_Projekt/MarketData/market_data.db"

# Verbindung
conn = sqlite3.connect(DB_PATH)

# Daten laden
import pandas as pd
df = pd.read_sql_query("""
    SELECT * FROM price_data 
    WHERE symbol = 'AAPL' 
    AND date >= '2025-01-01'
""", conn)
```

### Config-Datei (YAML)

```yaml
# config/data_sources.yaml in Ihrem Projekt
market_data:
  db_path: "~/Software_Projekt/MarketData/market_data.db"
  read_only: true
```

---

## 💾 Backup-Strategie

### Automatisches Backup

```bash
# Täglich (nach Update)
cp market_data.db backups/market_data_$(date +%Y%m%d).db

# Wöchentlich komprimiert
tar -czf backups/market_data_$(date +%Y%m%d).tar.gz market_data.db
```

### Cloud-Backup

**WICHTIG:** Datenbank-Datei (865 MB) **NICHT** in Git!

**Alternativen:**
- Lokales Backup (Time Machine, externe Festplatte)
- Cloud (Google Drive, Dropbox) - nur die DB-Datei
- NAS/Server

---

## 📈 Daten-Statistik

| Metrik | Wert |
|--------|------|
| Assets | 611 |
| Datenpunkte | 5.036.652 |
| Zeitraum | 1962-2026 (64 Jahre) |
| DB-Größe | 865.6 MB |
| Asset-Typen | Stocks, Indizes, Rohstoffe, FX |

---

## 🔄 Update-Frequenz

- **Automatisch:** Täglich 02:00 Uhr (launchd)
- **Manuell:** `MarketData_Update.command` (Doppelklick)
- **Duration:** ~10-15 Min (611 Assets × 1 Sek Rate Limit)

---

## 🛡️ Datenqualität

### Qualitäts-Checks

- ✅ **Lücken-Erkennung** (> 7 Tage = Warnung)
- ✅ **Outlier-Detection** (> 20% Tagesänderung)
- ✅ **OHLCV-Vollständigkeit** (alle Felder vorhanden?)
- ✅ **Qualitäts-Score** (0-100%)

### Prüfung ausführen

```bash
python3 scripts/upgrade_schema.py
```

---

## 📝 Lizenz

Privates Projekt - Nicht für öffentliche Nutzung

---

## 🆘 Support

Bei Fragen oder Problemen:
- **Logs prüfen:** `logs/update_YYYYMMDD.log`
- **Schema prüfen:** `sqlite3 market_data.db .schema`
- **Health Check:** `python3 scripts/manage_assets.py list`

---

## 📚 Weiterführende Dokumentation

- [Schema-Details](schema.sql)
- [Konfiguration](config.yaml)
- [Update-Logs](logs/)

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2026-01-08
