#!/usr/bin/env python3
"""
Fügt wichtige Rohstoffe zur MarketData-Datenbank hinzu.
Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "market_data.db"

# Wichtige Rohstoffe mit yfinance-Symbolen
COMMODITIES = [
    # Edelmetalle
    ('GC=F', 'Gold Futures', 'commodity', 'commodity'),
    ('SI=F', 'Silver Futures', 'commodity', 'commodity'),
    ('PL=F', 'Platinum Futures', 'commodity', 'commodity'),
    ('PA=F', 'Palladium Futures', 'commodity', 'commodity'),
    
    # Energie
    ('CL=F', 'Crude Oil WTI Futures', 'commodity', 'commodity'),
    ('BZ=F', 'Brent Oil Futures', 'commodity', 'commodity'),
    ('NG=F', 'Natural Gas Futures', 'commodity', 'commodity'),
    
    # Agrar
    ('ZC=F', 'Corn Futures', 'commodity', 'commodity'),
    ('ZW=F', 'Wheat Futures', 'commodity', 'commodity'),
    ('ZS=F', 'Soybean Futures', 'commodity', 'commodity'),
    
    # Weitere
    ('HG=F', 'Copper Futures', 'commodity', 'commodity'),
]

def add_commodities():
    """Fügt Rohstoffe zur Datenbank hinzu."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("📊 Füge Rohstoffe zur Datenbank hinzu...\n")
    
    added = 0
    skipped = 0
    
    for symbol, name, asset_type, asset_group in COMMODITIES:
        try:
            cursor.execute("""
                INSERT INTO asset_metadata 
                (symbol, name, asset_type, asset_group, timeframe, is_active)
                VALUES (?, ?, ?, ?, '1d', 1)
            """, (symbol, name, asset_type, asset_group))
            
            print(f"   ✅ {symbol:15} - {name}")
            added += 1
            
        except sqlite3.IntegrityError:
            print(f"   ⏭️  {symbol:15} - Existiert bereits")
            skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Fertig!")
    print(f"   Hinzugefügt: {added}")
    print(f"   Übersprungen: {skipped}")
    print(f"\n💡 Tipp: Führen Sie 'MarketData_Update.command' aus, um Daten zu laden!")
    
    return added, skipped


if __name__ == "__main__":
    add_commodities()
