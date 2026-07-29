"""Core Battleship rules: boards, ships, placement validation and firing."""

from __future__ import annotations

import random
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum

# Half-size ocean (8x7 = 56 cells) so a game finishes in one sitting. Everything
# else derives from these two constants, so widen them for a bigger board.
ROW_LABELS = "ABCDEFGH"
COL_LABELS = [str(n) for n in range(7)]

Coord = str


class Orientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    @property
    def flipped(self) -> Orientation:
        return Orientation.VERTICAL if self is Orientation.HORIZONTAL else Orientation.HORIZONTAL


class Outcome(str, Enum):
    HIT = "hit"
    MISS = "miss"


@dataclass(frozen=True)
class ShipType:
    name: str
    size: int
    emoji: str


FLEET: tuple[ShipType, ...] = (
    ShipType("Carrier", 5, "\U0001f6a2"),
    ShipType("Battleship", 4, "\U0001f6a4"),
    ShipType("Cruiser", 3, "\u26f4"),
    ShipType("Submarine", 3, "\U0001f6e5"),
    ShipType("Destroyer", 2, "\U0001f6f6"),
)

FLEET_BY_NAME = {ship.name: ship for ship in FLEET}


class PlacementError(ValueError):
    """Raised when a requested ship placement breaks the rules."""


def all_coords() -> Iterator[Coord]:
    for row in ROW_LABELS:
        for col in COL_LABELS:
            yield f"{row}{col}"


def parse_coord(coord: Coord) -> tuple[int, int]:
    """Return (row_index, col_index) for a coordinate like 'B2'."""
    cleaned = coord.strip().upper().replace(" ", "")
    if len(cleaned) != 2 or cleaned[0] not in ROW_LABELS or cleaned[1] not in COL_LABELS:
        raise PlacementError(f"'{coord}' is not a coordinate on this board")
    return ROW_LABELS.index(cleaned[0]), COL_LABELS.index(cleaned[1])


def format_coord(row: int, col: int) -> Coord:
    return f"{ROW_LABELS[row]}{COL_LABELS[col]}"


def span(start: Coord, size: int, orientation: Orientation) -> list[Coord]:
    """Cells a ship of ``size`` would occupy starting at ``start``.

    Raises PlacementError if the ship would hang off the grid.
    """
    row, col = parse_coord(start)
    cells: list[Coord] = []
    for step in range(size):
        r = row + (step if orientation is Orientation.VERTICAL else 0)
        c = col + (step if orientation is Orientation.HORIZONTAL else 0)
        if r >= len(ROW_LABELS) or c >= len(COL_LABELS):
            raise PlacementError("Ship would hang off the grid")
        cells.append(format_coord(r, c))
    return cells


@dataclass
class Ship:
    type: ShipType
    cells: list[Coord]
    hits: set[Coord] = field(default_factory=set)

    @property
    def name(self) -> str:
        return self.type.name

    @property
    def sunk(self) -> bool:
        return len(self.hits) == len(self.cells)


@dataclass
class ShotResult:
    coord: Coord
    outcome: Outcome
    ship_name: str | None = None
    sunk: bool = False
    fleet_destroyed: bool = False

    @property
    def hit(self) -> bool:
        return self.outcome is Outcome.HIT


@dataclass
class Board:
    """One player's ocean grid plus the shots that have been fired at it."""

    ships: list[Ship] = field(default_factory=list)
    shots: dict[Coord, Outcome] = field(default_factory=dict)

    @property
    def occupied(self) -> dict[Coord, Ship]:
        return {cell: ship for ship in self.ships for cell in ship.cells}

    @property
    def placed_names(self) -> set[str]:
        return {ship.name for ship in self.ships}

    @property
    def complete(self) -> bool:
        return self.placed_names == {ship.name for ship in FLEET}

    @property
    def all_sunk(self) -> bool:
        return bool(self.ships) and all(ship.sunk for ship in self.ships)

    def can_place(self, ship_type: ShipType, start: Coord, orientation: Orientation) -> list[Coord]:
        if ship_type.name in self.placed_names:
            raise PlacementError(f"{ship_type.name} is already on the board")
        cells = span(start, ship_type.size, orientation)
        taken = self.occupied
        overlap = [cell for cell in cells if cell in taken]
        if overlap:
            raise PlacementError(f"Overlaps {taken[overlap[0]].name} at {overlap[0]}")
        return cells

    def place(self, ship_type: ShipType, start: Coord, orientation: Orientation) -> Ship:
        ship = Ship(ship_type, self.can_place(ship_type, start, orientation))
        self.ships.append(ship)
        return ship

    def remove(self, ship_name: str) -> None:
        self.ships = [ship for ship in self.ships if ship.name != ship_name]

    def clear(self) -> None:
        self.ships = []
        self.shots = {}

    def fire(self, coord: Coord) -> ShotResult:
        row, col = parse_coord(coord)
        target = format_coord(row, col)
        if target in self.shots:
            raise PlacementError(f"{target} has already been fired at")
        ship = self.occupied.get(target)
        if ship is None:
            self.shots[target] = Outcome.MISS
            return ShotResult(target, Outcome.MISS)
        ship.hits.add(target)
        self.shots[target] = Outcome.HIT
        return ShotResult(
            target,
            Outcome.HIT,
            ship_name=ship.name,
            sunk=ship.sunk,
            fleet_destroyed=self.all_sunk,
        )

    def open_cells(self) -> list[Coord]:
        return [coord for coord in all_coords() if coord not in self.shots]

    def sunk_names(self) -> list[str]:
        return [ship.name for ship in self.ships if ship.sunk]


def random_fleet(rng: random.Random | None = None) -> Board:
    """A legal board with all five ships placed at random."""
    rng = rng or random.Random()
    board = Board()
    for ship_type in FLEET:
        while True:
            orientation = rng.choice(list(Orientation))
            start = format_coord(
                rng.randrange(len(ROW_LABELS)),
                rng.randrange(len(COL_LABELS)),
            )
            try:
                board.place(ship_type, start, orientation)
                break
            except PlacementError:
                continue
    return board


def board_from_spec(spec: Iterable[dict]) -> Board:
    """Build a board from ``[{"ship": "Carrier", "start": "B2", "orientation": "horizontal"}]``."""
    board = Board()
    for entry in spec:
        name = str(entry.get("ship", "")).strip().title()
        ship_type = FLEET_BY_NAME.get(name)
        if ship_type is None:
            raise PlacementError(f"Unknown ship '{entry.get('ship')}'")
        orientation_raw = str(entry.get("orientation", "")).strip().lower()
        if orientation_raw not in {o.value for o in Orientation}:
            raise PlacementError(f"Unknown orientation '{entry.get('orientation')}'")
        board.place(ship_type, str(entry.get("start", "")), Orientation(orientation_raw))
    if not board.complete:
        raise PlacementError("Board must contain all five ships")
    return board
