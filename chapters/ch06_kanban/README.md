# 第六章　看板系統：Kanban WIP 上限控制

## 概念說明

傳統製造使用 **Push（推式）系統**：上游設備依照排程持續生產，將半成品「推送」到下游，不管下游有沒有空間。當下游速度跟不上時，WIP 在站點之間堆積，最終失控。

**Pull（拉式）系統** 的邏輯相反：下游有需求時才發出訊號，上游才允許生產。這個訊號的具體實現就是 **Kanban（看板）**——一張實體卡片（或電子訊號），代表「下游有空間，請上游補一件」。

Kanban 的核心概念：

> **沒有看板，就不生產。**

這使得 WIP 有了「天花板」——系統中的看板數量決定了最大 WIP，讓流程時間可預測、問題可見。

---

## 核心公式

### WIP 上限計算

```
最大 WIP ≈ 看板數量 × 每批件數

設定原則（Takt Time 法）：
  初始看板數 = Takt Time 倍數 × 緩衝係數
             ≈ (平均 CT + 安全緩衝) ÷ Takt Time

本實驗設定：每站 WIP 上限 = N 件
```

### WIP 與 Cycle Time 的關係（Little's Law）

```
WIP = 到達率 × Cycle Time

若 WIP 被 Kanban 限制：
  Cycle Time 也會同比縮短（因為等待隊列縮短）
```

### Push vs Pull 比較

| 指標 | Push 系統 | Pull 系統（Kanban） |
|------|---------|-------------------|
| WIP | 不受控，隨瓶頸堆積 | 由看板數上限控制 |
| Cycle Time | 隨 WIP 增加而拉長 | 可預測、穩定 |
| 問題可見性 | 被庫存掩蓋 | 問題立即顯現 |
| 彈性 | 難以調整 | 調整看板數即可調整產能 |

---

## 產線實驗參數

四個情境，覆蓋「無 Kanban → 嚴格 → 適中 → 寬鬆」的完整範圍：

| 情境 | 系統 WIP 上限 | 系統類型 |
|------|-------------|---------|
| A | 無限制（Push） | Push 系統 |
| B | 20 件 | 嚴格 Kanban（可能阻礙流動） |
| C | 50 件 | 推薦值 |
| D | 80 件 | 寬鬆 Kanban（效果接近 Push） |

> **Kanban 實作說明**：系統級 WIP 限制——PCB 進板前必須等待系統有空位（Pull 訊號），
> 完工後才釋放空位讓下一片進板。Push 系統自然 WIP ≈ 100 pcs。

---

## 實驗設計

**核心問題：**
1. Kanban 能降低多少 WIP？
2. 看板數設太低（B）是否會阻礙流動、降低產出？
3. 最佳看板數設定在哪個範圍？

若 Kanban 有效，C 應在不顯著犧牲 Throughput 的前提下大幅降低 WIP 和 Cycle Time。

---

## 如何執行

```bash
conda run -n smt_twin python chapters/ch06_kanban/simulation.py
```

---

## 結果解讀

**預期輸出：**

```
情境                    WIP上限   平均WIP    Cycle Time    看板等待    產出率
A: 無 Kanban（Push）    無限制    ~101 pcs   ~3095 s       0 s       102 pcs/hr
B: Kanban limit=20      20        ~18 pcs    ~688 s        ~10 s     91 pcs/hr
C: Kanban limit=50      50        ~47 pcs    ~1559 s       ~5 s      102 pcs/hr
D: Kanban limit=80      80        ~75 pcs    ~2463 s       ~4 s      99 pcs/hr
```

**關鍵觀察：**
- Cycle Time 與 WIP 幾乎同比例縮減（驗證 Little's Law：WIP = λ × CT）
- B（limit=20）WIP 降 82%，但 Throughput 降 11%——Kanban 太緊，阻礙了流動
- C（limit=50）WIP 降 53%，Throughput 幾乎不變——最佳平衡點
- D（limit=80）效果有限，接近 Push（自然 WIP 就在 100 附近）

**看板等待時間的意義：**
- 看板等待時間高 → 上游生產被頻繁阻擋 → 看板數太少，需調高
- 看板等待時間低且 WIP 高 → 看板數太多，形同無限制

---

## 管理意涵

1. **Pull 系統是精實生產的核心**：Kanban 讓製造系統從「推」到「拉」，是消除浪費的基礎
2. **看板數的設定是藝術也是科學**：太少阻礙流動，太多等同無效——需根據 Takt Time 和波動性調整
3. **WIP 降低帶來連鎖效益**：
   - Flow Time 縮短 → 交期更可預測
   - 問題更快被發現 → 品質問題不會被庫存隱藏
   - 庫存持有成本下降
4. **看板數量可以動態調整**：淡旺季需求變化時，調整看板數即可，不需要修改複雜的排程系統

---

## 延伸閱讀

- 第一章：Little's Law 解釋了 WIP 降低為何能縮短 Cycle Time
- 第四章：SMED 縮短換線時間，是 Kanban 能小批量運作的前提
