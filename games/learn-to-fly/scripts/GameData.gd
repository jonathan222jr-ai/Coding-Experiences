extends Node

# Persistent game data across scenes
var coins: int = 0
var best_distance: float = 0.0
var total_flights: int = 0

# Upgrade levels (0 = not bought, max varies)
var upgrades: Dictionary = {
	"ramp":   0,  # max 5 — improves launch power
	"wings":  0,  # max 5 — reduces gravity / glide
	"rocket": 0,  # max 4 — mid-air boost
	"suit":   0,  # max 5 — reduces drag
}

const UPGRADE_MAX: Dictionary = {
	"ramp":   5,
	"wings":  5,
	"rocket": 4,
	"suit":   5,
}

const UPGRADE_BASE_COST: Dictionary = {
	"ramp":   30,
	"wings":  50,
	"rocket": 80,
	"suit":   40,
}

func upgrade_cost(id: String) -> int:
	var lvl = upgrades[id]
	return int(UPGRADE_BASE_COST[id] * pow(1.6, lvl))

func can_afford(id: String) -> bool:
	if upgrades[id] >= UPGRADE_MAX[id]:
		return false
	return coins >= upgrade_cost(id)

func buy_upgrade(id: String) -> bool:
	if not can_afford(id):
		return false
	coins -= upgrade_cost(id)
	upgrades[id] += 1
	return true

# ---- Derived launch stats ----
func get_launch_power() -> float:
	return 480.0 + upgrades["ramp"] * 80.0

func get_launch_angle_range() -> Vector2:
	# min/max angle in degrees; ramp widens the sweet spot
	return Vector2(20.0, 65.0 + upgrades["ramp"] * 3.0)

func get_gravity_scale() -> float:
	return 1.0 - upgrades["wings"] * 0.07

func get_drag() -> float:
	return 0.0012 - upgrades["suit"] * 0.00015

func get_boost_power() -> float:
	return upgrades["rocket"] * 220.0

func get_glide_factor() -> float:
	# multiplier on downward velocity each frame (wings slow falling)
	return 1.0 - upgrades["wings"] * 0.025
