
from __future__ import annotations

import json
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

DEFAULT_DB = Path(__file__).with_name("EuroJackpot_Operational_v3_5.sqlite")


class EuroJackpotV35App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("EuroJackpot Reliability Engine v3.5")
        self.geometry("1180x760")
        self.db_path = DEFAULT_DB
        self._build()
        self.refresh()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Open Database", command=self.open_db).pack(side="left", padx=6)
        self.status = ttk.Label(top, text="Ready")
        self.status.pack(side="right")

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.jackpot_tab = ttk.Frame(tabs)
        self.strategy_tab = ttk.Frame(tabs)
        self.registry_tab = ttk.Frame(tabs)
        self.audit_tab = ttk.Frame(tabs)
        tabs.add(self.jackpot_tab, text="Jackpot State")
        tabs.add(self.strategy_tab, text="Portfolio Mode")
        tabs.add(self.registry_tab, text="Prediction Registry")
        tabs.add(self.audit_tab, text="Audit")

        self.jackpot_text = tk.Text(self.jackpot_tab, wrap="word")
        self.jackpot_text.pack(fill="both", expand=True)

        self.strategy_tree = ttk.Treeview(
            self.strategy_tab,
            columns=("date","mode","jackpot","class2","anti","main","euro","portfolio"),
            show="headings",
        )
        for c, w in [("date",110),("mode",170),("jackpot",90),("class2",90),("anti",90),("main",90),("euro",90),("portfolio",380)]:
            self.strategy_tree.heading(c, text=c.title())
            self.strategy_tree.column(c, width=w)
        self.strategy_tree.pack(fill="both", expand=True)

        self.registry_tree = ttk.Treeview(
            self.registry_tab,
            columns=("target","main","euro","state","hash"),
            show="headings",
        )
        for c, w in [("target",120),("main",250),("euro",140),("state",420),("hash",150)]:
            self.registry_tree.heading(c, text=c.title())
            self.registry_tree.column(c, width=w)
        self.registry_tree.pack(fill="both", expand=True)

        self.audit_tree = ttk.Treeview(
            self.audit_tab,
            columns=("time","date","status","message"),
            show="headings",
        )
        for c, w in [("time",210),("date",120),("status",120),("message",600)]:
            self.audit_tree.heading(c, text=c.title())
            self.audit_tree.column(c, width=w)
        self.audit_tree.pack(fill="both", expand=True)

    def open_db(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("SQLite", "*.sqlite *.db"), ("All", "*.*")])
        if selected:
            self.db_path = Path(selected)
            self.refresh()

    def refresh(self) -> None:
        try:
            if not self.db_path.exists():
                self.status.config(text="Database not found")
                return
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                latest = conn.execute(
                    """
                    SELECT s.*, h.mode, h.recommended_portfolio, h.explanation,
                           h.main_probability, h.euro_probability
                    FROM jackpot_state s
                    JOIN jackpot_strategy_history h USING(draw_date)
                    ORDER BY s.draw_date DESC LIMIT 1
                    """
                ).fetchone()
                strategies = conn.execute(
                    "SELECT * FROM jackpot_strategy_history ORDER BY draw_date DESC"
                ).fetchall()
                predictions = conn.execute(
                    "SELECT * FROM predictions ORDER BY target_draw DESC"
                ).fetchall()
                audits = conn.execute(
                    "SELECT * FROM jackpot_state_audit ORDER BY audit_id DESC LIMIT 100"
                ).fetchall()

            self.jackpot_text.delete("1.0", "end")
            if latest:
                lines = [
                    f"Draw date: {latest['draw_date']}",
                    f"Jackpot: €{latest['jackpot_eur']:,.0f}",
                    f"Rollover count: {latest['rollover_count']}",
                    f"Mode: {latest['mode']}",
                    f"Verified: {latest['verification_status']}",
                    f"Overflow class: {latest['overflow_class']}",
                    f"Overflow: €{latest['overflow_eur']:,.0f}",
                    "",
                    f"Portfolio: {latest['recommended_portfolio']}",
                    latest['explanation'],
                    "",
                    f"Main inclusion probability: {latest['main_probability']:.4%}",
                    f"Euro inclusion probability: {latest['euro_probability']:.4%}",
                    "These probabilities do not change with jackpot state.",
                ]
            else:
                lines = ["No verified jackpot state has been imported yet."]
            self.jackpot_text.insert("1.0", "\n".join(lines))

            for tree in (self.strategy_tree, self.registry_tree, self.audit_tree):
                tree.delete(*tree.get_children())

            for r in strategies:
                self.strategy_tree.insert("", "end", values=(
                    r["draw_date"], r["mode"], f'{r["jackpot_weight"]:.0%}',
                    f'{r["class2_weight"]:.0%}', f'{r["anti_crowd_weight"]:.0%}',
                    f'{r["main_diversity_weight"]:.0%}', f'{r["euro_diversity_weight"]:.0%}',
                    r["recommended_portfolio"],
                ))
            for r in predictions:
                self.registry_tree.insert("", "end", values=(
                    r["target_draw"], r["primary_main"], r["primary_euro"],
                    r["confidence_state"], r["record_hash"][:14],
                ))
            for r in audits:
                self.audit_tree.insert("", "end", values=(
                    r["created_at_utc"], r["draw_date"], r["status"], r["message"],
                ))
            self.status.config(text=f"Loaded {self.db_path.name}")
        except Exception as exc:
            messagebox.showerror("Refresh failed", str(exc))
            self.status.config(text="Error")


if __name__ == "__main__":
    EuroJackpotV35App().mainloop()
