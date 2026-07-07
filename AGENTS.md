# AGENTS.md — 給 AI coding agent 的專案指南

## 專案是什麼

台灣天氣／地震查詢的 MCP server（stdio transport），資料來自中央氣象署開放資料平台。
官方 `mcp` Python SDK（FastMCP，穩定版 v1）＋ httpx。提供 3 個 tools、1 個 resource
（`taiwan-weather://cities`）、1 個 prompt（`weather_briefing`）。

## 常用指令

| 動作 | 指令 |
|---|---|
| 安裝依賴 | `uv sync` |
| 測試（離線、不需金鑰） | `uv run pytest` |
| 測試＋覆蓋率（CI 門檻 90%） | `uv run pytest --cov=taiwan_weather --cov=server --cov-fail-under=90` |
| Lint / 格式化 | `uv run ruff check .`／`uv run ruff format .` |
| 實測 CWA API＋重錄 fixtures | `uv run --env-file .env python scripts/explore_api.py` |
| 端對端煙霧測試（需金鑰） | `uv run --env-file .env python scripts/smoke_test.py` |
| 本機啟動 server | `uv run --env-file .env server.py` |

Windows 上跑腳本請設 `PYTHONUTF8=1`（主控台預設 cp950 會炸中文）。

## 架構與硬規則

```
server.py                    # 薄轉接層（向後相容 uv run server.py）
taiwan_weather/server.py     # FastMCP 實例、tools/resource/prompt、console script main()
taiwan_weather/api.py        # ★唯一允許做網路 I/O 的模組
taiwan_weather/cities.py     # 純函式：縣市模糊對應
taiwan_weather/formatters.py # 純函式：CWA JSON → 精簡繁中文字
taiwan_weather/errors.py     # CWAError ＋所有使用者訊息常數
```

1. **`formatters.py` 與 `cities.py` 必須維持純函式**——不 import httpx、不讀環境變數。
   離線測試依賴這條邊界。
2. **`CWA_API_KEY` 只能在呼叫時讀取**（`os.environ.get` 在函式內），不得在 import 時讀。
3. **server 端程式碼禁止 `print()`**——stdout 是 MCP JSON-RPC 協定通道；診斷走 stderr。
4. **錯誤回傳訊息、不 raise 給 client**——tools 捕捉 `CWAError` 回傳 `user_message`
   （繁中、含下一步指引）；未知例外回 `MSG_SCHEMA_MISMATCH`。訊息一律集中在 `errors.py`。
5. **金鑰安全**：任何檔案（含 fixtures、測試、文件）不得出現真實授權碼；
   CI 的 secret-scan job 會用 regex 掃真實金鑰樣式並擋下。
6. **工具 docstring 就是 MCP 工具說明**（模型靠它決定何時呼叫），用繁中、附參數說明。

## 改解析程式前必讀（CWA 資料怪癖）

- **欄位以 `tests/fixtures/` 的實測回應為準**，不要憑文件或記憶寫 parser；
  改動前先跑 `explore_api.py` 看最新真實結構，fixtures 一併更新。
- 地震 `OriginTime` 是 ISO 格式帶 `T`（`2026-07-02T07:06:06+08:00`）；預報時間卻是空格分隔。
- 地震 `ShakingArea[].CountyName` 可能是合併多縣市字串（`"雲林縣、嘉義縣、彰化縣"`），要 split。
- 震央 `Location` 含連續空格，需正規化。
- 無效金鑰：CWA 回 HTTP 401 純文字（非 JSON），也可能回 200＋`success:"false"`，兩者都要處理。
- 預報時段可能從 00:00／06:00／12:00／18:00 開始（凌晨/白天/下午/晚上標籤）。

## 測試慣例

- 整合測試用 in-memory client（`mcp.shared.memory.create_connected_server_and_client_session`），
  HTTP 用 **respx** 攔在 transport 層（能驗證 URL 組裝與重複 query 參數），金鑰用 `monkeypatch.setenv`。
- fixtures 相依的測試在 fixtures 不存在時自動 skip（見 `tests/conftest.py::load_fixture`）。
- 新增錯誤分支時，訊息常數放 `errors.py` 並在 `test_server.py` 加對應整合測試。

## 已知本機環境陷阱（Windows 開發機）

- 防毒偶爾鎖住 venv 內 `dist-info/entry_points.txt` 導致 `uv sync` 重裝專案失敗：
  刪掉壞的 dist-info 資料夾重試，或用 `uv sync --no-install-project` ＋ `uv run --no-sync`。
