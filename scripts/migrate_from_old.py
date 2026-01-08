#!/usr/bin/env python3
"""
Migriert Daten aus der alten trading_strategies.db in die neue zentrale market_data.db.
Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import yaml
from pathlib import Path
from datetime import datetime
import shutil


# Pfade
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
NEW_DB_PATH = BASE_DIR / "market_data.db"


def load_config():
    """Lädt die Konfiguration."""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def create_backup(old_db_path):
    """Erstellt ein Backup der alten Datenbank."""
    backup_dir = BASE_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"old_trading_strategies_{timestamp}.db"
    
    print(f"📦 Erstelle Backup: {backup_path.name}")
    shutil.copy2(old_db_path, backup_path)
    
    return backup_path


def analyze_old_db(old_db_path):
    """Analysiert die alte Datenbank."""
    print("\n🔍 Analysiere alte Datenbank...")
    
    conn = sqlite3.connect(old_db_path)
    cursor = conn.cursor()
    
    # Prüfe ob stocks_data Tabelle existiert
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = [t[0] for t in tables]
    
    print(f"   Gefundene Tabellen: {', '.join(table_names)}")
    
    if 'stocks_data' not in table_names:
        print("   ❌ Tabelle 'stocks_data' nicht gefunden!")
        conn.close()
        return None
    
    # Statistik
    stats = {}
    
    # Anzahl Symbole
    symbols_count = cursor.execute(
        "SELECT COUNT(DISTINCT symbol) FROM stocks_data"
    ).fetchone()[0]
    stats['symbols'] = symbols_count
    
    # Anzahl Datenpunkte
    total_rows = cursor.execute(
        "SELECT COUNT(*) FROM stocks_data"
    ).fetchone()[0]
    stats['rows'] = total_rows
    
    # Datumsspanne
    date_range = cursor.execute(
        "SELECT MIN(date), MAX(date) FROM stocks_data"
    ).fetchone()
    stats['min_date'] = date_range[0]
    stats['max_date'] = date_range[1]
    
    # Schema prüfen
    schema = cursor.execute("PRAGMA table_info(stocks_data)").fetchall()
    columns = [col[1] for col in schema]
    stats['columns'] = columns
    
    print(f"   Symbole: {stats['symbols']:,}")
    print(f"   Datenpunkte: {stats['rows']:,}")
    print(f"   Zeitraum: {stats['min_date']} bis {stats['max_date']}")
    print(f"   Spalten: {', '.join(columns)}")
    
    conn.close()
    
    return stats


def migrate_price_data(old_db_path, batch_size=10000):
    """Migriert OHLCV-Daten von stocks_data → price_data."""
    
    print("\n📊 Migriere Kursdaten...")
    
    old_conn = sqlite3.connect(old_db_path)
    new_conn = sqlite3.connect(NEW_DB_PATH)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    # Gesamtanzahl Datensätze
    total_rows = old_cursor.execute("SELECT COUNT(*) FROM stocks_data").fetchone()[0]
    
    print(f"   Zu migrierende Datensätze: {total_rows:,}")
    
    # Migration in Batches (für bessere Performance)
    offset = 0
    migrated = 0
    errors = 0
    
    while offset < total_rows:
        print(f"   Fortschritt: {offset:,} / {total_rows:,} ({offset/total_rows*100:.1f}%)", end='\r')
        
        # Lese Batch aus alter DB
        rows = old_cursor.execute(f"""
            SELECT 
                symbol, 
                date, 
                open, 
                high, 
                low, 
                close, 
                close as adj_close,
                volume
            FROM stocks_data
            ORDER BY symbol, date
            LIMIT {batch_size} OFFSET {offset}
        """).fetchall()
        
        if not rows:
            break
        
        # Schreibe in neue DB
        try:
            new_cursor.executemany("""
                INSERT OR IGNORE INTO price_data 
                (symbol, date, open, high, low, close, adj_close, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'migrated')
            """, rows)
            
            new_conn.commit()
            migrated += len(rows)
            
        except Exception as e:
            print(f"\n   ⚠️  Fehler bei Batch {offset}: {e}")
            errors += 1
        
        offset += batch_size
    
    print(f"\n   ✅ Migration abgeschlossen: {migrated:,} Datensätze")
    if errors > 0:
        print(f"   ⚠️  Fehler: {errors}")
    
    old_conn.close()
    new_conn.close()
    
    return migrated, errors


def migrate_asset_metadata(old_db_path):
    """Erstellt asset_metadata aus den migrierten Daten."""
    
    print("\n📋 Erstelle Asset-Metadaten...")
    
    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()
    
    # Extrahiere eindeutige Symbole und deren Zeitspannen
    cursor.execute("""
        INSERT OR REPLACE INTO asset_metadata 
        (symbol, asset_type, first_date, last_date, is_active)
        SELECT 
            symbol,
            CASE 
                WHEN symbol LIKE '^%' THEN 'index'
                WHEN symbol LIKE '%=F' THEN 'commodity'
                WHEN symbol LIKE '%EUR%' OR symbol LIKE '%USD%' THEN 'fx'
                ELSE 'stock'
            END as asset_type,
            MIN(date) as first_date,
            MAX(date) as last_date,
            1 as is_active
        FROM price_data
        WHERE source = 'migrated'
        GROUP BY symbol
    """)
    
    count = cursor.rowcount
    conn.commit()
    
    print(f"   ✅ {count} Assets katalogisiert")
    
    conn.close()
    
    return count


def create_summary():
    """Erstellt eine Zusammenfassung der Migration."""
    
    print("\n📈 Migrations-Zusammenfassung:")
    print("="*60)
    
    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()
    
    # price_data
    price_count = cursor.execute("SELECT COUNT(*) FROM price_data").fetchone()[0]
    symbols_count = cursor.execute("SELECT COUNT(DISTINCT symbol) FROM price_data").fetchone()[0]
    date_range = cursor.execute("SELECT MIN(date), MAX(date) FROM price_data").fetchone()
    
    print(f"   📊 price_data:")
    print(f"      - Datenpunkte: {price_count:,}")
    print(f"      - Symbole: {symbols_count:,}")
    print(f"      - Zeitraum: {date_range[0]} bis {date_range[1]}")
    
    # asset_metadata
    assets_count = cursor.execute("SELECT COUNT(*) FROM asset_metadata").fetchone()[0]
    asset_types = cursor.execute("""
        SELECT asset_type, COUNT(*) 
        FROM asset_metadata 
        GROUP BY asset_type
    """).fetchall()
    
    print(f"\n   📋 asset_metadata:")
    print(f"      - Gesamt: {assets_count}")
    for atype, count in asset_types:
        print(f"      - {atype}: {count}")
    
    # Datenbank-Größe
    db_size_mb = NEW_DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\n   💾 Datenbank-Größe: {db_size_mb:.1f} MB")
    
    print("="*60)
    
    conn.close()


def main():
    """Hauptfunktion für Migration."""
    
    print("="*60)
    print("MIGRATION: trading_strategies.db → market_data.db")
    print("="*60)
    
    # Lade Konfiguration
    config = load_config()
    old_db_path = Path(config['migration']['old_db_path'])
    
    # Prüfe ob alte DB existiert
    if not old_db_path.exists():
        print(f"\n❌ Alte Datenbank nicht gefunden: {old_db_path}")
        print("   Bitte passen Sie den Pfad in config.yaml an!")
        return False
    
    # Prüfe ob neue DB existiert
    if not NEW_DB_PATH.exists():
        print(f"\n❌ Neue Datenbank nicht gefunden: {NEW_DB_PATH}")
        print("   Bitte führen Sie zuerst 'create_schema.py' aus!")
        return False
    
    print(f"\n📂 Quell-Datenbank: {old_db_path}")
    print(f"📂 Ziel-Datenbank: {NEW_DB_PATH}")
    
    # Analysiere alte DB
    stats = analyze_old_db(old_db_path)
    if not stats:
        return False
    
    # Bestätigung
    print(f"\n⚠️  ACHTUNG: Es werden {stats['rows']:,} Datensätze migriert!")
    response = input("   Fortfahren? (ja/nein): ").lower()
    
    if response != 'ja':
        print("   ❌ Migration abgebrochen.")
        return False
    
    # Backup erstellen
    backup_path = create_backup(old_db_path)
    
    # Migration durchführen
    start_time = datetime.now()
    
    migrated, errors = migrate_price_data(old_db_path)
    meta_count = migrate_asset_metadata(old_db_path)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Zusammenfassung
    create_summary()
    
    print(f"\n⏱️  Dauer: {duration:.1f} Sekunden")
    print(f"📦 Backup gespeichert: {backup_path.name}")
    
    if errors == 0:
        print("\n🎉 Migration erfolgreich abgeschlossen!")
        return True
    else:
        print(f"\n⚠️  Migration mit {errors} Fehlern abgeschlossen!")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
