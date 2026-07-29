# Battleship vs. Open(AI)

A retro-CRT Battleship game where you fight OpenAI models on an **A–H × 0–6** grid
(56 cells — half the classic ocean, so a game finishes in one sitting; retune via
`ROW_LABELS` / `COL_LABELS` in `battleship/engine.py`).
Built with Python + Streamlit, deployable to Streamlit Community Cloud.

## Rules implemented
5 ships (Carrier 5, Battleship 4, Cruiser 3, Submarine 3, Destroyer 2), horizontal or
vertical only, no overlaps and no hanging off the grid (touching sides is fine). Boards are
hidden, one shot per turn, hits name the ship, ships are announced when sunk, and the first
side to sink all five wins.

## Screens
1. **Loading** — "Welcome to Battleship! Prepare Yourself for Open(AI) Warfare…" with one
   carrier sailing in per second for 4 seconds.
2. **Start** — the three model opponents with your running win/loss record, plus a popup
   transmission from whichever one you challenge.
3. **Game** — place your fleet (pick a ship → rotate → click a cell) while the model builds
   its own board in a background thread, then trade shots with explosion / water-droplet
   animations until a fleet is destroyed. Win or lose, you get a popup and the result is
   added to your record.

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
streamlit run app.py
```
Tests: `pip install pytest ruff && ruff check . && pytest`

## Deploy to Streamlit Community Cloud
1. Push this repo to GitHub.
2. On https://share.streamlit.io create an app pointing at `app.py`.
3. In **App settings → Secrets** add `OPENAI_API_KEY = "sk-..."`.

Without a key the game still plays — each opponent falls back to a built-in hunt/target
strategy and its configured taunts.

## Configuration
Everything the models say, and which models they are, lives in
[`battleship/config.py`](battleship/config.py): `model`, `persona`, `intro_messages`,
`taunts`, `victory_messages` (snark when you lose) and `defeat_messages`. Lines are sampled
at random, so add as many as you want.

## Layout
| Path | Purpose |
| --- | --- |
| `app.py` | Streamlit screens, session state, turn loop |
| `battleship/engine.py` | Rules: grid, placement validation, firing, sinking |
| `battleship/ai.py` | OpenAI placement + shot selection, hunt/target fallback |
| `battleship/config.py` | Opponents and all configurable messages |
| `battleship/records.py` | Win/loss tally (JSON; ephemeral on Streamlit Cloud) |
| `battleship/ui.py` | CRT theme, grid rendering, hit/miss animations |
