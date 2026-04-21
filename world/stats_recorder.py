import csv
import os
import time
import threading
from collections import Counter


class StatsRecorder:
    def __init__(self, level=1):
        self.level         = level
        self._base_hp_log  = []   # (wave, base_hp)
        self._enemy_log    = []   # (enemy_type, wave, lifespan)
        self._currency_log = []   # (event, amount, wave)
        self._tower_log    = []   # (tower_type, wave)

    # ── record hooks ──────────────────────────────────────────────────

    def record_enemy_killed(self, enemy_type, wave, lifespan):
        self._enemy_log.append((enemy_type, wave, round(lifespan, 2)))

    def record_tower_buy(self, tower_type, wave):
        self._tower_log.append((tower_type, wave))

    def record_currency(self, event, amount, wave):
        self._currency_log.append((event, amount, wave))

    def record_wave_end(self, wave, base_hp):
        # avoid duplicate entries for same wave
        if not self._base_hp_log or self._base_hp_log[-1][0] != wave:
            self._base_hp_log.append((wave, base_hp))

    # ── save ──────────────────────────────────────────────────────────

    def save_and_show(self):
        ts = time.strftime('%Y%m%d_%H%M%S')
        os.makedirs('data/stats', exist_ok=True)
        self._save(ts)
        threading.Thread(target=self._save_graphs, args=(ts,), daemon=True).start()

    def _save(self, ts):
        def write(name, header, rows):
            with open(f'data/stats/{name}_{ts}.csv', 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(rows)

        write('base_hp',  ['wave', 'base_hp'],               self._base_hp_log)
        write('enemies',  ['enemy_type', 'wave', 'lifespan'], self._enemy_log)
        write('currency', ['event', 'amount', 'wave'],        self._currency_log)
        write('towers',   ['tower_type', 'wave'],             self._tower_log)
        print(f'[Stats] CSV saved → data/stats/ ({ts})')

    # ── graphs ────────────────────────────────────────────────────────

    def _save_graphs(self, ts):
        try:
            import matplotlib
            matplotlib.use('Agg')   # non-interactive — no window
            import matplotlib.pyplot as plt
            import statistics

            fig, axes = plt.subplots(2, 2, figsize=(13, 8))
            fig.suptitle(f'Level {self.level}  –  Game Statistics', fontsize=14, fontweight='bold')

            # ── 1. Base HP over wave (line) ──────────────────────────
            ax = axes[0, 0]
            if self._base_hp_log:
                ws, hps = zip(*self._base_hp_log)
                max_hp  = hps[0] if hps else 300
                ax.plot(ws, hps, 'r-o', linewidth=2, markersize=7)
                ax.fill_between(ws, hps, alpha=0.12, color='red')
                ax.set_ylim(0, max_hp * 1.08)
                ax.set_xticks(ws)
            ax.set_xlabel('Wave'); ax.set_ylabel('Base HP')
            ax.set_title('Base HP Over Waves'); ax.grid(True, alpha=0.3)

            # ── 2. Enemies killed per wave (bar) ─────────────────────
            ax = axes[0, 1]
            if self._enemy_log:
                wave_kills = Counter(w for _, w, _ in self._enemy_log)
                ws2 = sorted(wave_kills)
                ax.bar(ws2, [wave_kills[w] for w in ws2],
                       color='steelblue', edgecolor='black', alpha=0.8)
                ax.set_xticks(ws2)
            ax.set_xlabel('Wave'); ax.set_ylabel('Enemies Killed')
            ax.set_title('Enemies Killed per Wave'); ax.grid(True, alpha=0.3, axis='y')

            # ── 3. Enemy lifespan histogram ───────────────────────────
            ax = axes[1, 0]
            lifespans = [ls for _, _, ls in self._enemy_log if ls > 0]
            if lifespans:
                ax.hist(lifespans, bins=min(20, len(lifespans)),
                        color='mediumseagreen', edgecolor='black', alpha=0.75)
                mean_ls = statistics.mean(lifespans)
                ax.axvline(mean_ls, color='red', linestyle='--', linewidth=2,
                           label=f'Mean: {mean_ls:.1f}s')
                ax.legend(fontsize=9)
            ax.set_xlabel('Lifespan (seconds)'); ax.set_ylabel('Frequency')
            ax.set_title('Enemy Lifespan Distribution'); ax.grid(True, alpha=0.3, axis='y')

            # ── 4. Tower purchases pie ────────────────────────────────
            ax = axes[1, 1]
            if self._tower_log:
                tc = Counter(t for t, _ in self._tower_log)
                ax.pie(tc.values(), labels=tc.keys(),
                       autopct='%1.0f%%', startangle=90,
                       wedgeprops={'edgecolor': 'white', 'linewidth': 1})
            else:
                ax.text(0.5, 0.5, 'No towers purchased',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=11, color='gray')
            ax.set_title('Tower Purchases')

            # ── currency summary text at bottom ───────────────────────
            if self._currency_log:
                earned = sum(a for ev, a, _ in self._currency_log if ev.startswith('earn'))
                spent  = sum(a for ev, a, _ in self._currency_log if ev.startswith('spend'))
                earn_vals = [a for ev, a, _ in self._currency_log if ev.startswith('earn')]
                summary = f'Currency — Earned: {earned}g | Spent: {spent}g'
                if len(earn_vals) > 1:
                    summary += (f'  |  Per-earn  mean: {statistics.mean(earn_vals):.1f}g'
                                f'  median: {statistics.median(earn_vals):.1f}g'
                                f'  SD: {statistics.stdev(earn_vals):.1f}g')
                fig.text(0.5, 0.01, summary, ha='center', fontsize=8.5, color='dimgray')

            plt.tight_layout(rect=[0, 0.04, 1, 1])
            out = f'data/stats/graphs_{ts}.png'
            fig.savefig(out, dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f'[Stats] Graph saved → {out}')
        except Exception as e:
            print(f'[Stats] Graph error: {e}')
