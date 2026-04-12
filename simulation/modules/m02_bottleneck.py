"""
M02 — 瓶頸分析（Theory of Constraints）
知識主題：TOC、Utilization、瓶頸改善前後對比

學習重點：
- TOC：系統產出由最慢的一個環節決定（瓶頸）
- Utilization = 忙碌時間 / 總時間
- 改善瓶頸（提速或增加機台）才能提升整體 Throughput
- 改善非瓶頸沒有效果（浪費投資）

情境對比：
- 情境 A：原始產線（高速機是瓶頸）
- 情境 B：高速機提速 20%（等比改善瓶頸）
- 情境 C：泛用機提速 20%（改善非瓶頸）

執行方式：
    python -m simulation.modules.m02_bottleneck
"""

import random
import copy
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS, MachineConfig


def _run_scenario(configs: dict, label: str, seed: int) -> dict:
    random.seed(seed)
    line = SMTLine(machine_configs=configs)
    stats = line.run()
    s = stats.summary()
    return {
        "scenario": label,
        "throughput_per_hr": s["throughput_per_hour"],
        "bottleneck": s["bottleneck"],
        "utilizations": {
            name: round(snap.get("utilization", 0) * 100, 1)
            for name, snap in stats.machine_snapshots.items()
        },
    }


def run(seed: int = 42) -> dict:
    # 情境 A：原始
    configs_a = copy.deepcopy(MACHINE_CONFIGS)

    # 情境 B：改善瓶頸（高速機 cycle_time 縮短 20%）
    configs_b = copy.deepcopy(MACHINE_CONFIGS)
    configs_b["chip_shooter"] = MachineConfig(
        **{**configs_a["chip_shooter"].__dict__,
           "cycle_time_mean": configs_a["chip_shooter"].cycle_time_mean * 0.8}
    )

    # 情境 C：改善非瓶頸（泛用機 cycle_time 縮短 20%）
    configs_c = copy.deepcopy(MACHINE_CONFIGS)
    configs_c["flex_placer"] = MachineConfig(
        **{**configs_a["flex_placer"].__dict__,
           "cycle_time_mean": configs_a["flex_placer"].cycle_time_mean * 0.8}
    )

    scenario_a = _run_scenario(configs_a, "A: 原始產線", seed)
    scenario_b = _run_scenario(configs_b, "B: 改善瓶頸（高速機+20%）", seed)
    scenario_c = _run_scenario(configs_c, "C: 改善非瓶頸（泛用機+20%）", seed)

    return {
        "module": "M02 Bottleneck (TOC)",
        "scenarios": [scenario_a, scenario_b, scenario_c],
        "insight": (
            f"改善瓶頸（B）產出提升 "
            f"{scenario_b['throughput_per_hr'] - scenario_a['throughput_per_hr']:.1f} pcs/hr，"
            f"改善非瓶頸（C）提升 "
            f"{scenario_c['throughput_per_hr'] - scenario_a['throughput_per_hr']:.1f} pcs/hr"
        ),
    }


def print_result(result: dict):
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        console = Console()
        console.print(f"\n[cyan bold]M02 — 瓶頸分析（TOC）[/cyan bold]")

        table = Table(box=box.SIMPLE_HEAVY)
        table.add_column("情境", style="cyan")
        table.add_column("產出率 (pcs/hr)", justify="right")
        table.add_column("瓶頸站點")

        for s in result["scenarios"]:
            table.add_row(s["scenario"], str(s["throughput_per_hr"]), s["bottleneck"])

        console.print(table)
        console.print(f"[yellow]洞察：{result['insight']}[/yellow]")

        # 稼動率分布
        console.print("\n各站稼動率（%）：")
        for scenario in result["scenarios"]:
            console.print(f"  {scenario['scenario']}:")
            for name, util in scenario["utilizations"].items():
                bar = "█" * int(util / 5)
                color = "red" if util > 85 else "yellow" if util > 60 else "green"
                console.print(f"    {name:20s} [{color}]{bar} {util}%[/{color}]")

    except ImportError:
        print("\n=== M02 瓶頸分析 ===")
        for s in result["scenarios"]:
            print(f"  {s['scenario']}: {s['throughput_per_hr']} pcs/hr, 瓶頸={s['bottleneck']}")
        print(f"  洞察: {result['insight']}")


if __name__ == "__main__":
    result = run()
    print_result(result)
