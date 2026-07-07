# Changelog

本專案遵循 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/) 與
[語意化版本](https://semver.org/lang/zh-TW/)。

## [0.1.0] - 2026-07-08

### Added

- 三個 MCP tool（stdio transport，官方 `mcp` SDK 的 FastMCP）：
  - `get_forecast(city)`：36 小時天氣預報（天氣現象、降雨機率、氣溫區間、舒適度），
    縣市名稱模糊對應（台→臺、補市/縣、英文別名、錯字相似度救援；「新竹」「嘉義」市縣都回）。
  - `get_weather_warnings()`：生效中天氣特報，依種類彙整影響縣市；無特報時明確說明。
  - `get_recent_earthquakes(limit)`：顯著有感地震報告（時間、規模、深度、震央、各縣市最大震度）。
- 對 LLM 友善的錯誤訊息（未設金鑰／金鑰無效／逾時／斷線／5xx／資料格式變更）。
- `scripts/explore_api.py`：實測 CWA API、錄製離線測試 fixtures、壞金鑰行為探測。
- `scripts/smoke_test.py`：以 stdio 啟動 server 的端對端煙霧測試。
- MCP resource `taiwan-weather://cities`（縣市清單）與 prompt `weather_briefing`（天氣播報範本）；
  三個工具皆標註 `readOnlyHint`。
- pytest 測試套件（50 項，覆蓋率 94%、CI 門檻 90%）：純函式單元測試 +
  in-memory MCP client 整合測試（respx 攔截 HTTP）。
- console script `taiwan-weather-mcp`，支援 `uvx --from git+…` 免 clone 執行。
- CI（GitHub Actions）：Ubuntu/Windows 測試、ruff lint、金鑰樣式掃描；
  Release workflow（發佈時自動建置並附加 wheel/sdist，預留 PyPI Trusted Publishing）。
- `AGENTS.md`／`CLAUDE.md`：給 AI coding agent 的專案指南。

[0.1.0]: https://github.com/tun0000/taiwan-weather-mcp/releases/tag/v0.1.0
