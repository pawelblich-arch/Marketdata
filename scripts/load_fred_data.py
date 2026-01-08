#!/usr/bin/env python3
"""
FRED API Integration für makroökonomische Sentiment-Daten.
Benötigt: pip install fredapi

API Key von: https://fred.stlouisfed.org/docs/api/api_key.html

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import os

DB_PATH = Path(__file__).parent.parent / "market_data.db"

# FRED API Key (aus Umgebungsvariable oder hier setzen)
FRED_API_KEY = os.environ.get('FRED_API_KEY', 'c8d18ec533d8ff68535fb656d68de586')


def load_fred_series(series_id, indicator_name, description=""):
    """Lädt eine FRED Serie und speichert sie in der DB."""
    
    try:
        from fredapi import Fred
    except ImportError:
        print("❌ fredapi nicht installiert!")
        print("   Installieren Sie: pip install fredapi")
        return 0
    
    if FRED_API_KEY == 'YOUR_API_KEY_HERE':
        print("❌ FRED_API_KEY nicht gesetzt!")
        print("   Setzen Sie: export FRED_API_KEY='your_key'")
        print("   Oder editieren Sie das Script")
        return 0
    
    print(f"📊 Lade {indicator_name} ({series_id})...")
    
    try:
        fred = Fred(api_key=FRED_API_KEY)
        
        # Lade Serie
        data = fred.get_series(series_id)
        
        if data.empty:
            print(f"   ⚠️ Keine Daten verfügbar")
            return 0
        
        print(f"   ✅ {len(data)} Datenpunkte geladen")
        print(f"   📅 {data.index[0].strftime('%Y-%m-%d')} bis {data.index[-1].strftime('%Y-%m-%d')}")
        
        # Speichere in DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for date, value in data.items():
            if pd.notna(value):
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO sentiment_data 
                        (indicator, date, value, source, metadata)
                        VALUES (?, ?, ?, 'fred', ?)
                    """, (
                        indicator_name,
                        date.strftime('%Y-%m-%d'),
                        float(value),
                        f'{{"series_id": "{series_id}", "description": "{description}"}}'
                    ))
                    saved += 1
                except Exception as e:
                    print(f"   ⚠️ Fehler bei {date}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {saved} Datenpunkte gespeichert")
        return saved
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return 0


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("FRED API - MAKROÖKONOMISCHE DATEN")
    print("="*60)
    print()
    
    # Wichtige Sentiment-relevante FRED Serien
    series = [
        # High Yield Spreads (Credit Risk)
        ('BAMLH0A0HYM2', 'HY_SPREAD', 'High Yield OAS Spread'),
        
        # Treasury Yields
        ('DGS10', 'TREASURY_10Y', '10-Year Treasury Yield'),
        ('DGS2', 'TREASURY_2Y', '2-Year Treasury Yield'),
        
        # Credit Spreads
        ('BAMLC0A0CM', 'CORP_SPREAD', 'Corporate Bond Spread'),
        
        # Unemployment (Sentiment-relevant)
        ('UNRATE', 'UNEMPLOYMENT', 'Unemployment Rate'),
        
        # VIX von FRED (falls verfügbar)
        ('VIXCLS', 'VIX_FRED', 'CBOE VIX Close (FRED)'),
    ]
    
    total_saved = 0
    
    for series_id, indicator_name, description in series:
        saved = load_fred_series(series_id, indicator_name, description)
        total_saved += saved
        print()
    
    print("="*60)
    print(f"✅ GESAMT: {total_saved} Datenpunkte geladen")
    print("="*60)
    print()
    print("💡 TIPP: Führen Sie dieses Script regelmäßig aus")
    print("   (z.B. wöchentlich, da FRED-Daten sich selten ändern)")
    print()


if __name__ == "__main__":
    import pandas as pd
    main()
