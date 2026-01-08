#!/bin/bash
# =============================================================================
# Erstellt eine native macOS .app für den Asset Manager
# =============================================================================

APP_NAME="MarketData Manager"
APP_DIR="/Users/pawelblicharski/Software_Projekt/MarketData"
SCRIPT_DIR="$APP_DIR/scripts"

# Erstelle .app Struktur
APP_PATH="$APP_DIR/$APP_NAME.app"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Info.plist
cat > "$APP_PATH/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>MarketDataManager</string>
    <key>CFBundleName</key>
    <string>MarketData Manager</string>
    <key>CFBundleIdentifier</key>
    <string>com.tradingsystem.marketdatamanager</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
EOF

# Hauptscript (verwendet System Python mit Tkinter)
cat > "$APP_PATH/Contents/MacOS/MarketDataManager" << 'EOF'
#!/bin/bash

# Wechsle ins MarketData-Verzeichnis
cd "/Users/pawelblicharski/Software_Projekt/MarketData"

# Nutze System Python (hat Tkinter)
/usr/bin/python3 scripts/asset_manager_gui.py

EOF

# Mache ausführbar
chmod +x "$APP_PATH/Contents/MacOS/MarketDataManager"

echo "✅ Native macOS App erstellt!"
echo "📂 Pfad: $APP_PATH"
echo ""
echo "Sie können die App jetzt wie jedes andere Mac-Programm starten:"
echo "  - Doppelklick im Finder"
echo "  - In den Programme-Ordner verschieben"
echo "  - Im Dock ablegen"
