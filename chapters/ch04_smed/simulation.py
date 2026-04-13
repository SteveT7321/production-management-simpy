"""
第四章：快速換線 — SMED（Single Minute Exchange of Die）
執行：python chapters/ch04_smed/simulation.py
"""
import random, copy, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine, STATION_ORDER
from simulation.config import MACHINE_CONFIGS, LINE_CONFIG
from simulation.pcb import PCB


class ScheduledLine(SMTLine):
    """支援多機種換線的 SMT 產線"""

    def __init__(self, batch_size: int, changeover_factor: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.changeover_factor = changeover_factor
        self.total_changeover_time = 0.0

    def run(self, verbose=False):
        self.env.process(self._scheduled_gen(verbose))
        self.env.process(self._wip_sampler())
        self.env.run(until=self.line_config["sim_duration"])
        for name, machine in self.machines.items():
            self.stats.machine_snapshots[name] = machine.get_snapshot()
        return self.stats

    def _scheduled_gen(self, verbose):
        product_types = ["TypeA", "TypeB"]
        idx = 0
        in_batch = 0

        while True:
            if in_batch >= self.batch_size:
                idx = 1 - idx
                in_batch = 0
                for station in ["chip_shooter", "flex_placer", "screen_printer"]:
                    m = self.machines[station]
                    dur = m.config.changeover_time * self.changeover_factor
                    self.total_changeover_time += dur
                    yield self.env.process(m._changeover_gen(dur))

            import random as _r
            yield self.env.timeout(_r.expovariate(1.0 / self.line_config["inter_arrival_mean"]))
            self._pcb_counter += 1
            pcb = PCB(self._pcb_counter, self.env.now, product_types[idx])
            in_batch += 1
            with self._wip_lock:
                self._wip_count += 1
            self.env.process(self._pcb_flow(pcb, verbose))


def _run(batch_size, co_factor, label, seed):
    random.seed(seed)
    line = ScheduledLine(batch_size=batch_size, changeover_factor=co_factor,
                         machine_configs=copy.deepcopy(MACHINE_CONFIGS))
    stats = line.run()
    s = stats.summary()
    return {
        "scenario":              label,
        "batch_size":            batch_size,
        "throughput_per_hr":     s["throughput_per_hour"],
        "total_changeover_hr":   round(line.total_changeover_time / 3600, 2),
        "avg_cycle_time_sec":    s["avg_cycle_time_sec"],
        "fpy_pct":               s["fpy_pct"],
    }


def run(seed: int = 42) -> dict:
    sa = _run(50, 1.0, "A: 大批量 50片，換線正常",      seed)
    sb = _run(10, 1.0, "B: 小批量 10片，換線正常",      seed)
    sc = _run(10, 0.2, "C: 小批量 10片 ＋ SMED（-80%）", seed)
    return {
        "scenarios": [sa, sb, sc],
        "smed_saving_hr": round(sb["total_changeover_hr"] - sc["total_changeover_hr"], 2),
    }


def print_result(r: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box

    c = Console()
    c.print()
    c.print(Rule("[bold cyan]第四章　SMED 快速換線 — 模擬結果[/bold cyan]", style="cyan"))
    c.print()

    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("情境", style="cyan")
    t.add_column("批量", justify="right")
    t.add_column("換線損失(hr)", justify="right")
    t.add_column("產出率(pcs/hr)", justify="right")
    t.add_column("FPY%", justify="right")

    for s in r["scenarios"]:
        co_col = "red" if s["total_changeover_hr"] > 1 else "green"
        t.add_row(s["scenario"], str(s["batch_size"]),
                  f"[{co_col}]{s['total_changeover_hr']}[/{co_col}]",
                  str(s["throughput_per_hr"]), str(s["fpy_pct"]))
    c.print(t)

    c.print()
    c.print(f"  [yellow]SMED 節省換線時間：{r['smed_saving_hr']} hr / 班次[/yellow]")
    c.print("  詳細概念說明請閱讀 README.md")
    c.print()


if __name__ == "__main__":
    print_result(run())
