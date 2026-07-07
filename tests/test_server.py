"""整合測試：in-memory MCP client 呼叫 server.py 的三個 tool，
respx 在 httpx transport 層攔截對 CWA 的請求。"""

import httpx
import pytest
import respx
from conftest import make_forecast_records
from mcp.shared.memory import create_connected_server_and_client_session

from server import mcp
from taiwan_weather.api import BASE_URL
from taiwan_weather.errors import (
    MSG_INVALID_KEY,
    MSG_MISSING_KEY,
    MSG_NO_WARNINGS,
    MSG_TIMEOUT,
)


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    monkeypatch.setenv("CWA_API_KEY", "CWA-TEST-KEY")


async def call_tool(name: str, arguments: dict) -> str:
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool(name, arguments)
    assert not result.isError
    return result.content[0].text


def mock_dataset(dataset_id: str, records: dict):
    return respx.get(f"{BASE_URL}/{dataset_id}").mock(
        return_value=httpx.Response(200, json={"success": "true", "records": records})
    )


@respx.mock
async def test_get_forecast_happy_path():
    route = mock_dataset("F-C0032-001", make_forecast_records("臺中市"))
    text = await call_tool("get_forecast", {"city": "台中"})
    assert "【臺中市】未來 36 小時天氣預報" in text
    assert "降雨機率：20%" in text
    # 模糊對應後帶官方名查詢
    assert "locationName=%E8%87%BA%E4%B8%AD%E5%B8%82" in str(route.calls[0].request.url)


@respx.mock
async def test_get_forecast_ambiguous_city_returns_both():
    mock_dataset("F-C0032-001", make_forecast_records("新竹市", "新竹縣"))
    text = await call_tool("get_forecast", {"city": "新竹"})
    assert "「新竹」同時對應新竹市與新竹縣" in text
    assert "【新竹市】" in text and "【新竹縣】" in text


async def test_get_forecast_unknown_city():
    text = await call_tool("get_forecast", {"city": "東京"})
    assert "無法辨識縣市名稱「東京」" in text
    assert "臺北市" in text  # 訊息要列出有效縣市


async def test_missing_key_message(monkeypatch):
    monkeypatch.delenv("CWA_API_KEY")
    text = await call_tool("get_forecast", {"city": "台中"})
    assert text == MSG_MISSING_KEY


@respx.mock
async def test_invalid_key_http_401():
    respx.get(f"{BASE_URL}/F-C0032-001").mock(return_value=httpx.Response(401))
    text = await call_tool("get_forecast", {"city": "台中"})
    assert text == MSG_INVALID_KEY


@respx.mock
async def test_invalid_key_success_false():
    respx.get(f"{BASE_URL}/F-C0032-001").mock(
        return_value=httpx.Response(200, json={"success": "false"})
    )
    text = await call_tool("get_forecast", {"city": "台中"})
    assert text == MSG_INVALID_KEY


@respx.mock
async def test_timeout_message():
    respx.get(f"{BASE_URL}/F-C0032-001").mock(side_effect=httpx.ConnectTimeout("boom"))
    text = await call_tool("get_forecast", {"city": "台中"})
    assert text == MSG_TIMEOUT


@respx.mock
async def test_get_weather_warnings_none_active():
    mock_dataset(
        "W-C0033-001",
        {"location": [{"locationName": "臺北市", "hazardConditions": {"hazards": []}}]},
    )
    text = await call_tool("get_weather_warnings", {})
    assert text == MSG_NO_WARNINGS


@respx.mock
async def test_get_recent_earthquakes_passes_limit():
    route = mock_dataset("E-A0015-001", {"Earthquake": []})
    text = await call_tool("get_recent_earthquakes", {"limit": 3})
    assert "limit=3" in str(route.calls[0].request.url)
    assert "目前查無近期顯著有感地震報告" in text


@respx.mock
async def test_get_recent_earthquakes_clamps_limit():
    route = mock_dataset("E-A0015-001", {"Earthquake": []})
    await call_tool("get_recent_earthquakes", {"limit": 99})
    assert "limit=10" in str(route.calls[0].request.url)


async def test_tool_docstrings_exposed():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        tools = (await client.list_tools()).tools
    names = {t.name for t in tools}
    assert names == {"get_forecast", "get_weather_warnings", "get_recent_earthquakes"}
    for t in tools:
        assert t.description  # docstring 會成為 MCP 工具說明
