#!/bin/bash
# =============================================================================
# ASSET MANAGER - WEB GUI (Streamlit)
# =============================================================================
# Moderne Web-Oberfläche zur Verwaltung der MarketData Assets
# Öffnet automatisch im Browser
# =============================================================================

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")"

# Aktiviere Virtual Environment (falls vorhanden)
if [ -f "/Users/pawelblicharski/TradingTool/venv/bin/activate" ]; then
    source "/Users/pawelblicharski/TradingTool/venv/bin/activate"
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       📊 MarketData Asset Manager (Web GUI)${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${GREEN}✅ Starte Streamlit...${NC}"
echo -e "${GREEN}🌐 Browser öffnet sich automatisch${NC}"
echo ""
echo -e "${BLUE}Zum Beenden: Drücken Sie Ctrl+C${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Starte Streamlit (öffnet automatisch Browser)
streamlit run scripts/asset_manager_web.py \
    --server.port 8501 \
    --server.headless false \
    --browser.gatherUsageStats false

exit 0
