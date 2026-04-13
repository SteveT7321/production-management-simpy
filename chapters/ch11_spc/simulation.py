"""
第十一章：SPC 統計製程管制

設備老化、耗材耗盡或環境變化，都可能造成「製程漂移（Process Drift）」：
不良率從正常的 0.002 悄悄爬升到 0.05，肉眼難以察覺。

SPC（Statistical Process Control）透過管制圖（Control Chart）
定期對製程取樣，一旦統計量超出管制界限（Control Limit）就發出警報，
在問題惡化前介入修正。

本章以 p 管制圖示範：有 SPC vs 無 SPC 時，製程漂移對 FPY 的影響差異。
"""

import sys
import os
import random
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS, LINE_CONFIG, MachineConfig
from simulation.machines import MachineStatus
from rich.console import Console
from rich.table import Table
from rich import box

RANDOM_SEED        = 42
SIM_DURATION       = 28800.0
WARMUP_TIME        = 3600.0

# 製程參數
DRIFT_MACHINE      = "chip_shooter"
NORMAL_DEFECT_RATE = MACHINE_CONFIGS[DRIFT_MACHINE].defect_rate   # 0.002
DRIFT_DEFECT_RATE  = 0.050      # 漂移後 25x，模擬設備磨損/耗材耗盡
DRIFT_START_TIME   = 7200.0     # 暖機後 2 小時（sim t=8200）

# SPC p 管制圖參數
# UCL = p₀ + 3√(p₀(1-p₀)/n)
SPC_SAMPLE_SIZE    = 20         # 每批取樣 n=20 片
RECALIBRATE_TIME   = 300.0      # 重新校正停機 5 分鐘

_UCL = NORMAL_DEFECT_RATE + 3 * math.sqrt(
    NORMAL_DEFECT_RATE * (1 - NORMAL_DEFECT_RATE) / SPC_SAMPLE_SIZE
)


class SPCLine(SMTLine):
    """
    加入製程漂移與 SPC 監控：
    - _drift_process：在 DRIFT_START_TIME 後提高 chip_shooter 不良率
    - _spc_monitor  ：定期取樣，超出 UCL 觸發重新校正
    """

    def __init__(self, enable_drift: bool = True, enable_spc: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.enable_drift     = enable_drift
        self.enable_spc       = enable_spc
        self.drift_active     = False
        self.alarms           = 0
        self.recalibrations   = 0
        self.total_recal_time = 0.0

        # 取樣狀態
        self._prev_processed  = 0
        self._prev_defects    = 0

    def run(self, verbose: bool = False):
        if self.enable_drift:
            self.env.process(self._drift_process())
        if self.enable_spc:
            self.env.process(self._spc_monitor())
        return super().run(verbose)

    def _drift_process(self):
        """在 DRIFT_START_TIME 觸發製程漂移"""
        yield self.env.timeout(DRIFT_START_TIME)
        self.drift_active = True
        self.machines[DRIFT_MACHINE].config.defect_rate = DRIFT_DEFECT_RATE

    def _spc_monitor(self):
        """
        p 管制圖監控：
        每累積 SPC_SAMPLE_SIZE 片，計算樣本不良率 p̂
        若 p̂ > UCL → 警報 → 停機重新校正
        """
        # 等 chip_shooter 有足夠資料後才開始監控
        cycle_approx = MACHINE_CONFIGS[DRIFT_MACHINE].cycle_time_mean
        check_interval = SPC_SAMPLE_SIZE * cycle_approx   # ≈ 160 s

        while True:
            yield self.env.timeout(check_interval)
            if self.env.now < WARMUP_TIME:
                continue

            machine  = self.machines[DRIFT_MACHINE]
            total_p  = machine.stats.total_processed
            total_d  = machine.stats.total_defects

            delta_p  = total_p - self._prev_processed
            delta_d  = total_d - self._prev_defects

            self._prev_processed = total_p
            self._prev_defects   = total_d

            if delta_p < SPC_SAMPLE_SIZE:
                continue   # 樣本不足，跳過

            p_hat = delta_d / delta_p

            if p_hat > _UCL:
                # 超出管制界限 → 停機重新校正
                self.alarms += 1
                self.recalibrations += 1
                recal_start = self.env.now

                machine._is_down = True
                machine.status   = MachineStatus.CHANGEOVER
                yield self.env.timeout(RECALIBRATE_TIME)
                self.total_recal_time += self.env.now - recal_start

                # 重校後恢復正常不良率
                machine.config.defect_rate = NORMAL_DEFECT_RATE
                self.drift_active          = False
                machine._is_down           = False
                machine.repair_event.succeed()
                machine.repair_event = self.env.event()
                machine.status       = MachineStatus.IDLE

                # 重置計數器
                self._prev_processed = machine.stats.total_processed
                self._prev_defects   = machine.stats.total_defects


def run_scenario(label: str, enable_drift: bool, enable_spc: bool,
                 seed: int = RANDOM_SEED) -> dict:
    random.seed(seed)
    lc = LINE_CONFIG.copy()
    lc["sim_duration"] = SIM_DURATION
    lc["warmup_time"]  = WARMUP_TIME

    line = SPCLine(enable_drift=enable_drift, enable_spc=enable_spc, line_config=lc)

    stats = line.run()
    s     = stats.summary()
    snap  = stats.machine_snapshots.get(DRIFT_MACHINE, {})

    return {
        "label":         label,
        "fpy":           s["fpy_pct"],
        "throughput":    s["throughput_per_hour"],
        "avg_wip":       s["avg_wip"],
        "chip_oee":      round(snap.get("oee", 0) * 100, 1),
        "chip_failures": snap.get("failure_count", 0),
        "alarms":        getattr(line, "alarms", 0),
        "recalibrations":getattr(line, "recalibrations", 0),
        "recal_min":     round(getattr(line, "total_recal_time", 0) / 60, 1),
    }


def main():
    console = Console()
    console.print("\n[bold cyan]第十一章　SPC 統計製程管制[/bold cyan]")
    console.print(
        f"  高速機 正常不良率 p0 = {NORMAL_DEFECT_RATE}"
        f"   漂移後 p = {DRIFT_DEFECT_RATE}（漂移時間：sim {DRIFT_START_TIME/3600:.1f} hr 後）\n"
        f"  UCL = {round(_UCL, 4)}（n={SPC_SAMPLE_SIZE}）\n"
    )

    scenarios = [
        ("A: 無漂移（基準）",           False, False),
        ("B: 有漂移，無 SPC",           True,  False),
        ("C: 有漂移，SPC(n=20) 監控",   True,  True),
    ]
    results = [run_scenario(lbl, drift, spc) for lbl, drift, spc in scenarios]

    table = Table(
        title=f"製程漂移 × SPC 監控比較（漂移 {DRIFT_DEFECT_RATE} = {int(DRIFT_DEFECT_RATE/NORMAL_DEFECT_RATE)}x 正常值）",
        box=box.SIMPLE_HEAVY,
    )
    table.add_column("情境", style="cyan")
    table.add_column("FPY%", justify="right")
    table.add_column("產出率(pcs/hr)", justify="right")
    table.add_column("平均WIP", justify="right")
    table.add_column("高速機OEE%", justify="right")
    table.add_column("SPC警報次數", justify="right")
    table.add_column("重校次數", justify="right")
    table.add_column("重校停機(min)", justify="right")

    for r in results:
        fpy_color = "green" if r["fpy"] >= 98.5 else "yellow" if r["fpy"] >= 95 else "red"
        table.add_row(
            r["label"],
            f"[{fpy_color}]{r['fpy']}%[/{fpy_color}]",
            str(r["throughput"]),
            str(r["avg_wip"]),
            str(r["chip_oee"]),
            str(r["alarms"]),
            str(r["recalibrations"]),
            str(r["recal_min"]),
        )
    console.print(table)

    a, b, c = results
    fpy_loss   = round(a["fpy"] - b["fpy"], 2)
    fpy_rescue = round(c["fpy"] - b["fpy"], 2)

    console.print(
        f"\n[yellow]→ 結論：[/yellow]\n"
        f"  製程漂移導致 FPY 下降 {fpy_loss}%（情境 A→B）\n"
        f"  SPC 偵測並重校後，FPY 恢復 {fpy_rescue}%（情境 B→C）\n"
        f"  代價：重校停機 {c['recal_min']} min vs 漂移損失的大量不良品返工成本"
    )


if __name__ == "__main__":
    main()
