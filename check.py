"""快速驗證腳本：執行基礎模擬並印出乾淨的報告"""
import random
random.seed(42)
from simulation.smt_line import SMTLine

line = SMTLine()
stats = line.run()
s = stats.summary()
print("Throughput:", s["throughput_per_hour"], "pcs/hr")
print("FPY:", s["fpy_pct"], "%")
print("Avg WIP:", s["avg_wip"])
print("Bottleneck:", s["bottleneck"])
print("Littles Law error:", s["littles_law"]["error_pct"], "%")
print("--- OEE per station ---")
for name, d in stats.oee_report().items():
    print(f"  {name}: OEE={d['oee']*100:.1f}%  util={d['utilization']*100:.1f}%  failures={d['failure_count']}")
