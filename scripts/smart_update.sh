#!/bin/bash
# =============================================================================
# SMART UPDATE - Läuft nur wenn letztes Update > 23h her ist
# =============================================================================
# Dieses Script wird von launchd aufgerufen und prüft, ob ein Update nötig ist.
# =============================================================================

LOG_DIR="/Users/pawelblicharski/Software_Projekt/MarketData/logs"
LAST_RUN_FILE="$LOG_DIR/.last_update_timestamp"
CURRENT_TIME=$(date +%s)

# Erstelle Log-Dir falls nicht vorhanden
mkdir -p "$LOG_DIR"

# Prüfe wann letztes Update war
if [ -f "$LAST_RUN_FILE" ]; then
    LAST_RUN=$(cat "$LAST_RUN_FILE")
    TIME_DIFF=$((CURRENT_TIME - LAST_RUN))
    HOURS_SINCE=$((TIME_DIFF / 3600))
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Letztes Update: vor $HOURS_SINCE Stunden"
    
    # Nur ausführen wenn > 23 Stunden her
    if [ $TIME_DIFF -lt 82800 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Update übersprungen (zu früh)"
        exit 0
    fi
fi

# Update durchführen
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starte Update..."

cd "/Users/pawelblicharski/Software_Projekt/MarketData"

# Aktiviere Virtual Environment
if [ -f "/Users/pawelblicharski/TradingTool/venv/bin/activate" ]; then
    source "/Users/pawelblicharski/TradingTool/venv/bin/activate"
fi

# Führe Update aus
python3 scripts/daily_update.py

EXIT_CODE=$?

# Speichere Timestamp
if [ $EXIT_CODE -eq 0 ]; then
    echo "$CURRENT_TIME" > "$LAST_RUN_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Update erfolgreich abgeschlossen"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Update fehlgeschlagen (Exit Code: $EXIT_CODE)"
fi

exit $EXIT_CODE
