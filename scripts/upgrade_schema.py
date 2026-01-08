#!/usr/bin/env python3
"""
Erweitert das Datenbank-Schema um zusätzliche Felder:
- timeframe (5min, 15min, 1h, 1d, 1w)
- asset_group (sp500, nasdaq100, dax, etc.)
- has_ohlc, has_volume (Daten-Vollständigkeit)

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "market_data.db"


def upgrade_schema():
    """Fügt neue Spalten zur asset_metadata Tabelle hinzu."""
    
    print("="*70)
    print("DATENBANK-SCHEMA UPGRADE")
    print("="*70)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Prüfe welche Spalten schon existieren
    columns = cursor.execute("PRAGMA table_info(asset_metadata)").fetchall()
    existing_columns = [col[1] for col in columns]
    
    print(f"Vorhandene Spalten: {len(existing_columns)}")
    
    # Füge neue Spalten hinzu (falls nicht vorhanden)
    new_columns = [
        ("timeframe", "TEXT DEFAULT '1d'", "Zeitrahmen der Daten (5min, 15min, 1h, 1d, 1w)"),
        ("asset_group", "TEXT", "Asset-Gruppe (sp500, nasdaq100, dax, etc.)"),
        ("has_ohlc", "INTEGER DEFAULT 1", "Sind OHLC-Daten vorhanden? (1=ja, 0=nein)"),
        ("has_volume", "INTEGER DEFAULT 1", "Sind Volume-Daten vorhanden? (1=ja, 0=nein)"),
        ("data_quality_score", "REAL DEFAULT 1.0", "Qualitäts-Score (0.0-1.0)")
    ]
    
    added = 0
    for col_name, col_def, description in new_columns:
        if col_name not in existing_columns:
            print(f"  → Füge Spalte hinzu: {col_name} ({description})")
            cursor.execute(f"ALTER TABLE asset_metadata ADD COLUMN {col_name} {col_def}")
            added += 1
        else:
            print(f"  ✓ Spalte existiert bereits: {col_name}")
    
    conn.commit()
    
    print()
    print(f"✅ {added} neue Spalten hinzugefügt!")
    
    # Aktualisiere asset_group basierend auf vorhandenen Daten
    print()
    print("🔄 Aktualisiere asset_group...")
    
    # Bekannte Asset-Gruppen
    groups = {
        'sp500': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'V', 'JPM'],
        'nasdaq100': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'PEP'],
        'dax': ['SAP', 'SIE', 'ALV', 'DTE', 'MBG', 'BMW', 'VOW3', 'BAS', 'EOAN', 'ADS'],
        'index': ['^GSPC', '^DJI', '^IXIC', '^RUT', '^GDAXI', '^STOXX50E', '^N225', '^HSI'],
        'commodity': ['GC=F', 'SI=F', 'CL=F', 'NG=F', 'HG=F'],
        'fx': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X']
    }
    
    updated = 0
    for group, symbols in groups.items():
        for symbol in symbols:
            cursor.execute("""
                UPDATE asset_metadata 
                SET asset_group = ?
                WHERE symbol = ? AND asset_group IS NULL
            """, (group, symbol))
            if cursor.rowcount > 0:
                updated += cursor.rowcount
    
    conn.commit()
    
    print(f"✅ {updated} Assets mit Gruppen versehen!")
    
    # Prüfe Daten-Vollständigkeit
    print()
    print("🔍 Prüfe Daten-Vollständigkeit...")
    
    assets = cursor.execute("SELECT symbol FROM asset_metadata WHERE is_active = 1").fetchall()
    
    checked = 0
    for (symbol,) in assets:
        # Prüfe ob OHLC vorhanden
        has_data = cursor.execute("""
            SELECT 
                COUNT(*) as cnt,
                SUM(CASE WHEN open IS NOT NULL AND high IS NOT NULL 
                             AND low IS NOT NULL AND close IS NOT NULL THEN 1 ELSE 0 END) as has_ohlc_cnt,
                SUM(CASE WHEN volume IS NOT NULL AND volume > 0 THEN 1 ELSE 0 END) as has_volume_cnt
            FROM price_data
            WHERE symbol = ?
        """, (symbol,)).fetchone()
        
        if has_data and has_data[0] > 0:
            total = has_data[0]
            has_ohlc = 1 if has_data[1] == total else 0
            has_volume = 1 if has_data[2] > 0 else 0
            quality = (has_data[1] / total + has_data[2] / total) / 2 if total > 0 else 0
            
            cursor.execute("""
                UPDATE asset_metadata 
                SET has_ohlc = ?, has_volume = ?, data_quality_score = ?
                WHERE symbol = ?
            """, (has_ohlc, has_volume, quality, symbol))
            
            checked += 1
    
    conn.commit()
    
    print(f"✅ {checked} Assets geprüft!")
    
    # Zusammenfassung
    print()
    print("="*70)
    print("UPGRADE ABGESCHLOSSEN")
    print("="*70)
    
    # Zeige neue Struktur
    columns_after = cursor.execute("PRAGMA table_info(asset_metadata)").fetchall()
    print(f"\nAnzahl Spalten: {len(columns_after)}")
    print("\nNeue Spalten:")
    for col in columns_after:
        if col[1] in [c[0] for c in new_columns]:
            print(f"  - {col[1]} ({col[2]})")
    
    conn.close()


if __name__ == "__main__":
    try:
        upgrade_schema()
        print("\n🎉 Schema-Upgrade erfolgreich!")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
