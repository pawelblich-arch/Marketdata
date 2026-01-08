#!/usr/bin/env python3
"""
Erstellt index_memberships Tabelle für Multi-Index-Support.
Ein Asset kann in mehreren Indices sein (z.B. AAPL in S&P 500 UND Nasdaq 100).

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def create_membership_table():
    """Erstellt index_memberships Tabelle."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("📊 Erstelle index_memberships Tabelle...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS index_memberships (
            symbol TEXT NOT NULL,
            index_name TEXT NOT NULL,
            added_date TEXT DEFAULT (date('now')),
            is_active INTEGER DEFAULT 1,
            PRIMARY KEY (symbol, index_name),
            FOREIGN KEY (symbol) REFERENCES asset_metadata(symbol)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_memberships_symbol 
        ON index_memberships(symbol)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_memberships_index 
        ON index_memberships(index_name)
    """)
    
    conn.commit()
    
    print("✅ Tabelle erstellt!")
    print("\n📝 HINWEIS:")
    print("   - asset_metadata.asset_group bleibt für primären Index")
    print("   - index_memberships für alle Memberships (inkl. Mehrfach)")
    
    conn.close()


if __name__ == "__main__":
    print("="*60)
    print("INDEX MEMBERSHIPS TABELLE")
    print("="*60)
    print()
    
    create_membership_table()
    
    print("\n💡 Nächster Schritt:")
    print("   Nutzen Sie diese Tabelle für Multi-Index-Support")
    print()
