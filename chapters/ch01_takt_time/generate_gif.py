"""
Ch01 GIF：各站稼動率 vs Takt Time 瓶頸一目了然
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

STATIONS   = ["Screen\nPrinter", "SPI", "Chip\nShooter", "Flex\nPlacer",
              "Reflow\nOven", "AOI"]
UTIL       = [55.2, 43.8, 99.1, 70.5, 71.3, 84.7]   # utilization %
COLORS     = ["#2196F3", "#2196F3", "#F44336", "#2196F3", "#2196F3", "#FF9800"]

SAVE_PATH  = os.path.join(os.path.dirname(__file__), "preview.gif")


def main():
    TAKT_REF = 100.0      # 100 % = machine must run every takt unit
    max_val  = 115

    FRAMES_PER_BAR = 8
    HOLD           = 28
    total          = len(STATIONS) * FRAMES_PER_BAR + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")
    x = np.arange(len(STATIONS))

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("Ch01: Station Utilization & Bottleneck\n"
                     "Red bar = bottleneck (utilization ≈ 100 %)",
                     fontsize=11, fontweight="bold", pad=8)
        ax.set_ylabel("Utilization (%)", fontsize=9)
        ax.set_ylim(0, max_val)
        ax.set_xticks(x)
        ax.set_xticklabels(STATIONS, fontsize=8.5)
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Takt reference line
        ax.axhline(TAKT_REF, color="#E53935", linewidth=1.8,
                   linestyle="--", alpha=0.9, zorder=5)
        ax.text(len(STATIONS) - 0.4, TAKT_REF + 1.5,
                "Takt limit (100%)", color="#E53935", fontsize=8)

        for i in range(len(STATIONS)):
            prog = (frame - i * FRAMES_PER_BAR) / FRAMES_PER_BAR
            h = float(np.clip(UTIL[i] * prog, 0, UTIL[i]))
            ax.bar(x[i], h, color=COLORS[i], width=0.62, alpha=0.88, zorder=3)
            if h > 5:
                ax.text(x[i], h + 1, f"{UTIL[i]:.1f}%",
                        ha="center", va="bottom", fontsize=8.5, fontweight="bold")

        # Throughput note
        if frame >= len(STATIONS) * FRAMES_PER_BAR:
            ax.text(0.02, 0.94, "Throughput: 102.4 pcs/hr  |  Takt: 36 s",
                    transform=ax.transAxes, fontsize=8.5,
                    color="#1565C0", bbox=dict(facecolor="#E3F2FD", alpha=0.8,
                                              edgecolor="none", pad=3))

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=60, repeat=True, repeat_delay=800)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
