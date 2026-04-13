"""
Ch10 GIF：安全庫存 — 執行模擬展示缺料斷線 vs 補料緩衝
"""
import sys, os, random
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'visualization'))

import importlib.util, sys as _sys

_spec = importlib.util.spec_from_file_location(
    "ch10_sim",
    os.path.join(os.path.dirname(__file__), "simulation.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_sys.modules["ch10_sim"] = _mod
_spec.loader.exec_module(_mod)
SafetyStockLine = _mod.SafetyStockLine

from gif_helpers import animated_wip_lines, PALETTE

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

ROP_SCENARIOS = [
    ("ROP = 0\n(no safety stock)", 0,   100, PALETTE[3]),
    ("ROP = 1× LTD",               64,  100, PALETTE[2]),
    ("ROP = 2× LTD",               128, 200, PALETTE[1]),
]


def main():
    results = []
    for label, rop, initial_stock, color in ROP_SCENARIOS:
        random.seed(42)
        line  = SafetyStockLine(rop=rop, initial_stock=initial_stock)
        stats = line.run()
        results.append({
            "label":       label,
            "wip_samples": stats.wip_samples,
            "color":       color,
        })
        print(f"  {label.split(chr(10))[0]}: throughput={stats.throughput:.1f}")

    animated_wip_lines(
        results,
        title="Ch10: Safety Stock — Stockout Dips vs Buffer\n"
              "ROP=0 causes WIP to collapse when material runs out",
        save_path=SAVE_PATH,
    )


if __name__ == "__main__":
    main()
