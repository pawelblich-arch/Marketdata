#!/usr/bin/env python3
"""
Prüft Index-Constituents (S&P 500, Nasdaq 100, DAX) auf Änderungen.
Findet neue Assets und entfernte Assets.

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import pandas as pd
from pathlib import Path
import yfinance as yf

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def get_sp500_constituents():
    """Holt aktuelle S&P 500 Constituents von Wikipedia."""
    try:
        import requests
        from io import StringIO
        
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        
        # User-Agent Header hinzufügen (täuscht Browser vor)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]  # Erste Tabelle = Current S&P 500 components
        
        # Symbol bereinigen (BRK.B -> BRK-B für yfinance)
        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
        
        return set(df['Symbol'].tolist())
    except Exception as e:
        print(f"❌ Fehler beim Laden von S&P 500: {e}")
        return set()


def get_nasdaq100_constituents():
    """Holt aktuelle Nasdaq 100 Constituents."""
    try:
        import requests
        from io import StringIO
        
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        
        # Die richtige Tabelle finden (enthält "Ticker")
        for table in tables:
            if 'Ticker' in table.columns:
                df = table
                break
        else:
            print("⚠️ Nasdaq 100 Tabelle nicht gefunden")
            return set()
        
        return set(df['Ticker'].tolist())
    except Exception as e:
        print(f"❌ Fehler beim Laden von Nasdaq 100: {e}")
        return set()


def get_dax_constituents():
    """Holt aktuelle DAX Constituents."""
    try:
        import requests
        from io import StringIO
        
        url = "https://en.wikipedia.org/wiki/DAX"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        
        # Erste Tabelle = DAX constituents
        df = tables[0]
        
        if 'Ticker symbol' in df.columns:
            # Füge .DE für yfinance hinzu
            symbols = [s + '.DE' if not s.endswith('.DE') else s for s in df['Ticker symbol'].tolist()]
            return set(symbols)
        else:
            print("⚠️ DAX Tabelle hat kein 'Ticker symbol' Spalte")
            return set()
    except Exception as e:
        print(f"❌ Fehler beim Laden von DAX: {e}")
        return set()


def get_db_constituents(asset_group):
    """Holt Constituents aus der Datenbank."""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT symbol FROM asset_metadata WHERE asset_group = '{asset_group}' AND is_active = 1"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return set(df['symbol'].tolist())


def check_index(index_name, asset_group, get_constituents_func):
    """Prüft einen Index auf Änderungen."""
    
    print(f"\n{'='*60}")
    print(f"📊 {index_name}")
    print(f"{'='*60}\n")
    
    # Lade aktuelle Constituents
    print(f"🔍 Lade aktuelle {index_name} Constituents...")
    current = get_constituents_func()
    
    if not current:
        print(f"⚠️ Keine Constituents geladen - überspringe {index_name}")
        return
    
    print(f"   ✅ {len(current)} Constituents geladen")
    
    # Lade DB-Constituents
    print(f"🔍 Lade {index_name} Constituents aus Datenbank...")
    db_symbols = get_db_constituents(asset_group)
    print(f"   ✅ {len(db_symbols)} Constituents in DB")
    
    # Finde Unterschiede
    new_symbols = current - db_symbols
    removed_symbols = db_symbols - current
    
    print(f"\n📈 ANALYSE:")
    print(f"   Aktuell: {len(current)}")
    print(f"   In DB: {len(db_symbols)}")
    print(f"   ✅ Neu: {len(new_symbols)}")
    print(f"   ❌ Entfernt: {len(removed_symbols)}")
    
    if new_symbols:
        print(f"\n➕ NEUE ASSETS ({len(new_symbols)}):")
        for symbol in sorted(new_symbols):
            print(f"   + {symbol}")
        
        print(f"\n💡 Befehl zum Hinzufügen:")
        print(f"   Öffnen Sie die GUI und fügen Sie diese Assets manuell hinzu:")
        print(f"   Asset-Typ: stock")
        print(f"   Asset-Gruppe: {asset_group}")
    
    if removed_symbols:
        print(f"\n➖ ENTFERNTE ASSETS ({len(removed_symbols)}):")
        for symbol in sorted(removed_symbols):
            print(f"   - {symbol}")
        
        print(f"\n💡 Diese Assets sollten deaktiviert werden.")
        print(f"   (In der GUI oder direkt in der DB)")
    
    if not new_symbols and not removed_symbols:
        print(f"\n✅ {index_name} ist aktuell - keine Änderungen!")
    
    return {
        'new': new_symbols,
        'removed': removed_symbols,
        'current_count': len(current),
        'db_count': len(db_symbols)
    }


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("INDEX CONSTITUENTS CHECK")
    print("="*60)
    print("\nPrüft S&P 500, Nasdaq 100 und DAX auf Änderungen")
    print(f"Datenbank: {DB_PATH}")
    print()
    
    results = {}
    
    # S&P 500
    results['sp500'] = check_index(
        "S&P 500",
        "sp500",
        get_sp500_constituents
    )
    
    # Nasdaq 100
    results['nasdaq100'] = check_index(
        "Nasdaq 100",
        "nasdaq100",
        get_nasdaq100_constituents
    )
    
    # DAX
    results['dax'] = check_index(
        "DAX 40",
        "dax",
        get_dax_constituents
    )
    
    # Gesamt-Zusammenfassung
    print(f"\n{'='*60}")
    print("📊 GESAMT-ZUSAMMENFASSUNG")
    print(f"{'='*60}\n")
    
    total_new = sum(len(r['new']) for r in results.values() if r)
    total_removed = sum(len(r['removed']) for r in results.values() if r)
    
    print(f"   Neue Assets gesamt: {total_new}")
    print(f"   Entfernte Assets gesamt: {total_removed}")
    
    if total_new > 0 or total_removed > 0:
        print(f"\n⚠️ AKTION ERFORDERLICH!")
        print(f"   1. Neue Assets in der GUI hinzufügen")
        print(f"   2. Entfernte Assets deaktivieren")
        print(f"   3. MarketData_Update.command ausführen")
    else:
        print(f"\n✅ ALLE INDICES SIND AKTUELL!")
    
    print()


if __name__ == "__main__":
    main()
