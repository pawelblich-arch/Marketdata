#!/usr/bin/env python3
"""
Automatische Synchronisation der Index-Constituents von Wikipedia.
Fügt neue Assets hinzu und deaktiviert alte Assets.

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import pandas as pd
from pathlib import Path
import requests
from io import StringIO

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def get_sp500_constituents():
    """Holt aktuelle S&P 500 Constituents von Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        
        # Symbol bereinigen
        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
        
        return set(df['Symbol'].tolist())
    except Exception as e:
        print(f"❌ Fehler beim Laden von S&P 500: {e}")
        return None


def get_nasdaq100_constituents():
    """Holt aktuelle Nasdaq 100 Constituents von Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        
        for table in tables:
            if 'Ticker' in table.columns:
                df = table
                break
        else:
            return None
        
        return set(df['Ticker'].tolist())
    except Exception as e:
        print(f"❌ Fehler beim Laden von Nasdaq 100: {e}")
        return None


def get_db_constituents(asset_group):
    """Holt Constituents aus DB."""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT symbol FROM asset_metadata WHERE asset_group = ? AND is_active = 1"
    cursor = conn.execute(query, (asset_group,))
    symbols = set([row[0] for row in cursor.fetchall()])
    conn.close()
    return symbols


def add_assets(symbols, asset_group):
    """Fügt neue Assets hinzu."""
    if not symbols:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    added = 0
    
    for symbol in sorted(symbols):
        try:
            # Prüfe ob existiert
            exists = cursor.execute(
                "SELECT is_active FROM asset_metadata WHERE symbol = ?",
                (symbol,)
            ).fetchone()
            
            if exists:
                if not exists[0]:
                    # Reaktivieren
                    cursor.execute("""
                        UPDATE asset_metadata 
                        SET is_active = 1, asset_group = ?
                        WHERE symbol = ?
                    """, (asset_group, symbol))
                    added += 1
                    print(f"      ✅ {symbol} reaktiviert")
            else:
                # Neu hinzufügen
                cursor.execute("""
                    INSERT INTO asset_metadata 
                    (symbol, asset_type, asset_group, timeframe, is_active)
                    VALUES (?, 'stock', ?, '1d', 1)
                """, (symbol, asset_group))
                added += 1
                print(f"      ✅ {symbol} neu hinzugefügt")
        except Exception as e:
            print(f"      ⚠️ {symbol}: {e}")
    
    conn.commit()
    conn.close()
    return added


def deactivate_assets(symbols, asset_group):
    """Deaktiviert Assets."""
    if not symbols:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    deactivated = 0
    
    for symbol in sorted(symbols):
        cursor.execute("""
            UPDATE asset_metadata 
            SET is_active = 0
            WHERE symbol = ? AND asset_group = ?
        """, (symbol, asset_group))
        
        if cursor.rowcount > 0:
            deactivated += 1
            print(f"      ⛔ {symbol} deaktiviert")
    
    conn.commit()
    conn.close()
    return deactivated


def sync_index(index_name, asset_group, get_constituents_func):
    """Synchronisiert einen Index."""
    
    print(f"\n{'='*60}")
    print(f"📊 {index_name}")
    print(f"{'='*60}\n")
    
    # Lade aktuelle Constituents
    print(f"🔍 Lade aktuelle {index_name} Constituents...")
    current = get_constituents_func()
    
    if current is None:
        print(f"⚠️ Überspringe {index_name}")
        return None
    
    print(f"   ✅ {len(current)} Constituents geladen")
    
    # Lade DB Constituents
    db_symbols = get_db_constituents(asset_group)
    print(f"   ✅ {len(db_symbols)} Constituents in DB")
    
    # Unterschiede
    new_symbols = current - db_symbols
    old_symbols = db_symbols - current
    
    print(f"\n📈 ANALYSE:")
    print(f"   Aktuell: {len(current)}")
    print(f"   In DB: {len(db_symbols)}")
    print(f"   ✅ Neu: {len(new_symbols)}")
    print(f"   ❌ Zu entfernen: {len(old_symbols)}")
    
    if not new_symbols and not old_symbols:
        print(f"\n✅ {index_name} ist aktuell!")
        return {'added': 0, 'deactivated': 0}
    
    # Neue Assets hinzufügen
    added = 0
    if new_symbols:
        print(f"\n➕ NEUE ASSETS ({len(new_symbols)}):")
        added = add_assets(new_symbols, asset_group)
    
    # Alte Assets deaktivieren
    deactivated = 0
    if old_symbols:
        print(f"\n➖ ENTFERNTE ASSETS ({len(old_symbols)}):")
        deactivated = deactivate_assets(old_symbols, asset_group)
    
    return {'added': added, 'deactivated': deactivated}


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("AUTOMATISCHE INDEX-SYNCHRONISATION")
    print("="*60)
    print(f"\nDatenbank: {DB_PATH}")
    print()
    
    total_added = 0
    total_deactivated = 0
    
    # S&P 500
    result = sync_index("S&P 500", "sp500", get_sp500_constituents)
    if result:
        total_added += result['added']
        total_deactivated += result['deactivated']
    
    # Nasdaq 100
    result = sync_index("Nasdaq 100", "nasdaq100", get_nasdaq100_constituents)
    if result:
        total_added += result['added']
        total_deactivated += result['deactivated']
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("📊 GESAMT-ZUSAMMENFASSUNG")
    print(f"{'='*60}\n")
    
    print(f"   ✅ Neue Assets: {total_added}")
    print(f"   ⛔ Deaktiviert: {total_deactivated}")
    
    if total_added > 0 or total_deactivated > 0:
        print(f"\n💡 NÄCHSTE SCHRITTE:")
        print(f"   1. MarketData_Update.command ausführen")
        print(f"   2. Lädt Daten für {total_added} neue Assets")
        print(f"   3. GUI aktualisieren (🔄 Button)")
    else:
        print(f"\n✅ ALLE INDICES SIND AKTUELL!")
    
    print()


if __name__ == "__main__":
    main()
