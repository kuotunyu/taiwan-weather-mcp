"""煙霧測試：以 stdio 真正啟動 server.py，實際呼叫三個 tool 並印出結果。

需要 CWA_API_KEY（會實打 CWA API）：
    uv run --env-file .env python scripts/smoke_test.py
"""

import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CALLS = [
    ("get_forecast", {"city": "台中"}),
    ("get_forecast", {"city": "新竹"}),  # 歧義：市與縣都回
    ("get_weather_warnings", {}),
    ("get_recent_earthquakes", {"limit": 3}),
]


async def main() -> None:
    if not os.environ.get("CWA_API_KEY"):
        print("錯誤：未設定 CWA_API_KEY，無法實測。", file=sys.stderr)
        sys.exit(1)

    params = StdioServerParameters(
        command=sys.executable,  # 由 `uv run` 執行時即專案 venv 的 python
        args=[str(PROJECT_ROOT / "server.py")],
        env={**os.environ, "PYTHONUTF8": "1"},
        cwd=str(PROJECT_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            print(f"{'=' * 70}\n已註冊的 tool（{len(tools)} 個）：")
            for t in tools:
                first_line = (t.description or "").strip().splitlines()[0]
                print(f"  - {t.name}: {first_line}")

            for name, args in CALLS:
                print(f"\n{'=' * 70}\n>>> {name}({args})\n")
                result = await session.call_tool(name, args)
                for block in result.content:
                    print(block.text)


if __name__ == "__main__":
    asyncio.run(main())
