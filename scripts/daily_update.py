#!/usr/bin/env python3
"""
Tägliches Update-Script für Marktdaten.
Läuft als Cron-Job oder manuell.

Autor: Trading System v2
Datum: 2026-01-08
"""

import sqlite3
import yaml
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
import time
import json


BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DB_PATH = BASE_DIR / "market_data.db"
LOG_DIR = BASE_DIR / "logs"
STATUS_FILE = BASE_DIR / "update_status.json"


def load_config():
    """Lädt die Konfiguration."""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def setup_logging():
    """Richtet Logging ein."""
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = LOG_DIR / f"update_{timestamp}.log"
    return log_file


def log_message(message, log_file=None):
    """Schreibt eine Log-Nachricht."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    if log_file:
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')


def update_status(status, current=0, total=0, message="", phase="ohlcv"):
    """Schreibt Update-Status in JSON-Datei für GUI."""
    status_data = {
        'status': status,  # 'running', 'completed', 'error'
        'phase': phase,    # 'ohlcv', 'sentiment', 'completed'
        'current': current,
        'total': total,
        'progress': (current / total * 100) if total > 0 else 0,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        print(f"Warnung: Konnte Status nicht schreiben: {e}")


def get_symbols_to_update():
    """Holt die Liste der zu aktualisierenden Symbole aus der DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Alle aktiven Symbole
    symbols = cursor.execute("""
        SELECT symbol FROM asset_metadata 
        WHERE is_active = 1
        ORDER BY symbol
    """).fetchall()
    
    conn.close()
    
    return [s[0] for s in symbols]


def get_last_date(symbol):
    """Holt das letzte verfügbare Datum für ein Symbol."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    result = cursor.execute("""
        SELECT MAX(date) FROM price_data 
        WHERE symbol = ?
    """, (symbol,)).fetchone()
    
    conn.close()
    
    return result[0] if result[0] else None


def update_symbol(symbol, start_date=None, log_file=None):
    """Aktualisiert Daten für ein einzelnes Symbol."""
    
    try:
        # Bestimme Start-Datum
        if not start_date:
            last_date = get_last_date(symbol)
            if last_date:
                # Starte einen Tag nach letztem Datum
                start_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                # Neues Symbol: Lade 20 Jahre Historie
                start_date = (datetime.now() - timedelta(days=365*20)).strftime('%Y-%m-%d')
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Download von yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
        
        if df.empty:
            log_message(f"   [{symbol}] Keine neuen Daten", log_file)
            return 0
        
        # Speichere in DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        inserted = 0
        for date, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO price_data 
                    (symbol, date, open, high, low, close, adj_close, volume, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'yfinance')
                """, (
                    symbol,
                    date.strftime('%Y-%m-%d'),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row['Close']),  # Adjusted Close = Close (da auto_adjust=True)
                    int(row['Volume'])
                ))
                inserted += 1
            except Exception as e:
                log_message(f"   [{symbol}] Fehler bei Datum {date}: {e}", log_file)
        
        conn.commit()
        
        # Update asset_metadata
        cursor.execute("""
            UPDATE asset_metadata 
            SET last_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (end_date, symbol))
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            log_message(f"   [{symbol}] ✅ {inserted} neue Datenpunkte", log_file)
        
        return inserted
        
    except Exception as e:
        log_message(f"   [{symbol}] ❌ Fehler: {e}", log_file)
        return 0


def update_sentiment_indicators(log_file=None):
    """Aktualisiert Sentiment-Indikatoren (VIX, VDAX, etc.) via yfinance."""
    
    # Volatilitäts-Indices (nur verfügbare über yfinance)
    sentiment_symbols = {
        '^VIX': 'VIX',      # S&P 500 Volatility
        '^VXN': 'VXN',      # Nasdaq 100 Volatility
        '^OVX': 'OVX',      # Oil Volatility
        '^GVZ': 'GVZ',      # Gold Volatility
        '^EVZ': 'EVZ',      # Emerging Markets Volatility
        # '^VDAX': 'VDAX',   # NICHT VERFÜGBAR über yfinance
        # '^VSTOXX': 'VSTOXX', # NICHT VERFÜGBAR über yfinance
        # '^RVX': 'RVX'      # NICHT VERFÜGBAR über yfinance
    }
    
    log_message(f"📊 Starte Sentiment-Update für {len(sentiment_symbols)} Indikatoren", log_file)
    
    # Update Status
    update_status(
        status='running',
        phase='sentiment',
        current=0,
        total=len(sentiment_symbols),
        message="Lade Sentiment-Indikatoren..."
    )
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    errors = 0
    
    # Bestimme Zeitraum
    # Hole letztes Datum aus sentiment_data
    last_date_result = cursor.execute("""
        SELECT MAX(date) FROM sentiment_data
    """).fetchone()
    
    if last_date_result[0]:
        start_date = (datetime.strptime(last_date_result[0], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        # Erstes Mal: Lade 20 Jahre Historie
        start_date = (datetime.now() - timedelta(days=365*20)).strftime('%Y-%m-%d')
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for idx, (yf_symbol, indicator_name) in enumerate(sentiment_symbols.items(), 1):
        log_message(f"   [{indicator_name}] Lade Daten...", log_file)
        
        # Update Status
        update_status(
            status='running',
            phase='sentiment',
            current=idx,
            total=len(sentiment_symbols),
            message=f"Lade {indicator_name}..."
        )
        
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            
            if df.empty:
                log_message(f"   [{indicator_name}] Keine neuen Daten", log_file)
                continue
            
            inserted = 0
            for date, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO sentiment_data 
                        (indicator, date, value, value_high, value_low, source)
                        VALUES (?, ?, ?, ?, ?, 'yfinance')
                    """, (
                        indicator_name,
                        date.strftime('%Y-%m-%d'),
                        float(row['Close']),  # Hauptwert = Close
                        float(row['High']) if 'High' in row else None,
                        float(row['Low']) if 'Low' in row else None
                    ))
                    inserted += 1
                except Exception as e:
                    log_message(f"   [{indicator_name}] Fehler bei {date}: {e}", log_file)
            
            conn.commit()
            total_inserted += inserted
            
            if inserted > 0:
                log_message(f"   [{indicator_name}] ✅ {inserted} neue Datenpunkte", log_file)
            
            # Rate Limit
            time.sleep(1)
            
        except Exception as e:
            log_message(f"   [{indicator_name}] ❌ Fehler: {e}", log_file)
            errors += 1
    
    conn.close()
    
    log_message(f"📊 Sentiment-Update: {total_inserted} neue Datenpunkte, {errors} Fehler", log_file)
    
    return total_inserted, errors


def update_all_symbols(log_file=None):
    """Aktualisiert alle aktiven Symbole."""
    
    symbols = get_symbols_to_update()
    log_message(f"🔄 Starte Update für {len(symbols)} Symbole", log_file)
    
    total_inserted = 0
    errors = 0
    start_time = time.time()
    
    for i, symbol in enumerate(symbols, 1):
        log_message(f"   [{i}/{len(symbols)}] {symbol}", log_file)
        
        # Update Status für GUI
        update_status(
            status='running',
            phase='ohlcv',
            current=i,
            total=len(symbols),
            message=f"Lade {symbol}..."
        )
        
        try:
            inserted = update_symbol(symbol, log_file=log_file)
            total_inserted += inserted
            
            # Rate Limit: 1 Request pro Sekunde (yfinance Limit)
            time.sleep(1)
            
        except Exception as e:
            log_message(f"   [{symbol}] FEHLER: {e}", log_file)
            errors += 1
    
    duration = time.time() - start_time
    
    log_message("="*60, log_file)
    log_message(f"✅ Update abgeschlossen", log_file)
    log_message(f"   Symbole: {len(symbols)}", log_file)
    log_message(f"   Neue Datenpunkte: {total_inserted:,}", log_file)
    log_message(f"   Fehler: {errors}", log_file)
    log_message(f"   Dauer: {duration:.1f} Sekunden", log_file)
    log_message("="*60, log_file)
    
    # Speichere Update-Log in DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO update_log 
        (update_type, symbols_updated, records_inserted, duration_seconds, status, started_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        'daily_update',
        len(symbols),
        total_inserted,
        duration,
        'success' if errors == 0 else 'partial',
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    conn.commit()
    conn.close()
    
    return total_inserted, errors


def main():
    """Hauptfunktion."""
    
    log_file = setup_logging()
    
    log_message("="*60, log_file)
    log_message("MARKTDATEN TÄGLICHES UPDATE", log_file)
    log_message("="*60, log_file)
    log_message(f"Datenbank: {DB_PATH}", log_file)
    log_message(f"Log: {log_file}", log_file)
    log_message("", log_file)
    
    try:
        # 1) Update OHLCV-Daten (Aktien, Indizes, etc.)
        inserted, errors = update_all_symbols(log_file)
        
        log_message("", log_file)
        
        # 2) Update Sentiment-Indikatoren (VIX, VDAX, etc.)
        sentiment_inserted, sentiment_errors = update_sentiment_indicators(log_file)
        
        total_errors = errors + sentiment_errors
        
        log_message("", log_file)
        log_message("="*60, log_file)
        log_message("📊 GESAMT-ZUSAMMENFASSUNG", log_file)
        log_message("="*60, log_file)
        log_message(f"   OHLCV-Daten: {inserted:,} neue Datenpunkte, {errors} Fehler", log_file)
        log_message(f"   Sentiment: {sentiment_inserted:,} neue Datenpunkte, {sentiment_errors} Fehler", log_file)
        log_message(f"   TOTAL: {inserted + sentiment_inserted:,} neue Datenpunkte", log_file)
        log_message("="*60, log_file)
        
        if total_errors == 0:
            log_message("\n🎉 Update erfolgreich!", log_file)
            update_status(
                status='completed',
                phase='completed',
                current=0,
                total=0,
                message="Update erfolgreich abgeschlossen!"
            )
            return True
        else:
            log_message(f"\n⚠️  Update mit {total_errors} Fehlern abgeschlossen!", log_file)
            update_status(
                status='completed',
                phase='completed',
                current=0,
                total=0,
                message=f"Update mit {total_errors} Fehlern abgeschlossen"
            )
            return False
            
    except Exception as e:
        log_message(f"\n❌ KRITISCHER FEHLER: {e}", log_file)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
