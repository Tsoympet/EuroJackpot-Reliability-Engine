# EuroJackpot Ticket Renderer Integration v3.6

This module adds an automated **ticket-image output layer** to the EuroJackpot engine.

## What it does

After each prediction run, the engine can render a EuroJackpot-style image showing:

- draw date
- jackpot field
- engine version
- mode
- run ID
- the primary prediction line
- up to four alternative lines
- one reserve column left empty if desired

The renderer uses the clean template image:

- `EuroJackpot_Ticket_Template_v3_6.png`

and generates an output such as:

- `EuroJackpot_Ticket_Run_2026-07-28_v3_6.png`

## Engine integration

### Option A — from a payload JSON

```bash
python eurojackpot_ticket_renderer_v3_6.py \
  --json EuroJackpot_Ticket_Payload_Sample_v3_6.json \
  --db EuroJackpot_Operational_v3_6.sqlite \
  --output EuroJackpot_Ticket_Output_v3_6.png
```

### Option B — directly from the latest prediction row in the database

```bash
python eurojackpot_ticket_renderer_v3_6.py \
  --latest \
  --db EuroJackpot_Operational_v3_6.sqlite \
  --jackpot "TBA" \
  --mode "Whole-engine consensus" \
  --alt-line "4,32,37,41,45|2,3" \
  --alt-line "1,32,37,44,48|3,7" \
  --alt-line "2,34,36,43,49|7,12" \
  --alt-line "6,33,39,42,47|5,11" \
  --output EuroJackpot_Ticket_Output_v3_6.png
```

## Database logging

The module creates `ticket_artifacts` in the operational SQLite database and records:

- target draw
- creation timestamp
- template name
- output image path
- payload JSON
- source prediction hash
- mode
- engine version

## Notes

- The ticket image is a **presentation/output artifact** only.
- It does **not** change the prediction logic.
- If no alternative lines are supplied, only the primary line is filled and the remaining columns stay empty.
