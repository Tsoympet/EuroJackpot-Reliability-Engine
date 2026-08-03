
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
from eurojackpot_edge_engine_v3_8 import run_edge_search
from eurojackpot_learning_engine_v3_8 import learning_status, score_draw_result, train_on_history
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
        self._telemetry_cache = ""

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
        style.configure("MetricValue.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("MetricCaption.TLabel", font=("Segoe UI", 9), foreground="#444444")
        style.configure("StatusGood.TLabel", foreground="#216e39")
        style.configure("StatusWarn.TLabel", foreground="#9a6700")
        style.configure("StatusBad.TLabel", foreground="#a40e26")
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("Action.TButton", padding=(10, 6))
        style.configure("Treeview", rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Footer.TLabel", font=("Segoe UI", 9), foreground="#333333")

    def _build_ui(self) -> None:
        self._build_menu()

        header = ttk.Frame(self, padding=(12, 10))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(side="left")
        self.header_subtitle = ttk.Label(
            header,
            text=f"v{APP_VERSION}  ·  Deployed champion: exact-uniform",
            style="MetricCaption.TLabel",
        )
        self.header_subtitle.pack(side="left", padx=(12, 0))
        self.status_label = ttk.Label(header, text="Ready", style="StatusGood.TLabel")
        self.status_label.pack(side="right")

        toolbar = ttk.Frame(self, padding=(12, 0, 12, 8))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Generate Prediction", style="Primary.TButton", command=self.run_quick).pack(side="left")
        ttk.Button(toolbar, text="Full Retraining", command=self.run_full).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Hunt Stable Edge", command=self.hunt_stable_edge).pack(side="left")
        ttk.Button(toolbar, text="Score Draw", command=self.score_official_draw).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_all).pack(side="left")
        ttk.Button(toolbar, text="Open Outputs", command=lambda: open_path(OUTPUT_DIR)).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Open Data", command=lambda: open_path(DATA_DIR)).pack(side="left")
        self.progress = ttk.Progressbar(toolbar, mode="indeterminate", length=220)
        self.progress.pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        self.dashboard_tab = ttk.Frame(self.tabs)
        self.prediction_tab = ttk.Frame(self.tabs)
        self.learning_tab = ttk.Frame(self.tabs)
        self.jackpot_tab = ttk.Frame(self.tabs)
        self.models_tab = ttk.Frame(self.tabs)
        self.wheels_tab = ttk.Frame(self.tabs)
        self.history_tab = ttk.Frame(self.tabs)
        self.audit_tab = ttk.Frame(self.tabs)
        self.settings_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.dashboard_tab, text="Dashboard")
        self.tabs.add(self.prediction_tab, text="Prediction & Ticket")
        self.tabs.add(self.learning_tab, text="AI Learning")
        self.tabs.add(self.jackpot_tab, text="Jackpot State")
        self.tabs.add(self.models_tab, text="Models")
        self.tabs.add(self.wheels_tab, text="Coverage Wheels")
        self.tabs.add(self.history_tab, text="History")
        self.tabs.add(self.audit_tab, text="Audit & Runs")
        self.tabs.add(self.settings_tab, text="Settings")

        self._build_dashboard()
        self._build_prediction()
        self._build_learning()
        self._build_jackpot()
        self._build_models()
        self._build_wheels()
        self._build_history()
        self._build_audit()
        self._build_settings()
        self._build_statusbar()

        self.bind_all("<Control-r>", lambda _e: self.refresh_all())
        self.bind_all("<Control-g>", lambda _e: self.run_quick())
        self.bind_all("<F5>", lambda _e: self.refresh_all())

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Outputs Folder", command=lambda: open_path(OUTPUT_DIR))
        file_menu.add_command(label="Open Data Folder", command=lambda: open_path(DATA_DIR))
        file_menu.add_command(label="Open Installation Folder", command=lambda: open_path(ROOT))
        file_menu.add_command(label="Open Database Location", command=lambda: open_path(DB_PATH.parent))
        file_menu.add_separator()
        file_menu.add_command(label="Import Jackpot JSON…", command=self.import_jackpot_json)
        file_menu.add_command(label="Export Jackpot Template…", command=self.export_jackpot_template)
        file_menu.add_separator()
        file_menu.add_command(label="Open Latest Ticket", command=self.open_latest_ticket)
        file_menu.add_command(label="Open Latest JSON Report", command=self.open_latest_report)
        file_menu.add_command(label="Open Edge Report", command=self.open_edge_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Generate Prediction (Quick)\tCtrl+G", command=self.run_quick)
        run_menu.add_command(label="Full Research Retraining…", command=self.run_full)
        run_menu.add_separator()
        run_menu.add_command(label="Hunt Stable Edge…", command=self.hunt_stable_edge)
        run_menu.add_command(label="Train AI on History…", command=self.train_on_history)
        run_menu.add_command(label="Score Official Draw…", command=self.score_official_draw)
        run_menu.add_separator()
        run_menu.add_command(label="Verify Coverage Wheels", command=self.refresh_wheels)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dashboard", command=lambda: self._show_tab(0))
        view_menu.add_command(label="Prediction & Ticket", command=lambda: self._show_tab(1))
        view_menu.add_command(label="AI Learning", command=lambda: self._show_tab(2))
        view_menu.add_command(label="Jackpot State", command=lambda: self._show_tab(3))
        view_menu.add_command(label="Models", command=lambda: self._show_tab(4))
        view_menu.add_command(label="Coverage Wheels", command=lambda: self._show_tab(5))
        view_menu.add_command(label="History", command=lambda: self._show_tab(6))
        view_menu.add_command(label="Audit & Runs", command=lambda: self._show_tab(7))
        view_menu.add_command(label="Settings", command=lambda: self._show_tab(8))
        view_menu.add_separator()
        view_menu.add_command(label="Refresh All\tF5", command=self.refresh_all)
        view_menu.add_command(label="Clear Live Log", command=self.clear_live_log)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="List Probability Methods", command=self.show_method_catalog)
        tools_menu.add_command(label="Copy Telemetry Snapshot", command=self.copy_telemetry_snapshot)
        tools_menu.add_command(label="Open Canonical History CSV", command=lambda: open_path(HISTORY))
        tools_menu.add_command(label="Open Engine Artifacts", command=lambda: open_path(ENGINE_OUT_DIR))

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Disclaimer", command=self.show_disclaimer)

    def _show_tab(self, index: int) -> None:
        self.tabs.select(index)

    def _build_statusbar(self) -> None:
        bar = ttk.Frame(self, padding=(12, 2, 12, 8))
        bar.pack(fill="x", side="bottom")
        self.footer_left = ttk.Label(bar, text="", style="Footer.TLabel")
        self.footer_left.pack(side="left")
        self.footer_right = ttk.Label(bar, text="", style="Footer.TLabel")
        self.footer_right.pack(side="right")

    def _metric_tile(self, parent: ttk.Frame, caption: str) -> ttk.Label:
        box = ttk.LabelFrame(parent, text=caption, padding=8)
        box.pack(side="left", fill="both", expand=True, padx=4)
        value = ttk.Label(box, text="—", style="MetricValue.TLabel")
        value.pack(anchor="w")
        hint = ttk.Label(box, text="", style="MetricCaption.TLabel")
        hint.pack(anchor="w")
        value._hint = hint  # type: ignore[attr-defined]
        return value

    def _build_dashboard(self) -> None:
        # Telemetry strip
        metrics = ttk.Frame(self.dashboard_tab, padding=(8, 10, 8, 4))
        metrics.pack(fill="x")
        self.metric_draws = self._metric_tile(metrics, "Canonical Draws")
        self.metric_runs = self._metric_tile(metrics, "Workflow Runs")
        self.metric_learning = self._metric_tile(metrics, "AI Learning")
        self.metric_edge = self._metric_tile(metrics, "Stable Edge")
        self.metric_jackpot = self._metric_tile(metrics, "Jackpot State")
        self.metric_odds = self._metric_tile(metrics, "Jackpot Odds")

        metrics2 = ttk.Frame(self.dashboard_tab, padding=(8, 0, 8, 8))
        metrics2.pack(fill="x")
        self.metric_models = self._metric_tile(metrics2, "Models")
        self.metric_wheels = self._metric_tile(metrics2, "Wheels")
        self.metric_tickets = self._metric_tile(metrics2, "Tickets")
        self.metric_db = self._metric_tile(metrics2, "Database")
        self.metric_champion = self._metric_tile(metrics2, "Champion")
        self.metric_target = self._metric_tile(metrics2, "Next / Last Target")

        # Snapshot + actions
        mid = ttk.Panedwindow(self.dashboard_tab, orient="horizontal")
        mid.pack(fill="both", expand=False, padx=12, pady=4)

        snap = ttk.LabelFrame(mid, text="Live Snapshot", padding=10)
        actions = ttk.LabelFrame(mid, text="Main Actions", padding=10)
        mid.add(snap, weight=3)
        mid.add(actions, weight=2)

        self.dashboard_summary = tk.Text(snap, height=12, wrap="word", font=("Segoe UI", 11))
        self.dashboard_summary.pack(fill="both", expand=True)

        action_specs = [
            ("Generate Prediction (Quick)", self.run_quick, True),
            ("Run Full Research Engine", self.run_full, False),
            ("Hunt Stable Edge", self.hunt_stable_edge, False),
            ("Train AI on History", self.train_on_history, False),
            ("Score Official Draw", self.score_official_draw, False),
            ("Import Jackpot JSON", self.import_jackpot_json, False),
            ("Verify Coverage Wheels", self.refresh_wheels, False),
            ("View Latest Ticket", self.open_latest_ticket, False),
            ("Open Latest Report", self.open_latest_report, False),
            ("Open Edge Report", self.open_edge_report, False),
            ("Refresh Telemetry", self.refresh_all, False),
            ("Clear Live Log", self.clear_live_log, False),
        ]
        grid = ttk.Frame(actions)
        grid.pack(fill="both", expand=True)
        for i, (label, cmd, primary) in enumerate(action_specs):
            r, c = divmod(i, 2)
            btn = ttk.Button(
                grid,
                text=label,
                style="Primary.TButton" if primary else "Action.TButton",
                command=cmd,
            )
            btn.grid(row=r, column=c, sticky="ew", padx=4, pady=4)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        log_frame = ttk.LabelFrame(self.dashboard_tab, text="Live Run Log / Telemetry Stream", padding=8)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(4, 8))
        log_tools = ttk.Frame(log_frame)
        log_tools.pack(fill="x", pady=(0, 4))
        ttk.Button(log_tools, text="Clear", command=self.clear_live_log).pack(side="right")
        ttk.Button(log_tools, text="Copy Log", command=self.copy_live_log).pack(side="right", padx=6)
        self.live_log = tk.Text(log_frame, wrap="word", font=("Consolas", 9), height=10)
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
        ttk.Button(action_row, text="Generate Prediction", style="Primary.TButton", command=self.run_quick).pack(side="left")
        ttk.Button(action_row, text="Open Ticket", command=self.open_latest_ticket).pack(side="left", padx=6)
        ttk.Button(action_row, text="Open JSON Report", command=self.open_latest_report).pack(side="left")
        ttk.Button(action_row, text="Refresh", command=self.refresh_prediction).pack(side="left", padx=6)

        ttk.Label(right, text="Latest Rendered Ticket", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        self.ticket_canvas = tk.Canvas(right, bg="#e6e6e6", highlightthickness=0)
        self.ticket_canvas.pack(fill="both", expand=True)
        self.ticket_canvas.bind("<Configure>", lambda _event: self._render_ticket_preview())

    def _build_learning(self) -> None:
        top = ttk.Frame(self.learning_tab, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="Score Official Draw", style="Primary.TButton", command=self.score_official_draw).pack(side="left")
        ttk.Button(top, text="Train on History", command=self.train_on_history).pack(side="left", padx=6)
        ttk.Button(top, text="Hunt Stable Edge", command=self.hunt_stable_edge).pack(side="left")
        ttk.Button(top, text="Refresh Learning", command=self.refresh_learning).pack(side="left", padx=6)

        self.learning_summary = tk.Text(self.learning_tab, height=10, wrap="word", font=("Segoe UI", 11))
        self.learning_summary.pack(fill="x", padx=12, pady=(0, 8))

        pane = ttk.Panedwindow(self.learning_tab, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=1)
        pane.add(right, weight=2)

        ttk.Label(left, text="Top Adaptive Main Weights", style="Heading.TLabel").pack(anchor="w")
        self.learning_main_tree = ttk.Treeview(left, columns=("number", "weight"), show="headings", height=12)
        self.learning_main_tree.heading("number", text="Number")
        self.learning_main_tree.heading("weight", text="Weight")
        self.learning_main_tree.column("number", width=90, anchor="center")
        self.learning_main_tree.column("weight", width=110, anchor="center")
        self.learning_main_tree.pack(fill="both", expand=True, pady=6)

        ttk.Label(right, text="Recent Learning Events", style="Heading.TLabel").pack(anchor="w")
        self.learning_events_tree = ttk.Treeview(
            right,
            columns=("draw", "main", "euro", "result", "reward", "when"),
            show="headings",
            height=12,
        )
        for col, label, width in [
            ("draw", "Draw", 110),
            ("main", "Main Hits", 90),
            ("euro", "Euro Hits", 90),
            ("result", "Outcome", 90),
            ("reward", "Reward", 90),
            ("when", "Scored UTC", 190),
        ]:
            self.learning_events_tree.heading(col, text=label)
            self.learning_events_tree.column(col, width=width, anchor="center")
        self.learning_events_tree.pack(fill="both", expand=True, pady=6)

    def _build_jackpot(self) -> None:
        top = ttk.Frame(self.jackpot_tab, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="Import ENGINE_STATE_JSON", style="Primary.TButton", command=self.import_jackpot_json).pack(side="left")
        ttk.Button(top, text="Refresh State", command=self.refresh_jackpot).pack(side="left", padx=6)
        ttk.Button(top, text="Export Template", command=self.export_jackpot_template).pack(side="left")

        self.jackpot_text = tk.Text(self.jackpot_tab, wrap="word", font=("Segoe UI", 11))
        self.jackpot_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_models(self) -> None:
        top = ttk.Frame(self.models_tab, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="Refresh Models", style="Primary.TButton", command=self.refresh_models).pack(side="left")
        ttk.Button(top, text="List Probability Methods", command=self.show_method_catalog).pack(side="left", padx=6)
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
        self.models_tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

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
        top = ttk.Frame(self.history_tab, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="Refresh History", style="Primary.TButton", command=self.refresh_history).pack(side="left")
        ttk.Button(top, text="Open Canonical CSV", command=lambda: open_path(HISTORY)).pack(side="left", padx=6)
        self.history_text = tk.Text(self.history_tab, wrap="word", font=("Segoe UI", 11))
        self.history_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_audit(self) -> None:
        top = ttk.Frame(self.audit_tab, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="Refresh Runs", style="Primary.TButton", command=self.refresh_audit).pack(side="left")
        ttk.Button(top, text="Open Selected Ticket", command=self._open_selected_audit_ticket).pack(side="left", padx=6)
        ttk.Button(top, text="Open Outputs", command=lambda: open_path(OUTPUT_DIR)).pack(side="left")
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
        self.audit_tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))
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
        row = len(values) + 1
        ttk.Button(frame, text="Open User Data", command=lambda: open_path(DATA_DIR)).grid(row=row, column=0, sticky="w")
        ttk.Button(frame, text="Open Installation Folder", command=lambda: open_path(ROOT)).grid(row=row, column=1, sticky="w")
        ttk.Button(frame, text="Open Outputs", command=lambda: open_path(OUTPUT_DIR)).grid(row=row + 1, column=0, sticky="w", pady=6)
        ttk.Button(frame, text="Open Engine Artifacts", command=lambda: open_path(ENGINE_OUT_DIR)).grid(row=row + 1, column=1, sticky="w", pady=6)
        ttk.Button(frame, text="Copy Telemetry Snapshot", command=self.copy_telemetry_snapshot).grid(row=row + 2, column=0, sticky="w")
        ttk.Button(frame, text="About", command=self.show_about).grid(row=row + 2, column=1, sticky="w")

    def _set_busy(self, busy: bool, text: str = "Ready") -> None:
        style = "StatusWarn.TLabel" if busy else (
            "StatusBad.TLabel" if "fail" in text.lower() else "StatusGood.TLabel"
        )
        self.status_label.config(text=text, style=style)
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
        self.refresh_learning()
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
            last_draw = conn.execute(
                "SELECT * FROM draws ORDER BY draw_date DESC LIMIT 1"
            ).fetchone() if self._table_exists(conn, "draws") else None

        learn = learning_status(DB_PATH)
        rate = "n/a" if learn["success_rate"] is None else f"{learn['success_rate']:.1%}"
        edge = self._load_edge_summary()
        jackpot = self._load_jackpot_snapshot()
        wheels_pass, wheels_total = self._wheel_pass_counts()

        # Metric tiles
        self._set_metric(self.metric_draws, str(draws), f"Latest: {last_draw['draw_date'] if last_draw else 'n/a'}")
        self._set_metric(self.metric_runs, str(runs), f"Artifacts: {artifacts}")
        self._set_metric(
            self.metric_learning,
            str(learn["events"]),
            f"Success {learn['successes']} / Fail {learn['failures']} ({rate})",
        )
        if edge:
            edge_label = "EURO" if edge.get("euro_edge_detected") and not edge.get("main_edge_detected") else (
                "FULL" if edge.get("draw_probability_edge_detected") else (
                    "MAIN" if edge.get("main_edge_detected") else "NONE"
                )
            )
            self._set_metric(
                self.metric_edge,
                edge_label,
                str(edge.get("decision", "n/a"))[:42],
            )
        else:
            self._set_metric(self.metric_edge, "—", "No edge search yet")
        self._set_metric(
            self.metric_jackpot,
            jackpot.get("display", "n/a"),
            jackpot.get("mode", "NO VERIFIED STATE"),
        )
        self._set_metric(self.metric_odds, "1 / 139,838,160", "Unique line · fail-closed")
        self._set_metric(self.metric_models, str(models), "Champion stays uniform")
        self._set_metric(self.metric_wheels, f"{wheels_pass}/{wheels_total}", "Coverage verification")
        self._set_metric(self.metric_tickets, str(artifacts), "Rendered ticket images")
        self._set_metric(
            self.metric_db,
            "OK" if integrity == "ok" else "CHECK",
            integrity if integrity == "ok" else str(integrity)[:40],
        )
        self._set_metric(self.metric_champion, "Uniform", learn.get("deployed_champion", "uniform-1.0"))
        target = last_run["target_draw"] if last_run else (last_draw["draw_date"] if last_draw else "n/a")
        self._set_metric(
            self.metric_target,
            str(target),
            f"Mode: {last_run['engine_mode'] if last_run else 'n/a'}",
        )

        lines = [
            f"{APP_NAME} v{APP_VERSION}",
            "",
            "Telemetry snapshot",
            f"• Database integrity: {integrity}",
            f"• Canonical draws: {draws}" + (f" (latest {last_draw['draw_date']})" if last_draw else ""),
            f"• Registered models: {models}",
            f"• Workflow runs: {runs} | ticket artifacts: {artifacts}",
            f"• AI learning: {learn['events']} events · success rate {rate}",
            f"• Deployed champion: exact-uniform (research ranking may adapt)",
            f"• Unique-line jackpot odds: 1/139,838,160",
            f"• Jackpot display: {jackpot.get('display', 'n/a')} ({jackpot.get('mode', 'n/a')})",
        ]
        if edge:
            primary = edge.get("primary") or {}
            lines += [
                "",
                "Stable-edge hunt",
                f"• Decision: {edge.get('decision')}",
                f"• Euro edge: {edge.get('euro_edge_detected')} | Main edge: {edge.get('main_edge_detected')}",
                f"• Euro Brier Δ: {edge.get('euro_brier_improvement', 'n/a')}",
                f"• Primary research line: {primary.get('main')} + {primary.get('euro')}",
            ]
        else:
            lines += ["", "Stable-edge hunt: not run yet (use Hunt Stable Edge)."]

        if last_run:
            lines += [
                "",
                "Latest workflow run",
                f"• Run ID: {last_run['run_id']}",
                f"• Target draw: {last_run['target_draw']}",
                f"• Engine mode: {last_run['engine_mode']}",
                f"• Decision: {last_run['overall_status']}",
                f"• Jackpot mode: {last_run['jackpot_mode']}",
                f"• Ticket: {last_run['output_image']}",
            ]
        else:
            lines += ["", "Latest workflow run: none yet."]

        self.dashboard_summary.delete("1.0", "end")
        self.dashboard_summary.insert("1.0", "\n".join(lines))
        self._telemetry_cache = "\n".join(lines)
        self._update_footer(integrity=integrity, draws=draws, runs=runs)

    def _set_metric(self, label: ttk.Label, value: str, hint: str = "") -> None:
        label.config(text=value)
        hint_label = getattr(label, "_hint", None)
        if hint_label is not None:
            hint_label.config(text=hint)

    def _update_footer(self, *, integrity: str = "ok", draws: int = 0, runs: int = 0) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.footer_left.config(
            text=f"v{APP_VERSION}  ·  DB {integrity}  ·  {draws} draws  ·  {runs} runs  ·  {DATA_DIR}"
        )
        self.footer_right.config(text=now)

    def _load_edge_summary(self) -> dict:
        candidates = [
            OUTPUT_DIR / "EuroJackpot_Edge_Search_Summary_v3_8.json",
            ENGINE_OUT_DIR / "EuroJackpot_Edge_Search_Summary_v3_8.json",
            ROOT / "EuroJackpot_Edge_Search_Summary_v3_8.json",
        ]
        for path in candidates:
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
        return {}

    def _load_jackpot_snapshot(self) -> dict:
        try:
            state = latest_state(DB_PATH)
            if not state:
                return {"display": "n/a", "mode": "NO VERIFIED STATE"}
            return {
                "display": f"€{float(state.get('jackpot_eur', 0)):,.0f}",
                "mode": state.get("verification_status", "n/a"),
            }
        except Exception:
            return {"display": "n/a", "mode": "NO VERIFIED STATE"}

    def _wheel_pass_counts(self) -> tuple[int, int]:
        pool = [4, 21, 25, 27, 28, 35, 36, 37, 42, 44, 48, 50]
        specs = [
            ("EuroJackpot_Wheel_54_Pair_Compact.csv", 54, 2),
            ("EuroJackpot_Wheel_135_Pair_Extended.csv", 135, 2),
            ("EuroJackpot_Wheel_198_Triple_Compact.csv", 198, 3),
            ("EuroJackpot_Wheel_495_Triple_Extended.csv", 495, 3),
        ]
        passed = 0
        for filename, expected, subset in specs:
            try:
                result = verify_wheel_csv(ROOT / filename, expected, subset, pool)
                if result.get("passed"):
                    passed += 1
            except Exception:
                pass
        return passed, len(specs)

    def refresh_learning(self) -> None:
        status = learning_status(DB_PATH)
        rate = "n/a" if status["success_rate"] is None else f"{status['success_rate']:.1%}"
        summary = [
            "Adaptive AI Learning (research only)",
            "",
            f"Events scored: {status['events']}",
            f"Successes: {status['successes']}",
            f"Failures: {status['failures']}",
            f"Success rate: {rate}",
            f"Avg main hits: {status['avg_main_hits']}",
            f"Avg euro hits: {status['avg_euro_hits']}",
            f"Deployed champion: {status['deployed_champion']}",
            "",
            status["disclaimer"],
            "",
            "After each official draw, use Score Official Draw so the learner can reinforce hits and damp misses.",
        ]
        self.learning_summary.delete("1.0", "end")
        self.learning_summary.insert("1.0", "\n".join(summary))

        self.learning_main_tree.delete(*self.learning_main_tree.get_children())
        for row in status["top_main"]:
            self.learning_main_tree.insert("", "end", values=(row["number"], f"{row['weight']:.4f}"))

        self.learning_events_tree.delete(*self.learning_events_tree.get_children())
        for event in status["recent_events"]:
            self.learning_events_tree.insert(
                "",
                "end",
                values=(
                    event["target_draw"],
                    event["main_hits"],
                    event["euro_hits"],
                    "SUCCESS" if event["success"] else "FAIL",
                    f"{float(event['reward']):+.3f}",
                    event["created_at_utc"],
                ),
            )

    def hunt_stable_edge(self) -> None:
        if not messagebox.askyesno(
            "Hunt stable edge",
            "Run the multi-signal walk-forward edge search?\n\n"
            "It tests hard for a draw-probability edge and builds a prize-value research portfolio.\n"
            "Deployed jackpot odds stay uniform unless every gate passes.",
        ):
            return

        def worker() -> None:
            try:
                self.events.put(("log", "Starting stable-edge search…"))
                report = run_edge_search(
                    HISTORY,
                    min_history=120,
                    train_learner=True,
                    output_dir=ENGINE_OUT_DIR,
                )
                summary = OUTPUT_DIR / "EuroJackpot_Edge_Search_Summary_v3_8.json"
                summary.write_text(
                    json.dumps(
                        {
                            "overall_status": report["overall_status"],
                            "decision": report["gates"]["decision"],
                            "main_edge_detected": report["gates"]["main_edge_detected"],
                            "euro_edge_detected": report["gates"]["euro_edge_detected"],
                            "draw_probability_edge_detected": report["gates"][
                                "draw_probability_edge_detected"
                            ],
                            "primary": report["primary_experimental_line"],
                            "statement": report["statement"],
                            "report_file": report["report_file"],
                            "results_file": report["results_file"],
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                self.events.put((
                    "log",
                    (
                        f"Edge search done: {report['gates']['decision']} | "
                        f"euro_edge={report['gates']['euro_edge_detected']} | "
                        f"main_edge={report['gates']['main_edge_detected']} | "
                        f"primary={report['primary_experimental_line']}"
                    ),
                ))
                self.events.put(("done", {"ticket_image": None, "edge": report}))
            except Exception:
                self.events.put(("error", traceback.format_exc()))

        self._start_thread(worker, "Hunting stable edge…")

    def train_on_history(self) -> None:
        if not messagebox.askyesno(
            "Train on history",
            "Walk-forward train the AI on official EuroJackpot history?\n\n"
            "For each past draw it predicts using only earlier draws, then learns from the real result.\n"
            "This can take a minute or two.",
        ):
            return

        def worker() -> None:
            try:
                self.events.put(("log", "Starting historical walk-forward training…"))
                result = train_on_history(
                    DB_PATH,
                    HISTORY,
                    min_history=80,
                    reset=True,
                    progress_every=100,
                )
                report = OUTPUT_DIR / "EuroJackpot_History_Training_Report_v3_8.json"
                report.write_text(json.dumps(result, indent=2), encoding="utf-8")
                # Keep a dedicated copy under engine/ for inspection.
                ENGINE_OUT_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(DB_PATH, ENGINE_OUT_DIR / "EuroJackpot_Learning_History.sqlite")
                self.events.put((
                    "log",
                    (
                        f"History training done: {result['trained_draws']} draws, "
                        f"avg main hits {result['avg_main_hits']:.3f}, "
                        f"success rate {result['success_rate']:.1%}. Report: {report}"
                    ),
                ))
                self.events.put(("done", {"ticket_image": None, "training": result}))
            except Exception:
                self.events.put(("error", traceback.format_exc()))

        self._start_thread(worker, "Training AI on history…")

    def score_official_draw(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Score Official Draw")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        fields = ttk.Frame(dialog, padding=14)
        fields.pack(fill="both", expand=True)
        ttk.Label(fields, text="Draw date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w", pady=4)
        date_var = tk.StringVar()
        ttk.Entry(fields, textvariable=date_var, width=28).grid(row=0, column=1, sticky="w", pady=4)
        ttk.Label(fields, text="Main numbers (5 comma-separated)").grid(row=1, column=0, sticky="w", pady=4)
        main_var = tk.StringVar()
        ttk.Entry(fields, textvariable=main_var, width=28).grid(row=1, column=1, sticky="w", pady=4)
        ttk.Label(fields, text="Euro numbers (2 comma-separated)").grid(row=2, column=0, sticky="w", pady=4)
        euro_var = tk.StringVar()
        ttk.Entry(fields, textvariable=euro_var, width=28).grid(row=2, column=1, sticky="w", pady=4)

        def submit() -> None:
            try:
                main_nums = [int(x.strip()) for x in main_var.get().split(",") if x.strip()]
                euro_nums = [int(x.strip()) for x in euro_var.get().split(",") if x.strip()]
                result = score_draw_result(
                    DB_PATH,
                    draw_date=date_var.get().strip(),
                    result_main=main_nums,
                    result_euro=euro_nums,
                    source="desktop-manual",
                )
                dialog.destroy()
                self.refresh_all()
                messagebox.showinfo(
                    "Draw scored",
                    (
                        f"Predictions scored: {len(result['predictions_scored'])}\n"
                        f"Workflow lines scored: {len(result['workflow_lines_scored'])}\n"
                        f"Learning events: {result['learning']['events']}\n\n"
                        f"{result['statement']}"
                    ),
                )
            except Exception as exc:
                messagebox.showerror("Score failed", str(exc))

        buttons = ttk.Frame(fields)
        buttons.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(buttons, text="Score & Learn", style="Primary.TButton", command=submit).pack(side="right", padx=8)

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

    def clear_live_log(self) -> None:
        self.live_log.delete("1.0", "end")

    def copy_live_log(self) -> None:
        content = self.live_log.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(content)
        self.status_label.config(text="Log copied", style="StatusGood.TLabel")

    def copy_telemetry_snapshot(self) -> None:
        content = getattr(self, "_telemetry_cache", "") or self.dashboard_summary.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(content.strip())
        self.status_label.config(text="Telemetry copied", style="StatusGood.TLabel")

    def open_edge_report(self) -> None:
        candidates = [
            ENGINE_OUT_DIR / "EuroJackpot_Edge_Search_Report_v3_8.json",
            OUTPUT_DIR / "EuroJackpot_Edge_Search_Summary_v3_8.json",
            ROOT / "EuroJackpot_Edge_Search_Summary_v3_8.json",
        ]
        for path in candidates:
            if path.exists():
                open_path(path)
                return
        messagebox.showinfo("Edge report", "No edge-search report found yet. Run Hunt Stable Edge first.")

    def show_method_catalog(self) -> None:
        try:
            from eurojackpot_edge_engine_v3_8 import method_catalog
            payload = json.dumps(method_catalog(), indent=2)
        except Exception as exc:
            messagebox.showerror("Methods", str(exc))
            return
        dialog = tk.Toplevel(self)
        dialog.title("Probability Method Catalog")
        dialog.geometry("760x520")
        dialog.transient(self)
        text_box = tk.Text(dialog, wrap="word", font=("Consolas", 10))
        text_box.pack(fill="both", expand=True, padx=10, pady=10)
        text_box.insert("1.0", payload)
        text_box.config(state="disabled")

    def show_about(self) -> None:
        messagebox.showinfo(
            "About",
            (
                f"{APP_NAME}\n"
                f"Version {APP_VERSION}\n\n"
                "Desktop control center for prediction, AI learning,\n"
                "stable-edge hunt, jackpot state, wheels, and audit.\n\n"
                "Deployed champion remains exact-uniform unless every\n"
                "promotion gate passes. Unique-line odds: 1/139,838,160."
            ),
        )

    def show_disclaimer(self) -> None:
        path = ROOT / "DISCLAIMER.md"
        body = path.read_text(encoding="utf-8") if path.exists() else (
            "Research / entertainment software. Lottery house edge remains. "
            "No guaranteed profit. Deployed odds stay uniform unless gates pass."
        )
        dialog = tk.Toplevel(self)
        dialog.title("Disclaimer")
        dialog.geometry("720x480")
        dialog.transient(self)
        text_box = tk.Text(dialog, wrap="word", font=("Segoe UI", 11))
        text_box.pack(fill="both", expand=True, padx=10, pady=10)
        text_box.insert("1.0", body)
        text_box.config(state="disabled")

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
