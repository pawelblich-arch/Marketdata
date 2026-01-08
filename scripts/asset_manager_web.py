#!/usr/bin/env python3
"""
Asset Manager - Streamlit Web GUI (Multi-Table View)
Moderne Web-Oberfläche zur Verwaltung der MarketData Assets

Autor: Trading System v2
Datum: 2026-01-08
"""

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Pfade
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "market_data.db"

# Seitenkonfiguration
st.set_page_config(
    page_title="MarketData Asset Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    /* Deploy-Button ausblenden */
    [data-testid="stToolbar"] {
        display: none;
    }
    header {
        visibility: hidden;
    }
    /* Tabellen-Header Styling */
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection():
    """DB-Verbindung (gecached)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def load_assets_by_group(asset_group=None, asset_type=None):
    """Lädt Assets nach Gruppe/Typ."""
    conn = get_connection()
    
    where_clauses = ["a.is_active = 1"]  # Nur aktive Assets
    
    if asset_group:
        where_clauses.append(f"a.asset_group = '{asset_group}'")
    
    if asset_type:
        where_clauses.append(f"a.asset_type = '{asset_type}'")
    
    where_clause = "WHERE " + " AND ".join(where_clauses)
    
    query = f"""
        SELECT 
            a.symbol,
            a.name,
            a.asset_type,
            a.sector,
            a.exchange,
            a.timeframe,
            a.first_date,
            a.last_date,
            COUNT(p.date) as data_points,
            a.has_ohlc,
            a.has_volume,
            a.data_quality_score
        FROM asset_metadata a
        LEFT JOIN price_data p ON a.symbol = p.symbol
        {where_clause}
        GROUP BY a.symbol
        ORDER BY a.symbol
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Formatierung
    if not df.empty:
        df['name'] = df['name'].fillna('N/A')
        df['sector'] = df['sector'].fillna('-')
        df['exchange'] = df['exchange'].fillna('-')
        df['ohlc'] = df['has_ohlc'].apply(lambda x: '✅' if x == 1 else '❌')
        df['volume'] = df['has_volume'].apply(lambda x: '✅' if x == 1 else '❌')
        df['quality'] = df['data_quality_score'].apply(lambda x: f"{x:.0%}" if pd.notna(x) else "N/A")
        df['data_points'] = df['data_points'].apply(lambda x: f"{x:,}")
    
    return df


def load_sentiment_data():
    """Lädt Sentiment-Indikatoren mit letzten Werten."""
    conn = get_connection()
    
    query = """
        SELECT 
            s.indicator,
            s.date,
            s.value,
            s.source
        FROM sentiment_data s
        INNER JOIN (
            SELECT indicator, MAX(date) as max_date
            FROM sentiment_data
            GROUP BY indicator
        ) latest ON s.indicator = latest.indicator AND s.date = latest.max_date
        ORDER BY s.indicator
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Formatierung
    if not df.empty:
        df['value'] = df['value'].apply(lambda x: f"{x:.2f}")
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    return df


def display_asset_table(title, emoji, df, key_suffix):
    """Zeigt eine Asset-Tabelle an."""
    
    st.markdown(f"""
    <div class="section-header">
        <h2>{emoji} {title}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if df.empty:
        st.info(f"Keine {title} in der Datenbank.")
        return
    
    # Statistik
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Assets", len(df))
    with col2:
        total_points = df['data_points'].str.replace(',', '').astype(int).sum()
        st.metric("Datenpunkte", f"{total_points:,}")
    with col3:
        if 'data_quality_score' in df.columns:
            avg_quality = df['data_quality_score'].mean()
            st.metric("Qualität Ø", f"{avg_quality:.0%}")
    
    # Tabelle
    display_columns = {
        'symbol': 'Symbol',
        'name': 'Name',
        'sector': 'Sektor',
        'exchange': 'Exchange',
        'timeframe': 'Zeitrahmen',
        'first_date': 'Von',
        'last_date': 'Bis',
        'data_points': 'Datenpunkte',
        'ohlc': 'OHLC',
        'volume': 'Vol',
        'quality': 'Qualität'
    }
    
    display_df = df[list(display_columns.keys())].copy()
    display_df.columns = list(display_columns.values())
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(len(df) * 35 + 50, 400),  # Dynamische Höhe
        key=f"table_{key_suffix}"
    )


def display_sentiment_table(df):
    """Zeigt Sentiment-Indikatoren-Tabelle an."""
    
    st.markdown("""
    <div class="section-header">
        <h2>📊 SENTIMENT & INDIKATOREN</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if df.empty:
        st.info("Keine Sentiment-Daten verfügbar. Führen Sie 'MarketData_Update.command' aus.")
        return
    
    # Statistik
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Indikatoren", len(df))
    with col2:
        latest_date = df['date'].max()
        st.metric("Letztes Update", latest_date)
    with col3:
        sources = df['source'].nunique()
        st.metric("Quellen", sources)
    
    # Tabelle
    display_df = df[['indicator', 'value', 'date', 'source']].copy()
    display_df.columns = ['Indikator', 'Wert', 'Datum', 'Quelle']
    
    # Indikator-Namen verschönern
    indicator_names = {
        'VIX': '📉 VIX (S&P 500 Volatility)',
        'VDAX': '📉 VDAX (DAX Volatility)',
        'VSTOXX': '📉 VSTOXX (EuroStoxx Volatility)',
        'OVX': '📉 OVX (Oil Volatility)',
        'GVZ': '📉 GVZ (Gold Volatility)',
        'EVZ': '📉 EVZ (Emerging Markets Volatility)',
        'VXN': '📉 VXN (Nasdaq 100 Volatility)',
        'RVX': '📉 RVX (Russell 2000 Volatility)',
        'FEAR_GREED': '😨 Fear & Greed Index',
        'AAII_BULL': '🐂 AAII Bullish Sentiment',
        'AAII_BEAR': '🐻 AAII Bearish Sentiment',
        'PUT_CALL_EQUITY': '📊 Put/Call Ratio (Equity)',
        'PUT_CALL_TOTAL': '📊 Put/Call Ratio (Total)'
    }
    
    display_df['Indikator'] = display_df['Indikator'].apply(lambda x: indicator_names.get(x, x))
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(len(df) * 35 + 50, 400),
        key="table_sentiment"
    )


def main():
    """Hauptfunktion."""
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 MarketData Asset Manager")
        st.caption("Zentrale Verwaltung aller Marktdaten-Assets")
    with col2:
        if st.button("🔄 Aktualisieren", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Gesamtstatistik
    conn = get_connection()
    total_assets = pd.read_sql_query("SELECT COUNT(*) as count FROM asset_metadata WHERE is_active = 1", conn)['count'][0]
    total_datapoints = pd.read_sql_query("SELECT COUNT(*) as count FROM price_data", conn)['count'][0]
    total_sentiment = pd.read_sql_query("SELECT COUNT(DISTINCT indicator) as count FROM sentiment_data", conn)['count'][0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Aktive Assets", f"{total_assets:,}")
    with col2:
        st.metric("📊 OHLCV Datenpunkte", f"{total_datapoints:,}")
    with col3:
        st.metric("📈 Sentiment-Indikatoren", f"{total_sentiment}")
    with col4:
        last_update = pd.read_sql_query("SELECT MAX(completed_at) as last FROM update_log", conn)['last'][0]
        if last_update:
            last_update_date = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
            st.metric("🕐 Letztes Update", last_update_date)
        else:
            st.metric("🕐 Letztes Update", "N/A")
    
    st.markdown("---")
    
    # === TABELLE 1: INDICES ===
    indices_df = load_assets_by_group(asset_type='index')
    display_asset_table("INDICES", "📈", indices_df, "indices")
    
    # === TABELLE 2: ROHSTOFFE & METALLE ===
    commodities_df = load_assets_by_group(asset_type='commodity')
    display_asset_table("ROHSTOFFE & METALLE", "🥇", commodities_df, "commodities")
    
    # === TABELLE 3: SENTIMENT & INDIKATOREN ===
    sentiment_df = load_sentiment_data()
    display_sentiment_table(sentiment_df)
    
    # === TABELLE 4: S&P 500 AKTIEN ===
    sp500_df = load_assets_by_group(asset_group='sp500')
    display_asset_table("S&P 500 AKTIEN", "🇺🇸", sp500_df, "sp500")
    
    # === TABELLE 5: NASDAQ 100 AKTIEN ===
    nasdaq_df = load_assets_by_group(asset_group='nasdaq100')
    display_asset_table("NASDAQ 100 AKTIEN", "💻", nasdaq_df, "nasdaq")
    
    # === TABELLE 6: DAX 40 AKTIEN ===
    dax_df = load_assets_by_group(asset_group='dax')
    display_asset_table("DAX 40 AKTIEN", "🇩🇪", dax_df, "dax")
    
    # === FOOTER ===
    st.markdown("---")
    st.caption("""
    💡 **Tipps:**  
    - Assets hinzufügen: Datenbank direkt editieren oder über TradingTool  
    - Daten aktualisieren: `MarketData_Update.command` ausführen  
    - Sentiment-Update: `Update_Sentiment_External.command` ausführen  
    """)


if __name__ == "__main__":
    main()
