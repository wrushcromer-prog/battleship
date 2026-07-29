"""Retro-with-a-twist styling and small rendering helpers."""

from __future__ import annotations

import streamlit as st

from .engine import COL_LABELS, ROW_LABELS, Board, Outcome

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');

:root {
  --deep: #04121f;
  --sea: #0b3c5d;
  --neon: #33f6ff;
  --neon-dim: #1c8f99;
  --hot: #ff3864;
  --gold: #ffd166;
}

.stApp {
  background:
    radial-gradient(circle at 20% 10%, rgba(51,246,255,.10), transparent 45%),
    radial-gradient(circle at 85% 85%, rgba(255,56,100,.10), transparent 45%),
    linear-gradient(180deg, #04121f 0%, #061c2c 55%, #04121f 100%);
  color: #d7f7ff;
}
.stApp::after {
  content: ""; position: fixed; inset: 0; pointer-events: none; opacity: .35;
  background: repeating-linear-gradient(180deg, rgba(0,0,0,.28) 0 1px, transparent 1px 3px);
}
h1, h2, h3, .retro-font { font-family: 'Press Start 2P', monospace !important; letter-spacing: 1px; }
h1 { color: var(--neon); text-shadow: 0 0 12px rgba(51,246,255,.55), 3px 3px 0 var(--hot); }
.stApp, p, li, label, .stMarkdown { font-family: 'VT323', monospace; font-size: 1.15rem; }

.crt-panel {
  border: 2px solid var(--neon-dim);
  border-radius: 10px;
  background: rgba(4,26,40,.72);
  box-shadow: inset 0 0 24px rgba(51,246,255,.12), 0 0 18px rgba(0,0,0,.6);
  padding: 14px 18px;
  margin-bottom: 14px;
}
.marquee { color: var(--gold); font-family: 'Press Start 2P', monospace; font-size: .8rem; }
.tally { color: var(--neon); font-family: 'Press Start 2P', monospace; font-size: .75rem; }

/* --- grids --- */
.grid-head { font-family: 'Press Start 2P', monospace; font-size: .6rem; color: var(--neon-dim); text-align: center; }
.grid-row-label { font-family: 'Press Start 2P', monospace; font-size: .6rem; color: var(--neon-dim); padding-top: 12px; }

div[data-testid="stHorizontalBlock"] div.stButton > button {
  width: 100%; min-width: 0; padding: 0; height: 34px;
  border: 1px solid rgba(51,246,255,.28);
  border-radius: 4px;
  background: linear-gradient(180deg, #0a3550, #072235);
  color: rgba(215,247,255,.35);
  font-family: 'VT323', monospace; font-size: 1rem;
  transition: transform .08s ease, box-shadow .12s ease;
}
div[data-testid="stHorizontalBlock"] div.stButton > button:hover:not(:disabled) {
  border-color: var(--neon); box-shadow: 0 0 10px rgba(51,246,255,.6); transform: translateY(-1px);
}
div[data-testid="stHorizontalBlock"] div.stButton > button:disabled { opacity: 1; }

.ocean-grid { display: grid; grid-template-columns: 26px repeat(10, 1fr); gap: 3px; }
.ocean-grid .cell {
  height: 34px; border-radius: 4px; display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(51,246,255,.2);
  background: linear-gradient(180deg, #0a3550, #072235);
  font-size: 1rem;
}
.ocean-grid .cell.ship { background: linear-gradient(180deg, #1f5f7a, #123f52); border-color: var(--neon); }
.ocean-grid .cell.hit { background: radial-gradient(circle, #ff8a3d, #a01414); border-color: var(--hot); }
.ocean-grid .cell.miss { background: linear-gradient(180deg, #0e2a3c, #08202e); color: var(--neon); }
.ocean-grid .cell.sunk { filter: grayscale(.4) brightness(.7); }
.ocean-grid .label { font-family: 'Press Start 2P', monospace; font-size: .55rem; color: var(--neon-dim);
  display: flex; align-items: center; justify-content: center; }

@keyframes boom {
  0% { transform: scale(.6); box-shadow: 0 0 0 rgba(255,56,100,.9); }
  40% { transform: scale(1.25); box-shadow: 0 0 26px 8px rgba(255,138,61,.95); }
  100% { transform: scale(1); box-shadow: 0 0 12px rgba(255,56,100,.5); }
}
@keyframes splash {
  0% { transform: scale(.7); box-shadow: 0 0 0 rgba(51,246,255,.9); }
  45% { transform: scale(1.2); box-shadow: 0 0 22px 6px rgba(51,246,255,.8); }
  100% { transform: scale(1); box-shadow: 0 0 8px rgba(51,246,255,.35); }
}
.boom-cell, .splash-cell { animation-duration: .9s; animation-iteration-count: 2; }
.boom-cell { animation-name: boom; }
.splash-cell { animation-name: splash; }

@keyframes sail-in {
  from { transform: translateX(-40px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.convoy-ship { animation: sail-in .7s ease-out both; font-family: 'VT323', monospace; font-size: 1.4rem; color: var(--neon); }
.convoy-ship .hull { font-size: 1.8rem; margin-right: 10px; }

@keyframes blink { 50% { opacity: .25; } }
.blink { animation: blink 1s step-start infinite; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def panel(html: str) -> None:
    st.markdown(f'<div class="crt-panel">{html}</div>', unsafe_allow_html=True)


def animation_css(coord: str | None, hit: bool, prefix: str) -> None:
    """Animate one already-rendered cell (button or div) for the latest shot."""
    if not coord:
        return
    name = "boom" if hit else "splash"
    st.markdown(
        f"""<style>
        .st-key-{prefix}{coord} button, #cell-{prefix}{coord} {{
            animation: {name} .9s ease-out 2;
        }}</style>""",
        unsafe_allow_html=True,
    )


def render_own_board(board: Board, prefix: str = "own") -> str:
    """Static HTML for the player's own ocean grid (ships visible)."""
    occupied = board.occupied
    cells = ['<div class="ocean-grid">', '<div class="label"></div>']
    cells += [f'<div class="label">{c}</div>' for c in COL_LABELS]
    for row in ROW_LABELS:
        cells.append(f'<div class="label">{row}</div>')
        for col in COL_LABELS:
            coord = f"{row}{col}"
            ship = occupied.get(coord)
            outcome = board.shots.get(coord)
            classes = ["cell"]
            glyph = ""
            if outcome is Outcome.HIT:
                classes.append("hit")
                glyph = "\U0001f4a5"
            elif outcome is Outcome.MISS:
                classes.append("miss")
                glyph = "\u25cb"
            elif ship is not None:
                classes.append("ship")
                glyph = ship.type.emoji
            if ship is not None and ship.sunk:
                classes.append("sunk")
            cells.append(
                f'<div id="cell-{prefix}{coord}" class="{" ".join(classes)}">{glyph}</div>'
            )
    cells.append("</div>")
    return "".join(cells)


def fleet_status(board: Board, reveal: bool) -> str:
    rows = []
    for ship in board.ships:
        if ship.sunk:
            rows.append(f"<span style='color:#ff3864'>{ship.type.emoji} {ship.name} \u2014 SUNK</span>")
        elif reveal:
            pegs = "\u25cf" * len(ship.hits) + "\u25cb" * (len(ship.cells) - len(ship.hits))
            rows.append(f"{ship.type.emoji} {ship.name} {pegs}")
        else:
            rows.append(f"{ship.type.emoji} {ship.name} \u2014 afloat")
    return "<br>".join(rows)
