"""
C01：5S 評核工具

5S 是管理文化，沒有隨機事件可以模擬。
但 5S 成熟度對生產效率有量化的影響，
本工具提供：
1. 5S 評核評分表（每個 S 的具體查核點）
2. 得分對應的效率影響估算（基於業界研究數據）
3. 改善前後的量化比較
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.table import Table
from rich import box

# ── 5S 評核項目（每項 0-4 分）────────────────────────────────────
AUDIT_ITEMS = {
    "S1 整理（Seiri）": [
        ("不需要的物品已清除", 0),
        ("工具 / 零件標示使用頻率分類", 0),
        ("異常物品有明確處置程序", 0),
    ],
    "S2 整頓（Seiton）": [
        ("每樣東西都有固定位置", 0),
        ("取用 30 秒內可找到所需工具", 0),
        ("儲存位置有視覺標示（地板線、看板）", 0),
    ],
    "S3 清掃（Seiso）": [
        ("設備每日清潔，無積塵 / 油污", 0),
        ("清潔同時進行點檢（異常即時發現）", 0),
        ("清潔責任區有明確分配", 0),
    ],
    "S4 清潔（Seiketsu）": [
        ("前三 S 有標準化作業程序（SOP）", 0),
        ("5S 標準定期更新並公告", 0),
        ("新進人員有 5S 訓練", 0),
    ],
    "S5 素養（Shitsuke）": [
        ("員工主動維持 5S 標準", 0),
        ("每月進行 5S 稽核並公布結果", 0),
        ("主管以身作則示範 5S", 0),
    ],
}

# 預設情境：現況分數（0-4 每題）
CURRENT_SCORES = {
    "S1 整理（Seiri）":     [2, 1, 1],
    "S2 整頓（Seiton）":    [1, 0, 1],
    "S3 清掃（Seiso）":     [2, 1, 1],
    "S4 清潔（Seiketsu）":  [1, 1, 0],
    "S5 素養（Shitsuke）":  [1, 0, 1],
}

# 目標分數（改善後）
TARGET_SCORES = {
    "S1 整理（Seiri）":     [3, 3, 2],
    "S2 整頓（Seiton）":    [3, 3, 3],
    "S3 清掃（Seiso）":     [3, 3, 3],
    "S4 清潔（Seiketsu）":  [3, 3, 2],
    "S5 素養（Shitsuke）":  [3, 3, 3],
}

MAX_SCORE_PER_S = 12  # 3 題 × 4 分
MAX_TOTAL       = MAX_SCORE_PER_S * 5

# ── 5S 分數 → 效率影響（基於業界研究）────────────────────────────
# 搜尋時間佔工作時間的比例（分數越低，搜尋越耗時）
# 資料來源：工廠改善案例彙整（SME / Lean Enterprise Institute）
def search_time_pct(score_pct: float) -> float:
    """5S 分數 → 搜尋時間佔比（%）"""
    # 低 5S（<40%）：搜尋時間約 15-20% 工作時間
    # 高 5S（>80%）：搜尋時間降至 2-5% 工作時間
    if score_pct >= 80:
        return 3.0
    elif score_pct >= 60:
        return 7.0
    elif score_pct >= 40:
        return 12.0
    else:
        return 18.0

def defect_reduction_pct(score_pct: float) -> float:
    """5S 環境整潔度對不良率的減少比例"""
    # 清潔度提升 → 靜電/異物導致的不良品減少
    if score_pct >= 80:
        return 30.0
    elif score_pct >= 60:
        return 15.0
    elif score_pct >= 40:
        return 5.0
    else:
        return 0.0

def accident_rate_reduction(score_pct: float) -> float:
    """5S 對工安事故率的改善（%）"""
    if score_pct >= 80:
        return 70.0
    elif score_pct >= 60:
        return 40.0
    else:
        return 10.0


def calc_scores(score_dict: dict) -> dict:
    per_s = {}
    total = 0
    for s_name, scores in score_dict.items():
        s_score = sum(scores)
        per_s[s_name] = s_score
        total += s_score
    return {"per_s": per_s, "total": total, "pct": round(total / MAX_TOTAL * 100, 1)}


def main():
    console = Console()
    console.print("\n[bold cyan]C01　5S 評核工具[/bold cyan]")
    console.print("  場景：SMT 廠區現況評核 vs 改善目標\n")

    current = calc_scores(CURRENT_SCORES)
    target  = calc_scores(TARGET_SCORES)

    # ── 各 S 得分 ────────────────────────────────────────────────
    t1 = Table(title="5S 評核結果", box=box.SIMPLE_HEAVY)
    t1.add_column("維度", style="cyan")
    t1.add_column(f"現況（/{MAX_SCORE_PER_S}）", justify="right")
    t1.add_column("現況%", justify="right")
    t1.add_column(f"目標（/{MAX_SCORE_PER_S}）", justify="right")
    t1.add_column("目標%", justify="right")
    t1.add_column("差距", justify="right")

    for s_name in CURRENT_SCORES:
        c_score = current["per_s"][s_name]
        t_score = target["per_s"][s_name]
        c_pct = round(c_score / MAX_SCORE_PER_S * 100)
        t_pct = round(t_score / MAX_SCORE_PER_S * 100)
        gap = t_score - c_score
        c_color = "red" if c_pct < 50 else "yellow" if c_pct < 75 else "green"
        t1.add_row(
            s_name,
            f"[{c_color}]{c_score}[/{c_color}]",
            f"[{c_color}]{c_pct}%[/{c_color}]",
            str(t_score),
            f"{t_pct}%",
            f"+{gap}" if gap > 0 else str(gap),
        )

    t1.add_row(
        "[bold]總分[/bold]",
        f"[bold]{current['total']}[/bold]",
        f"[bold]{current['pct']}%[/bold]",
        f"[bold]{target['total']}[/bold]",
        f"[bold]{target['pct']}%[/bold]",
        f"[bold]+{target['total']-current['total']}[/bold]",
    )
    console.print(t1)

    # ── 效率影響估算 ─────────────────────────────────────────────
    c_search = search_time_pct(current["pct"])
    t_search = search_time_pct(target["pct"])
    c_defect = defect_reduction_pct(current["pct"])
    t_defect = defect_reduction_pct(target["pct"])

    t2 = Table(title="5S 成熟度 -> 效率影響估算", box=box.SIMPLE_HEAVY)
    t2.add_column("指標", style="cyan")
    t2.add_column(f"現況（{current['pct']}%）", justify="right")
    t2.add_column(f"目標（{target['pct']}%）", justify="right")
    t2.add_column("改善幅度", justify="right")

    rows = [
        ("搜尋工具 / 材料浪費時間",  f"{c_search}% 工時",  f"{t_search}% 工時",  f"-{c_search-t_search}%"),
        ("環境相關不良率減少",       f"{c_defect}%",       f"{t_defect}%",       f"+{t_defect-c_defect}%"),
        ("工安事故率改善",           f"{accident_rate_reduction(current['pct'])}%", f"{accident_rate_reduction(target['pct'])}%", f"+{accident_rate_reduction(target['pct'])-accident_rate_reduction(current['pct']):.0f}%"),
    ]
    for label, cv, tv, imp in rows:
        t2.add_row(label, cv, tv, f"[green]{imp}[/green]")
    console.print(t2)

    # ── 各查核點細節 ─────────────────────────────────────────────
    t3 = Table(title="各查核點現況 vs 目標（0-4 分）", box=box.SIMPLE_HEAVY)
    t3.add_column("S", style="cyan", width=20)
    t3.add_column("查核項目", width=30)
    t3.add_column("現況", justify="center")
    t3.add_column("目標", justify="center")
    t3.add_column("狀態")

    for s_name, items in AUDIT_ITEMS.items():
        c_scores = CURRENT_SCORES[s_name]
        t_scores = TARGET_SCORES[s_name]
        for idx, (item, _) in enumerate(items):
            cs, ts = c_scores[idx], t_scores[idx]
            status = "OK" if cs >= ts else f"需+{ts-cs}分"
            s_color = "green" if cs >= ts else "red"
            t3.add_row(
                s_name if idx == 0 else "",
                item,
                f"[{s_color}]{cs}[/{s_color}]",
                str(ts),
                f"[{s_color}]{status}[/{s_color}]",
            )
    console.print(t3)

    console.print(
        "\n[yellow]5S 與生產管理其他工具的關係：[/yellow]\n"
        "  S2 整頓 → 視覺化管理，讓 Kanban 看板狀態一目了然（第六章）\n"
        "  S3 清掃 → 設備點檢，發現異常即 PM（第七章）\n"
        "  S4 清潔 → SOP 標準化，SPC 才有可比較的基準（第十一章）\n"
        "  5S 是所有精實工具的地基，沒有 5S，其他工具效果大打折扣"
    )


if __name__ == "__main__":
    main()
