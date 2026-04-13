"""
Ch05 GIF：FPY 串聯計算 — 不良率對整線良率的影響
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

# Serial FPY calculation visualization
STATIONS   = ["Screen\nPrinter", "SPI", "Chip\nShooter", "Flex\nPlacer",
              "Reflow\nOven", "AOI"]
DEFECT_BASE = [0.005, 0.000, 0.002, 0.003, 0.001, 0.000]

def serial_fpy(defects):
    fpy = 1.0
    for d in defects:
        fpy *= (1 - d)
    return fpy * 100


def main():
    multipliers = [0.5, 1.0, 2.0, 4.0]
    colors      = ["#4CAF50", "#2196F3", "#FF9800", "#F44336"]
    labels      = ["Defect×0.5", "Original", "Defect×2", "Defect×4"]

    # Compute cumulative FPY at each station for each scenario
    cum_fpy = []
    for m in multipliers:
        d_list = [d * m for d in DEFECT_BASE]
        cum = []
        fpy = 1.0
        for d in d_list:
            fpy *= (1 - d)
            cum.append(fpy * 100)
        cum_fpy.append(cum)

    DRAW_FRAMES = 55
    HOLD        = 25
    total       = DRAW_FRAMES + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")
    x = np.arange(len(STATIONS))

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("Ch05: Serial FPY — Defect Rate Cascades Through Stations\n"
                     "Each station multiplies FPY: small defect rate, big cumulative impact",
                     fontsize=10.5, fontweight="bold", pad=8)
        ax.set_ylabel("Cumulative FPY (%)", fontsize=9)
        ax.set_ylim(94, 101)
        ax.set_xticks(x)
        ax.set_xticklabels(STATIONS, fontsize=8.5)
        ax.set_xlim(-0.5, len(STATIONS) - 0.5)
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        n_show = max(int(frame / DRAW_FRAMES * len(STATIONS)), 1)

        for ci, (cum, lbl, col) in enumerate(zip(cum_fpy, labels, colors)):
            ax.plot(x[:n_show], cum[:n_show],
                    color=col, linewidth=2.2, marker="o",
                    markersize=6, label=lbl, zorder=3)
            if n_show >= len(STATIONS):
                ax.text(x[-1] + 0.08, cum[-1],
                        f"  {cum[-1]:.2f}%", color=col,
                        fontsize=8, va="center", fontweight="bold")

        ax.axhline(99.0, color="#757575", linewidth=0.8,
                   linestyle=":", alpha=0.7)
        ax.legend(loc="lower left", fontsize=8, framealpha=0.8)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=80, repeat=True, repeat_delay=800)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=12), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
