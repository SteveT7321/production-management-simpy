"""
Ch03 GIF：OEE 三維分解 — Availability × Performance × Quality
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

# Data for 3 scenarios × 3 OEE components
SCENARIOS = ["A: Original", "B: MTBF×2\n(Availability Up)", "C: Defect×0.5\n(Quality Up)"]
AVAIL     = [0.923, 0.962, 0.923]   # Availability
PERF      = [0.600, 0.750, 0.610]   # Performance (approx)
QUAL      = [0.989, 0.989, 0.994]   # Quality
OEE       = [a * p * q for a, p, q in zip(AVAIL, PERF, QUAL)]

COLORS_AV = "#2196F3"
COLORS_PF = "#FF9800"
COLORS_QL = "#4CAF50"


def main():
    n = len(SCENARIOS)
    x = np.arange(n)
    w = 0.25

    FRAMES_PER_GRP = 8
    HOLD           = 28
    total          = n * FRAMES_PER_GRP + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("Ch03: OEE = Availability × Performance × Quality\n"
                     "Availability (failures) is the dominant loss",
                     fontsize=11, fontweight="bold", pad=8)
        ax.set_ylabel("Rate (%)", fontsize=9)
        ax.set_ylim(0, 115)
        ax.set_xticks(x)
        ax.set_xticklabels(SCENARIOS, fontsize=8.5)
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        layers = [
            ("Availability", AVAIL, COLORS_AV, x - w),
            ("Performance",  PERF,  COLORS_PF, x),
            ("Quality",      QUAL,  COLORS_QL, x + w),
        ]

        for gi in range(n):
            prog = (frame - gi * FRAMES_PER_GRP) / FRAMES_PER_GRP
            for lbl, vals, col, xs in layers:
                h = float(np.clip(vals[gi] * 100 * prog, 0, vals[gi] * 100))
                bar = ax.bar(xs[gi], h, width=w * 0.9, color=col, alpha=0.85,
                             zorder=3, label=lbl if gi == 0 else "")
                if h > 5:
                    ax.text(xs[gi], h + 0.5, f"{vals[gi]*100:.1f}",
                            ha="center", va="bottom", fontsize=6.5)

            # OEE overall
            if frame >= (gi + 1) * FRAMES_PER_GRP:
                oee_pct = OEE[gi] * 100
                ax.text(x[gi], 107, f"OEE\n{oee_pct:.1f}%",
                        ha="center", fontsize=8, fontweight="bold",
                        color="#1A237E")

        ax.legend(loc="lower right", fontsize=8, framealpha=0.8)
        ax.axhline(85, color="#E53935", linewidth=1.2, linestyle="--", alpha=0.7)
        ax.text(n - 0.5, 86, "World-class 85%", color="#E53935", fontsize=7.5)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=60, repeat=True, repeat_delay=800)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
