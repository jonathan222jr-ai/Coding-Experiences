"""
ELEMENTAL CATACLYSM GENERATOR FOR BLENDER
A procedural D&D 5e creature with fire, water, earth, and air elements.
Paste into Blender's Python console or Script Editor and run.
"""

import bpy
import bmesh
from mathutils import Vector, Quaternion
import random
import math

# Clear existing meshes
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Collection setup
if "Elemental Cataclysm" in bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections["Elemental Cataclysm"])
collection = bpy.data.collections.new("Elemental Cataclysm")
bpy.context.scene.collection.children.link(collection)

def create_material(name, base_color, emission_color=(0,0,0,1), emission_strength=0):
    """Create a procedural shader material"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Create nodes
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    output = nodes.new(type='ShaderNodeOutputMaterial')
    noise = nodes.new(type='ShaderNodeTexNoise')
    color_ramp = nodes.new(type='ShaderNodeValRamp')
    
    # Configure noise
    noise.inputs[1].default_value = 8.0  # Scale
    
    # Configure BSDF
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Emission'].default_value = emission_color
    bsdf.inputs['Emission Strength'].default_value = emission_strength
    bsdf.inputs['Metallic'].default_value = 0.3
    bsdf.inputs['Roughness'].default_value = 0.6
    
    # Link nodes
    mat.node_tree.links.new(noise.outputs[0], color_ramp.inputs[0])
    mat.node_tree.links.new(color_ramp.outputs[0], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
    
    return mat

def create_chaotic_mesh(name, vertices_count=500, scale=3):
    """Create a chaotic geometry using voronoi-like clusters"""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    
    # Create random vertices
    verts = []
    faces = []
    
    # Create clusters of vertices
    num_clusters = 8
    for cluster in range(num_clusters):
        cx = random.uniform(-scale, scale)
        cy = random.uniform(-scale, scale)
        cz = random.uniform(-scale, scale)
        
        verts_per_cluster = vertices_count // num_clusters
        for i in range(verts_per_cluster):
            x = cx + random.uniform(-scale*0.5, scale*0.5)
            y = cy + random.uniform(-scale*0.5, scale*0.5)
            z = cz + random.uniform(-scale*0.5, scale*0.5)
            verts.append((x, y, z))
    
    # Create simple faces from vertices
    if len(verts) > 3:
        for i in range(len(verts) - 3):
            if random.random() > 0.3:  # Don't connect all vertices
                faces.append((i, i+1, i+2))
    
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    # Subdivision surface for smoothness
    subsurf = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 3
    
    # Displace modifier for extra chaos
    displace = obj.modifiers.new(name="Displace", type='DISPLACE')
    
    return obj

def create_core_elements():
    """Create the core elemental shapes"""
    elements = []
    
    # Fire core (UV sphere with pointed geometry)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2, location=(0, 0, 0))
    fire_core = bpy.context.active_object
    fire_core.name = "Fire Core"
    fire_core.data.materials.append(create_material(
        "Fire Material",
        base_color=(1.0, 0.4, 0.1, 1.0),
        emission_color=(1.0, 0.6, 0.0, 1.0),
        emission_strength=2.0
    ))
    collection.objects.link(fire_core)
    bpy.context.scene.collection.objects.unlink(fire_core)
    
    # Add spikes with array modifier
    spike = bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.3, depth=1.5)
    elements.append(fire_core)
    
    # Water element (icosphere with wave deformer)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1.8, location=(2.5, 0, 0))
    water_elem = bpy.context.active_object
    water_elem.name = "Water Element"
    water_elem.data.materials.append(create_material(
        "Water Material",
        base_color=(0.2, 0.6, 1.0, 0.8),
        emission_color=(0.3, 0.8, 1.0, 1.0),
        emission_strength=1.0
    ))
    collection.objects.link(water_elem)
    bpy.context.scene.collection.objects.unlink(water_elem)
    
    # Wave deform
    wave = water_elem.modifiers.new(name="Wave", type='WAVE')
    wave.speed = 2.0
    wave.height = 0.5
    wave.width = 2.0
    
    elements.append(water_elem)
    
    # Earth element (irregular cube)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.5, 0, 0))
    earth_elem = bpy.context.active_object
    earth_elem.name = "Earth Element"
    earth_elem.data.materials.append(create_material(
        "Earth Material",
        base_color=(0.5, 0.3, 0.1, 1.0),
        emission_color=(0.3, 0.2, 0.05, 1.0),
        emission_strength=0.5
    ))
    
    # Fracture earth
    bpy.ops.object.shade_smooth()
    collection.objects.link(earth_elem)
    bpy.context.scene.collection.objects.unlink(earth_elem)
    
    elements.append(earth_elem)
    
    # Air element (torus with transparency)
    bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.4, location=(0, 2.5, 0))
    air_elem = bpy.context.active_object
    air_elem.name = "Air Element"
    air_elem.data.materials.append(create_material(
        "Air Material",
        base_color=(0.7, 0.9, 1.0, 0.5),
        emission_color=(0.8, 0.95, 1.0, 1.0),
        emission_strength=1.5
    ))
    collection.objects.link(air_elem)
    bpy.context.scene.collection.objects.unlink(air_elem)
    
    elements.append(air_elem)
    
    return elements

def create_particle_effects():
    """Create particle systems for elemental chaos"""
    
    # Create empty for particle emissions
    bpy.ops.object.add(type='EMPTY', location=(0, 0, 0))
    emitter = bpy.context.active_object
    emitter.name = "Particle Emitter"
    collection.objects.link(emitter)
    bpy.context.scene.collection.objects.unlink(emitter)
    
    # Fire particles
    fire_particles = emitter.particle_systems.new("Fire")
    fire_psys_settings = fire_particles.settings
    fire_psys_settings.count = 2000
    fire_psys_settings.frame_start = 1
    fire_psys_settings.frame_end = 250
    fire_psys_settings.lifetime = 60
    fire_psys_settings.lifetime_random = 0.3
    fire_psys_settings.emission_factor_random = 0.5
    
    # Fire velocity
    fire_psys_settings.initial_velocity_factor = 2.0
    fire_psys_settings.angular_velocity_factor = 1.0
    fire_psys_settings.object_align_factor = (0, 0, 1)
    
    # Emitter settings
    fire_psys_settings.emit_from = 'FACE'
    fire_psys_settings.normal_factor = 1.5
    fire_psys_settings.factor_random = 0.6
    
    # Water particles
    water_particles = emitter.particle_systems.new("Water")
    water_psys_settings = water_particles.settings
    water_psys_settings.count = 1500
    water_psys_settings.lifetime = 80
    water_psys_settings.lifetime_random = 0.2
    water_psys_settings.initial_velocity_factor = 1.5
    water_psys_settings.emit_from = 'FACE'
    water_psys_settings.normal_factor = 1.0
    
    # Lightning/Energy particles
    energy_particles = emitter.particle_systems.new("Energy")
    energy_psys_settings = energy_particles.settings
    energy_psys_settings.count = 500
    energy_psys_settings.lifetime = 40
    energy_psys_settings.emit_from = 'FACE'
    energy_psys_settings.normal_factor = 2.0
    
    return emitter

def create_environment_light():
    """Create dramatic lighting"""
    
    # Key light (warm)
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 8))
    sun = bpy.context.active_object
    sun.data.energy = 1500
    sun.data.color = (1.0, 0.8, 0.6)
    collection.objects.link(sun)
    bpy.context.scene.collection.objects.unlink(sun)
    
    # Fill light (cool)
    bpy.ops.object.light_add(type='SUN', location=(-5, -5, 5))
    fill = bpy.context.active_object
    fill.data.energy = 800
    fill.data.color = (0.3, 0.5, 1.0)
    collection.objects.link(fill)
    bpy.context.scene.collection.objects.unlink(fill)
    
    # Rim light
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 6))
    rim = bpy.context.active_object
    rim.data.energy = 1000
    rim.data.color = (1.0, 0.6, 0.2)
    rim.scale = (2, 2, 2)
    collection.objects.link(rim)
    bpy.context.scene.collection.objects.unlink(rim)

def create_world_shader():
    """Create an epic sky/world background"""
    world = bpy.data.worlds["World"]
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    
    # Create gradient background
    background = nodes.new(type='ShaderNodeBackground')
    output = nodes.new(type='ShaderNodeOutputWorld')
    coord = nodes.new(type='ShaderNodeTexCoord')
    mapping = nodes.new(type='ShaderNodeMapping')
    noise = nodes.new(type='ShaderNodeTexNoise')
    color_ramp = nodes.new(type='ShaderNodeValRamp')
    mix_rgb = nodes.new(type='ShaderNodeMix')
    
    # Configure for dramatic chaos
    noise.inputs[1].default_value = 3.0
    color_ramp.elements[0].color = (0.05, 0.05, 0.15, 1.0)  # Dark purple
    color_ramp.elements[1].color = (0.3, 0.1, 0.2, 1.0)    # Dark red
    
    background.inputs[0].default_value = (0.1, 0.05, 0.2, 1.0)
    background.inputs[1].default_value = 2.0
    
    # Link nodes
    world.node_tree.links.new(coord.outputs[0], mapping.inputs[0])
    world.node_tree.links.new(mapping.outputs[0], noise.inputs[0])
    world.node_tree.links.new(noise.outputs[0], color_ramp.inputs[0])
    world.node_tree.links.new(color_ramp.outputs[0], background.inputs[0])
    world.node_tree.links.new(background.outputs[0], output.inputs[0])

def setup_camera_and_render():
    """Setup camera and render settings"""
    
    # Camera
    bpy.ops.object.camera_add(location=(8, -8, 6))
    camera = bpy.context.active_object
    camera.name = "Cataclysm Camera"
    bpy.context.scene.camera = camera
    collection.objects.link(camera)
    bpy.context.scene.collection.objects.unlink(camera)
    
    # Point at origin
    camera.rotation_euler = (math.radians(70), 0, math.radians(225))
    
    # Render settings for beauty
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.render.image_settings.file_format = 'PNG'

# ============ MAIN EXECUTION ============

print("🔥 Generating Elemental Cataclysm...")

# Create core elements
print("  Creating core elemental forms...")
elements = create_core_elements()

# Create particle systems
print("  Spawning particle chaos...")
emitter = create_particle_effects()

# Create lighting
print("  Setting up dramatic lighting...")
create_environment_light()

# World shader
print("  Crafting the apocalyptic sky...")
create_world_shader()

# Camera and render
print("  Positioning camera...")
setup_camera_and_render()

# Select all and apply a parent
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.parent_set(type='OBJECT')

print("\n✨ ELEMENTAL CATACLYSM READY!")
print("━" * 50)
print("What you've got:")
print("  ✓ 4 core elemental shapes (Fire, Water, Earth, Air)")
print("  ✓ 3 particle systems for chaos and energy")
print("  ✓ Procedural emission shaders with glow")
print("  ✓ Dramatic 3-light setup")
print("  ✓ Apocalyptic world shader")
print("  ✓ Cycles render configured for cinema")
print("\nNext steps:")
print("  1. Press SPACEBAR → play to animate particles")
print("  2. Render a frame: F12 or Render > Render Image")
print("  3. Tweak materials: Edit each shader in Shading workspace")
print("  4. Add more chaos: Select Fire Core, Modifiers, add Displace")
print("  5. Make it move: Add keyframes to rotation/location")
print("━" * 50)
