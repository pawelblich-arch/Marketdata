# 📊 Zentrale Marktdaten-Datenbank

**Version:** 1.0  
**Erstellt:** 2026-01-08  
**Zweck:** Zentrale, projektübergreifende Kursdatenbank für Trading-Tools

---

## 🎯 Überblick

Diese Datenbank dient als **Single Source of Truth** für alle Marktdaten (OHLCV) und wird von mehreren Trading-Projekten genutzt.

### Vorteile
- ✅ **Keine Daten-Duplikate** über Projekte hinweg
- ✅ **Konsistente Datenqualität**
- ✅ **Ein Update-Prozess** für alle Tools
- ✅ **Einfache Backup-Strategie**

---

## 📂 Ordnerstruktur

```
MarketData/
├── market_data.db          # Hauptdatenbank (SQLite)
├── config.yaml             # Konfiguration
├── README.md               # Diese Datei
│
├── scripts/
│   ├── create_schema.py   # Erstellt DB-Schema
│   ├── migrate_from_old.py # Migration aus alter DB
│   └── daily_update.py    # Tägliches Update-Script
│
├── logs/
│   └── update_YYYYMMDD.log # Tägliche Update-Logs
│
└── backups/
    └── market_data_YYYYMMDD.db.bak # Automatische Backups
```

---

## 🗄️ Datenbank-Schema

### 1. `price_data` (OHLCV - Rohdaten)
Speichert alle Kursdaten für Aktien, Indizes, Rohstoffe, FX.

**Spalten:**
- `symbol` (TEXT): Ticker-Symbol (z.B. "AAPL", "^GSPC")
- `date` (DATE): Handelsdatum
- `open`, `high`, `low`, `close`, `adj_close` (REAL): Kursdaten
- `volume` (INTEGER): Handelsvolumen
- `data_quality` (TEXT): Qualitäts-Flag ('ok', 'gap', 'outlier')
- `source` (TEXT): Datenquelle ('yfinance', 'eodhd', etc.)

**Primary Key:** `(symbol, date)`

### 2. `asset_metadata` (Stammdaten)
Katalog aller Assets mit Metadaten.

**Spalten:**
- `symbol` (TEXT): Ticker-Symbol
- `name`, `asset_type`, `exchange`, `sector`, `industry`
- `first_date`, `last_date`: Verfügbarer Zeitraum
- `is_active` (INTEGER): Aktiv? (1/0)

### 3. `indicators_cache` (Pre-calculated)
Cache für langsame Indikatoren (Saisonalität, RSL, etc.)

**Spalten:**
- `symbol`, `date`, `indicator_name`, `value`
- `calculation_version`: Versioning für Formeln

### 4. `data_quality_log`
Protokolliert Datenqualitäts-Probleme.

### 5. `update_log`
Tracking aller Update-Läufe.

---

## 🚀 Setup & Initialisierung

### 1. Schema erstellen

```bash
cd /Users/pawelblicharski/Software_Projekt/MarketData/scripts
python3 create_schema.py
```

**Output:**
```
✅ Schema erfolgreich erstellt!
   Datenbank: ../market_data.db
   Tabellen: 5
```

### 2. Migration aus alter Datenbank (optional)

Falls Sie bereits eine `trading_strategies.db` haben:

```bash
python3 migrate_from_old.py
```

**Was passiert:**
- ✅ Backup der alten DB
- ✅ Migration aller OHLCV-Daten → `price_data`
- ✅ Automatische Asset-Katalogisierung → `asset_metadata`

### 3. Erstes Daten-Update

```bash
python3 daily_update.py
```

**Was passiert:**
- ✅ Lädt fehlende Daten für alle aktiven Assets
- ✅ Erstellt Log-Datei in `logs/`
- ✅ Speichert Update-Status in DB

---

## 📅 Automatisierung (Cron-Job)

Für **tägliche** Updates um 02:00 Uhr:

```bash
# Crontab öffnen
crontab -e

# Folgende Zeile hinzufügen:
0 2 * * * /usr/bin/python3 /Users/pawelblicharski/Software_Projekt/MarketData/scripts/daily_update.py >> /Users/pawelblicharski/Software_Projekt/MarketData/logs/cron.log 2>&1
```

---

## 🔌 Nutzung in Projekten

### Python-Zugriff

```python
import sqlite3
from pathlib import Path

# Verbindung zur zentralen DB
DB_PATH = "/Users/pawelblicharski/Software_Projekt/MarketData/market_data.db"
conn = sqlite3.connect(DB_PATH)

# Beispiel: Lade AAPL Kurse für 2025
df = pd.read_sql_query("""
    SELECT date, open, high, low, close, volume
    FROM price_data
    WHERE symbol = 'AAPL'
      AND date >= '2025-01-01'
    ORDER BY date
""", conn)
```

### Read-Only Zugriff (empfohlen)

Projekte sollten nur **lesen**, nicht schreiben:

```python
# config.yaml im Projekt
database:
  market_data_path: "/Users/pawelblicharski/Software_Projekt/MarketData/market_data.db"
  read_only: true  # Verhindert versehentliche Änderungen
```

---

## 🛠️ Wartung & Backup

### Manuelles Backup

```bash
cd /Users/pawelblicharski/Software_Projekt/MarketData
cp market_data.db backups/market_data_$(date +%Y%m%d).db
```

### Datenbank-Größe prüfen

```bash
sqlite3 market_data.db "
SELECT 
    'price_data' as table_name,
    COUNT(*) as rows,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM price_data WHERE 1=1)), 2) as percent
FROM price_data
UNION ALL
SELECT 'asset_metadata', COUNT(*), NULL FROM asset_metadata
"
```

### Alte Logs löschen (älter als 90 Tage)

```bash
find logs/ -name "*.log" -mtime +90 -delete
```

---

## 📊 Datenquellen

**Aktuell:** yfinance (kostenlos, 20+ Jahre Historie)  
**Geplant:** EODHD, Alpha Vantage (für zusätzliche Assets)

### Asset-Universum

| Kategorie | Anzahl | Beispiele |
|-----------|--------|-----------|
| **Indizes** | ~10 | ^GSPC, ^DJI, ^IXIC, ^GDAXI |
| **S&P 500** | 500 | AAPL, MSFT, GOOGL, ... |
| **Nasdaq 100** | 100 | TSLA, NVDA, META, ... |
| **DAX** | 40 | SAP, SIE, VOW3, ... |
| **Rohstoffe** | ~10 | GC=F (Gold), SI=F (Silber), CL=F (Öl) |
| **FX** | ~5 | EURUSD=X, GBPUSD=X, ... |

---

## ⚠️ Wichtige Hinweise

### Datenqualität

- ✅ **auto_adjust=True** bei yfinance (Split/Dividenden-bereinigt)
- ✅ **Outlier-Detection** (Änderungen >20% werden geloggt)
- ✅ **Gap-Detection** (Fehlende Handelstage werden markiert)

### Performance

- **Batch-Updates:** 100 Symbole pro Durchlauf
- **Rate Limit:** 1 Request/Sekunde (yfinance)
- **Caching:** Häufig genutzte Indikatoren in `indicators_cache`

### Speicherplatz

- **500 Assets × 20 Jahre × 252 Tage:** ~500 MB (OHLCV)
- **Indikatoren-Cache:** ~200 MB
- **Empfohlen:** Min. 2 GB freier Speicher

---

## 🆘 Troubleshooting

### Problem: "Database is locked"

**Ursache:** Gleichzeitiger Zugriff von mehreren Prozessen.  
**Lösung:** Nutze read-only Verbindungen in Projekten.

### Problem: "No data for symbol XYZ"

**Ursache:** Symbol nicht aktiv oder delisted.  
**Lösung:** Prüfe `asset_metadata` und setze `is_active=0`.

### Problem: Update dauert zu lange

**Ursache:** Zu viele Symbole.  
**Lösung:** Anpassen in `config.yaml` → `batch_size` erhöhen.

---

## 📞 Support

Bei Fragen oder Problemen:
- **Log-Dateien prüfen:** `logs/update_YYYYMMDD.log`
- **Datenqualität prüfen:** `SELECT * FROM data_quality_log ORDER BY detected_at DESC LIMIT 50`

---

## 📝 Changelog

### Version 1.0 (2026-01-08)
- ✅ Initiales Setup
- ✅ Schema-Erstellung
- ✅ Migrations-Script
- ✅ Daily-Update-Script
- ✅ Dokumentation

---

**Viel Erfolg mit Ihrer Trading-Datenbank! 🚀**
