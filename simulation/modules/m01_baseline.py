"""
M01 — 基礎產線分析
知識主題：Takt Time、Throughput、Little's Law、WIP

學習重點：
- Takt Time = 可用工時 / 客戶需求數量
- Throughput = 實際單位時間產出
- Little's Law: WIP = λ × W（λ=到達率，W=平均停留時間）
- 識別產線是否符合客戶需求

執行方式：
    python -m simulation.modules.m01_baseline
"""

import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import LINE_CONFIG


def run(seed: int = 42, verbose: bool = False) -> dict:
    random.seed(seed)

    # 客戶需求：每小時 100 片
    customer_demand_per_hour = 100.0
    available_hours = (LINE_CONFIG["sim_duration"] - LINE_CONFIG["warmup_time"]) / 3600.0
    takt_time = 3600.0 / customer_demand_per_hour  # = 36 秒/片

    line = SMTLine()
    stats = line.run(verbose=verbose)

    summary = stats.summary()
    actual_throughput = summary["throughput_per_hour"]

    result = {
        "module": "M01 Baseline",
        "takt_time_sec": takt_time,
        "actual_cycle_time_sec": summary["avg_cycle_time_sec"],
        "actual_throughput_per_hr": actual_throughput,
        "customer_demand_per_hr": customer_demand_per_hour,
        "demand_met": actual_throughput >= customer_demand_per_hour,
        "throughput_gap": round(actual_throughput - customer_demand_per_hour, 1),
        "avg_wip": summary["avg_wip"],
        "littles_law": summary["littles_law"],
        "bottleneck": summary["bottleneck"],
    }

    return result


def print_result(result: dict):
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel(
            f"[bold]Takt Time[/bold]: {result['takt_time_sec']} s  "
            f"（客戶需求 {result['customer_demand_per_hr']} pcs/hr）\n"
            f"[bold]實際 Cycle Time[/bold]: {result['actual_cycle_time_sec']} s\n"
            f"[bold]實際產出率[/bold]: [{'green' if result['demand_met'] else 'red'}]"
            f"{result['actual_throughput_per_hr']} pcs/hr[/]\n"
            f"[bold]需求達成[/bold]: {'✓' if result['demand_met'] else '✗ 缺口 ' + str(abs(result['throughput_gap'])) + ' pcs/hr'}\n"
            f"[bold]平均 WIP[/bold]: {result['avg_wip']} pcs\n"
            f"[bold]Little's Law[/bold]: {result['littles_law']}\n"
            f"[bold]瓶頸站點[/bold]: [red]{result['bottleneck']}[/red]",
            title="[cyan]M01 — 基礎產線分析[/cyan]"
        ))
    except ImportError:
        print("\n=== M01 基礎產線分析 ===")
        for k, v in result.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    result = run()
    print_result(result)
