"""錯誤類別與所有回覆給 LLM 的繁中訊息。

工具回傳的錯誤訊息會被 MCP client（LLM）直接讀到，
因此每則訊息都要說清楚「發生什麼事」與「下一步該做什麼」。
"""

MSG_MISSING_KEY = (
    "尚未設定 CWA_API_KEY 環境變數，無法查詢中央氣象署資料。"
    "請至中央氣象署開放資料平臺（https://opendata.cwa.gov.tw/）註冊會員並取得 API 授權碼，"
    "將其設定為環境變數 CWA_API_KEY 後重新啟動 MCP server。"
)

MSG_INVALID_KEY = (
    "CWA API 授權碼無效或已失效。"
    "請至 https://opendata.cwa.gov.tw/user/authkey 確認授權碼是否正確，"
    "更新環境變數 CWA_API_KEY 後重新啟動 MCP server。"
)

MSG_TIMEOUT = "連線中央氣象署逾時。CWA 伺服器偶爾回應較慢，請稍後再試一次。"

MSG_CONNECTION = "無法連線至中央氣象署開放資料平臺，請確認網路連線後再試。"

MSG_SERVER_ERROR = "中央氣象署伺服器暫時無法提供服務（HTTP {code}），請稍後再試。"

MSG_SCHEMA_MISMATCH = (
    "CWA 回應的資料格式與預期不符（資料集 {dataset}），可能是官方格式已變更。"
    "請至 https://github.com/tun0000/taiwan-weather-mcp/issues 回報此問題。"
)

MSG_NO_WARNINGS = "目前全臺無生效中的天氣警特報。"

MSG_NO_EARTHQUAKES = "目前查無近期顯著有感地震報告。"


class CWAError(Exception):
    """帶有「可直接回覆給 LLM 的繁中訊息」的錯誤。"""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


class UnknownCityError(CWAError):
    """縣市名稱無法辨識。"""
