#!/bin/bash
# =============================================================================
# Git Repository initialisieren für MarketData Infrastructure
# =============================================================================

cd "$(dirname "$0")"

echo "============================================================"
echo "  GIT REPOSITORY INITIALISIERUNG"
echo "============================================================"
echo ""

# 1. Git initialisieren
echo "1️⃣  Initialisiere Git Repository..."
git init

# 2. .gitignore prüfen
if [ -f ".gitignore" ]; then
    echo "✅ .gitignore vorhanden"
else
    echo "❌ .gitignore fehlt!"
    exit 1
fi

# 3. Schema exportieren
echo ""
echo "2️⃣  Exportiere Datenbank-Schema..."
./scripts/export_schema.sh

# 4. Dateien hinzufügen
echo ""
echo "3️⃣  Füge Dateien hinzu..."

git add .gitignore
git add schema.sql
git add config.yaml
git add scripts/*.py
git add scripts/*.sh
git add *.command
git add README_GITHUB.md

echo "✅ Dateien hinzugefügt"

# 5. Status anzeigen
echo ""
echo "4️⃣  Git Status:"
git status

echo ""
echo "============================================================"
echo "✅ REPOSITORY BEREIT"
echo "============================================================"
echo ""
echo "📋 NÄCHSTE SCHRITTE:"
echo ""
echo "1. Ersten Commit erstellen:"
echo "   git commit -m 'Initial commit: MarketData Infrastructure'"
echo ""
echo "2. GitHub Repository erstellen:"
echo "   https://github.com/new"
echo ""
echo "3. Remote hinzufügen:"
echo "   git remote add origin https://github.com/USERNAME/MarketData-Infrastructure.git"
echo ""
echo "4. Push:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "============================================================"
