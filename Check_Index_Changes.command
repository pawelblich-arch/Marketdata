#!/bin/zsh

# Pfad zum Virtual Environment des Hauptprojekts
VENV_PATH="/Users/pawelblicharski/TradingTool/venv/bin/activate"

# Pfad zum Python-Script
SCRIPT_PATH="$(dirname "$0")/scripts/check_index_constituents.py"

echo "============================================================"
echo "  🔍 INDEX CONSTITUENTS CHECK"
echo "============================================================"
echo "Zeitpunkt: $(date)"
echo ""

# Prüfen, ob das venv existiert und aktivieren
if [ -f "$VENV_PATH" ]; then
    echo "✅ Virtual Environment aktiviert: $VENV_PATH"
    source "$VENV_PATH"
else
    echo "⚠️  Virtual Environment nicht gefunden: $VENV_PATH"
fi

# Führe das Python-Script aus
python3 "$SCRIPT_PATH" "$@"

EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ INDEX-CHECK ABGESCHLOSSEN (Erfolgreich)"
else
    echo "❌ INDEX-CHECK ABGESCHLOSSEN (Fehler: $EXIT_CODE)"
fi
echo "============================================================"

# Halte das Terminal offen
if [[ -t 0 ]]; then
    echo "Drücken Sie Enter zum Beenden..."
    read
fi

exit $EXIT_CODE
