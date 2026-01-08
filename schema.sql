CREATE TABLE price_data (
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
        );
CREATE INDEX idx_price_symbol ON price_data(symbol);
CREATE INDEX idx_price_date ON price_data(date);
CREATE INDEX idx_price_quality ON price_data(data_quality);
CREATE TABLE asset_metadata (
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
        , timeframe TEXT DEFAULT '1d', asset_group TEXT, has_ohlc INTEGER DEFAULT 1, has_volume INTEGER DEFAULT 1, data_quality_score REAL DEFAULT 1.0);
CREATE INDEX idx_asset_type ON asset_metadata(asset_type);
CREATE INDEX idx_asset_sector ON asset_metadata(sector);
CREATE INDEX idx_asset_active ON asset_metadata(is_active);
CREATE TABLE indicators_cache (
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            indicator_name TEXT NOT NULL,
            value REAL NOT NULL,
            calculation_version TEXT DEFAULT 'v1',
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, date, indicator_name)
        );
CREATE INDEX idx_indicator_symbol ON indicators_cache(symbol);
CREATE INDEX idx_indicator_date ON indicators_cache(date);
CREATE INDEX idx_indicator_name ON indicators_cache(indicator_name);
CREATE TABLE data_quality_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            issue_type TEXT,
            severity TEXT,
            description TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_quality_symbol ON data_quality_log(symbol);
CREATE INDEX idx_quality_severity ON data_quality_log(severity);
CREATE TABLE update_log (
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
        );
