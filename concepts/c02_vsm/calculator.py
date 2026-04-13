"""
C02：Value Stream Mapping（VSM）價值流圖分析

VSM 是靜態分析工具，用於繪製「從訂單到出貨」的完整流程，
識別增值活動（VA）和非增值活動（NVA），計算製程效率（PCE）。

本工具以 SMT 產線真實數據計算 VSM 指標，
並對比「改善前（Push）」vs「改善後（Kanban+PM）」的流程效率。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.table import Table
from rich import box

# ── SMT 產線站點數據 ─────────────────────────────────────────────
# 直接使用 simulation/config.py 的參數
STATIONS = [
    {"name": "錫膏印刷", "ct": 20.0, "uptime": 0.923, "defect_rate": 0.005, "wip_before": 5},
    {"name": "SPI",     "ct": 15.0, "uptime": 0.980, "defect_rate": 0.000, "wip_before": 3},
    {"name": "高速機",   "ct":  8.0, "uptime": 0.800, "defect_rate": 0.002, "wip_before": 8},
    {"name": "泛用機",   "ct": 25.0, "uptime": 0.882, "defect_rate": 0.003, "wip_before": 6},
    {"name": "回焊爐",   "ct": 45.0, "uptime": 0.941, "defect_rate": 0.001, "wip_before": 4},
    {"name": "AOI",     "ct": 30.0, "uptime": 0.968, "defect_rate": 0.000, "wip_before": 3},
]

TAKT_TIME = 36.0   # 客戶 Takt Time（s/片）


def calc_vsm(stations: list, takt: float) -> dict:
    """計算 VSM 核心指標"""
    # 增值時間（Value-Added）= 純加工時間
    va_time = sum(s["ct"] for s in stations)

    # 站間等待 NVA = WIP_before × Takt Time（Little's Law）
    nva_queue = sum(s["wip_before"] * takt for s in stations)

    total_lead_time = va_time + nva_queue

    # 製程效率 PCE = VA / Total Lead Time
    pce = va_time / total_lead_time * 100

    # 串聯 FPY
    fpy = 1.0
    for s in stations:
        fpy *= (1 - s["defect_rate"])
    fpy *= 100

    # 最低 Availability（瓶頸可用率）
    min_avail = min(s["uptime"] for s in stations)

    return {
        "va_time_s": round(va_time, 1),
        "nva_queue_s": round(nva_queue, 1),
        "total_lead_time_s": round(total_lead_time, 1),
        "pce_pct": round(pce, 1),
        "fpy_pct": round(fpy, 3),
        "min_avail": round(min_avail * 100, 1),
    }


def main():
    console = Console()
    console.print("\n[bold cyan]C02　Value Stream Mapping（VSM）價值流分析[/bold cyan]")
    console.print(f"  Takt Time = {TAKT_TIME} s/片（客戶需求 100 pcs/hr）\n")

    # ── 各站詳細 ────────────────────────────────────────────────
    t_station = Table(title="各站 VSM 數據", box=box.SIMPLE_HEAVY)
    t_station.add_column("站點", style="cyan")
    t_station.add_column("CT(s)", justify="right")
    t_station.add_column("稼動率", justify="right")
    t_station.add_column("不良率", justify="right")
    t_station.add_column("進站前WIP", justify="right")
    t_station.add_column("佇列等待(s)", justify="right")
    t_station.add_column("VA vs NVA")

    for s in STATIONS:
        queue_wait = s["wip_before"] * TAKT_TIME
        total_at_station = s["ct"] + queue_wait
        va_pct = round(s["ct"] / total_at_station * 100)
        nva_pct = 100 - va_pct
        bar = "[green]" + "#" * (va_pct // 10) + "[/green]" + "[red]" + "-" * (nva_pct // 10) + "[/red]"
        t_station.add_row(
            s["name"],
            str(s["ct"]),
            f"{s['uptime']*100:.1f}%",
            f"{s['defect_rate']*100:.2f}%",
            str(s["wip_before"]),
            str(round(queue_wait, 1)),
            bar,
        )
    console.print(t_station)

    # ── 現況 vs 改善後比較 ───────────────────────────────────────
    # 現況（Push）：從模擬第一章，avg WIP ≈ 101，avg CT ≈ 3095 s
    push_result = {"label": "現況（Push）", **calc_vsm(STATIONS, TAKT_TIME)}
    # 覆蓋為模擬實際值
    push_result["nva_queue_s"] = round(3095 - push_result["va_time_s"], 1)
    push_result["total_lead_time_s"] = 3095
    push_result["pce_pct"] = round(push_result["va_time_s"] / 3095 * 100, 1)

    # 改善後（Kanban limit=50）：avg CT ≈ 1559 s（第六章）
    kanban_result = {"label": "改善後（Kanban+PM）",
                     "va_time_s": push_result["va_time_s"],
                     "nva_queue_s": round(1559 - push_result["va_time_s"], 1),
                     "total_lead_time_s": 1559,
                     "pce_pct": round(push_result["va_time_s"] / 1559 * 100, 1),
                     "fpy_pct": push_result["fpy_pct"],
                     "min_avail": 88.0}

    # 精實目標（PCE ≥ 25%）
    target_lt = round(push_result["va_time_s"] / 0.25)
    lean_result = {"label": f"精實目標（PCE >= 25%）",
                   "va_time_s": push_result["va_time_s"],
                   "nva_queue_s": round(target_lt - push_result["va_time_s"], 1),
                   "total_lead_time_s": target_lt,
                   "pce_pct": 25.0,
                   "fpy_pct": 99.5,
                   "min_avail": 92.0}

    t_compare = Table(title="VSM 改善比較", box=box.SIMPLE_HEAVY)
    t_compare.add_column("狀態", style="cyan")
    t_compare.add_column("VA 時間(s)", justify="right")
    t_compare.add_column("NVA 等待(s)", justify="right")
    t_compare.add_column("總 Lead Time(s)", justify="right")
    t_compare.add_column("PCE%", justify="right")
    t_compare.add_column("FPY%", justify="right")

    for r in [push_result, kanban_result, lean_result]:
        pce_color = "green" if r["pce_pct"] >= 25 else "yellow" if r["pce_pct"] >= 10 else "red"
        t_compare.add_row(
            r["label"],
            str(r["va_time_s"]),
            str(r["nva_queue_s"]),
            str(r["total_lead_time_s"]),
            f"[{pce_color}]{r['pce_pct']}%[/{pce_color}]",
            str(r["fpy_pct"]),
        )
    console.print(t_compare)

    va = push_result["va_time_s"]
    console.print(
        f"\n[yellow]VSM 洞察：[/yellow]\n"
        f"  增值時間（VA）固定為 {va} s（純加工時間，無法壓縮）\n"
        f"  現況 PCE = {va}/{push_result['total_lead_time_s']} = "
        f"{push_result['pce_pct']}%（典型製造業 5~10%）\n"
        f"  Kanban 後 PCE 提升至 {kanban_result['pce_pct']}%\n"
        f"  精實目標（PCE>=25%）：Lead Time 壓縮到 {target_lt} s 以內\n\n"
        f"  [bold]改善 NVA 的工具：[/bold]\n"
        f"  NVA 等待（佇列） → Kanban（第六章）\n"
        f"  NVA 故障停機   → PM（第七章）\n"
        f"  NVA 換線時間   → SMED（第四章）\n"
        f"  NVA 返工時間   → SPC（第十一章）"
    )


if __name__ == "__main__":
    main()
