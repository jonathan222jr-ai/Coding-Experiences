# Learn to Fly — Godot 4 Project

A penguin launcher game inspired by the classic "Learn to Fly" series.
Built for Godot 4.2+.

## How to open

1. Download and install **Godot 4.2** (or newer) from https://godotengine.org
2. Open Godot → click **Import** → select the `project.godot` file in this folder
3. Press **F5** (or the Play button) to run

## How to play

| Action | Key / Button |
|--------|-------------|
| Start power meter | Space / Launch button |
| Fire at current angle | Space / Fire button |
| Mid-air rocket boost | B / Boost button |
| Open upgrade shop | "Upgrades Shop" button (top-right) |

## Project structure

```
learn_to_fly/
├── project.godot          ← Godot project config (autoloads GameData)
├── scenes/
│   ├── Main.tscn          ← Main game scene (launch + flight)
│   └── Shop.tscn          ← Upgrades shop scene
└── scripts/
    ├── GameData.gd        ← Autoload singleton: coins, upgrades, derived stats
    ├── Main.gd            ← Game loop: power meter, physics, HUD, camera
    ├── Penguin.gd         ← Penguin visual drawn via _draw() — no sprites needed
    └── Shop.gd            ← Shop UI: buy upgrades, back to game
```

## Upgrades

| Upgrade | Max level | Effect |
|---------|-----------|--------|
| Ramp Angle | 5 | +80 launch speed per level |
| Glider Wings | 5 | Reduces gravity & fall speed |
| Rocket Booster | 4 | +220 horizontal speed on boost |
| Aerodynamic Suit | 5 | Reduces air drag |

Coins earned = `distance ÷ 10` per flight.

## Extending the game

- **Add more upgrades**: edit `GameData.gd` (add entry to `upgrades`, `UPGRADE_MAX`, etc.)
  then add a row in `Shop.gd`'s `UPGRADES` array.
- **Add sprites**: replace the `_draw()` calls in `Penguin.gd` with `Sprite2D` nodes.
- **Add sound**: attach an `AudioStreamPlayer` to Main and play it on launch/land.
- **Parallax background**: add a `ParallaxBackground` node in `Main.tscn`.
- **Save/load**: add `save()` / `load()` methods to `GameData.gd` using `FileAccess`.
