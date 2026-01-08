# 📊 MarketData Infrastructure

**Zentrale Marktdaten-Datenbank für Trading-Tools**

---

## 🎯 Überblick

Die **MarketData Infrastructure** ist eine professionelle, zentrale Datenbank für:
- **OHLCV-Daten** (Open, High, Low, Close, Volume) für Aktien, Indizes, Rohstoffe
- **Sentiment-Indikatoren** (VIX, VDAX, Fear & Greed, Put/Call Ratio, AAII)
- **Marktbreite-Kennzahlen** (New Highs/Lows, Advance/Decline, etc.)

**Warum zentral?**
- ✅ Mehrere Applikationen nutzen dieselbe Datenquelle
- ✅ Keine Redundanz, keine Inkonsistenzen
- ✅ Automatische tägliche Updates
- ✅ Professionelles Schema mit Versionierung

---

## 📂 Struktur

```
MarketData/
├── market_data.db              # Hauptdatenbank (NICHT auf GitHub!)
├── config.yaml                 # Konfiguration
├── schema.sql                  # Versioniertes Schema
├── scripts/
│   ├── create_schema.py        # Datenbank initialisieren
│   ├── daily_update.py         # OHLCV + Sentiment Update
│   ├── update_sentiment_external.py  # Externe APIs (Fear & Greed, etc.)
│   ├── asset_manager_web.py    # Streamlit GUI
│   └── ...
├── logs/                       # Update-Logs
└── backups/                    # DB-Backups
```

---

## 🗄️ Datenbank-Schema

### **Tabellen:**

| Tabelle | Zweck | Anzahl Zeilen |
|---------|-------|---------------|
| `price_data` | OHLCV-Rohdaten | ~5 Millionen |
| `asset_metadata` | Asset-Stammdaten | ~800 |
| `sentiment_data` | VIX, Fear & Greed, etc. | ~50.000 |
| `market_breadth` | Berechnete Marktbreite (Cache) | Leer (für TradingTool) |
| `indicators_cache` | Pre-calculated Indikatoren | ~10 Millionen |
| `data_quality_log` | Datenqualitäts-Tracking | ~5.000 |
| `update_log` | Update-Historie | ~500 |

### **Schema Export:**

```bash
sqlite3 market_data.db .dump > schema.sql
```

---

## 🚀 Installation & Setup

### **1. Repository klonen:**

```bash
git clone https://github.com/pawelblich-arch/Marketdata.git
cd Marketdata
```

### **2. Datenbank initialisieren:**

```bash
python3 scripts/create_schema.py
```

### **3. Erste Daten laden (Migration):**

Falls Sie die alte `trading_strategies.db` haben:

```bash
python3 scripts/migrate_from_old.py
```

Oder manuell Assets hinzufügen und updaten:

```bash
./MarketData_Update.command
```

---

## 🔄 Tägliche Updates

### **Automatisch (via launchd):**

```bash
# Service installieren
cp com.tradingsystem.marketdata.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.tradingsystem.marketdata.plist

# Status prüfen
launchctl list | grep marketdata
```

**Update läuft täglich um 02:00 Uhr und bei System-Start (falls verpasst).**

### **Manuell:**

```bash
# OHLCV-Daten + VIX/VDAX/etc.
./MarketData_Update.command

# Externe Sentiment (Fear & Greed, AAII, Put/Call)
./Update_Sentiment_External.command
```

---

## 🖥️ Asset Manager (GUI)

**Streamlit Web-GUI zur Verwaltung:**

```bash
./MarketData_Manager.command
```

**Features:**
- 📊 **6 Tabellen:** Indices, Rohstoffe, Sentiment, S&P 500, Nasdaq, DAX
- 📈 **Live-Statistiken:** Datenpunkte, Qualität, letztes Update
- 🔍 **Sentiment-Übersicht:** VIX, VDAX, Fear & Greed mit letzten Werten
- 🎨 **Moderne UI:** Keine "Deploy"-Buttons, clean & professionell

**Screenshot:**

![Asset Manager GUI](docs/screenshot_gui.png)

---

## 📊 Sentiment-Indikatoren

### **Via yfinance (täglich automatisch):**

| Indikator | Symbol | Beschreibung |
|-----------|--------|--------------|
| **VIX** | `^VIX` | S&P 500 Volatility Index |
| **VDAX** | `^VDAX` | DAX Volatility Index |
| **VSTOXX** | `^VSTOXX` | EuroStoxx 50 Volatility |
| **OVX** | `^OVX` | Oil Volatility Index |
| **GVZ** | `^GVZ` | Gold Volatility Index |
| **EVZ** | `^EVZ` | Emerging Markets Volatility |
| **VXN** | `^VXN` | Nasdaq 100 Volatility |
| **RVX** | `^RVX` | Russell 2000 Volatility |

### **Externe APIs (in Entwicklung):**

| Indikator | Quelle | Status |
|-----------|--------|--------|
| **Fear & Greed Index** | CNN Money | ⚠️ Cloudflare-Schutz |
| **AAII Sentiment** | AAII.com | ⚠️ Keine öffentliche API |
| **Put/Call Ratio** | CBOE | ⚠️ Symbole nicht über yfinance |

**💡 Lösung:** Web-Scraping oder alternative APIs (AlphaVantage, Quandl)

---

## 🛠️ Entwicklung

### **Schema erweitern:**

```bash
# Neues Upgrade-Script erstellen
python3 scripts/upgrade_schema_NEW.py
```

### **Neue Asset-Gruppe hinzufügen:**

```python
# In asset_manager_web.py
asset_groups = ["sp500", "nasdaq100", "dax", "YOUR_NEW_GROUP"]
```

### **Backup erstellen:**

```bash
# Automatisch bei Updates
# Manuell:
cp market_data.db backups/market_data_$(date +%Y%m%d).db
```

---

## 📝 API-Zugriff (für TradingTool)

```python
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "Software_Projekt" / "MarketData" / "market_data.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# OHLCV-Daten abfragen
df = pd.read_sql_query("""
    SELECT * FROM price_data 
    WHERE symbol = 'AAPL' 
    AND date >= '2020-01-01'
    ORDER BY date
""", conn)

# Sentiment-Daten abfragen
sentiment = pd.read_sql_query("""
    SELECT * FROM sentiment_data 
    WHERE indicator = 'VIX'
    AND date >= '2020-01-01'
    ORDER BY date
""", conn)

conn.close()
```

---

## 🔒 Sicherheit

- ✅ **Datenbank NICHT auf GitHub** (`.gitignore`)
- ✅ **Schema versioniert** (`schema.sql`)
- ✅ **Automatische Backups** bei jedem Update
- ✅ **Separater DB-Pfad** (außerhalb des TradingTool-Repos)

---

## 📊 Statistiken (Stand: 08.01.2026)

| Metrik | Wert |
|--------|------|
| **Datenbank-Größe** | 1.2 GB |
| **OHLCV-Datenpunkte** | ~5 Millionen |
| **Assets** | ~800 (aktiv) |
| **Sentiment-Indikatoren** | 8 (via yfinance) |
| **Update-Frequenz** | Täglich (02:00 Uhr) |
| **Historische Daten** | Seit 1990 |

---

## 🆘 Troubleshooting

### **Problem: Update schlägt fehl**

```bash
# Logs prüfen
cat logs/update_$(date +%Y%m%d).log

# Manuelle Ausführung mit Fehler-Details
cd /Users/pawelblicharski/Software_Projekt/MarketData
source /path/to/venv/bin/activate
python3 scripts/daily_update.py
```

### **Problem: GUI startet nicht**

```bash
# Streamlit neu installieren
pip install --upgrade streamlit

# Port ändern (falls 8501 belegt)
streamlit run scripts/asset_manager_web.py --server.port 8502
```

### **Problem: Sentiment-Daten fehlen**

```bash
# Schema-Upgrade ausführen
python3 scripts/upgrade_schema_sentiment.py

# Externe Sentiment-Update testen
python3 scripts/update_sentiment_external.py
```

---

## 🤝 Beiträge

Dieses Repository ist Teil eines privaten Trading-Systems. Pull Requests sind willkommen für:
- 🐛 Bug-Fixes
- 📝 Dokumentations-Verbesserungen
- 🚀 Performance-Optimierungen
- 🔌 Neue Datenquellen-Integrationen

---

## 📄 Lizenz

Privates Projekt. Alle Rechte vorbehalten.

---

## 📧 Kontakt

Bei Fragen oder Problemen: [GitHub Issues](https://github.com/pawelblich-arch/Marketdata/issues)

---

**🎉 Happy Trading!**
