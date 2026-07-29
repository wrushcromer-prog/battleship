---
name: testing-battleship
description: How to run and end-to-end test the Streamlit Battleship-vs-OpenAI app locally, including how to finish a full game quickly and what the "fallback strategy in use" caption means.
---

# Testing the Battleship Streamlit app

## Run it
```bash
cd <repo> && .venv/bin/streamlit run app.py --server.port 8501 --server.headless true > /tmp/st.log 2>&1 &
```
Deps live in `.venv` (`pip install -r requirements.txt` if missing). Open http://localhost:8501.
Only one process can hold port 8501 — check `pgrep -f "streamlit run"` before starting; another agent may already have it running.

## Devin Secrets Needed
- `OPENAI_API_KEY` — without it the opponent screen shows a warning banner and all opponents use the local hunt/target heuristic, so LLM behaviour cannot be tested.

## Records / tally
`data/records.json` (per-opponent `wins`/`losses`), overridable with `BATTLESHIP_RECORD_PATH`. Delete or point elsewhere to test the 0—0 starting state. It is written only when the endgame dialog first renders.

## Reaching the interesting states fast
- Screen 1 auto-advances after ~4s; screenshot at ~2s to prove carriers reveal one per second.
- Placement: off-grid error = pick a start where the ship overruns (e.g. Carrier horizontal at A7); overlap error = place a second ship on an occupied cell. `START THE BATTLE` only renders when all 5 ships are placed; grid buttons become `disabled` once the board is complete, so use "pick up" to change ships.
- To finish a real game you need the AI's board. A temporary debug dump is the cheapest route: in `screen_game()` write `state["ai_board"].ships` cells to a file, read it with the shell, then revert the edit. Note the early `return True` inside `resolve_ai_board()` means a dump placed after the `thread.join()` line often never runs — put it in `screen_game()` instead.
- To test the loss path, place your fleet as a dense block (e.g. Carrier A0, Battleship B0, Cruiser C0, Submarine D0, Destroyer E0) and fire only at columns you know are empty from the dump; a competent model sinks 17 cells in ~20 turns.
- Each shot triggers a real OpenAI call; allow ~6-9s per turn and re-scroll to the top before each grid click because reruns move the page.

## Known/likely issues to watch for
- The `fallback strategy in use: ...` caption means an OpenAI response was rejected. `gpt-4o-mini` and `gpt-4.1-mini` frequently return illegal fleets ("Ship would hang off the grid" / "Overlaps ..."), and `LLMOpponent.last_error` is never cleared, so the caption sticks for the rest of the game even if later calls succeed. `gpt-4o` was reliable. Retrying the placement call and clearing `last_error` on success would be the fixes to look for.
- `already fired at` in that caption is the repeat-coordinate guard working, not a rules violation.
- The endgame "Battle report" dialog is dismissible by clicking outside it and will not reappear until the next rerun (pressing `R` re-renders it). Avoid extra clicks right after the final hit, or you will lose the win/loss popup evidence.
