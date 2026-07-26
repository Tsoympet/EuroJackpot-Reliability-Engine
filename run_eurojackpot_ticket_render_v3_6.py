
from pathlib import Path
from eurojackpot_ticket_renderer_v3_6 import payload_from_json, render_ticket

ROOT = Path(__file__).resolve().parent
payload = payload_from_json(ROOT / "EuroJackpot_Ticket_Payload_Sample_v3_6.json")
out = render_ticket(payload, ROOT / "EuroJackpot_Ticket_Run_2026-07-28_v3_6.png", ROOT / "EuroJackpot_Ticket_Template_v3_6.png", db_path=ROOT / "EuroJackpot_Operational_v3_6.sqlite")
print(out)
