#!/usr/bin/env python3
"""
Crawler für VDAX, VSTOXX und RVX von Investing.com.
Nutzt requests + BeautifulSoup für Web Scraping.

Benötigt: pip install beautifulsoup4 lxml

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import requests
from pathlib import Path
from datetime import datetime
import time

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def get_current_value(url, selector, indicator_name):
    """Scrapt einen einzelnen Wert von einer Website."""
    
    print(f"🔍 Lade {indicator_name}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Finde den Wert (muss an Website angepasst werden)
        element = soup.select_one(selector)
        
        if element:
            value_text = element.text.strip().replace(',', '.')
            value = float(value_text)
            
            print(f"   ✅ Aktueller Wert: {value}")
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'value': value
            }
        else:
            print(f"   ⚠️ Element nicht gefunden (Selector: {selector})")
            return None
            
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return None


def save_to_db(indicator_name, data):
    """Speichert den Wert in der DB."""
    
    if not data:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO sentiment_data 
            (indicator, date, value, source)
            VALUES (?, ?, ?, 'web_scraping')
        """, (indicator_name, data['date'], data['value']))
        
        conn.commit()
        print(f"   ✅ Gespeichert: {indicator_name} = {data['value']}")
        return 1
        
    except Exception as e:
        print(f"   ⚠️ DB-Fehler: {e}")
        return 0
        
    finally:
        conn.close()


def crawl_vdax():
    """Crawlt VDAX von Investing.com."""
    
    # HINWEIS: Diese URLs und Selektoren müssen ggf. angepasst werden
    url = "https://www.investing.com/indices/volatility-vdax-new"
    selector = "span[data-test='instrument-price-last']"
    
    data = get_current_value(url, selector, "VDAX")
    
    if data:
        return save_to_db('VDAX', data)
    return 0


def crawl_vstoxx():
    """Crawlt VSTOXX von Investing.com."""
    
    url = "https://www.investing.com/indices/vstoxx"
    selector = "span[data-test='instrument-price-last']"
    
    data = get_current_value(url, selector, "VSTOXX")
    
    if data:
        return save_to_db('VSTOXX', data)
    return 0


def crawl_rvx():
    """Crawlt RVX (Russell 2000 Volatility) von Investing.com."""
    
    url = "https://www.investing.com/indices/cboe-russell-2000-volatility"
    selector = "span[data-test='instrument-price-last']"
    
    data = get_current_value(url, selector, "RVX")
    
    if data:
        return save_to_db('RVX', data)
    return 0


def main():
    """Hauptfunktion."""
    
    print("="*60)
    print("VOLATILITY INDICES WEB SCRAPER")
    print("="*60)
    print("\n⚠️  HINWEIS: Web Scraping kann instabil sein!")
    print("   - Websites können Struktur ändern")
    print("   - Rate Limits beachten")
    print("   - Nur für tägliche Updates nutzen\n")
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ BeautifulSoup nicht installiert!")
        print("   Installieren Sie: pip install beautifulsoup4 lxml")
        return
    
    saved = 0
    
    # VDAX
    saved += crawl_vdax()
    time.sleep(2)  # Rate Limiting
    
    # VSTOXX
    saved += crawl_vstoxx()
    time.sleep(2)
    
    # RVX
    saved += crawl_rvx()
    
    print("\n" + "="*60)
    print(f"✅ SCRAPING ABGESCHLOSSEN: {saved} Werte gespeichert")
    print("="*60)
    print("\n💡 TIPP:")
    print("   - Führen Sie dieses Script täglich aus")
    print("   - Prüfen Sie regelmäßig, ob Selektoren noch funktionieren")
    print("   - Bei Fehlern: Selektoren anpassen\n")


if __name__ == "__main__":
    main()
