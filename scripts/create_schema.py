#!/usr/bin/env python3
"""
Erstellt das professionelle Schema für die zentrale Marktdaten-Datenbank.
Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def create_schema():
    """Erstellt alle Tabellen für die Marktdaten-Datenbank."""
    
    print(f"📊 Erstelle Datenbank-Schema: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ========================================
    # Tabelle 1: PRICE_DATA (OHLCV - Raw)
    # ========================================
    print("  → Erstelle Tabelle: price_data")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_data (
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            adj_close REAL NOT NULL,
            volume INTEGER NOT NULL,
            data_quality TEXT DEFAULT 'ok',
            source TEXT DEFAULT 'yfinance',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, date)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol ON price_data(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_date ON price_data(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_quality ON price_data(data_quality)")
    
    # ========================================
    # Tabelle 2: ASSET_METADATA (Stammdaten)
    # ========================================
    print("  → Erstelle Tabelle: asset_metadata")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asset_metadata (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            asset_type TEXT,
            exchange TEXT,
            sector TEXT,
            industry TEXT,
            currency TEXT DEFAULT 'USD',
            first_date DATE,
            last_date DATE,
            is_active INTEGER DEFAULT 1,
            update_frequency TEXT DEFAULT 'daily',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_type ON asset_metadata(asset_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_sector ON asset_metadata(sector)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_active ON asset_metadata(is_active)")
    
    # ========================================
    # Tabelle 3: INDICATORS_CACHE (Pre-calculated)
    # ========================================
    print("  → Erstelle Tabelle: indicators_cache")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators_cache (
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            indicator_name TEXT NOT NULL,
            value REAL NOT NULL,
            calculation_version TEXT DEFAULT 'v1',
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, date, indicator_name)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator_symbol ON indicators_cache(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator_date ON indicators_cache(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator_name ON indicators_cache(indicator_name)")
    
    # ========================================
    # Tabelle 4: DATA_QUALITY_LOG
    # ========================================
    print("  → Erstelle Tabelle: data_quality_log")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_quality_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            issue_type TEXT,
            severity TEXT,
            description TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_symbol ON data_quality_log(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_severity ON data_quality_log(severity)")
    
    # ========================================
    # Tabelle 5: UPDATE_LOG (Tracking)
    # ========================================
    print("  → Erstelle Tabelle: update_log")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS update_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_type TEXT NOT NULL,
            symbols_updated INTEGER DEFAULT 0,
            records_inserted INTEGER DEFAULT 0,
            records_updated INTEGER DEFAULT 0,
            duration_seconds REAL,
            status TEXT,
            error_message TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ========================================
    # Commit & Close
    # ========================================
    conn.commit()
    
    # Statistik anzeigen
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    
    print(f"\n✅ Schema erfolgreich erstellt!")
    print(f"   Datenbank: {DB_PATH}")
    print(f"   Tabellen: {len(tables)}")
    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        print(f"   - {table[0]}: {count} Einträge")
    
    conn.close()
    
    return True


def verify_schema():
    """Überprüft das erstellte Schema."""
    
    print("\n🔍 Verifiziere Schema...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    required_tables = [
        'price_data',
        'asset_metadata',
        'indicators_cache',
        'data_quality_log',
        'update_log'
    ]
    
    existing_tables = [
        row[0] for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    
    all_ok = True
    for table in required_tables:
        if table in existing_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} FEHLT!")
            all_ok = False
    
    conn.close()
    
    return all_ok


if __name__ == "__main__":
    print("="*60)
    print("MARKTDATEN-DATENBANK INITIALISIERUNG")
    print("="*60)
    print()
    
    try:
        create_schema()
        
        if verify_schema():
            print("\n🎉 Datenbank erfolgreich initialisiert!")
            print(f"📂 Pfad: {DB_PATH}")
        else:
            print("\n❌ Schema-Verifizierung fehlgeschlagen!")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
