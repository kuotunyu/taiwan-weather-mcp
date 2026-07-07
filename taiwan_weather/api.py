"""中央氣象署開放資料 API 呼叫層——整個專案唯一做網路 I/O 的模組。

CWA_API_KEY 在「每次呼叫時」才從環境變數讀取（不能在 import 時讀，
否則 MCP client 以 env 注入金鑰、或測試用 monkeypatch 時都會失效）。
"""

import os

import httpx

from .errors import (
    CWAError,
    MSG_CONNECTION,
    MSG_INVALID_KEY,
    MSG_MISSING_KEY,
    MSG_SERVER_ERROR,
    MSG_TIMEOUT,
)

BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

TIMEOUT = httpx.Timeout(15.0, connect=5.0)


async def fetch_dataset(dataset_id: str, **params) -> dict:
    """呼叫一個 CWA datastore dataset，回傳解析後的 JSON dict。

    params 值可以是 list（httpx 會展開成重複的 query 參數，
    例如 locationName=新竹市&locationName=新竹縣）。
    失敗時 raise CWAError，其 user_message 可直接回覆給 LLM。
    """
    key = os.environ.get("CWA_API_KEY")
    if not key:
        raise CWAError(MSG_MISSING_KEY)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{BASE_URL}/{dataset_id}",
                params={"Authorization": key, **params},
            )
    except httpx.TimeoutException:
        raise CWAError(MSG_TIMEOUT)
    except httpx.HTTPError:
        raise CWAError(MSG_CONNECTION)

    if resp.status_code in (401, 403):
        raise CWAError(MSG_INVALID_KEY)
    if resp.status_code >= 500:
        raise CWAError(MSG_SERVER_ERROR.format(code=resp.status_code))

    data = resp.json()
    # CWA 對無效金鑰也可能回 200 + success != "true"
    if str(data.get("success", "")).lower() != "true":
        raise CWAError(MSG_INVALID_KEY)
    return data
