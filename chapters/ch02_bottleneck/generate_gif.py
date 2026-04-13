"""
Ch02 GIF：TOC — 改善瓶頸 vs 改善非瓶頸的 throughput 差異
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from visualization.gif_helpers import animated_bar_chart, PALETTE

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

animated_bar_chart(
    categories=["A: Original\nBaseline", "B: Improve\nBottleneck (+20%)",
                "C: Improve\nNon-Bottleneck (+20%)"],
    values=[102.4, 106.7, 99.0],
    title="Ch02: Theory of Constraints\nBottleneck improvement lifts throughput; non-bottleneck does not",
    ylabel="Throughput (pcs/hr)",
    save_path=SAVE_PATH,
    colors=[PALETTE[0], PALETTE[1], PALETTE[2]],
    reference_line=100.0,
    reference_label="Customer Takt (100)",
    highlight_idx=1,
)
