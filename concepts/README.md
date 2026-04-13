# Concepts：靜態分析工具集

本目錄收錄**不需要 SimPy 模擬**的生產管理知識工具。
這些工具以解析公式或靜態查表為核心，適合快速計算和學習理論基礎。

## 為什麼獨立放在 concepts/ 而不是 chapters/？

| 特性 | `concepts/`（本目錄） | `chapters/`（主模擬） |
|------|---------------------|---------------------|
| 計算方式 | 解析公式 / 靜態查表 | SimPy 離散事件模擬 |
| 時間維度 | 無（一次性計算） | 有（事件隨時間發生）|
| 隨機性 | 無（輸入固定，輸出唯一）| 有（MTBF、到達間隔服從分布）|
| 執行速度 | 瞬時 | 需要模擬時間（秒~分鐘）|
| 典型用途 | 計算目標值、設定改善基準 | 驗證改善效果、觀察動態行為 |

**原則：能用公式算清楚的，不要過度工程化加模擬；需要觀察動態互動的，才使用 SimPy。**

---

## 工具一覽

| 目錄 | 主題 | 核心公式 / 方法 | 執行指令 |
|------|------|--------------|---------|
| [c01_5s/](c01_5s/) | 5S 評核 | 分數 → 效率影射 | `python concepts/c01_5s/calculator.py` |
| [c02_vsm/](c02_vsm/) | VSM 價值流圖 | PCE = VA / Lead Time | `python concepts/c02_vsm/calculator.py` |
| [c03_eoq/](c03_eoq/) | EOQ 經濟訂購量 | sqrt(2DS/H) | `python concepts/c03_eoq/calculator.py` |
| [c04_mrp/](c04_mrp/) | MRP 物料需求計畫 | BOM 展開 + 淨需求 | `python concepts/c04_mrp/calculator.py` |
| [c05_six_sigma/](c05_six_sigma/) | Six Sigma 製程能力 | Cp / Cpk / DPMO | `python concepts/c05_six_sigma/calculator.py` |
| [c06_aql/](c06_aql/) | AQL 抽樣計畫 | ANSI Z1.4 + OC 曲線 | `python concepts/c06_aql/calculator.py` |

---

## 執行全部工具

```bash
# 從專案根目錄執行
for f in concepts/c0*/calculator.py; do
    echo "=== $f ==="
    python $f
done
```

---

## 與 SimPy 模擬章節的對應關係

```
concepts/（靜態基準計算）        chapters/（動態模擬驗證）
─────────────────────────────    ──────────────────────────────
c01_5s      → 5S 成熟度評核     ─→  影響 ch03 OEE、ch07 PM 效果
c02_vsm     → PCE 基準分析      ─→  ch06 Kanban 改善 Lead Time
c03_eoq     → 最佳批量計算      ─→  ch10 Safety Stock 補貨參數
c04_mrp     → 採購計畫生成      ─→  ch10 Safety Stock 缺料停線
c05_six_sigma → Cpk 能力計算    ─→  ch11 SPC 漂移偵測
c06_aql     → 出廠抽樣方案      ─→  ch05 Quality FPY 不良率
```

---

## 學習路徑建議

如果你是**剛接觸生產管理**：
1. 先看 `c01_5s` → 理解精實基礎文化
2. 再看 `c02_vsm` → 了解哪裡有浪費
3. 然後 `c03_eoq` + `c04_mrp` → 掌握庫存與採購邏輯
4. 最後 `c05_six_sigma` + `c06_aql` → 品質管理的量化工具

如果你熟悉生產管理，想了解 SimPy 模擬：
- 先在 concepts/ 確認你理解對應的靜態概念
- 再到 chapters/ 觀察加入時間維度後的動態行為
