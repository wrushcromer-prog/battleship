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

st.set_page_config(page_title="AI Battleship", page_icon="\U0001f6a2", layout="wide")
ui.inject_css()


# --------------------------------------------------------------------------- state


def init_state() -> None:
    st.session_state.setdefault("screen", "loading")
    st.session_state.setdefault("convoy_ready", False)
    st.session_state.setdefault("opponent_key", None)
    st.session_state.setdefault("intro_shown", False)
    st.session_state.setdefault("intro_line", "")
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


def convoy_html(revealed: list[tuple[str, str]]) -> str:
    rows = "".join(
        f"<div class='convoy-ship'><span class='hull'>{emoji}</span>{name}</div>"
        for emoji, name in revealed
    )
    return f"<div class='crt-panel'>{rows}</div>"


def screen_loading() -> None:
    """Reveals the convoy one ship per second, then waits for the player to proceed."""
    st.markdown(f"<h1>{LOADING_GREETING}</h1>", unsafe_allow_html=True)
    ready = st.session_state["convoy_ready"]
    headline = "FLEET READY" if ready else "BOOTING TACTICAL DISPLAY\u2026"
    ui.panel(
        f"<span class='marquee{'' if ready else ' blink'}'>{headline}</span><br>"
        "<span class='muted'>Calibrating torpedoes \u2022 flooding ballast \u2022 "
        "warming up the language models</span>"
    )
    if ready:
        st.markdown(convoy_html(list(LOADING_SHIPS)), unsafe_allow_html=True)
        if st.button(
            "PROCEED TO SEE CHALLENGERS \u2192", type="primary", use_container_width=True
        ):
            st.session_state["screen"] = "start"
            st.rerun()
        return

    convoy = st.empty()
    revealed: list[tuple[str, str]] = []
    for index in range(LOADING_SECONDS):
        if index < len(LOADING_SHIPS):
            revealed.append(LOADING_SHIPS[index])
        convoy.markdown(convoy_html(revealed), unsafe_allow_html=True)
        time.sleep(1)
    st.session_state["convoy_ready"] = True
    st.rerun()


# ------------------------------------------------------------------- screen 2


@st.dialog("Incoming transmission")
def intro_dialog(chosen: Opponent) -> None:
    st.markdown(
        f"<div class='retro-font' style='font-size:1rem;color:#ffd166;line-height:1.6'>"
        f"{chosen.avatar} {chosen.name}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"### \u201c{st.session_state['intro_line']}\u201d")
    if st.button("Deploy my fleet \u2192", type="primary", use_container_width=True):
        st.session_state["game"] = new_game(chosen)
        st.session_state["screen"] = "game"
        st.rerun()


@st.dialog("Service record")
def backstory_dialog(chosen: Opponent) -> None:
    st.markdown(
        f"<div class='retro-font' style='font-size:1rem;color:#ffd166;line-height:1.6'>"
        f"{chosen.avatar} {chosen.name}</div>"
        f"<div class='muted'>{chosen.tagline} \u2022 <code>{chosen.model}</code></div>",
        unsafe_allow_html=True,
    )
    for paragraph in chosen.backstory:
        st.markdown(f"<div class='callout' style='margin-top:10px'>{paragraph}</div>",
                    unsafe_allow_html=True)
    st.write("")
    if st.button(
        f"Challenge {chosen.name} \u2192",
        key=f"challenge_from_dossier_{chosen.key}",
        type="primary",
        use_container_width=True,
    ):
        select_opponent(chosen)


def select_opponent(chosen: Opponent) -> None:
    st.session_state["opponent_key"] = chosen.key
    st.session_state["intro_shown"] = False
    # Drawn once here: picking inside the dialog re-rolled the line on every rerun, so
    # clicking "Deploy my fleet" flashed a different greeting for one frame.
    st.session_state["intro_line"] = random.choice(chosen.intro_messages)
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
                "<div class='opp-card'>"
                f"<div style='font-size:2.4rem'>{candidate.avatar}</div>"
                f"<div class='retro-font' style='font-size:1rem;color:#33f6ff;line-height:1.6'>"
                f"{candidate.name}</div>"
                f"<div class='callout' style='margin-top:6px'>{candidate.tagline}</div>"
                f"<div class='muted'>model: <code>{candidate.model}</code></div>"
                f"<div class='tally' style='margin-top:10px'>YOU {entry['wins']} \u2014 "
                f"{entry['losses']} {candidate.short_name}</div></div>"
            )
            if st.button(
                f"\u2694 Challenge {candidate.name}",
                key=f"pick_{candidate.key}",
                type="primary",
                use_container_width=True,
            ):
                select_opponent(candidate)
            if st.button(
                "\U0001f4d6 View backstory",
                key=f"dossier_{candidate.key}",
                use_container_width=True,
            ):
                st.session_state["dossier_key"] = candidate.key
                st.rerun()

    chosen_key = st.session_state.get("opponent_key")
    dossier_key = st.session_state.pop("dossier_key", None)
    if chosen_key and not st.session_state["intro_shown"]:
        st.session_state["intro_shown"] = True
        intro_dialog(OPPONENTS_BY_KEY[chosen_key])
    elif dossier_key:
        backstory_dialog(OPPONENTS_BY_KEY[dossier_key])


# ------------------------------------------------------------------- screen 3


def placement_controls() -> None:
    state = game()
    board: Board = state["player_board"]
    remaining = [ship for ship in FLEET if ship.name not in board.placed_names]
    if state["selected_ship"] not in {s.name for s in remaining} and remaining:
        state["selected_ship"] = remaining[0].name

    horizontal = state["orientation"] is Orientation.HORIZONTAL
    heading = engine.FLEET_BY_NAME[state["selected_ship"]] if remaining else None
    if heading is not None:
        direction = "RIGHT \u2192" if horizontal else "DOWN \u2193"
        ui.panel(
            f"<div class='step'>STEP 1 &nbsp;\u2022&nbsp; PLACE YOUR FLEET "
            f"({len(board.placed_names)} of {len(FLEET)} ships placed)</div>"
            f"<div class='callout' style='margin-top:8px'>Now placing "
            f"<b style='color:#ffd166'>{heading.emoji} {heading.name}</b> — "
            f"{heading.size} cells, running <b style='color:#ffd166'>{direction}</b> "
            f"from the cell you click.</div>"
            "<div class='muted' style='margin-top:6px'>Click any · on the grid to drop it. "
            "Placed a ship badly? Hit <i>Pick up</i> below and click again.</div>"
        )
    else:
        ui.panel(
            "<div class='step'>ALL FIVE SHIPS ARE IN THE WATER \u2014 "
            "<b>ready when you are.</b></div>"
        )

    if heading is not None:
        rotate_label = (
            "\U0001f504 Rotate \u2014 now \u2194 HORIZONTAL, click to go \u2195 VERTICAL"
            if horizontal
            else "\U0001f504 Rotate \u2014 now \u2195 VERTICAL, click to go \u2194 HORIZONTAL"
        )
        if st.button(rotate_label, use_container_width=True, type="primary"):
            state["orientation"] = state["orientation"].flipped
            st.rerun()

    st.markdown("##### Your ships")
    for ship in FLEET:
        label = f"{ship.emoji} {ship.name} \u2014 {ship.size} cells"
        if ship.name in board.placed_names:
            # Keys drive the styling: see the st-key-shipbtn rules in ui.CSS.
            if st.button(
                f"\u2714 {ship.emoji} {ship.name} \u2014 placed \u00b7 pick up",
                key=f"shipbtn_placed_{ship.name}",
                use_container_width=True,
            ):
                board.remove(ship.name)
                state["selected_ship"] = ship.name
                st.rerun()
        elif state["selected_ship"] == ship.name:
            if st.button(
                f"\u25b6 PLACING NOW: {label}",
                key=f"shipbtn_active_{ship.name}",
                use_container_width=True,
            ):
                st.rerun()
        elif st.button(
            f"\u25a1 {label} \u2014 waiting",
            key=f"shipbtn_todo_{ship.name}",
            use_container_width=True,
        ):
            state["selected_ship"] = ship.name
            st.rerun()

    st.write("")
    shortcuts = st.columns(2)
    if shortcuts[0].button("\U0001f3b2 Place them for me", use_container_width=True):
        state["player_board"] = engine.random_fleet()
        st.rerun()
    if shortcuts[1].button("\U0001f9f9 Clear the board", use_container_width=True):
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
    occupied = board.occupied
    with st.container(key="gridwrap_place"):
        header = st.columns([1] + [2] * len(engine.COL_LABELS))
        header[0].markdown("&nbsp;", unsafe_allow_html=True)
        for column, label in zip(header[1:], engine.COL_LABELS):
            column.markdown(f"<div class='grid-head'>{label}</div>", unsafe_allow_html=True)
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
                        help=(
                            f"{coord} \u2014 {existing.name}"
                            if existing
                            else f"Put the {ship.name} here ({coord})"
                        ),
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
    # The key lets ui.CSS tighten the row gap so this grid lines up with the ocean grid.
    with st.container(key="gridwrap_target"):
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
                        help=(
                            f"Fire at {coord}"
                            if outcome is None
                            else f"{coord} \u2014 already fired"
                        ),
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
            error = st.session_state.pop("placement_error", None)
            if error:
                # Above the controls, otherwise it lands below the fold.
                st.error(f"{error}. Pick a different cell, or rotate the ship.", icon="\u26d3")
            placement_controls()
            if board.complete:
                with st.spinner(f"{foe.name} is deploying its fleet\u2026"):
                    resolve_ai_board()
                if st.button(
                    "\U0001f680 START THE BATTLE", type="primary", use_container_width=True
                ):
                    state["phase"] = "player_turn"
                    log("Battle stations! You fire first.")
                    st.rerun()
        with right:
            st.markdown("#### \u2693 Your ocean \u2014 click a cell to place the selected ship")
            placement_grid()
            ui.panel(
                "<span class='muted'>\u00b7 open water &nbsp;\u2022&nbsp; "
                "emoji = one of your ships &nbsp;\u2022&nbsp; the enemy never sees this grid, "
                "and ships may touch but never overlap.</span>"
            )
        return

    if state["phase"] == "over":
        endgame_dialog()
        with st.container(border=True):
            endgame_body("return_to_port_inline")

    # Kept at the top of the page: the AI's spinner used to sit under both grids, where a
    # multi-second turn looked like the app had frozen. The slot keeps a fixed height so
    # swapping "your turn" for the plotting spinner never shifts the grids below it.
    with st.container(key="turnslot"):
        turn_banner = st.empty()
    taunt = state["last_taunt"] or "&nbsp;"
    if state["phase"] == "player_turn":
        with turn_banner.container():
            ui.panel(
                "<span class='marquee blink'>YOUR TURN \u2014 CALL A SHOT</span>"
                f"<div class='callout banner-line'>{foe.avatar} <i>\u201c{taunt}\u201d</i></div>"
            )

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

    fleets, journal = st.columns([1, 1])
    with fleets:
        st.markdown("##### \U0001f6a9 Fleet status")
        st.markdown(
            "<div class='fleet-pair'>"
            f"<div><div class='fleet-title'>Yours</div>{ui.fleet_status(board, reveal=True)}</div>"
            f"<div><div class='fleet-title'>{foe.short_name}</div>"
            f"{ui.fleet_status(state['ai_board'], reveal=False)}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with journal:
        st.markdown("##### \U0001f4dc Battle log")
        st.markdown(
            "<div class='battle-log'>"
            + ("<br>".join(state["log"][:10]) or "\u2014")
            + "</div>",
            unsafe_allow_html=True,
        )

    footer = st.columns([1, 3])
    with footer[0]:
        if st.button("Abandon ship \u2190", use_container_width=True):
            go_to_start()
            st.rerun()
    with footer[1]:
        if state["llm"].last_error:
            st.caption(f"fallback strategy in use: {state['llm'].last_error}")

    if state["phase"] == "ai_turn":
        # Same two-line panel as the player's turn rather than st.spinner, whose own
        # element has a different height and shoved the grids down mid-turn.
        with turn_banner.container():
            ui.panel(
                f"<span class='marquee blink'>{foe.avatar} {foe.name.upper()} "
                "IS PLOTTING</span>"
                "<div class='callout banner-line'>taking aim\u2026</div>"
            )
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
