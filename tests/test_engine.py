import random

import pytest

from battleship import ai, engine
from battleship.engine import FLEET_BY_NAME, Board, Orientation, PlacementError


def test_span_horizontal_and_vertical():
    assert engine.span("B2", 3, Orientation.HORIZONTAL) == ["B2", "B3", "B4"]
    assert engine.span("B2", 3, Orientation.VERTICAL) == ["B2", "C2", "D2"]


@pytest.mark.parametrize("start,orientation", [("A8", Orientation.HORIZONTAL), ("J0", Orientation.VERTICAL)])
def test_span_rejects_off_grid(start, orientation):
    with pytest.raises(PlacementError):
        engine.span(start, 5, orientation)


def test_grid_is_a_to_k_and_zero_to_nine():
    assert engine.ROW_LABELS == "ABCDEFGHIJK"
    assert engine.parse_coord("K9") == (10, 9)
    with pytest.raises(PlacementError):
        engine.parse_coord("L3")


def test_no_overlap_but_touching_allowed():
    board = Board()
    board.place(FLEET_BY_NAME["Carrier"], "B2", Orientation.HORIZONTAL)
    with pytest.raises(PlacementError):
        board.place(FLEET_BY_NAME["Cruiser"], "B4", Orientation.HORIZONTAL)
    board.place(FLEET_BY_NAME["Cruiser"], "C2", Orientation.HORIZONTAL)
    assert len(board.ships) == 2


def test_hit_miss_sink_and_win():
    board = Board()
    board.place(FLEET_BY_NAME["Destroyer"], "A0", Orientation.HORIZONTAL)
    assert board.fire("B5").outcome is engine.Outcome.MISS
    first = board.fire("A0")
    assert first.hit and first.ship_name == "Destroyer" and not first.sunk
    second = board.fire("A1")
    assert second.sunk and second.fleet_destroyed
    with pytest.raises(PlacementError):
        board.fire("A1")


def test_random_fleet_is_legal():
    board = engine.random_fleet(random.Random(7))
    assert board.complete
    cells = [cell for ship in board.ships for cell in ship.cells]
    assert len(cells) == len(set(cells)) == 17


def test_board_from_spec_requires_full_fleet():
    with pytest.raises(PlacementError):
        engine.board_from_spec([{"ship": "Carrier", "start": "A0", "orientation": "horizontal"}])


def test_heuristic_targets_adjacent_to_wounded_ship():
    board = Board()
    board.place(FLEET_BY_NAME["Carrier"], "D3", Orientation.HORIZONTAL)
    board.fire("D4")
    assert ai.heuristic_shot(board, random.Random(1)) in {"C4", "E4", "D3", "D5"}
