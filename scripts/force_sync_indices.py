#!/usr/bin/env python3
"""
FORCE SYNC: Komplette Synchronisation der Index-Constituents.
Nutzt mehrere Quellen und macht kompletten Abgleich.

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import pandas as pd
from pathlib import Path
import requests
from io import StringIO
import yfinance as yf

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def get_sp500_constituents():
    """S&P 500 von Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        
        # Symbol bereinigen
        symbols = set(df['Symbol'].str.replace('.', '-', regex=False).tolist())
        
        print(f"   ✅ Wikipedia: {len(symbols)} Symbole")
        return symbols
        
    except Exception as e:
        print(f"   ❌ Wikipedia Fehler: {e}")
        return set()


def get_nasdaq100_constituents():
    """Nasdaq 100 von Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        
        for table in tables:
            if 'Ticker' in table.columns:
                symbols = set(table['Ticker'].tolist())
                print(f"   ✅ Wikipedia: {len(symbols)} Symbole")
                return symbols
        
        return set()
        
    except Exception as e:
        print(f"   ❌ Wikipedia Fehler: {e}")
        return set()


def get_dax_constituents():
    """DAX 40 - manuell korrigiert auf 40."""
    # DAX 40 - offizielle Liste
    dax40 = [
        'ADS.DE', 'AIR.DE', 'ALV.DE', 'BAS.DE', 'BAYN.DE',
        'BEI.DE', 'BMW.DE', 'BNR.DE', 'CON.DE', 'DB1.DE',
        'DBK.DE', 'DHL.DE', 'DTE.DE', 'EOAN.DE', 'FME.DE',
        'FRE.DE', 'HEI.DE', 'HEN3.DE', 'HFG.DE', 'IFX.DE',
        'LIN.DE', 'MBG.DE', 'MRK.DE', 'MTX.DE', 'MUV2.DE',
        'PAH3.DE', 'P911.DE', 'QIA.DE', 'RHM.DE', 'RWE.DE',
        'SAP.DE', 'SHL.DE', 'SIE.DE', 'SRT3.DE', 'SY1.DE',
        'VNA.DE', 'VOW3.DE', 'ZAL.DE', '1COV.DE', 'BDT.DE'
    ]
    
    symbols = set(dax40)
    print(f"   ✅ Manuell: {len(symbols)} Symbole (DAX 40)")
    return symbols


def force_sync(index_name, asset_group, get_constituents_func, force_count=None):
    """Force Sync mit komplettem Reset."""
    
    print(f"\n{'='*60}")
    print(f"📊 {index_name} - FORCE SYNC")
    print(f"{'='*60}\n")
    
    # Lade korrekte Constituents
    print(f"🔍 Lade {index_name} Constituents...")
    correct = get_constituents_func()
    
    if not correct:
        print(f"⚠️ Überspringe {index_name}")
        return None
    
    # Prüfe ob Anzahl plausibel ist
    if force_count and len(correct) < force_count * 0.8:
        print(f"   ⚠️ WARNUNG: Nur {len(correct)} von ~{force_count} geladen!")
        user_input = input(f"   Fortfahren? (j/n): ").lower()
        if user_input != 'j':
            return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hole ALLE Symbole mit diesem asset_group (aktiv + inaktiv)
    all_db = cursor.execute("""
        SELECT symbol, is_active FROM asset_metadata 
        WHERE asset_group = ?
    """, (asset_group,)).fetchall()
    
    db_active = set([s for s, active in all_db if active])
    db_inactive = set([s for s, active in all_db if not active])
    db_all = set([s for s, _ in all_db])
    
    print(f"\n📊 STATUS:")
    print(f"   Korrekt (Quelle): {len(correct)}")
    print(f"   DB aktiv: {len(db_active)}")
    print(f"   DB inaktiv: {len(db_inactive)}")
    print(f"   DB gesamt: {len(db_all)}")
    
    # Finde Änderungen
    to_activate = correct - db_active  # Sollte aktiv sein, ist aber nicht
    to_deactivate = db_active - correct  # Ist aktiv, sollte aber nicht
    to_add = correct - db_all  # Existiert noch gar nicht
    
    print(f"\n🔧 ÄNDERUNGEN:")
    print(f"   ➕ Neu hinzufügen: {len(to_add)}")
    print(f"   ✅ Reaktivieren: {len(to_activate - to_add)}")
    print(f"   ⛔ Deaktivieren: {len(to_deactivate)}")
    
    # 1. Neue Assets hinzufügen
    added = 0
    if to_add:
        print(f"\n➕ NEUE ASSETS ({len(to_add)}):")
        for symbol in sorted(to_add)[:20]:  # Zeige erste 20
            try:
                cursor.execute("""
                    INSERT INTO asset_metadata 
                    (symbol, asset_type, asset_group, timeframe, is_active)
                    VALUES (?, 'stock', ?, '1d', 1)
                """, (symbol, asset_group))
                added += 1
                print(f"      ✅ {symbol}")
            except Exception as e:
                print(f"      ⚠️ {symbol}: {e}")
        
        if len(to_add) > 20:
            print(f"      ... und {len(to_add) - 20} weitere")
    
    # 2. Inaktive reaktivieren
    reactivated = 0
    to_reactivate = to_activate - to_add
    if to_reactivate:
        print(f"\n✅ REAKTIVIEREN ({len(to_reactivate)}):")
        for symbol in sorted(to_reactivate)[:10]:
            cursor.execute("""
                UPDATE asset_metadata 
                SET is_active = 1, asset_group = ?
                WHERE symbol = ?
            """, (asset_group, symbol))
            reactivated += cursor.rowcount
            print(f"      ✅ {symbol}")
        
        if len(to_reactivate) > 10:
            print(f"      ... und {len(to_reactivate) - 10} weitere")
    
    # 3. Falsche deaktivieren
    deactivated = 0
    if to_deactivate:
        print(f"\n⛔ DEAKTIVIEREN ({len(to_deactivate)}):")
        for symbol in sorted(to_deactivate)[:10]:
            cursor.execute("""
                UPDATE asset_metadata 
                SET is_active = 0
                WHERE symbol = ?
            """, (symbol,))
            deactivated += cursor.rowcount
            print(f"      ⛔ {symbol}")
        
        if len(to_deactivate) > 10:
            print(f"      ... und {len(to_deactivate) - 10} weitere")
    
    conn.commit()
    conn.close()
    
    print(f"\n📈 ERGEBNIS:")
    print(f"   ✅ {added} neu hinzugefügt")
    print(f"   ✅ {reactivated} reaktiviert")
    print(f"   ⛔ {deactivated} deaktiviert")
    print(f"   → Jetzt {len(correct)} aktive Assets")
    
    return {'added': added, 'reactivated': reactivated, 'deactivated': deactivated}


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("FORCE SYNC - KOMPLETTE INDEX-SYNCHRONISATION")
    print("="*60)
    print(f"\nDatenbank: {DB_PATH}")
    print("\n⚠️  ACHTUNG: Dies macht einen kompletten Abgleich!")
    print("Assets, die nicht im Index sind, werden deaktiviert.")
    print()
    
    # S&P 500
    result = force_sync("S&P 500", "sp500", get_sp500_constituents, 500)
    
    # Nasdaq 100
    result = force_sync("Nasdaq 100", "nasdaq100", get_nasdaq100_constituents, 100)
    
    # DAX 40
    result = force_sync("DAX 40", "dax", get_dax_constituents, 40)
    
    print(f"\n{'='*60}")
    print("✅ FORCE SYNC ABGESCHLOSSEN")
    print(f"{'='*60}\n")
    print("💡 NÄCHSTE SCHRITTE:")
    print("   1. MarketData_Update.command ausführen")
    print("   2. GUI aktualisieren (🔄 Button)")
    print()


if __name__ == "__main__":
    main()
