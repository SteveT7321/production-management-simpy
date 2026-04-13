"""
C03：EOQ 經濟訂購量

EOQ = sqrt(2DS/H)

這是一條公式，不需要時間維度，也不需要模擬。
本工具計算最佳訂購量並展示成本曲線。
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.table import Table
from rich import box

# ── 預設參數（SMT 原物料採購情境）──────────────────────────────────
ANNUAL_DEMAND    = 50_000   # 年需求量（片）
ORDERING_COST    = 800.0    # 每次訂購成本（NT$）
UNIT_COST        = 120.0    # 單位成本（NT$/片）
HOLDING_RATE     = 0.20     # 年持有成本率（佔單位成本）

H = UNIT_COST * HOLDING_RATE   # 年持有成本（NT$/片/年）


def eoq(D: float, S: float, h: float) -> float:
    """最佳訂購量 EOQ = sqrt(2DS/H)"""
    return math.sqrt(2 * D * S / h)


def annual_total_cost(D: float, S: float, h: float, Q: float) -> dict:
    """年總成本分解"""
    ordering = (D / Q) * S
    holding  = (Q / 2) * h
    purchase = D * (S / Q * 0)  # 採購成本為固定，不影響決策
    return {
        "Q":        round(Q),
        "orders_per_year": round(D / Q, 1),
        "ordering_cost":   round(ordering),
        "holding_cost":    round(holding),
        "total_cost":      round(ordering + holding),
    }


def reorder_point(D: float, lead_time_days: float, safety_stock: float = 0) -> float:
    """再訂購點 ROP = d × L + SS"""
    daily_demand = D / 250   # 年工作日 250 天
    return daily_demand * lead_time_days + safety_stock


def main():
    console = Console()
    D, S, h = ANNUAL_DEMAND, ORDERING_COST, H

    Q_opt = eoq(D, S, h)
    base  = annual_total_cost(D, S, h, Q_opt)

    console.print("\n[bold cyan]C03　EOQ 經濟訂購量[/bold cyan]")
    console.print(
        f"  年需求 D={D:,} 片  |  訂購成本 S=NT${S:.0f}  |  "
        f"持有成本 H=NT${h:.1f}/片/年（{HOLDING_RATE:.0%} × NT${UNIT_COST}）\n"
    )
    console.print(
        f"  [green]EOQ = sqrt(2 × {D:,} × {S:.0f} / {h:.1f}) "
        f"= {Q_opt:.0f} 片[/green]\n"
    )

    # ── 敏感度分析：不同批量的成本比較 ──────────────────────────────
    table = Table(title="不同訂購量的年成本比較", box=box.SIMPLE_HEAVY)
    table.add_column("訂購量Q", justify="right", style="cyan")
    table.add_column("年訂購次數", justify="right")
    table.add_column("訂購成本(NT$)", justify="right")
    table.add_column("持有成本(NT$)", justify="right")
    table.add_column("年總成本(NT$)", justify="right")
    table.add_column("vs EOQ", justify="right")

    q_list = [200, 500, 1000, round(Q_opt), 2000, 3000, 5000]
    opt_total = base["total_cost"]

    for q in q_list:
        r = annual_total_cost(D, S, h, q)
        diff = round((r["total_cost"] - opt_total) / opt_total * 100, 1)
        color = "green" if q == round(Q_opt) else "white"
        diff_str = "0% (最佳)" if diff == 0 else f"+{diff}%"
        table.add_row(
            f"[{color}]{r['Q']:,}[/{color}]",
            f"{r['orders_per_year']}",
            f"{r['ordering_cost']:,}",
            f"{r['holding_cost']:,}",
            f"[{color}]{r['total_cost']:,}[/{color}]",
            f"[{color}]{diff_str}[/{color}]",
        )
    console.print(table)

    # ── 再訂購點（搭配第十章安全庫存）────────────────────────────────
    rop_scenarios = [
        ("無安全庫存",       0),
        ("SS = 0.5x LTD",  round(ANNUAL_DEMAND / 250 * 5 * 0.5)),
        ("SS = 1x LTD",    round(ANNUAL_DEMAND / 250 * 5)),
    ]
    t2 = Table(title="再訂購點 ROP（前置時間 = 5 天）", box=box.SIMPLE_HEAVY)
    t2.add_column("安全庫存策略", style="cyan")
    t2.add_column("安全庫存(片)", justify="right")
    t2.add_column("ROP(片)", justify="right")
    t2.add_column("含義", justify="left")

    for label, ss in rop_scenarios:
        rop = reorder_point(D, lead_time_days=5, safety_stock=ss)
        t2.add_row(
            label,
            str(ss),
            str(round(rop)),
            f"庫存降到 {round(rop)} 片時下單",
        )
    console.print(t2)

    console.print(
        f"\n[yellow]結論：[/yellow]\n"
        f"  最佳批量 EOQ = {Q_opt:.0f} 片，年訂購 {round(D/Q_opt, 1)} 次\n"
        f"  偏離 EOQ 10%（訂購量 {round(Q_opt*0.9)} 或 {round(Q_opt*1.1)}）：成本僅增加 ~0.5%\n"
        f"  EOQ 曲線底部平坦 → 實務上不必精確，±20% 都可接受"
    )


if __name__ == "__main__":
    main()
