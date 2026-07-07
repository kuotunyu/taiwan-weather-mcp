"""實測中央氣象署開放資料 API，確認回應格式並錄製離線測試用 fixtures。

用法（金鑰放 .env 或環境變數 CWA_API_KEY）：
    uv run --env-file .env python scripts/explore_api.py

會做三件事：
1. 逐一呼叫各 dataset，印出實際回應的欄位結構樹（欄位名稱大小寫以此為準）。
2. 把原始回應存到 tests/fixtures/*.json（存檔前確認金鑰字串不在內容中）。
3. 用假金鑰探測一次，記錄 CWA 對無效金鑰的實際回應方式（HTTP 狀態碼／body）。
"""

import json
import os
import sys
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# dataset id -> (額外參數, fixture 檔名；None 表示只印結構不存檔)
DATASETS: dict[str, tuple[dict, str | None]] = {
    "F-C0032-001": ({}, "f_c0032_001.json"),  # 36 小時天氣預報（全部縣市）
    "W-C0033-001": ({}, "w_c0033_001.json"),  # 天氣特報-各別縣市
    "W-C0033-002": ({}, "w_c0033_002.json"),  # 天氣特報-警特報內容（參考用）
    "E-A0015-001": ({"limit": 5}, "e_a0015_001.json"),  # 顯著有感地震報告
    "E-A0016-001": ({"limit": 3}, None),  # 小區域有感地震（僅觀察，v1 不使用）
}


def structure(obj, depth=0, max_depth=6) -> list[str]:
    """遞迴列出 JSON 結構（欄位名與型別），list 只展開第一個元素。"""
    lines = []
    pad = "  " * depth
    if depth > max_depth:
        return [f"{pad}..."]
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                tag = f"list[{len(v)}]" if isinstance(v, list) else "dict"
                lines.append(f"{pad}{k}: {tag}")
                lines.extend(structure(v, depth + 1, max_depth))
            else:
                preview = str(v)
                if len(preview) > 60:
                    preview = preview[:60] + "…"
                lines.append(f"{pad}{k}: {type(v).__name__} = {preview}")
    elif isinstance(obj, list) and obj:
        lines.extend(structure(obj[0], depth, max_depth))
    return lines


def fetch(client: httpx.Client, key: str, dataset_id: str, params: dict) -> httpx.Response:
    return client.get(
        f"{BASE_URL}/{dataset_id}",
        params={"Authorization": key, **params},
    )


def main() -> None:
    key = os.environ.get("CWA_API_KEY")
    if not key:
        print("錯誤：未設定 CWA_API_KEY 環境變數，無法實測。", file=sys.stderr)
        sys.exit(1)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for dataset_id, (params, fixture_name) in DATASETS.items():
            print(f"\n{'=' * 70}\n### {dataset_id}  params={params}")
            resp = fetch(client, key, dataset_id, params)
            print(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            print(f"success = {data.get('success')!r}")
            print("\n".join(structure(data)[:80]))

            if fixture_name:
                text = json.dumps(data, ensure_ascii=False, indent=2)
                assert key not in text, f"金鑰字串出現在 {dataset_id} 回應中，拒絕存檔！"
                path = FIXTURES_DIR / fixture_name
                path.write_text(text, encoding="utf-8")
                print(f"→ 已存 {path.relative_to(FIXTURES_DIR.parent.parent)}")

        # 無效金鑰探測：確認 CWA 實際的失敗回應形式（僅印出，不存檔）
        print(f"\n{'=' * 70}\n### 無效金鑰探測（F-C0032-001, key=CWA-00000000-...）")
        bad = fetch(client, "CWA-00000000-0000-0000-0000-000000000000", "F-C0032-001", {})
        print(f"HTTP {bad.status_code}")
        print(bad.text[:300])


if __name__ == "__main__":
    main()
