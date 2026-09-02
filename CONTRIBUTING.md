# 貢獻指南

感謝你願意改進 taiwan-weather-mcp！

## 開發環境

```bash
git clone https://github.com/kuotunyu/taiwan-weather-mcp.git
cd taiwan-weather-mcp
uv sync                      # 自動安裝 Python 3.12 與所有依賴
cp .env.example .env         # 填入你的 CWA 授權碼（只有實測腳本需要）
```

## 開發流程

| 動作 | 指令 |
|---|---|
| 跑測試（離線，不需金鑰） | `uv run pytest` |
| Lint / 格式化 | `uv run ruff check .` / `uv run ruff format .` |
| 實測 CWA API、重錄 fixtures | `uv run --env-file .env python scripts/explore_api.py` |
| 端對端煙霧測試 | `uv run --env-file .env python scripts/smoke_test.py` |

## 原則

- **模組邊界**：`taiwan_weather/formatters.py` 與 `cities.py` 是純函式（不碰網路與環境變數）；
  只有 `api.py` 做 I/O。新功能請維持這個切法，解析邏輯才能離線測試。
- **欄位以實測為準**：CWA 改過欄位命名。改解析程式前先跑 `explore_api.py` 看真實回應，
  fixtures 一併更新進 PR。
- **金鑰安全**：授權碼只能來自環境變數。任何檔案（含 fixtures、測試、文件）都不得
  出現真實金鑰——CI 會掃描並擋下。
- **stdout 是協定通道**：server 端程式碼不可 `print()`，診斷訊息走 stderr / logging。
- 送 PR 前請確認 `uv run pytest` 與 `uv run ruff check .` 都通過。

## 回報問題

請開 [issue](https://github.com/kuotunyu/taiwan-weather-mcp/issues)，附上：
使用環境（Claude Desktop / Claude Code、Windows / WSL）、工具呼叫內容與完整錯誤訊息
（記得把授權碼遮掉）。
