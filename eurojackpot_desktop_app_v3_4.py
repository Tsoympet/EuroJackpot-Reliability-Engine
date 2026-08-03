
from __future__ import annotations

import json
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

DEFAULT_DB = Path(__file__).with_name("EuroJackpot_Operational_v3_4.sqlite")
DEFAULT_SELFTEST = Path(__file__).with_name("EuroJackpot_Operational_SelfTest_v3_4.json")


class EuroJackpotApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("EuroJackpot Reliability Engine v3.4")
        self.geometry("1120x720")
        self.db_path = DEFAULT_DB
        self.selftest_path = DEFAULT_SELFTEST
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=8)
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(toolbar, text="Open Database", command=self.open_database).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Open Self-Test", command=self.open_selftest).pack(side="left")
        self.status = ttk.Label(toolbar, text="Ready")
        self.status.pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.dashboard = ttk.Frame(notebook)
        self.models = ttk.Frame(notebook)
        self.registry = ttk.Frame(notebook)
        self.audit = ttk.Frame(notebook)
        notebook.add(self.dashboard, text="Dashboard")
        notebook.add(self.models, text="Champion / Challengers")
        notebook.add(self.registry, text="Prediction Registry")
        notebook.add(self.audit, text="Audit")

        self.dashboard_text = tk.Text(self.dashboard, wrap="word")
        self.dashboard_text.pack(fill="both", expand=True)

        self.model_tree = ttk.Treeview(self.models, columns=("version","role","status","gates"), show="headings")
        for c, label in [("version","Version"),("role","Role"),("status","Status"),("gates","Gate Status")]:
            self.model_tree.heading(c, text=label)
            self.model_tree.column(c, width=170)
        self.model_tree.pack(fill="both", expand=True)

        self.registry_tree = ttk.Treeview(
            self.registry,
            columns=("target","cutoff","champion","research","main","euro","state","hash"),
            show="headings",
        )
        for c in self.registry_tree["columns"]:
            self.registry_tree.heading(c, text=c.title())
            self.registry_tree.column(c, width=125)
        self.registry_tree.pack(fill="both", expand=True)

        self.audit_tree = ttk.Treeview(self.audit, columns=("time","category","status","message"), show="headings")
        for c, width in [("time",190),("category",150),("status",100),("message",600)]:
            self.audit_tree.heading(c, text=c.title())
            self.audit_tree.column(c, width=width)
        self.audit_tree.pack(fill="both", expand=True)

    def open_database(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("SQLite databases","*.sqlite *.db"),("All files","*.*")])
        if selected:
            self.db_path = Path(selected)
            self.refresh()

    def open_selftest(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("JSON files","*.json"),("All files","*.*")])
        if selected:
            self.selftest_path = Path(selected)
            self.refresh()

    def refresh(self) -> None:
        try:
            self._refresh_dashboard()
            self._refresh_database_tabs()
            self.status.config(text=f"Loaded {self.db_path.name}")
        except Exception as exc:
            messagebox.showerror("Refresh failed", str(exc))
            self.status.config(text="Error")

    def _refresh_dashboard(self) -> None:
        data = json.loads(self.selftest_path.read_text(encoding="utf-8"))
        cc = data["champion_challenger"]
        independent = data["independent_verification"]
        leakage = data["leakage_tests"]
        neg = data["negative_controls"]
        summary = [
            "EuroJackpot Reliability Engine v3.4",
            "",
            f"Champion: {cc['champion']['model_id']} {cc['champion']['version']}",
            f"Promotion decision: {cc['promotion_test']['decision']}",
            f"Prospective scored draws: {data['prospective_summary']['scored_draws']}",
            f"Independent verification: {'PASS' if independent['all_passed'] else 'FAIL'}",
            f"Leakage challenge suite: {'PASS' if leakage['passed'] else 'FAIL'}",
            f"Negative controls: {'PASS' if neg['passed'] else 'FAIL'}",
            "",
            "Deployment remains Uniform mode until every promotion gate passes.",
            "",
            f"Next draw operating time: {data['next_draw_schedule']['pre_draw_local_time']}",
            data['next_draw_schedule']['post_draw_action'],
        ]
        self.dashboard_text.delete("1.0", "end")
        self.dashboard_text.insert("1.0", "\n".join(summary))

    def _refresh_database_tabs(self) -> None:
        if not self.db_path.exists():
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            models = conn.execute("SELECT * FROM models ORDER BY role, model_id").fetchall()
            predictions = conn.execute("SELECT * FROM predictions ORDER BY target_draw DESC").fetchall()
            audits = conn.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 100").fetchall()

        for tree in (self.model_tree, self.registry_tree, self.audit_tree):
            tree.delete(*tree.get_children())

        for r in models:
            self.model_tree.insert("", "end", values=(r["version"], r["role"], r["status"], r["gate_status"]))

        for r in predictions:
            self.registry_tree.insert("", "end", values=(
                r["target_draw"], r["data_cutoff"], r["champion_model"], r["research_model"],
                r["primary_main"], r["primary_euro"], r["confidence_state"], r["record_hash"][:12],
            ))

        for r in audits:
            self.audit_tree.insert("", "end", values=(r["created_at_utc"], r["category"], r["status"], r["message"]))


if __name__ == "__main__":
    EuroJackpotApp().mainloop()
