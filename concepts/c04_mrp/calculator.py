"""
C04：MRP 物料需求計畫

MRP（Material Requirements Planning）透過 BOM 展開、
淨需求計算、批量排程，產生採購與生產計畫。

本工具以 SMT 線 PCB 組裝為例：
  成品（PCBA）← 主板 + 電容 + 電阻 + IC + 焊錫膏
並執行：
1. BOM 展開（多層）
2. 淨需求計算（= 毛需求 - 在手庫存 - 在途）
3. 計畫訂單（Plan Order Release）含前置時間偏移
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.table import Table
from rich import box

# ── BOM（Bill of Materials）定義 ─────────────────────────────────
# 格式：item_id → {"name", "level", "lead_time_weeks", "lot_size", "children": [(child_id, qty)]}

BOM = {
    "PCBA": {
        "name":        "成品 PCBA",
        "level":       0,
        "lead_time":   1,   # 週
        "lot_size":    100, # 最小訂購量（件）
        "on_hand":     50,
        "on_order":    0,   # 在途
        "children":    [("PCB", 1), ("CAP_100N", 20), ("RES_10K", 15),
                        ("IC_MCU", 1), ("SOLDER", 0.5)],
    },
    "PCB": {
        "name":        "裸板 PCB",
        "level":       1,
        "lead_time":   2,
        "lot_size":    200,
        "on_hand":     120,
        "on_order":    200,
        "children":    [],  # 外購件（無子階）
    },
    "CAP_100N": {
        "name":        "電容 100nF",
        "level":       1,
        "lead_time":   1,
        "lot_size":    1000,
        "on_hand":     3500,
        "on_order":    0,
        "children":    [],
    },
    "RES_10K": {
        "name":        "電阻 10kΩ",
        "level":       1,
        "lead_time":   1,
        "lot_size":    1000,
        "on_hand":     2000,
        "on_order":    1000,
        "children":    [],
    },
    "IC_MCU": {
        "name":        "MCU 芯片",
        "level":       1,
        "lead_time":   4,   # IC 前置時間最長
        "lot_size":    50,
        "on_hand":     30,
        "on_order":    50,
        "children":    [],
    },
    "SOLDER": {
        "name":        "焊錫膏（瓶）",
        "level":       1,
        "lead_time":   1,
        "lot_size":    10,
        "on_hand":     8,
        "on_order":    0,
        "children":    [],
    },
}

# ── 主需求排程（MPS：Master Production Schedule）───────────────────
# 週別索引：1=第一週, 2=第二週, ...（共 8 週計畫期）
MPS = {
    1: 0,
    2: 200,
    3: 150,
    4: 300,
    5: 200,
    6: 250,
    7: 200,
    8: 300,
}

WEEKS = list(range(1, 9))


# ── MRP 計算核心 ────────────────────────────────────────────────

def mrp_explosion(item_id: str, gross_requirements: dict) -> dict:
    """
    對單一物料執行 MRP 展開
    回傳：每週的淨需求、計畫訂單收貨、計畫訂單發出
    """
    item = BOM[item_id]
    lt   = item["lead_time"]
    ls   = item["lot_size"]

    on_hand   = item["on_hand"]
    scheduled_receipts = {w: 0 for w in WEEKS}
    # 假設在途訂單在第 1 週到
    if item["on_order"] > 0:
        scheduled_receipts[1] = item["on_order"]

    net_req          = {w: 0 for w in WEEKS}
    planned_receipts = {w: 0 for w in WEEKS}
    planned_releases = {w: 0 for w in WEEKS}
    proj_on_hand     = {}

    for w in WEEKS:
        # 期初在手 + 預計到貨 + 計畫收貨
        available = on_hand + scheduled_receipts[w] + planned_receipts[w]
        gross     = gross_requirements.get(w, 0)
        net       = gross - available

        if net > 0:
            # 批量化：無條件進位到最小訂購量的倍數
            lots = -(-net // ls)   # ceiling division
            qty  = lots * ls
            planned_receipts[w] += qty  # 此週收貨
            # 計畫發出：往前推 lead_time 週
            release_week = w - lt
            if release_week >= 1:
                planned_releases[release_week] += qty
            else:
                planned_releases[1] += qty  # 已逾期，標記第 1 週

            available += qty

        proj_on_hand[w] = max(available - gross, 0)
        on_hand = proj_on_hand[w]

    return {
        "gross_req":       gross_requirements,
        "sched_receipts":  scheduled_receipts,
        "net_req":         net_req,
        "planned_receipts":planned_receipts,
        "planned_releases":planned_releases,
        "proj_on_hand":    proj_on_hand,
    }


def cascade_requirements(mps: dict) -> dict:
    """
    從 MPS 出發，依 BOM 展開所有子階的毛需求
    """
    # Level 0：成品 PCBA 的毛需求 = MPS
    item_gross = {"PCBA": dict(mps)}

    # 依層級展開（Level 0 → Level 1）
    results = {}
    for item_id in BOM:
        gross = item_gross.get(item_id, {w: 0 for w in WEEKS})
        result = mrp_explosion(item_id, gross)
        results[item_id] = result

        # 子階毛需求 = 父階計畫訂單發出 × 用量
        for child_id, qty_per in BOM[item_id]["children"]:
            if child_id not in item_gross:
                item_gross[child_id] = {w: 0 for w in WEEKS}
            for w in WEEKS:
                item_gross[child_id][w] += result["planned_releases"][w] * qty_per

    return results


def main():
    console = Console()
    console.print("\n[bold cyan]C04　MRP 物料需求計畫[/bold cyan]")
    console.print("  場景：SMT PCBA 生產，8 週滾動計畫\n")

    results = cascade_requirements(MPS)

    # ── MPS 顯示 ────────────────────────────────────────────────
    t_mps = Table(title="主生產計畫（MPS）", box=box.SIMPLE_HEAVY)
    t_mps.add_column("週次", style="cyan")
    for w in WEEKS:
        t_mps.add_column(f"W{w}", justify="right")
    t_mps.add_row("需求量（片）", *[str(MPS[w]) for w in WEEKS])
    console.print(t_mps)

    # ── 各物料 MRP 展開 ──────────────────────────────────────────
    for item_id, r in results.items():
        item = BOM[item_id]
        title = (
            f"{item_id}  {item['name']}"
            f"  [LT={item['lead_time']}週  LS={item['lot_size']}件"
            f"  OH={item['on_hand']}  OO={item['on_order']}]"
        )
        t = Table(title=title, box=box.SIMPLE_HEAVY)
        t.add_column("項目", style="cyan", width=14)
        for w in WEEKS:
            t.add_column(f"W{w}", justify="right", width=6)

        rows_def = [
            ("毛需求",     "gross_req",        "white"),
            ("預計到貨",   "sched_receipts",   "blue"),
            ("計畫收貨",   "planned_receipts", "green"),
            ("預計在手",   "proj_on_hand",     "yellow"),
            ("計畫發出",   "planned_releases", "red"),
        ]
        for label, key, color in rows_def:
            vals = []
            for w in WEEKS:
                v = r[key].get(w, 0)
                if v == 0:
                    vals.append("-")
                else:
                    vals.append(f"[{color}]{v:.0f}[/{color}]")
            t.add_row(label, *vals)
        console.print(t)

    # ── 關鍵路徑：IC_MCU 前置時間最長 ───────────────────────────
    ic_releases = results["IC_MCU"]["planned_releases"]
    earliest_issue = min((w for w, v in ic_releases.items() if v > 0), default=None)

    console.print(
        "\n[yellow]MRP 關鍵洞察：[/yellow]\n"
        "  MCU 芯片前置時間 4 週 → 是所有物料中最長的關鍵路徑\n"
        f"  W2 的 200 片需求 → MCU 必須在 W{2-4 if 2-4>=1 else 1} 發出採購單（已逾期）\n"
        "  實務對策：維持 IC 安全庫存 or 與供應商簽框架合約縮短 LT\n"
        "\n  [bold]MRP → ERP 的延伸：[/bold]\n"
        "  MRP I   → 物料計畫（本工具）\n"
        "  MRP II  → 加入產能計畫（CRP）\n"
        "  ERP     → 整合財務、人事、客戶（SAP / Oracle）"
    )


if __name__ == "__main__":
    main()
