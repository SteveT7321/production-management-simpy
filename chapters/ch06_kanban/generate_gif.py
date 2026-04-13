"""
Ch06 GIF：Kanban WIP 控制 — 實際執行模擬，展示 WIP 時序
"""
import sys, os, random
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'visualization'))

from simulation.smt_line import SMTLine
from gif_helpers import animated_wip_lines, PALETTE

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

SCENARIOS_CFG = [
    ("Push (No Limit)",  dict(),                                       PALETTE[3]),
    ("Kanban limit=20",  dict(enable_kanban=True, kanban_limit=20),    PALETTE[0]),
    ("Kanban limit=50",  dict(enable_kanban=True, kanban_limit=50),    PALETTE[1]),
    ("Kanban limit=80",  dict(enable_kanban=True, kanban_limit=80),    PALETTE[2]),
]


def main():
    results = []
    for label, kwargs, color in SCENARIOS_CFG:
        random.seed(42)
        line  = SMTLine(**kwargs)
        stats = line.run()
        results.append({
            "label":       label,
            "wip_samples": stats.wip_samples,
            "color":       color,
        })
        print(f"  {label}: avg WIP = {stats.avg_wip:.1f}")

    animated_wip_lines(
        results,
        title="Ch06: Kanban — WIP Control Over 8-Hour Shift\n"
              "Kanban limit caps WIP; tighter limit = lower WIP, but risks throughput loss",
        save_path=SAVE_PATH,
    )


if __name__ == "__main__":
    main()
