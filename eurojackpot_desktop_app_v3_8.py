
from __future__ import annotations

import argparse
import json
import os
import platform
import queue
import runpy
import shutil
import sqlite3
import subprocess
import sys
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from PIL import Image, ImageTk

from eurojackpot_jackpot_state_v3_5 import import_state, latest_state
from eurojackpot_one_click_v3_7 import build_parser as workflow_parser
from eurojackpot_one_click_v3_7 import execute as execute_workflow
from eurojackpot_operational_v3_4 import verify_wheel_csv
from eurojackpot_paths import ensure_user_layout, package_root, read_version, short_version


APP_NAME = "EuroJackpot Reliability Engine"
APP_VERSION = read_version()
APP_VERSION_SHORT = short_version(APP_VERSION)

ROOT = package_root()
BUNDLED_DB = ROOT / "EuroJackpot_Operational_v3_7.sqlite"
TEMPLATE = ROOT / "EuroJackpot_Ticket_Template_v3_6.png"
HISTORY = ROOT / "EuroJackpot_Canonical_History_v3.csv"
FULL_ENGINE = ROOT / "eurojackpot_reliability_engine_v3.py"

_USER = ensure_user_layout(BUNDLED_DB)
DATA_DIR = _USER["data"]
OUTPUT_DIR = _USER["outputs"]
DB_PATH = _USER["db"]
LOG_DIR = _USER["logs"]
ENGINE_OUT_DIR = _USER["engine"]


def initialize_user_data() -> None:
    ensure_user_layout(BUNDLED_DB)


def open_path(path: Path) -> None:
    path = path.resolve()
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class EuroJackpotDesktop(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        initialize_user_data()
        self.title(f"{APP_NAME} v{APP_VERSION_SHORT}")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.ticket_photo: ImageTk.PhotoImage | None = None
        self.active_thread: threading.Thread | None = None

        self._configure_style()
        self._build_ui()
        self.after(150, self._process_events)
        self.refresh_all()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        available = style.theme_names()
        if "clam" in available:
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("StatusGood.TLabel", foreground="#216e39")
        style.configure("StatusWarn.TLabel", foreground="#9a6700")
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("Treeview", rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(12, 10))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(side="left")
        self.status_label = ttk.Label(header, text="Ready", style="StatusGood.TLabel")
        self.status_label.pack(side="right")

        toolbar = ttk.Frame(self, padding=(12, 0, 12, 8))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Generate Prediction", style="Primary.TButton", command=self.run_quick).pack(side="left")
        ttk.Button(toolbar, text="Full Retraining", command=self.run_full).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_all).pack(side="left")
        ttk.Button(toolbar, text="Open Outputs", command=lambda: open_path(OUTPUT_DIR)).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Open Data Folder", command=lambda: open_path(DATA_DIR)).pack(side="left")

        self.progress = ttk.Progressbar(toolbar, mode="indeterminate", length=220)
        self.progress.pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.dashboard_tab = ttk.Frame(self.tabs)
        self.prediction_tab = ttk.Frame(self.tabs)
        self.jackpot_tab = ttk.Frame(self.tabs)
        self.models_tab = ttk.Frame(self.tabs)
        self.wheels_tab = ttk.Frame(self.tabs)
        self.history_tab = ttk.Frame(self.tabs)
        self.audit_tab = ttk.Frame(self.tabs)
        self.settings_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.dashboard_tab, text="Dashboard")
        self.tabs.add(self.prediction_tab, text="Prediction & Ticket")
        self.tabs.add(self.jackpot_tab, text="Jackpot State")
        self.tabs.add(self.models_tab, text="Models")
        self.tabs.add(self.wheels_tab, text="Coverage Wheels")
        self.tabs.add(self.history_tab, text="History")
        self.tabs.add(self.audit_tab, text="Audit & Runs")
        self.tabs.add(self.settings_tab, text="Settings")

        self._build_dashboard()
        self._build_prediction()
        self._build_jackpot()
        self._build_models()
        self._build_wheels()
        self._build_history()
        self._build_audit()
        self._build_settings()

    def _build_dashboard(self) -> None:
        top = ttk.Frame(self.dashboard_tab, padding=12)
        top.pack(fill="x")
        self.dashboard_summary = tk.Text(top, height=13, wrap="word", font=("Segoe UI", 11))
        self.dashboard_summary.pack(fill="x")

        buttons = ttk.LabelFrame(self.dashboard_tab, text="Main Actions", padding=12)
        buttons.pack(fill="x", padx=12, pady=6)
        ttk.Button(buttons, text="Generate Prediction (Quick)", style="Primary.TButton", command=self.run_quick).pack(side="left")
        ttk.Button(buttons, text="Run Full Engine", command=self.run_full).pack(side="left", padx=8)
        ttk.Button(buttons, text="Import Jackpot JSON", command=self.import_jackpot_json).pack(side="left")
        ttk.Button(buttons, text="View Latest Ticket", command=self.open_latest_ticket).pack(side="left", padx=8)

        log_frame = ttk.LabelFrame(self.dashboard_tab, text="Live Run Log", padding=8)
        log_frame.pack(fill="both", expand=True, padx=12, pady=8)
        self.live_log = tk.Text(log_frame, wrap="word", font=("Consolas", 9))
        self.live_log.pack(fill="both", expand=True)

    def _build_prediction(self) -> None:
        pane = ttk.Panedwindow(self.prediction_tab, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=2)
        pane.add(right, weight=3)

        ttk.Label(left, text="Latest Prediction", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        self.lines_tree = ttk.Treeview(left, columns=("role", "main", "euro", "score", "crowd"), show="headings")
        for col, label, width in [
            ("role", "Role", 90), ("main", "Main Numbers", 230), ("euro", "Euro", 100),
            ("score", "Portfolio Score", 120), ("crowd", "Anti-Crowd", 100),
        ]:
            self.lines_tree.heading(col, text=label)
            self.lines_tree.column(col, width=width, anchor="center")
        self.lines_tree.pack(fill="both", expand=True)

        action_row = ttk.Frame(left)
        action_row.pack(fill="x", pady=8)
        ttk.Button(action_row, text="Open Ticket", command=self.open_latest_ticket).pack(side="left")
        ttk.Button(action_row, text="Open JSON Report", command=self.open_latest_report).pack(side="left", padx=6)

        ttk.Label(right, text="Latest Rendered Ticket", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        self.ticket_canvas = tk.Canvas(right, bg="#e6e6e6", highlightthickness=0)
        self.ticket_canvas.pack(fill="both", expand=True)
        self.ticket_canvas.bind("<Configure>", lambda _event: self._render_ticket_preview())

    def _build_jackpot(self) -> None:
        top = ttk.Frame(self.jackpot_tab, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="Import ENGINE_STATE_JSON", style="Primary.TButton", command=self.import_jackpot_json).pack(side="left")
        ttk.Button(top, text="Refresh State", command=self.refresh_jackpot).pack(side="left", padx=6)
        ttk.Button(top, text="Export Template", command=self.export_jackpot_template).pack(side="left")

        self.jackpot_text = tk.Text(self.jackpot_tab, wrap="word", font=("Segoe UI", 11))
        self.jackpot_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_models(self) -> None:
        self.models_tree = ttk.Treeview(
            self.models_tab,
            columns=("model", "version", "role", "status", "brier", "logloss", "gate", "description"),
            show="headings",
        )
        specs = [
            ("model", "Model", 150), ("version", "Version", 80), ("role", "Role", 110),
            ("status", "Status", 110), ("brier", "Brier", 90), ("logloss", "Log Loss", 90),
            ("gate", "Gate", 90), ("description", "Description", 430),
        ]
        for col, label, width in specs:
            self.models_tree.heading(col, text=label)
            self.models_tree.column(col, width=width)
        self.models_tree.pack(fill="both", expand=True, padx=12, pady=12)

    def _build_wheels(self) -> None:
        top = ttk.Frame(self.wheels_tab, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="Verify All Wheels", style="Primary.TButton", command=self.refresh_wheels).pack(side="left")
        ttk.Button(top, text="Open Project Folder", command=lambda: open_path(ROOT)).pack(side="left", padx=6)

        self.wheels_tree = ttk.Treeview(
            self.wheels_tab,
            columns=("wheel", "rows", "unique", "required", "covered", "missing", "status"),
            show="headings",
        )
        for col, label, width in [
            ("wheel", "Wheel", 170), ("rows", "Rows", 90), ("unique", "Unique", 90),
            ("required", "Required Subsets", 130), ("covered", "Covered", 100),
            ("missing", "Missing", 90), ("status", "Status", 100),
        ]:
            self.wheels_tree.heading(col, text=label)
            self.wheels_tree.column(col, width=width, anchor="center")
        self.wheels_tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_history(self) -> None:
        self.history_text = tk.Text(self.history_tab, wrap="word", font=("Segoe UI", 11))
        self.history_text.pack(fill="both", expand=True, padx=12, pady=12)

    def _build_audit(self) -> None:
        self.audit_tree = ttk.Treeview(
            self.audit_tab,
            columns=("time", "run", "target", "mode", "status", "ticket"),
            show="headings",
        )
        for col, label, width in [
            ("time", "Created UTC", 190), ("run", "Run ID", 210), ("target", "Target", 110),
            ("mode", "Mode", 100), ("status", "Status", 130), ("ticket", "Ticket Image", 480),
        ]:
            self.audit_tree.heading(col, text=label)
            self.audit_tree.column(col, width=width)
        self.audit_tree.pack(fill="both", expand=True, padx=12, pady=12)
        self.audit_tree.bind("<Double-1>", self._open_selected_audit_ticket)

    def _build_settings(self) -> None:
        frame = ttk.Frame(self.settings_tab, padding=16)
        frame.pack(fill="both", expand=True)
        values = [
            ("Application version", APP_VERSION),
            ("Operating system", f"{platform.system()} {platform.release()}"),
            ("Python", sys.version.split()[0]),
            ("Installation/resources", str(ROOT)),
            ("User data", str(DATA_DIR)),
            ("Database", str(DB_PATH)),
            ("Outputs", str(OUTPUT_DIR)),
            ("Canonical history", str(HISTORY)),
        ]
        for r, (label, value) in enumerate(values):
            ttk.Label(frame, text=label, style="Heading.TLabel").grid(row=r, column=0, sticky="nw", padx=(0, 15), pady=5)
            ttk.Label(frame, text=value, wraplength=850).grid(row=r, column=1, sticky="nw", pady=5)

        ttk.Separator(frame).grid(row=len(values), column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Button(frame, text="Open User Data", command=lambda: open_path(DATA_DIR)).grid(row=len(values)+1, column=0, sticky="w")
        ttk.Button(frame, text="Open Installation Folder", command=lambda: open_path(ROOT)).grid(row=len(values)+1, column=1, sticky="w")

    def _set_busy(self, busy: bool, text: str = "Ready") -> None:
        self.status_label.config(text=text)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _append_log(self, text: str) -> None:
        self.live_log.insert("end", text.rstrip() + "\n")
        self.live_log.see("end")

    def _process_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self._append_log(str(payload))
                elif kind == "done":
                    self._set_busy(False, "Run completed")
                    self.refresh_all()
                    result = payload if isinstance(payload, dict) else {}
                    ticket = result.get("ticket_image")
                    if ticket:
                        messagebox.showinfo("Prediction completed", f"Ticket generated:\n{ticket}")
                elif kind == "error":
                    self._set_busy(False, "Run failed")
                    self._append_log(str(payload))
                    messagebox.showerror("Run failed", str(payload))
        except queue.Empty:
            pass
        self.after(150, self._process_events)

    def _start_thread(self, target, status: str) -> None:
        if self.active_thread and self.active_thread.is_alive():
            messagebox.showwarning("Engine busy", "A prediction run is already in progress.")
            return
        self._set_busy(True, status)
        self.active_thread = threading.Thread(target=target, daemon=True)
        self.active_thread.start()

    def run_quick(self) -> None:
        self._start_thread(lambda: self._run_workflow("audited"), "Generating prediction…")

    def run_full(self) -> None:
        if not messagebox.askyesno(
            "Full retraining",
            "This runs the complete research engine and can take substantially longer. Continue?",
        ):
            return
        self._start_thread(self._run_full_workflow, "Running full engine…")

    def _workflow_args(self, mode: str, results: Path | None = None):
        parser = workflow_parser()
        argv = [
            "--engine-mode", mode,
            "--db", str(DB_PATH),
            "--output-dir", str(OUTPUT_DIR),
            "--engine-out", str(ENGINE_OUT_DIR),
        ]
        if results is not None:
            argv += ["--results", str(results)]
        return parser.parse_args(argv)

    def _run_workflow(self, mode: str, results: Path | None = None) -> None:
        try:
            self.events.put(("log", f"[{datetime.now().isoformat(timespec='seconds')}] Starting {mode} workflow"))
            result = execute_workflow(self._workflow_args(mode, results))
            self.events.put(("log", json.dumps({
                "run_id": result["run_id"],
                "target_draw": result["target_draw"],
                "primary": result["primary"],
                "ticket": result["ticket_image"],
            }, indent=2)))
            self.events.put(("done", result))
        except Exception:
            self.events.put(("error", traceback.format_exc()))

    def _run_full_workflow(self) -> None:
        try:
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            log_path = LOG_DIR / f"full_engine_{timestamp}.log"
            self.events.put(("log", f"Full-engine log: {log_path}"))
            ENGINE_OUT_DIR.mkdir(parents=True, exist_ok=True)
            os.environ["EUROJACKPOT_OUTPUT_DIR"] = str(ENGINE_OUT_DIR)
            with log_path.open("w", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
                runpy.run_path(str(FULL_ENGINE), run_name="__main__")
            generated = ENGINE_OUT_DIR / "EuroJackpot_Model_Results_v3.json"
            if not generated.exists():
                raise RuntimeError("Full engine did not create EuroJackpot_Model_Results_v3.json")
            self.events.put(("log", f"Full engine completed. Results: {generated}"))
            self.events.put(("log", "Running validation, freeze and rendering."))
            self._run_workflow("audited", generated)
        except Exception:
            self.events.put(("error", traceback.format_exc()))

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_prediction()
        self.refresh_jackpot()
        self.refresh_models()
        self.refresh_wheels()
        self.refresh_history()
        self.refresh_audit()

    def refresh_dashboard(self) -> None:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            draws = conn.execute("SELECT COUNT(*) FROM draws").fetchone()[0] if self._table_exists(conn, "draws") else 0
            models = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0] if self._table_exists(conn, "models") else 0
            runs = conn.execute("SELECT COUNT(*) FROM workflow_runs_v3_7").fetchone()[0] if self._table_exists(conn, "workflow_runs_v3_7") else 0
            artifacts = conn.execute("SELECT COUNT(*) FROM ticket_artifacts").fetchone()[0] if self._table_exists(conn, "ticket_artifacts") else 0
            last_run = conn.execute(
                "SELECT * FROM workflow_runs_v3_7 ORDER BY created_at_utc DESC LIMIT 1"
            ).fetchone() if self._table_exists(conn, "workflow_runs_v3_7") else None

        lines = [
            f"{APP_NAME} v{APP_VERSION}",
            "",
            f"Database integrity: {integrity}",
            f"Canonical draws in database: {draws}",
            f"Registered models: {models}",
            f"Workflow runs: {runs}",
            f"Ticket artifacts: {artifacts}",
            "",
        ]
        if last_run:
            lines += [
                f"Latest run: {last_run['run_id']}",
                f"Target draw: {last_run['target_draw']}",
                f"Engine mode: {last_run['engine_mode']}",
                f"Decision: {last_run['overall_status']}",
                f"Jackpot mode: {last_run['jackpot_mode']}",
                f"Ticket: {last_run['output_image']}",
            ]
        else:
            lines.append("No v3.7 workflow run recorded yet.")

        self.dashboard_summary.delete("1.0", "end")
        self.dashboard_summary.insert("1.0", "\n".join(lines))

    def refresh_prediction(self) -> None:
        self.lines_tree.delete(*self.lines_tree.get_children())
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not self._table_exists(conn, "workflow_runs_v3_7"):
                return
            run = conn.execute("SELECT * FROM workflow_runs_v3_7 ORDER BY created_at_utc DESC LIMIT 1").fetchone()
            if not run:
                return
            lines = conn.execute(
                "SELECT * FROM workflow_lines_v3_7 WHERE run_id=? ORDER BY line_no",
                (run["run_id"],),
            ).fetchall()
        for row in lines:
            self.lines_tree.insert("", "end", values=(
                row["role"],
                " – ".join(str(x) for x in json.loads(row["main_json"])),
                " – ".join(str(x) for x in json.loads(row["euro_json"])),
                "" if row["portfolio_score"] is None else f"{row['portfolio_score']:.5f}",
                "" if row["anti_crowd_score"] is None else f"{row['anti_crowd_score']:.3f}",
            ))
        self._render_ticket_preview()

    def _latest_ticket_path(self) -> Path | None:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not self._table_exists(conn, "workflow_runs_v3_7"):
                return None
            row = conn.execute(
                "SELECT output_image FROM workflow_runs_v3_7 WHERE output_image IS NOT NULL ORDER BY created_at_utc DESC LIMIT 1"
            ).fetchone()
        if row and row["output_image"]:
            path = Path(row["output_image"])
            if path.exists():
                return path
            alternate = OUTPUT_DIR / path.name
            if alternate.exists():
                return alternate
        return None

    def _latest_report_path(self) -> Path | None:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not self._table_exists(conn, "workflow_runs_v3_7"):
                return None
            row = conn.execute(
                "SELECT output_summary FROM workflow_runs_v3_7 WHERE output_summary IS NOT NULL ORDER BY created_at_utc DESC LIMIT 1"
            ).fetchone()
        if row and row["output_summary"]:
            path = Path(row["output_summary"])
            if path.exists():
                return path
            alternate = OUTPUT_DIR / path.name
            if alternate.exists():
                return alternate
        return None

    def _render_ticket_preview(self) -> None:
        path = self._latest_ticket_path()
        self.ticket_canvas.delete("all")
        if not path:
            self.ticket_canvas.create_text(
                max(self.ticket_canvas.winfo_width() // 2, 200),
                max(self.ticket_canvas.winfo_height() // 2, 150),
                text="Generate a prediction to create the ticket image.",
                fill="#555555",
                font=("Segoe UI", 13),
            )
            return
        try:
            image = Image.open(path)
            max_w = max(self.ticket_canvas.winfo_width() - 10, 300)
            max_h = max(self.ticket_canvas.winfo_height() - 10, 250)
            image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            self.ticket_photo = ImageTk.PhotoImage(image)
            self.ticket_canvas.create_image(
                self.ticket_canvas.winfo_width() // 2,
                self.ticket_canvas.winfo_height() // 2,
                image=self.ticket_photo,
                anchor="center",
            )
        except Exception as exc:
            self.ticket_canvas.create_text(20, 20, anchor="nw", text=str(exc), fill="red")

    def open_latest_ticket(self) -> None:
        path = self._latest_ticket_path()
        if path:
            open_path(path)
        else:
            messagebox.showinfo("No ticket", "No rendered ticket is available yet.")

    def open_latest_report(self) -> None:
        path = self._latest_report_path()
        if path:
            open_path(path)
        else:
            messagebox.showinfo("No report", "No run report is available yet.")

    def import_jackpot_json(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not selected:
            return
        try:
            payload = json.loads(Path(selected).read_text(encoding="utf-8"))
            if "ENGINE_STATE_JSON" in payload:
                payload = payload["ENGINE_STATE_JSON"]
            result = import_state(DB_PATH, payload)
            if result.get("accepted"):
                messagebox.showinfo("Jackpot state imported", f"Mode: {result['profile']['mode']}")
            else:
                messagebox.showerror("Import rejected", "\n".join(result.get("errors", [])))
            self.refresh_jackpot()
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))

    def export_jackpot_template(self) -> None:
        source = ROOT / "EuroJackpot_ENGINE_STATE_TEMPLATE_v3_5.json"
        if not source.exists():
            messagebox.showerror("Missing template", str(source))
            return
        target = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="EuroJackpot_ENGINE_STATE_TEMPLATE.json",
            filetypes=[("JSON files", "*.json")],
        )
        if target:
            shutil.copy2(source, target)

    def refresh_jackpot(self) -> None:
        state = latest_state(DB_PATH)
        self.jackpot_text.delete("1.0", "end")
        if not state:
            self.jackpot_text.insert(
                "1.0",
                "No verified jackpot-state record has been imported.\n\n"
                "The prediction workflow will display Jackpot: TBA.\n"
                "Jackpot information affects payout and portfolio context only; it never alters number probabilities.",
            )
            return
        lines = [
            f"Draw date: {state['draw_date']}",
            f"Jackpot: €{state['jackpot_eur']:,.0f}",
            f"Rollover count: {state['rollover_count']}",
            f"Mode: {state['mode']}",
            f"Cap reached: {bool(state['cap_reached'])}",
            f"Overflow class: {state['overflow_class']}",
            f"Overflow amount: €{state['overflow_eur']:,.0f}",
            f"Verification: {state['verification_status']} ({state['source_count']} sources)",
            "",
            f"Recommended portfolio: {state['recommended_portfolio']}",
            state["explanation"],
            "",
            f"Main-number inclusion probability: {state['main_probability']:.4%}",
            f"Euro-number inclusion probability: {state['euro_probability']:.4%}",
            "Probabilities remain unchanged.",
        ]
        self.jackpot_text.insert("1.0", "\n".join(lines))

    def refresh_models(self) -> None:
        self.models_tree.delete(*self.models_tree.get_children())
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not self._table_exists(conn, "models"):
                return
            rows = conn.execute("SELECT * FROM models ORDER BY role, model_id").fetchall()
        for row in rows:
            self.models_tree.insert("", "end", values=(
                row["model_id"], row["version"], row["role"], row["status"],
                "" if row["brier"] is None else f"{row['brier']:.6f}",
                "" if row["log_loss"] is None else f"{row['log_loss']:.6f}",
                row["gate_status"], row["description"],
            ))

    def refresh_wheels(self) -> None:
        self.wheels_tree.delete(*self.wheels_tree.get_children())
        pool = [4, 21, 25, 27, 28, 35, 36, 37, 42, 44, 48, 50]
        specs = [
            ("54 Pair Compact", "EuroJackpot_Wheel_54_Pair_Compact.csv", 54, 2),
            ("135 Pair Extended", "EuroJackpot_Wheel_135_Pair_Extended.csv", 135, 2),
            ("198 Triple Compact", "EuroJackpot_Wheel_198_Triple_Compact.csv", 198, 3),
            ("495 Triple Extended", "EuroJackpot_Wheel_495_Triple_Extended.csv", 495, 3),
        ]
        for label, filename, expected, subset in specs:
            try:
                result = verify_wheel_csv(ROOT / filename, expected, subset, pool)
                self.wheels_tree.insert("", "end", values=(
                    label, result["rows"], result["unique_lines"], result["required_subsets"],
                    result["covered_subsets"], result["missing_subsets"], "PASS" if result["passed"] else "FAIL",
                ))
            except Exception as exc:
                self.wheels_tree.insert("", "end", values=(label, "", "", "", "", "", f"ERROR: {exc}"))

    def refresh_history(self) -> None:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not self._table_exists(conn, "draws"):
                return
            count = conn.execute("SELECT COUNT(*) FROM draws").fetchone()[0]
            first = conn.execute("SELECT * FROM draws ORDER BY draw_date LIMIT 1").fetchone()
            last = conn.execute("SELECT * FROM draws ORDER BY draw_date DESC LIMIT 1").fetchone()
            eras = conn.execute(
                "SELECT euro_pool, COUNT(*) AS n, MIN(draw_date), MAX(draw_date) FROM draws GROUP BY euro_pool ORDER BY euro_pool"
            ).fetchall()

        text = [
            f"Canonical draws: {count}",
            f"First draw: {first['draw_date']}",
            f"Latest draw: {last['draw_date']}",
            "",
            "Latest result:",
            f"Main: {last['main_1']}, {last['main_2']}, {last['main_3']}, {last['main_4']}, {last['main_5']}",
            f"Euro: {last['euro_1']}, {last['euro_2']}",
            "",
            "Euro-number pool eras:",
        ]
        for row in eras:
            text.append(f"2/{row[0]}: {row[1]} draws, {row[2]} through {row[3]}")
        self.history_text.delete("1.0", "end")
        self.history_text.insert("1.0", "\n".join(text))

    def refresh_audit(self) -> None:
        self.audit_tree.delete(*self.audit_tree.get_children())
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not self._table_exists(conn, "workflow_runs_v3_7"):
                return
            rows = conn.execute(
                "SELECT * FROM workflow_runs_v3_7 ORDER BY created_at_utc DESC LIMIT 200"
            ).fetchall()
        for row in rows:
            self.audit_tree.insert("", "end", values=(
                row["created_at_utc"], row["run_id"], row["target_draw"],
                row["engine_mode"], row["overall_status"], row["output_image"],
            ))

    def _open_selected_audit_ticket(self, _event=None) -> None:
        selected = self.audit_tree.selection()
        if not selected:
            return
        values = self.audit_tree.item(selected[0], "values")
        if len(values) >= 6 and values[5]:
            path = Path(values[5])
            if not path.exists():
                path = OUTPUT_DIR / path.name
            if path.exists():
                open_path(path)

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone() is not None


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    args, _unknown = parser.parse_known_args()

    app = EuroJackpotDesktop()
    if args.quick:
        app.after(500, app.run_quick)
    elif args.full:
        app.after(500, app.run_full)
    app.mainloop()


if __name__ == "__main__":
    main()
