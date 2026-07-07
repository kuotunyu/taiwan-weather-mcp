from conftest import load_fixture, make_forecast_records

from taiwan_weather.errors import MSG_NO_EARTHQUAKES, MSG_NO_WARNINGS
from taiwan_weather.formatters import (
    format_earthquakes,
    format_forecast,
    format_warnings,
)

# ---------------------------------------------------------------- 合成資料（隨時可跑）


def test_forecast_synthetic():
    text = format_forecast(make_forecast_records("臺中市"))
    assert "【臺中市】未來 36 小時天氣預報" in text
    assert "多雲時晴" in text
    assert "降雨機率：20%" in text
    assert "溫度：26°C ～ 31°C" in text
    assert "舒適度：悶熱" in text
    assert "07/07 18:00 ～ 07/08 06:00（晚上）" in text
    assert "資料來源：中央氣象署" in text


def test_forecast_two_cities():
    text = format_forecast(make_forecast_records("新竹市", "新竹縣"))
    assert "【新竹市】" in text and "【新竹縣】" in text


def test_warnings_empty_is_explicit():
    records = {"location": [{"locationName": "臺北市", "hazardConditions": {"hazards": []}}]}
    assert format_warnings(records) == MSG_NO_WARNINGS


def test_warnings_grouped_by_phenomena():
    def loc(name, phenomena):
        return {
            "locationName": name,
            "hazardConditions": {
                "hazards": [
                    {
                        "info": {"phenomena": phenomena, "significance": "特報"},
                        "validTime": {
                            "startTime": "2026-07-07 10:00:00",
                            "endTime": "2026-07-08 06:00:00",
                        },
                    }
                ]
            },
        }

    records = {
        "location": [loc("基隆市", "陸上強風"), loc("宜蘭縣", "陸上強風"), loc("花蓮縣", "大雨")]
    }
    text = format_warnings(records)
    assert "目前生效中的天氣特報（2 種）" in text
    assert "■ 陸上強風特報" in text
    assert "影響區域：基隆市、宜蘭縣" in text
    assert "■ 大雨特報" in text
    assert "有效時間：07/07 10:00 ～ 07/08 06:00" in text


def test_earthquakes_empty_is_explicit():
    assert format_earthquakes({"Earthquake": []}, 5) == MSG_NO_EARTHQUAKES


def test_earthquakes_synthetic():
    records = {
        "Earthquake": [
            {
                "EarthquakeInfo": {
                    "OriginTime": "2026-07-06 14:23:00",
                    "FocalDepth": 22.5,
                    "Epicenter": {"Location": "花蓮縣政府南南東方 31.3 公里 (位於花蓮縣近海)"},
                    "EarthquakeMagnitude": {"MagnitudeType": "芮氏規模", "MagnitudeValue": 5.2},
                },
                "Intensity": {
                    "ShakingArea": [
                        {"CountyName": "花蓮縣", "AreaIntensity": "4級"},
                        {"CountyName": "南投縣", "AreaIntensity": "3級"},
                        {"CountyName": "花蓮縣", "AreaIntensity": "2級"},  # 同縣取最大
                    ]
                },
            }
        ]
    }
    text = format_earthquakes(records, 5)
    assert "最近 1 筆顯著有感地震報告" in text
    assert "2026-07-06 14:23" in text
    assert "芮氏規模 5.2，深度 22.5 公里" in text
    assert "震央：花蓮縣政府南南東方" in text
    assert "花蓮縣 4級、南投縣 3級" in text  # 依震度排序、同縣取最大


def test_earthquakes_combined_county_entry_is_split():
    # CWA 會把同震度縣市合併成一個項目（CountyName="雲林縣、嘉義縣、彰化縣"）
    records = {
        "Earthquake": [
            {
                "EarthquakeInfo": {
                    "OriginTime": "2026-05-20T09:11:00+08:00",
                    "FocalDepth": 27.8,
                    "Epicenter": {"Location": "臺東縣政府北北東方  65.3  公里"},
                    "EarthquakeMagnitude": {"MagnitudeType": "芮氏規模", "MagnitudeValue": 4.8},
                },
                "Intensity": {
                    "ShakingArea": [
                        {"CountyName": "臺東縣", "AreaIntensity": "4級"},
                        {"CountyName": "雲林縣、嘉義縣、彰化縣", "AreaIntensity": "2級"},
                    ]
                },
            }
        ]
    }
    text = format_earthquakes(records, 5)
    assert "臺東縣 4級、雲林縣 2級、嘉義縣 2級、彰化縣 2級" in text
    assert "、彰化縣、" not in text  # 合併項目不得原樣出現
    assert "2026-05-20 09:11" in text  # ISO 的 T 已換成空格
    assert "北北東方 65.3 公里" in text  # 連續空格已正規化


def test_earthquakes_respects_limit():
    def quake(day):
        return {
            "EarthquakeInfo": {
                "OriginTime": f"2026-07-0{day} 00:00:00",
                "FocalDepth": 10,
                "Epicenter": {"Location": "某處"},
                "EarthquakeMagnitude": {"MagnitudeType": "芮氏規模", "MagnitudeValue": 4.0},
            }
        }

    records = {"Earthquake": [quake(d) for d in range(1, 6)]}
    text = format_earthquakes(records, 2)
    assert "最近 2 筆" in text


# ---------------------------------------------------------- 實測 fixtures（錄製後可跑）


def test_forecast_real_fixture():
    data = load_fixture("f_c0032_001.json")
    text = format_forecast(data["records"])
    assert "【臺中市】未來 36 小時天氣預報" in text
    assert "降雨機率" in text and "°C" in text and "舒適度" in text


def test_warnings_real_fixture():
    data = load_fixture("w_c0033_001.json")
    text = format_warnings(data["records"])
    # 有無特報都合法，但輸出必須是兩者之一的格式
    assert text == MSG_NO_WARNINGS or "目前生效中的天氣特報" in text


def test_earthquakes_real_fixture():
    data = load_fixture("e_a0015_001.json")
    text = format_earthquakes(data["records"], 5)
    assert "顯著有感地震報告" in text
    assert "規模" in text and "深度" in text and "震央" in text
