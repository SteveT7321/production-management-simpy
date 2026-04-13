"""
Ch07 GIF：PM 預防保養 — 故障次數與產出率比較
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

SCENARIOS   = ["No PM", "With PM"]
THROUGHPUT  = [102.4, 109.3]
FAILURES    = [21,      9]
C1          = "#F44336"   # red = no PM
C2          = "#4CAF50"   # green = with PM


def main():
    FRAMES_PER = 10
    HOLD       = 28
    total      = 2 * FRAMES_PER + HOLD

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 5))
    fig.patch.set_facecolor("white")
    fig.suptitle("Ch07: Preventive Maintenance\n"
                 "PM halves failures and raises throughput by +6.9 pcs/hr",
                 fontsize=11, fontweight="bold", y=0.97)

    def draw(frame):
        for ax in (ax1, ax2):
            ax.clear()
            ax.set_facecolor("#F9F9F9")
            ax.grid(axis="y", alpha=0.3)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        # Left: Throughput
        ax1.set_title("Throughput (pcs/hr)", fontsize=9)
        ax1.set_ylim(0, 130)
        ax1.set_xticks([0, 1])
        ax1.set_xticklabels(SCENARIOS, fontsize=9)

        # Right: Failures
        ax2.set_title("Total Failures (8-hr shift)", fontsize=9)
        ax2.set_ylim(0, 28)
        ax2.set_xticks([0, 1])
        ax2.set_xticklabels(SCENARIOS, fontsize=9)

        colors = [C1, C2]
        for i in range(2):
            prog = (frame - i * FRAMES_PER) / FRAMES_PER
            h1 = float(np.clip(THROUGHPUT[i] * prog, 0, THROUGHPUT[i]))
            h2 = float(np.clip(FAILURES[i] * prog, 0, FAILURES[i]))
            ax1.bar(i, h1, color=colors[i], width=0.55, alpha=0.88)
            ax2.bar(i, h2, color=colors[i], width=0.55, alpha=0.88)
            if h1 > 3:
                ax1.text(i, h1 + 1, f"{THROUGHPUT[i]:.1f}",
                         ha="center", va="bottom", fontsize=9, fontweight="bold")
            if h2 > 0.5:
                ax2.text(i, h2 + 0.4, str(FAILURES[i]),
                         ha="center", va="bottom", fontsize=9, fontweight="bold")

        # Improvement arrows
        if frame >= 2 * FRAMES_PER:
            ax1.annotate("", xy=(1, THROUGHPUT[1]), xytext=(0, THROUGHPUT[0]),
                         arrowprops=dict(arrowstyle="->", color="#1B5E20", lw=1.8))
            ax1.text(0.5, 111, "+6.9", ha="center", color="#1B5E20",
                     fontsize=10, fontweight="bold")
            ax2.annotate("", xy=(1, FAILURES[1]), xytext=(0, FAILURES[0]),
                         arrowprops=dict(arrowstyle="->", color="#B71C1C", lw=1.8))
            ax2.text(0.5, 16, "-57%", ha="center", color="#B71C1C",
                     fontsize=10, fontweight="bold")

        fig.tight_layout(rect=[0, 0, 1, 0.93])

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=60, repeat=True, repeat_delay=800)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
