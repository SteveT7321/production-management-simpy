"""
SMT 產線主模擬流程

定義產線的 DES 邏輯：
1. PCB 依 inter-arrival 時間進板
2. 依序通過各站加工
3. AOI 後判定不良品是否返工
4. 收集統計數據

此模組被各個生產管理模組（M01~M07）繼承或直接使用。
"""

import simpy
import random
import threading
from typing import Dict, List, Optional, Callable

from simulation.config import MACHINE_CONFIGS, LINE_CONFIG, MachineConfig
from simulation.machines import Machine, MachineStatus
from simulation.pcb import PCB
from simulation.statistics import LineStats


# SMT 產線站點順序
STATION_ORDER = [
    "screen_printer",
    "spi",
    "chip_shooter",
    "flex_placer",
    "reflow_oven",
    "aoi",
]

MAX_REWORK_CYCLES = 2       # 超過此次數則報廢


class SMTLine:
    """
    SMT 電子組裝線 DES 模擬

    使用方式：
        line = SMTLine()
        line.run()
        line.stats.print_report()
    """

    def __init__(
        self,
        machine_configs: Optional[Dict[str, MachineConfig]] = None,
        line_config: Optional[dict] = None,
        state_callback: Optional[Callable] = None,
        enable_kanban: bool = False,
        kanban_limit: Optional[int] = None,
        enable_maintenance: bool = False,
    ):
        self.env = simpy.Environment()
        _base_configs = machine_configs or MACHINE_CONFIGS

        # PM 效果：MTBF 提升 2x（PM 讓設備壽命加倍，故障次數減半）
        # 計畫性保養停機時間由 _pm_process 另行累計
        PM_MTBF_FACTOR = 2.0
        if enable_maintenance:
            import copy as _copy
            self.machine_configs = {
                name: MachineConfig(**{**cfg.__dict__, "mtbf": cfg.mtbf * PM_MTBF_FACTOR})
                for name, cfg in _base_configs.items()
            }
        else:
            self.machine_configs = _base_configs

        self.line_config = line_config or LINE_CONFIG.copy()
        self.state_callback = state_callback

        self.enable_kanban = enable_kanban
        self.kanban_limit = kanban_limit or self.line_config.get("wip_kanban_limit", 5)
        self.enable_maintenance = enable_maintenance

        # 建立機台
        self.machines: Dict[str, Machine] = {
            name: Machine(self.env, cfg, state_callback=self._on_state_change)
            for name, cfg in self.machine_configs.items()
        }

        # Kanban：系統級 WIP 上限（進板前須取得許可，出板後釋放）
        self._system_kanban: Optional[simpy.Container] = None
        if self.enable_kanban:
            self._system_kanban = simpy.Container(
                self.env, capacity=self.kanban_limit, init=self.kanban_limit
            )

        self.stats = LineStats(
            sim_duration=self.line_config["sim_duration"],
            warmup_time=self.line_config["warmup_time"],
        )

        self._wip_count = 0
        self._wip_lock = threading.Lock()
        self._pcb_counter = 0

        # 外部狀態快照（供 Isaac Sim 橋接讀取）
        self._shared_state: Dict[str, dict] = {}
        self._state_lock = threading.Lock()

    # ── 狀態快照（Isaac Sim 橋接用）──────────────────────────────

    def get_shared_state(self) -> dict:
        """thread-safe 讀取整條產線狀態"""
        with self._state_lock:
            return {
                "time": round(self.env.now, 1),
                "wip": self._wip_count,
                "machines": {k: v.copy() for k, v in self._shared_state.items()},
            }

    def _on_state_change(self, machine_name: str, status: MachineStatus):
        with self._state_lock:
            self._shared_state[machine_name] = self.machines[machine_name].get_snapshot()

    # ── 模擬主流程 ────────────────────────────────────────────────

    def run(self, verbose: bool = False) -> LineStats:
        self.env.process(self._pcb_generator(verbose))
        self.env.process(self._wip_sampler())

        if self.enable_maintenance:
            for machine in self.machines.values():
                self.env.process(self._pm_process(machine))

        self.env.run(until=self.line_config["sim_duration"])

        # 取最終機台快照
        for name, machine in self.machines.items():
            self.stats.machine_snapshots[name] = machine.get_snapshot()

        return self.stats

    def _pcb_generator(self, verbose: bool):
        """依 inter-arrival 時間持續產生 PCB 進板
        若啟用 Kanban，進板前須等待系統有空位（Pull 系統）
        """
        while True:
            iat = random.expovariate(
                1.0 / self.line_config["inter_arrival_mean"]
            )
            yield self.env.timeout(iat)

            # Kanban Pull：等待系統空位，超過 WIP 上限則阻塞
            kanban_wait = 0.0
            if self._system_kanban is not None:
                wait_start = self.env.now
                yield self._system_kanban.get(1)
                kanban_wait = self.env.now - wait_start

            self._pcb_counter += 1
            pcb = PCB(
                pcb_id=self._pcb_counter,
                arrival_time=self.env.now,
            )
            pcb.kanban_wait_time = kanban_wait

            with self._wip_lock:
                self._wip_count += 1

            self.env.process(self._pcb_flow(pcb, verbose))

    def _pcb_flow(self, pcb: PCB, verbose: bool):
        """單片 PCB 流過整條產線"""
        after_warmup = self.env.now >= self.line_config["warmup_time"]

        for station_name in STATION_ORDER:
            machine = self.machines.get(station_name)
            if machine is None:
                continue

            pcb.record_enter(station_name, self.env.now)
            yield machine.process(pcb)
            pcb.record_exit(station_name, self.env.now)

            # SPI 攔截：印刷不良直接返印（不繼續往下）
            if station_name == "spi" and pcb.is_defect:
                pcb.is_defect = False
                pcb.rework_count += 1
                pcb.failed_station = "screen_printer"
                if verbose:
                    print(f"  [t={self.env.now:.0f}] PCB#{pcb.pcb_id} SPI 攔截，返回印刷")
                yield from self._rework_flow(pcb, "screen_printer", verbose)
                pcb.is_defect = False

            # AOI 攔截：回焊後不良品分流
            if station_name == "aoi" and pcb.is_defect:
                pcb.failed_station = "aoi"
                if pcb.rework_count >= MAX_REWORK_CYCLES:
                    pcb.is_scrapped = True
                    if verbose:
                        print(f"  [t={self.env.now:.0f}] PCB#{pcb.pcb_id} 報廢")
                    break
                else:
                    pcb.rework_count += 1
                    pcb.is_defect = False
                    if verbose:
                        print(f"  [t={self.env.now:.0f}] PCB#{pcb.pcb_id} AOI 攔截，送返工")
                    rework_station = self.line_config.get(
                        "rework_return_station", "flex_placer"
                    )
                    yield from self._rework_flow(pcb, rework_station, verbose)

        # 完工：釋放 Kanban 許可讓下一片進板
        if self._system_kanban is not None:
            yield self._system_kanban.put(1)

        pcb.finish_time = self.env.now
        with self._wip_lock:
            self._wip_count -= 1

        if after_warmup:
            if pcb.is_scrapped:
                self.stats.scrapped_pcbs.append(pcb)
            else:
                self.stats.completed_pcbs.append(pcb)

    def _rework_flow(self, pcb: PCB, start_station: str, verbose: bool):
        """從指定站點重新加工到 AOI"""
        rework_stations = STATION_ORDER[STATION_ORDER.index(start_station):]
        for station_name in rework_stations:
            machine = self.machines.get(station_name)
            if machine is None:
                continue
            pcb.record_enter(f"{station_name}_rework", self.env.now)
            yield machine.process(pcb)
            pcb.record_exit(f"{station_name}_rework", self.env.now)

    # ── WIP 取樣（Little's Law）────────────────────────────────────

    def _wip_sampler(self):
        """每 60 秒取樣一次 WIP，供 Little's Law 驗證"""
        while True:
            yield self.env.timeout(60.0)
            if self.env.now >= self.line_config["warmup_time"]:
                self.stats.wip_samples.append((self.env.now, self._wip_count))

    # ── 預防保養（M07）────────────────────────────────────────────

    def _pm_process(self, machine: Machine):
        """
        定期預防保養程序
        PM 間隔 = MTBF × 0.8（在故障前先介入）

        PM 效果建模方式：
          - 機台 MTBF 已在 __init__ 乘以 pm_mtbf_factor（預設 2x）
            → 直接反映「PM 讓設備壽命加倍、故障次數減半」
          - 本程序僅負責計畫性停機時間（佔 MTTR × 0.3）
            → 反映 PM 的「計畫性成本」
        """
        pm_interval = machine.config.mtbf * 0.8
        pm_duration = machine.config.mttr_mean * 0.3   # PM 比緊急修復快（約 30% MTTR）

        while True:
            yield self.env.timeout(pm_interval)

            # 若目前正在故障修復中，跳過此次 PM
            if machine._is_down:
                continue

            # 計畫性停機：阻塞機台加工
            machine._is_down = True
            machine.status = MachineStatus.CHANGEOVER
            pm_start = self.env.now

            yield self.env.timeout(pm_duration)

            machine.stats.changeover_time += self.env.now - pm_start
            machine._is_down = False
            machine.repair_event.succeed()
            machine.repair_event = machine.env.event()
            machine.status = MachineStatus.IDLE


# ── 獨立執行入口 ────────────────────────────────────────────────────

if __name__ == "__main__":
    import random
    random.seed(42)

    print("執行 SMT 產線基礎模擬（8小時，含1小時暖機）...")
    line = SMTLine()
    line.run(verbose=False)
    line.stats.print_report()
