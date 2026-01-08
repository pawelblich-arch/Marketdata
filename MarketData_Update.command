#!/bin/bash
# =============================================================================
# MARKTDATEN UPDATE - Doppelklick-Starter
# =============================================================================
# Dieses Script kann per Doppelklick aus dem Finder gestartet werden.
# Es führt ein Update aller Marktdaten durch.
#
# Autor: Trading System v2
# Datum: 2026-01-08
# =============================================================================

# Farben für Terminal-Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Wechsle ins MarketData-Verzeichnis
cd "$(dirname "$0")"

# Aktiviere TradingTool Virtual Environment (falls vorhanden)
VENV_PATH="/Users/pawelblicharski/TradingTool/venv/bin/activate"
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
    echo -e "${GREEN}✅ Virtual Environment aktiviert${NC}"
fi

# Funktion: Banner anzeigen
show_banner() {
    clear
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}          📊 MARKTDATEN UPDATE GESTARTET 📊${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo -e "  Datenbank: ${GREEN}market_data.db${NC}"
    echo -e "  Zeitpunkt: $(date '+%d.%m.%Y %H:%M:%S')"
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

# Funktion: Prüfe ob Python verfügbar ist
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ FEHLER: Python3 nicht gefunden!${NC}"
        echo ""
        echo "Bitte installieren Sie Python 3:"
        echo "  https://www.python.org/downloads/"
        echo ""
        read -p "Drücken Sie Enter zum Beenden..."
        exit 1
    fi
    
    echo -e "${GREEN}✅ Python3 gefunden: $(python3 --version)${NC}"
}

# Funktion: Prüfe ob Datenbank existiert
check_database() {
    if [ ! -f "market_data.db" ]; then
        echo -e "${RED}❌ FEHLER: market_data.db nicht gefunden!${NC}"
        echo ""
        echo "Bitte führen Sie zuerst das Setup aus:"
        echo "  cd scripts && python3 create_schema.py"
        echo ""
        read -p "Drücken Sie Enter zum Beenden..."
        exit 1
    fi
    
    local size=$(du -h market_data.db | cut -f1)
    echo -e "${GREEN}✅ Datenbank gefunden: ${size}${NC}"
}

# Funktion: Prüfe ob yfinance installiert ist
check_yfinance() {
    if ! python3 -c "import yfinance" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  yfinance nicht installiert${NC}"
        echo ""
        echo -e "Installiere yfinance..."
        
        # Versuche Installation (mit fallback für system Python)
        pip3 install yfinance pyyaml --quiet 2>/dev/null || pip3 install yfinance pyyaml --break-system-packages --quiet
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ yfinance erfolgreich installiert${NC}"
        else
            echo -e "${RED}❌ Installation fehlgeschlagen${NC}"
            echo ""
            echo "Bitte installieren Sie yfinance manuell:"
            echo "  pip3 install yfinance pyyaml --break-system-packages"
            echo ""
            read -p "Drücken Sie Enter zum Beenden..."
            exit 1
        fi
    else
        echo -e "${GREEN}✅ yfinance installiert${NC}"
    fi
}

# Funktion: Update durchführen
run_update() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}🔄 STARTE UPDATE...${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    
    # Führe Python-Script aus
    python3 scripts/daily_update.py
    
    local exit_code=$?
    
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ UPDATE ERFOLGREICH ABGESCHLOSSEN!${NC}"
    else
        echo -e "${RED}❌ UPDATE MIT FEHLERN BEENDET (Exit Code: $exit_code)${NC}"
        echo ""
        echo "Prüfen Sie das Log in: logs/"
    fi
    
    echo -e "${BLUE}============================================================${NC}"
}

# Funktion: Zusammenfassung anzeigen
show_summary() {
    echo ""
    echo -e "${BLUE}📊 DATENBANK-STATISTIK:${NC}"
    echo -e "${BLUE}------------------------------------------------------------${NC}"
    
    # Nutze Python für DB-Abfragen
    python3 << EOF
import sqlite3
from datetime import datetime

conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()

# Anzahl Symbole
symbols = cursor.execute("SELECT COUNT(DISTINCT symbol) FROM price_data").fetchone()[0]
print(f"   Symbole: {symbols:,}")

# Anzahl Datenpunkte
rows = cursor.execute("SELECT COUNT(*) FROM price_data").fetchone()[0]
print(f"   Datenpunkte: {rows:,}")

# Zeitraum
date_range = cursor.execute("SELECT MIN(date), MAX(date) FROM price_data").fetchone()
if date_range[0]:
    print(f"   Zeitraum: {date_range[0]} bis {date_range[1]}")

# DB-Größe
import os
size_mb = os.path.getsize('market_data.db') / (1024 * 1024)
print(f"   Größe: {size_mb:.1f} MB")

# Letztes Update
last_update = cursor.execute("""
    SELECT MAX(completed_at) FROM update_log
""").fetchone()[0]
if last_update:
    print(f"   Letztes Update: {last_update}")

conn.close()
EOF
    
    echo -e "${BLUE}------------------------------------------------------------${NC}"
}

# Funktion: Logs anzeigen (optional)
show_logs() {
    echo ""
    echo -e "${YELLOW}📄 Möchten Sie die Log-Datei öffnen?${NC}"
    echo -e "   (j = Ja, n = Nein)"
    read -n 1 -p "   Ihre Wahl: " choice
    echo ""
    
    if [ "$choice" = "j" ] || [ "$choice" = "J" ]; then
        # Finde neuestes Log
        latest_log=$(ls -t logs/*.log 2>/dev/null | head -1)
        
        if [ -n "$latest_log" ]; then
            echo ""
            echo -e "${BLUE}Öffne Log: ${latest_log}${NC}"
            echo ""
            tail -50 "$latest_log"
        else
            echo -e "${YELLOW}Keine Log-Dateien gefunden.${NC}"
        fi
    fi
}

# =============================================================================
# HAUPTPROGRAMM
# =============================================================================

show_banner

echo -e "${YELLOW}🔍 SYSTEM-CHECK...${NC}"
echo ""

check_python
check_yfinance
check_database

echo ""
echo -e "${GREEN}✅ Alle Checks erfolgreich!${NC}"
echo ""

# Warte kurz
sleep 1

# Update durchführen
run_update

# Zusammenfassung
show_summary

# Optional: Logs anzeigen
show_logs

# Abschluss
echo ""
echo -e "${GREEN}🎉 FERTIG!${NC}"
echo ""
echo -e "${BLUE}Tipp: Sie können dieses Script jederzeit per Doppelklick starten.${NC}"
echo ""

# Warte auf Tastendruck
read -p "Drücken Sie Enter zum Beenden..."

exit 0
