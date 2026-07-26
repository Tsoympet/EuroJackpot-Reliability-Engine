# EuroJackpot Prize Watch Integration v3.5

The scheduled Prize Watch supplies one `ENGINE_STATE_JSON` object whenever the jackpot state changes.

## Import

Save the JSON object to a file and run:

```bash
python eurojackpot_jackpot_state_v3_5.py   --db EuroJackpot_Operational_v3_5.sqlite   --json jackpot_state.json
```

Inspect the latest imported state:

```bash
python eurojackpot_jackpot_state_v3_5.py   --db EuroJackpot_Operational_v3_5.sqlite   --latest
```

## What changes

The state machine changes:

- jackpot / prize-class portfolio weights
- anti-crowd weighting
- main-combination diversity
- Euro-pair diversity
- recommended portfolio mode

## What never changes

- main-number inclusion probability remains `5/50 = 10%`
- Euro-number inclusion probability remains `2/12 = 16.6667%`
- no number is promoted because the jackpot rolled over or reached the cap

## Modes

- `NORMAL`
- `ROLLOVER`
- `HIGH_JACKPOT`
- `MAX_CAP`
- `MAX_CAP_OVERFLOW`
- `RESET`

A state marked `VERIFIED` requires at least two sources and both source URLs.
