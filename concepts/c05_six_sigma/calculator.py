"""
C05：Six Sigma / 製程能力分析

Cp、Cpk、DPMO、Sigma Level 都是靜態計算，不需要時間模擬。
本工具以 SMT 印刷製程（錫膏厚度）為例，計算製程能力並推算改善路徑。
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.table import Table
from rich import box

# ── 製程規格（SMT 錫膏印刷厚度）─────────────────────────────────
# 規格：目標 150 um，允差 ±30 um
TARGET  = 150.0   # um（目標值）
USL     = 180.0   # 上規格界限
LSL     = 120.0   # 下規格界限


# ── 計算函式 ──────────────────────────────────────────────────────

def cp(usl: float, lsl: float, sigma: float) -> float:
    """製程精確度（不考慮偏移）Cp = (USL-LSL) / 6σ"""
    return (usl - lsl) / (6 * sigma)


def cpk(usl: float, lsl: float, mean: float, sigma: float) -> float:
    """製程能力指數 Cpk = min((USL-μ)/3σ, (μ-LSL)/3σ)"""
    cpu = (usl - mean) / (3 * sigma)
    cpl = (mean - lsl) / (3 * sigma)
    return min(cpu, cpl)


def _norm_cdf(x: float) -> float:
    """標準常態分布 CDF（Abramowitz & Stegun 近似）"""
    t = 1 / (1 + 0.2316419 * abs(x))
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    cdf = 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-x**2 / 2) * poly
    return cdf if x >= 0 else 1 - cdf


def ppm_out_of_spec(usl: float, lsl: float, mean: float, sigma: float) -> float:
    """規格外比例 (PPM)"""
    z_upper = (usl - mean) / sigma
    z_lower = (mean - lsl) / sigma
    p_out = (1 - _norm_cdf(z_upper)) + _norm_cdf(-z_lower)
    return p_out * 1_000_000


def sigma_level(dpmo: float) -> float:
    """DPMO 轉換 Sigma Level（含 1.5σ 偏移）"""
    if dpmo <= 0:
        return 6.0
    # 逆正態近似（Beasley-Springer-Moro 算法簡化版）
    p = 1 - dpmo / 1_000_000
    # 使用查表近似
    sigma_table = [
        (3.4,    6.0), (233,    5.0), (6_210, 4.0),
        (66_807, 3.0), (308_537, 2.0), (690_000, 1.0),
    ]
    for threshold, level in sigma_table:
        if dpmo <= threshold:
            return level
    return 1.0


def sigma_to_yield(sigma: float) -> float:
    """Sigma Level → 製程良率（含 1.5σ 偏移）"""
    dpmo_map = {6.0: 3.4, 5.0: 233, 4.0: 6_210, 3.0: 66_807, 2.0: 308_537}
    dpmo = dpmo_map.get(round(sigma, 1), 66_807)
    return (1 - dpmo / 1_000_000) * 100


# ── 改善情境 ─────────────────────────────────────────────────────

SCENARIOS = [
    {"label": "現況：製程偏移",          "mean": 158.0, "sigma": 12.0},
    {"label": "改善一：置中（消除偏移）",  "mean": 150.0, "sigma": 12.0},
    {"label": "改善二：變異縮小（置中）",  "mean": 150.0, "sigma":  8.0},
    {"label": "改善三：Six Sigma 目標",   "mean": 150.0, "sigma":  5.0},
]


def main():
    console = Console()
    console.print("\n[bold cyan]C05　Six Sigma / 製程能力分析[/bold cyan]")
    console.print(
        f"  SMT 錫膏印刷厚度規格：LSL={LSL} um  目標={TARGET} um  USL={USL} um\n"
    )

    table = Table(title="製程能力改善路徑", box=box.SIMPLE_HEAVY)
    table.add_column("情境", style="cyan")
    table.add_column("均值(um)", justify="right")
    table.add_column("標準差(um)", justify="right")
    table.add_column("Cp", justify="right")
    table.add_column("Cpk", justify="right")
    table.add_column("DPMO", justify="right")
    table.add_column("Sigma Level", justify="right")
    table.add_column("製程良率", justify="right")

    for sc in SCENARIOS:
        m, s   = sc["mean"], sc["sigma"]
        _cp    = cp(USL, LSL, s)
        _cpk   = cpk(USL, LSL, m, s)
        _dpmo  = ppm_out_of_spec(USL, LSL, m, s)
        _sigma = sigma_level(_dpmo)
        _yield = 100 - _dpmo / 10_000

        cpk_color = "green" if _cpk >= 1.33 else "yellow" if _cpk >= 1.0 else "red"
        table.add_row(
            sc["label"],
            f"{m:.0f}",
            f"{s:.0f}",
            f"{_cp:.2f}",
            f"[{cpk_color}]{_cpk:.2f}[/{cpk_color}]",
            f"{_dpmo:,.0f}",
            f"{_sigma:.1f}",
            f"[{cpk_color}]{_yield:.3f}%[/{cpk_color}]",
        )
    console.print(table)

    # ── Cpk 基準說明 ────────────────────────────────────────────────
    t2 = Table(title="Cpk 判讀標準", box=box.SIMPLE_HEAVY)
    t2.add_column("Cpk 值", style="cyan")
    t2.add_column("DPMO 約值", justify="right")
    t2.add_column("Sigma Level", justify="right")
    t2.add_column("判定", justify="left")

    criteria = [
        ("< 1.00",  "> 66,807",  "< 3.0", "[red]製程不足（需立即改善）[/red]"),
        ("1.00",    "66,807",    "3.0",    "[yellow]勉強符合（最低標準）[/yellow]"),
        ("1.33",    "63",        "4.0",    "[green]一般工業標準[/green]"),
        ("1.67",    "0.6",       "5.0",    "[green]汽車/航太標準[/green]"),
        ("2.00",    "0.002",     "6.0",    "[bold green]Six Sigma 目標[/bold green]"),
    ]
    for row in criteria:
        t2.add_row(*row)
    console.print(t2)

    console.print(
        "\n[yellow]改善優先順序（ROI 最高到最低）：[/yellow]\n"
        "  1. 製程置中（消除偏移）：最快見效，通常只需調整機台參數\n"
        "  2. 變異縮小（降低 sigma）：需要找並消除變異來源（材料、機台、操作員）\n"
        "  3. 規格放寬（修改 USL/LSL）：與客戶協商，風險高\n"
        "\n  SMT 實務：SPI 量測錫膏體積可直接計算 Cpk，閉環回饋控制印刷壓力/速度"
    )


if __name__ == "__main__":
    main()
