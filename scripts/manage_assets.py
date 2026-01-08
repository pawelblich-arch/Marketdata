#!/usr/bin/env python3
"""
Asset-Management Tool für MarketData Datenbank
- Assets hinzufügen
- Assets löschen/deaktivieren
- Assets auflisten mit Details
- Daten-Lücken finden

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Pfade
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "market_data.db"


def get_connection():
    """Öffnet DB-Verbindung."""
    return sqlite3.connect(DB_PATH)


def list_assets(active_only=True, show_details=True):
    """Listet alle Assets mit Details auf."""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Query
    where_clause = "WHERE is_active = 1" if active_only else ""
    
    query = f"""
        SELECT 
            a.symbol,
            a.asset_type,
            a.name,
            a.sector,
            a.exchange,
            a.first_date,
            a.last_date,
            a.is_active,
            COUNT(p.date) as data_points,
            a.updated_at
        FROM asset_metadata a
        LEFT JOIN price_data p ON a.symbol = p.symbol
        {where_clause}
        GROUP BY a.symbol
        ORDER BY a.asset_type, a.symbol
    """
    
    results = cursor.execute(query).fetchall()
    
    print("="*100)
    print(f"{'Symbol':<12} {'Typ':<8} {'Name':<25} {'Von':<12} {'Bis':<12} {'Tage':<8} {'Status'}")
    print("="*100)
    
    for row in results:
        symbol, atype, name, sector, exchange, first_date, last_date, is_active, data_points, updated_at = row
        
        status = "✅ Aktiv" if is_active else "❌ Inaktiv"
        name_short = (name[:22] + "...") if name and len(name) > 25 else (name or "N/A")
        
        # Berechne Tage
        if first_date and last_date:
            days = (datetime.strptime(last_date, '%Y-%m-%d') - 
                   datetime.strptime(first_date, '%Y-%m-%d')).days
        else:
            days = 0
        
        print(f"{symbol:<12} {atype:<8} {name_short:<25} {first_date or 'N/A':<12} {last_date or 'N/A':<12} {days:<8} {status}")
        
        if show_details and data_points > 0:
            # Prüfe Daten-Lücken
            gaps = find_data_gaps(symbol, cursor)
            if gaps > 0:
                print(f"             ⚠️  {gaps} Lücken in Daten gefunden")
    
    print("="*100)
    print(f"\nGesamt: {len(results)} Assets")
    
    # Statistik
    active_count = sum(1 for r in results if r[7] == 1)
    inactive_count = len(results) - active_count
    print(f"Aktiv: {active_count} | Inaktiv: {inactive_count}")
    
    # Nach Typ
    types = {}
    for r in results:
        types[r[1]] = types.get(r[1], 0) + 1
    
    print("\nNach Typ:")
    for atype, count in sorted(types.items()):
        print(f"  {atype}: {count}")
    
    conn.close()


def find_data_gaps(symbol, cursor):
    """Findet Lücken in den Daten (fehlende Handelstage)."""
    
    # Hole alle Daten für Symbol
    dates = cursor.execute("""
        SELECT date FROM price_data 
        WHERE symbol = ?
        ORDER BY date
    """, (symbol,)).fetchall()
    
    if len(dates) < 2:
        return 0
    
    # Prüfe auf Lücken (> 5 Tage = Wochenende + Feiertag = OK, > 7 Tage = Lücke)
    gaps = 0
    for i in range(1, len(dates)):
        prev_date = datetime.strptime(dates[i-1][0], '%Y-%m-%d')
        curr_date = datetime.strptime(dates[i][0], '%Y-%m-%d')
        diff = (curr_date - prev_date).days
        
        if diff > 7:  # Mehr als 1 Woche
            gaps += 1
    
    return gaps


def add_asset(symbol, asset_type='stock', name=None, sector=None, exchange=None):
    """Fügt ein neues Asset hinzu."""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Prüfe ob Symbol schon existiert
    existing = cursor.execute(
        "SELECT symbol, is_active FROM asset_metadata WHERE symbol = ?", 
        (symbol,)
    ).fetchone()
    
    if existing:
        if existing[1] == 0:
            # Reaktiviere inaktives Asset
            cursor.execute("""
                UPDATE asset_metadata 
                SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (symbol,))
            conn.commit()
            print(f"✅ Asset {symbol} reaktiviert!")
        else:
            print(f"⚠️  Asset {symbol} existiert bereits und ist aktiv!")
        conn.close()
        return
    
    # Füge neues Asset hinzu
    cursor.execute("""
        INSERT INTO asset_metadata 
        (symbol, asset_type, name, sector, exchange, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (symbol, asset_type, name, sector, exchange))
    
    conn.commit()
    
    print(f"✅ Asset {symbol} hinzugefügt!")
    print(f"   Typ: {asset_type}")
    if name:
        print(f"   Name: {name}")
    
    conn.close()


def remove_asset(symbol, delete_data=False):
    """Entfernt ein Asset (deaktiviert oder löscht)."""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Prüfe ob Asset existiert
    existing = cursor.execute(
        "SELECT symbol FROM asset_metadata WHERE symbol = ?", 
        (symbol,)
    ).fetchone()
    
    if not existing:
        print(f"❌ Asset {symbol} nicht gefunden!")
        conn.close()
        return
    
    if delete_data:
        # WARNUNG: Daten werden gelöscht!
        print(f"⚠️  ACHTUNG: Lösche Asset {symbol} und ALLE Daten!")
        confirm = input("Sind Sie sicher? (ja/nein): ").lower()
        
        if confirm != 'ja':
            print("❌ Abgebrochen.")
            conn.close()
            return
        
        # Lösche Daten
        cursor.execute("DELETE FROM price_data WHERE symbol = ?", (symbol,))
        cursor.execute("DELETE FROM indicators_cache WHERE symbol = ?", (symbol,))
        cursor.execute("DELETE FROM asset_metadata WHERE symbol = ?", (symbol,))
        
        print(f"✅ Asset {symbol} und alle Daten gelöscht!")
    else:
        # Nur deaktivieren
        cursor.execute("""
            UPDATE asset_metadata 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (symbol,))
        
        print(f"✅ Asset {symbol} deaktiviert (Daten bleiben erhalten)!")
    
    conn.commit()
    conn.close()


def show_asset_details(symbol):
    """Zeigt detaillierte Informationen zu einem Asset."""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Asset-Metadaten
    meta = cursor.execute("""
        SELECT * FROM asset_metadata WHERE symbol = ?
    """, (symbol,)).fetchone()
    
    if not meta:
        print(f"❌ Asset {symbol} nicht gefunden!")
        conn.close()
        return
    
    # Daten-Statistik
    stats = cursor.execute("""
        SELECT 
            COUNT(*) as count,
            MIN(date) as first_date,
            MAX(date) as last_date,
            MIN(low) as min_price,
            MAX(high) as max_price,
            AVG(volume) as avg_volume
        FROM price_data
        WHERE symbol = ?
    """, (symbol,)).fetchone()
    
    print("="*70)
    print(f"📊 ASSET DETAILS: {symbol}")
    print("="*70)
    print()
    
    print(f"Name:         {meta[1] or 'N/A'}")
    print(f"Typ:          {meta[2]}")
    print(f"Exchange:     {meta[3] or 'N/A'}")
    print(f"Sektor:       {meta[4] or 'N/A'}")
    print(f"Industrie:    {meta[5] or 'N/A'}")
    print(f"Währung:      {meta[6]}")
    print(f"Status:       {'✅ Aktiv' if meta[9] else '❌ Inaktiv'}")
    print()
    
    if stats and stats[0] > 0:
        print("📈 DATEN:")
        print(f"Datenpunkte:  {stats[0]:,}")
        print(f"Zeitraum:     {stats[1]} bis {stats[2]}")
        
        # Berechne Handelstage
        first = datetime.strptime(stats[1], '%Y-%m-%d')
        last = datetime.strptime(stats[2], '%Y-%m-%d')
        total_days = (last - first).days
        print(f"Zeitspanne:   {total_days} Tage ({total_days/365:.1f} Jahre)")
        
        print(f"Preisspanne:  ${stats[3]:.2f} - ${stats[4]:.2f}")
        print(f"Ø Volumen:    {stats[5]:,.0f}")
        
        # Letzte 10 Einträge
        print()
        print("📅 LETZTE 10 EINTRÄGE:")
        recent = cursor.execute("""
            SELECT date, open, high, low, close, volume
            FROM price_data
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 10
        """, (symbol,)).fetchall()
        
        print(f"{'Datum':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}")
        print("-"*70)
        for r in recent:
            print(f"{r[0]:<12} {r[1]:<10.2f} {r[2]:<10.2f} {r[3]:<10.2f} {r[4]:<10.2f} {r[5]:<12,}")
    else:
        print("⚠️  Keine Kursdaten vorhanden!")
    
    print("="*70)
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Asset-Management Tool für MarketData Datenbank'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')
    
    # List
    list_parser = subparsers.add_parser('list', help='Alle Assets auflisten')
    list_parser.add_argument('--all', action='store_true', help='Auch inaktive Assets anzeigen')
    list_parser.add_argument('--simple', action='store_true', help='Einfache Ausgabe ohne Details')
    
    # Add
    add_parser = subparsers.add_parser('add', help='Neues Asset hinzufügen')
    add_parser.add_argument('symbol', help='Ticker-Symbol (z.B. AAPL)')
    add_parser.add_argument('--type', default='stock', help='Asset-Typ (stock, index, commodity, fx)')
    add_parser.add_argument('--name', help='Name des Assets')
    add_parser.add_argument('--sector', help='Sektor')
    add_parser.add_argument('--exchange', help='Börse')
    
    # Remove
    remove_parser = subparsers.add_parser('remove', help='Asset entfernen')
    remove_parser.add_argument('symbol', help='Ticker-Symbol')
    remove_parser.add_argument('--delete', action='store_true', help='Auch Daten löschen (ACHTUNG!)')
    
    # Show
    show_parser = subparsers.add_parser('show', help='Asset-Details anzeigen')
    show_parser.add_argument('symbol', help='Ticker-Symbol')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Führe Befehl aus
    if args.command == 'list':
        list_assets(active_only=not args.all, show_details=not args.simple)
    
    elif args.command == 'add':
        add_asset(
            args.symbol.upper(),
            asset_type=args.type,
            name=args.name,
            sector=args.sector,
            exchange=args.exchange
        )
    
    elif args.command == 'remove':
        remove_asset(args.symbol.upper(), delete_data=args.delete)
    
    elif args.command == 'show':
        show_asset_details(args.symbol.upper())


if __name__ == "__main__":
    main()
