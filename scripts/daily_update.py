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


BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DB_PATH = BASE_DIR / "market_data.db"
LOG_DIR = BASE_DIR / "logs"


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


def update_all_symbols(log_file=None):
    """Aktualisiert alle aktiven Symbole."""
    
    symbols = get_symbols_to_update()
    log_message(f"🔄 Starte Update für {len(symbols)} Symbole", log_file)
    
    total_inserted = 0
    errors = 0
    start_time = time.time()
    
    for i, symbol in enumerate(symbols, 1):
        log_message(f"   [{i}/{len(symbols)}] {symbol}", log_file)
        
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
        inserted, errors = update_all_symbols(log_file)
        
        if errors == 0:
            log_message("\n🎉 Update erfolgreich!", log_file)
            return True
        else:
            log_message(f"\n⚠️  Update mit {errors} Fehlern abgeschlossen!", log_file)
            return False
            
    except Exception as e:
        log_message(f"\n❌ KRITISCHER FEHLER: {e}", log_file)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
