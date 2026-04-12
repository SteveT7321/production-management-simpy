# SMT Line Digital Twin — SimPy 生產管理模擬

SMT 電子組裝線數位孿生專案。
SimPy DES 模擬引擎，7 個生產管理知識模組。

## Conda 環境

```bash
conda activate smt_twin
```

## 執行

```bash
# 快速驗證（基礎模擬報告）
conda run -n smt_twin python check.py

# 各生產管理模組
conda run -n smt_twin python -m simulation.modules.m01_baseline
conda run -n smt_twin python -m simulation.modules.m02_bottleneck
conda run -n smt_twin python -m simulation.modules.m03_oee
conda run -n smt_twin python -m simulation.modules.m04_scheduling
conda run -n smt_twin python -m simulation.modules.m05_quality
conda run -n smt_twin python -m simulation.modules.m06_kanban
conda run -n smt_twin python -m simulation.modules.m07_maintenance

# 測試
conda run -n smt_twin python -m pytest tests/ -v
```

## 專案結構

```
simulation/
  config.py          機台參數（Yamaha/Fuji 業界規格）
  machines.py        Machine class（故障/換線/統計）
  pcb.py             PCB 生命週期
  statistics.py      OEE/Throughput/WIP/Little's Law
  smt_line.py        主產線流程（含 Kanban/PM）
  modules/           7 個生產管理模組（各自獨立可執行）
    m01_baseline.py  Takt Time、Little's Law
    m02_bottleneck.py  TOC 約束理論
    m03_oee.py       OEE（可用率×效率×品質）
    m04_scheduling.py  SMED 換線、批量大小
    m05_quality.py   FPY 串聯、Rework Loop
    m06_kanban.py    WIP 上限、Pull 系統
    m07_maintenance.py  PM 排程、MTTR 優化

tests/
  test_simulation.py

check.py             快速驗證腳本
requirements.txt
```

## SMT 產線站點

```
錫膏印刷 → SPI → 高速機 → 泛用機 → 回焊爐 → AOI
 ~20s      ~15s   ~8s*    ~25s*    ~45s     ~30s
                 *主瓶頸區
```

## 7 個生產管理模組

| 模組 | 知識主題 | 驗證指標 |
|------|---------|---------|
| M01 Baseline | Takt Time、Little's Law | WIP / Throughput |
| M02 Bottleneck | TOC 約束理論 | 瓶頸站 Utilization |
| M03 OEE | Availability×Performance×Quality | OEE % |
| M04 Scheduling | SMED 換線、批量大小 | 換線損失時間 |
| M05 Quality | FPY 串聯、Rework Loop | 良率 % |
| M06 Kanban | WIP 上限、Pull 系統 | WIP 上限效果 |
| M07 Maintenance | PM 排程、MTTR 優化 | 停機時間比較 |
