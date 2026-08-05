extends Control

# ── upgrade metadata (mirrors GameData) ──────────────────────
const UPGRADES = [
	{
		"id":    "ramp",
		"name":  "Ramp Angle",
		"desc":  "Better launch angle — increases launch power.",
		"icon":  "⬆"
	},
	{
		"id":    "wings",
		"name":  "Glider Wings",
		"desc":  "Lose altitude slower. Penguin grows visible wings!",
		"icon":  "🪂"
	},
	{
		"id":    "rocket",
		"name":  "Rocket Booster",
		"desc":  "Press Boost mid-flight for a speed burst.",
		"icon":  "🚀"
	},
	{
		"id":    "suit",
		"name":  "Aerodynamic Suit",
		"desc":  "Reduce air drag — travel farther on each flight.",
		"icon":  "🌀"
	},
]

@onready var coin_label : Label     = $VBox/Header/CoinLabel
@onready var best_label : Label     = $VBox/Header/BestLabel
@onready var card_list  : VBoxContainer = $VBox/ScrollContainer/CardList
@onready var play_btn   : Button    = $VBox/PlayBtn

func _ready() -> void:
	play_btn.pressed.connect(_on_play)
	_build_cards()
	_refresh_header()

func _build_cards() -> void:
	for child in card_list.get_children():
		child.queue_free()

	for upg in UPGRADES:
		var card = _make_card(upg)
		card_list.add_child(card)

func _make_card(upg: Dictionary) -> PanelContainer:
	var panel = PanelContainer.new()
	panel.custom_minimum_size = Vector2(0, 100)

	var hbox = HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 16)
	panel.add_child(hbox)

	# Icon label
	var icon_lbl = Label.new()
	icon_lbl.text = upg["icon"]
	icon_lbl.add_theme_font_size_override("font_size", 36)
	icon_lbl.custom_minimum_size = Vector2(50, 0)
	hbox.add_child(icon_lbl)

	# Info column
	var vbox = VBoxContainer.new()
	vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hbox.add_child(vbox)

	var name_lbl = Label.new()
	name_lbl.text = upg["name"]
	name_lbl.add_theme_font_size_override("font_size", 18)
	vbox.add_child(name_lbl)

	var desc_lbl = Label.new()
	desc_lbl.text = upg["desc"]
	desc_lbl.add_theme_color_override("font_color", Color(0.65, 0.65, 0.65))
	desc_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vbox.add_child(desc_lbl)

	var level_lbl = Label.new()
	level_lbl.name = "LevelLabel"
	level_lbl.add_theme_color_override("font_color", Color(0.5, 0.8, 0.5))
	vbox.add_child(level_lbl)

	# Buy button
	var btn = Button.new()
	btn.name = "BuyBtn"
	btn.custom_minimum_size = Vector2(160, 0)
	hbox.add_child(btn)

	_refresh_card(panel, upg["id"])

	btn.pressed.connect(func():
		if GameData.buy_upgrade(upg["id"]):
			_refresh_all()
	)

	return panel

func _refresh_all() -> void:
	_refresh_header()
	for i in card_list.get_child_count():
		var panel = card_list.get_child(i)
		_refresh_card(panel, UPGRADES[i]["id"])

func _refresh_card(panel: Control, id: String) -> void:
	var lvl  = GameData.upgrades[id]
	var maxed = lvl >= GameData.UPGRADE_MAX[id]
	var cost = GameData.upgrade_cost(id)

	var level_lbl : Label  = panel.find_child("LevelLabel", true, false)
	var btn       : Button = panel.find_child("BuyBtn",     true, false)

	level_lbl.text = "Level %d / %d" % [lvl, GameData.UPGRADE_MAX[id]]

	if maxed:
		btn.text     = "Maxed!"
		btn.disabled = true
	else:
		btn.text     = "Buy  %d coins" % cost
		btn.disabled = not GameData.can_afford(id)

func _refresh_header() -> void:
	coin_label.text = "Coins: %d" % GameData.coins
	best_label.text = "Best: %d m" % int(GameData.best_distance)

func _on_play() -> void:
	get_tree().change_scene_to_file("res://scenes/Main.tscn")
