#!/bin/zsh

# Pfad zum Virtual Environment des Hauptprojekts
VENV_PATH="/Users/pawelblicharski/TradingTool/venv/bin/activate"

# Pfad zum Python-Script
SCRIPT_PATH="$(dirname "$0")/scripts/update_sentiment_external.py"

# Log-Verzeichnis
LOG_DIR="/Users/pawelblicharski/Software_Projekt/MarketData/logs"
mkdir -p "$LOG_DIR"

echo "============================================================"
echo "  📊 EXTERNE SENTIMENT-DATEN UPDATE"
echo "============================================================"
echo "Zeitpunkt: $(date)"
echo ""

# Prüfen, ob das venv existiert und aktivieren
if [ -f "$VENV_PATH" ]; then
    echo "✅ Virtual Environment aktiviert: $VENV_PATH"
    source "$VENV_PATH"
else
    echo "⚠️  Virtual Environment nicht gefunden: $VENV_PATH"
    echo "    Versuche, Python direkt auszuführen (kann zu Problemen führen)."
fi

# Führe das Python-Script aus
python3 "$SCRIPT_PATH" "$@"

EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SENTIMENT-UPDATE ABGESCHLOSSEN (Erfolgreich)"
else
    echo "❌ SENTIMENT-UPDATE ABGESCHLOSSEN (Fehler: $EXIT_CODE)"
fi
echo "============================================================"

# Halte das Terminal offen, wenn es interaktiv gestartet wurde
if [[ -t 0 ]]; then
    echo "Drücken Sie Enter zum Beenden..."
    read
fi

exit $EXIT_CODE
