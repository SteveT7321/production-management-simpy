"""
M06 — Kanban 看板系統
知識主題：WIP 上限控制、Pull vs Push、庫存緩衝

學習重點：
- Push 系統：上游不管下游狀況，持續生產 → WIP 堆積
- Pull 系統（Kanban）：下游有空位才讓上游生產
- WIP 上限（Kanban limit）的設定影響：
  - 太低：上游常被阻擋，產出下降
  - 太高：等同無 Kanban，WIP 堆積
  - 最佳值：Takt Time × 緩衝係數

情境對比：
- 情境 A：無 Kanban（Push 系統）
- 情境 B：Kanban limit = 3（嚴格）
- 情境 C：Kanban limit = 5（業界常見）
- 情境 D：Kanban limit = 10（寬鬆）

執行方式：
    python -m simulation.modules.m06_kanban
"""

import random
import copy
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS


def _run_kanban(kanban_limit, enable: bool, label: str, seed: int) -> dict:
    random.seed(seed)
    line = SMTLine(
        machine_configs=copy.deepcopy(MACHINE_CONFIGS),
        enable_kanban=enable,
        kanban_limit=kanban_limit,
    )
    stats = line.run()
    s = stats.summary()

    # Kanban 等待時間統計
    kanban_waits = [p.kanban_wait_time for p in stats.completed_pcbs]
    avg_kanban_wait = sum(kanban_waits) / max(len(kanban_waits), 1)

    return {
        "scenario": label,
        "kanban_limit": kanban_limit if enable else "無限制",
        "throughput_per_hr": s["throughput_per_hour"],
        "avg_wip": s["avg_wip"],
        "avg_cycle_time_sec": s["avg_cycle_time_sec"],
        "avg_kanban_wait_sec": round(avg_kanban_wait, 1),
        "fpy_pct": s["fpy_pct"],
    }


def run(seed: int = 42) -> dict:
    scenario_a = _run_kanban(999, False, "A: 無 Kanban（Push）", seed)
    scenario_b = _run_kanban(3, True, "B: Kanban limit = 3（嚴格）", seed)
    scenario_c = _run_kanban(5, True, "C: Kanban limit = 5", seed)
    scenario_d = _run_kanban(10, True, "D: Kanban limit = 10（寬鬆）", seed)

    return {
        "module": "M06 Kanban",
        "scenarios": [scenario_a, scenario_b, scenario_c, scenario_d],
        "insight": (
            f"Push 系統平均 WIP={scenario_a['avg_wip']} pcs，"
            f"Kanban(5) 降至 {scenario_c['avg_wip']} pcs，"
            f"Cycle Time {scenario_a['avg_cycle_time_sec']}s → {scenario_c['avg_cycle_time_sec']}s"
        ),
    }


def print_result(result: dict):
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        console = Console()
        console.print(f"\n[cyan bold]M06 — Kanban 看板系統[/cyan bold]")

        table = Table(box=box.SIMPLE_HEAVY)
        table.add_column("情境", style="cyan")
        table.add_column("Kanban上限", justify="right")
        table.add_column("平均WIP", justify="right")
        table.add_column("Cycle Time(s)", justify="right")
        table.add_column("Kanban等待(s)", justify="right")
        table.add_column("產出率", justify="right")

        for s in result["scenarios"]:
            table.add_row(
                s["scenario"], str(s["kanban_limit"]),
                str(s["avg_wip"]), str(s["avg_cycle_time_sec"]),
                str(s["avg_kanban_wait_sec"]), str(s["throughput_per_hr"]),
            )
        console.print(table)
        console.print(f"[yellow]{result['insight']}[/yellow]")
    except ImportError:
        print("\n=== M06 Kanban ===")
        for s in result["scenarios"]:
            print(f"  {s['scenario']}: WIP={s['avg_wip']}, CT={s['avg_cycle_time_sec']}s")


if __name__ == "__main__":
    result = run()
    print_result(result)
