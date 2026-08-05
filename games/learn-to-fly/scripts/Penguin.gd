extends Node2D

# Draws the penguin entirely via _draw() so no external art assets are needed.

func _draw() -> void:
	var wings_level = GameData.upgrades.get("wings", 0)
	var rocket_level = GameData.upgrades.get("rocket", 0)

	# ── Glider wings (if upgraded) ──────────────────────────────
	if wings_level > 0:
		var wing_span = 30.0 + wings_level * 10.0
		var wing_color = Color(0.2, 0.54, 0.87, 0.8)
		# Left wing
		var l_pts = PackedVector2Array([
			Vector2(-8, -12),
			Vector2(-wing_span, -28),
			Vector2(-8, 8)
		])
		draw_colored_polygon(l_pts, wing_color)
		# Right wing
		var r_pts = PackedVector2Array([
			Vector2(8, -12),
			Vector2(wing_span, -28),
			Vector2(8, 8)
		])
		draw_colored_polygon(r_pts, wing_color)

	# ── Rocket pack (if upgraded) ───────────────────────────────
	if rocket_level > 0:
		draw_rect(Rect2(Vector2(-6, 6), Vector2(12, 10)), Color(0.4, 0.4, 0.45))
		draw_rect(Rect2(Vector2(-4, 14), Vector2(4, 5)), Color(0.9, 0.35, 0.2))

	# ── Body ────────────────────────────────────────────────────
	draw_circle(Vector2.ZERO, 18.0, Color(0.13, 0.13, 0.13))

	# ── Belly ───────────────────────────────────────────────────
	var belly_pts = PackedVector2Array([
		Vector2(0, -10), Vector2(9, -4), Vector2(10, 4),
		Vector2(8, 12),  Vector2(0, 15), Vector2(-8, 12),
		Vector2(-10, 4), Vector2(-9, -4)
	])
	draw_colored_polygon(belly_pts, Color(1.0, 1.0, 1.0))

	# ── Left arm/flipper ────────────────────────────────────────
	draw_colored_polygon(PackedVector2Array([
		Vector2(-14, -6), Vector2(-24, 2), Vector2(-14, 8)
	]), Color(0.15, 0.15, 0.15))

	# ── Right arm/flipper ───────────────────────────────────────
	draw_colored_polygon(PackedVector2Array([
		Vector2(14, -6), Vector2(24, 2), Vector2(14, 8)
	]), Color(0.15, 0.15, 0.15))

	# ── Eye white ───────────────────────────────────────────────
	draw_circle(Vector2(-7, -10), 5.0, Color(1.0, 1.0, 1.0))

	# ── Pupil ───────────────────────────────────────────────────
	draw_circle(Vector2(-8, -10), 2.5, Color(0.05, 0.05, 0.05))

	# ── Beak ────────────────────────────────────────────────────
	draw_colored_polygon(PackedVector2Array([
		Vector2(-18, -5), Vector2(-26, -2), Vector2(-18, 2)
	]), Color(0.94, 0.63, 0.13))

	# ── Feet ────────────────────────────────────────────────────
	draw_colored_polygon(PackedVector2Array([
		Vector2(-6, 16), Vector2(-14, 22), Vector2(-2, 20)
	]), Color(0.94, 0.63, 0.13))
	draw_colored_polygon(PackedVector2Array([
		Vector2(6, 16), Vector2(14, 22), Vector2(2, 20)
	]), Color(0.94, 0.63, 0.13))
