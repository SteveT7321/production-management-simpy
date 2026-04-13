"""
第十章：安全庫存與補料策略

原物料若突然斷料，整條產線會被迫停機等待。
安全庫存（Safety Stock）是在「再訂購點（ROP）」之上額外備存的緩衝，
用來對抗補料前置時間（Lead Time）內的需求波動。

本章模擬三種庫存策略對斷料次數與產出率的影響。
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import simpy
from simulation.smt_line import SMTLine
from simulation.config import LINE_CONFIG
from simulation.pcb import PCB
from rich.console import Console
from rich.table import Table
from rich import box

RANDOM_SEED       = 42
SIM_DURATION      = 28800.0   # 8 小時
WARMUP_TIME       = 3600.0

# 原物料補料參數
ORDER_QTY         = 120       # 每次訂購量（片）
REPLENISH_LEAD    = 1800.0    # 補料前置時間 30 分鐘
CONSUME_RATE      = 1         # 每片 PCB 消耗 1 單位原料

# 安全庫存策略：ROP = 再訂購點（當庫存降到此水位時下單）
# 安全庫存 = ROP - 前置時間期望需求
# 前置時間期望需求 ≈ (1800 s ÷ 28 s/pcs) ≈ 64 片
LEAD_TIME_DEMAND  = round(REPLENISH_LEAD / LINE_CONFIG["inter_arrival_mean"])  # ≈ 64

SCENARIOS = [
    {"label": "A: 無安全庫存（ROP=0）",         "initial_stock": 100, "rop": 0,                          "ss": 0},
    {"label": "B: 安全庫存 1x（ROP=LTD）",      "initial_stock": 100, "rop": LEAD_TIME_DEMAND,           "ss": LEAD_TIME_DEMAND},
    {"label": "C: 安全庫存 2x（ROP=2×LTD）",    "initial_stock": 100, "rop": LEAD_TIME_DEMAND * 2,       "ss": LEAD_TIME_DEMAND * 2},
]


class SafetyStockLine(SMTLine):
    """
    在標準 SMTLine 前加一道原料緩衝器。
    - material_buffer：原料庫存容器
    - _replenishment_loop：當庫存降到 ROP 以下時下單，Lead Time 後到料
    """

    def __init__(self, initial_stock: int, rop: int, **kwargs):
        super().__init__(**kwargs)
        self.rop             = rop
        self.stockout_events = 0
        self.total_stop_time = 0.0
        self.orders_placed   = 0

        self.material_buffer = simpy.Container(
            self.env, capacity=500, init=initial_stock
        )

    def run(self, verbose: bool = False):
        self.env.process(self._replenishment_loop())
        return super().run(verbose)

    def _replenishment_loop(self):
        """持續監控庫存：低於 ROP 就下單，Lead Time 後到料"""
        while True:
            # 等到庫存低於 ROP
            while self.material_buffer.level > self.rop:
                yield self.env.timeout(30.0)   # 每 30 秒檢查一次

            # 下單
            self.orders_placed += 1
            yield self.env.timeout(REPLENISH_LEAD)

            # 到料（補到 capacity 上限）
            space = self.material_buffer.capacity - self.material_buffer.level
            receive_qty = min(ORDER_QTY, space)
            if receive_qty > 0:
                yield self.material_buffer.put(receive_qty)

            # 短暫等待後再次檢查（避免同一時間點重複下單）
            yield self.env.timeout(60.0)

    def _pcb_generator(self, verbose: bool = False):
        """進板前先從原料庫存取 1 單位；若庫存為 0 則等待（斷料停機）"""
        while True:
            yield self.env.timeout(
                random.expovariate(1.0 / self.line_config["inter_arrival_mean"])
            )

            # 嘗試取料：若庫存為 0 則阻塞（simpy.Container.get 自動等待）
            before_get = self.env.now
            yield self.material_buffer.get(CONSUME_RATE)
            wait = self.env.now - before_get

            if wait > 0.5 and self.env.now >= self.line_config["warmup_time"]:
                self.stockout_events  += 1
                self.total_stop_time  += wait

            # 建立 PCB 並投入產線
            self._pcb_counter += 1
            pcb = PCB(pcb_id=self._pcb_counter, arrival_time=self.env.now)
            with self._wip_lock:
                self._wip_count += 1
            self.env.process(self._pcb_flow(pcb, verbose))


def run_scenario(cfg: dict, seed: int = RANDOM_SEED) -> dict:
    random.seed(seed)
    lc = LINE_CONFIG.copy()
    lc["sim_duration"] = SIM_DURATION
    lc["warmup_time"]  = WARMUP_TIME

    line  = SafetyStockLine(
        initial_stock=cfg["initial_stock"],
        rop=cfg["rop"],
        line_config=lc,
    )
    stats = line.run()
    s     = stats.summary()

    return {
        "label":          cfg["label"],
        "ss":             cfg["ss"],
        "rop":            cfg["rop"],
        "throughput":     s["throughput_per_hour"],
        "avg_wip":        s["avg_wip"],
        "stockout_events":line.stockout_events,
        "total_stop_min": round(line.total_stop_time / 60, 1),
        "orders_placed":  line.orders_placed,
        "fpy":            s["fpy_pct"],
    }


def main():
    console = Console()
    console.print("\n[bold cyan]第十章　安全庫存與補料策略[/bold cyan]")
    console.print(
        f"  前置時間期望需求（LTD）= {LEAD_TIME_DEMAND} 片"
        f"（補料 Lead Time {int(REPLENISH_LEAD/60)} min / {LINE_CONFIG['inter_arrival_mean']} s/片）\n"
    )

    results = [run_scenario(cfg) for cfg in SCENARIOS]

    table = Table(title="安全庫存策略比較（補料 Lead Time = 30 min）", box=box.SIMPLE_HEAVY)
    table.add_column("情境", style="cyan")
    table.add_column("安全庫存(片)", justify="right")
    table.add_column("再訂購點 ROP", justify="right")
    table.add_column("斷料次數", justify="right")
    table.add_column("斷料停機(min)", justify="right")
    table.add_column("下單次數", justify="right")
    table.add_column("產出率(pcs/hr)", justify="right")
    table.add_column("FPY%", justify="right")

    for r in results:
        stop_color = "green" if r["total_stop_min"] == 0 else "yellow" if r["total_stop_min"] < 10 else "red"
        table.add_row(
            r["label"],
            str(r["ss"]),
            str(r["rop"]),
            str(r["stockout_events"]),
            f"[{stop_color}]{r['total_stop_min']}[/{stop_color}]",
            str(r["orders_placed"]),
            str(r["throughput"]),
            str(r["fpy"]),
        )
    console.print(table)

    a, c = results[0], results[2]
    throughput_gain = round(c["throughput"] - a["throughput"], 1)
    console.print(
        f"\n[yellow]→ 結論：[/yellow]\n"
        f"  情境 A 斷料 {a['stockout_events']} 次，停機 {a['total_stop_min']} min\n"
        f"  情境 C 安全庫存 {c['ss']} 片（{round(c['ss']/LEAD_TIME_DEMAND,1)}x LTD），"
        f"斷料 {c['stockout_events']} 次，產出率提升 {throughput_gain} pcs/hr\n"
        f"  代價：持有庫存成本上升（安全庫存越多，資金凍結越多）"
    )


if __name__ == "__main__":
    main()
