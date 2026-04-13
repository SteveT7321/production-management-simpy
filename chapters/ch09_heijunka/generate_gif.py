"""
Ch09 GIF：Heijunka 均衡生產 — 執行模擬展示 WIP 平滑效果
"""
import sys, os, random
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'visualization'))

import importlib.util, types

# ── 動態載入 ch09 HeijunkaLine（避免 __init__.py 依賴） ─────────────
_spec = importlib.util.spec_from_file_location(
    "ch09_sim",
    os.path.join(os.path.dirname(__file__), "simulation.py"),
)
_mod = importlib.util.module_from_spec(_spec)
# 讓子模組在 sys.modules 下找到自己，避免 import 迴圈
sys.modules["ch09_sim"] = _mod
_spec.loader.exec_module(_mod)
HeijunkaLine = _mod.HeijunkaLine

from gif_helpers import animated_wip_lines, PALETTE

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")


def main():
    results = []
    for label, mode, color in [
        ("Batch Production\n(80 pcs / hour burst)",  "batch",   PALETTE[3]),
        ("Heijunka (Leveled)\n(1 pcs every 45 s)",   "leveled", PALETTE[1]),
    ]:
        random.seed(42)
        line  = HeijunkaLine(mode=mode)
        stats = line.run()
        results.append({
            "label":       label,
            "wip_samples": stats.wip_samples,
            "color":       color,
        })
        print(f"  {label.split(chr(10))[0]}: avg WIP={stats.avg_wip:.1f}  std≈{_wip_std(stats):.1f}")

    animated_wip_lines(
        results,
        title="Ch09: Heijunka — Production Leveling Stabilizes WIP\n"
              "Batch mode causes WIP spikes; leveled arrival keeps WIP smooth",
        save_path=SAVE_PATH,
    )


def _wip_std(stats):
    import statistics as _s
    ws = [w for _, w in stats.wip_samples]
    return _s.stdev(ws) if len(ws) > 1 else 0.0


if __name__ == "__main__":
    main()
