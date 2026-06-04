"""Minimal smoke test for Paper-Agent.

This script is intentionally small. It does not generate a full paper. It only
runs the lightweight CLI checks that are useful before a long workflow:

1. check     - verify project files and runtime config
2. ping      - test one short LLM request
3. quicktest - summarize a short truncated material and write outputs/quicktest

Usage:
    python quick_test.py
    python quick_test.py --project examples/demo_project --max-chars 800
    python quick_test.py --skip-llm
"""

from __future__ import annotations

import argparse
import sys

from src.tool_cli import main as cli_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a minimal Paper-Agent smoke test.")
    parser.add_argument("--project", default="examples/demo_project", help="Project directory")
    parser.add_argument("--max-chars", type=int, default=800, help="Chars used by quicktest")
    parser.add_argument("--skip-llm", action="store_true", help="Only run check, do not call model")
    parser.add_argument("--model", default=None, help="Optional model override")
    parser.add_argument("--base-url", default=None, help="Optional base URL override")
    parser.add_argument("--api-key-env", default=None, help="Optional API key env name")
    return parser


def _common_args(args: argparse.Namespace) -> list[str]:
    out = ["--project", args.project]
    if args.model:
        out += ["--model", args.model]
    if args.base_url:
        out += ["--base-url", args.base_url]
    if args.api_key_env:
        out += ["--api-key-env", args.api_key_env]
    return out


def run() -> int:
    args = build_parser().parse_args()

    print("\n[1/3] check")
    code = cli_main(["check", *_common_args(args)])
    if code != 0:
        return code

    if args.skip_llm:
        print("\n已跳过 LLM 调用。")
        return 0

    print("\n[2/3] ping")
    code = cli_main(["ping", *_common_args(args)])
    if code != 0:
        return code

    print("\n[3/3] quicktest")
    return cli_main(["quicktest", *_common_args(args), "--max-chars", str(args.max_chars)])


if __name__ == "__main__":
    raise SystemExit(run())
