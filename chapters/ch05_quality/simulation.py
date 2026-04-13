"""
第五章：品質管理 — FPY 串聯計算與 Rework Loop
執行：python chapters/ch05_quality/simulation.py
"""
import random, copy, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS, MachineConfig


def _theoretical_fpy(configs):
    fpy = 1.0
    for cfg in configs.values():
        fpy *= (1.0 - cfg.defect_rate)
    return fpy


def _scale_defects(configs, factor):
    scaled = copy.deepcopy(configs)
    for name, cfg in scaled.items():
        scaled[name] = MachineConfig(
            **{**cfg.__dict__, "defect_rate": min(cfg.defect_rate * factor, 1.0)}
        )
    return scaled


def _run(configs, label, seed):
    random.seed(seed)
    line = SMTLine(machine_configs=configs)
    stats = line.run()
    s = stats.summary()
    rework_counts = [p.rework_count for p in stats.completed_pcbs]
    avg_rework = sum(rework_counts) / max(len(rework_counts), 1)
    rework_rate = sum(1 for r in rework_counts if r > 0) / max(len(rework_counts), 1)
    return {
        "scenario":           label,
        "theoretical_fpy_pct": round(_theoretical_fpy(configs) * 100, 3),
        "actual_fpy_pct":     s["fpy_pct"],
        "scrap_rate_pct":     s["scrap_rate_pct"],
        "rework_rate_pct":    round(rework_rate * 100, 2),
        "avg_rework_per_pcb": round(avg_rework, 3),
        "avg_cycle_time_sec": s["avg_cycle_time_sec"],
        "avg_wip":            s["avg_wip"],
        "throughput_per_hr":  s["throughput_per_hour"],
    }


def run(seed: int = 42) -> dict:
    sa = _run(MACHINE_CONFIGS,               "A: 原始不良率",      seed)
    sb = _run(_scale_defects(MACHINE_CONFIGS, 0.5), "B: 不良率×0.5（改善）", seed)
    sc = _run(_scale_defects(MACHINE_CONFIGS, 2.0), "C: 不良率×2（惡化）",   seed)
    return {"scenarios": [sa, sb, sc]}


def print_result(r: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box

    c = Console()
    c.print()
    c.print(Rule("[bold cyan]第五章　FPY 品質管理 — 模擬結果[/bold cyan]", style="cyan"))
    c.print()

    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("情境", style="cyan")
    t.add_column("理論FPY%", justify="right")
    t.add_column("實際FPY%", justify="right")
    t.add_column("返工率%", justify="right")
    t.add_column("平均WIP", justify="right")
    t.add_column("產出率", justify="right")

    for s in r["scenarios"]:
        fpy_col = "green" if s["actual_fpy_pct"] >= 99 else "yellow" if s["actual_fpy_pct"] >= 95 else "red"
        t.add_row(s["scenario"],
                  str(s["theoretical_fpy_pct"]),
                  f"[{fpy_col}]{s['actual_fpy_pct']}%[/{fpy_col}]",
                  str(s["rework_rate_pct"]),
                  str(s["avg_wip"]),
                  str(s["throughput_per_hr"]))
    c.print(t)

    base = r["scenarios"][0]
    best = r["scenarios"][1]
    c.print()
    c.print(f"  [yellow]品質改善 50%（B）：WIP {base['avg_wip']} → {best['avg_wip']} pcs，"
            f"FPY {base['actual_fpy_pct']}% → {best['actual_fpy_pct']}%[/yellow]")
    c.print("  詳細概念說明請閱讀 README.md")
    c.print()


if __name__ == "__main__":
    print_result(run())
