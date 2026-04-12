"""
生產統計計算模組

負責彙整模擬結果，計算：
- Throughput（產出率）
- WIP（在製品數量）
- Takt Time vs Cycle Time
- OEE per station
- FPY（First Pass Yield）
- Little's Law 驗證
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import statistics as stats


@dataclass
class LineStats:
    """單次模擬結束後的彙整報告"""

    sim_duration: float = 0.0
    warmup_time: float = 0.0

    # 完工 PCB 清單（warmup 後才計入）
    completed_pcbs: list = field(default_factory=list)
    scrapped_pcbs: list = field(default_factory=list)

    # WIP 時間序列（供 Little's Law 驗證）
    wip_samples: List[tuple] = field(default_factory=list)   # (time, wip_count)

    # 各站機台統計快照
    machine_snapshots: Dict[str, dict] = field(default_factory=dict)

    # ── 基礎指標 ──────────────────────────────────────────────────

    @property
    def effective_duration(self) -> float:
        return max(self.sim_duration - self.warmup_time, 1.0)

    @property
    def throughput(self) -> float:
        """每小時產出片數"""
        return len(self.completed_pcbs) / (self.effective_duration / 3600.0)

    @property
    def fpy(self) -> float:
        """First Pass Yield：一次通過率（未返工）"""
        total = len(self.completed_pcbs)
        if total == 0:
            return 0.0
        no_rework = sum(1 for p in self.completed_pcbs if p.rework_count == 0)
        return no_rework / total

    @property
    def scrap_rate(self) -> float:
        total = len(self.completed_pcbs) + len(self.scrapped_pcbs)
        if total == 0:
            return 0.0
        return len(self.scrapped_pcbs) / total

    @property
    def avg_cycle_time(self) -> float:
        """平均 Cycle Time（s）"""
        cts = [p.cycle_time for p in self.completed_pcbs if p.cycle_time]
        return stats.mean(cts) if cts else 0.0

    @property
    def avg_wip(self) -> float:
        """平均 WIP（Little's Law: WIP = Throughput × Lead Time）"""
        if not self.wip_samples:
            return 0.0
        return stats.mean(w for _, w in self.wip_samples)

    @property
    def littles_law_check(self) -> dict:
        """
        Little's Law 驗證
        WIP = λ × W
        λ = throughput（每秒），W = avg cycle time（s）
        """
        lam = len(self.completed_pcbs) / self.effective_duration  # 每秒
        predicted_wip = lam * self.avg_cycle_time
        return {
            "actual_avg_wip": round(self.avg_wip, 2),
            "predicted_wip_by_littles_law": round(predicted_wip, 2),
            "error_pct": round(
                abs(self.avg_wip - predicted_wip) / max(predicted_wip, 0.001) * 100, 1
            ),
        }

    # ── OEE ────────────────────────────────────────────────────────

    def oee_report(self) -> Dict[str, dict]:
        """各站 OEE 分解報告"""
        report = {}
        for name, snap in self.machine_snapshots.items():
            report[name] = {
                "display_name": snap.get("display_name", name),
                "oee": snap.get("oee", 0.0),
                "utilization": snap.get("utilization", 0.0),
                "total_processed": snap.get("total_processed", 0),
                "failure_count": snap.get("failure_count", 0),
            }
        return report

    # ── 瓶頸分析 ────────────────────────────────────────────────────

    def bottleneck_station(self) -> Optional[str]:
        """找出 utilization 最高的站點（瓶頸）"""
        if not self.machine_snapshots:
            return None
        return max(
            self.machine_snapshots,
            key=lambda k: self.machine_snapshots[k].get("utilization", 0)
        )

    # ── 報告輸出 ────────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "throughput_per_hour": round(self.throughput, 1),
            "avg_cycle_time_sec": round(self.avg_cycle_time, 1),
            "total_completed": len(self.completed_pcbs),
            "total_scrapped": len(self.scrapped_pcbs),
            "fpy_pct": round(self.fpy * 100, 2),
            "scrap_rate_pct": round(self.scrap_rate * 100, 3),
            "avg_wip": round(self.avg_wip, 1),
            "littles_law": self.littles_law_check,
            "bottleneck": self.bottleneck_station(),
        }

    def print_report(self):
        """富文字終端報告（用 rich 套件）"""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box

            console = Console()
            s = self.summary()

            console.print("\n[bold cyan]═══ SMT 產線模擬報告 ═══[/bold cyan]")
            console.print(f"  模擬時長（扣除暖機）: [yellow]{self.effective_duration/3600:.1f} hr[/yellow]")
            console.print(f"  產出率: [green]{s['throughput_per_hour']} pcs/hr[/green]")
            console.print(f"  平均 Cycle Time: {s['avg_cycle_time_sec']} s")
            console.print(f"  完工數量: {s['total_completed']}  |  報廢: {s['total_scrapped']}")
            console.print(f"  FPY: [green]{s['fpy_pct']}%[/green]  |  報廢率: {s['scrap_rate_pct']}%")
            console.print(f"  平均 WIP: {s['avg_wip']} pcs")

            ll = s["littles_law"]
            console.print(
                f"  Little's Law — 實際 WIP: {ll['actual_avg_wip']}  "
                f"預測: {ll['predicted_wip_by_littles_law']}  "
                f"誤差: {ll['error_pct']}%"
            )
            console.print(f"  [bold red]瓶頸站點: {s['bottleneck']}[/bold red]")

            # OEE 表格
            table = Table(title="各站 OEE", box=box.SIMPLE_HEAVY)
            table.add_column("站點", style="cyan")
            table.add_column("OEE", justify="right")
            table.add_column("稼動率", justify="right")
            table.add_column("加工數", justify="right")
            table.add_column("故障次數", justify="right")

            for name, row in self.oee_report().items():
                oee_color = "green" if row["oee"] >= 0.85 else "yellow" if row["oee"] >= 0.65 else "red"
                table.add_row(
                    row["display_name"],
                    f"[{oee_color}]{row['oee']*100:.1f}%[/{oee_color}]",
                    f"{row['utilization']*100:.1f}%",
                    str(row["total_processed"]),
                    str(row["failure_count"]),
                )
            console.print(table)

        except ImportError:
            # rich 未安裝，fallback 純文字
            s = self.summary()
            print("\n=== SMT 產線模擬報告 ===")
            for k, v in s.items():
                print(f"  {k}: {v}")
