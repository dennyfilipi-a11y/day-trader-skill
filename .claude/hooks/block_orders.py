#!/usr/bin/env python3
"""Paper-only guard for this project (Claude Code PreToolUse hook).

Blocks every MCP tool that could reach a broker or place, change, cancel or
close an order: Alpaca, Interactive Brokers and anything named like an order
tool. The Python tools in this repo never talk to a broker, so with this hook
nothing in the project can send an order, paper or live.

Exit code 2 tells Claude Code to refuse the call and show the reason.
"""
import json
import re
import sys

BLOCK = re.compile(
    r"alpaca|ibkr|interactive.?brokers|tradier|schwab|robinhood|etrade|webull|"
    r"place_\w*order|submit_\w*order|replace_order|cancel_\w*order|"
    r"close_\w*position|exercise_\w*option",
    re.I,
)


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    name = str(event.get("tool_name") or "")
    if name.startswith("mcp__") and BLOCK.search(name):
        sys.stderr.write(
            "Blocked by .claude/hooks/block_orders.py: this project is paper trading "
            "only, no broker connection and no orders (tool %s).\n" % name)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
