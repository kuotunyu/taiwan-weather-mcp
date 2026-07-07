"""薄轉接層：讓 `uv run server.py` 這種以檔案路徑啟動的方式繼續可用。

實際邏輯在 taiwan_weather/server.py；打包安裝後也可直接用
`taiwan-weather-mcp` 指令（或 `uvx --from git+... taiwan-weather-mcp`）啟動。
"""

from taiwan_weather.server import main, mcp

__all__ = ["main", "mcp"]

if __name__ == "__main__":
    main()
