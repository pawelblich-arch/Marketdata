#!/usr/bin/env python3
"""
Asset Manager - Streamlit Web GUI
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
    initial_sidebar_state="expanded",
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
    .asset-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    /* Deploy-Button ausblenden */
    [data-testid="stToolbar"] {
        display: none;
    }
    header {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection():
    """DB-Verbindung (gecached)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def load_assets(filter_type="all", asset_group=None):
    """Lädt Assets aus DB."""
    conn = get_connection()
    
    where_clauses = []
    
    if filter_type == "active":
        where_clauses.append("a.is_active = 1")
    elif filter_type == "inactive":
        where_clauses.append("a.is_active = 0")
    
    if asset_group and asset_group != "all":
        where_clauses.append(f"a.asset_group = '{asset_group}'")
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"""
        SELECT 
            a.symbol,
            a.asset_type,
            a.name,
            a.sector,
            a.exchange,
            a.first_date,
            a.last_date,
            a.is_active,
            a.timeframe,
            a.asset_group,
            a.has_ohlc,
            a.has_volume,
            a.data_quality_score,
            COUNT(p.date) as data_points,
            a.updated_at
        FROM asset_metadata a
        LEFT JOIN price_data p ON a.symbol = p.symbol
        {where_clause}
        GROUP BY a.symbol
        ORDER BY a.asset_group, a.asset_type, a.symbol
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Berechne Tage
    if not df.empty and 'first_date' in df.columns and 'last_date' in df.columns:
        df['days'] = pd.to_datetime(df['last_date']) - pd.to_datetime(df['first_date'])
        df['days'] = df['days'].dt.days
    
    # Status formatieren
    df['status'] = df['is_active'].apply(lambda x: '✅ Aktiv' if x == 1 else '❌ Inaktiv')
    df['ohlc_status'] = df['has_ohlc'].apply(lambda x: '✅' if x == 1 else '❌')
    df['volume_status'] = df['has_volume'].apply(lambda x: '✅' if x == 1 else '❌')
    
    return df


def add_asset(symbol, asset_type, timeframe='1d', asset_group=None, name=None, sector=None, exchange=None):
    """Fügt ein neues Asset hinzu."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO asset_metadata 
            (symbol, asset_type, timeframe, asset_group, name, sector, exchange, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (symbol, asset_type, timeframe, asset_group, name, sector, exchange))
        
        conn.commit()
        return True, f"Asset {symbol} erfolgreich hinzugefügt!"
        
    except sqlite3.IntegrityError:
        # Asset existiert schon, reaktivieren?
        cursor.execute("""
            UPDATE asset_metadata 
            SET is_active = 1, 
                timeframe = ?,
                asset_group = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (timeframe, asset_group, symbol))
        conn.commit()
        return True, f"Asset {symbol} reaktiviert!"
    
    except Exception as e:
        return False, f"Fehler: {str(e)}"


def deactivate_asset(symbol):
    """Deaktiviert ein Asset."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE asset_metadata 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (symbol,))
        
        conn.commit()
        return True, f"Asset {symbol} deaktiviert!"
    
    except Exception as e:
        return False, f"Fehler: {str(e)}"


def get_asset_details(symbol):
    """Holt Details zu einem Asset."""
    conn = get_connection()
    
    # Metadaten
    meta_query = "SELECT * FROM asset_metadata WHERE symbol = ?"
    meta = pd.read_sql_query(meta_query, conn, params=(symbol,))
    
    # Daten-Statistik
    stats_query = """
        SELECT 
            COUNT(*) as count,
            MIN(date) as first_date,
            MAX(date) as last_date,
            MIN(low) as min_price,
            MAX(high) as max_price,
            AVG(volume) as avg_volume
        FROM price_data
        WHERE symbol = ?
    """
    stats = pd.read_sql_query(stats_query, conn, params=(symbol,))
    
    # Letzte Einträge
    recent_query = """
        SELECT date, open, high, low, close, volume
        FROM price_data
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT 10
    """
    recent = pd.read_sql_query(recent_query, conn, params=(symbol,))
    
    return meta, stats, recent


def main():
    """Hauptfunktion."""
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 MarketData Asset Manager")
    with col2:
        if st.button("🔄 Aktualisieren", key="refresh"):
            st.rerun()
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Aktionen")
        
        # Filter
        st.subheader("🔍 Filter")
        
        filter_type = st.radio(
            "Status:",
            ["all", "active", "inactive"],
            format_func=lambda x: {"all": "Alle", "active": "Nur Aktive", "inactive": "Nur Inaktive"}[x],
            key="filter"
        )
        
        # Asset-Gruppen Filter
        conn = get_connection()
        groups_df = pd.read_sql_query("""
            SELECT DISTINCT asset_group 
            FROM asset_metadata 
            WHERE asset_group IS NOT NULL
            ORDER BY asset_group
        """, conn)
        
        asset_groups = ["all"] + groups_df['asset_group'].tolist()
        
        asset_group_filter = st.selectbox(
            "Asset-Gruppe:",
            asset_groups,
            format_func=lambda x: {
                "all": "Alle Gruppen",
                "sp500": "📊 S&P 500",
                "nasdaq100": "📊 Nasdaq 100",
                "dax": "📊 DAX",
                "eurostoxx": "📊 EuroStoxx",
                "index": "📈 Indizes",
                "commodity": "🥇 Rohstoffe",
                "fx": "💱 Währungen",
                "bonds": "📄 Anleihen"
            }.get(x, x.upper()),
            key="asset_group_filter"
        )
        
        st.markdown("---")
        
        # Asset hinzufügen
        st.subheader("➕ Asset hinzufügen")
        
        with st.form("add_asset"):
            symbol = st.text_input("Symbol (z.B. AAPL)", key="add_symbol").upper()
            
            col1, col2 = st.columns(2)
            with col1:
                asset_type = st.selectbox("Typ", ["stock", "index", "commodity", "fx", "bond"], key="add_type")
            with col2:
                timeframe = st.selectbox(
                    "Zeitrahmen",
                    ["5min", "15min", "30min", "1h", "1d", "1w"],
                    index=4,  # Default: 1d
                    key="add_timeframe"
                )
            
            asset_group = st.selectbox(
                "Asset-Gruppe",
                ["", "sp500", "nasdaq100", "dax", "eurostoxx", "emerging_markets", "index", "commodity", "fx", "bonds"],
                format_func=lambda x: "Keine Gruppe" if x == "" else x.upper(),
                key="add_group"
            )
            
            name = st.text_input("Name (optional)", key="add_name")
            sector = st.text_input("Sektor (optional)", key="add_sector")
            exchange = st.text_input("Exchange (optional)", key="add_exchange")
            
            submit = st.form_submit_button("➕ Hinzufügen", use_container_width=True)
            
            if submit:
                if not symbol:
                    st.error("Symbol darf nicht leer sein!")
                else:
                    success, message = add_asset(
                        symbol,
                        asset_type,
                        timeframe,
                        asset_group if asset_group else None,
                        name if name else None,
                        sector if sector else None,
                        exchange if exchange else None
                    )
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    # Hauptbereich
    df = load_assets(filter_type, asset_group_filter)
    
    if df.empty:
        st.warning("Keine Assets gefunden!")
        return
    
    # Statistik
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Gesamt", len(df))
    
    with col2:
        active = len(df[df['is_active'] == 1])
        st.metric("✅ Aktiv", active)
    
    with col3:
        inactive = len(df[df['is_active'] == 0])
        st.metric("❌ Inaktiv", inactive)
    
    with col4:
        total_points = df['data_points'].sum()
        st.metric("📊 Datenpunkte", f"{total_points:,}")
    
    with col5:
        avg_quality = df['data_quality_score'].mean() if 'data_quality_score' in df.columns else 0
        st.metric("⭐ Qualität Ø", f"{avg_quality:.1%}")
    
    st.markdown("---")
    
    # Nach Typ und Indizes gruppieren
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Nach Asset-Typ")
        type_counts = df.groupby('asset_type').size().to_dict()
        
        type_cols = st.columns(len(type_counts) if len(type_counts) <= 4 else 4)
        for i, (atype, count) in enumerate(type_counts.items()):
            with type_cols[i % len(type_cols)]:
                icon = {
                    'stock': '📈',
                    'index': '📊',
                    'commodity': '🥇',
                    'fx': '💱',
                    'bond': '📄'
                }.get(atype, '📌')
                st.metric(f"{icon} {atype.capitalize()}", count)
    
    with col2:
        st.subheader("🏛️ Nach Index/Gruppe")
        
        # Zähle Assets pro Gruppe (nur wenn Gruppe vorhanden)
        group_df = df[df['asset_group'].notna() & (df['asset_group'] != '-')]
        
        if not group_df.empty:
            group_counts = group_df.groupby('asset_group').size().sort_values(ascending=False).head(8)
            
            group_names = {
                'sp500': '📊 S&P 500',
                'nasdaq100': '📊 Nasdaq 100',
                'dax': '📊 DAX',
                'eurostoxx': '📊 EuroStoxx',
                'index': '📈 Indizes',
                'commodity': '🥇 Rohstoffe',
                'fx': '💱 Währungen',
                'bonds': '📄 Anleihen',
                'emerging_markets': '🌍 Emerging Markets'
            }
            
            for group, count in group_counts.items():
                label = group_names.get(group, group.upper())
                st.write(f"{label}: **{count}** Assets")
        else:
            st.info("💡 Tipp: Führen Sie 'Update_Asset_Names.command' aus, um Gruppen zuzuweisen!")
    
    st.markdown("---")
    
    # Assets-Tabelle
    st.subheader("📋 Assets")
    
    # Suchfunktion
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "🔍 Suche (Symbol, Name, Sektor):",
            key="search",
            placeholder="z.B. AAPL, Apple, Technology..."
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        clear_search = st.button("🗑️ Suche löschen", use_container_width=True)
        if clear_search:
            st.session_state.search = ""
            st.rerun()
    
    # Filter nach Suchbegriff
    if search_term:
        mask = (
            df['symbol'].str.contains(search_term, case=False, na=False) |
            df['name'].str.contains(search_term, case=False, na=False) |
            df['sector'].str.contains(search_term, case=False, na=False) |
            df['asset_type'].str.contains(search_term, case=False, na=False) |
            df['asset_group'].str.contains(search_term, case=False, na=False)
        )
        df = df[mask]
        
        if df.empty:
            st.warning(f"Keine Assets gefunden für: '{search_term}'")
            return
        else:
            st.info(f"📊 {len(df)} Assets gefunden für: '{search_term}'")
    
    # Spalten auswählen
    display_df = df[[
        'symbol', 'asset_type', 'asset_group', 'timeframe', 'name', 
        'sector', 'exchange',
        'first_date', 'last_date', 'days', 'data_points', 
        'ohlc_status', 'volume_status', 'data_quality_score', 'status'
    ]].copy()
    
    display_df.columns = [
        'Symbol', 'Typ', 'Gruppe', 'Zeitrahmen', 'Name', 
        'Sektor', 'Exchange',
        'Von', 'Bis', 'Tage', 'Punkte', 
        'OHLC', 'Volume', 'Qualität', 'Status'
    ]
    
    # Formatierung
    display_df['Tage'] = display_df['Tage'].apply(lambda x: f"{x:,}" if pd.notna(x) else "N/A")
    display_df['Punkte'] = display_df['Punkte'].apply(lambda x: f"{x:,}")
    display_df['Name'] = display_df['Name'].fillna('N/A')
    display_df['Sektor'] = display_df['Sektor'].fillna('-')
    display_df['Exchange'] = display_df['Exchange'].fillna('-')
    display_df['Gruppe'] = display_df['Gruppe'].fillna('-')
    display_df['Qualität'] = display_df['Qualität'].apply(lambda x: f"{x:.0%}" if pd.notna(x) else "N/A")
    
    # Zeige Tabelle
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config={
            "OHLC": st.column_config.TextColumn("OHLC", help="Open, High, Low, Close verfügbar?"),
            "Volume": st.column_config.TextColumn("Vol", help="Volume-Daten verfügbar?"),
            "Qualität": st.column_config.TextColumn("Q%", help="Datenqualität 0-100%")
        }
    )
    
    st.markdown("---")
    
    # Asset-Details & Aktionen
    st.subheader("🔍 Asset Details & Aktionen")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_symbol = st.selectbox(
            "Asset auswählen:",
            df['symbol'].tolist(),
            key="selected_symbol"
        )
    
    with col2:
        if st.button("🗑️ Asset deaktivieren", key="deactivate", use_container_width=True):
            success, message = deactivate_asset(selected_symbol)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    # Details anzeigen
    if selected_symbol:
        meta, stats, recent = get_asset_details(selected_symbol)
        
        if not meta.empty:
            st.markdown("### 📊 Metadaten")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Name:** {meta['name'].iloc[0] if pd.notna(meta['name'].iloc[0]) else 'N/A'}")
                st.write(f"**Typ:** {meta['asset_type'].iloc[0]}")
                st.write(f"**Exchange:** {meta['exchange'].iloc[0] if pd.notna(meta['exchange'].iloc[0]) else 'N/A'}")
            
            with col2:
                st.write(f"**Sektor:** {meta['sector'].iloc[0] if pd.notna(meta['sector'].iloc[0]) else 'N/A'}")
                st.write(f"**Währung:** {meta['currency'].iloc[0]}")
                st.write(f"**Status:** {'✅ Aktiv' if meta['is_active'].iloc[0] == 1 else '❌ Inaktiv'}")
            
            with col3:
                if not stats.empty and stats['count'].iloc[0] > 0:
                    st.write(f"**Datenpunkte:** {stats['count'].iloc[0]:,}")
                    st.write(f"**Von:** {stats['first_date'].iloc[0]}")
                    st.write(f"**Bis:** {stats['last_date'].iloc[0]}")
        
        if not stats.empty and stats['count'].iloc[0] > 0:
            st.markdown("### 📈 Daten-Statistik")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Min Preis", f"${stats['min_price'].iloc[0]:.2f}")
            
            with col2:
                st.metric("Max Preis", f"${stats['max_price'].iloc[0]:.2f}")
            
            with col3:
                st.metric("Ø Volumen", f"{stats['avg_volume'].iloc[0]:,.0f}")
            
            st.markdown("### 📅 Letzte 10 Einträge")
            recent_display = recent.copy()
            recent_display.columns = ['Datum', 'Open', 'High', 'Low', 'Close', 'Volume']
            recent_display[['Open', 'High', 'Low', 'Close']] = recent_display[['Open', 'High', 'Low', 'Close']].round(2)
            recent_display['Volume'] = recent_display['Volume'].apply(lambda x: f"{x:,}")
            
            st.dataframe(recent_display, use_container_width=True)
        else:
            st.warning("⚠️ Keine Kursdaten vorhanden!")


if __name__ == "__main__":
    main()
