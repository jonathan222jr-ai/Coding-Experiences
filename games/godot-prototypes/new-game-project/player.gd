extends CharacterBody2D

@export var speed := 200.0
@export var jump_force := -400.0
@export var gravity := 900.0
@export var max_fall_speed := 800.0

@export var accel := 1200.0
@export var friction := 1000.0

var direction := 0

func _physics_process(delta):
	handle_input(delta)
	apply_gravity(delta)
	move_and_slide()

func handle_input(delta):
	direction = Input.get_axis("move_left", "move_right")
	
	if direction != 0:
		velocity.x = move_toward(velocity.x, direction * speed, accel * delta)
	else:
		velocity.x = move_toward(velocity.x, 0, friction * delta)

	# Jump
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_force

func apply_gravity(delta):
	if not is_on_floor():
		velocity.y += gravity * delta
		velocity.y = min(velocity.y, max_fall_speed)
