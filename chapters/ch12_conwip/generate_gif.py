"""
Ch12 GIF：CONWIP vs 逐站 Kanban — 執行模擬展示 WIP 時序
"""
import sys, os, random
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'visualization'))

from simulation.smt_line import SMTLine
from gif_helpers import animated_wip_lines, PALETTE

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

SCENARIOS_CFG = [
    ("Push (No Limit)",
     dict(),
     PALETTE[3]),
    ("CONWIP\n(system limit=50)",
     dict(enable_kanban=True, kanban_limit=50),
     PALETTE[1]),
    ("Per-Station\n(each=10)",
     dict(enable_station_kanban=True, station_kanban_limit=10),
     PALETTE[0]),
    ("Per-Station\n(each=15)",
     dict(enable_station_kanban=True, station_kanban_limit=15),
     PALETTE[2]),
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
        print(f"  {label.split(chr(10))[0]}: avg WIP={stats.avg_wip:.1f}  "
              f"throughput={stats.throughput:.1f}")

    animated_wip_lines(
        results,
        title="Ch12: CONWIP vs Per-Station Kanban\n"
              "CONWIP (system-level) achieves -53% WIP with minimal throughput loss",
        save_path=SAVE_PATH,
    )


if __name__ == "__main__":
    main()
