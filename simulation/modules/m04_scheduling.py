"""
M04 — 排程與換線（SMED）
知識主題：SMED（Single Minute Exchange of Die）、批量大小對換線損失的影響

學習重點：
- SMED：將換線時間縮短到 10 分鐘以內
- 大批量生產：換線頻率低，但庫存高、彈性差
- 小批量生產：換線頻率高，換線時間未改善前效率低
- SMED 後可兼顧小批量 + 效率

情境：一個工作班次內生產 A、B 兩種機種
- 情境 A：大批量（批次 50 片，換線 2 次）
- 情境 B：小批量未 SMED（批次 10 片，換線 10 次，換線時間不變）
- 情境 C：小批量 + SMED（換線時間縮短 80%）

執行方式：
    python -m simulation.modules.m04_scheduling
"""

import random
import simpy
import copy
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine, STATION_ORDER
from simulation.config import MACHINE_CONFIGS, LINE_CONFIG
from simulation.pcb import PCB


class ScheduledSMTLine(SMTLine):
    """
    支援多機種換線的 SMT 產線
    每生產完一個批次，執行換線後繼續下個批次
    """

    def __init__(self, batch_size: int, changeover_factor: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.changeover_factor = changeover_factor    # SMED: < 1.0
        self.total_changeover_time = 0.0

    def run(self, verbose: bool = False):
        self.env.process(self._scheduled_generator(verbose))
        self.env.process(self._wip_sampler())
        self.env.run(until=self.line_config["sim_duration"])

        for name, machine in self.machines.items():
            self.stats.machine_snapshots[name] = machine.get_snapshot()

        return self.stats

    def _scheduled_generator(self, verbose: bool):
        product_types = ["TypeA", "TypeB"]
        current_type_idx = 0
        pcb_in_batch = 0

        while True:
            # 檢查是否需要換線
            if pcb_in_batch >= self.batch_size:
                current_type_idx = 1 - current_type_idx
                pcb_in_batch = 0

                if verbose:
                    print(f"  [t={self.env.now:.0f}] 換線至 {product_types[current_type_idx]}")

                # 執行換線（所有關鍵機台都要換）
                changeover_procs = []
                for station in ["chip_shooter", "flex_placer", "screen_printer"]:
                    m = self.machines[station]
                    duration = m.config.changeover_time * self.changeover_factor
                    changeover_procs.append(
                        self.env.process(m._changeover_gen(duration))
                    )
                    self.total_changeover_time += duration

                for proc in changeover_procs:
                    yield proc

            iat = random.expovariate(1.0 / self.line_config["inter_arrival_mean"])
            yield self.env.timeout(iat)

            self._pcb_counter += 1
            pcb = PCB(
                pcb_id=self._pcb_counter,
                arrival_time=self.env.now,
                product_type=product_types[current_type_idx],
            )
            pcb_in_batch += 1

            with self._wip_lock:
                self._wip_count += 1

            self.env.process(self._pcb_flow(pcb, verbose))


def _run_scenario(batch_size: int, co_factor: float, label: str, seed: int) -> dict:
    random.seed(seed)
    line = ScheduledSMTLine(
        batch_size=batch_size,
        changeover_factor=co_factor,
        machine_configs=copy.deepcopy(MACHINE_CONFIGS),
    )
    stats = line.run()
    s = stats.summary()
    return {
        "scenario": label,
        "batch_size": batch_size,
        "changeover_factor": co_factor,
        "throughput_per_hr": s["throughput_per_hour"],
        "total_changeover_time_hr": round(line.total_changeover_time / 3600, 2),
        "avg_cycle_time_sec": s["avg_cycle_time_sec"],
        "fpy_pct": s["fpy_pct"],
    }


def run(seed: int = 42) -> dict:
    scenario_a = _run_scenario(50, 1.0, "A: 大批量（50片，換線時間正常）", seed)
    scenario_b = _run_scenario(10, 1.0, "B: 小批量（10片，換線時間正常）", seed)
    scenario_c = _run_scenario(10, 0.2, "C: 小批量 + SMED（換線時間縮短80%）", seed)

    return {
        "module": "M04 Scheduling / SMED",
        "scenarios": [scenario_a, scenario_b, scenario_c],
        "insight": (
            f"SMED 後小批量（C）vs 未改善小批量（B）："
            f"換線損失從 {scenario_b['total_changeover_time_hr']} hr "
            f"降至 {scenario_c['total_changeover_time_hr']} hr"
        ),
    }


def print_result(result: dict):
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        console = Console()
        console.print(f"\n[cyan bold]M04 — 排程與換線（SMED）[/cyan bold]")

        table = Table(box=box.SIMPLE_HEAVY)
        table.add_column("情境", style="cyan")
        table.add_column("批次大小", justify="right")
        table.add_column("換線損失(hr)", justify="right")
        table.add_column("產出率(pcs/hr)", justify="right")
        table.add_column("FPY(%)", justify="right")

        for s in result["scenarios"]:
            table.add_row(
                s["scenario"], str(s["batch_size"]),
                str(s["total_changeover_time_hr"]),
                str(s["throughput_per_hr"]), str(s["fpy_pct"])
            )
        console.print(table)
        console.print(f"[yellow]{result['insight']}[/yellow]")
    except ImportError:
        print("\n=== M04 排程/SMED ===")
        for s in result["scenarios"]:
            print(f"  {s['scenario']}: {s['throughput_per_hr']} pcs/hr, 換線={s['total_changeover_time_hr']}hr")


if __name__ == "__main__":
    result = run()
    print_result(result)
