"""
第三章：整體設備效率 — OEE (Overall Equipment Effectiveness)
執行：python chapters/ch03_oee/simulation.py
"""
import random, copy, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.smt_line import SMTLine
from simulation.config import MACHINE_CONFIGS, MachineConfig


def _improve_mtbf(configs, factor):
    improved = copy.deepcopy(configs)
    for name, cfg in improved.items():
        improved[name] = MachineConfig(**{**cfg.__dict__, "mtbf": cfg.mtbf * factor})
    return improved


def _improve_quality(configs, factor):
    improved = copy.deepcopy(configs)
    for name, cfg in improved.items():
        improved[name] = MachineConfig(
            **{**cfg.__dict__, "defect_rate": cfg.defect_rate * factor}
        )
    return improved


def _run(configs, label, seed):
    random.seed(seed)
    line = SMTLine(machine_configs=configs)
    stats = line.run()
    oee_data = stats.oee_report()
    avg_oee = sum(v["oee"] for v in oee_data.values()) / max(len(oee_data), 1)
    s = stats.summary()
    return {
        "scenario":        label,
        "avg_oee":         round(avg_oee, 3),
        "throughput_per_hr": s["throughput_per_hour"],
        "fpy_pct":         s["fpy_pct"],
        "per_station": {
            name: {"oee": v["oee"], "utilization": v["utilization"]}
            for name, v in oee_data.items()
        },
    }


def run(seed: int = 42) -> dict:
    sa = _run(MACHINE_CONFIGS,                     "A: 原始（基準）",           seed)
    sb = _run(_improve_mtbf(MACHINE_CONFIGS, 2.0), "B: MTBF×2（故障減半）",    seed)
    sc = _run(_improve_quality(MACHINE_CONFIGS, 0.5), "C: 不良率×0.5（品質↑）", seed)
    return {"scenarios": [sa, sb, sc], "world_class": 0.85}


def print_result(r: dict):
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box

    c = Console()
    c.print()
    c.print(Rule("[bold cyan]第三章　OEE 整體設備效率 — 模擬結果[/bold cyan]", style="cyan"))
    c.print()

    wc = r["world_class"]
    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("情境", style="cyan")
    t.add_column("整體 OEE", justify="right")
    t.add_column("vs 原始", justify="right")
    t.add_column("產出率", justify="right")
    t.add_column("FPY%", justify="right")

    base_oee = r["scenarios"][0]["avg_oee"]
    for s in r["scenarios"]:
        oee_pct = s["avg_oee"] * 100
        col = "green" if s["avg_oee"] >= wc else "yellow"
        delta = round((s["avg_oee"] - base_oee) * 100, 1)
        d_str = f"[green]＋{delta}%[/green]" if delta > 0 else "[dim]—[/dim]"
        t.add_row(s["scenario"], f"[{col}]{oee_pct:.1f}%[/{col}]",
                  d_str, str(s["throughput_per_hr"]), str(s["fpy_pct"]))
    c.print(t)

    c.print()
    c.print("  各站 OEE 明細（A / B / C）：")
    stations = list(r["scenarios"][0]["per_station"].keys())
    t2 = Table(box=box.MINIMAL)
    t2.add_column("站點", style="cyan", min_width=18)
    for s in r["scenarios"]:
        t2.add_column(s["scenario"][:6], justify="right")

    for stn in stations:
        row = [stn]
        for s in r["scenarios"]:
            pct = s["per_station"].get(stn, {}).get("oee", 0) * 100
            col = "green" if pct >= 85 else "yellow" if pct >= 60 else "red"
            row.append(f"[{col}]{pct:.1f}%[/{col}]")
        t2.add_row(*row)
    c.print(t2)

    c.print(f"\n  世界級標準：≥ {wc*100:.0f}%")
    c.print("  詳細概念說明請閱讀 README.md")
    c.print()


if __name__ == "__main__":
    print_result(run())
