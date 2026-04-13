"""
GIF 動畫輔助工具

提供兩種核心動畫：
1. animated_bar_chart    — 章節情境比較（長條圖逐條展開）
2. animated_wip_lines    — WIP 時序折線（多情境同步繪製）
"""

import matplotlib
matplotlib.use("Agg")          # 無視窗後端，CI / 無顯示器環境皆可用

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from typing import List, Dict, Optional

# ── 全域配色 ──────────────────────────────────────────────────────
PALETTE = [
    "#2196F3",   # blue
    "#4CAF50",   # green
    "#FF9800",   # orange
    "#F44336",   # red
    "#9C27B0",   # purple
    "#00BCD4",   # cyan
]


def _setup_ax(ax, title: str, xlabel: str = "", ylabel: str = "",
              ylim: tuple = None, grid_axis: str = "y"):
    ax.set_facecolor("#F9F9F9")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(axis=grid_axis, alpha=0.35, linewidth=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def animated_bar_chart(
    categories: List[str],
    values: List[float],
    title: str,
    ylabel: str,
    save_path: str,
    colors: Optional[List[str]] = None,
    reference_line: Optional[float] = None,
    reference_label: str = "",
    fmt: str = "{:.1f}",
    figsize: tuple = (8, 5),
    highlight_idx: Optional[int] = None,
):
    """
    長條圖動畫：各條從左到右依序從 0 長高到終值，最後停住 2 秒。

    Parameters
    ----------
    categories : list of str     X 軸標籤
    values     : list of float   對應高度
    reference_line : float       可選：橫向參考線（如 Takt Time）
    highlight_idx  : int         某條特別用金色框線強調（最佳值）
    """
    colors = colors or PALETTE[: len(values)]
    max_val = max(max(values) * 1.25, 1)

    FRAMES_PER_BAR = 8
    HOLD_FRAMES    = 25
    n = len(values)
    total_frames   = n * FRAMES_PER_BAR + HOLD_FRAMES

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")

    x = np.arange(n)

    def _draw(frame):
        ax.clear()
        _setup_ax(ax, title, ylabel=ylabel, ylim=(0, max_val))
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=8.5, wrap=True)

        if reference_line is not None:
            ax.axhline(reference_line, color="#E53935", linewidth=1.5,
                       linestyle="--", alpha=0.85, zorder=5)
            ax.text(n - 0.5, reference_line, f" {reference_label}",
                    color="#E53935", fontsize=8, va="bottom")

        for i in range(n):
            prog = (frame - i * FRAMES_PER_BAR) / FRAMES_PER_BAR
            h = float(np.clip(values[i] * prog, 0, values[i]))

            ec = "#FFD600" if i == highlight_idx else "none"
            lw = 2.5      if i == highlight_idx else 0
            bar = ax.bar(x[i], h, color=colors[i], width=0.62,
                         alpha=0.88, edgecolor=ec, linewidth=lw, zorder=3)

            if h >= max_val * 0.06:
                ax.text(x[i], h + max_val * 0.01,
                        fmt.format(values[i]),
                        ha="center", va="bottom", fontsize=8.5,
                        fontweight="bold", color="#333333")

    ani = animation.FuncAnimation(fig, _draw, frames=total_frames,
                                  interval=60, repeat=True, repeat_delay=800)
    ani.save(save_path, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {save_path}")


def animated_grouped_bar(
    groups: List[str],
    series: List[Dict],       # [{'label': str, 'values': [...], 'color': str}]
    title: str,
    ylabel: str,
    save_path: str,
    figsize: tuple = (9, 5),
):
    """
    分組長條圖動畫：每個 series 的每組條從左往右依序長高。
    """
    n_groups = len(groups)
    n_series = len(series)
    width     = 0.7 / n_series
    max_val   = max(max(s["values"]) for s in series) * 1.25

    FRAMES_PER_GROUP = 8
    HOLD_FRAMES      = 25
    total_frames     = n_groups * FRAMES_PER_GROUP + HOLD_FRAMES

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")

    x = np.arange(n_groups)

    def _draw(frame):
        ax.clear()
        _setup_ax(ax, title, ylabel=ylabel, ylim=(0, max_val))
        ax.set_xticks(x)
        ax.set_xticklabels(groups, fontsize=8.5)

        for si, s in enumerate(series):
            offsets = x + (si - n_series / 2 + 0.5) * width
            for gi in range(n_groups):
                prog = (frame - gi * FRAMES_PER_GROUP) / FRAMES_PER_GROUP
                h = float(np.clip(s["values"][gi] * prog, 0, s["values"][gi]))
                ax.bar(offsets[gi], h, width=width * 0.9,
                       color=s["color"], alpha=0.85, zorder=3,
                       label=s["label"] if gi == 0 else "")
                if h >= max_val * 0.06:
                    ax.text(offsets[gi], h + max_val * 0.01,
                            f"{s['values'][gi]:.1f}",
                            ha="center", va="bottom", fontsize=7, color="#333333")

        ax.legend(loc="upper right", fontsize=8, framealpha=0.8)

    ani = animation.FuncAnimation(fig, _draw, frames=total_frames,
                                  interval=60, repeat=True, repeat_delay=800)
    ani.save(save_path, writer=animation.PillowWriter(fps=14), dpi=100)
    plt.close(fig)
    print(f"Saved: {save_path}")


def animated_wip_lines(
    scenarios: List[Dict],     # [{'label': str, 'wip_samples': [(t,w),...], 'color': str}]
    title: str,
    save_path: str,
    sim_duration: float = 28800,
    figsize: tuple = (9, 5),
    N_POINTS: int = 80,
):
    """
    WIP 時序動畫：多條折線同步從左往右繪出。

    Parameters
    ----------
    scenarios : 每個 dict 含 label、wip_samples（(time, wip) list）、color
    """
    t_grid = np.linspace(0, sim_duration, N_POINTS)
    t_hr   = t_grid / 3600

    interp = []
    for s in scenarios:
        ts = np.array([t for t, w in s["wip_samples"]])
        ws = np.array([w for t, w in s["wip_samples"]], dtype=float)
        if len(ts) < 2:
            ws_i = np.zeros(N_POINTS)
        else:
            ws_i = np.interp(t_grid, ts, ws)
        interp.append({**s, "t": t_hr, "w": ws_i})

    max_wip = max(max(s["w"]) for s in interp) * 1.15
    max_wip = max(max_wip, 1)

    DRAW_FRAMES = 55
    HOLD_FRAMES = 20
    total_frames = DRAW_FRAMES + HOLD_FRAMES

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")

    def _draw(frame):
        ax.clear()
        _setup_ax(ax, title, xlabel="Sim Time (hours)", ylabel="WIP (units)",
                  ylim=(0, max_wip), grid_axis="both")
        ax.set_xlim(0, sim_duration / 3600)

        n_show = max(int(min(frame, DRAW_FRAMES) / DRAW_FRAMES * N_POINTS), 2)

        for s in interp:
            ax.plot(s["t"][:n_show], s["w"][:n_show],
                    color=s["color"], linewidth=2.2, label=s["label"])
            if n_show >= N_POINTS:
                ax.text(s["t"][-1] * 1.005, s["w"][-1],
                        f"  {s['w'][-1]:.0f}", color=s["color"],
                        fontsize=8, va="center", fontweight="bold")

        ax.legend(loc="upper right", fontsize=8, framealpha=0.8)

    ani = animation.FuncAnimation(fig, _draw, frames=total_frames,
                                  interval=80, repeat=True, repeat_delay=1000)
    ani.save(save_path, writer=animation.PillowWriter(fps=12), dpi=100)
    plt.close(fig)
    print(f"Saved: {save_path}")
