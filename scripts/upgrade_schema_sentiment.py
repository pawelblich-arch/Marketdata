#!/usr/bin/env python3
"""
Erweitert das Schema um Sentiment- und Marktbreite-Tabellen.
Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def upgrade_schema():
    """Fügt sentiment_data und market_breadth Tabellen hinzu."""
    
    print(f"📊 Erweitere Datenbank-Schema: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ========================================
    # Tabelle 6: SENTIMENT_DATA (VIX, Fear & Greed, AAII, Put/Call)
    # ========================================
    print("  → Erstelle Tabelle: sentiment_data")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator TEXT NOT NULL,           -- 'VIX', 'VDAX', 'FEAR_GREED', 'AAII_BULL', 'PUT_CALL'
            date TEXT NOT NULL,                -- YYYY-MM-DD
            value REAL NOT NULL,               -- Hauptwert
            value_high REAL,                   -- Für Intraday-Range (optional)
            value_low REAL,
            metadata TEXT,                     -- JSON für zusätzliche Infos
            source TEXT,                       -- 'yfinance', 'cnn', 'aaii', 'cboe'
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(indicator, date)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_indicator ON sentiment_data(indicator)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_date ON sentiment_data(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_indicator_date ON sentiment_data(indicator, date)")
    
    # ========================================
    # Tabelle 7: MARKET_BREADTH (Berechnete Marktbreite - für später)
    # ========================================
    print("  → Erstelle Tabelle: market_breadth (leer, für TradingTool)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_breadth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            index_symbol TEXT NOT NULL,        -- 'SPX', 'DAX', 'NDX'
            
            -- New Highs/Lows (52 Wochen)
            new_highs_52w INTEGER,
            new_lows_52w INTEGER,
            hl_ratio REAL,                     -- Highs / (Highs + Lows)
            
            -- Advance/Decline
            advancing INTEGER,
            declining INTEGER,
            unchanged INTEGER,
            ad_line REAL,                      -- Kumulativ
            ad_ratio REAL,                     -- Adv / Decl
            
            -- Trend Strength
            pct_above_ema20 REAL,
            pct_above_ema50 REAL,
            pct_above_ema200 REAL,
            
            -- Volume Analysis
            up_volume REAL,
            down_volume REAL,
            volume_ratio REAL,
            
            -- Metadata
            calculation_version TEXT DEFAULT 'v1.0',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(date, index_symbol, calculation_version)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_breadth_date ON market_breadth(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_breadth_index ON market_breadth(index_symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_breadth_date_index ON market_breadth(date, index_symbol)")
    
    # ========================================
    # Commit & Close
    # ========================================
    conn.commit()
    
    # Statistik anzeigen
    print("\n✅ Schema-Upgrade erfolgreich!")
    print(f"   Neue Tabellen:")
    
    for table in ['sentiment_data', 'market_breadth']:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"   - {table}: {count} Einträge")
    
    conn.close()
    
    return True


def verify_upgrade():
    """Überprüft ob die neuen Tabellen existieren."""
    
    print("\n🔍 Verifiziere Schema-Upgrade...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    new_tables = ['sentiment_data', 'market_breadth']
    
    existing_tables = [
        row[0] for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    
    all_ok = True
    for table in new_tables:
        if table in existing_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} FEHLT!")
            all_ok = False
    
    conn.close()
    
    return all_ok


if __name__ == "__main__":
    print("="*60)
    print("SCHEMA-UPGRADE: SENTIMENT & MARKTBREITE")
    print("="*60)
    print()
    
    try:
        upgrade_schema()
        
        if verify_upgrade():
            print("\n🎉 Schema erfolgreich erweitert!")
            print(f"📂 Pfad: {DB_PATH}")
            print("\n📝 HINWEIS:")
            print("   - sentiment_data: Bereit für VIX, Fear & Greed, AAII, Put/Call")
            print("   - market_breadth: Leer, wird später von TradingTool befüllt")
        else:
            print("\n❌ Schema-Upgrade fehlgeschlagen!")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
