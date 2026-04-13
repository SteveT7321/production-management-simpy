"""
C04 GIF：MRP 計畫訂單 — 各物料的每週發出量（甘特式橫條）
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

WEEKS = list(range(1, 9))
ITEMS = ["PCBA\n(LT=1w)", "PCB\n(LT=2w)", "CAP 100nF\n(LT=1w)",
         "RES 10k\n(LT=1w)", "IC MCU\n(LT=4w)", "Solder\n(LT=1w)"]

# Planned order releases (computed from MRP calculator)
RELEASES = {
    "PCBA\n(LT=1w)":      [200, 100, 300, 200, 300, 200, 300, 0],
    "PCB\n(LT=2w)":       [400, 200, 200, 200, 400, 0,   0,   0],
    "CAP 100nF\n(LT=1w)": [3000,6000,4000,6000,4000,6000, 0,  0],
    "RES 10k\n(LT=1w)":   [2000,4000,3000,5000,3000,4000, 0,  0],
    "IC MCU\n(LT=4w)":    [1050,200, 300,  0,   0,   0,   0,  0],
    "Solder\n(LT=1w)":    [150, 150, 100, 150,  100, 150,  0,  0],
}
# Normalise for display (each item has its own scale)
MAX_PER_ITEM = {k: max(v) if max(v) > 0 else 1 for k, v in RELEASES.items()}

COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"]


def main():
    n_items = len(ITEMS)
    y       = np.arange(n_items)

    # Each week's bars appear one at a time
    FRAMES_PER_WEEK = 6
    HOLD            = 28
    total           = len(WEEKS) * FRAMES_PER_WEEK + HOLD

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor("white")

    w_width = 0.65 / n_items

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("C04: MRP Planned Order Releases (8-week horizon)\n"
                     "IC MCU (LT=4w) must be ordered NOW — the critical path",
                     fontsize=10.5, fontweight="bold", pad=8)
        ax.set_xlabel("Week", fontsize=9)
        ax.set_ylabel("Item", fontsize=9)
        ax.set_xlim(0.5, 8.5)
        ax.set_ylim(-0.5, n_items - 0.5)
        ax.set_xticks(WEEKS)
        ax.set_xticklabels([f"W{w}" for w in WEEKS], fontsize=8.5)
        ax.set_yticks(y)
        ax.set_yticklabels(ITEMS, fontsize=8)
        ax.grid(axis="x", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        n_show = int(min(frame, len(WEEKS) * FRAMES_PER_WEEK) / FRAMES_PER_WEEK)

        for wi in range(min(n_show, len(WEEKS))):
            w  = WEEKS[wi]
            for ii, (item, color) in enumerate(zip(ITEMS, COLORS)):
                qty = RELEASES[item][wi]
                if qty == 0:
                    continue
                width_frac = qty / MAX_PER_ITEM[item] * 0.38
                ax.barh(y[ii] + (wi % 2) * 0.0,   # slight y jitter for visibility
                        width_frac, left=w - width_frac / 2,
                        color=color, height=0.45, alpha=0.85,
                        edgecolor="white", linewidth=0.5)

        # Legend
        from matplotlib.patches import Patch
        patches = [Patch(color=c, label=item.replace('\n', ' '))
                   for item, c in zip(ITEMS, COLORS)]
        ax.legend(handles=patches, loc="upper right",
                  fontsize=7.5, framealpha=0.9, ncol=2)

        # Highlight critical path: IC MCU
        ax.annotate("Critical path:\nMCU must be\nordered W1",
                    xy=(1, y[ITEMS.index("IC MCU\n(LT=4w)")]),
                    xytext=(3.5, y[ITEMS.index("IC MCU\n(LT=4w)")] + 1.2),
                    arrowprops=dict(arrowstyle="->", color="#B71C1C"),
                    fontsize=7.5, color="#B71C1C", fontweight="bold")

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=80, repeat=True, repeat_delay=1000)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=12), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
