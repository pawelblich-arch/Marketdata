#!/bin/bash
# =============================================================================
# UPDATE ASSET-NAMEN
# =============================================================================
# Lädt Asset-Namen von yfinance und aktualisiert die Datenbank
# Dauer: ~10 Minuten (611 Assets × 1 Sek)
# =============================================================================

cd "$(dirname "$0")"

# Aktiviere Virtual Environment
if [ -f "/Users/pawelblicharski/TradingTool/venv/bin/activate" ]; then
    source "/Users/pawelblicharski/TradingTool/venv/bin/activate"
fi

echo "============================================================"
echo "  📝 ASSET-NAMEN UPDATE"
echo "============================================================"
echo ""
echo "⏱️  Dauer: ~10 Minuten (Rate Limit: 1 Request/Sekunde)"
echo ""
echo "Das Terminal-Fenster offen lassen!"
echo "============================================================"
echo ""

python3 scripts/update_asset_names.py

echo ""
echo "============================================================"
echo "✅ Fertig! Sie können jetzt die Web-GUI neu laden."
echo "============================================================"
echo ""

read -p "Drücken Sie Enter zum Beenden..."

exit 0
