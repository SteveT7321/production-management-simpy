# SMT 生產管理模擬教學

以 **SimPy 離散事件模擬（DES）** 建構的 SMT 電子組裝線數位孿生，  
涵蓋 7 個生產管理核心知識點，每個章節包含概念說明、公式推導、模擬實驗與結果解讀。

---

## 產線架構

```
錫膏印刷 → SPI → 高速機 → 泛用機 → 回焊爐（6槽）→ AOI
  ~20 s    ~15 s   ~8 s   ~25 s      ~45 s          ~30 s
                                        ↑
                             AOI 攔截不良品 → 返工迴路
```

機台參數參考 Yamaha / Fuji 業界規格（MTBF、MTTR、不良率、換線時間）。

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

每個章節資料夾內有兩個檔案：

```
chapters/ch0N_xxx/
├── README.md      ← 概念說明、核心公式、結果解讀、管理意涵
└── simulation.py  ← 可直接執行的模擬程式
```

---

## 快速開始

```bash
# 建立環境
conda create -n smt_twin python=3.10 -y
conda activate smt_twin
pip install -r requirements.txt

# 執行任一章節
python chapters/ch01_takt_time/simulation.py
python chapters/ch02_bottleneck/simulation.py
python chapters/ch03_oee/simulation.py
python chapters/ch04_smed/simulation.py
python chapters/ch05_quality/simulation.py
python chapters/ch06_kanban/simulation.py
python chapters/ch07_maintenance/simulation.py

# 快速驗證整條產線
python check.py

# 執行單元測試
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

---

## 專案結構

```
├── chapters/                  教學章節
│   ├── ch01_takt_time/
│   │   ├── README.md          概念、公式、結果解讀、管理意涵
│   │   └── simulation.py      模擬程式碼
│   ├── ch02_bottleneck/
│   ├── ch03_oee/
│   ├── ch04_smed/
│   ├── ch05_quality/
│   ├── ch06_kanban/
│   └── ch07_maintenance/
│
├── simulation/                核心模擬引擎
│   ├── config.py              機台參數（Yamaha/Fuji 業界規格）
│   ├── machines.py            Machine class（故障 / 換線 / OEE 統計）
│   ├── pcb.py                 PCB 生命週期
│   ├── smt_line.py            主產線 SimPy 流程（含 Kanban / PM）
│   └── statistics.py          OEE / Throughput / WIP / Little's Law
│
├── tests/
│   └── test_simulation.py     單元測試（8 項）
├── check.py                   快速驗證腳本
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
