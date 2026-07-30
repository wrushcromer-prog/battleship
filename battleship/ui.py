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
/* Press Start 2P is unreadable below ~1rem, so it is reserved for the big headings. */
h1, .retro-font { font-family: 'Press Start 2P', monospace !important; letter-spacing: 1px; line-height: 1.5; }
h1 { color: var(--neon); font-size: 1.7rem !important; text-shadow: 0 0 12px rgba(51,246,255,.55), 3px 3px 0 var(--hot); }
h2, h3, h4, h5 { font-family: 'VT323', monospace !important; color: var(--neon); letter-spacing: .5px; }
h3 { font-size: 1.9rem !important; }
h4, h5 { font-size: 1.5rem !important; }
.stApp, p, li, label, .stMarkdown, .stAlert { font-family: 'VT323', monospace; font-size: 1.25rem; }
.stApp p, .stMarkdown p, .stMarkdown li { color: #e4fbff; }
.stApp code { font-size: 1.05rem; color: var(--gold); background: rgba(51,246,255,.10); }
/* Dialogs default to small text on this theme. */
div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 { font-size: 1.9rem !important; }
div[data-testid="stDialog"] p, div[data-testid="stDialog"] li { font-size: 1.35rem; color: #eaffff; }
div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] { gap: .6rem; }
.stAlert p { font-size: 1.25rem; color: #04121f; }

.crt-panel {
  border: 2px solid var(--neon-dim);
  border-radius: 10px;
  background: rgba(4,26,40,.72);
  box-shadow: inset 0 0 24px rgba(51,246,255,.12), 0 0 18px rgba(0,0,0,.6);
  padding: 14px 18px;
  margin-bottom: 14px;
}
/* Keeps the three opponent cards, and so their buttons, the same height. */
.opp-card { min-height: 168px; }
.marquee { color: var(--gold); font-family: 'Press Start 2P', monospace; font-size: 1rem; line-height: 1.6; }
.tally { color: var(--gold); font-family: 'Press Start 2P', monospace; font-size: .95rem; }
.callout { color: #eaffff; font-size: 1.3rem; }
.muted { color: #a9d6e6; font-size: 1.15rem; }
.step { color: var(--gold); font-size: 1.35rem; }
.step b { color: #fff; }

/* --- buttons --- */
.stButton > button, .stFormSubmitButton > button {
  font-family: 'VT323', monospace; font-size: 1.3rem; letter-spacing: .5px;
  color: #eaffff; border: 2px solid var(--neon-dim);
  background: linear-gradient(180deg, #10496b, #0a2c42);
}
/* Streamlit wraps button labels in <p>, which carries its own tiny font-size. */
.stButton > button p, .stFormSubmitButton > button p {
  font-family: 'VT323', monospace !important; font-size: 1.3rem !important;
  line-height: 1.3; margin: 0; color: inherit;
}
.stButton > button:hover { color: #fff; border-color: var(--neon); box-shadow: 0 0 12px rgba(51,246,255,.5); }
.stButton > button[kind="primary"] {
  color: #fff; border-color: var(--hot);
  background: linear-gradient(180deg, #ff4f76, #c2143c);
  text-shadow: 0 1px 0 rgba(0,0,0,.45);
}

/* --- grids --- */
.grid-head, .grid-row-label { font-family: 'Press Start 2P', monospace; font-size: .95rem; color: var(--neon); }
.grid-head { text-align: center; }
.grid-row-label { padding-top: 10px; text-align: center; }

/* Streamlit's 1rem stack gap between rows made the button grid far taller than the CSS
   ocean grid; both now use a 40px cell on a 4px gap so the two boards line up exactly. */
div[class*="st-key-gridwrap_"],
div[class*="st-key-gridwrap_"] div[data-testid="stVerticalBlock"],
div[class*="st-key-gridwrap_"] div[data-testid="stHorizontalBlock"] { gap: 4px !important; }

/* Only the 1-cell grid buttons get the compact treatment. */
div[class*="st-key-fire_"] .stButton > button p,
div[class*="st-key-place_"] .stButton > button p { font-size: 1.15rem !important; }
div[class*="st-key-fire_"] .stButton > button,
div[class*="st-key-place_"] .stButton > button {
  width: 100%; min-width: 0; padding: 0; height: 40px;
  border: 1px solid rgba(51,246,255,.30);
  border-radius: 4px;
  background: linear-gradient(180deg, #0a3550, #072235);
  color: rgba(215,247,255,.45);
  font-size: 1.1rem;
  transition: transform .08s ease, box-shadow .12s ease;
}
div[class*="st-key-fire_"] .stButton > button:hover:not(:disabled),
div[class*="st-key-place_"] .stButton > button:hover:not(:disabled) {
  border-color: var(--neon); box-shadow: 0 0 10px rgba(51,246,255,.6); transform: translateY(-1px);
}
div[class*="st-key-fire_"] .stButton > button:disabled,
div[class*="st-key-place_"] .stButton > button:disabled { opacity: 1; }

/* 3px offsets the column-label row so it sits level with the button grid's labels. */
.ocean-grid { display: grid; grid-template-columns: 30px repeat(var(--cols), 1fr); gap: 4px; margin-top: 3px; }
.ocean-grid .cell {
  height: 40px; border-radius: 4px; display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(51,246,255,.2);
  background: linear-gradient(180deg, #0a3550, #072235);
  font-size: 1rem;
}
.ocean-grid .cell.ship { background: linear-gradient(180deg, #1f5f7a, #123f52); border-color: var(--neon); }
.ocean-grid .cell.hit { background: radial-gradient(circle, #ff8a3d, #a01414); border-color: var(--hot); }
.ocean-grid .cell.miss { background: linear-gradient(180deg, #0e2a3c, #08202e); color: var(--neon); }
.ocean-grid .cell.sunk { filter: grayscale(.4) brightness(.7); }
.ocean-grid .label { font-family: 'Press Start 2P', monospace; font-size: .9rem; color: var(--neon);
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

/* Game page footer: the two fleets sit side by side so they fill the row instead of
   stacking into a tall, half-empty column. */
.fleet-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.fleet-title { font-family: 'Press Start 2P', monospace; font-size: .8rem; color: var(--gold); margin-bottom: 6px; }
/* Reserved slot for the turn banner: its content swaps between "your turn" and the
   opponent's plotting notice, and without a fixed height the grids jumped every shot. */
div[class*="st-key-turnslot"] { min-height: 96px; }
.banner-line { margin-top: 6px; min-height: 1.5em; }
.size-pips { color: var(--gold); letter-spacing: 2px; }
.pip-count { color: #8fb6c6; }
.battle-log { font-family: 'VT323', monospace; font-size: 1.2rem; color: #d7f7ff; line-height: 1.5; }

/* Fleet roster: the ship being placed pulses, placed ships fade out of the way. */
@keyframes ship-pulse {
  0%, 100% { box-shadow: 0 0 6px rgba(255,209,102,.45); border-color: var(--gold); }
  50% { box-shadow: 0 0 18px 3px rgba(255,209,102,.95); border-color: #fff2c6; }
}
div[class*="st-key-shipbtn_active_"] .stButton > button {
  border: 2px solid var(--gold);
  background: linear-gradient(180deg, #3a2f10, #21180a);
  animation: ship-pulse 1.1s ease-in-out infinite;
}
div[class*="st-key-shipbtn_active_"] .stButton > button p {
  color: var(--gold) !important;
  font-weight: 700;
}
div[class*="st-key-shipbtn_placed_"] .stButton > button {
  border: 1px dashed rgba(140,170,185,.45);
  background: rgba(255,255,255,.03);
}
div[class*="st-key-shipbtn_placed_"] .stButton > button p {
  color: #7f9dab !important;
  text-decoration: line-through;
  text-decoration-color: rgba(127,157,171,.6);
}
div[class*="st-key-shipbtn_placed_"] .stButton > button:hover p {
  color: #d6f4ff !important;
  text-decoration: none;
}
div[class*="st-key-shipbtn_todo_"] .stButton > button p { color: #eaffff !important; }

/* Phones only. Streamlit collapses st.columns into a vertical stack below its own
   breakpoint, which turned each rank of the boards into seven full-width buttons, so the
   grids are pinned back into rows here and the cells shrunk to fit seven across. */
@media (max-width: 640px) {
  div[class*="st-key-gridwrap_"] div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 2px !important;
  }
  div[class*="st-key-gridwrap_"] div[data-testid="stColumn"] {
    min-width: 0 !important;
    flex: 1 1 0 !important;
  }
  div[class*="st-key-fire_"] .stButton > button,
  div[class*="st-key-place_"] .stButton > button {
    height: 34px;
    font-size: .85rem;
  }
  .ocean-grid { grid-template-columns: 18px repeat(var(--cols), 1fr); gap: 2px; }
  .ocean-grid .cell { height: 34px; font-size: .85rem; }
  .grid-head, .grid-row-label { font-size: .9rem; }
  /* Both fleets side by side is unreadable at this width. */
  .fleet-pair { grid-template-columns: 1fr; }
  /* Taunts wrap to an unpredictable number of lines at this width, which would move the
     boards even with a reserved slot, so the line is clamped to a fixed two. */
  div[class*="st-key-turnslot"] { min-height: 152px; }
  .banner-line {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.45;
    height: 3.8rem;
  }
  h1 { font-size: 1.05rem !important; }
  .marquee { font-size: .8rem; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f"<style>:root {{ --cols: {len(COL_LABELS)}; }}</style>",
        unsafe_allow_html=True,
    )


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
        size = len(ship.cells)
        if ship.sunk:
            rows.append(
                f"<span style='color:#ff3864'>{ship.type.emoji} {ship.name} \u2014 SUNK "
                f"({size} cells)</span>"
            )
        elif reveal:
            pegs = "\u25cf" * len(ship.hits) + "\u25cb" * (size - len(ship.hits))
            rows.append(f"{ship.type.emoji} {ship.name} {pegs}")
        else:
            # Hidden fleet: the pips give away a ship's size but never how badly it is hit.
            pips = "\u25aa" * size
            rows.append(
                f"{ship.type.emoji} {ship.name} <span class='size-pips'>{pips}</span> "
                f"<span class='pip-count'>{size} cells</span>"
            )
    return "<br>".join(rows)
