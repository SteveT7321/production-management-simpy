"""
SMT 產線機台參數設定
所有時間單位：秒（seconds）
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MachineConfig:
    name: str
    display_name: str
    cycle_time_mean: float      # 平均加工時間 (s)
    cycle_time_std: float       # 加工時間標準差 (s)
    mtbf: float                 # Mean Time Between Failures (s)
    mttr_mean: float            # Mean Time To Repair (s)
    mttr_std: float             # MTTR 標準差 (s)
    defect_rate: float          # 不良率 0.0 ~ 1.0
    changeover_time: float      # 換線時間 (s)，SMED 模組用
    num_resources: int = 1      # 機台數量


# ── 預設 SMT 產線參數 ──────────────────────────────────────────────
# 參考業界 Yamaha / Fuji 設備規格與產業經驗值

MACHINE_CONFIGS: Dict[str, MachineConfig] = {
    "screen_printer": MachineConfig(
        name="screen_printer",
        display_name="錫膏印刷機",
        cycle_time_mean=20.0,
        cycle_time_std=2.0,
        mtbf=7200.0,    # 2 小時
        mttr_mean=600.0,  # 10 分鐘
        mttr_std=120.0,
        defect_rate=0.005,
        changeover_time=1800.0,  # 30 分鐘
    ),
    "spi": MachineConfig(
        name="spi",
        display_name="SPI 錫膏檢測",
        cycle_time_mean=15.0,
        cycle_time_std=1.0,
        mtbf=14400.0,   # 4 小時
        mttr_mean=300.0,
        mttr_std=60.0,
        defect_rate=0.0,   # 檢測站不產生不良，只篩選
        changeover_time=600.0,
    ),
    "chip_shooter": MachineConfig(
        name="chip_shooter",
        display_name="高速機",
        cycle_time_mean=8.0,    # 高速機最快，但通常是瓶頸（零件多）
        cycle_time_std=1.5,
        mtbf=3600.0,    # 1 小時（高速機故障率較高）
        mttr_mean=900.0,  # 15 分鐘
        mttr_std=180.0,
        defect_rate=0.002,
        changeover_time=2400.0,  # 40 分鐘（換料多）
    ),
    "flex_placer": MachineConfig(
        name="flex_placer",
        display_name="泛用機",
        cycle_time_mean=25.0,   # 放置大型/異形件，速度較慢
        cycle_time_std=3.0,
        mtbf=5400.0,
        mttr_mean=720.0,
        mttr_std=150.0,
        defect_rate=0.003,
        changeover_time=3000.0,  # 50 分鐘
    ),
    "reflow_oven": MachineConfig(
        name="reflow_oven",
        display_name="回焊爐",
        cycle_time_mean=45.0,   # 爐長 / 鏈速決定，固定較長
        cycle_time_std=1.0,
        mtbf=28800.0,   # 8 小時（很穩定）
        mttr_mean=1800.0,  # 30 分鐘（需降溫）
        mttr_std=300.0,
        defect_rate=0.001,
        changeover_time=3600.0,  # 換profile 60 分鐘
        num_resources=6,    # 隧道爐：同時可承載多片 PCB（管道模型）
    ),
    "aoi": MachineConfig(
        name="aoi",
        display_name="AOI 自動光學檢測",
        cycle_time_mean=30.0,
        cycle_time_std=2.0,
        mtbf=18000.0,   # 5 小時
        mttr_mean=600.0,
        mttr_std=120.0,
        defect_rate=0.0,   # 檢測站
        changeover_time=1200.0,
    ),
}

# 產線整體參數
LINE_CONFIG = {
    "warmup_time": 3600.0,          # 暖機時間 1 小時，統計不計入
    "sim_duration": 28800.0,        # 模擬時長 8 小時（一個班）
    "inter_arrival_mean": 28.0,     # PCB 進板間隔（s）— 略大於泛用機 cycle_time，維持產線穩定
    "rework_return_station": "flex_placer",  # 不良品返工站
    "wip_kanban_limit": 5,          # M06 Kanban WIP 上限（每站）
}
