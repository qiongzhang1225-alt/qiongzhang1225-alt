#!/usr/bin/env python3
"""Quick local test for Gomoku game logic. Run: python test_game.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from process_move import (
    BLACK, WHITE, BOARD_SIZE,
    check_win, make_move, new_game, parse_move, render_board_html, render_status,
)


def test_parse():
    assert parse_move("gomoku|5|5") == (5, 5)
    assert parse_move("gomoku|0|10") == (0, 10)
    assert parse_move(" Gomoku | 3 | 4 ") == (3, 4)
    assert parse_move("not a move") is None
    assert parse_move("gomoku|abc|5") is None
    print("OK parse_move")


def test_win_horizontal():
    state = new_game()
    for c in range(5):
        state, msg, ok = make_move(state, 5, c, "tester") if c % 2 == 0 else make_move(state, 5, c, "tester")
        # alternates: B at (5,0), W at (5,1)... that won't form a black row
    # Manual setup:
    state = new_game()
    state["board"][3][0] = BLACK
    state["board"][3][1] = BLACK
    state["board"][3][2] = BLACK
    state["board"][3][3] = BLACK
    win = check_win(state["board"], 3, 3, BLACK)
    assert not win, "Only 4 in a row, should not win"
    state["board"][3][4] = BLACK
    win = check_win(state["board"], 3, 4, BLACK)
    assert len(win) == 5, f"Expected 5-in-a-row, got {win}"
    print("OK horizontal win")


def test_win_diagonal():
    state = new_game()
    for i in range(5):
        state["board"][i][i] = WHITE
    win = check_win(state["board"], 4, 4, WHITE)
    assert len(win) == 5, f"Expected diagonal win, got {win}"

    state = new_game()
    for i in range(5):
        state["board"][i][4 - i] = BLACK
    win = check_win(state["board"], 4, 0, BLACK)
    assert len(win) == 5, f"Expected anti-diagonal win, got {win}"
    print("OK diagonal wins")


def test_turn_alternation():
    state = new_game()
    assert state["current_player"] == BLACK
    state, _, ok = make_move(state, 5, 5, "alice")
    assert ok
    assert state["current_player"] == WHITE
    state, _, ok = make_move(state, 5, 6, "bob")
    assert ok
    assert state["current_player"] == BLACK
    print("OK turn alternation")


def test_occupied_cell():
    state = new_game()
    state, _, ok = make_move(state, 5, 5, "alice")
    assert ok
    state, msg, ok = make_move(state, 5, 5, "bob")
    assert not ok
    assert "已经有棋子" in msg
    print("OK occupied cell rejected")


def test_out_of_bounds():
    state = new_game()
    state, msg, ok = make_move(state, -1, 5, "alice")
    assert not ok
    state, msg, ok = make_move(state, 5, BOARD_SIZE, "alice")
    assert not ok
    print("OK out-of-bounds rejected")


def test_full_game_then_new():
    state = new_game()
    # Black wins quickly with 5 in a column
    moves = [
        (0, 0, "alice"),  # B
        (0, 1, "bob"),    # W
        (1, 0, "alice"),  # B
        (1, 1, "bob"),    # W
        (2, 0, "alice"),  # B
        (2, 1, "bob"),    # W
        (3, 0, "alice"),  # B
        (3, 1, "bob"),    # W
        (4, 0, "alice"),  # B — wins!
    ]
    for r, c, who in moves:
        state, msg, ok = make_move(state, r, c, who)
        assert ok, msg
    assert state["winner"] == BLACK
    assert state["game_id"] == 1
    # Next move starts new game
    state, msg, ok = make_move(state, 5, 5, "charlie")
    assert ok
    assert state["game_id"] == 2
    assert state["winner"] == 0
    assert state["move_count"] == 1
    print("OK win detection + auto-restart")


def test_render():
    state = new_game()
    state["board"][5][5] = BLACK
    state["last_move"] = {"row": 5, "col": 5, "player": BLACK, "by": "alice", "at": "2026-01-01"}
    html = render_board_html(state, "user/repo")
    assert "<table" in html
    assert "🔴" in html or "⚫" in html  # last move highlighted as red
    status = render_status(state)
    assert "进行中" in status or "黑棋" in status
    print("OK rendering")


if __name__ == "__main__":
    test_parse()
    test_win_horizontal()
    test_win_diagonal()
    test_turn_alternation()
    test_occupied_cell()
    test_out_of_bounds()
    test_full_game_then_new()
    test_render()
    print("\nAll tests passed!")
