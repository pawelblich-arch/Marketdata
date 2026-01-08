#!/usr/bin/env python3
"""
Synchronisiert Index-Constituents automatisch basierend auf ETF-Holdings.

Nutzt:
- SPY (SPDR S&P 500 ETF) → S&P 500
- QQQ (Invesco QQQ Trust) → Nasdaq 100
- EXS1.DE (iShares EURO STOXX 50) → EuroStoxx 50
- DAX: Wird von Wikipedia geladen (Fallback)

Autor: Trading System v2
Datum: 2026-01-08
"""

import yfinance as yf
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "market_data.db"

# ETF → Index Mapping
ETF_MAPPING = {
    'SPY': {
        'index_name': 'S&P 500',
        'asset_group': 'sp500',
        'expected_count': 500
    },
    'QQQ': {
        'index_name': 'Nasdaq 100',
        'asset_group': 'nasdaq100',
        'expected_count': 100
    },
    'EXW1.DE': {  # iShares EURO STOXX 50
        'index_name': 'EuroStoxx 50',
        'asset_group': 'eurostoxx',
        'expected_count': 50
    }
}


def get_etf_holdings(etf_symbol):
    """Holt Holdings eines ETFs via yfinance."""
    
    try:
        etf = yf.Ticker(etf_symbol)
        
        # Methode 1: get_holdings() (neuere yfinance Versionen)
        try:
            holdings = etf.get_holdings()
            if holdings is not None and not holdings.empty:
                return set(holdings.index.tolist())
        except:
            pass
        
        # Methode 2: info['holdings']
        try:
            info = etf.info
            if 'holdings' in info:
                return set([h['symbol'] for h in info['holdings']])
        except:
            pass
        
        # Methode 3: Fallback - Top Holdings aus info
        try:
            info = etf.info
            if 'topHoldings' in info:
                return set([h['symbol'] for h in info['topHoldings']])
        except:
            pass
        
        return None
        
    except Exception as e:
        print(f"   ❌ Fehler beim Laden von {etf_symbol}: {e}")
        return None


def get_db_constituents(asset_group):
    """Holt aktuelle Constituents aus DB."""
    
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT symbol 
        FROM asset_metadata 
        WHERE asset_group = ? AND is_active = 1
    """
    cursor = conn.execute(query, (asset_group,))
    symbols = set([row[0] for row in cursor.fetchall()])
    conn.close()
    
    return symbols


def add_new_assets(symbols, asset_group):
    """Fügt neue Assets zur DB hinzu."""
    
    if not symbols:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    added = 0
    
    for symbol in symbols:
        try:
            # Prüfe ob Symbol schon existiert
            exists = cursor.execute(
                "SELECT symbol, is_active, asset_group FROM asset_metadata WHERE symbol = ?",
                (symbol,)
            ).fetchone()
            
            if exists:
                # Existiert schon - ggf. reaktivieren/umgruppieren
                if not exists[1] or exists[2] != asset_group:
                    cursor.execute("""
                        UPDATE asset_metadata 
                        SET is_active = 1, asset_group = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE symbol = ?
                    """, (asset_group, symbol))
                    added += 1
                    print(f"      ✅ {symbol} reaktiviert/umgruppiert")
            else:
                # Neu hinzufügen
                cursor.execute("""
                    INSERT INTO asset_metadata 
                    (symbol, asset_type, asset_group, timeframe, is_active)
                    VALUES (?, 'stock', ?, '1d', 1)
                """, (symbol, asset_group))
                added += 1
                print(f"      ✅ {symbol} hinzugefügt")
                
        except Exception as e:
            print(f"      ⚠️ {symbol}: {e}")
    
    conn.commit()
    conn.close()
    
    return added


def deactivate_old_assets(symbols, asset_group):
    """Deaktiviert Assets, die nicht mehr im Index sind."""
    
    if not symbols:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    deactivated = 0
    
    for symbol in symbols:
        cursor.execute("""
            UPDATE asset_metadata 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ? AND asset_group = ?
        """, (symbol, asset_group))
        
        if cursor.rowcount > 0:
            deactivated += 1
            print(f"      ⛔ {symbol} deaktiviert")
    
    conn.commit()
    conn.close()
    
    return deactivated


def sync_index(etf_symbol, config):
    """Synchronisiert einen Index basierend auf ETF-Holdings."""
    
    index_name = config['index_name']
    asset_group = config['asset_group']
    expected = config['expected_count']
    
    print(f"\n{'='*60}")
    print(f"📊 {index_name}")
    print(f"{'='*60}\n")
    
    # Hole ETF Holdings
    print(f"🔍 Lade Holdings von {etf_symbol}...")
    current = get_etf_holdings(etf_symbol)
    
    if current is None:
        print(f"   ⚠️ Keine Holdings verfügbar - überspringe {index_name}")
        return None
    
    print(f"   ✅ {len(current)} Holdings geladen")
    
    # Warnug falls zu wenig
    if len(current) < expected * 0.5:  # Weniger als 50% erwartet
        print(f"   ⚠️ WARNUNG: Nur {len(current)} von ~{expected} Holdings!")
        print(f"   ⚠️ yfinance liefert möglicherweise unvollständige Daten")
        print(f"   ⚠️ Überspringe {index_name} um Datenverlust zu vermeiden")
        return None
    
    # Hole DB Constituents
    print(f"🔍 Lade {index_name} Constituents aus Datenbank...")
    db_symbols = get_db_constituents(asset_group)
    print(f"   ✅ {len(db_symbols)} Constituents in DB")
    
    # Finde Unterschiede
    new_symbols = current - db_symbols
    old_symbols = db_symbols - current
    
    print(f"\n📈 ANALYSE:")
    print(f"   Aktuell (ETF): {len(current)}")
    print(f"   In DB: {len(db_symbols)}")
    print(f"   ✅ Neu: {len(new_symbols)}")
    print(f"   ❌ Zu entfernen: {len(old_symbols)}")
    
    if not new_symbols and not old_symbols:
        print(f"\n✅ {index_name} ist aktuell - keine Änderungen!")
        return {'added': 0, 'deactivated': 0}
    
    # Neue Assets hinzufügen
    added = 0
    if new_symbols:
        print(f"\n➕ NEUE ASSETS ({len(new_symbols)}):")
        added = add_new_assets(sorted(new_symbols), asset_group)
    
    # Alte Assets deaktivieren
    deactivated = 0
    if old_symbols:
        print(f"\n➖ ENTFERNTE ASSETS ({len(old_symbols)}):")
        deactivated = deactivate_old_assets(sorted(old_symbols), asset_group)
    
    return {
        'added': added,
        'deactivated': deactivated,
        'current_count': len(current),
        'db_count': len(db_symbols) + added - deactivated
    }


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("INDEX CONSTITUENTS SYNCHRONISATION")
    print("="*60)
    print("\nAutomatisches Update basierend auf ETF-Holdings")
    print(f"Datenbank: {DB_PATH}")
    print()
    
    total_added = 0
    total_deactivated = 0
    
    # Synchronisiere alle Indices
    for etf_symbol, config in ETF_MAPPING.items():
        result = sync_index(etf_symbol, config)
        
        if result:
            total_added += result['added']
            total_deactivated += result['deactivated']
    
    # Gesamt-Zusammenfassung
    print(f"\n{'='*60}")
    print("📊 GESAMT-ZUSAMMENFASSUNG")
    print(f"{'='*60}\n")
    
    print(f"   ✅ Neue Assets hinzugefügt: {total_added}")
    print(f"   ⛔ Assets deaktiviert: {total_deactivated}")
    
    if total_added > 0 or total_deactivated > 0:
        print(f"\n⚠️ WICHTIG:")
        print(f"   1. Führen Sie 'MarketData_Update.command' aus")
        print(f"   2. Lädt Daten für neue Assets")
        print(f"   3. GUI aktualisieren (🔄 Button)")
    else:
        print(f"\n✅ ALLE INDICES SIND AKTUELL!")
    
    print()


if __name__ == "__main__":
    main()
