"""
第十二章：CONWIP vs 逐站 Kanban

第六章的 Kanban 是「系統級 WIP 上限」（即 CONWIP：Constant WIP）。
本章比較三種控制策略：

1. Push（無上限）     ：WIP 不受控
2. CONWIP            ：全線一張全域 WIP 卡，進板前等待
3. 逐站 Kanban       ：每站獨立 WIP 上限，形成站間拉式訊號

CONWIP 實作簡單（一個計數器），但無法對局部壅塞快速反應。
逐站 Kanban 對局部問題更敏感，但管理複雜度高（6 站 × 各自設定）。
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from simulation.smt_line import SMTLine
from simulation.config import LINE_CONFIG
from rich.console import Console
from rich.table import Table
from rich import box

RANDOM_SEED  = 42
SIM_DURATION = 28800.0
WARMUP_TIME  = 3600.0

# WIP 上限設定（設計原則：讓三者總 WIP 上限接近相同，才能公平比較）
# 自然 WIP（Push）≈ 100 片
# CONWIP 上限 = 50（與第六章 C 情境相同）
# 逐站 Kanban 每站 = 10（6 站 × 10 = 60，略高於 CONWIP 50）
CONWIP_LIMIT    = 50
STATION_LIMIT   = 10

SCENARIOS = [
    {"label": "A: Push（無限制）",          "kanban": False, "conwip": None,        "station": False, "slimit": None},
    {"label": "B: CONWIP（全域上限=50）",   "kanban": True,  "conwip": CONWIP_LIMIT, "station": False, "slimit": None},
    {"label": "C: 逐站 Kanban（每站=10）",  "kanban": False, "conwip": None,        "station": True,  "slimit": STATION_LIMIT},
    {"label": "D: 逐站 Kanban（每站=15）",  "kanban": False, "conwip": None,        "station": True,  "slimit": 15},
]


def run_scenario(cfg: dict, seed: int = RANDOM_SEED) -> dict:
    random.seed(seed)
    lc = LINE_CONFIG.copy()
    lc["sim_duration"] = SIM_DURATION
    lc["warmup_time"]  = WARMUP_TIME

    line = SMTLine(
        line_config=lc,
        enable_kanban=cfg["kanban"],
        kanban_limit=cfg["conwip"],
        enable_station_kanban=cfg["station"],
        station_kanban_limit=cfg["slimit"],
    )
    stats = line.run()
    s     = stats.summary()

    return {
        "label":      cfg["label"],
        "throughput": s["throughput_per_hour"],
        "avg_wip":    s["avg_wip"],
        "avg_ct":     s["avg_cycle_time_sec"],
        "fpy":        s["fpy_pct"],
        "bottleneck": s["bottleneck"],
    }


def main():
    console = Console()
    console.print("\n[bold cyan]第十二章　CONWIP vs 逐站 Kanban[/bold cyan]")
    console.print(
        f"  CONWIP 上限={CONWIP_LIMIT}  |  逐站 Kanban 每站={STATION_LIMIT}/{STATION_LIMIT+5}\n"
    )

    results = [run_scenario(cfg) for cfg in SCENARIOS]

    table = Table(title="Push vs CONWIP vs 逐站 Kanban 比較", box=box.SIMPLE_HEAVY)
    table.add_column("情境", style="cyan")
    table.add_column("產出率(pcs/hr)", justify="right")
    table.add_column("平均WIP", justify="right")
    table.add_column("平均CT(s)", justify="right")
    table.add_column("FPY%", justify="right")
    table.add_column("瓶頸站", justify="right")

    a_wip = results[0]["avg_wip"]
    a_ct  = results[0]["avg_ct"]
    for r in results:
        wip_drop = round((a_wip - r["avg_wip"]) / a_wip * 100, 1)
        ct_drop  = round((a_ct  - r["avg_ct"])  / a_ct  * 100, 1)
        wip_color = "green" if wip_drop > 30 else "yellow" if wip_drop > 10 else "white"
        table.add_row(
            r["label"],
            str(r["throughput"]),
            f"[{wip_color}]{r['avg_wip']}[/{wip_color}]",
            str(r["avg_ct"]),
            str(r["fpy"]),
            r["bottleneck"] or "-",
        )
    console.print(table)

    # WIP / CT 降幅摘要
    t2 = Table(title="vs Push 降幅比較", box=box.SIMPLE_HEAVY)
    t2.add_column("情境", style="cyan")
    t2.add_column("WIP降幅%", justify="right")
    t2.add_column("CT降幅%", justify="right")
    t2.add_column("Throughput變化", justify="right")

    for r in results:
        wip_drop = round((a_wip - r["avg_wip"]) / a_wip * 100, 1)
        ct_drop  = round((a_ct  - r["avg_ct"])  / a_ct  * 100, 1)
        tp_delta = round(r["throughput"] - results[0]["throughput"], 1)
        tp_str   = f"+{tp_delta}" if tp_delta >= 0 else str(tp_delta)
        t2.add_row(r["label"], f"{wip_drop}%", f"{ct_drop}%", tp_str)
    console.print(t2)

    console.print(
        "\n[yellow]→ 結論：[/yellow]\n"
        "  CONWIP：實作最簡單（一個全域計數器），有效降低 WIP 和 CT\n"
        "  逐站 Kanban：每站獨立限制，對局部壅塞反應更快，但設定複雜\n"
        "  兩者都比 Push 好，CONWIP 是入門 Pull 系統的最佳起點"
    )


if __name__ == "__main__":
    main()
