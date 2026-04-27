# Project Description

## 1. Project Overview

- **Project Name:** Tower Defence 3D — Protect your base from evil Thing
- **Brief Description:**  
  Tower Defence 3D is a game that merges the strategic depth of tower defence with the immersion of a 3D third-person shooter. Built entirely with Python and Pygame, the game uses a custom software 3D renderer based on the Painter's Algorithm — no external 3D engine or OpenGL is used. The player navigates a 3D world, physically walks to a shop to purchase towers, and places them on a grid to defend a base from enemy waves.

  The game features 10 levels (including 2 boss levels), 9 tower types, 8+ enemy types, a phase-based boss system, and a full statistical data recording system that exports CSV files and generates matplotlib graphs after each session.

- **Problem Statement:**  
  Most tower defence games lack immersion due to a top-down 2D view. This project explores how a first/third-person 3D perspective and real-time player agency (walking, placing towers manually) can increase player engagement while maintaining the strategic elements of classic tower defence.

- **Target Users:**  
  Casual gamers interested in tower defence, students studying 3D rendering and game development with Python.

- **Key Features:**
  - Custom software 3D renderer (Painter's Algorithm, billboard sprites, polygon depth sorting)
  - 10 levels with progressive enemy variety and wave difficulty
  - 9 purchasable tower types unlocked by level
  - 8+ enemy types with unique behaviors (teleport, spawn minions, egg→chicken transform)
  - Phase-based boss system with enemy summoning
  - In-world shop (player must physically walk to purchase)
  - Wave-based music transitions and SFX system
  - Statistical data recording: CSV export + matplotlib graph visualization

- **Screenshots:**  
  [screenshots]

- **Proposal:** [PDF proposal]

- **YouTube Presentation:** [link YouTube]

---

## 2. Concept

### 2.1 Background

This project was inspired by *Plants vs. Zombies* (PopCap, 2009) — a lane-based tower defence game where players place units on a grid to stop waves of enemies. The key improvement in this project is upgrading from a 2D top-down view to a full 3D third-person perspective, giving the player physical presence in the world and making tower management feel more interactive and immersive.

The problem being solved is the lack of player agency and immersion in traditional 2D tower defence games.

### 2.2 Objectives

- Implement a functional 3D game using only Python, Pygame, and NumPy (no game engines)
- Create a strategic tower defence loop with wave progression and economy management
- Design a boss system with multi-phase difficulty scaling
- Record meaningful gameplay statistics and visualize them with graphs

---

## 3. UML Class Diagram

[TODO: ใส่รูป UML หรือ embed จาก PDF]

**UML PDF:** [TODO: ใส่ link หรือชื่อไฟล์ PDF]

---

## 4. Object-Oriented Programming Implementation

| Class | Description |
|-------|-------------|
| `SoftwareRender` | Core renderer and game loop. Manages scene, entities, and draw pipeline |
| `Camera` | 3D camera with yaw/pitch, produces view matrix |
| `Projection` | Projects 3D world coordinates to 2D screen coordinates |
| `Player` | Third-person player with movement, gravity, animation arms |
| `Enemy` | Billboard sprite enemy with waypoint pathfinding, HP, and special abilities |
| `Boss` | Stationary boss with phase system, enemy summoning, and billboard rendering |
| `Tower` | Grid-placed auto-targeting turret loaded from OBJ files |
| `WaveManager` | CSV-driven wave spawner with timing and between-wave delays |
| `AudioManager` | Music/SFX manager with wave-based transitions and USEREVENT chaining |
| `StatsRecorder` | Records gameplay data (kills, HP, currency, towers) and saves CSV + PNG graphs |
| `Map` | Renders the placement grid, lane dividers, and ground tiles |
| `Inventory` | Manages equipped items (currently Wrench) |
| `Wrench` | Equippable item for placing/removing towers on the grid |
| `ShopGUI` | In-world shop UI for purchasing towers with gold |
| `TowerSelectUI` | UI panel for selecting which tower to place from inventory |
| `PauseMenu` | ESC pause overlay with Resume/Main Menu |
| `VictoryScreen` | Victory overlay shown when all waves are cleared |
| `GameOverScreen` | Game over overlay shown when base HP reaches 0 |
| `MainMenu` | Title screen with Play/Tutorial/Settings/Exit |
| `LevelSelectScreen` | Level selection grid with locked/unlocked/boss level states |
| `SettingsScreen` | Volume sliders and fullscreen toggle with live update |
| `TutorialScreen` | Image slideshow from `image/tutorial/` folder |

---

## 5. Statistical Data

### 5.1 Data Recording Method

Data is collected in real time during gameplay via `StatsRecorder` (in `world/stats_recorder.py`). When the game ends (victory or game over), all data is saved as CSV files to `data/stats/` and a PNG graph is generated automatically using matplotlib (non-blocking background thread).

### 5.2 Data Features

| Feature | Description | Collection Point | Visualization |
|---------|-------------|-----------------|---------------|
| Base HP Over Waves | Tracks base HP at the end of each wave | `WaveManager` on wave complete | Line graph |
| Enemies Killed per Wave | Count of enemies killed in each wave | `Enemy.die()` | Bar graph |
| Enemy Lifespan | Time (seconds) from spawn to death for each enemy | `Enemy.die()` - `Enemy._spawn_time` | Histogram + mean line |
| Tower Purchases | Which tower type was bought and in which wave | `ShopGUI._buy()` | Pie chart |
| Currency Flow | All earn/spend transactions (kill reward, wave bonus, passive, shop spend) | Multiple hooks | Summary statistics (mean/median/SD) |

---

## 6. Changed Proposed Features

- Removed weapon/projectile system from original proposal (caused performance issues with software renderer)
- Added boss level system (levels 5 and 10) not in original proposal
- Added passive income (+15g every 10s) and wave clear bonus
- Audio system with CSV-driven track list added beyond original scope

---

## 7. External Sources

- [credit]
- Example: `image/boss.png` — [source / license]
- Example: `music/stx_boss.mp3` — [source / license]
