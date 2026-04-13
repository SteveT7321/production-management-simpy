"""
第九章：Heijunka 均衡生產

客戶訂單通常是波動的（週一大量、週五少量；或每小時集中一批），
若工廠直接按訂單到達順序「批量推送」，會造成 WIP 劇烈波動，
Cycle Time 不穩定，交期難以預測。

Heijunka（平準化）的做法：把一段時間的訂單均勻分配到每個生產時段，
讓產線以穩定節拍運行，縮小 WIP 波動。
"""

import sys
import os
import random
import statistics as _stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import simpy
from simulation.smt_line import SMTLine, STATION_ORDER
from simulation.config import MACHINE_CONFIGS, LINE_CONFIG
from simulation.pcb import PCB
from rich.console import Console
from rich.table import Table
from rich import box

RANDOM_SEED  = 42
PCBS_PER_HR  = 80          # 需求：每小時 80 片
SHIFT_HRS    = 8
SIM_DURATION = SHIFT_HRS * 3600.0
WARMUP_TIME  = 3600.0


class HeijunkaLine(SMTLine):
    """
    mode='batch'  ：每小時集中一次放板（模擬波動訂單批量推送）
    mode='leveled'：每片均勻間隔進板（Heijunka 平準化）
    """

    def __init__(self, mode: str = "batch", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode

    def _pcb_generator(self, verbose: bool = False):
        interval = 3600.0 / PCBS_PER_HR   # 均衡間隔 = 45 s

        if self.mode == "leveled":
            while True:
                yield self.env.timeout(interval)
                self._create_pcb(verbose)
        else:
            # 批量模式：每小時前 40 秒密集放板（模擬集中到料）
            burst_interval = 40.0 / PCBS_PER_HR   # ~0.5 s 間隔
            while True:
                yield self.env.timeout(3600.0)
                for _ in range(PCBS_PER_HR):
                    yield self.env.timeout(burst_interval)
                    self._create_pcb(verbose)

    def _create_pcb(self, verbose: bool):
        self._pcb_counter += 1
        pcb = PCB(pcb_id=self._pcb_counter, arrival_time=self.env.now)
        import threading
        with self._wip_lock:
            self._wip_count += 1
        self.env.process(self._pcb_flow(pcb, verbose))


def run_scenario(mode: str, seed: int = RANDOM_SEED) -> dict:
    random.seed(seed)
    cfg = LINE_CONFIG.copy()
    cfg["sim_duration"] = SIM_DURATION
    cfg["warmup_time"]  = WARMUP_TIME

    line  = HeijunkaLine(mode=mode, line_config=cfg)
    stats = line.run()
    s     = stats.summary()

    wip_vals = [w for _, w in stats.wip_samples]
    wip_std  = round(_stats.stdev(wip_vals), 1) if len(wip_vals) > 1 else 0.0
    wip_max  = max(wip_vals) if wip_vals else 0

    ct_vals = [p.cycle_time for p in stats.completed_pcbs if p.cycle_time]
    ct_std  = round(_stats.stdev(ct_vals), 1) if len(ct_vals) > 1 else 0.0

    return {
        "mode":         mode,
        "throughput":   s["throughput_per_hour"],
        "avg_wip":      s["avg_wip"],
        "wip_std":      wip_std,
        "wip_max":      wip_max,
        "avg_ct":       s["avg_cycle_time_sec"],
        "ct_std":       ct_std,
        "fpy":          s["fpy_pct"],
    }


def main():
    console = Console()
    console.print("\n[bold cyan]第九章　Heijunka 均衡生產[/bold cyan]")
    console.print(
        f"  需求：{PCBS_PER_HR} pcs/hr，模擬 {SHIFT_HRS} 小時（含 1 小時暖機）\n"
    )

    results = [run_scenario("batch"), run_scenario("leveled")]

    table = Table(title="批量推送 vs Heijunka 均衡生產比較", box=box.SIMPLE_HEAVY)
    table.add_column("情境", style="cyan")
    table.add_column("產出率(pcs/hr)", justify="right")
    table.add_column("平均WIP", justify="right")
    table.add_column("WIP標準差", justify="right")
    table.add_column("WIP峰值", justify="right")
    table.add_column("平均CT(s)", justify="right")
    table.add_column("CT標準差(s)", justify="right")
    table.add_column("FPY%", justify="right")

    labels = ["A: 批量（每小時集中放板）", "B: 均衡（Heijunka）"]
    for label, r in zip(labels, results):
        wip_color = "green" if r["wip_std"] < 20 else "yellow" if r["wip_std"] < 50 else "red"
        table.add_row(
            label,
            str(r["throughput"]),
            str(r["avg_wip"]),
            f"[{wip_color}]{r['wip_std']}[/{wip_color}]",
            str(r["wip_max"]),
            str(r["avg_ct"]),
            str(r["ct_std"]),
            str(r["fpy"]),
        )
    console.print(table)

    a, b = results
    wip_std_drop = round((a["wip_std"] - b["wip_std"]) / max(a["wip_std"], 1) * 100, 1)
    wip_max_drop = round((a["wip_max"] - b["wip_max"]) / max(a["wip_max"], 1) * 100, 1)
    ct_std_drop  = round((a["ct_std"] - b["ct_std"]) / max(a["ct_std"], 1) * 100, 1)

    console.print(
        f"\n[yellow]→ Heijunka 效果：[/yellow]\n"
        f"  WIP 標準差減少 {wip_std_drop}%\n"
        f"  WIP 峰值減少   {wip_max_drop}%\n"
        f"  CT 標準差減少  {ct_std_drop}%（Cycle Time 更穩定 = 交期更可預測）\n"
        f"  產出率幾乎不變（平準化本身不增產，只穩定流動）"
    )


if __name__ == "__main__":
    main()
