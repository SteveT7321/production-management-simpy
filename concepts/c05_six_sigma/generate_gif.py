"""
C05 GIF：Six Sigma — 常態分布曲線，四種製程能力情境
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.stats import norm as _norm

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

LSL = 120.0
USL = 180.0
TARGET = 150.0

SCENARIOS = [
    ("Current (biased)",   158.0, 12.0, "#F44336"),
    ("Step 1: Centered",   150.0, 12.0, "#FF9800"),
    ("Step 2: Tighter",    150.0,  8.0, "#2196F3"),
    ("Step 3: Six Sigma",  150.0,  5.0, "#4CAF50"),
]


def main():
    x = np.linspace(85, 215, 500)
    FRAMES_PER = 10
    HOLD       = 28
    total      = len(SCENARIOS) * FRAMES_PER + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("C05: Process Capability — Solder Paste Thickness\n"
                     f"Spec: LSL={LSL:.0f} µm  Target={TARGET:.0f} µm  USL={USL:.0f} µm",
                     fontsize=11, fontweight="bold", pad=8)
        ax.set_xlabel("Thickness (µm)", fontsize=9)
        ax.set_ylabel("Probability Density", fontsize=9)
        ax.set_xlim(85, 215)
        ax.set_ylim(0, 0.092)
        ax.grid(alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Spec limits
        ax.axvline(LSL, color="#333333", linewidth=1.5, linestyle="--", alpha=0.7)
        ax.axvline(USL, color="#333333", linewidth=1.5, linestyle="--", alpha=0.7)
        ax.axvline(TARGET, color="#9E9E9E", linewidth=1.0, linestyle=":", alpha=0.5)
        ax.text(LSL - 1, 0.085, "LSL", ha="right", fontsize=8, color="#333333")
        ax.text(USL + 1, 0.085, "USL", ha="left",  fontsize=8, color="#333333")

        for si, (label, mu, sig, color) in enumerate(SCENARIOS):
            prog = (frame - si * FRAMES_PER) / FRAMES_PER
            if prog <= 0:
                break
            alpha = min(prog, 1.0)

            y = _norm.pdf(x, mu, sig)
            ax.plot(x, y, color=color, linewidth=2.3, alpha=alpha,
                    label=label)

            # Shade out-of-spec region
            mask_lo = x < LSL
            mask_hi = x > USL
            for mask in (mask_lo, mask_hi):
                ax.fill_between(x, y, where=mask, color=color,
                                alpha=0.18 * alpha)

            # Cpk annotation
            if alpha >= 1.0:
                cpk = min((USL - mu) / (3 * sig), (mu - LSL) / (3 * sig))
                ax.text(mu, _norm.pdf(mu, mu, sig) + 0.002,
                        f"Cpk={cpk:.2f}",
                        ha="center", fontsize=7.5, color=color, fontweight="bold")

        ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=65, repeat=True, repeat_delay=1000)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
