#!/bin/zsh

# Pfad zum Virtual Environment
VENV_PATH="/Users/pawelblicharski/TradingTool/venv/bin/activate"

# Pfad zum Script
SCRIPT_PATH="$(dirname "$0")/scripts/auto_sync_indices.py"

echo "============================================================"
echo "  🔄 AUTOMATISCHE INDEX-SYNCHRONISATION"
echo "============================================================"
echo "Zeitpunkt: $(date)"
echo ""

# Aktiviere venv
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    echo "⚠️  Virtual Environment nicht gefunden"
fi

# Führe Script aus
python3 "$SCRIPT_PATH"

EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SYNCHRONISATION ABGESCHLOSSEN"
else
    echo "❌ FEHLER: $EXIT_CODE"
fi
echo "============================================================"

# Terminal offen halten
if [[ -t 0 ]]; then
    echo "Drücken Sie Enter zum Beenden..."
    read
fi

exit $EXIT_CODE
