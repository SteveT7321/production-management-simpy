"""
第二章：瓶頸分析 — Theory of Constraints (TOC)
執行：python chapters/ch02_bottleneck/simulation.py
"""
import random, copy, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS, MachineConfig


def _run_scenario(configs, label, seed):
    random.seed(seed)
    line = SMTLine(machine_configs=configs)
    stats = line.run()
    s = stats.summary()
    return {
        "scenario":         label,
        "throughput_per_hr": s["throughput_per_hour"],
        "bottleneck":        s["bottleneck"],
        "utilizations": {
            name: round(snap.get("utilization", 0) * 100, 1)
            for name, snap in stats.machine_snapshots.items()
        },
    }


def run(seed: int = 42) -> dict:
    cfg_a = copy.deepcopy(MACHINE_CONFIGS)

    # 情境 B：改善瓶頸（高速機 CT -20%）
    cfg_b = copy.deepcopy(MACHINE_CONFIGS)
    cfg_b["chip_shooter"] = MachineConfig(
        **{**cfg_a["chip_shooter"].__dict__,
           "cycle_time_mean": cfg_a["chip_shooter"].cycle_time_mean * 0.8}
    )

    # 情境 C：改善非瓶頸（泛用機 CT -20%）
    cfg_c = copy.deepcopy(MACHINE_CONFIGS)
    cfg_c["flex_placer"] = MachineConfig(
        **{**cfg_a["flex_placer"].__dict__,
           "cycle_time_mean": cfg_a["flex_placer"].cycle_time_mean * 0.8}
    )

    sa = _run_scenario(cfg_a, "A: 原始產線",              seed)
    sb = _run_scenario(cfg_b, "B: 改善瓶頸（高速機+20%）", seed)
    sc = _run_scenario(cfg_c, "C: 改善非瓶頸（泛用機+20%）", seed)

    return {
        "scenarios":  [sa, sb, sc],
        "base_th":    sa["throughput_per_hr"],
        "gain_b":     round(sb["throughput_per_hr"] - sa["throughput_per_hr"], 1),
        "gain_c":     round(sc["throughput_per_hr"] - sa["throughput_per_hr"], 1),
    }


def print_result(r: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box

    c = Console()
    c.print()
    c.print(Rule("[bold cyan]第二章　TOC 瓶頸分析 — 模擬結果[/bold cyan]", style="cyan"))
    c.print()

    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("情境", style="cyan")
    t.add_column("產出率 (pcs/hr)", justify="right")
    t.add_column("vs 原始", justify="right")
    t.add_column("瓶頸站點")

    base = r["base_th"]
    for s in r["scenarios"]:
        delta = round(s["throughput_per_hr"] - base, 1)
        d_str = (f"[green]＋{delta}[/green]" if delta > 0.5
                 else ("[red]" + str(delta) + "[/red]" if delta < -0.5
                       else "[dim]±0[/dim]"))
        color = "red" if s["utilizations"].get(s["bottleneck"], 0) > 85 else "yellow"
        t.add_row(s["scenario"], str(s["throughput_per_hr"]), d_str,
                  f"[{color}]{s['bottleneck']}[/{color}]")
    c.print(t)

    c.print()
    c.print("  各站稼動率（A | B | C）：")
    stations = list(r["scenarios"][0]["utilizations"].keys())
    for stn in stations:
        parts = []
        for s in r["scenarios"]:
            u = s["utilizations"].get(stn, 0)
            col = "red" if u > 85 else "yellow" if u > 60 else "green"
            bar = "█" * int(u / 5)
            parts.append(f"[{col}]{bar}{u:5.1f}%[/{col}]")
        c.print(f"  {stn:20s}  {'  |  '.join(parts)}")

    c.print()
    c.print(f"  [yellow]改善瓶頸（B）＋{r['gain_b']} pcs/hr｜改善非瓶頸（C）＋{r['gain_c']} pcs/hr[/yellow]")
    c.print()
    c.print("  詳細概念說明請閱讀 README.md")
    c.print()


if __name__ == "__main__":
    print_result(run())
