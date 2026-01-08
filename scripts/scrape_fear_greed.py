#!/usr/bin/env python3
"""
Fear & Greed Index Scraper.
Lädt den CNN Fear & Greed Index und speichert ihn in der DB.

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import requests
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def fetch_fear_greed():
    """Holt Fear & Greed Index von CNN."""
    
    print("📊 Lade Fear & Greed Index...")
    
    # CNN API URL
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.cnn.com/markets/fear-and-greed'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Aktueller Wert
        current = data.get('fear_and_greed', {})
        current_value = current.get('score')
        current_rating = current.get('rating')
        current_timestamp = current.get('timestamp')
        
        if not current_value or not current_timestamp:
            print("   ⚠️ Keine aktuellen Daten verfügbar")
            return []
        
        # Timestamp in Datum konvertieren
        try:
            # Versuche ISO-Format (z.B. '2026-01-08T18:18:22+00:00')
            current_date = datetime.fromisoformat(current_timestamp.replace('+00:00', '')).strftime('%Y-%m-%d')
        except:
            # Fallback: Millisekunden-Timestamp
            current_date = datetime.fromtimestamp(int(current_timestamp) / 1000).strftime('%Y-%m-%d')
        
        results = [{
            'date': current_date,
            'value': float(current_value),
            'rating': current_rating,
            'previous_close': current.get('previous_close'),
            'previous_1_week': current.get('previous_1_week'),
            'previous_1_month': current.get('previous_1_month'),
            'previous_1_year': current.get('previous_1_year')
        }]
        
        print(f"   ✅ Aktueller Wert: {current_value} ({current_rating})")
        print(f"   📅 Datum: {current_date}")
        
        # Historische Daten
        historical = data.get('fear_and_greed_historical', {}).get('data', [])
        
        if historical:
            print(f"   📊 {len(historical)} historische Datenpunkte verfügbar")
            
            for item in historical:
                try:
                    item_date = datetime.fromtimestamp(int(item['x']) / 1000).strftime('%Y-%m-%d')
                    results.append({
                        'date': item_date,
                        'value': float(item['y']),
                        'rating': None,
                        'previous_close': None,
                        'previous_1_week': None,
                        'previous_1_month': None,
                        'previous_1_year': None
                    })
                except Exception as e:
                    print(f"   ⚠️ Fehler bei historischem Datenpunkt: {e}")
        
        print(f"   ✅ Gesamt: {len(results)} Datenpunkte geladen")
        return results
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 418:
            print(f"   ❌ Cloudflare-Block (418)")
            print(f"   💡 Tipp: Später nochmal versuchen oder VPN nutzen")
        else:
            print(f"   ❌ HTTP Fehler: {e}")
        return []
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return []


def save_to_db(data_list):
    """Speichert Fear & Greed Daten in DB."""
    
    if not data_list:
        return 0
    
    print(f"\n💾 Speichere {len(data_list)} Datenpunkte...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved = 0
    
    for data in data_list:
        try:
            # Metadata als JSON
            metadata = json.dumps({
                'rating': data['rating'],
                'previous_close': data['previous_close'],
                'previous_1_week': data['previous_1_week'],
                'previous_1_month': data['previous_1_month'],
                'previous_1_year': data['previous_1_year']
            })
            
            cursor.execute("""
                INSERT OR REPLACE INTO sentiment_data 
                (indicator, date, value, source, metadata)
                VALUES ('FEAR_GREED', ?, ?, 'cnn', ?)
            """, (data['date'], data['value'], metadata))
            
            saved += 1
            
        except Exception as e:
            print(f"   ⚠️ Fehler bei {data['date']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ {saved} Datenpunkte gespeichert")
    
    return saved


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("FEAR & GREED INDEX SCRAPER")
    print("="*60)
    print()
    
    try:
        # Lade Daten
        data = fetch_fear_greed()
        
        if not data:
            print("\n⚠️ Keine Daten geladen")
            return False
        
        # Speichere in DB
        saved = save_to_db(data)
        
        print("\n" + "="*60)
        print("✅ SCRAPING ERFOLGREICH")
        print("="*60)
        print(f"\n   {saved} Datenpunkte gespeichert")
        print(f"   Aktueller Wert: {data[0]['value']} ({data[0]['rating']})")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
