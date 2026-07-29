"""Battleship vs. Open(AI) \u2014 a retro Streamlit game.

Run locally with: streamlit run app.py
"""

from __future__ import annotations

import random
import threading
import time

import streamlit as st

from battleship import ai, engine, records, ui
from battleship.config import (
    LOADING_GREETING,
    LOADING_SECONDS,
    LOADING_SHIPS,
    OPPONENTS,
    OPPONENTS_BY_KEY,
    PLAYER_WIN_MESSAGES,
    Opponent,
)
from battleship.engine import FLEET, Board, Orientation, PlacementError

st.set_page_config(page_title="Battleship vs Open(AI)", page_icon="\U0001f6a2", layout="wide")
ui.inject_css()


# --------------------------------------------------------------------------- state


def init_state() -> None:
    st.session_state.setdefault("screen", "loading")
    st.session_state.setdefault("opponent_key", None)
    st.session_state.setdefault("intro_shown", False)
    st.session_state.setdefault("game", None)


def new_game(opponent: Opponent) -> dict:
    """Kick off a game: empty player board, AI fleet built in a background thread."""
    llm = ai.LLMOpponent(opponent)
    holder: dict[str, Board | None] = {"board": None}

    def build() -> None:
        holder["board"] = llm.build_board()

    thread = threading.Thread(target=build, daemon=True)
    thread.start()
    return {
        "opponent": opponent.key,
        "llm": llm,
        "player_board": Board(),
        "ai_board": None,
        "ai_board_thread": thread,
        "ai_board_holder": holder,
        "phase": "placement",
        "selected_ship": FLEET[0].name,
        "orientation": Orientation.HORIZONTAL,
        "log": [],
        "last_player_shot": None,
        "last_ai_shot": None,
        "last_taunt": None,
        "winner": None,
        "recorded": False,
    }


def game() -> dict:
    return st.session_state["game"]


def opponent() -> Opponent:
    return OPPONENTS_BY_KEY[game()["opponent"]]


def log(message: str) -> None:
    game()["log"].insert(0, message)


def go_to_start() -> None:
    st.session_state["screen"] = "start"
    st.session_state["game"] = None
    st.session_state["opponent_key"] = None
    st.session_state["intro_shown"] = False


# ------------------------------------------------------------------- screen 1


def screen_loading() -> None:
    st.markdown(f"<h1>{LOADING_GREETING}</h1>", unsafe_allow_html=True)
    ui.panel(
        "<span class='marquee blink'>BOOTING TACTICAL DISPLAY\u2026</span><br>"
        "<span style='color:#8fd9e8'>Calibrating torpedoes \u2022 flooding ballast \u2022 "
        "warming up the language models</span>"
    )
    convoy = st.empty()
    revealed: list[tuple[str, str]] = []
    for index in range(LOADING_SECONDS):
        if index < len(LOADING_SHIPS):
            revealed.append(LOADING_SHIPS[index])
        rows = "".join(
            f"<div class='convoy-ship'><span class='hull'>{emoji}</span>{name}</div>"
            for emoji, name in revealed
        )
        convoy.markdown(f"<div class='crt-panel'>{rows}</div>", unsafe_allow_html=True)
        time.sleep(1)
    st.session_state["screen"] = "start"
    st.rerun()


# ------------------------------------------------------------------- screen 2


@st.dialog("Incoming transmission")
def intro_dialog(chosen: Opponent) -> None:
    st.markdown(
        f"<div class='retro-font' style='font-size:.8rem;color:#ffd166'>{chosen.avatar} "
        f"{chosen.name}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"### \u201c{random.choice(chosen.intro_messages)}\u201d")
    if st.button("Deploy my fleet \u2192", type="primary", use_container_width=True):
        st.session_state["game"] = new_game(chosen)
        st.session_state["screen"] = "game"
        st.rerun()


def screen_start() -> None:
    st.markdown("<h1>\u2620 CHOOSE YOUR OPPONENT</h1>", unsafe_allow_html=True)
    if not ai.api_key():
        st.warning(
            "No `OPENAI_API_KEY` found \u2014 opponents will fall back to a built-in "
            "hunt/target strategy. Add the key to `.streamlit/secrets.toml` or the "
            "environment to face the real models.",
            icon="\u26a0\ufe0f",
        )
    tally = records.load()
    columns = st.columns(len(OPPONENTS))
    for column, candidate in zip(columns, OPPONENTS):
        entry = tally.get(candidate.key, {"wins": 0, "losses": 0})
        with column:
            ui.panel(
                f"<div style='font-size:2.4rem'>{candidate.avatar}</div>"
                f"<div class='retro-font' style='font-size:.75rem;color:#33f6ff'>{candidate.name}</div>"
                f"<div style='color:#8fd9e8'>{candidate.tagline}</div>"
                f"<div style='color:#5f8fa3'>model: <code>{candidate.model}</code></div>"
                f"<div class='tally' style='margin-top:10px'>YOU {entry['wins']} \u2014 "
                f"{entry['losses']} {candidate.name.split()[-1].upper()}</div>"
            )
            if st.button(
                f"Challenge {candidate.name}",
                key=f"pick_{candidate.key}",
                use_container_width=True,
            ):
                st.session_state["opponent_key"] = candidate.key
                st.session_state["intro_shown"] = False
                st.rerun()

    chosen_key = st.session_state.get("opponent_key")
    if chosen_key and not st.session_state["intro_shown"]:
        st.session_state["intro_shown"] = True
        intro_dialog(OPPONENTS_BY_KEY[chosen_key])


# ------------------------------------------------------------------- screen 3


def placement_controls() -> None:
    state = game()
    board: Board = state["player_board"]
    remaining = [ship for ship in FLEET if ship.name not in board.placed_names]
    if state["selected_ship"] not in {s.name for s in remaining} and remaining:
        state["selected_ship"] = remaining[0].name

    ui.panel(
        "<div class='retro-font' style='font-size:.7rem;color:#ffd166'>1. PICK A SHIP &nbsp; "
        "2. ROTATE &nbsp; 3. CLICK THE GRID</div>"
    )
    for ship in FLEET:
        label = f"{ship.emoji} {ship.name} ({ship.size})"
        if ship.name in board.placed_names:
            if st.button(
                f"\u2714 {label} \u2014 pick up",
                key=f"pickup_{ship.name}",
                use_container_width=True,
            ):
                board.remove(ship.name)
                state["selected_ship"] = ship.name
                st.rerun()
        else:
            selected = state["selected_ship"] == ship.name
            marker = "\u25b6 " if selected else ""
            if st.button(
                marker + label,
                key=f"select_{ship.name}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                state["selected_ship"] = ship.name
                st.rerun()

    st.write("")
    if st.button(
        f"Rotate \u2014 {ai.describe_orientation(state['orientation'])}",
        use_container_width=True,
    ):
        state["orientation"] = state["orientation"].flipped
        st.rerun()
    if st.button("Randomise my fleet", use_container_width=True):
        state["player_board"] = engine.random_fleet()
        st.rerun()
    if st.button("Clear board", use_container_width=True):
        board.clear()
        st.rerun()


def resolve_ai_board() -> bool:
    """True once the opponent's fleet is ready."""
    state = game()
    if state["ai_board"] is not None:
        return True
    holder = state["ai_board_holder"]
    if holder["board"] is not None:
        state["ai_board"] = holder["board"]
        return True
    state["ai_board_thread"].join(timeout=30)
    state["ai_board"] = holder["board"] or engine.random_fleet()
    return True


def placement_grid() -> None:
    state = game()
    board: Board = state["player_board"]
    ship = engine.FLEET_BY_NAME[state["selected_ship"]]
    header = st.columns([1] + [2] * len(engine.COL_LABELS))
    header[0].markdown("&nbsp;", unsafe_allow_html=True)
    for column, label in zip(header[1:], engine.COL_LABELS):
        column.markdown(f"<div class='grid-head'>{label}</div>", unsafe_allow_html=True)
    occupied = board.occupied
    for row in engine.ROW_LABELS:
        cells = st.columns([1] + [2] * len(engine.COL_LABELS))
        cells[0].markdown(f"<div class='grid-row-label'>{row}</div>", unsafe_allow_html=True)
        for column, col_label in zip(cells[1:], engine.COL_LABELS):
            coord = f"{row}{col_label}"
            existing = occupied.get(coord)
            with column:
                if st.button(
                    existing.type.emoji if existing else "\u00b7",
                    key=f"place_{coord}",
                    help=coord,
                    use_container_width=True,
                    disabled=board.complete,
                ):
                    try:
                        board.place(ship, coord, state["orientation"])
                    except PlacementError as exc:
                        st.session_state["placement_error"] = str(exc)
                    st.rerun()


def target_grid() -> None:
    state = game()
    ai_board: Board = state["ai_board"]
    playable = state["phase"] == "player_turn"
    header = st.columns([1] + [2] * len(engine.COL_LABELS))
    header[0].markdown("&nbsp;", unsafe_allow_html=True)
    for column, label in zip(header[1:], engine.COL_LABELS):
        column.markdown(f"<div class='grid-head'>{label}</div>", unsafe_allow_html=True)
    for row in engine.ROW_LABELS:
        cells = st.columns([1] + [2] * len(engine.COL_LABELS))
        cells[0].markdown(f"<div class='grid-row-label'>{row}</div>", unsafe_allow_html=True)
        for column, col_label in zip(cells[1:], engine.COL_LABELS):
            coord = f"{row}{col_label}"
            outcome = ai_board.shots.get(coord)
            glyph = "\U0001f4a5" if outcome is engine.Outcome.HIT else (
                "\U0001f4a7" if outcome is engine.Outcome.MISS else "\u00b7"
            )
            with column:
                if st.button(
                    glyph,
                    key=f"fire_{coord}",
                    help=coord,
                    use_container_width=True,
                    disabled=outcome is not None or not playable,
                ):
                    player_fires(coord)


def player_fires(coord: str) -> None:
    state = game()
    result = state["ai_board"].fire(coord)
    state["last_player_shot"] = result
    if result.hit:
        note = f"\U0001f4a5 You hit the {result.ship_name} at {coord}"
        if result.sunk:
            note += " \u2014 SUNK!"
    else:
        note = f"\U0001f4a7 You missed at {coord}"
    log(note)
    if result.fleet_destroyed:
        state["phase"] = "over"
        state["winner"] = "player"
    else:
        state["phase"] = "ai_turn"
    st.rerun()


def ai_fires() -> None:
    state = game()
    shot = state["llm"].next_shot(state["player_board"])
    result = state["player_board"].fire(shot.coord)
    state["last_ai_shot"] = result
    state["last_taunt"] = shot.trash_talk or random.choice(opponent().taunts or ("\u2026",))
    if result.hit:
        note = f"\U0001f4a5 {opponent().name} hit your {result.ship_name} at {shot.coord}"
        if result.sunk:
            note += " \u2014 SUNK!"
    else:
        note = f"\U0001f4a7 {opponent().name} missed at {shot.coord}"
    log(note)
    if result.fleet_destroyed:
        state["phase"] = "over"
        state["winner"] = "ai"
    else:
        state["phase"] = "player_turn"
    st.rerun()


def endgame_body(button_key: str) -> None:
    """The battle report, rendered both in the popup and inline on the page, so
    dismissing the popup can never strand the player on a finished board."""
    state = game()
    foe = opponent()
    won = state["winner"] == "player"
    if not state["recorded"]:
        records.add_result(foe.key, won)
        state["recorded"] = True
        state["headline"] = (
            random.choice(PLAYER_WIN_MESSAGES) if won else random.choice(foe.victory_messages)
        )
        state["sign_off"] = random.choice(foe.defeat_messages) if won else None
    if won:
        st.markdown(f"## \U0001f3c6 {state['headline']}")
        st.markdown(f"\u201c{state['sign_off']}\u201d \u2014 {foe.name}")
    else:
        st.markdown("## \U0001f480 YOUR FLEET IS ON THE SEABED")
        st.markdown(
            f"<div class='crt-panel'>{foe.avatar} <b>{foe.name}</b><br>"
            f"\u201c{state['headline']}\u201d</div>",
            unsafe_allow_html=True,
        )
    entry = records.record_for(foe.key)
    st.markdown(f"**Record vs {foe.name}:** {entry['wins']}W \u2013 {entry['losses']}L")
    if st.button(
        "\u2190 Return to port", key=button_key, type="primary", use_container_width=True
    ):
        go_to_start()
        st.rerun()


@st.dialog("Battle report")
def endgame_dialog() -> None:
    endgame_body("return_to_port_dialog")


def screen_game() -> None:
    state = game()
    foe = opponent()
    board: Board = state["player_board"]
    st.markdown(
        f"<h1>\u2694 YOU vs {foe.name.upper()}</h1>",
        unsafe_allow_html=True,
    )

    if state["phase"] == "placement":
        left, right = st.columns([1, 2])
        with left:
            placement_controls()
            error = st.session_state.pop("placement_error", None)
            if error:
                st.error(error, icon="\u26d3")
            if board.complete:
                with st.spinner(f"{foe.name} is deploying its fleet\u2026"):
                    resolve_ai_board()
                if st.button("\U0001f680 START THE BATTLE", type="primary", use_container_width=True):
                    state["phase"] = "player_turn"
                    log("Battle stations! You fire first.")
                    st.rerun()
        with right:
            st.markdown("#### Your ocean grid")
            placement_grid()
        return

    if state["phase"] == "over":
        endgame_dialog()
        with st.container(border=True):
            endgame_body("return_to_port_inline")

    left, right = st.columns(2)
    with left:
        st.markdown("#### \U0001f3af Target grid \u2014 enemy waters")
        target_grid()
        shot = state["last_player_shot"]
        if shot:
            ui.animation_css(shot.coord, shot.hit, "fire_")
    with right:
        st.markdown("#### \u2693 Your ocean grid")
        st.markdown(ui.render_own_board(board), unsafe_allow_html=True)
        incoming = state["last_ai_shot"]
        if incoming:
            ui.animation_css(incoming.coord, incoming.hit, "own")

    status = st.columns([2, 1])
    with status[0]:
        if state["phase"] == "player_turn":
            ui.panel("<span class='marquee blink'>YOUR TURN \u2014 CALL A SHOT</span>")
        elif state["phase"] == "ai_turn":
            ui.panel(f"<span class='marquee'>{foe.name.upper()} IS PLOTTING\u2026</span>")
        if state["last_taunt"]:
            ui.panel(f"{foe.avatar} <i>\u201c{state['last_taunt']}\u201d</i>")
        st.markdown("##### Battle log")
        st.markdown("<br>".join(state["log"][:12]) or "\u2014", unsafe_allow_html=True)
    with status[1]:
        st.markdown("##### Your fleet")
        st.markdown(ui.fleet_status(board, reveal=True), unsafe_allow_html=True)
        st.markdown("##### Enemy fleet")
        st.markdown(ui.fleet_status(state["ai_board"], reveal=False), unsafe_allow_html=True)
        if state["llm"].last_error:
            st.caption(f"fallback strategy in use: {state['llm'].last_error}")
        if st.button("Abandon ship \u2190", use_container_width=True):
            go_to_start()
            st.rerun()

    if state["phase"] == "ai_turn":
        with st.spinner(f"{foe.name} is taking aim\u2026"):
            ai_fires()


# --------------------------------------------------------------------------- main

init_state()
screen = st.session_state["screen"]
if screen == "loading":
    screen_loading()
elif screen == "start" or st.session_state.get("game") is None:
    screen_start()
else:
    screen_game()
