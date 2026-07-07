"""縣市名稱模糊對應：把使用者的各種寫法對應到 CWA 官方 22 縣市名。

純函式模組，不做任何 I/O。
"""

import difflib
import unicodedata

from .errors import UnknownCityError

# CWA F-C0032-001 的官方 locationName（22 縣市）
OFFICIAL_CITIES = [
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "新竹縣", "苗栗縣", "彰化縣", "南投縣",
    "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣",
]

# 英文／羅馬拼音／中文簡稱 → 官方名（key 一律小寫、無空格）
ALIASES = {
    "taipei": "臺北市",
    "newtaipei": "新北市",
    "taoyuan": "桃園市",
    "taichung": "臺中市",
    "tainan": "臺南市",
    "kaohsiung": "高雄市",
    "keelung": "基隆市",
    "hsinchucity": "新竹市",
    "hsinchucounty": "新竹縣",
    "miaoli": "苗栗縣",
    "changhua": "彰化縣",
    "nantou": "南投縣",
    "yunlin": "雲林縣",
    "chiayicity": "嘉義市",
    "chiayicounty": "嘉義縣",
    "pingtung": "屏東縣",
    "yilan": "宜蘭縣",
    "ilan": "宜蘭縣",
    "hualien": "花蓮縣",
    "taitung": "臺東縣",
    "penghu": "澎湖縣",
    "kinmen": "金門縣",
    "lienchiang": "連江縣",
    "matsu": "連江縣",
    "北市": "臺北市",
    "新北": "新北市",
    "馬祖": "連江縣",
}

# 一個名字同時對應「市」與「縣」的歧義寫法 → 兩個都回
AMBIGUOUS = {
    "新竹": ["新竹市", "新竹縣"],
    "嘉義": ["嘉義市", "嘉義縣"],
    "hsinchu": ["新竹市", "新竹縣"],
    "chiayi": ["嘉義市", "嘉義縣"],
}


def _normalize(raw: str) -> str:
    q = unicodedata.normalize("NFKC", raw).strip().lower()
    q = "".join(q.split())  # 移除所有空白（含全形）
    return q.replace("台", "臺")


def resolve_city(raw: str) -> list[str]:
    """把使用者輸入解析成一或兩個官方縣市名。

    解析順序：正規化（NFKC、去空白、台→臺）→ 完全比對 → 別名表 →
    歧義表（新竹／嘉義 → 市縣都回）→ 補「市／縣」字尾 → difflib 相似度後援。
    全部落空時 raise UnknownCityError，訊息列出所有可查詢的縣市名。
    """
    q = _normalize(raw)

    if q in OFFICIAL_CITIES:
        return [q]
    if q in ALIASES:
        return [ALIASES[q]]
    if q in AMBIGUOUS:
        return list(AMBIGUOUS[q])

    # 補字尾：例如「苗栗」→「苗栗縣」、「高雄」→「高雄市」
    suffixed = [name for name in (q + "市", q + "縣") if name in OFFICIAL_CITIES]
    if len(suffixed) == 1:
        return suffixed
    if len(suffixed) == 2:
        return suffixed  # 理論上已被 AMBIGUOUS 攔下，保險起見

    # 錯字後援：例如「臺北巿」（巿 U+5DFF）
    candidates = OFFICIAL_CITIES + list(ALIASES) + list(AMBIGUOUS)
    close = difflib.get_close_matches(q, candidates, n=1, cutoff=0.6)
    if close:
        hit = close[0]
        if hit in OFFICIAL_CITIES:
            return [hit]
        if hit in ALIASES:
            return [ALIASES[hit]]
        return list(AMBIGUOUS[hit])

    raise UnknownCityError(
        f"無法辨識縣市名稱「{raw}」。可查詢的縣市：{'、'.join(OFFICIAL_CITIES)}。"
    )
