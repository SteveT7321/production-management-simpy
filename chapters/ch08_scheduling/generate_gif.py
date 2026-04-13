"""
Ch08 GIF：排程規則 — FIFO / SPT / EDD 多指標雷達比較
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

RULES      = ["FIFO", "SPT", "EDD"]
ON_TIME    = [84.5, 92.5, 86.6]      # on-time rate %
AVG_FLOW   = [62.4, 50.8, 60.1]      # avg flow time (s)
MAX_LATE   = [240.0, 1058.0, 223.3]  # max lateness (s)

COLORS = ["#2196F3", "#FF9800", "#4CAF50"]


def main():
    FRAMES_PER = 8
    HOLD       = 28
    total      = 3 * FRAMES_PER + HOLD

    fig, axes = plt.subplots(1, 3, figsize=(11, 5))
    fig.patch.set_facecolor("white")
    fig.suptitle("Ch08: Scheduling Rules — FIFO vs SPT vs EDD\n"
                 "SPT maximizes on-time rate; EDD minimizes maximum lateness",
                 fontsize=10.5, fontweight="bold", y=0.97)

    metrics = [
        (axes[0], "On-Time Rate (%)",    ON_TIME,  115, True),
        (axes[1], "Avg Flow Time (s)",   AVG_FLOW,  80, False),
        (axes[2], "Max Lateness (s)",    MAX_LATE, 1300, False),
    ]

    def draw(frame):
        for ax, title, vals, ylim_max, higher_better in metrics:
            ax.clear()
            ax.set_facecolor("#F9F9F9")
            ax.set_title(title, fontsize=9)
            ax.set_ylim(0, ylim_max)
            ax.set_xticks([0, 1, 2])
            ax.set_xticklabels(RULES, fontsize=8.5)
            ax.grid(axis="y", alpha=0.3)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            best_idx = (np.argmax(vals) if higher_better else np.argmin(vals))

            for i in range(3):
                prog = (frame - i * FRAMES_PER) / FRAMES_PER
                h = float(np.clip(vals[i] * prog, 0, vals[i]))
                ec = "#FFD600" if i == best_idx else "none"
                lw = 2.5 if i == best_idx else 0
                ax.bar(i, h, color=COLORS[i], width=0.6, alpha=0.88,
                       edgecolor=ec, linewidth=lw, zorder=3)
                if h > ylim_max * 0.06:
                    ax.text(i, h + ylim_max * 0.01, f"{vals[i]:.1f}",
                            ha="center", va="bottom", fontsize=8, fontweight="bold")

        fig.tight_layout(rect=[0, 0, 1, 0.92])

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=60, repeat=True, repeat_delay=800)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
