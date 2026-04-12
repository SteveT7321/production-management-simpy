# SMT Production Line — SimPy 生產管理模擬

以 **SimPy 離散事件模擬（DES）** 建構的 SMT 電子組裝線數位孿生，  
包含 7 個生產管理知識模組，各自獨立可執行並輸出量化報告。

---

## 產線架構

```
錫膏印刷 → SPI → 高速機 → 泛用機 → 回焊爐 → AOI
  ~20s     ~15s   ~8s*    ~25s*    ~45s     ~30s
                 * 主瓶頸區
```

機台參數參考 **Yamaha / Fuji** 業界規格：含加工時間、MTBF、MTTR、不良率、換線時間。

---

## 7 個生產管理模組

| 模組 | 知識主題 | 核心指標 |
|------|---------|---------|
| **M01 Baseline** | Takt Time、Throughput、Little's Law | WIP、產出率 |
| **M02 Bottleneck** | TOC 約束理論、瓶頸改善對比 | Utilization % |
| **M03 OEE** | Availability × Performance × Quality | OEE % |
| **M04 Scheduling** | SMED 換線縮短、批量大小優化 | 換線損失時間 |
| **M05 Quality** | FPY 串聯計算、Rework Loop | 良率 %、WIP 影響 |
| **M06 Kanban** | WIP 上限、Pull 系統 vs Push 系統 | WIP 上限效果 |
| **M07 Maintenance** | PM 排程、預防保養 vs 故障停機 | 停機時間比較 |

---

## 快速開始

```bash
# 建立環境
conda create -n smt_twin python=3.10 -y
conda activate smt_twin
pip install -r requirements.txt

# 快速驗證（產線基本報告）
python check.py

# 執行各模組
python -m simulation.modules.m01_baseline
python -m simulation.modules.m02_bottleneck
python -m simulation.modules.m03_oee
python -m simulation.modules.m04_scheduling
python -m simulation.modules.m05_quality
python -m simulation.modules.m06_kanban
python -m simulation.modules.m07_maintenance

# 執行測試
python -m pytest tests/ -v
```

---

## 模組輸出範例

**M01 Baseline**
```
Takt Time: 36.0 s  （客戶需求 100.0 pcs/hr）
實際產出率: 102.4 pcs/hr  ✓
平均 WIP: 101.1 pcs
瓶頸站點: aoi
```

**M02 Bottleneck（TOC 改善對比）**
```
情境 A（原始）：Throughput 102.4 pcs/hr，瓶頸 chip_shooter，Utilization 92%
情境 B（改善瓶頸）：Throughput +15%
情境 C（改善非瓶頸）：Throughput ≈ 不變
```

**M03 OEE**
```
screen_printer: OEE 66.7%  稼動 68.6%
chip_shooter:   OEE 23.0%  稼動 27.2%
aoi:            OEE 86.9%  稼動 89.3%
```

---

## 專案結構

```
simulation/
├── config.py          機台參數（Yamaha/Fuji 業界規格）
├── machines.py        Machine class（故障/換線/OEE 統計）
├── pcb.py             PCB 生命週期追蹤
├── smt_line.py        主產線 SimPy 流程
├── statistics.py      OEE / Throughput / WIP / Little's Law
└── modules/
    ├── m01_baseline.py
    ├── m02_bottleneck.py
    ├── m03_oee.py
    ├── m04_scheduling.py
    ├── m05_quality.py
    ├── m06_kanban.py
    └── m07_maintenance.py

tests/
└── test_simulation.py

check.py               快速驗證腳本
```

---

## 技術棧

- **Python 3.10**
- **SimPy 4.x** — 離散事件模擬引擎
- **NumPy / Pandas** — 統計計算
- **Rich** — 終端輸出格式化
