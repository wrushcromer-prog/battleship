"""The OpenAI-powered opponent: fleet placement and shot selection.

Every LLM response is validated against the rules. If the model is unreachable or
returns something illegal we fall back to a classic hunt/target heuristic so the
game never stalls.
"""

from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass

from openai import OpenAI

from . import engine
from .config import Opponent
from .engine import Board, Coord, Orientation, Outcome

PLACEMENT_SYSTEM = """You are {persona} playing Battleship on a {grid} grid.
Rows are letters {rows}, columns are digits {cols}, so a cell looks like "B2" or "{last}".
Place all five ships: Carrier (5), Battleship (4), Cruiser (3), Submarine (3), Destroyer (2).
Ships are horizontal (start cell, then increasing column) or vertical (start cell, then
increasing row). They may not overlap or hang off the grid. Spread them out unpredictably.
Reply with JSON only: {{"ships": [{{"ship": "Carrier", "start": "B2", "orientation": "horizontal"}}, ...]}}"""

SHOT_SYSTEM = """You are {persona} playing Battleship on a {grid} grid (rows {rows}, columns {cols}).
Pick your next shot at the human's fleet. Play well: after a hit, probe the cells adjacent to
unsunk hits; otherwise spread shots out. Never repeat a coordinate you have already fired at.
Stay in character in trash_talk: one short line of your own, never the example text.
Keep trash_talk under {taunt_limit} characters so it fits the display.
Reply with JSON only: {{"shot": "B2", "trash_talk": "..."}}"""

# The turn banner reserves three rows at phone width; the hand-written taunts all fit inside
# this, so it doubles as the ceiling for model-written ones.
TAUNT_LIMIT = 90


def grid_facts() -> dict[str, str]:
    """Grid dimensions described for the prompts, derived from the engine constants."""
    rows, cols = engine.ROW_LABELS, engine.COL_LABELS
    return {
        "grid": f"{len(rows)}x{len(cols)}",
        "rows": f"{rows[0]}-{rows[-1]}",
        "cols": f"{cols[0]}-{cols[-1]}",
        "last": f"{rows[-1]}{cols[-1]}",
    }


# o-series and gpt-5+ think before answering, which costs seconds per turn.
REASONING_MODELS = re.compile(r"^(o\d|gpt-[5-9])")


def api_key() -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:  # Streamlit Community Cloud stores it in secrets
        import streamlit as st

        return st.secrets.get("OPENAI_API_KEY")  # type: ignore[no-any-return]
    except Exception:
        return None


@dataclass
class Shot:
    coord: Coord
    trash_talk: str | None = None
    from_model: bool = True


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in model response")
    return json.loads(match.group(0))


def heuristic_shot(board: Board, rng: random.Random | None = None) -> Coord:
    """Hunt/target fallback: finish wounded ships, otherwise fire on a parity grid."""
    rng = rng or random.Random()
    wounded = [
        cell
        for ship in board.ships
        if not ship.sunk
        for cell in ship.hits
    ]
    neighbours: list[Coord] = []
    for cell in wounded:
        row, col = engine.parse_coord(cell)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r, c = row + dr, col + dc
            if 0 <= r < len(engine.ROW_LABELS) and 0 <= c < len(engine.COL_LABELS):
                candidate = engine.format_coord(r, c)
                if candidate not in board.shots:
                    neighbours.append(candidate)
    if neighbours:
        return rng.choice(neighbours)
    open_cells = board.open_cells()
    parity = [
        coord
        for coord in open_cells
        if sum(engine.parse_coord(coord)) % 2 == 0
    ]
    return rng.choice(parity or open_cells)


class LLMOpponent:
    """Wraps one configured model. All methods degrade gracefully without an API key."""

    def __init__(self, opponent: Opponent, key: str | None = None, timeout: float = 25.0):
        self.opponent = opponent
        self._key = key or api_key()
        self._client = OpenAI(api_key=self._key, timeout=timeout) if self._key else None
        self.last_error: str | None = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def _tuning(self) -> dict[str, str]:
        """Reasoning models burn a few seconds of hidden thinking on every turn.

        Battleship on a 8x7 grid does not need it, so the effort is dialled down to keep
        turns snappy. Set ``reasoning_effort`` in an opponent's ``extras`` to override.
        """
        effort = self.opponent.extras.get("reasoning_effort")
        if effort is None and REASONING_MODELS.match(self.opponent.model):
            effort = "low"
        return {"reasoning_effort": effort} if effort else {}

    def _chat(self, system: str, user: str) -> dict:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        response = self._client.chat.completions.create(
            model=self.opponent.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            **self._tuning(),
        )
        return _extract_json(response.choices[0].message.content or "")

    def build_board(self, attempts: int = 3) -> Board:
        """Ask the model for a fleet, retrying illegal layouts before going random.

        Smaller models emit illegal fleets fairly often, so each retry feeds the
        rejection reason back to them.
        """
        note = ""
        for _ in range(attempts):
            try:
                payload = self._chat(
                    PLACEMENT_SYSTEM.format(persona=self.opponent.persona, **grid_facts()),
                    "Deploy your fleet for a new game." + note,
                )
                board = engine.board_from_spec(payload["ships"])
                self.last_error = None
                return board
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                note = (
                    f"\nYour previous layout was rejected: {exc}. Recheck every ship "
                    "against the grid bounds and against the other ships."
                )
        return engine.random_fleet()

    def next_shot(self, player_board: Board) -> Shot:
        """Choose a shot at ``player_board`` (the human's ocean grid)."""
        fallback = heuristic_shot(player_board)
        try:
            payload = self._chat(
                SHOT_SYSTEM.format(
                    persona=self.opponent.persona,
                    taunt_limit=TAUNT_LIMIT,
                    **grid_facts(),
                ),
                self._shot_prompt(player_board),
            )
            coord = str(payload["shot"]).strip().upper()
            engine.parse_coord(coord)
            if coord in player_board.shots:
                raise ValueError(f"{coord} already fired at")
            self.last_error = None
            return Shot(coord, self._clean_talk(payload.get("trash_talk")))
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return Shot(fallback, random.choice(self.opponent.taunts or ("...",)), from_model=False)

    def _clean_talk(self, talk: object) -> str | None:
        """Weaker models echo the prompt's placeholder instead of writing their own line."""
        text = str(talk).strip() if talk else ""
        if text.strip(".").lower() in {"", "one short taunt", "trash_talk", "taunt"}:
            return random.choice(self.opponent.taunts) if self.opponent.taunts else None
        # The banner reserves a fixed number of rows, so an over-long line would be clipped
        # mid-word; a written-in-character taunt reads better than a truncated one.
        if len(text) > TAUNT_LIMIT and self.opponent.taunts:
            return random.choice(self.opponent.taunts)
        return text

    def _shot_prompt(self, player_board: Board) -> str:
        hits = sorted(c for c, o in player_board.shots.items() if o is Outcome.HIT)
        misses = sorted(c for c, o in player_board.shots.items() if o is Outcome.MISS)
        sunk = player_board.sunk_names()
        unsunk_hits = sorted(
            cell for ship in player_board.ships if not ship.sunk for cell in ship.hits
        )
        return json.dumps(
            {
                "your_hits": hits,
                "your_misses": misses,
                "enemy_ships_you_sank": sunk,
                "hits_on_ships_still_afloat": unsunk_hits,
                "remaining_enemy_ships": [
                    {"ship": s.type.name, "size": s.type.size}
                    for s in player_board.ships
                    if not s.sunk
                ],
            },
            indent=2,
        )


def describe_orientation(orientation: Orientation) -> str:
    return "\u2194 horizontal" if orientation is Orientation.HORIZONTAL else "\u2195 vertical"
