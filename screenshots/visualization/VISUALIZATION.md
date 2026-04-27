# Data Visualization

This document describes the statistical data collected during gameplay and their visualizations.

All graphs are generated automatically at game end and saved to `data/stats/` as PNG files.

---

## Overview

[TODO: ใส่ screenshot ภาพรวมของ graph ทั้งหมด (graphs_YYYYMMDD_HHMMSS.png)]

The visualization consists of 4 graphs displayed in a 2×2 grid, plus a currency summary line at the bottom.

---

## 1. Base HP Over Waves (Line Graph)

[TODO: ใส่ screenshot crop เฉพาะกราฟนี้]

**Description:**  
Tracks the base's remaining HP at the end of each wave. A steep decline indicates waves where many enemies reached the base. A flat line indicates the player defended effectively.

- X-axis: Wave number  
- Y-axis: Base HP (max 300)  
- Red shaded area shows HP loss over time

---

## 2. Enemies Killed per Wave (Bar Graph)

[TODO: ใส่ screenshot crop เฉพาะกราฟนี้]

**Description:**  
Shows how many enemies were killed by towers (not counting enemies that reached the base) in each wave. Useful for evaluating tower effectiveness as difficulty increases.

- X-axis: Wave number  
- Y-axis: Number of enemies killed

---

## 3. Enemy Lifespan Distribution (Histogram)

[TODO: ใส่ screenshot crop เฉพาะกราฟนี้]

**Description:**  
Shows the distribution of how long enemies survived on the map before being killed. A left-skewed distribution (short lifespans) indicates powerful towers. The red dashed line shows the mean lifespan.

- X-axis: Lifespan in seconds  
- Y-axis: Frequency (number of enemies)  
- Red dashed line: Mean lifespan

---

## 4. Tower Purchases (Pie Chart)

[TODO: ใส่ screenshot crop เฉพาะกราฟนี้]

**Description:**  
Shows the proportion of each tower type purchased from the shop during the session. Reveals player strategy and preference (e.g., whether players prefer damage towers or economy towers).

---

## 5. Currency Summary (Statistics)

Displayed as a text summary below the graphs.

| Metric | Description |
|--------|-------------|
| Total Earned | Sum of all gold earned (kills + wave bonus + passive) |
| Total Spent | Sum of all gold spent at the shop |
| Per-earn Mean | Average gold per earning event |
| Per-earn Median | Median gold per earning event |
| Per-earn SD | Standard deviation of earning events |
