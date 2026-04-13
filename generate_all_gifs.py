"""
一鍵產生所有章節的 preview.gif

執行：python generate_all_gifs.py

說明：
  - 靜態章節（ch01-ch05, ch07-ch08, concepts）：純數學計算，幾秒完成
  - 動態章節（ch06, ch09-ch12）：執行 SimPy 模擬，每個約 10-30 秒
  - 全部完成約 3-5 分鐘

生成的 GIF 路徑：
  chapters/ch0N_xxx/preview.gif
  concepts/c0N_xxx/preview.gif
"""

import subprocess
import sys
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

GIF_SCRIPTS = [
    # ── 模擬章節 ──────────────────────────────────────────────────
    "chapters/ch01_takt_time/generate_gif.py",
    "chapters/ch02_bottleneck/generate_gif.py",
    "chapters/ch03_oee/generate_gif.py",
    "chapters/ch04_smed/generate_gif.py",
    "chapters/ch05_quality/generate_gif.py",
    "chapters/ch06_kanban/generate_gif.py",       # runs simulation
    "chapters/ch07_maintenance/generate_gif.py",
    "chapters/ch08_scheduling/generate_gif.py",
    "chapters/ch09_heijunka/generate_gif.py",     # runs simulation
    "chapters/ch10_safety_stock/generate_gif.py", # runs simulation
    "chapters/ch11_spc/generate_gif.py",          # runs simulation
    "chapters/ch12_conwip/generate_gif.py",       # runs simulation
    # ── 概念工具 ──────────────────────────────────────────────────
    "concepts/c01_5s/generate_gif.py",
    "concepts/c02_vsm/generate_gif.py",
    "concepts/c03_eoq/generate_gif.py",
    "concepts/c04_mrp/generate_gif.py",
    "concepts/c05_six_sigma/generate_gif.py",
    "concepts/c06_aql/generate_gif.py",
]


def main():
    failed = []
    for script in GIF_SCRIPTS:
        path = os.path.join(ROOT, script)
        name = script.replace("\\", "/")
        print(f"\n[{GIF_SCRIPTS.index(script)+1}/{len(GIF_SCRIPTS)}] {name}")
        t0 = time.time()
        result = subprocess.run(
            [sys.executable, path],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            print(f"  ERROR ({elapsed:.1f}s):\n{result.stderr[-400:]}")
            failed.append(name)
        else:
            out = result.stdout.strip().splitlines()
            for line in out:
                print(f"  {line}")
            print(f"  ({elapsed:.1f}s)")

    print("\n" + "=" * 55)
    if failed:
        print(f"Failed ({len(failed)}):")
        for f in failed:
            print(f"  {f}")
    else:
        print(f"All {len(GIF_SCRIPTS)} GIFs generated successfully.")


if __name__ == "__main__":
    main()
