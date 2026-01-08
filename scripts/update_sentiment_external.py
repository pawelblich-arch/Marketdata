#!/usr/bin/env python3
"""
Update-Script für externe Sentiment-Daten:
- Fear & Greed Index (CNN)
- AAII Sentiment Survey
- Put/Call Ratio (CBOE)

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "market_data.db"
LOG_DIR = BASE_DIR / "logs"


def log_message(message, log_file=None):
    """Schreibt eine Log-Nachricht."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    if log_file:
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')


def fetch_fear_greed_index(log_file=None):
    """
    Holt den Fear & Greed Index von CNN.
    API: https://production.dataviz.cnn.io/index/fearandgreed/graphdata
    """
    
    log_message("📊 Fear & Greed Index: Lade Daten...", log_file)
    
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Aktueller Wert
        current_value = data.get('fear_and_greed', {}).get('score')
        current_timestamp = data.get('fear_and_greed', {}).get('timestamp')
        
        if not current_value or not current_timestamp:
            log_message("   ⚠️  Keine aktuellen Daten verfügbar", log_file)
            return []
        
        # Timestamp in Datum konvertieren
        # Timestamp ist in Millisekunden
        current_date = datetime.fromtimestamp(int(current_timestamp) / 1000).strftime('%Y-%m-%d')
        
        results = [{
            'indicator': 'FEAR_GREED',
            'date': current_date,
            'value': float(current_value),
            'source': 'cnn',
            'metadata': json.dumps({
                'rating': data.get('fear_and_greed', {}).get('rating'),
                'previous_close': data.get('fear_and_greed', {}).get('previous_close'),
                'previous_1_week': data.get('fear_and_greed', {}).get('previous_1_week'),
                'previous_1_month': data.get('fear_and_greed', {}).get('previous_1_month'),
                'previous_1_year': data.get('fear_and_greed', {}).get('previous_1_year')
            })
        }]
        
        # Historische Daten (wenn verfügbar)
        historical = data.get('fear_and_greed_historical', {}).get('data', [])
        for item in historical:
            item_date = datetime.fromtimestamp(int(item['x']) / 1000).strftime('%Y-%m-%d')
            results.append({
                'indicator': 'FEAR_GREED',
                'date': item_date,
                'value': float(item['y']),
                'source': 'cnn',
                'metadata': None
            })
        
        log_message(f"   ✅ {len(results)} Datenpunkte geladen (aktueller Wert: {current_value})", log_file)
        return results
        
    except Exception as e:
        log_message(f"   ❌ Fehler: {e}", log_file)
        return []


def fetch_aaii_sentiment(log_file=None):
    """
    Holt AAII Sentiment Survey.
    
    HINWEIS: AAII bietet keine öffentliche API.
    Optionen:
    1. Web Scraping (erfordert Subscription)
    2. Manuelle CSV-Imports
    3. Alternative Datenquelle (z.B. Quandl)
    
    Für jetzt: Placeholder-Funktion
    """
    
    log_message("📊 AAII Sentiment: Übersprungen (keine öffentliche API)", log_file)
    log_message("   💡 Alternative: Manuelle CSV-Imports oder Quandl API", log_file)
    
    return []


def fetch_put_call_ratio(log_file=None):
    """
    Holt Put/Call Ratio.
    
    HINWEIS: CBOE bietet Daten an, aber meist via yfinance:
    - Symbol: $CPCE (Equity Put/Call Ratio)
    - Symbol: $CPC (Total Put/Call Ratio)
    
    Wir versuchen beide über yfinance.
    """
    
    log_message("📊 Put/Call Ratio: Lade Daten (yfinance)...", log_file)
    
    try:
        import yfinance as yf
        
        pc_symbols = {
            '$CPCE': 'PUT_CALL_EQUITY',
            '$CPC': 'PUT_CALL_TOTAL'
        }
        
        results = []
        
        # Hole letzte 5 Tage (für aktuelle Werte)
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        for symbol, indicator_name in pc_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
                
                if df.empty:
                    log_message(f"   ⚠️  {indicator_name}: Keine Daten verfügbar (evtl. Symbol falsch)", log_file)
                    continue
                
                for date, row in df.iterrows():
                    results.append({
                        'indicator': indicator_name,
                        'date': date.strftime('%Y-%m-%d'),
                        'value': float(row['Close']),
                        'source': 'yfinance',
                        'metadata': None
                    })
                
                log_message(f"   ✅ {indicator_name}: {len(df)} Datenpunkte", log_file)
                
            except Exception as e:
                log_message(f"   ❌ {indicator_name}: {e}", log_file)
        
        if not results:
            log_message("   💡 Alternative: CBOE direkt oder andere API", log_file)
        
        return results
        
    except Exception as e:
        log_message(f"   ❌ Fehler: {e}", log_file)
        return []


def save_sentiment_data(data_list, log_file=None):
    """Speichert Sentiment-Daten in die Datenbank."""
    
    if not data_list:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    
    for data in data_list:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO sentiment_data 
                (indicator, date, value, source, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data['indicator'],
                data['date'],
                data['value'],
                data['source'],
                data.get('metadata')
            ))
            inserted += 1
        except Exception as e:
            log_message(f"   ⚠️  Fehler beim Speichern: {e}", log_file)
    
    conn.commit()
    conn.close()
    
    return inserted


def main():
    """Hauptfunktion."""
    
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"sentiment_external_{timestamp}.log"
    
    log_message("="*60, log_file)
    log_message("EXTERNE SENTIMENT-DATEN UPDATE", log_file)
    log_message("="*60, log_file)
    log_message(f"Datenbank: {DB_PATH}", log_file)
    log_message(f"Log: {log_file}", log_file)
    log_message("", log_file)
    
    total_inserted = 0
    
    try:
        # 1) Fear & Greed Index
        fear_greed_data = fetch_fear_greed_index(log_file)
        inserted = save_sentiment_data(fear_greed_data, log_file)
        total_inserted += inserted
        log_message(f"   → {inserted} Fear & Greed Datenpunkte gespeichert", log_file)
        
        time.sleep(2)  # Rate Limit
        
        # 2) AAII Sentiment (Placeholder)
        aaii_data = fetch_aaii_sentiment(log_file)
        inserted = save_sentiment_data(aaii_data, log_file)
        total_inserted += inserted
        
        time.sleep(2)
        
        # 3) Put/Call Ratio
        pc_data = fetch_put_call_ratio(log_file)
        inserted = save_sentiment_data(pc_data, log_file)
        total_inserted += inserted
        log_message(f"   → {inserted} Put/Call Datenpunkte gespeichert", log_file)
        
        log_message("", log_file)
        log_message("="*60, log_file)
        log_message(f"✅ Update abgeschlossen: {total_inserted} neue Datenpunkte", log_file)
        log_message("="*60, log_file)
        
        return True
        
    except Exception as e:
        log_message(f"\n❌ KRITISCHER FEHLER: {e}", log_file)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
