#!/usr/bin/env python3
"""
Process a Gomoku move from a GitHub issue title.
Updates board state, checks for win, and regenerates the README board section.

Usage:
    python process_move.py "<issue_title>" "<player_login>" [--repo OWNER/REPO]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

# Force UTF-8 stdout so emoji prints don't crash on Windows (GBK) locales.
# GitHub Actions Linux runners default to UTF-8 already.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BOARD_SIZE = 11
WIN_LENGTH = 5

ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = ROOT / "gomoku" / "board.json"
HISTORY_FILE = ROOT / "gomoku" / "history.json"
README_FILE = ROOT / "README.md"

BOARD_START = "<!-- GOMOKU_BOARD_START -->"
BOARD_END = "<!-- GOMOKU_BOARD_END -->"
STATUS_START = "<!-- GOMOKU_STATUS_START -->"
STATUS_END = "<!-- GOMOKU_STATUS_END -->"

EMPTY, BLACK, WHITE = 0, 1, 2
STONE_LABEL = {BLACK: "⚫ 黑棋", WHITE: "⚪ 白棋"}


def new_game(game_id: int = 1) -> dict:
    return {
        "board": [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)],
        "current_player": BLACK,
        "move_count": 0,
        "last_move": None,
        "winner": 0,
        "winning_line": [],
        "game_id": game_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ended_at": None,
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        with STATE_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    return new_game()


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def append_history(record: dict) -> None:
    history = []
    if HISTORY_FILE.exists():
        try:
            with HISTORY_FILE.open(encoding="utf-8") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []
    history.append(record)
    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(history[-500:], f, indent=2, ensure_ascii=False)


def parse_move(title: str) -> tuple[int, int] | None:
    match = re.match(r"^\s*gomoku\s*\|\s*(\d+)\s*\|\s*(\d+)\s*$", title, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def check_win(board: list[list[int]], row: int, col: int, player: int) -> list[tuple[int, int]]:
    """Return the winning line (list of coords) if `player` just won at (row,col), else []."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        line = [(row, col)]
        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                line.append((r, c))
                r += sign * dr
                c += sign * dc
        if len(line) >= WIN_LENGTH:
            return sorted(line)
    return []


def make_move(state: dict, row: int, col: int, player_login: str) -> tuple[dict, str, bool]:
    """Returns (new_state, message, success)."""
    if state["winner"] != 0:
        state = new_game(game_id=state.get("game_id", 1) + 1)

    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return state, f"❌ 坐标越界 ({row},{col})。棋盘范围 0–{BOARD_SIZE - 1}。", False

    if state["board"][row][col] != EMPTY:
        return state, f"❌ 位置 ({row},{col}) 已经有棋子了，请选另一个空位。", False

    player = state["current_player"]
    state["board"][row][col] = player
    state["move_count"] += 1
    state["last_move"] = {
        "row": row,
        "col": col,
        "player": player,
        "by": player_login,
        "at": datetime.now(timezone.utc).isoformat(),
    }

    winning_line = check_win(state["board"], row, col, player)
    msg_lines = [
        f"✅ @{player_login} 落下 {STONE_LABEL[player]} 于 ({row},{col})！",
    ]

    if winning_line:
        state["winner"] = player
        state["winning_line"] = winning_line
        state["ended_at"] = datetime.now(timezone.utc).isoformat()
        msg_lines.append(f"🎉 **{STONE_LABEL[player]} 获胜！** 连成五子：{winning_line}")
        msg_lines.append("下一手将自动开启新一局。")
    elif state["move_count"] >= BOARD_SIZE * BOARD_SIZE:
        state["winner"] = 3  # draw
        state["ended_at"] = datetime.now(timezone.utc).isoformat()
        msg_lines.append("🤝 棋盘已满，本局平局！下一手将自动开启新一局。")
    else:
        state["current_player"] = WHITE if player == BLACK else BLACK
        msg_lines.append(f"轮到 {STONE_LABEL[state['current_player']]} 落子。")

    append_history(
        {
            "game_id": state["game_id"],
            "move_number": state["move_count"],
            "row": row,
            "col": col,
            "player": player,
            "by": player_login,
            "at": state["last_move"]["at"],
            "winner": state["winner"],
        }
    )

    return state, "\n\n".join(msg_lines), True


def issue_url(owner_repo: str, row: int, col: int) -> str:
    title = quote(f"gomoku|{row}|{col}")
    body = quote("Click 'Submit new issue' below to confirm your move. The action will update the board automatically.")
    return f"https://github.com/{owner_repo}/issues/new?title={title}&body={body}"


def render_board_html(state: dict, owner_repo: str) -> str:
    last_move = state.get("last_move") or {}
    last_row, last_col = last_move.get("row"), last_move.get("col")
    winning = set(tuple(c) for c in state.get("winning_line") or [])

    lines = ['<div align="center">', '<table cellspacing="0" cellpadding="3" style="border-collapse: collapse;">']
    header_cells = ["<td></td>"] + [f"<td align=\"center\"><b>{i}</b></td>" for i in range(BOARD_SIZE)]
    lines.append("<tr>" + "".join(header_cells) + "</tr>")

    for r in range(BOARD_SIZE):
        row_html = [f"<td><b>{r}</b></td>"]
        for c in range(BOARD_SIZE):
            val = state["board"][r][c]
            is_last = (r == last_row and c == last_col)
            is_win = (r, c) in winning

            if val == BLACK:
                glyph = "🔴" if is_win or is_last else "⚫"
            elif val == WHITE:
                glyph = "🟡" if is_win or is_last else "⚪"
            else:
                url = issue_url(owner_repo, r, c)
                glyph = f'<a href="{url}" title="落子于 ({r},{c})">·</a>'
            row_html.append(f'<td align="center">{glyph}</td>')
        lines.append("<tr>" + "".join(row_html) + "</tr>")

    lines.append("</table>")
    lines.append("</div>")
    return "\n".join(lines)


def render_status(state: dict) -> str:
    winner = state["winner"]
    if winner in (BLACK, WHITE):
        status = f"🏆 **{STONE_LABEL[winner]} 已获胜！** 下一手将开启新局"
        turn_text = "新局即将开始"
    elif winner == 3:
        status = "🤝 **平局** — 下一手将开启新局"
        turn_text = "新局即将开始"
    else:
        status = "🟢 进行中"
        turn_text = STONE_LABEL[state["current_player"]]

    last = state.get("last_move")
    if last:
        last_text = f"({last['row']},{last['col']}) by @{last['by']}"
    else:
        last_text = "等待第一手"

    return (
        f"**当前回合：** {turn_text} ｜ "
        f"**步数：** {state['move_count']} ｜ "
        f"**上一步：** {last_text} ｜ "
        f"**状态：** {status} ｜ "
        f"**Game #** {state['game_id']}"
    )


def update_readme(state: dict, owner_repo: str) -> None:
    if not README_FILE.exists():
        print("README.md not found, skipping update", file=sys.stderr)
        return

    text = README_FILE.read_text(encoding="utf-8")

    new_board = f"{BOARD_START}\n{render_board_html(state, owner_repo)}\n{BOARD_END}"
    new_status = f"{STATUS_START}\n{render_status(state)}\n{STATUS_END}"

    text = re.sub(
        rf"{re.escape(BOARD_START)}.*?{re.escape(BOARD_END)}",
        lambda m: new_board,
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        rf"{re.escape(STATUS_START)}.*?{re.escape(STATUS_END)}",
        lambda m: new_status,
        text,
        count=1,
        flags=re.DOTALL,
    )

    README_FILE.write_text(text, encoding="utf-8")


def write_outputs(message: str, success: bool) -> None:
    """Write outputs for GitHub Actions (newer GITHUB_OUTPUT mechanism)."""
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(f"success={'true' if success else 'false'}\n")
        f.write("message<<EOF_GOMOKU\n")
        f.write(message.rstrip() + "\n")
        f.write("EOF_GOMOKU\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("title", help="Issue title containing the move (gomoku|row|col)")
    parser.add_argument("login", help="GitHub login of the player")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""), help="OWNER/REPO")
    args = parser.parse_args()

    owner_repo = args.repo or "qiongzhang1225-alt/qiongzhang1225-alt"

    move = parse_move(args.title)
    if move is None:
        msg = (
            "❌ 无法识别落子格式。请使用棋盘上的链接落子，"
            "或者把 Issue 标题改为 `gomoku|row|col`（例如 `gomoku|5|5`）。"
        )
        write_outputs(msg, success=False)
        print(msg)
        return 0  # Don't fail the workflow — just comment

    state = load_state()
    state, msg, success = make_move(state, move[0], move[1], args.login)
    save_state(state)
    update_readme(state, owner_repo)
    write_outputs(msg, success=success)
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
