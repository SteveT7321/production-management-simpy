"""
C03 GIF：EOQ 成本曲線 — 訂購成本 + 持有成本 = 總成本 U 型碗
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import math

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

D  = 50_000     # annual demand
S  = 800.0      # ordering cost
H  = 24.0       # holding cost per unit per year
Q_OPT = math.sqrt(2 * D * S / H)   # ~1826


def costs(Q):
    order = D / Q * S
    hold  = Q / 2 * H
    return order, hold, order + hold


def main():
    Q_range = np.linspace(200, 5000, 300)
    ord_c, hld_c, tot_c = zip(*[costs(q) for q in Q_range])
    ord_c = np.array(ord_c)
    hld_c = np.array(hld_c)
    tot_c = np.array(tot_c)

    DRAW_FRAMES = 50
    HOLD        = 28
    total       = DRAW_FRAMES + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("C03: EOQ — Economic Order Quantity\n"
                     f"Optimal Q* = {Q_OPT:.0f} units  (minimises total cost)",
                     fontsize=11, fontweight="bold", pad=8)
        ax.set_xlabel("Order Quantity (units)", fontsize=9)
        ax.set_ylabel("Annual Cost (NT$)", fontsize=9)
        ax.set_xlim(200, 5000)
        ax.set_ylim(0, 160_000)
        ax.grid(alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        n_show = max(min(int(frame / DRAW_FRAMES * len(Q_range)), len(Q_range)), 2)

        ax.plot(Q_range[:n_show], ord_c[:n_show],
                color="#F44336", linewidth=2, label="Ordering cost (D/Q × S)")
        ax.plot(Q_range[:n_show], hld_c[:n_show],
                color="#2196F3", linewidth=2, label="Holding cost (Q/2 × H)")
        ax.plot(Q_range[:n_show], tot_c[:n_show],
                color="#4CAF50", linewidth=2.5, label="Total cost")

        # EOQ marker (show only when lines are long enough)
        if Q_range[n_show - 1] >= Q_OPT:
            tc_opt = costs(Q_OPT)[2]
            ax.scatter([Q_OPT], [tc_opt], color="#FFD600", s=120,
                       zorder=6, edgecolors="#E65100", linewidths=1.5)
            ax.annotate(f"EOQ = {Q_OPT:.0f}\nCost = {tc_opt:,.0f}",
                        xy=(Q_OPT, tc_opt),
                        xytext=(Q_OPT + 400, tc_opt + 15_000),
                        arrowprops=dict(arrowstyle="->", color="#333333"),
                        fontsize=8.5, color="#1A237E", fontweight="bold")

        ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=80, repeat=True, repeat_delay=1000)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=12), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
