import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """讀取實測錄製的 fixture；還沒錄製時 skip 該測試。"""
    path = FIXTURES_DIR / name
    if not path.exists():
        pytest.skip(f"fixture {name} 不存在（先跑 scripts/explore_api.py 錄製）")
    return json.loads(path.read_text(encoding="utf-8"))


def make_forecast_records(*location_names: str) -> dict:
    """依 F-C0032-001 結構產生合成測試資料。"""

    def location(name: str) -> dict:
        def element(el_name: str, values: list[str], unit: str) -> dict:
            return {
                "elementName": el_name,
                "time": [
                    {
                        "startTime": start,
                        "endTime": end,
                        "parameter": {"parameterName": value, "parameterUnit": unit},
                    }
                    for (start, end), value in zip(
                        [
                            ("2026-07-07 18:00:00", "2026-07-08 06:00:00"),
                            ("2026-07-08 06:00:00", "2026-07-08 18:00:00"),
                            ("2026-07-08 18:00:00", "2026-07-09 06:00:00"),
                        ],
                        values,
                        strict=True,
                    )
                ],
            }

        return {
            "locationName": name,
            "weatherElement": [
                element("Wx", ["多雲時晴", "晴時多雲", "多雲"], ""),
                element("PoP", ["20", "10", "30"], "百分比"),
                element("MinT", ["26", "27", "26"], "C"),
                element("MaxT", ["31", "33", "32"], "C"),
                element("CI", ["悶熱", "悶熱", "舒適"], ""),
            ],
        }

    return {"location": [location(n) for n in location_names]}
