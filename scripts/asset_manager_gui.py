#!/usr/bin/env python3
"""
Asset Manager - GUI Version
Grafische Oberfläche zur Verwaltung der MarketData Assets

Autor: Trading System v2
Datum: 2026-01-08
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from pathlib import Path
from datetime import datetime

# Pfade
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "market_data.db"


class AssetManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 MarketData Asset Manager")
        self.root.geometry("1200x700")
        
        # Farben
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007acc"
        
        self.setup_ui()
        self.load_assets()
    
    def setup_ui(self):
        """Erstellt die UI-Elemente."""
        
        # Hauptframe
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titel
        title = tk.Label(
            main_frame,
            text="📊 MarketData Asset Manager",
            font=("Arial", 20, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        title.pack(pady=10)
        
        # Buttons-Frame
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(
            button_frame,
            text="🔄 Aktualisieren",
            command=self.load_assets,
            font=("Arial", 12),
            bg=self.accent_color,
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="➕ Asset hinzufügen",
            command=self.add_asset_dialog,
            font=("Arial", 12),
            bg="#28a745",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="🗑️ Asset deaktivieren",
            command=self.remove_asset,
            font=("Arial", 12),
            bg="#dc3545",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="📄 Details anzeigen",
            command=self.show_details,
            font=("Arial", 12),
            bg="#17a2b8",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        # Filter
        filter_frame = tk.Frame(main_frame, bg=self.bg_color)
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            filter_frame,
            text="Filter:",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(side=tk.LEFT, padx=5)
        
        self.filter_var = tk.StringVar(value="all")
        tk.Radiobutton(
            filter_frame,
            text="Alle",
            variable=self.filter_var,
            value="all",
            command=self.load_assets,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.accent_color
        ).pack(side=tk.LEFT)
        
        tk.Radiobutton(
            filter_frame,
            text="Nur Aktive",
            variable=self.filter_var,
            value="active",
            command=self.load_assets,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.accent_color
        ).pack(side=tk.LEFT)
        
        tk.Radiobutton(
            filter_frame,
            text="Nur Inaktive",
            variable=self.filter_var,
            value="inactive",
            command=self.load_assets,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.accent_color
        ).pack(side=tk.LEFT)
        
        # Treeview (Tabelle)
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Symbol", "Typ", "Name", "Von", "Bis", "Tage", "Punkte", "Status"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Spalten definieren
        columns = [
            ("Symbol", 100),
            ("Typ", 80),
            ("Name", 200),
            ("Von", 100),
            ("Bis", 100),
            ("Tage", 80),
            ("Punkte", 100),
            ("Status", 80)
        ]
        
        for col, width in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=width)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Statistik-Label
        self.stats_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.fg_color,
            justify=tk.LEFT
        )
        self.stats_label.pack(pady=10)
    
    def get_connection(self):
        """DB-Verbindung."""
        return sqlite3.connect(DB_PATH)
    
    def load_assets(self):
        """Lädt Assets aus DB."""
        
        # Clear Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Filter
        filter_val = self.filter_var.get()
        if filter_val == "active":
            where_clause = "WHERE is_active = 1"
        elif filter_val == "inactive":
            where_clause = "WHERE is_active = 0"
        else:
            where_clause = ""
        
        query = f"""
            SELECT 
                a.symbol,
                a.asset_type,
                a.name,
                a.first_date,
                a.last_date,
                a.is_active,
                COUNT(p.date) as data_points
            FROM asset_metadata a
            LEFT JOIN price_data p ON a.symbol = p.symbol
            {where_clause}
            GROUP BY a.symbol
            ORDER BY a.asset_type, a.symbol
        """
        
        results = cursor.execute(query).fetchall()
        
        # Fülle Treeview
        for row in results:
            symbol, atype, name, first_date, last_date, is_active, data_points = row
            
            # Berechne Tage
            if first_date and last_date:
                days = (datetime.strptime(last_date, '%Y-%m-%d') - 
                       datetime.strptime(first_date, '%Y-%m-%d')).days
            else:
                days = 0
            
            status = "✅ Aktiv" if is_active else "❌ Inaktiv"
            name_short = (name[:25] + "...") if name and len(name) > 28 else (name or "N/A")
            
            self.tree.insert("", tk.END, values=(
                symbol,
                atype,
                name_short,
                first_date or "N/A",
                last_date or "N/A",
                f"{days:,}",
                f"{data_points:,}",
                status
            ))
        
        # Statistik
        active_count = sum(1 for r in results if r[5] == 1)
        inactive_count = len(results) - active_count
        
        # Nach Typ
        types = {}
        for r in results:
            types[r[1]] = types.get(r[1], 0) + 1
        
        type_str = " | ".join([f"{t}: {c}" for t, c in sorted(types.items())])
        
        stats_text = (f"Gesamt: {len(results)} Assets | "
                     f"Aktiv: {active_count} | Inaktiv: {inactive_count}\n"
                     f"{type_str}")
        
        self.stats_label.config(text=stats_text)
        
        conn.close()
    
    def add_asset_dialog(self):
        """Dialog zum Hinzufügen eines Assets."""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Asset hinzufügen")
        dialog.geometry("400x300")
        dialog.configure(bg=self.bg_color)
        
        # Symbol
        tk.Label(dialog, text="Symbol (z.B. AAPL):", bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        symbol_entry = tk.Entry(dialog, font=("Arial", 12))
        symbol_entry.pack(pady=5)
        
        # Typ
        tk.Label(dialog, text="Typ:", bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        type_var = tk.StringVar(value="stock")
        type_combo = ttk.Combobox(dialog, textvariable=type_var, 
                                   values=["stock", "index", "commodity", "fx"])
        type_combo.pack(pady=5)
        
        # Name
        tk.Label(dialog, text="Name (optional):", bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        name_entry = tk.Entry(dialog, font=("Arial", 12))
        name_entry.pack(pady=5)
        
        def submit():
            symbol = symbol_entry.get().strip().upper()
            if not symbol:
                messagebox.showerror("Fehler", "Symbol darf nicht leer sein!")
                return
            
            asset_type = type_var.get()
            name = name_entry.get().strip() or None
            
            # Füge hinzu
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO asset_metadata 
                    (symbol, asset_type, name, is_active)
                    VALUES (?, ?, ?, 1)
                """, (symbol, asset_type, name))
                
                conn.commit()
                messagebox.showinfo("Erfolg", f"Asset {symbol} hinzugefügt!")
                dialog.destroy()
                self.load_assets()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Fehler", f"Asset {symbol} existiert bereits!")
            
            finally:
                conn.close()
        
        tk.Button(dialog, text="Hinzufügen", command=submit, 
                 bg="#28a745", fg="white", font=("Arial", 12), padx=20, pady=5).pack(pady=20)
    
    def remove_asset(self):
        """Deaktiviert ausgewähltes Asset."""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Asset aus!")
            return
        
        item = self.tree.item(selection[0])
        symbol = item['values'][0]
        
        confirm = messagebox.askyesno(
            "Bestätigung",
            f"Asset {symbol} deaktivieren?\n\n(Daten bleiben erhalten)"
        )
        
        if not confirm:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE asset_metadata 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (symbol,))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Erfolg", f"Asset {symbol} deaktiviert!")
        self.load_assets()
    
    def show_details(self):
        """Zeigt Details zum ausgewählten Asset."""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Asset aus!")
            return
        
        item = self.tree.item(selection[0])
        symbol = item['values'][0]
        
        # Details-Fenster
        details_window = tk.Toplevel(self.root)
        details_window.title(f"📊 Details: {symbol}")
        details_window.geometry("600x500")
        details_window.configure(bg=self.bg_color)
        
        # Hole Daten
        conn = self.get_connection()
        cursor = conn.cursor()
        
        meta = cursor.execute("""
            SELECT * FROM asset_metadata WHERE symbol = ?
        """, (symbol,)).fetchone()
        
        stats = cursor.execute("""
            SELECT 
                COUNT(*) as count,
                MIN(date) as first_date,
                MAX(date) as last_date,
                MIN(low) as min_price,
                MAX(high) as max_price,
                AVG(volume) as avg_volume
            FROM price_data
            WHERE symbol = ?
        """, (symbol,)).fetchone()
        
        # Text-Widget
        text = tk.Text(details_window, font=("Courier", 11), bg="#2d2d2d", fg="white", padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Formatiere Details
        details = f"""
{'='*60}
ASSET DETAILS: {symbol}
{'='*60}

Name:         {meta[1] or 'N/A'}
Typ:          {meta[2]}
Exchange:     {meta[3] or 'N/A'}
Sektor:       {meta[4] or 'N/A'}
Industrie:    {meta[5] or 'N/A'}
Währung:      {meta[6]}
Status:       {'✅ Aktiv' if meta[9] else '❌ Inaktiv'}

"""
        
        if stats and stats[0] > 0:
            first = datetime.strptime(stats[1], '%Y-%m-%d')
            last = datetime.strptime(stats[2], '%Y-%m-%d')
            total_days = (last - first).days
            
            details += f"""
{'='*60}
DATEN
{'='*60}

Datenpunkte:  {stats[0]:,}
Zeitraum:     {stats[1]} bis {stats[2]}
Zeitspanne:   {total_days:,} Tage ({total_days/365:.1f} Jahre)
Preisspanne:  ${stats[3]:.2f} - ${stats[4]:.2f}
Ø Volumen:    {stats[5]:,.0f}
"""
        else:
            details += "\n⚠️  Keine Kursdaten vorhanden!\n"
        
        text.insert("1.0", details)
        text.config(state=tk.DISABLED)
        
        conn.close()
    
    def sort_by(self, col):
        """Sortiert Tabelle nach Spalte."""
        # Vereinfachte Sortierung
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        items.sort()
        
        for index, (val, k) in enumerate(items):
            self.tree.move(k, '', index)


def main():
    root = tk.Tk()
    app = AssetManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
