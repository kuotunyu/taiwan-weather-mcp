"""taiwan-weather-mcp：中央氣象署開放資料 MCP server（stdio）。

工具：get_forecast、get_weather_warnings、get_recent_earthquakes。
注意：stdout 是 MCP 協定通道，本檔案內絕對不要 print()。
"""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .api import fetch_dataset
from .cities import OFFICIAL_CITIES, resolve_city
from .errors import MSG_SCHEMA_MISMATCH, CWAError
from .formatters import format_earthquakes, format_forecast, format_warnings

mcp = FastMCP("taiwan-weather")

# 三個工具都只讀取公開資料、不改變任何狀態
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


@mcp.tool(annotations=READ_ONLY)
async def get_forecast(city: str) -> str:
    """查詢台灣某縣市未來 36 小時天氣預報。

    回傳三個時段的天氣現象、降雨機率、氣溫區間與舒適度。
    縣市名稱接受常見寫法，例如「台中」「臺北市」「高雄」「Taipei」；
    「新竹」「嘉義」同時對應市與縣，會一次回傳兩者。

    Args:
        city: 縣市名稱（台灣 22 縣市，中英文皆可）。
    """
    try:
        names = resolve_city(city)
        data = await fetch_dataset("F-C0032-001", locationName=names)
        text = format_forecast(data["records"])
        if len(names) > 1:
            text = f"「{city}」同時對應{'與'.join(names)}，以下提供兩者預報：\n\n{text}"
        return text
    except CWAError as e:
        return e.user_message
    except Exception:
        return MSG_SCHEMA_MISMATCH.format(dataset="F-C0032-001")


@mcp.tool(annotations=READ_ONLY)
async def get_weather_warnings() -> str:
    """查詢目前生效中的天氣特報（颱風、豪雨、大雨、低溫、強風等）。

    依特報種類彙整影響縣市與有效時間；若全臺皆無生效中的警特報，
    會明確回覆「目前全臺無生效中的天氣警特報」。
    """
    try:
        data = await fetch_dataset("W-C0033-001")
        return format_warnings(data["records"])
    except CWAError as e:
        return e.user_message
    except Exception:
        return MSG_SCHEMA_MISMATCH.format(dataset="W-C0033-001")


@mcp.tool(annotations=READ_ONLY)
async def get_recent_earthquakes(limit: int = 5) -> str:
    """查詢最近幾筆顯著有感地震報告。

    每筆包含發生時間、規模、深度、震央位置與各縣市最大震度摘要。

    Args:
        limit: 回傳筆數（1–10，預設 5）。
    """
    limit = max(1, min(10, limit))
    try:
        data = await fetch_dataset("E-A0015-001", limit=limit)
        return format_earthquakes(data["records"], limit)
    except CWAError as e:
        return e.user_message
    except Exception:
        return MSG_SCHEMA_MISMATCH.format(dataset="E-A0015-001")


@mcp.resource(
    "taiwan-weather://cities",
    name="taiwan_cities",
    description="get_forecast 可查詢的 22 個官方縣市名稱清單（也接受台/臺、英文、簡稱等常見寫法）",
    mime_type="text/plain",
)
def cities_resource() -> str:
    """22 縣市官方名稱，供 client 顯示或模型參考。"""
    return "、".join(OFFICIAL_CITIES)


@mcp.prompt(name="weather_briefing", title="台灣天氣簡報")
def weather_briefing(city: str = "臺北市") -> str:
    """產生「查詢並播報某縣市天氣」的提示詞範本。

    Args:
        city: 要播報的縣市名稱（預設臺北市）。
    """
    return (
        f"請使用 get_forecast 查詢「{city}」的 36 小時天氣預報，"
        "並用 get_weather_warnings 確認目前是否有生效中的天氣特報。"
        "然後以親切、簡潔的口吻整理成三句以內的天氣簡報，"
        "最後給一句出門建議（例如是否帶傘、防曬或注意低溫）。"
    )


def main() -> None:
    """console script 進入點（uvx / pip install 後的 taiwan-weather-mcp 指令）。"""
    mcp.run()  # 預設 stdio transport


if __name__ == "__main__":
    main()
