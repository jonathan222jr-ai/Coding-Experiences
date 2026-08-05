extends Node2D

# ── References ──────────────────────────────────────────────
@onready var penguin        : Node2D          = $Penguin
@onready var launch_bar     : Control         = $HUD/LaunchBar
@onready var power_fill     : ColorRect       = $HUD/LaunchBar/PowerFill
@onready var angle_label    : Label           = $HUD/LaunchBar/AngleLabel
@onready var dist_label     : Label           = $HUD/StatsBar/DistLabel
@onready var best_label     : Label           = $HUD/StatsBar/BestLabel
@onready var coin_label     : Label           = $HUD/StatsBar/CoinLabel
@onready var launch_btn     : Button          = $HUD/LaunchBtn
@onready var boost_btn      : Button          = $HUD/BoostBtn
@onready var shop_btn       : Button          = $HUD/ShopBtn
@onready var result_panel   : Control         = $HUD/ResultPanel
@onready var result_dist    : Label           = $HUD/ResultPanel/VBox/DistLabel
@onready var result_coins   : Label           = $HUD/ResultPanel/VBox/CoinsLabel
@onready var camera         : Camera2D        = $Camera2D
@onready var trail          : Line2D          = $Trail

enum Phase { IDLE, POWER, FLYING, DONE }
var phase: Phase = Phase.IDLE

var velocity:    Vector2 = Vector2.ZERO
var distance:    float   = 0.0
var boost_used:  bool    = false

var power_angle: float = 45.0
var power_dir:   float = 1.0
const POWER_SPEED: float = 60.0

const LAUNCH_X: float = 160.0
const LAUNCH_Y: float = 560.0
const GROUND_Y: float = 582.0
const CAM_LEAD: float = 320.0

var cam_start: Vector2

func _ready() -> void:
	cam_start = camera.global_position
	_reset_penguin()
	_update_hud()
	launch_btn.pressed.connect(_on_launch_btn)
	boost_btn.pressed.connect(_on_boost_btn)
	shop_btn.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/Shop.tscn"))
	boost_btn.visible = false
	result_panel.visible = false
	launch_bar.visible = false

func _reset_penguin() -> void:
	penguin.global_position = Vector2(LAUNCH_X, LAUNCH_Y)
	penguin.rotation = 0.0
	velocity = Vector2.ZERO
	distance = 0.0
	boost_used = false
	trail.clear_points()
	camera.global_position = cam_start
	penguin.queue_redraw()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("ui_select"):
		_handle_action()
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_B:
			if phase == Phase.FLYING and not boost_used:
				_boost()

func _handle_action() -> void:
	match phase:
		Phase.IDLE:  _begin_power()
		Phase.POWER: _fire()

func _begin_power() -> void:
	phase = Phase.POWER
	power_angle = 45.0
	power_dir = 1.0
	launch_bar.visible = true
	launch_btn.text = "Fire!  [Space]"
	result_panel.visible = false

func _fire() -> void:
	phase = Phase.FLYING
	launch_bar.visible = false
	var angle_range = GameData.get_launch_angle_range()
	var clamped = clamp(power_angle, angle_range.x, angle_range.y)
	var rad = deg_to_rad(clamped)
	var spd = GameData.get_launch_power()
	velocity = Vector2(cos(rad) * spd, -sin(rad) * spd)
	_reset_penguin()
	penguin.global_position = Vector2(LAUNCH_X, LAUNCH_Y)
	launch_btn.text = "Flying..."
	launch_btn.disabled = true
	var has_boost = GameData.get_boost_power() > 0
	boost_btn.visible = has_boost
	boost_btn.disabled = false
	boost_btn.text = "Boost!  [B]"

func _boost() -> void:
	boost_used = true
	velocity.x += GameData.get_boost_power()
	boost_btn.disabled = true
	boost_btn.text = "Boosted!"

func _land() -> void:
	phase = Phase.DONE
	penguin.global_position.y = LAUNCH_Y
	penguin.rotation = 0.0
	velocity = Vector2.ZERO
	boost_btn.visible = false
	var earned = int(distance / 10.0)
	GameData.coins += earned
	if distance > GameData.best_distance:
		GameData.best_distance = distance
	GameData.total_flights += 1
	result_dist.text  = "%d m" % int(distance)
	result_coins.text = "+ %d coins" % earned
	result_panel.visible = true
	launch_btn.text = "Launch again!  [Space]"
	launch_btn.disabled = false
	_update_hud()

func _physics_process(delta: float) -> void:
	match phase:
		Phase.POWER:   _tick_power(delta)
		Phase.FLYING:  _tick_flight(delta)

func _tick_power(delta: float) -> void:
	var angle_range = GameData.get_launch_angle_range()
	power_angle += power_dir * POWER_SPEED * delta
	if power_angle >= angle_range.y:
		power_angle = angle_range.y; power_dir = -1.0
	elif power_angle <= angle_range.x:
		power_angle = angle_range.x; power_dir = 1.0
	var t = (power_angle - angle_range.x) / (angle_range.y - angle_range.x)
	power_fill.size.x = t * 260.0
	angle_label.text = "%d°" % int(power_angle)

func _tick_flight(delta: float) -> void:
	var grav = 900.0 * GameData.get_gravity_scale()
	velocity.y += grav * delta
	if velocity.y > 0:
		velocity.y *= pow(GameData.get_glide_factor(), delta * 60.0)
	var drag = GameData.get_drag()
	velocity.x -= velocity.x * drag * 60.0 * delta
	velocity.y -= velocity.y * drag * 30.0 * delta
	penguin.global_position += velocity * delta
	if velocity.length() > 20:
		penguin.rotation = velocity.angle()
	trail.add_point(penguin.global_position)
	if trail.get_point_count() > 150:
		trail.remove_point(0)
	distance = max(distance, (penguin.global_position.x - LAUNCH_X) / 4.0)
	dist_label.text = "Distance: %d m" % int(distance)
	var target_x = penguin.global_position.x + CAM_LEAD
	var target_y = clamp(penguin.global_position.y, 100.0, 500.0)
	camera.global_position.x = lerp(camera.global_position.x, target_x, 6.0 * delta)
	camera.global_position.y = lerp(camera.global_position.y, target_y, 3.0 * delta)
	if penguin.global_position.y >= GROUND_Y:
		_land()

func _update_hud() -> void:
	best_label.text = "Best: %d m" % int(GameData.best_distance)
	coin_label.text = "Coins: %d" % GameData.coins

func _on_launch_btn() -> void:
	_handle_action()

func _on_boost_btn() -> void:
	if phase == Phase.FLYING and not boost_used:
		_boost()
