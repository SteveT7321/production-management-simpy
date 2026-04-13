"""
C02 GIF：VSM — VA vs NVA 堆疊橫條，三種狀態比較
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

STATES   = ["Push\n(Current)", "Kanban+PM\n(Ch06/07)", "Lean Target\n(PCE>=25%)"]
VA_TIME  = [143, 143, 143]            # seconds, fixed
TOTAL_LT = [3095, 1559, 572]
NVA_TIME = [lt - va for va, lt in zip(VA_TIME, TOTAL_LT)]
PCE      = [round(va / lt * 100, 1) for va, lt in zip(VA_TIME, TOTAL_LT)]

COLORS_VA  = "#4CAF50"
COLORS_NVA = "#F44336"


def main():
    n         = len(STATES)
    y         = np.arange(n)
    max_width = max(TOTAL_LT) * 1.15

    FRAMES_PER = 10
    HOLD       = 28
    total      = n * FRAMES_PER + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("C02: Value Stream Map — VA vs NVA Lead Time\n"
                     "PCE = VA Time / Total Lead Time  (Green = value-added)",
                     fontsize=10.5, fontweight="bold", pad=8)
        ax.set_xlabel("Lead Time (seconds)", fontsize=9)
        ax.set_xlim(0, max_width)
        ax.set_yticks(y)
        ax.set_yticklabels(STATES, fontsize=9)
        ax.grid(axis="x", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        for i in range(n):
            prog = (frame - i * FRAMES_PER) / FRAMES_PER
            va_w  = float(np.clip(VA_TIME[i]  * prog, 0, VA_TIME[i]))
            nva_w = float(np.clip(NVA_TIME[i] * prog, 0, NVA_TIME[i]))

            ax.barh(y[i], va_w, color=COLORS_VA,  height=0.5, alpha=0.9,
                    label="VA (Value-Added)" if i == 0 else "")
            ax.barh(y[i], nva_w, left=va_w, color=COLORS_NVA, height=0.5,
                    alpha=0.75, label="NVA (Waste)" if i == 0 else "")

            if nva_w + va_w > 50:
                total_shown = va_w + nva_w
                ax.text(total_shown + 20, y[i],
                        f"{TOTAL_LT[i]} s  PCE={PCE[i]}%",
                        va="center", fontsize=8.5, fontweight="bold",
                        color="#1A237E")

        ax.legend(loc="lower right", fontsize=9, framealpha=0.9)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=65, repeat=True, repeat_delay=800)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
