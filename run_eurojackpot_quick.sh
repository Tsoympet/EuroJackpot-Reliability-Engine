#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 eurojackpot_one_click_v3_7.py --engine-mode audited
