"""
第八章：生產排程規則 — FIFO / SPT / EDD

在製品排隊等待加工時，「哪一片先被服務」就是排程規則（Scheduling Rule）。
不同規則對準時交貨率、平均等待時間有截然不同的影響。

本章以單一瓶頸站＋混線生產為場景，驗證三大排程規則的理論效果。
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import simpy
from dataclasses import dataclass
from typing import List
from rich.console import Console
from rich.table import Table
from rich import box

# ── 模擬參數 ──────────────────────────────────────────────────────
RANDOM_SEED      = 42
SIM_DURATION     = 28800.0   # 8 小時
WARMUP_TIME      = 3600.0    # 1 小時暖機

# 3 種機種：A(急單/短)、B(一般/中)、C(寬鬆/長)
# 設計上 A 交期緊、C 加工最長 → 不同規則在 A/C 之間產生真正的取捨
PRODUCT_TYPES = {
    "A": {"proc_mean": 12.0, "proc_std": 2.0, "due_window": 80.0},
    "B": {"proc_mean": 22.0, "proc_std": 3.0, "due_window": 130.0},
    "C": {"proc_mean": 35.0, "proc_std": 5.0, "due_window": 110.0},
}
# 機種比例：A 40%、B 40%、C 20%
PRODUCT_MIX = ["A", "A", "B", "B", "C"]

# inter_arrival_mean=28s → 整體稼動率 ≈ 0.86
INTER_ARRIVAL_MEAN = 28.0


@dataclass
class Job:
    job_id: int
    product_type: str
    arrival_time: float
    proc_time: float
    due_date: float
    finish_time: float = 0.0

    @property
    def tardiness(self) -> float:
        return max(0.0, self.finish_time - self.due_date)

    @property
    def is_late(self) -> bool:
        return self.finish_time > self.due_date

    @property
    def flow_time(self) -> float:
        return self.finish_time - self.arrival_time


def run_scenario(rule: str, seed: int = RANDOM_SEED) -> dict:
    """
    rule: 'FIFO' | 'SPT' | 'EDD'

    SPT  (Shortest Processing Time)：加工時間最短的先做 → 最小化平均等待時間
    EDD  (Earliest Due Date)       ：交期最近的先做 → 最小化最大延誤
    FIFO (First In, First Out)     ：先到先服務 → 公平但兩者都不是最優
    """
    random.seed(seed)
    env = simpy.Environment()

    # PriorityResource：priority 值越小越優先
    server = simpy.PriorityResource(env, capacity=1)
    completed: List[Job] = []

    def process_job(job: Job):
        if rule == "SPT":
            priority = job.proc_time          # 短工件優先
        elif rule == "EDD":
            priority = job.due_date           # 交期早優先
        else:  # FIFO
            priority = job.arrival_time       # 先到先服務

        with server.request(priority=priority) as req:
            yield req
            yield env.timeout(job.proc_time)
            job.finish_time = env.now
            if env.now >= WARMUP_TIME:
                completed.append(job)

    def generator():
        job_id = 0
        while True:
            yield env.timeout(random.expovariate(1.0 / INTER_ARRIVAL_MEAN))
            ptype = random.choice(PRODUCT_MIX)
            cfg = PRODUCT_TYPES[ptype]
            proc_time = max(1.0, random.gauss(cfg["proc_mean"], cfg["proc_std"]))
            job_id += 1
            job = Job(
                job_id=job_id,
                product_type=ptype,
                arrival_time=env.now,
                proc_time=proc_time,
                due_date=env.now + cfg["due_window"],
            )
            env.process(process_job(job))

    env.process(generator())
    env.run(until=SIM_DURATION)

    if not completed:
        return {}

    avg_tardiness   = sum(j.tardiness for j in completed) / len(completed)
    max_tardiness   = max(j.tardiness for j in completed)
    on_time_rate    = sum(1 for j in completed if not j.is_late) / len(completed) * 100
    avg_flow_time   = sum(j.flow_time for j in completed) / len(completed)

    # 各機種準時率
    type_on_time = {}
    for ptype in ["A", "B", "C"]:
        jobs_of_type = [j for j in completed if j.product_type == ptype]
        if jobs_of_type:
            type_on_time[ptype] = round(
                sum(1 for j in jobs_of_type if not j.is_late) / len(jobs_of_type) * 100, 1
            )
        else:
            type_on_time[ptype] = 0.0

    return {
        "rule": rule,
        "completed": len(completed),
        "avg_tardiness_s": round(avg_tardiness, 1),
        "max_tardiness_s": round(max_tardiness, 1),
        "on_time_rate_pct": round(on_time_rate, 1),
        "avg_flow_time_s": round(avg_flow_time, 1),
        "on_time_A": type_on_time["A"],
        "on_time_B": type_on_time["B"],
        "on_time_C": type_on_time["C"],
    }


def main():
    console = Console()
    console.print(
        "\n[bold cyan]第八章　生產排程規則 — FIFO / SPT / EDD[/bold cyan]"
    )
    console.print(
        "  場景：單一瓶頸站，3 種機種混線（A=急單/短、B=一般/中、C=寬鬆/長）\n"
    )

    results = [run_scenario(rule) for rule in ["FIFO", "SPT", "EDD"]]

    # ── 總覽表 ──────────────────────────────────────────────────────
    t1 = Table(title="排程規則總覽", box=box.SIMPLE_HEAVY)
    t1.add_column("排程規則", style="cyan")
    t1.add_column("完工數", justify="right")
    t1.add_column("平均延誤(s)", justify="right")
    t1.add_column("最大延誤(s)", justify="right")
    t1.add_column("整體準時率", justify="right")
    t1.add_column("平均流程時間(s)", justify="right")

    for r in results:
        ot = r["on_time_rate_pct"]
        color = "green" if ot >= 90 else "yellow" if ot >= 75 else "red"
        t1.add_row(
            r["rule"],
            str(r["completed"]),
            str(r["avg_tardiness_s"]),
            str(r["max_tardiness_s"]),
            f"[{color}]{ot}%[/{color}]",
            str(r["avg_flow_time_s"]),
        )
    console.print(t1)

    # ── 各機種準時率 ────────────────────────────────────────────────
    t2 = Table(title="各機種準時率", box=box.SIMPLE_HEAVY)
    t2.add_column("排程規則", style="cyan")
    t2.add_column("A 急單/短(due=80s)", justify="right")
    t2.add_column("B 一般/中(due=130s)", justify="right")
    t2.add_column("C 寬鬆/長(due=110s)", justify="right")

    for r in results:
        t2.add_row(
            r["rule"],
            f"{r['on_time_A']}%",
            f"{r['on_time_B']}%",
            f"{r['on_time_C']}%",
        )
    console.print(t2)

    console.print(
        "\n[yellow]結論：[/yellow]\n"
        "  SPT  → 平均延誤最低（最小化平均等待時間，C 型工件受害）\n"
        "  EDD  → 整體準時率最高（最小化最大延誤，各型工件較均衡）\n"
        "  FIFO → 公平但兩者皆非最優\n"
        "\n  管理意涵：急單比例高 → 用 EDD；以降低平均 Lead Time 為目標 → 用 SPT"
    )


if __name__ == "__main__":
    main()
