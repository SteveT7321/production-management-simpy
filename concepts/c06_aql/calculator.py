"""
C06：AQL 抽樣計畫

AQL（Acceptable Quality Level）定義「可接受的最大平均不良率」。
本工具實作 ANSI/ASQ Z1.4 簡化版：
  Lot Size → 樣本代字 → 樣本數 n、允收數 c、拒收數 r
並計算 OC 曲線（Operating Characteristic Curve）。
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.table import Table
from rich import box

# ── ANSI/ASQ Z1.4 簡化對照表（Normal Inspection, Level II）─────
# 格式：(lot_size_min, lot_size_max, code_letter)
LOT_SIZE_CODE = [
    (2,       8,       "A"),
    (9,       15,      "B"),
    (16,      25,      "C"),
    (26,      50,      "D"),
    (51,      90,      "E"),
    (91,      150,     "F"),
    (151,     280,     "G"),
    (281,     500,     "H"),
    (501,     1200,    "J"),
    (1201,    3200,    "K"),
    (3201,    10000,   "L"),
    (10001,   35000,   "M"),
    (35001,   150000,  "N"),
    (150001,  500000,  "P"),
    (500001,  999999,  "Q"),
]

# 格式：code_letter → {AQL: (n, c, r), ...}
# 僅列常用 AQL：0.65%, 1.0%, 1.5%, 2.5%, 4.0%
SAMPLING_PLAN = {
    "F":  {"0.65": (20, 0, 1),  "1.0": (20, 0, 1),  "1.5": (20, 1, 2),  "2.5": (20, 1, 2),  "4.0": (20, 2, 3)},
    "G":  {"0.65": (32, 0, 1),  "1.0": (32, 1, 2),  "1.5": (32, 1, 2),  "2.5": (32, 2, 3),  "4.0": (32, 3, 4)},
    "H":  {"0.65": (50, 1, 2),  "1.0": (50, 1, 2),  "1.5": (50, 2, 3),  "2.5": (50, 3, 4),  "4.0": (50, 5, 6)},
    "J":  {"0.65": (80, 1, 2),  "1.0": (80, 2, 3),  "1.5": (80, 3, 4),  "2.5": (80, 5, 6),  "4.0": (80, 7, 8)},
    "K":  {"0.65": (125, 2, 3), "1.0": (125, 3, 4), "1.5": (125, 5, 6), "2.5": (125, 7, 8), "4.0": (125, 10, 11)},
    "L":  {"0.65": (200, 3, 4), "1.0": (200, 5, 6), "1.5": (200, 7, 8), "2.5": (200, 10, 11),"4.0": (200, 14, 15)},
    "M":  {"0.65": (315, 5, 6), "1.0": (315, 7, 8), "1.5": (315, 10, 11),"2.5": (315, 14, 15),"4.0": (315, 21, 22)},
}


def get_code_letter(lot_size: int) -> str:
    for lo, hi, code in LOT_SIZE_CODE:
        if lo <= lot_size <= hi:
            return code
    return "Q"


def get_plan(lot_size: int, aql: str) -> dict:
    code = get_code_letter(lot_size)
    if code not in SAMPLING_PLAN or aql not in SAMPLING_PLAN[code]:
        return {}
    n, c, r = SAMPLING_PLAN[code][aql]
    return {"code": code, "n": n, "c": c, "r": r}


def _binom_cdf(n: int, k: int, p: float) -> float:
    """P(X <= k) where X ~ Binomial(n, p)"""
    total = 0.0
    coeff = 1.0
    p_pow = 1.0
    q_pow = (1 - p) ** n
    for i in range(k + 1):
        if i > 0:
            coeff *= (n - i + 1) / i
            p_pow *= p
            q_pow /= (1 - p)
        total += coeff * p_pow * q_pow
    return min(total, 1.0)


def pa_of_lot(n: int, c: int, p: float) -> float:
    """Pa(p)：不良率為 p 時批量被允收的機率"""
    return _binom_cdf(n, c, p)


def oc_curve(n: int, c: int) -> list:
    """OC 曲線：各不良率對應的允收機率"""
    points = []
    for p_pct in [0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0]:
        p = p_pct / 100
        pa = pa_of_lot(n, c, p)
        points.append({"p_pct": p_pct, "pa": round(pa * 100, 1)})
    return points


def main():
    console = Console()
    console.print("\n[bold cyan]C06　AQL 抽樣計畫（ANSI/ASQ Z1.4）[/bold cyan]")
    console.print("  場景：SMT PCB 出貨前檢驗，找出最適抽樣方案\n")

    # ── 常見批量 + AQL 1.0 的抽樣方案 ────────────────────────────
    lot_scenarios = [
        ("小批量",    200,   "1.0"),
        ("中批量",    500,   "1.0"),
        ("標準批量",  1200,  "1.0"),
        ("大批量",    3200,  "1.0"),
        ("大批量",    3200,  "0.65"),
        ("大批量",    3200,  "2.5"),
    ]

    t1 = Table(title="不同批量 / AQL 的抽樣方案", box=box.SIMPLE_HEAVY)
    t1.add_column("批量大小", justify="right", style="cyan")
    t1.add_column("AQL%", justify="right")
    t1.add_column("代字", justify="center")
    t1.add_column("樣本數 n", justify="right")
    t1.add_column("允收數 c", justify="right")
    t1.add_column("拒收數 r", justify="right")
    t1.add_column("抽樣比例", justify="right")

    for label, lot, aql in lot_scenarios:
        plan = get_plan(lot, aql)
        if not plan:
            continue
        ratio = round(plan["n"] / lot * 100, 1)
        t1.add_row(
            f"{lot:,}",
            aql,
            plan["code"],
            str(plan["n"]),
            str(plan["c"]),
            str(plan["r"]),
            f"{ratio}%",
        )
    console.print(t1)

    # ── OC 曲線（批量 3200，AQL=1.0）────────────────────────────
    plan = get_plan(3200, "1.0")
    n, c = plan["n"], plan["c"]
    oc = oc_curve(n, c)

    t2 = Table(
        title=f"OC 曲線（n={n}, c={c}，批量 3200 片，AQL=1.0%）",
        box=box.SIMPLE_HEAVY,
    )
    t2.add_column("實際不良率(%)", justify="right", style="cyan")
    t2.add_column("允收機率 Pa(%)", justify="right")
    t2.add_column("拒收機率(%)", justify="right")
    t2.add_column("風險說明", justify="left")

    risk_labels = {
        0.1:  "供應商風險極低（幾乎必過）",
        1.0:  "AQL 點：Pa ~ 95%（供應商風險 5%）",
        2.5:  "LTPD 區：消費者開始面臨風險",
        5.0:  "不良品 5%：批量應被拒收",
        10.0: "高不良率：幾乎確定拒收",
    }

    for pt in oc:
        pa = pt["pa"]
        reject = round(100 - pa, 1)
        color = "green" if pa >= 90 else "yellow" if pa >= 50 else "red"
        label = risk_labels.get(pt["p_pct"], "")
        t2.add_row(
            f"{pt['p_pct']}%",
            f"[{color}]{pa}%[/{color}]",
            f"{reject}%",
            label,
        )
    console.print(t2)

    console.print(
        "\n[yellow]管理意涵：[/yellow]\n"
        "  AQL 越小：樣本越多，檢驗成本越高，但消費者保護越強\n"
        "  AQL 越大：樣本越少，成本低，但允許更多不良品流出\n"
        "  OC 曲線的「陡峭度」反映鑑別力：樣本 n 越大，曲線越陡，鑑別力越強\n"
        "\n  SMT 出貨建議：功能板 AQL=0.65、外觀板 AQL=2.5；\n"
        "  高單價產品（車用/醫療）應使用 Tightened Inspection（加嚴抽樣）"
    )


if __name__ == "__main__":
    main()
