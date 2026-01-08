#!/usr/bin/env python3
"""
Migriert asset_group aus der alten trading_strategies.db.
Liest index_name aus stocks_data und überträgt in asset_metadata.asset_group.

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
from pathlib import Path

OLD_DB = Path.home() / "TradingTool" / "database" / "trading_strategies.db"
NEW_DB = Path(__file__).parent.parent / "market_data.db"

# Mapping von index_name zu asset_group
INDEX_MAPPING = {
    'S&P500': 'sp500',
    'SP500': 'sp500',
    'NASDAQ100': 'nasdaq100',
    'DAX': 'dax',
    'MAIN_INDICES': 'index',
    'Strategy_Assets': None  # Diese nicht zuordnen
}


def get_symbol_to_index_mapping():
    """Liest Symbol → index_name Mapping aus alter DB."""
    
    print(f"📖 Lese Index-Zuordnungen aus: {OLD_DB}")
    
    conn = sqlite3.connect(OLD_DB)
    cursor = conn.cursor()
    
    # Hole DISTINCT Symbol + index_name
    query = """
        SELECT DISTINCT symbol, index_name
        FROM stocks_data
        WHERE index_name IS NOT NULL
        ORDER BY symbol, index_name
    """
    
    results = cursor.execute(query).fetchall()
    conn.close()
    
    # Erstelle Mapping (bevorzuge spezifischere Zuordnung)
    symbol_to_group = {}
    
    for symbol, index_name in results:
        asset_group = INDEX_MAPPING.get(index_name)
        
        if asset_group:
            # Falls Symbol schon existiert, bevorzuge spezifischere Gruppe
            # (sp500/nasdaq100/dax über index)
            if symbol in symbol_to_group:
                priority = {'sp500': 3, 'nasdaq100': 2, 'dax': 2, 'index': 1}
                current_priority = priority.get(symbol_to_group[symbol], 0)
                new_priority = priority.get(asset_group, 0)
                
                if new_priority > current_priority:
                    symbol_to_group[symbol] = asset_group
            else:
                symbol_to_group[symbol] = asset_group
    
    print(f"✅ {len(symbol_to_group)} Symbole mit Index-Zuordnung gefunden")
    
    # Zeige Statistik
    groups = {}
    for group in symbol_to_group.values():
        groups[group] = groups.get(group, 0) + 1
    
    print("\n📊 Verteilung:")
    for group, count in sorted(groups.items(), key=lambda x: x[1], reverse=True):
        print(f"   {group:15} → {count:3} Symbole")
    
    return symbol_to_group


def update_asset_groups(symbol_to_group):
    """Aktualisiert asset_group in neuer DB."""
    
    print(f"\n📝 Aktualisiere asset_group in: {NEW_DB}")
    
    conn = sqlite3.connect(NEW_DB)
    cursor = conn.cursor()
    
    updated = 0
    not_found = 0
    
    for symbol, asset_group in symbol_to_group.items():
        # Prüfe ob Symbol existiert
        exists = cursor.execute(
            "SELECT COUNT(*) FROM asset_metadata WHERE symbol = ?",
            (symbol,)
        ).fetchone()[0]
        
        if exists:
            cursor.execute("""
                UPDATE asset_metadata 
                SET asset_group = ?
                WHERE symbol = ?
            """, (asset_group, symbol))
            updated += 1
        else:
            not_found += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {updated} Symbole aktualisiert")
    print(f"⚠️  {not_found} Symbole nicht in neuer DB gefunden")
    
    return updated


def fix_common_issues():
    """Behebt bekannte Probleme (ALV vs ALV.DE)."""
    
    print(f"\n🔧 Behebe bekannte Probleme...")
    
    conn = sqlite3.connect(NEW_DB)
    cursor = conn.cursor()
    
    fixes = 0
    
    # Problem 1: ALV (Autoliv, US) ist NICHT DAX!
    cursor.execute("""
        UPDATE asset_metadata 
        SET asset_group = NULL
        WHERE symbol = 'ALV' AND name LIKE '%Autoliv%'
    """)
    fixes += cursor.rowcount
    
    # Problem 2: ALV.DE (Allianz, DE) IST DAX!
    cursor.execute("""
        UPDATE asset_metadata 
        SET asset_group = 'dax'
        WHERE symbol = 'ALV.DE' AND name LIKE '%Allianz%'
    """)
    fixes += cursor.rowcount
    
    # Problem 3: Alle .DE Symbole ohne asset_group, die in der alten DB als DAX waren
    # Diese müssen manuell von der Migration oben abgedeckt werden
    
    conn.commit()
    conn.close()
    
    print(f"✅ {fixes} Probleme behoben (ALV/ALV.DE)")


def verify_results():
    """Zeigt finale Statistik."""
    
    print(f"\n📊 FINALE STATISTIK:")
    
    conn = sqlite3.connect(NEW_DB)
    cursor = conn.cursor()
    
    # Aktien pro Gruppe
    results = cursor.execute("""
        SELECT 
            COALESCE(asset_group, 'NO_GROUP') as gruppe,
            COUNT(*) as anzahl
        FROM asset_metadata 
        WHERE is_active = 1 AND asset_type = 'stock'
        GROUP BY COALESCE(asset_group, 'NO_GROUP')
        ORDER BY anzahl DESC
    """).fetchall()
    
    print("")
    for gruppe, anzahl in results:
        icon = {
            'sp500': '🇺🇸',
            'nasdaq100': '💻',
            'dax': '🇩🇪',
            'index': '📊',
            'NO_GROUP': '❓'
        }.get(gruppe, '📌')
        
        print(f"   {icon} {gruppe:15} → {anzahl:3} Symbole")
    
    conn.close()


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("ASSET GROUP MIGRATION")
    print("="*60)
    print(f"\nVon: {OLD_DB}")
    print(f"Nach: {NEW_DB}")
    print()
    
    try:
        # Schritt 1: Lese Mapping aus alter DB
        symbol_to_group = get_symbol_to_index_mapping()
        
        # Schritt 2: Aktualisiere neue DB
        updated = update_asset_groups(symbol_to_group)
        
        # Schritt 3: Behebe bekannte Probleme
        fix_common_issues()
        
        # Schritt 4: Zeige Ergebnis
        verify_results()
        
        print("\n" + "="*60)
        print("✅ MIGRATION ERFOLGREICH!")
        print("="*60)
        print("\n💡 Nächste Schritte:")
        print("   1. GUI neu starten (MarketData_Manager.command)")
        print("   2. Prüfen Sie die Tabellen (sollten jetzt gefüllt sein)")
        print("   3. Falls nötig: MarketData_Update.command ausführen")
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
