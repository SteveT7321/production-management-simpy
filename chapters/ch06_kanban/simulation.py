"""
第六章：看板系統 — Kanban WIP 上限控制
執行：python chapters/ch06_kanban/simulation.py
"""
import random, copy, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS


def _run(kanban_limit, enable, label, seed):
    random.seed(seed)
    line = SMTLine(
        machine_configs=copy.deepcopy(MACHINE_CONFIGS),
        enable_kanban=enable,
        kanban_limit=kanban_limit,
    )
    stats = line.run()
    s = stats.summary()
    kanban_waits = [p.kanban_wait_time for p in stats.completed_pcbs]
    avg_wait = sum(kanban_waits) / max(len(kanban_waits), 1)
    return {
        "scenario":            label,
        "kanban_limit":        kanban_limit if enable else "無限制",
        "throughput_per_hr":   s["throughput_per_hour"],
        "avg_wip":             s["avg_wip"],
        "avg_cycle_time_sec":  s["avg_cycle_time_sec"],
        "avg_kanban_wait_sec": round(avg_wait, 1),
        "fpy_pct":             s["fpy_pct"],
    }


def run(seed: int = 42) -> dict:
    sa = _run(999, False, "A: 無 Kanban（Push 系統）",       seed)
    sb = _run(20,  True,  "B: Kanban limit = 20（嚴格）",    seed)
    sc = _run(50,  True,  "C: Kanban limit = 50（推薦）",    seed)
    sd = _run(80,  True,  "D: Kanban limit = 80（寬鬆）",    seed)
    return {"scenarios": [sa, sb, sc, sd]}


def print_result(r: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box

    c = Console()
    c.print()
    c.print(Rule("[bold cyan]第六章　Kanban 看板系統 — 模擬結果[/bold cyan]", style="cyan"))
    c.print()

    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("情境", style="cyan")
    t.add_column("WIP上限", justify="right")
    t.add_column("平均WIP", justify="right")
    t.add_column("Cycle Time(s)", justify="right")
    t.add_column("看板等待(s)", justify="right")
    t.add_column("產出率", justify="right")

    base_wip = r["scenarios"][0]["avg_wip"]
    for s in r["scenarios"]:
        wip = s["avg_wip"]
        wip_col = "red" if wip >= base_wip * 0.95 else "green" if wip < base_wip * 0.7 else "yellow"
        t.add_row(s["scenario"], str(s["kanban_limit"]),
                  f"[{wip_col}]{wip}[/{wip_col}]",
                  str(s["avg_cycle_time_sec"]),
                  str(s["avg_kanban_wait_sec"]),
                  str(s["throughput_per_hr"]))
    c.print(t)

    sc = r["scenarios"][2]   # C: limit=5
    c.print()
    c.print(f"  [yellow]Kanban(5) 將 WIP 從 {base_wip} → {sc['avg_wip']} pcs，"
            f"Cycle Time {r['scenarios'][0]['avg_cycle_time_sec']}s → {sc['avg_cycle_time_sec']}s[/yellow]")
    c.print("  詳細概念說明請閱讀 README.md")
    c.print()


if __name__ == "__main__":
    print_result(run())
