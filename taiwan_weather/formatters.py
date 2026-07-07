"""把 CWA 回應的 JSON 轉成精簡的繁中文字。

純函式模組：dict 進、str 出，不碰 httpx / os.environ，離線即可測試。
欄位名稱以 tests/fixtures 內的實測回應為準。
"""

from .errors import MSG_NO_EARTHQUAKES, MSG_NO_WARNINGS

SOURCE_LINE = "資料來源：中央氣象署"


def _short_time(t: str) -> str:
    """'2026-07-07 18:00:00' → '07/07 18:00'"""
    return f"{t[5:7]}/{t[8:10]} {t[11:16]}"


def _period_label(start_time: str) -> str:
    hour = start_time[11:13]
    return {"00": "凌晨", "06": "白天", "12": "下午", "18": "晚上"}.get(hour, "")


# ---------------------------------------------------------------- 36 小時預報


def format_forecast(records: dict) -> str:
    """F-C0032-001 records → 每縣市三個時段的預報文字。"""
    sections = []
    for loc in records["location"]:
        name = loc["locationName"]
        elements = {el["elementName"]: el["time"] for el in loc["weatherElement"]}
        wx, pop = elements["Wx"], elements["PoP"]
        min_t, max_t, ci = elements["MinT"], elements["MaxT"], elements["CI"]

        lines = [f"【{name}】未來 36 小時天氣預報"]
        for i in range(len(wx)):
            start, end = wx[i]["startTime"], wx[i]["endTime"]
            label = _period_label(start)
            label_part = f"（{label}）" if label else ""
            lines.append(f"■ {_short_time(start)} ～ {_short_time(end)}{label_part}")
            lines.append(f"   天氣：{wx[i]['parameter']['parameterName']}")
            lines.append(f"   降雨機率：{pop[i]['parameter']['parameterName']}%")
            lines.append(
                f"   溫度：{min_t[i]['parameter']['parameterName']}°C"
                f" ～ {max_t[i]['parameter']['parameterName']}°C"
            )
            lines.append(f"   舒適度：{ci[i]['parameter']['parameterName']}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections) + f"\n\n{SOURCE_LINE}"


# ------------------------------------------------------------------ 天氣特報


def format_warnings(records: dict) -> str:
    """W-C0033-001 records → 依「特報種類」彙整影響縣市與有效時間。"""
    # (phenomena, significance) -> {"counties": [...], "starts": [...], "ends": [...]}
    groups: dict[tuple[str, str], dict] = {}
    for loc in records["location"]:
        hazards = (loc.get("hazardConditions") or {}).get("hazards") or []
        for hz in hazards:
            info = hz.get("info") or {}
            phenomena = info.get("phenomena", "")
            significance = info.get("significance", "")
            if not phenomena:
                continue
            g = groups.setdefault(
                (phenomena, significance), {"counties": [], "starts": [], "ends": []}
            )
            county = loc["locationName"]
            if county not in g["counties"]:
                g["counties"].append(county)
            valid = hz.get("validTime") or {}
            if valid.get("startTime"):
                g["starts"].append(valid["startTime"])
            if valid.get("endTime"):
                g["ends"].append(valid["endTime"])

    if not groups:
        return MSG_NO_WARNINGS

    lines = [f"目前生效中的天氣特報（{len(groups)} 種）：", ""]
    for (phenomena, significance), g in groups.items():
        lines.append(f"■ {phenomena}{significance}")
        lines.append(f"   影響區域：{'、'.join(g['counties'])}")
        if g["starts"] and g["ends"]:
            lines.append(
                f"   有效時間：{_short_time(min(g['starts']))} ～ {_short_time(max(g['ends']))}"
            )
    lines += ["", SOURCE_LINE]
    return "\n".join(lines)


# ------------------------------------------------------------------ 有感地震


def _intensity_rank(intensity: str) -> int:
    """震度字串排序權重：'5強' > '5弱' > '4級' > …"""
    if not intensity:
        return 0
    try:
        base = int(intensity[0]) * 10
    except ValueError:
        return 0
    return base + (5 if "強" in intensity else 0)


def format_earthquakes(records: dict, limit: int) -> str:
    """E-A0015-001 records → 編號列出近期顯著有感地震摘要。"""
    quakes = records.get("Earthquake") or records.get("earthquake") or []
    quakes = quakes[:limit]
    if not quakes:
        return MSG_NO_EARTHQUAKES

    lines = [f"最近 {len(quakes)} 筆顯著有感地震報告：", ""]
    for i, eq in enumerate(quakes, 1):
        info = eq["EarthquakeInfo"]
        magnitude = info["EarthquakeMagnitude"]
        mag_type = magnitude.get("MagnitudeType", "規模")
        mag_value = magnitude.get("MagnitudeValue", "?")
        depth = info.get("FocalDepth", "?")
        # OriginTime 為 ISO 格式（2026-07-02T07:06:06+08:00）
        origin_time = info.get("OriginTime", "").replace("T", " ")
        epicenter = (info.get("Epicenter") or {}).get("Location", "不明")
        epicenter = " ".join(epicenter.split())  # CWA 原文有連續空格

        lines.append(f"{i}. {origin_time[:16]}  {mag_type} {mag_value}，深度 {depth} 公里")
        lines.append(f"   震央：{epicenter}")

        # 各縣市最大震度：同縣市取最大，依震度由大到小列出，最多 6 個
        county_max: dict[str, str] = {}
        areas = (eq.get("Intensity") or {}).get("ShakingArea") or []
        for area in areas:
            intensity = area.get("AreaIntensity", "")
            if not intensity:
                continue
            # CountyName 可能是「雲林縣、嘉義縣、彰化縣」的合併多縣市項目
            for county in area.get("CountyName", "").split("、"):
                county = county.strip()
                if not county:
                    continue
                if _intensity_rank(intensity) > _intensity_rank(county_max.get(county, "")):
                    county_max[county] = intensity
        if county_max:
            ranked = sorted(county_max.items(), key=lambda kv: _intensity_rank(kv[1]), reverse=True)
            shown = "、".join(f"{county} {intensity}" for county, intensity in ranked[:6])
            suffix = "…等地" if len(ranked) > 6 else ""
            lines.append(f"   各地最大震度：{shown}{suffix}")

    lines += ["", f"{SOURCE_LINE}（顯著有感地震報告）"]
    return "\n".join(lines)
