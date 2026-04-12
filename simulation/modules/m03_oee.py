"""
M03 — OEE 分析
知識主題：Overall Equipment Effectiveness = Availability × Performance × Quality

學習重點：
- Availability（可用率）= 運行時間 / 計畫時間（扣除故障）
- Performance（效率）= 實際產出 / 理論最大產出
- Quality（良率）= 良品數 / 總產出數
- 世界級 OEE ≥ 85%
- 各分項找到改善優先順序

情境對比：
- 情境 A：原始（基準）
- 情境 B：MTBF 提升 2倍（Availability ↑）
- 情境 C：不良率降低 50%（Quality ↑）

執行方式：
    python -m simulation.modules.m03_oee
"""

import random
import copy
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS, MachineConfig


def _improve_mtbf(configs: dict, factor: float) -> dict:
    improved = copy.deepcopy(configs)
    for name, cfg in improved.items():
        improved[name] = MachineConfig(
            **{**cfg.__dict__, "mtbf": cfg.mtbf * factor}
        )
    return improved


def _improve_quality(configs: dict, factor: float) -> dict:
    improved = copy.deepcopy(configs)
    for name, cfg in improved.items():
        improved[name] = MachineConfig(
            **{**cfg.__dict__, "defect_rate": cfg.defect_rate * factor}
        )
    return improved


def _run_and_oee(configs: dict, label: str, seed: int) -> dict:
    random.seed(seed)
    line = SMTLine(machine_configs=configs)
    stats = line.run()

    oee_data = stats.oee_report()
    avg_oee = sum(v["oee"] for v in oee_data.values()) / max(len(oee_data), 1)

    return {
        "scenario": label,
        "avg_oee": round(avg_oee, 3),
        "throughput_per_hr": stats.summary()["throughput_per_hour"],
        "fpy_pct": stats.summary()["fpy_pct"],
        "per_station": {
            name: {
                "oee": v["oee"],
                "utilization": v["utilization"],
            }
            for name, v in oee_data.items()
        },
    }


def run(seed: int = 42) -> dict:
    scenario_a = _run_and_oee(MACHINE_CONFIGS, "A: 原始", seed)
    scenario_b = _run_and_oee(
        _improve_mtbf(MACHINE_CONFIGS, 2.0), "B: MTBF 提升 2x（減少故障）", seed
    )
    scenario_c = _run_and_oee(
        _improve_quality(MACHINE_CONFIGS, 0.5), "C: 不良率降低 50%", seed
    )

    return {
        "module": "M03 OEE",
        "world_class_oee": 0.85,
        "scenarios": [scenario_a, scenario_b, scenario_c],
    }


def print_result(result: dict):
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        console = Console()
        console.print(f"\n[cyan bold]M03 — OEE 分析[/cyan bold]  "
                      f"（世界級標準 ≥ {result['world_class_oee']*100:.0f}%）")

        for s in result["scenarios"]:
            color = "green" if s["avg_oee"] >= result["world_class_oee"] else "yellow"
            console.print(
                f"\n  [bold]{s['scenario']}[/bold]  "
                f"整體 OEE: [{color}]{s['avg_oee']*100:.1f}%[/{color}]  "
                f"產出: {s['throughput_per_hr']} pcs/hr  "
                f"FPY: {s['fpy_pct']}%"
            )
            table = Table(box=box.MINIMAL, show_header=False)
            for name, vals in s["per_station"].items():
                oee_pct = vals["oee"] * 100
                c = "green" if oee_pct >= 85 else "yellow" if oee_pct >= 65 else "red"
                table.add_row(
                    f"  {name}",
                    f"[{c}]OEE {oee_pct:.1f}%[/{c}]",
                    f"稼動 {vals['utilization']*100:.1f}%"
                )
            console.print(table)

    except ImportError:
        print("\n=== M03 OEE 分析 ===")
        for s in result["scenarios"]:
            print(f"  {s['scenario']}: OEE={s['avg_oee']*100:.1f}%")


if __name__ == "__main__":
    result = run()
    print_result(result)
