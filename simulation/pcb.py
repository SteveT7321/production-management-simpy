"""
PCB 實體（產品）

每片 PCB 記錄完整的生命週期，包含：
- 進板時間、各站完工時間
- 是否不良品、是否返工
- 最終 cycle time

這些資料是計算 Lead Time、WIP、FPY 的基礎
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PCB:
    pcb_id: int
    arrival_time: float             # 進板時間
    product_type: str = "default"   # 機種（M04 換線用）

    # 各站時間戳
    station_enter: Dict[str, float] = field(default_factory=dict)
    station_exit: Dict[str, float] = field(default_factory=dict)

    # 品質狀態
    is_defect: bool = False
    rework_count: int = 0
    failed_station: Optional[str] = None   # AOI 攔截到哪站的問題

    # 完工
    finish_time: Optional[float] = None
    is_scrapped: bool = False               # 超過返工次數則報廢

    # Kanban（M06）
    kanban_wait_time: float = 0.0           # 被 Kanban 上限阻擋的累積時間

    @property
    def cycle_time(self) -> Optional[float]:
        if self.finish_time is None:
            return None
        return self.finish_time - self.arrival_time

    @property
    def queue_time(self) -> float:
        """各站等待時間總和"""
        total = 0.0
        for station, enter in self.station_enter.items():
            exit_t = self.station_exit.get(station)
            if exit_t is not None:
                total += exit_t - enter
        return max(0.0, total - self.processing_time)

    @property
    def processing_time(self) -> float:
        """純加工時間（不含等待）"""
        total = 0.0
        for station, exit_t in self.station_exit.items():
            enter = self.station_enter.get(station, exit_t)
            total += exit_t - enter
        return total

    def record_enter(self, station: str, time: float):
        self.station_enter[station] = time

    def record_exit(self, station: str, time: float):
        self.station_exit[station] = time

    def to_dict(self) -> dict:
        return {
            "pcb_id": self.pcb_id,
            "product_type": self.product_type,
            "arrival_time": round(self.arrival_time, 2),
            "finish_time": round(self.finish_time, 2) if self.finish_time else None,
            "cycle_time": round(self.cycle_time, 2) if self.cycle_time else None,
            "is_defect": self.is_defect,
            "rework_count": self.rework_count,
            "is_scrapped": self.is_scrapped,
        }
