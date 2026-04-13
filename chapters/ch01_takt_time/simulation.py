"""
第一章：基礎產線分析 — Takt Time 與 Little's Law
執行：python chapters/ch01_takt_time/simulation.py
"""
import random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine


def run(seed: int = 42) -> dict:
    random.seed(seed)

    customer_demand_per_hour = 100.0
    takt_time = 3600.0 / customer_demand_per_hour   # 36 s/pcs

    line = SMTLine()
    stats = line.run()
    s = stats.summary()

    actual_throughput = s["throughput_per_hour"]
    gap = round(actual_throughput - customer_demand_per_hour, 1)

    return {
        "takt_time_sec":            takt_time,
        "actual_cycle_time_sec":    s["avg_cycle_time_sec"],
        "actual_throughput_per_hr": actual_throughput,
        "customer_demand_per_hr":   customer_demand_per_hour,
        "demand_met":               actual_throughput >= customer_demand_per_hour,
        "throughput_gap":           gap,
        "avg_wip":                  s["avg_wip"],
        "littles_law":              s["littles_law"],
        "bottleneck":               s["bottleneck"],
    }


def print_result(r: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box

    c = Console()
    c.print()
    c.print(Rule("[bold cyan]第一章　Takt Time 與 Little's Law — 模擬結果[/bold cyan]", style="cyan"))
    c.print()

    t = Table(box=box.SIMPLE_HEAVY, show_header=False, padding=(0, 2))
    t.add_column("指標", style="cyan", min_width=22)
    t.add_column("數值")

    ok = "[green]✓ 達標[/green]" if r["demand_met"] else "[red]✗ 未達標[/red]"
    gap = r["throughput_gap"]
    gap_str = f"{'＋' if gap >= 0 else ''}{gap} pcs/hr"

    t.add_row("Takt Time",           f"{r['takt_time_sec']} s/pcs")
    t.add_row("實際 Cycle Time",     f"{r['actual_cycle_time_sec']} s/pcs")
    t.add_row("實際產出率",           f"{r['actual_throughput_per_hr']} pcs/hr  {ok}")
    t.add_row("客戶需求",             f"{r['customer_demand_per_hr']} pcs/hr")
    t.add_row("產出差距",             gap_str)
    t.add_row("平均 WIP",             f"{r['avg_wip']} pcs")
    t.add_row("Little's Law 驗算",   str(r["littles_law"]))
    t.add_row("瓶頸站點",             f"[red]{r['bottleneck']}[/red]")
    c.print(t)

    c.print()
    c.print("  詳細概念說明請閱讀 [link]README.md[/link]")
    c.print()


if __name__ == "__main__":
    print_result(run())
