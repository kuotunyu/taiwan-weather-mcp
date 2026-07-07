import pytest

from taiwan_weather.cities import OFFICIAL_CITIES, resolve_city
from taiwan_weather.errors import UnknownCityError


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("臺中市", ["臺中市"]),  # 官方名原樣
        ("台中", ["臺中市"]),  # 台→臺 + 補市
        ("台北", ["臺北市"]),
        ("臺北", ["臺北市"]),
        ("台北市", ["臺北市"]),
        ("高雄", ["高雄市"]),
        ("苗栗", ["苗栗縣"]),  # 補縣
        ("澎湖", ["澎湖縣"]),
        ("Taipei", ["臺北市"]),  # 英文（大小寫不拘）
        ("kaohsiung", ["高雄市"]),
        ("New Taipei", ["新北市"]),  # 含空格的英文
        ("北市", ["臺北市"]),  # 中文簡稱
        ("馬祖", ["連江縣"]),
        (" 台南市 ", ["臺南市"]),  # 前後空白
    ],
)
def test_resolve_single(raw, expected):
    assert resolve_city(raw) == expected


@pytest.mark.parametrize("raw", ["新竹", "嘉義", "Hsinchu", "chiayi"])
def test_resolve_ambiguous_returns_both(raw):
    result = resolve_city(raw)
    assert len(result) == 2
    assert result[0].endswith("市") and result[1].endswith("縣")


def test_typo_fallback():
    # 「巿」是 U+5DFF（不是「市」U+5E02），靠 difflib 救回
    assert resolve_city("臺北巿") == ["臺北市"]


def test_unknown_city_lists_valid_names():
    with pytest.raises(UnknownCityError) as exc_info:
        resolve_city("東京")
    message = exc_info.value.user_message
    assert "東京" in message
    for name in OFFICIAL_CITIES:
        assert name in message


def test_all_official_names_resolve_to_themselves():
    for name in OFFICIAL_CITIES:
        assert resolve_city(name) == [name]
