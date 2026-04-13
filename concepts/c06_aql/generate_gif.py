"""
C06 GIF：AQL OC 曲線 — 允收機率 vs 實際不良率
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from math import comb

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

# Three sampling plans: (n, c, label, color, AQL)
PLANS = [
    (125, 3, "n=125, c=3  AQL=1.0%",  "#2196F3", 1.0),
    (125, 7, "n=125, c=7  AQL=2.5%",  "#FF9800", 2.5),
    (200, 5, "n=200, c=5  AQL=1.0%",  "#4CAF50", 1.0),
]


def pa(n, c, p):
    """P(X <= c) where X ~ Binom(n, p)"""
    total = 0.0
    for k in range(c + 1):
        total += comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    return min(total, 1.0)


def main():
    p_range = np.linspace(0.001, 0.15, 300)

    DRAW_FRAMES = 60
    HOLD        = 28
    total       = DRAW_FRAMES + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("C06: AQL — Operating Characteristic (OC) Curve\n"
                     "AQL point: Pa ≈ 95% (5% producer's risk)  |  Larger n = steeper curve",
                     fontsize=10.5, fontweight="bold", pad=8)
        ax.set_xlabel("True Defect Rate (%)", fontsize=9)
        ax.set_ylabel("Acceptance Probability Pa (%)", fontsize=9)
        ax.set_xlim(0, 15)
        ax.set_ylim(0, 105)
        ax.grid(alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Risk zones
        ax.axhspan(95, 105, alpha=0.07, color="#4CAF50")
        ax.axhspan(0,  10,  alpha=0.07, color="#F44336")
        ax.text(0.5,  98, "Producer safe zone (Pa > 95%)",
                fontsize=7, color="#2E7D32")
        ax.text(0.5,   4, "Consumer risk zone (Pa < 10%)",
                fontsize=7, color="#B71C1C")
        ax.axhline(95, color="#4CAF50", linewidth=0.8, linestyle=":", alpha=0.6)
        ax.axhline(10, color="#F44336", linewidth=0.8, linestyle=":", alpha=0.6)

        n_show = max(min(int(frame / DRAW_FRAMES * len(p_range)), len(p_range)), 2)

        for (n, c, label, color, aql) in PLANS:
            pa_vals = np.array([pa(n, c, p) * 100 for p in p_range[:n_show]])
            ax.plot(p_range[:n_show] * 100, pa_vals,
                    color=color, linewidth=2.3, label=label)

            # AQL point marker
            if p_range[n_show - 1] * 100 >= aql:
                pa_aql = pa(n, c, aql / 100) * 100
                ax.scatter([aql], [pa_aql], color=color, s=70, zorder=6)

        ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=70, repeat=True, repeat_delay=1000)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=13), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
