"""
Ch11 GIF：SPC — 製程漂移偵測，FPY 時序折線
"""
import sys, os, random
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'visualization'))

import importlib.util, sys as _sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

_spec = importlib.util.spec_from_file_location(
    "ch11_sim",
    os.path.join(os.path.dirname(__file__), "simulation.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_sys.modules["ch11_sim"] = _mod
_spec.loader.exec_module(_mod)
SPCLine = _mod.SPCLine

SAVE_PATH = os.path.join(os.path.dirname(__file__), "preview.gif")

WINDOW_S   = 600   # 每 600 秒計算一次滾動 FPY（10 分鐘）
SIM_DUR    = 28800


def rolling_fpy(completed_pcbs, window=WINDOW_S, duration=SIM_DUR):
    """將完工 PCB 依完成時間分組，計算每個時窗的 FPY"""
    buckets = int(duration / window)
    fpy_series = []
    for b in range(buckets):
        t0 = b * window
        t1 = t0 + window
        pcbs_in = [p for p in completed_pcbs
                   if p.finish_time is not None and t0 <= p.finish_time < t1]
        if not pcbs_in:
            fpy_series.append(None)
        else:
            no_rework = sum(1 for p in pcbs_in if p.rework_count == 0)
            fpy_series.append(no_rework / len(pcbs_in) * 100)
    return fpy_series


def run_spc_scenario(enable_drift, enable_spc, seed=42):
    random.seed(seed)
    line  = SPCLine(enable_drift=enable_drift, enable_spc=enable_spc)
    stats = line.run()
    return rolling_fpy(stats.completed_pcbs)


def main():
    print("Running SPC scenarios (takes ~30s)...")
    data = [
        ("No Drift",        run_spc_scenario(False, False), "#4CAF50"),
        ("Drift, No SPC",   run_spc_scenario(True,  False), "#F44336"),
        ("Drift + SPC",     run_spc_scenario(True,  True),  "#2196F3"),
    ]
    print("Done.")

    buckets  = int(SIM_DUR / WINDOW_S)
    t_hr     = np.array([(b + 0.5) * WINDOW_S / 3600 for b in range(buckets)])

    DRAW_FRAMES = 55
    HOLD        = 25
    total       = DRAW_FRAMES + HOLD

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")

    def draw(frame):
        ax.clear()
        ax.set_facecolor("#F9F9F9")
        ax.set_title("Ch11: SPC — Detecting Process Drift\n"
                     "Without SPC, FPY silently degrades; SPC catches drift within ~4 min",
                     fontsize=10.5, fontweight="bold", pad=8)
        ax.set_xlabel("Simulated Time (hours)", fontsize=9)
        ax.set_ylabel("FPY % (10-min window)", fontsize=9)
        ax.set_xlim(0, SIM_DUR / 3600)
        ax.set_ylim(90, 101)
        ax.grid(alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        n_show = max(int(min(frame, DRAW_FRAMES) / DRAW_FRAMES * buckets), 2)

        # Drift start marker
        drift_hr = 3600 / 3600  # drift starts at 1h
        ax.axvline(drift_hr, color="#FF9800", linewidth=1.5,
                   linestyle="--", alpha=0.7, zorder=2)
        ax.text(drift_hr + 0.05, 100.5, "Drift\nstart",
                color="#FF9800", fontsize=7.5)

        for label, series, color in data:
            ys = [v if v is not None else float("nan") for v in series[:n_show]]
            ax.plot(t_hr[:len(ys)], ys, color=color, linewidth=2.2,
                    label=label, zorder=3)
            if len(ys) >= 1 and not np.isnan(ys[-1]):
                ax.text(t_hr[len(ys) - 1] * 1.005, ys[-1],
                        f"  {ys[-1]:.1f}%", color=color,
                        fontsize=7.5, va="center", fontweight="bold")

        ax.legend(loc="lower left", fontsize=8, framealpha=0.8)

    ani = animation.FuncAnimation(fig, draw, frames=total,
                                  interval=80, repeat=True, repeat_delay=1000)
    ani.save(SAVE_PATH, writer=animation.PillowWriter(fps=12), dpi=100)
    plt.close(fig)
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
