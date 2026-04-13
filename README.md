# SMT 生產管理模擬教學

以 **SimPy 離散事件模擬（DES）** 建構的 SMT 電子組裝線數位孿生，  
涵蓋 **12 個模擬章節** + **6 個靜態分析工具**，每個章節包含概念說明、公式推導、模擬實驗與結果解讀。

---

## 產線架構

```
錫膏印刷 → SPI → 高速機 → 泛用機 → 回焊爐（6槽）→ AOI
  ~20 s    ~15 s   ~8 s   ~25 s      ~45 s          ~30 s
                                        ↑
                             AOI 攔截不良品 → 返工迴路（回泛用機重跑）
```

機台參數參考 Yamaha / Fuji 業界規格（MTBF、MTTR、不良率、換線時間）。

---

## 整體運行架構

```
chapters/ch0X/simulation.py      ← 使用者執行的入口（各章節獨立）
        │
        │  import
        ▼
simulation/                      ← 核心模擬引擎（共用，不直接執行）
  ├── config.py                     機台參數（cycle time / MTBF / 不良率 / 換線時間）
  ├── machines.py                   Machine class（加工 / 故障 / OEE 統計）
  ├── pcb.py                        PCB class（產品生命週期紀錄）
  ├── smt_line.py                   SMTLine class（SimPy DES 主流程）
  └── statistics.py                 LineStats class（統計彙整 / Little's Law / OEE）
        │
        │  執行結果
        ▼
     LineStats                    ← 模擬結束後回傳，包含所有統計數據
```

### 一次模擬的執行流程

```
SMTLine.__init__()
  ├─ 讀取 config.py 機台參數
  ├─ 建立 6 台 Machine（各自啟動背景故障程序 _failure_process）
  ├─ 建立 LineStats 統計容器
  └─ 若啟用 Kanban：建立 simpy.Container 控制系統級 WIP 上限

SMTLine.run()
  ├─ 啟動 _pcb_generator：依指數分佈 inter-arrival 持續產生 PCB
  │     └─ 若 Kanban 啟用：PCB 進板前必須先等系統有空位（Pull 訊號）
  ├─ 啟動 _wip_sampler：每 60 秒記錄一次 WIP（供 Little's Law）
  ├─ 若啟用 PM：為每台機台啟動 _pm_process（定期計畫性保養）
  └─ env.run(until=28800)  ← 跑滿 8 小時

每片 PCB 的流程（_pcb_flow）：
  進板 → 錫膏印刷 → SPI → 高速機 → 泛用機 → 回焊爐 → AOI
           │                                         │
      SPI 攔截不良 ──────────────────────────────────┘
      返回印刷重跑                    AOI 攔截不良 → 返工迴路（回泛用機）
                                     超過 2 次返工 → 報廢

模擬結束 → LineStats.summary() 輸出統計
```

### 各模組職責

| 模組 | 職責 | 關鍵類別 / 函式 |
|------|------|---------------|
| `config.py` | 定義所有機台的靜態參數 | `MachineConfig`, `MACHINE_CONFIGS`, `LINE_CONFIG` |
| `machines.py` | 單台機台的 SimPy 行為（加工/故障/換線） | `Machine`, `MachineStats`, `MachineStatus` |
| `pcb.py` | 追蹤一片 PCB 從進板到完工的完整紀錄 | `PCB.cycle_time`, `rework_count`, `kanban_wait_time` |
| `smt_line.py` | 整條產線的 SimPy 流程控制 | `SMTLine.run()`, `_pcb_flow()`, `_pm_process()` |
| `statistics.py` | 模擬結束後的統計計算與輸出 | `LineStats.summary()`, `throughput`, `fpy`, `littles_law_check` |

---

## 章節目錄

| 章節 | 知識主題 | 核心問題 |
|------|---------|---------|
| [第一章](chapters/ch01_takt_time/) | Takt Time、Little's Law | 我們跟得上客戶需求嗎？ |
| [第二章](chapters/ch02_bottleneck/) | Theory of Constraints（TOC） | 改善哪裡才真的有效？ |
| [第三章](chapters/ch03_oee/) | OEE = Availability × Performance × Quality | 設備時間流失在哪裡？ |
| [第四章](chapters/ch04_smed/) | SMED 快速換線 | 如何讓小批量生產可行？ |
| [第五章](chapters/ch05_quality/) | FPY 串聯計算、Rework Loop | 不良率如何影響整線？ |
| [第六章](chapters/ch06_kanban/) | Kanban、Push vs Pull | 如何控制在製品數量？ |
| [第七章](chapters/ch07_maintenance/) | PM 預防保養 vs 故障停機 | 預防保養划算嗎？ |
| [第八章](chapters/ch08_scheduling/) | FIFO / SPT / EDD 排程規則 | 哪一片訂單先做效益最高？ |
| [第九章](chapters/ch09_heijunka/) | Heijunka 均衡生產 | 如何讓產線節拍穩定？ |
| [第十章](chapters/ch10_safety_stock/) | 安全庫存、再訂購點（ROP） | 要備多少料才不會斷線？ |
| [第十一章](chapters/ch11_spc/) | SPC p 管制圖、製程漂移偵測 | 製程悄悄變差時如何第一時間發現？ |
| [第十二章](chapters/ch12_conwip/) | CONWIP vs 逐站 Kanban | 全域 WIP 上限和逐站限制有什麼不同？ |

每個章節資料夾：

```
chapters/ch0N_xxx/
├── README.md      ← 概念說明、核心公式、結果解讀、管理意涵
└── simulation.py  ← 可直接執行的模擬程式（import 核心引擎並設定情境參數）
```

---

## 靜態分析工具（concepts/）

有些生產管理知識用公式就能算清楚，不需要 SimPy 模擬。
這類工具獨立放在 `concepts/` 目錄，執行後輸出計算結果與管理意涵。

| 目錄 | 主題 | 核心方法 |
|------|------|---------|
| [c01_5s](concepts/c01_5s/) | 5S 評核工具 | 分數 → 效率影射 |
| [c02_vsm](concepts/c02_vsm/) | VSM 價值流圖分析 | PCE = VA / Lead Time |
| [c03_eoq](concepts/c03_eoq/) | EOQ 經濟訂購量 | sqrt(2DS/H) |
| [c04_mrp](concepts/c04_mrp/) | MRP 物料需求計畫 | BOM 展開 + 淨需求計算 |
| [c05_six_sigma](concepts/c05_six_sigma/) | Six Sigma 製程能力 | Cp / Cpk / DPMO |
| [c06_aql](concepts/c06_aql/) | AQL 抽樣計畫 | ANSI Z1.4 + OC 曲線 |

詳細說明：[concepts/README.md](concepts/README.md)

---

## 快速開始

```bash
# 建立環境
conda create -n smt_twin python=3.10 -y
conda activate smt_twin
pip install -r requirements.txt

# 執行任一章節（直接看該知識點的模擬實驗）
python chapters/ch01_takt_time/simulation.py
python chapters/ch02_bottleneck/simulation.py
python chapters/ch03_oee/simulation.py
python chapters/ch04_smed/simulation.py
python chapters/ch05_quality/simulation.py
python chapters/ch06_kanban/simulation.py
python chapters/ch07_maintenance/simulation.py
python chapters/ch08_scheduling/simulation.py
python chapters/ch09_heijunka/simulation.py
python chapters/ch10_safety_stock/simulation.py
python chapters/ch11_spc/simulation.py
python chapters/ch12_conwip/simulation.py

# 靜態分析工具（不需要 SimPy）
python concepts/c01_5s/calculator.py
python concepts/c02_vsm/calculator.py
python concepts/c03_eoq/calculator.py
python concepts/c04_mrp/calculator.py
python concepts/c05_six_sigma/calculator.py
python concepts/c06_aql/calculator.py

# 快速驗證整條產線（輸出基礎統計，確認環境設定正確）
python check.py

# 執行單元測試（驗證核心邏輯沒有被改壞）
python -m pytest tests/ -v
```

---

## 各章節模擬結果預覽

### 第一章　Takt Time（Takt Time = 36 s，客戶需求 100 pcs/hr）

```
Takt Time          36.0 s/pcs
實際 Cycle Time    ~35 s/pcs
實際產出率         102.4 pcs/hr  ✓ 達標
平均 WIP           101.1 pcs
瓶頸站點           AOI
```

### 第二章　TOC 瓶頸分析（改善瓶頸 vs 改善非瓶頸）

```
情境                          產出率      vs 原始
A: 原始產線                   102.4 pcs/hr    —
B: 改善瓶頸（高速機+20%）     106.7 pcs/hr   ＋4.3
C: 改善非瓶頸（泛用機+20%）    99.0 pcs/hr   ＋0
```
→ 改善非瓶頸幾乎無效，驗證 TOC 核心洞見

### 第三章　OEE（世界級標準 ≥ 85%）

```
情境                      整體 OEE    產出率
A: 原始（基準）             ~55%       102 pcs/hr
B: MTBF×2（故障減半）       ~72%       112 pcs/hr
C: 不良率×0.5（品質↑）      ~56%       103 pcs/hr
```
→ Availability（故障）是最大損失來源

### 第四章　SMED 快速換線

```
情境                          換線損失    產出率
A: 大批量（50片）              6.67 hr    21 pcs/hr
B: 小批量（10片，未改善）        8.0 hr     4 pcs/hr
C: 小批量 ＋ SMED（-80%）       6.7 hr    20 pcs/hr
```
→ SMED 讓小批量生產具備大批量效率

### 第五章　FPY 品質管理（串聯公式驗證）

```
情境                  理論 FPY    實際 FPY    平均 WIP
A: 原始               98.9%       99.0%       101 pcs
B: 不良率×0.5         99.45%      99.9%        92 pcs
C: 不良率×2           97.8%       97.4%        92 pcs
```
→ 理論值與模擬值吻合；品質惡化連鎖影響 WIP

### 第六章　Kanban WIP 控制

```
情境                    平均 WIP    Cycle Time    產出率
A: 無 Kanban（Push）    101 pcs     3095 s        102 pcs/hr
B: Kanban limit=20       18 pcs      688 s         91 pcs/hr  ← 太緊
C: Kanban limit=50       47 pcs     1559 s        102 pcs/hr  ← 推薦
D: Kanban limit=80       75 pcs     2463 s         99 pcs/hr
```
→ limit=50：WIP -53%、Cycle Time -50%，產出率幾乎不變

### 第七章　預防保養（PM）

```
情境                故障次數    產出率        平均 WIP
A: 無 PM              21        102 pcs/hr    101 pcs
B: 有 PM（MTBF×0.8）   9        109 pcs/hr     90 pcs
```
→ PM 使故障減少 57%，產出率 ＋6.9 pcs/hr

### 第八章　排程規則（FIFO / SPT / EDD）

```
情境    整體準時率   平均延誤(s)   最大延誤(s)   平均流程時間(s)
FIFO      84.5%         9.9          240.0          62.4
SPT       92.5%        10.4         1058.0          50.8  ← 流程時間最短（C 型犧牲）
EDD       86.6%         8.6          223.3          60.1  ← 最大延誤最小
```
→ SPT 最小化平均等待；EDD 最小化最大延誤；FIFO 公平但兩者皆非最優

### 第九章　Heijunka 均衡生產（需求 80 pcs/hr）

```
情境                   產出率     平均WIP   WIP標準差   WIP峰值   CT標準差
A: 批量（每小時集中）   77 pcs/hr   36.9      28.1        82        841 s
B: Heijunka 均衡       77 pcs/hr   14.4       8.6        31        397 s
```
→ WIP 標準差 -69%，CT 標準差 -53%；產出率不變，流動更穩定

### 第十章　安全庫存（補料 Lead Time = 30 min）

```
情境                      斷料次數   斷料停機   產出率
A: 無安全庫存（ROP=0）       5次     148 min   77 pcs/hr
B: 安全庫存 1x LTD            1次       3 min  100 pcs/hr
C: 安全庫存 2x LTD            0次       0 min  102 pcs/hr
```
→ 安全庫存 2x Lead Time Demand 可消除斷料停機

### 第十一章　SPC 管制圖（chip_shooter 不良率漂移 25x）

```
情境                      FPY%    產出率
A: 無漂移（基準）           99.02%   102
B: 有漂移，無 SPC           95.55%    93  ← 問題惡化無人知
C: 有漂移，SPC(n=20)        98.74%   102  ← SPC 偵測並重校
```
→ 製程漂移導致 FPY 下降 3.5%；SPC 在 ~4 分鐘內偵測並重校，FPY 幾乎恢復

### 第十二章　CONWIP vs 逐站 Kanban

```
情境                       平均WIP   WIP降幅   CT降幅    產出率
A: Push（無限制）            101        —         —       102
B: CONWIP（上限=50）          47      -53%      -50%      102  ← 推薦起點
C: 逐站 Kanban（每站=10）     77      -24%      -21%       98  ← 略緊
D: 逐站 Kanban（每站=15）     99       -2%       -4%      103  ← 幾乎無效
```
→ CONWIP 實作最簡單且效果最好；逐站 Kanban 提供局部可視性但設定複雜

---

## 專案結構

```
warehouse_omniverse/
│
├── chapters/                  教學章節（每章獨立執行）
│   ├── ch01_takt_time/
│   │   ├── README.md          概念、公式、結果解讀、管理意涵
│   │   └── simulation.py      import 核心引擎，設定情境參數，輸出比較表
│   ├── ch02_bottleneck/       TOC 瓶頸理論
│   ├── ch03_oee/              OEE 三維分解
│   ├── ch04_smed/             SMED 快速換線
│   ├── ch05_quality/          FPY 串聯計算
│   ├── ch06_kanban/           Kanban Push vs Pull
│   ├── ch07_maintenance/      PM 預防保養
│   ├── ch08_scheduling/       FIFO / SPT / EDD 排程規則
│   ├── ch09_heijunka/         Heijunka 均衡生產
│   ├── ch10_safety_stock/     安全庫存 / ROP 再訂購點
│   ├── ch11_spc/              SPC p 管制圖 / 製程漂移偵測
│   └── ch12_conwip/           CONWIP vs 逐站 Kanban
│
├── simulation/                核心模擬引擎（被 chapters 共用）
│   ├── config.py              機台參數（Yamaha/Fuji 業界規格）
│   ├── machines.py            Machine class（故障 / 換線 / OEE 統計）
│   ├── pcb.py                 PCB 生命週期紀錄
│   ├── smt_line.py            主產線 SimPy 流程（含 Kanban / PM）
│   └── statistics.py          OEE / Throughput / WIP / Little's Law
│
├── concepts/                  靜態分析工具（公式計算，不需要 SimPy）
│   ├── README.md              各工具說明與學習路徑
│   ├── c01_5s/                5S 評核評分工具
│   ├── c02_vsm/               VSM 價值流圖 PCE 計算
│   ├── c03_eoq/               EOQ 經濟訂購量
│   ├── c04_mrp/               MRP 物料需求計畫（BOM 展開）
│   ├── c05_six_sigma/         Cp / Cpk / DPMO / Sigma Level
│   └── c06_aql/               AQL 抽樣計畫 + OC 曲線
│
├── tests/
│   └── test_simulation.py     單元測試（8 項，驗證核心引擎邏輯）
├── check.py                   快速驗證腳本（確認環境設定正確）
└── requirements.txt
```

---

## 技術棧

| 工具 | 用途 |
|------|------|
| Python 3.10 | |
| SimPy 4.x | 離散事件模擬引擎 |
| NumPy / Pandas | 統計計算 |
| Rich | 終端格式化輸出 |
| pytest | 單元測試 |
