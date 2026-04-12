"""
M05 — 品質管理
知識主題：FPY 串聯計算、Rework Loop 對 WIP 的影響、不良率改善效益

學習重點：
- FPY 串聯：整線 FPY = 各站 FPY 相乘（越多站越低）
  例：6站各 99.5% → 整線 FPY = 0.995^6 ≈ 97%
- Rework 不只影響良率，也增加 WIP 和 Cycle Time
- 品質改善（不良率 ↓）的複合效益

情境對比：
- 情境 A：原始不良率
- 情境 B：各站不良率降低 50%（6σ 品質改善）
- 情境 C：各站不良率提高 2x（品質惡化）

執行方式：
    python -m simulation.modules.m05_quality
"""

import random
import copy
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS, MachineConfig


def _theoretical_fpy(configs: dict) -> float:
    """計算理論整線 FPY（各站串聯）"""
    fpy = 1.0
    for cfg in configs.values():
        fpy *= (1.0 - cfg.defect_rate)
    return fpy


def _scale_defect_rates(configs: dict, factor: float) -> dict:
    scaled = copy.deepcopy(configs)
    for name, cfg in scaled.items():
        scaled[name] = MachineConfig(
            **{**cfg.__dict__, "defect_rate": min(cfg.defect_rate * factor, 1.0)}
        )
    return scaled


def _run_quality(configs: dict, label: str, seed: int) -> dict:
    random.seed(seed)
    line = SMTLine(machine_configs=configs)
    stats = line.run()
    s = stats.summary()

    rework_counts = [p.rework_count for p in stats.completed_pcbs]
    avg_rework = sum(rework_counts) / max(len(rework_counts), 1)
    rework_rate = sum(1 for r in rework_counts if r > 0) / max(len(rework_counts), 1)

    return {
        "scenario": label,
        "theoretical_fpy_pct": round(_theoretical_fpy(configs) * 100, 3),
        "actual_fpy_pct": s["fpy_pct"],
        "scrap_rate_pct": s["scrap_rate_pct"],
        "rework_rate_pct": round(rework_rate * 100, 2),
        "avg_rework_per_pcb": round(avg_rework, 3),
        "avg_cycle_time_sec": s["avg_cycle_time_sec"],
        "avg_wip": s["avg_wip"],
        "throughput_per_hr": s["throughput_per_hour"],
    }


def run(seed: int = 42) -> dict:
    scenario_a = _run_quality(MACHINE_CONFIGS, "A: 原始不良率", seed)
    scenario_b = _run_quality(
        _scale_defect_rates(MACHINE_CONFIGS, 0.5), "B: 不良率降低 50%", seed
    )
    scenario_c = _run_quality(
        _scale_defect_rates(MACHINE_CONFIGS, 2.0), "C: 不良率提高 2x", seed
    )

    return {
        "module": "M05 Quality (FPY / Rework)",
        "scenarios": [scenario_a, scenario_b, scenario_c],
        "insight": (
            f"不良率改善 50%（B）：FPY {scenario_a['actual_fpy_pct']}% → {scenario_b['actual_fpy_pct']}%，"
            f"WIP {scenario_a['avg_wip']} → {scenario_b['avg_wip']} pcs"
        ),
    }


def print_result(result: dict):
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        console = Console()
        console.print(f"\n[cyan bold]M05 — 品質管理（FPY / Rework Loop）[/cyan bold]")

        table = Table(box=box.SIMPLE_HEAVY)
        table.add_column("情境", style="cyan")
        table.add_column("理論FPY%", justify="right")
        table.add_column("實際FPY%", justify="right")
        table.add_column("返工率%", justify="right")
        table.add_column("平均WIP", justify="right")
        table.add_column("產出率", justify="right")

        for s in result["scenarios"]:
            table.add_row(
                s["scenario"],
                str(s["theoretical_fpy_pct"]),
                str(s["actual_fpy_pct"]),
                str(s["rework_rate_pct"]),
                str(s["avg_wip"]),
                str(s["throughput_per_hr"]),
            )
        console.print(table)
        console.print(f"[yellow]{result['insight']}[/yellow]")
    except ImportError:
        print("\n=== M05 品質管理 ===")
        for s in result["scenarios"]:
            print(f"  {s['scenario']}: FPY={s['actual_fpy_pct']}%, WIP={s['avg_wip']}")


if __name__ == "__main__":
    result = run()
    print_result(result)
