
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = ROOT / "EuroJackpot_Ticket_Template_v3_6.png"
DEFAULT_OUTPUT = ROOT / "EuroJackpot_Ticket_Output_v3_6.png"

W, H = 1448, 1086
PANEL_LEFTS = [28, 266, 504, 742, 980, 1218]
PANEL_TOP = 346
PANEL_WIDTH = 220

MAIN_X0 = 37
MAIN_Y0 = 65
MAIN_X_STEP = 38.7
MAIN_Y_STEP = 30.1

EURO_X0 = 26
EURO_Y0 = 403
EURO_X_STEP = 31.5
EURO_Y_STEP = 31.8

LABEL_Y = 322

PRIMARY_FILL = "#1E4DB7"
ALT_FILL = "#1E4DB7"
TEXT_DARK = "#5a3400"
OUTLINE = "#C78C33"
WHITE = "#FFFFFF"

HEADER_Y = 59
HEADER_TEXT_X = {
    "draw_date": 165,
    "jackpot": 500,
    "engine_version": 770,
    "mode": 1010,
    "run_id": 1285,
}


@dataclass
class TicketPayload:
    draw_date: str
    jackpot: str
    engine_version: str
    mode: str
    run_id: str
    source_record_hash: str | None
    line_labels: list[str]
    lines: list[dict[str, list[int]]]


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT_SMALL = _load_font(16, False)
FONT_SMALL_BOLD = _load_font(17, True)
FONT_MED = _load_font(22, False)
FONT_MED_BOLD = _load_font(26, True)
FONT_BIG_BOLD = _load_font(28, True)
FONT_NUM = _load_font(24, True)


def _draw_centered(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font, fill=TEXT_DARK):
    bbox = draw.textbbox((0,0), text, font=font)
    x = xy[0] - (bbox[2]-bbox[0]) / 2
    y = xy[1] - (bbox[3]-bbox[1]) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _main_position(panel_index: int, number: int) -> tuple[float, float]:
    n = number - 1
    row, col = divmod(n, 5)
    x = PANEL_LEFTS[panel_index] + MAIN_X0 + col * MAIN_X_STEP
    y = PANEL_TOP + MAIN_Y0 + row * MAIN_Y_STEP
    return x, y


def _euro_position(panel_index: int, number: int) -> tuple[float, float]:
    if not 1 <= number <= 12:
        raise ValueError(f"Euro number out of range: {number}")
    row = 0 if number <= 6 else 1
    col = (number - 1) % 6
    x = PANEL_LEFTS[panel_index] + EURO_X0 + col * EURO_X_STEP
    y = PANEL_TOP + EURO_Y0 + row * EURO_Y_STEP
    return x, y


def _draw_marker(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, shape: str = "circle"):
    if shape == "square":
        r = 17
        draw.rounded_rectangle((x-r, y-r, x+r, y+r), radius=8, fill=PRIMARY_FILL, outline=OUTLINE, width=1)
    else:
        r = 17
        draw.ellipse((x-r, y-r, x+r, y+r), fill=ALT_FILL, outline=OUTLINE, width=1)
    _draw_centered(draw, (x, y+0.5), text, FONT_NUM, WHITE)


def ensure_ticket_schema(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_artifacts (
                artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_draw TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                template_name TEXT NOT NULL,
                output_path TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                source_record_hash TEXT,
                mode TEXT,
                engine_version TEXT
            )
            """
        )


def payload_from_json(path: str | Path) -> TicketPayload:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return TicketPayload(**data)


def payload_from_latest_prediction(
    db_path: str | Path,
    alt_lines: Sequence[str] | None = None,
    jackpot: str = "TBA",
    mode: str | None = None,
) -> TicketPayload:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM predictions ORDER BY target_draw DESC LIMIT 1").fetchone()
        if row is None:
            raise RuntimeError("No prediction row found in predictions table.")
        primary_main = [int(x) for x in json.loads(str(row["primary_main"]))]
        primary_euro = [int(x) for x in json.loads(str(row["primary_euro"]))]
        line_labels = ["Primary", "Alt 1", "Alt 2", "Alt 3", "Alt 4", "Reserve"]
        lines = [{"main": primary_main, "euro": primary_euro}]
        if alt_lines:
            for item in alt_lines[:4]:
                main_part, euro_part = item.split("|")
                lines.append({
                    "main": [int(x) for x in main_part.split(",") if x],
                    "euro": [int(x) for x in euro_part.split(",") if x],
                })
        while len(lines) < 6:
            lines.append({"main": [], "euro": []})
        run_id = f"{row['target_draw']}-{str(row['record_hash'])[:12]}"
        return TicketPayload(
            draw_date=str(row["target_draw"]),
            jackpot=jackpot,
            engine_version=str(row["model_version"]),
            mode=mode or str(row["confidence_state"]),
            run_id=run_id,
            source_record_hash=str(row["record_hash"]),
            line_labels=line_labels,
            lines=lines[:6],
        )


def render_ticket(
    payload: TicketPayload | dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT,
    template_path: str | Path = DEFAULT_TEMPLATE,
    db_path: str | Path | None = None,
) -> Path:
    if isinstance(payload, dict):
        payload = TicketPayload(**payload)
    image = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(image)

    # Header values
    values = {
        "draw_date": payload.draw_date,
        "jackpot": payload.jackpot,
        "engine_version": payload.engine_version,
        "mode": payload.mode,
        "run_id": payload.run_id[:24],
    }
    header_fonts = {
        "draw_date": FONT_SMALL_BOLD,
        "jackpot": FONT_SMALL_BOLD,
        "engine_version": FONT_SMALL_BOLD,
        "mode": FONT_SMALL_BOLD,
        "run_id": _load_font(14, True),
    }
    values["mode"] = values["mode"][:22]
    values["run_id"] = values["run_id"][:12]
    for key, x in HEADER_TEXT_X.items():
        _draw_centered(draw, (x, HEADER_Y), values[key], header_fonts[key], TEXT_DARK)

    # Column labels on compact tags so they remain readable over the artwork.
    for i, label in enumerate((payload.line_labels + [""] * 6)[:6]):
        cx = PANEL_LEFTS[i] + PANEL_WIDTH / 2
        tag_w = 86
        tag_h = 22
        draw.rounded_rectangle(
            (cx-tag_w/2, LABEL_Y-tag_h/2, cx+tag_w/2, LABEL_Y+tag_h/2),
            radius=7,
            fill="#FFF7E8",
            outline=OUTLINE,
            width=1,
        )
        _draw_centered(draw, (cx, LABEL_Y), label, _load_font(14, True), TEXT_DARK)

    # Mark numbers
    for i, line in enumerate((payload.lines + [{"main": [], "euro": []}] * 6)[:6]):
        shape = "square" if i == 0 else "circle"
        for n in line.get("main", []):
            if 1 <= int(n) <= 50:
                x, y = _main_position(i, int(n))
                _draw_marker(draw, x, y, str(int(n)), shape=shape)
        for n in line.get("euro", []):
            if 1 <= int(n) <= 12:
                x, y = _euro_position(i, int(n))
                _draw_marker(draw, x, y, str(int(n)), shape=shape)

    output_path = Path(output_path)
    image.save(output_path)

    if db_path is not None:
        ensure_ticket_schema(db_path)
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO ticket_artifacts (
                    target_draw, created_at_utc, template_name, output_path, payload_json,
                    source_record_hash, mode, engine_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.draw_date,
                    datetime.now(timezone.utc).isoformat(),
                    Path(template_path).name,
                    str(output_path),
                    json.dumps(asdict(payload), sort_keys=True),
                    payload.source_record_hash,
                    payload.mode,
                    payload.engine_version,
                ),
            )

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Render EuroJackpot ticket image from payload or latest DB prediction.")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--db", default=None, help="Operational SQLite DB. If provided with --latest, reads latest prediction and logs artifact.")
    parser.add_argument("--json", default=None, help="Ticket payload JSON file.")
    parser.add_argument("--latest", action="store_true", help="Use latest row from predictions table in --db.")
    parser.add_argument("--jackpot", default="TBA")
    parser.add_argument("--mode", default=None)
    parser.add_argument("--alt-line", action="append", default=[], help='Alternative line format: "4,32,37,41,45|2,3"')
    args = parser.parse_args()

    if args.latest:
        if not args.db:
            parser.error("--latest requires --db")
        payload = payload_from_latest_prediction(args.db, alt_lines=args.alt_line, jackpot=args.jackpot, mode=args.mode)
        render_ticket(payload, args.output, args.template, db_path=args.db)
    elif args.json:
        payload = payload_from_json(args.json)
        render_ticket(payload, args.output, args.template, db_path=args.db)
    else:
        parser.error("Provide either --json or --latest")

    print(str(Path(args.output)))


if __name__ == "__main__":
    main()
