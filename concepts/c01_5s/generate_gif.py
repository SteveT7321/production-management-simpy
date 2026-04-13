"""
C01 GIF：5S 雷達圖 — 現況 vs 目標
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

LABELS   = ["S1\nSeiri\n(Sort)", "S2\nSeiton\n(Set)",
            "S3\nSeiso\n(Shine)", "S4\nSeiketsu\n(Standardize)",
            "S5\nShitsuke\n(Sustain)"]
CURRENT  = [4, 2, 4, 2, 2]    # /12 per dimension
TARGET   = [8, 9, 9, 8, 9]


def main():
    N     = len(LABELS)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    c_vals = [v / 12 for v in CURRENT] + [CURRENT[0] / 12]
    t_vals = [v / 12 for v in TARGET]  + [TARGET[0] / 12]

    DRAW_FRAMES = 40
    HOLD        = 25
    total       = DRAW_FRAMES + HOLD

    fig, ax = plt.subplots(figsize=(7, 6),
                           subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("white")
    fig.suptitle("C01: 5S Maturity Radar\n"
                 "Current vs Target (each axis = 0 to 100%)",
                 fontsize=11, fontweight="bold", y=1.02)

    def draw(frame):
        ax.clear()
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(LABELS, fontsize=8)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7)
        ax.set_ylim(0, 1)
        ax.grid(color="#cccccc", linewidth=0.5)

        prog = min(frame / DRAW_FRAMES, 1.0)

        # Target polygon (faded background)
        t_interp = [t * prog for t in t_vals]
        ax.fill(angles, t_interp, color="#4CAF50", alpha=0.18)
        ax.plot(angles, t_interp, color="#4CAF50", linewidth=2,
                linestyle="--", label=f"Target  ({round(sum(TARGET)/60*100)}%)")

        # Current polygon
        c_interp = [c * prog for c in c_vals]
        ax.fill(angles, c_interp, color="#F44336", alpha=0.30)
        ax.plot(angles, c_interp, color="#F44336", linewidth=2.5,
                label=f"Current ({round(sum(CURRENT)/60*100)}%)")

        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1),
                  fontsize=9, framealpha=0.9)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=70, repeat=True, repeat_delay=1000)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=13), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
