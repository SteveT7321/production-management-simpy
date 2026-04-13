"""
SMT 機台 SimPy Resource 封裝

每台機台追蹤：
- 狀態：idle / processing / down / changeover
- 累積統計：加工時間、故障時間、換線時間
- 即時狀態供 Isaac Sim 橋接讀取
"""

import simpy
import random
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable
from simulation.config import MachineConfig


class MachineStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    DOWN = "down"
    CHANGEOVER = "changeover"
    BLOCKED = "blocked"      # 下游滿，無法放板


@dataclass
class MachineStats:
    total_processed: int = 0
    total_defects: int = 0
    busy_time: float = 0.0
    down_time: float = 0.0
    changeover_time: float = 0.0
    failure_count: int = 0
    queue_length_samples: list = field(default_factory=list)

    @property
    def availability(self) -> float:
        total = self.busy_time + self.down_time + self.changeover_time
        if total == 0:
            return 1.0
        return self.busy_time / total

    @property
    def quality_rate(self) -> float:
        if self.total_processed == 0:
            return 1.0
        return 1.0 - (self.total_defects / self.total_processed)


class Machine:
    """
    SimPy-based 機台模型

    負責：
    1. 加工 PCB（consume cycle_time）
    2. 隨機故障（MTBF/MTTR exponential）
    3. 狀態追蹤供 Isaac Sim 讀取
    """

    def __init__(self, env: simpy.Environment, config: MachineConfig,
                 state_callback: Optional[Callable] = None):
        self.env = env
        self.config = config
        self.name = config.name
        self.display_name = config.display_name

        self.resource = simpy.Resource(env, capacity=config.num_resources)
        self.stats = MachineStats()
        self._status = MachineStatus.IDLE
        self._lock = threading.Lock()

        # 故障旗標：故障時 down_event 被觸發
        self.down_event = env.event()
        self.repair_event = env.event()
        self._is_down = False

        self._state_callback = state_callback

        # 啟動背景故障程序（保留引用供 PM interrupt 使用）
        self._failure_gen_process = env.process(self._failure_process())

    # ── 狀態管理 ──────────────────────────────────────────────────

    @property
    def status(self) -> MachineStatus:
        return self._status

    @status.setter
    def status(self, value: MachineStatus):
        with self._lock:
            self._status = value
        if self._state_callback:
            self._state_callback(self.name, value)

    def get_snapshot(self) -> dict:
        """供 Isaac Sim 橋接讀取的即時快照（thread-safe）"""
        with self._lock:
            num_res = self.config.num_resources
            elapsed = max(self.env.now, 1)
            utilization = self.stats.busy_time / (elapsed * num_res)
            return {
                "name": self.name,
                "display_name": self.display_name,
                "status": self._status.value,
                "queue": len(self.resource.queue),
                "utilization": round(min(utilization, 1.0), 3),
                "total_processed": self.stats.total_processed,
                "failure_count": self.stats.failure_count,
                "oee": round(self._calc_oee(), 3),
            }

    def _calc_oee(self) -> float:
        num_res = self.config.num_resources
        elapsed = max(self.env.now, 1)
        # 多資源機台：busy_time 為所有資源累加，需除以 num_resources
        availability = 1.0 - (self.stats.down_time / elapsed)
        performance = min(self.stats.busy_time / (elapsed * num_res), 1.0)
        quality = self.stats.quality_rate
        return max(0.0, availability * performance * quality)

    # ── 加工流程 ──────────────────────────────────────────────────

    def process(self, pcb) -> simpy.events.Event:
        """
        請求機台加工一片 PCB。
        若機台故障，等待修復完成後才加工。
        回傳 SimPy generator，供 smt_line.py yield。
        """
        return self.env.process(self._process_gen(pcb))

    def _process_gen(self, pcb):
        # 等待機台資源空出
        with self.resource.request() as req:
            yield req

            # 若此時機台正在故障，等修好
            while self._is_down:
                yield self.repair_event

            self.status = MachineStatus.PROCESSING
            start = self.env.now

            # 加工時間（常態分佈，下限 0.1s）
            ct = max(0.1, random.gauss(
                self.config.cycle_time_mean,
                self.config.cycle_time_std
            ))

            yield self.env.timeout(ct)

            # 判定是否產生不良品
            is_defect = random.random() < self.config.defect_rate
            if is_defect:
                self.stats.total_defects += 1
                pcb.is_defect = True

            self.stats.total_processed += 1
            self.stats.busy_time += self.env.now - start
            self.status = MachineStatus.IDLE

    # ── 故障流程 ──────────────────────────────────────────────────

    def _failure_process(self):
        """背景常駐：指數分佈 MTBF/MTTR 隨機故障循環
        若被 PM interrupt：
          - 在 TTF 等待期間：重置計時器（PM 預防了這次故障）
          - 在修復等待期間：直接忽略（修復不被 PM 中斷）
        """
        while True:
            # ── 等待下次故障 ──
            try:
                ttf = random.expovariate(1.0 / self.config.mtbf)
                yield self.env.timeout(ttf)
            except simpy.Interrupt:
                # PM 重置 TTF 計時器：本次故障被預防，重新等待
                continue

            # ── 發生故障 ──
            self._is_down = True
            self.stats.failure_count += 1
            self.status = MachineStatus.DOWN
            down_start = self.env.now

            ttr = max(60.0, random.gauss(
                self.config.mttr_mean,
                self.config.mttr_std
            ))

            try:
                yield self.env.timeout(ttr)
            except simpy.Interrupt:
                # PM interrupt 在修復期間到來：忽略，繼續完成修復
                pass

            self.stats.down_time += self.env.now - down_start
            self._is_down = False

            # 觸發修復事件，喚醒等待中的加工
            self.repair_event.succeed()
            self.repair_event = self.env.event()
            self.status = MachineStatus.IDLE

    # ── 換線（SMED 模組用）────────────────────────────────────────

    def do_changeover(self, duration_override: Optional[float] = None):
        """執行換線，期間機台不可用"""
        return self.env.process(self._changeover_gen(duration_override))

    def _changeover_gen(self, duration_override):
        self.status = MachineStatus.CHANGEOVER
        start = self.env.now
        duration = duration_override or self.config.changeover_time
        yield self.env.timeout(duration)
        self.stats.changeover_time += self.env.now - start
        self.status = MachineStatus.IDLE
