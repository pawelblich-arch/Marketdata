#!/bin/bash
# =============================================================================
# Exportiert DB-Schema (OHNE Daten) für Git
# =============================================================================

cd "$(dirname "$0")/.."

echo "📊 Exportiere Datenbank-Schema..."

# Exportiere nur Schema (keine Daten)
sqlite3 market_data.db .schema > schema.sql

echo "✅ Schema exportiert: schema.sql"
echo ""
echo "📏 Dateigröße:"
ls -lh schema.sql

echo ""
echo "💡 Diese Datei kann in Git committed werden!"
echo "   (Enthält nur Struktur, keine Daten)"
