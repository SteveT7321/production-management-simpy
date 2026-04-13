"""
Ch04 GIF：SMED — 快速換線讓小批量達到大批量效率
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from visualization.gif_helpers import animated_bar_chart, PALETTE

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

animated_bar_chart(
    categories=["Large Batch\n(no changeover)", "Small Batch\n(no SMED)",
                "Small Batch\n(+ SMED -80%)"],
    values=[21.0, 4.0, 20.0],
    title="Ch04: SMED — Quick Changeover\nSMED restores small-batch throughput to large-batch level",
    ylabel="Effective Throughput (pcs/hr)",
    save_path=SAVE_PATH,
    colors=[PALETTE[0], PALETTE[3], PALETTE[1]],
    reference_line=20.0,
    reference_label="Large-batch benchmark",
    highlight_idx=2,
)
