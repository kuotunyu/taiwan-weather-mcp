# taiwan-weather-mcp

台灣即時天氣預報、天氣特報與有感地震查詢的 [MCP](https://modelcontextprotocol.io/)（Model Context Protocol）server，
讓 Claude Desktop / Claude Code 直接查中央氣象署的開放資料。

使用官方 [`mcp` Python SDK](https://github.com/modelcontextprotocol/python-sdk) 的 **FastMCP**
（SDK v2 起更名為 `MCPServer`，本專案使用穩定版 v1 系列），stdio transport。
資料來源：[中央氣象署開放資料平臺](https://opendata.cwa.gov.tw/)。

## 提供的工具

| 工具 | 說明 | 參數 |
|---|---|---|
| `get_forecast` | 某縣市未來 36 小時天氣預報（天氣現象、降雨機率、氣溫區間、舒適度）。縣市名稱有模糊對應：「台中」→「臺中市」、「Taipei」→「臺北市」；「新竹」「嘉義」會同時回傳市與縣 | `city`：縣市名稱 |
| `get_weather_warnings` | 目前生效中的天氣特報（颱風、豪雨、低溫、強風等），依特報種類彙整影響縣市；沒有特報時會明確說明 | 無 |
| `get_recent_earthquakes` | 最近幾筆顯著有感地震（時間、規模、深度、震央、各縣市最大震度摘要） | `limit`：筆數 1–10，預設 5 |

對應的 CWA dataset：`F-C0032-001`（36 小時預報）、`W-C0033-001`（天氣特報）、`E-A0015-001`（顯著有感地震報告）。

## 1. 申請 CWA API 授權碼（免費）

1. 到 [中央氣象署開放資料平臺](https://opendata.cwa.gov.tw/) 點右上角「登入/註冊」，註冊會員（一般 Email 即可，即時核發）。
2. 登入後到 [會員資訊 → API授權碼](https://opendata.cwa.gov.tw/user/authkey)。
3. 點「取得授權碼」，複製形如 `CWA-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` 的字串。

> 授權碼**只**透過環境變數 `CWA_API_KEY` 讀取，不要寫進任何檔案。
> 本機開發可複製 `.env.example` 為 `.env` 填入（`.env` 已被 `.gitignore` 排除）。

## 2. 安裝

先安裝 [uv](https://docs.astral.sh/uv/)：

```bash
# Windows（PowerShell）
winget install astral-sh.uv
# WSL / Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

然後：

```bash
git clone https://github.com/tun0000/taiwan-weather-mcp.git
cd taiwan-weather-mcp
uv sync          # 會自動下載 Python 3.12 與所有依賴
```

## 3. 在 Claude Code 使用

```bash
# Windows（PowerShell，路徑換成你 clone 的位置）
claude mcp add taiwan-weather -e CWA_API_KEY=你的授權碼 -- uv --directory "C:\path\to\taiwan-weather-mcp" run server.py

# WSL / Linux / macOS（repo 需 clone 在該環境內）
claude mcp add taiwan-weather -e CWA_API_KEY=你的授權碼 -- uv --directory ~/taiwan-weather-mcp run server.py
```

加好後用 `claude mcp list` 確認，然後在對話中直接問「台中明天天氣如何？」即可。

## 4. 在 Claude Desktop（Windows）使用

設定檔位置：`%APPDATA%\Claude\claude_desktop_config.json`
（Claude Desktop → 設定 → 開發人員 → 編輯設定檔）。

> 改完設定檔請從系統匣**完全結束** Claude Desktop 再重開；檔案須以 UTF-8 儲存。

### 寫法 A：server 在 WSL 內，透過 `wsl.exe` 橋接

前置（在 WSL 內執行一次）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh        # 安裝 uv
git clone https://github.com/tun0000/taiwan-weather-mcp.git ~/taiwan-weather-mcp
cd ~/taiwan-weather-mcp && uv sync
```

> repo 請放 WSL 自己的檔案系統（如 `~/`），不要放 `/mnt/c/...`，速度差很多。

```json
{
  "mcpServers": {
    "taiwan-weather": {
      "command": "wsl.exe",
      "args": [
        "-e", "bash", "-c",
        "CWA_API_KEY=你的授權碼 exec $HOME/.local/bin/uv --directory $HOME/taiwan-weather-mcp run server.py"
      ]
    }
  }
}
```

兩個常見地雷這個寫法都避開了：

- Claude Desktop 的 `env` 區塊**不會**自動穿透 WSL 邊界，所以金鑰用行內環境變數帶入。
  若不想讓金鑰出現在 args，可改用 `WSLENV` 轉送：

  ```json
  {
    "mcpServers": {
      "taiwan-weather": {
        "command": "wsl.exe",
        "args": ["-e", "/home/你的WSL帳號/.local/bin/uv",
                 "--directory", "/home/你的WSL帳號/taiwan-weather-mcp",
                 "run", "server.py"],
        "env": { "CWA_API_KEY": "你的授權碼", "WSLENV": "CWA_API_KEY/u" }
      }
    }
  }
  ```

- 用非登入 shell（`bash -c` 而非 `bash -lc`）＋ uv 絕對路徑：登入 shell 的 profile 若有任何輸出，
  會污染 stdout 打斷 MCP 協定。

### 寫法 B：直接在 Windows 端用 Python/uv 執行

前置：Windows 裝好 uv（見上），repo clone 在 Windows 檔案系統並 `uv sync`。

```json
{
  "mcpServers": {
    "taiwan-weather": {
      "command": "C:\\Users\\你的帳號\\.local\\bin\\uv.exe",
      "args": ["--directory", "C:\\path\\to\\taiwan-weather-mcp", "run", "server.py"],
      "env": { "CWA_API_KEY": "你的授權碼" }
    }
  }
}
```

> `command` 建議填 uv 的**完整路徑**（Claude Desktop 不一定繼承你的 PATH）。
> 在 PowerShell 執行 `(Get-Command uv).Source` 查詢實際位置
> （winget 安裝的路徑會在 `...\WinGet\Packages\astral-sh.uv_...\uv.exe`）。
> JSON 內的反斜線要寫成 `\\`。

## 5. 示範對話

**36 小時天氣預報**（「台中這兩天天氣怎樣？」）

![36小時預報示範](docs/images/demo-forecast.png)

**天氣特報**（「現在有什麼天氣警報嗎？」）

![天氣特報示範](docs/images/demo-warnings.png)

**近期有感地震**（「最近有地震嗎？」）

![有感地震示範](docs/images/demo-earthquake.png)

## 6. 開發

```bash
uv run pytest                                          # 離線測試（fixtures）
uv run --env-file .env python scripts/explore_api.py   # 實測 CWA API、重錄 fixtures
uv run --env-file .env python scripts/smoke_test.py    # stdio 起 server 實呼叫三個 tool
```

專案結構：

```
server.py                  # MCP server 入口（FastMCP + 3 個 tool）
taiwan_weather/
  api.py                   # CWA API 呼叫（唯一做網路 I/O 的模組）
  cities.py                # 縣市名稱模糊對應（純函式）
  formatters.py            # JSON → 精簡繁中文字（純函式）
  errors.py                # 錯誤類別與所有使用者訊息
scripts/explore_api.py     # 實測 API、錄製 tests/fixtures
scripts/smoke_test.py      # stdio 端對端煙霧測試
tests/                     # pytest（unit + in-memory 整合測試）
```

## 資料來源與授權

- 氣象資料：[中央氣象署開放資料平臺](https://opendata.cwa.gov.tw/)，依
  [政府資料開放授權條款](https://data.gov.tw/license) 使用。
- 程式碼：[MIT License](LICENSE)。

## 安全性

- 授權碼只從環境變數 `CWA_API_KEY` 讀取，程式碼與 repo 中不含任何金鑰。
- `.env` 已被 `.gitignore` 排除；`.env.example` 僅含佔位字串。
