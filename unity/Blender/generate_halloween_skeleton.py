"""Generate a detailed, fully rigged 1.8 m skeleton from procedural geometry.

Run from the repository root:
    blender --background --python .\\unity\\Blender\\generate_halloween_skeleton.py -- --out .\\unity\\Assets\\Models

The model uses separate named, rigidly weighted bones and no external assets.
"""
import bpy
import math
import os
import sys
import argparse
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument("--out", default=os.path.abspath("./generated"))
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(args.out, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures, bpy.data.materials):
    for block in list(datablocks):
        if block.users == 0:
            datablocks.remove(block)


def bone_material():
    material = bpy.data.materials.new("Weathered_Antique_Bone")
    material.diffuse_color = (.72, .64, .48, 1)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = .82

    color_noise = nodes.new("ShaderNodeTexNoise")
    color_noise.inputs["Scale"].default_value = 22
    color_noise.inputs["Detail"].default_value = 4
    color_noise.inputs["Roughness"].default_value = .78
    colors = nodes.new("ShaderNodeValToRGB")
    colors.color_ramp.elements[0].position = .19
    colors.color_ramp.elements[0].color = (.19, .115, .052, 1)
    colors.color_ramp.elements[1].position = .81
    colors.color_ramp.elements[1].color = (.89, .82, .67, 1)
    colors.color_ramp.elements.new(.49).color = (.57, .43, .26, 1)
    links.new(color_noise.outputs["Fac"], colors.inputs["Fac"])
    links.new(colors.outputs["Color"], shader.inputs["Base Color"])

    fine_noise = nodes.new("ShaderNodeTexNoise")
    fine_noise.inputs["Scale"].default_value = 80
    fine_noise.inputs["Detail"].default_value = 3
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .13
    bump.inputs["Distance"].default_value = .012
    links.new(fine_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


bone_mat = bone_material()
cancellous_mat = bpy.data.materials.new("Dark_Cancellous_Bone")
cancellous_mat.diffuse_color = (.20, .13, .075, 1)
cancellous_mat.use_nodes = True
cancellous_shader = cancellous_mat.node_tree.nodes.get("Principled BSDF")
cancellous_shader.inputs["Base Color"].default_value = (.20, .13, .075, 1)
cancellous_shader.inputs["Roughness"].default_value = .95
socket_mat = bpy.data.materials.new("Deep_Eye_Sockets")
socket_mat.diffuse_color = (.009, .006, .004, 1)
socket_mat.use_nodes = True
socket_shader = socket_mat.node_tree.nodes.get("Principled BSDF")
socket_shader.inputs["Base Color"].default_value = (.009, .006, .004, 1)
socket_shader.inputs["Roughness"].default_value = 1
parts = []
rig_bones = {}
HEIGHT = 1.8


def add_bone(name, head, tail, parent=None):
    rig_bones[name] = (Vector(head), Vector(tail), parent)


add_bone("Hips", (0, 0, .91), (0, 0, 1.08))
add_bone("Spine", (0, 0, 1.08), (0, 0, 1.28), "Hips")
add_bone("Chest", (0, 0, 1.28), (0, 0, 1.49), "Spine")
add_bone("Neck", (0, .015, 1.49), (0, .015, 1.61), "Chest")
add_bone("Head", (0, 0, 1.60), (0, 0, 1.78), "Neck")
add_bone("Jaw", (0, -.07, 1.61), (0, -.10, 1.55), "Head")

for side, sign in (("Left", 1), ("Right", -1)):
    add_bone(side + "Shoulder", (.10 * sign, 0, 1.48), (.29 * sign, 0, 1.45), "Chest")
    add_bone(side + "UpperArm", (.29 * sign, 0, 1.45), (.43 * sign, 0, 1.18), side + "Shoulder")
    add_bone(side + "LowerArm", (.43 * sign, 0, 1.18), (.59 * sign, 0, .92), side + "UpperArm")
    add_bone(side + "Hand", (.59 * sign, 0, .92), (.61 * sign, 0, .83), side + "LowerArm")
    for digit, spread, length in (
        ("Thumb", .070, .11), ("Index", .042, .145), ("Middle", .014, .17),
        ("Ring", -.014, .155), ("Pinky", -.042, .125),
    ):
        start = (.605 * sign, spread, .845)
        end = ((.605 + length * .35) * sign, spread * 1.35, .845 - length)
        add_bone(side + digit, start, end, side + "Hand")
    add_bone(side + "UpperLeg", (.135 * sign, 0, .95), (.155 * sign, 0, .54), "Hips")
    add_bone(side + "LowerLeg", (.155 * sign, 0, .54), (.155 * sign, 0, .14), side + "UpperLeg")
    add_bone(side + "Foot", (.155 * sign, 0, .14), (.155 * sign, -.15, .065), side + "LowerLeg")
    add_bone(side + "Toes", (.155 * sign, -.15, .065), (.155 * sign, -.25, .055), side + "Foot")

arm_data = bpy.data.armatures.new("ReferenceSkeleton_Armature")
arm = bpy.data.objects.new("HalloweenSkeleton_Rig", arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
for name, (head, tail, _) in rig_bones.items():
    edit_bone = arm_data.edit_bones.new(name)
    edit_bone.head = head
    edit_bone.tail = tail
    edit_bone.use_deform = True
for name, (_, _, parent) in rig_bones.items():
    if parent:
        arm_data.edit_bones[name].parent = arm_data.edit_bones[parent]
bpy.ops.object.mode_set(mode="OBJECT")
arm.select_set(False)


def finish_part(obj, name, bone_name, material=bone_mat, smooth=True):
    obj.name = name
    obj.data.materials.append(material)
    if smooth and obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    group = obj.vertex_groups.new(name=bone_name)
    group.add(list(range(len(obj.data.vertices))), 1, "REPLACE")
    parts.append(obj)
    return obj


def ellipsoid(name, center, radii, bone_name, material=bone_mat, rotation=None):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=16, location=center,
    )
    obj = bpy.context.object
    obj.scale = radii
    if rotation is not None:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return finish_part(obj, name, bone_name, material)


def tube(name, points, radii, bone_name, material=bone_mat, resolution=8, bevel_depth=.012):
    """Smooth tapered bone, with enlarged joint ends and a narrow shaft."""
    data = bpy.data.curves.new(name + "_Curve", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = resolution
    data.bevel_depth = bevel_depth
    data.bevel_resolution = 4
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, position, radius in zip(spline.bezier_points, points, radii):
        point.co = position
        point.radius = radius
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.select_set(False)
    return finish_part(obj, name, bone_name, material)


def shaped_bone(name, start, end, radius, bone_name, material=bone_mat, bulge=1.5):
    a, b = Vector(start), Vector(end)
    direction = b - a
    if direction.length < 1e-5:
        return
    return tube(
        name,
        [a, a + direction * .16, a + direction * .48, a + direction * .84, b],
        [radius * .82, radius * bulge, radius, radius * bulge * .88, radius * .62],
        bone_name, material, bevel_depth=1,
    )


def ring_points(center, radius_x, radius_z, count=32, y_offset=0):
    cx, cy, cz = center
    return [
        (cx + radius_x * math.cos(2 * math.pi * i / count),
         cy + y_offset,
         cz + radius_z * math.sin(2 * math.pi * i / count))
        for i in range(count + 1)
    ]


def plate(name, outline, y_front, y_back, bone_name):
    """Closed, softly bevelled thin bone plate in the X/Z plane."""
    count = len(outline)
    vertices = [(x, y_front, z) for x, z in outline]
    vertices += [(x, y_back, z) for x, z in outline]
    faces = [tuple(range(count)), tuple(range(count, 2 * count))[::-1]]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
    mesh_data = bpy.data.meshes.new(name + "_Geometry")
    mesh_data.from_pydata(vertices, [], faces)
    mesh_data.update()
    obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.collection.objects.link(obj)
    bevel = obj.modifiers.new("SoftBoneEdges", "BEVEL")
    bevel.width = .012
    bevel.segments = 3
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.select_set(False)
    return finish_part(obj, name, bone_name, smooth=False)


# Skull, jaw, and facial bones.
ellipsoid("Cranial_Vault", (0, .005, 1.690), (.116, .106, .126), "Head")
ellipsoid("Occipital_Base", (0, .055, 1.637), (.083, .064, .074), "Head")
ellipsoid("Forehead_Bone", (0, -.071, 1.704), (.090, .052, .067), "Head")
for sign, label in ((-1, "Right"), (1, "Left")):
    orbit_center = (sign * .047, -.102, 1.688)
    ellipsoid(label + "_Eye_Socket", orbit_center, (.035, .012, .041), "Head", socket_mat)
    rim = ring_points((sign * .047, -.108, 1.688), .040, .047, 32)
    tube(label + "_Orbital_Rim", rim, [.22] * len(rim), "Head")
    shaped_bone(label + "_Zygomatic_Arch",
                (sign * .023, -.101, 1.657), (sign * .099, -.061, 1.644),
                .009, "Head")
    shaped_bone(label + "_Maxilla", (sign * .017, -.087, 1.638),
                (sign * .073, -.076, 1.620), .012, "Head")
    shaped_bone(label + "_Mandibular_Ramus",
                (sign * .070, -.070, 1.625), (sign * .064, -.071, 1.570),
                .015, "Jaw")
    shaped_bone(label + "_Coronal_Suture",
                (sign * .11, -.028, 1.742), (sign * .095, -.052, 1.775),
                .0025, "Head", cancellous_mat)

# Narrow pear-shaped nasal opening and bridge, positioned on the front plane of the face.
ellipsoid("Nasal_Aperture", (0, -.118, 1.657), (.014, .009, .024), "Head", socket_mat)
shaped_bone("Nasal_Bridge", (0, -.099, 1.724), (0, -.119, 1.665), .012, "Head")
shaped_bone("Sagittal_Suture", (0, -.078, 1.772), (0, -.108, 1.731),
            .0025, "Head", cancellous_mat)
tube("Lower_Jaw_Horseshoe",
     [(-.064, -.071, 1.570), (-.043, -.105, 1.557), (0, -.112, 1.553),
      (.043, -.105, 1.557), (.064, -.071, 1.570)],
     [.9, .95, 1, .95, .9], "Jaw")
for i in range(8):
    x = (i - 3.5) * .014
    tooth_height = .018 if i not in (0, 7) else .014
    ellipsoid("Upper_Tooth_%02d" % i, (x, -.116, 1.604), (.0065, .009, tooth_height),
              "Head", bone_mat)
    ellipsoid("Lower_Tooth_%02d" % i, (x, -.115, 1.578), (.006, .008, .013),
              "Jaw", bone_mat)

# Individual cervical, thoracic, and lumbar vertebrae with transverse and spinous processes.
for index in range(24):
    z = 1.045 + index * .019
    bone_name = "Spine" if z < 1.29 else "Chest"
    scale = .68 if z > 1.47 else 1.0
    width = (.024 + max(0, .045 - z) * .04) * scale
    ellipsoid("Vertebral_Body_%02d" % index, (0, .018, z),
              (width, .032 * scale, .014 * scale), bone_name)
    for sign, side in ((-1, "R"), (1, "L")):
        shaped_bone("Vertebral_Pedicle_%02d_%s" % (index, side),
                    (0, .025, z), (sign * width * 1.4, .045, z),
                    .007 * scale, bone_name)
        shaped_bone("Vertebral_Transverse_%02d_%s" % (index, side),
                    (sign * width, .044, z), (sign * width * 2.8, .055, z + .004),
                    .006 * scale, bone_name)
    shaped_bone("Vertebral_Spinous_%02d" % index,
                (0, .04, z), (0, .094, z - .007), .008 * scale, bone_name)

for index in range(6):
    z = 1.488 + index * .018
    ellipsoid("Cervical_Body_%02d" % (index + 1), (0, .015, z),
              (.019, .025, .011), "Neck")
    for sign, side in ((-1, "R"), (1, "L")):
        shaped_bone("Cervical_Transverse_%02d_%s" % (index + 1, side),
                    (0, .024, z), (sign * .031, .036, z + .003),
                    .0055, "Neck")
    shaped_bone("Cervical_Spinous_%02d" % (index + 1),
                (0, .031, z), (0, .075, z - .003), .006, "Neck")

# Clavicles, scapulae, and the twelve arched pairs of ribs.
for sign, side in ((-1, "Right"), (1, "Left")):
    tube(side + "_Clavicle",
         [(0, -.055, 1.465), (sign * .065, -.061, 1.487),
          (sign * .155, -.050, 1.489), (sign * .265, -.013, 1.455)],
         [.72, 1.5, 1.3, .8], side + "Shoulder")
    plate(side + "_Scapula",
          [(sign * .105, 1.435), (sign * .202, 1.461), (sign * .275, 1.419),
           (sign * .265, 1.330), (sign * .208, 1.274), (sign * .149, 1.326)],
          .071, .105, "Chest")
    tube(side + "_Scapular_Spine",
         [(sign * .117, .067, 1.426), (sign * .195, .064, 1.435),
          (sign * .267, .063, 1.418)], [.8, 1.15, .55], "Chest")

for row in range(12):
    z = 1.432 - row * .024
    lower = max(0, row - 7)
    width = .188 + .022 * math.sin(min(row, 7) / 7 * math.pi) - lower * .011
    height = .57 if row >= 10 else 1
    bone_name = "Chest" if row < 8 else "Spine"
    for sign, side in ((-1, "R"), (1, "L")):
        tube("Rib_%02d_%s" % (row + 1, side),
             [(sign * .027, .045, z),
              (sign * width * .48, .105, z + .012),
              (sign * width, .074, z + .002),
              (sign * width * 1.02, -.002, z - .012),
              (sign * width * .79, -.084, z - .019),
              (sign * .039, -.101, z - .015)],
             [.6 * height, 1.05 * height, .93 * height, .78 * height,
              .53 * height, .16 * height], bone_name)
    if row < 10:
        shaped_bone("Costal_Cartilage_%02d" % row,
                    (0, -.102, z - .015), (0, -.107, z - .018),
                    .006, "Chest", cancellous_mat)
tube("Sternum_Manubrium", [(0, -.112, 1.475), (0, -.125, 1.438), (0, -.120, 1.405)],
     [.9, 1.35, .9], "Chest")
tube("Sternum_Body", [(0, -.120, 1.410), (0, -.121, 1.335), (0, -.115, 1.254)],
     [1, 1.1, .6], "Chest")
shaped_bone("Xiphoid_Process", (0, -.112, 1.256), (0, -.097, 1.216), .009, "Chest")

# Pelvic ring: thin, shaped iliac blades rather than oversized spherical hip joints.
plate("Sacrum_Plate",
      [(-.045, 1.045), (-.054, 1.002), (-.035, .949), (0, .921),
       (.035, .949), (.054, 1.002), (.045, 1.045), (0, 1.035)],
      .017, .068, "Hips")
for level in range(5):
    z = 1.025 - level * .019
    shaped_bone("Sacral_Ridge_%02d" % level,
                (-.024, .012, z), (.024, .012, z), .005, "Hips", cancellous_mat)
for sign, side in ((-1, "Right"), (1, "Left")):
    plate(side + "_Ilium",
          [(sign * .045, 1.029), (sign * .070, 1.092), (sign * .130, 1.115),
           (sign * .211, 1.087), (sign * .237, 1.039), (sign * .213, .982),
           (sign * .184, .970), (sign * .168, .990), (sign * .145, 1.000),
           (sign * .117, .985), (sign * .075, .984)],
          -.043, .033, "Hips")
    tube(side + "_Iliac_Crest",
         [(sign * .066, -.048, 1.083), (sign * .125, -.054, 1.121),
          (sign * .197, -.046, 1.099), (sign * .229, -.034, 1.045)],
         [.5, .75, .68, .35], "Hips")
    ellipsoid(side + "_Acetabulum",
              (sign * .153, -.037, .930), (.043, .020, .046), "Hips", cancellous_mat)
    tube(side + "_Obturator_Ring",
         [(sign * .159, -.045, .970), (sign * .217, -.041, .946),
          (sign * .201, -.047, .901), (sign * .144, -.050, .903),
          (sign * .116, -.045, .924)], [.72, .74, .66, .72, .58], "Hips")
    tube(side + "_Pubic_Ramus",
         [(sign * .155, -.055, .924), (sign * .113, -.070, .895),
          (sign * .055, -.078, .908), (0, -.081, .920)],
         [.75, .8, .68, .52], "Hips")

# Arm bones. The posed arms hang out and down like the front view in the reference.
for side, sign in (("Left", 1), ("Right", -1)):
    ellipsoid(side + "_Humeral_Head", (sign * .298, 0, 1.443),
              (.047, .044, .047), side + "UpperArm")
    shaped_bone(side + "_Humerus", (sign * .315, .002, 1.433),
                (sign * .428, -.004, 1.191), .023, side + "UpperArm", bulge=1.55)
    tube(side + "_Deltoid_Ridge",
         [(sign * .335, -.020, 1.405), (sign * .365, -.025, 1.35),
          (sign * .390, -.020, 1.296)], [.6, .85, .3], side + "UpperArm", cancellous_mat)
    ellipsoid(side + "_Elbow", (sign * .433, 0, 1.177),
              (.034, .032, .036), side + "LowerArm")
    shaped_bone(side + "_Radius", (sign * .448, -.020, 1.169),
                (sign * .582, -.024, .938), .012, side + "LowerArm", bulge=1.5)
    shaped_bone(side + "_Ulna", (sign * .421, .023, 1.174),
                (sign * .563, .023, .941), .011, side + "LowerArm", bulge=1.55)
    ellipsoid(side + "_Olecranon", (sign * .421, .027, 1.174),
              (.021, .021, .028), side + "LowerArm")
    for carpal in range(4):
        ellipsoid(side + "_Carpal_%02d" % carpal,
                  (sign * (.584 + (carpal % 2) * .016), -.009,
                   .923 - (carpal // 2) * .014),
                  (.014, .013, .013), side + "Hand")
    ellipsoid(side + "_Metacarpus", (sign * .612, -.006, .864),
              (.035, .022, .064), side + "Hand")
    for digit_index, (digit, spread, length) in enumerate((
        ("Thumb", .070, .110), ("Index", .042, .145), ("Middle", .014, .170),
        ("Ring", -.014, .155), ("Pinky", -.042, .125),
    )):
        base = sign * (.612 + spread * .72)
        mid = sign * (.612 + spread + length * .045)
        tip = sign * (.612 + spread + length * .10)
        z0 = .867
        tube(side + digit + "_Phalanges",
             [(base, -.012, z0), (mid, -.018, z0 - length * .48),
              (tip, -.020, z0 - length)],
             [.58, .36, .12], side + digit)
        if digit != "Thumb":
            ellipsoid(side + digit + "_Knuckle",
                      (base, -.012, z0), (.010, .010, .011), side + digit)

# Femora, kneecaps, tibiae, fibulae, and the small bones of each foot.
for side, sign in (("Left", 1), ("Right", -1)):
    ellipsoid(side + "_Femoral_Head", (sign * .137, 0, .928),
              (.049, .044, .049), side + "UpperLeg")
    shaped_bone(side + "_Femur", (sign * .146, .004, .908),
                (sign * .157, -.002, .552), .024, side + "UpperLeg", bulge=1.55)
    shaped_bone(side + "_Greater_Trochanter",
                (sign * .143, .008, .929), (sign * .184, .018, .866),
                .024, side + "UpperLeg", bulge=1.25)
    for condyle, offset in (("Medial", -.020), ("Lateral", .020)):
        ellipsoid(side + "_" + condyle + "_Femoral_Condyle",
                  (sign * (.157 + offset), -.002, .544),
                  (.022, .030, .027), side + "UpperLeg")
    ellipsoid(side + "_Patella", (sign * .157, -.035, .541),
              (.034, .020, .033), side + "LowerLeg")
    shaped_bone(side + "_Tibia", (sign * .157, -.006, .519),
                (sign * .155, -.002, .163), .019, side + "LowerLeg", bulge=1.5)
    shaped_bone(side + "_Fibula", (sign * .186, .018, .509),
                (sign * .181, .023, .170), .009, side + "LowerLeg", bulge=1.4)
    ellipsoid(side + "_Lateral_Malleolus",
              (sign * .184, .018, .146), (.020, .023, .030), side + "Foot")
    ellipsoid(side + "_Medial_Malleolus",
              (sign * .146, -.006, .147), (.018, .021, .028), side + "Foot")
    ellipsoid(side + "_Calcaneus", (sign * .155, .037, .090),
              (.044, .052, .038), side + "Foot")
    ellipsoid(side + "_Talus", (sign * .155, -.012, .105),
              (.034, .043, .030), side + "Foot")
    for ray in range(5):
        x = sign * (.105 + ray * .025)
        toe_length = (.205, .245, .235, .207, .173)[ray]
        start = (sign * (.145 + ray * .005), -.026, .085)
        ball = (x, -.115 - toe_length * .20, .065)
        tip = (x + sign * (ray - 2) * .008, -.115 - toe_length, .048)
        tube(side + "_Metatarsal_%02d" % ray,
             [start, (x, -.068, .075), ball], [.75, .64, .35], side + "Foot")
        tube(side + "_Toe_Phalanges_%02d" % ray,
             [ball, (x, ball[1] - toe_length * .38, .057), tip],
             [.48, .30, .12], side + "Toes")

# Assemble one skinned mesh while retaining bone-specific groups and material regions.
bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
mesh = bpy.context.object
mesh.name = "HalloweenSkeleton_AnatomicalMesh"
mesh.data.name = "HalloweenSkeleton_Geometry"
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
minimum_z = min(vertex.co.z for vertex in mesh.data.vertices)
maximum_z = max(vertex.co.z for vertex in mesh.data.vertices)
height_scale = HEIGHT / (maximum_z - minimum_z)
for vertex in mesh.data.vertices:
    vertex.co.z = (vertex.co.z - minimum_z) * height_scale

bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for edit_bone in arm_data.edit_bones:
    edit_bone.head.z = (edit_bone.head.z - minimum_z) * height_scale
    edit_bone.tail.z = (edit_bone.tail.z - minimum_z) * height_scale
bpy.ops.object.mode_set(mode="OBJECT")
arm.select_set(False)
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
mesh.parent = arm
skin = mesh.modifiers.new("Armature_Skin", "ARMATURE")
skin.object = arm

bone_names = set(arm.data.bones.keys())
mesh_group_names = {group.name for group in mesh.vertex_groups}
if mesh.parent != arm or not any(mod.type == "ARMATURE" and mod.object == arm for mod in mesh.modifiers):
    raise RuntimeError("The generated mesh is not attached to its armature.")
if not mesh_group_names or not mesh_group_names.issubset(bone_names):
    raise RuntimeError("Some mesh vertex groups do not match named armature bones.")
unweighted = [
    vertex.index for vertex in mesh.data.vertices
    if len(vertex.groups) != 1 or abs(vertex.groups[0].weight - 1.0) > 1e-5
]
if unweighted:
    raise RuntimeError(f"{len(unweighted)} vertices do not have one rigid 1.0 bone weight.")
z_bounds = [vertex.co.z for vertex in mesh.data.vertices]
actual_height = max(z_bounds) - min(z_bounds)
if abs(actual_height - HEIGHT) > .005 or min(z_bounds) < -.005:
    raise RuntimeError(f"Expected a {HEIGHT:.2f} m model, got {actual_height:.3f} m.")

def evaluated_positions():
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    evaluated_mesh = evaluated.to_mesh()
    positions = [vertex.co.copy() for vertex in evaluated_mesh.vertices]
    evaluated.to_mesh_clear()
    return positions

before = evaluated_positions()
arm.pose.bones["LeftUpperArm"].rotation_mode = "XYZ"
arm.pose.bones["LeftUpperArm"].rotation_euler[2] = math.radians(18)
bpy.context.view_layer.update()
after = evaluated_positions()
arm.pose.bones["LeftUpperArm"].rotation_euler[2] = 0
bpy.context.view_layer.update()
if len(before) != len(after) or max((a - b).length for a, b in zip(before, after)) < 1e-5:
    raise RuntimeError("The armature pose smoke test did not deform the mesh.")

print(f"Rig validated: {len(arm.data.bones)} bones, {len(mesh.data.vertices)} weighted vertices, "
      f"{actual_height:.3f} m tall; arm posing deforms the mesh.")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.out, "HalloweenSkeleton.blend"))
fbx_path = os.path.join(args.out, "HalloweenSkeleton.fbx")
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
mesh.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(
    filepath=fbx_path, use_selection=True, add_leaf_bones=False, apply_unit_scale=True,
    axis_forward="-Z", axis_up="Y", bake_anim=False, mesh_smooth_type="FACE",
)
print("FBX exported:", fbx_path)
try:
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(args.out, "HalloweenSkeleton.glb"),
        export_format="GLB", use_selection=True, export_skins=True, export_animations=False,
    )
except Exception as error:
    print("GLB export failed:", error)
print(f"Finished: {len(rig_bones)} bones, {len(parts)} anatomical parts.")
