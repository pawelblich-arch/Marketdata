#!/usr/bin/env python3
"""
Aktualisiert Asset-Metadaten automatisch von yfinance.
- Name
- Sektor
- Industrie
- Exchange
- Währung

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import yfinance as yf
from pathlib import Path
import time

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "market_data.db"


def update_metadata():
    """Lädt und aktualisiert Asset-Metadaten von yfinance."""
    
    print("="*70)
    print("ASSET-METADATEN UPDATE")
    print("="*70)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hole alle aktiven Assets
    assets = cursor.execute("""
        SELECT symbol FROM asset_metadata 
        WHERE is_active = 1
        ORDER BY symbol
    """).fetchall()
    
    print(f"Assets zu aktualisieren: {len(assets)}")
    print()
    
    if not assets:
        print("⚠️  Keine aktiven Assets gefunden!")
        conn.close()
        return
    
    updated = 0
    errors = 0
    
    for i, (symbol,) in enumerate(assets, 1):
        try:
            print(f"[{i}/{len(assets)}] {symbol:<12} ", end="", flush=True)
            
            # Hole Info von yfinance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extrahiere Metadaten
            name = (
                info.get('longName') or 
                info.get('shortName') or 
                info.get('name') or 
                None
            )
            
            sector = info.get('sector')
            industry = info.get('industry')
            exchange = info.get('exchange') or info.get('exchangeName')
            currency = info.get('currency') or info.get('financialCurrency')
            
            # Update in DB (nur wenn Daten vorhanden)
            update_fields = []
            update_values = []
            
            if name:
                update_fields.append("name = ?")
                update_values.append(name)
            
            if sector:
                update_fields.append("sector = ?")
                update_values.append(sector)
            
            if industry:
                update_fields.append("industry = ?")
                update_values.append(industry)
            
            if exchange:
                update_fields.append("exchange = ?")
                update_values.append(exchange)
            
            if currency:
                update_fields.append("currency = ?")
                update_values.append(currency)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_values.append(symbol)
                
                query = f"""
                    UPDATE asset_metadata 
                    SET {', '.join(update_fields)}
                    WHERE symbol = ?
                """
                
                cursor.execute(query, update_values)
                
                # Zeige was aktualisiert wurde
                parts = []
                if name:
                    parts.append(f"Name: {name[:25]}")
                if sector:
                    parts.append(f"Sektor: {sector}")
                if exchange:
                    parts.append(f"Exchange: {exchange}")
                
                print(f"✅ {' | '.join(parts)}"[:70])
                updated += 1
            else:
                print(f"⚠️  Keine Metadaten gefunden")
            
            # Rate Limit (1 pro Sekunde)
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)[:40]}")
            errors += 1
            time.sleep(1)
        
        # Commit alle 50 Assets
        if i % 50 == 0:
            conn.commit()
            print(f"    💾 Zwischenspeicherung... ({i}/{len(assets)})")
    
    conn.commit()
    conn.close()
    
    print()
    print("="*70)
    print(f"✅ {updated} Assets aktualisiert")
    print(f"⚠️  {errors} Fehler")
    print("="*70)


if __name__ == "__main__":
    update_metadata()
