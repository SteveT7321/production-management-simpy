"""
第七章：預防保養 — PM vs 故障停機
執行：python chapters/ch07_maintenance/simulation.py
"""
import random, copy, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS


def _run(enable_pm, label, seed):
    random.seed(seed)
    line = SMTLine(
        machine_configs=copy.deepcopy(MACHINE_CONFIGS),
        enable_maintenance=enable_pm,
    )
    stats = line.run()
    s = stats.summary()
    total_failures = sum(
        snap.get("failure_count", 0)
        for snap in stats.machine_snapshots.values()
    )
    return {
        "scenario":          label,
        "enable_pm":         enable_pm,
        "throughput_per_hr": s["throughput_per_hour"],
        "avg_wip":           s["avg_wip"],
        "total_failures":    total_failures,
        "fpy_pct":           s["fpy_pct"],
        "bottleneck":        s["bottleneck"],
        "oee_per_station": {
            name: round(snap.get("oee", 0) * 100, 1)
            for name, snap in stats.machine_snapshots.items()
        },
    }


def run(seed: int = 42) -> dict:
    sa = _run(False, "A: 無 PM（純故障停機，Corrective Maintenance）", seed)
    sb = _run(True,  "B: 有 PM（預防保養，PM 週期 = MTBF × 0.8）",    seed)
    return {
        "scenarios": [sa, sb],
        "failure_reduction": sa["total_failures"] - sb["total_failures"],
        "throughput_gain":   round(sb["throughput_per_hr"] - sa["throughput_per_hr"], 1),
    }


def print_result(r: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box

    c = Console()
    c.print()
    c.print(Rule("[bold cyan]第七章　預防保養（PM）— 模擬結果[/bold cyan]", style="cyan"))
    c.print()

    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("情境", style="cyan")
    t.add_column("故障次數", justify="right")
    t.add_column("產出率(pcs/hr)", justify="right")
    t.add_column("平均WIP", justify="right")
    t.add_column("FPY%", justify="right")

    for s in r["scenarios"]:
        f_col = "red" if s["total_failures"] > 20 else "green"
        t.add_row(s["scenario"],
                  f"[{f_col}]{s['total_failures']}[/{f_col}]",
                  str(s["throughput_per_hr"]),
                  str(s["avg_wip"]),
                  str(s["fpy_pct"]))
    c.print(t)

    c.print()
    c.print("  各站 OEE（A → B）：")
    stations = list(r["scenarios"][0]["oee_per_station"].keys())
    for stn in stations:
        vals = [f"{s['oee_per_station'].get(stn, 0):.1f}%" for s in r["scenarios"]]
        a_val = r["scenarios"][0]["oee_per_station"].get(stn, 0)
        b_val = r["scenarios"][1]["oee_per_station"].get(stn, 0)
        col = "green" if b_val > a_val else "dim"
        c.print(f"  {stn:20s}: {vals[0]}  →  [{col}]{vals[1]}[/{col}]")

    c.print()
    c.print(f"  [yellow]啟用 PM：故障減少 {r['failure_reduction']} 次，"
            f"產出率 ＋{r['throughput_gain']} pcs/hr[/yellow]")
    c.print("  詳細概念說明請閱讀 README.md")
    c.print()


if __name__ == "__main__":
    print_result(run())
