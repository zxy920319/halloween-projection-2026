"""Generate a stylized-realistic Halloween skeleton with a real Blender armature.
Run: blender --background --python generate_halloween_skeleton.py -- --out /absolute/path/output
Outputs .blend, .fbx and .glb if the installed Blender exporters support them.
All mesh vertices are weighted (rigid 1.0) to named bones using Armature modifier.
Blender 3.6 / 4.x target. No external assets or add-ons.
"""
import bpy, math, os, sys, argparse
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--out', default=os.path.abspath('./generated'))
a = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
os.makedirs(a.out, exist_ok=True)

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for datablocks in [bpy.data.meshes, bpy.data.armatures, bpy.data.materials]:
    for block in list(datablocks):
        if block.users == 0: datablocks.remove(block)

def mat(name, rgb, metallic=0, roughness=.8, emission=None, power=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    principled=m.node_tree.nodes.get('Principled BSDF')
    principled.inputs['Base Color'].default_value=(*rgb,1)
    principled.inputs['Metallic'].default_value=metallic
    principled.inputs['Roughness'].default_value=roughness
    if emission:
        try:
            principled.inputs['Emission Color'].default_value=(*emission,1)
            principled.inputs['Emission Strength'].default_value=power
        except KeyError:
            principled.inputs['Emission'].default_value=(*emission,1)
    return m

bone_mat=mat('Ancient_Ivory', (.67,.62,.52),0,.88)
accent_mat=mat('Shadowed_Bone',(.27,.24,.22),0,1)
socket_mat=mat('Deep_Eye_Sockets',(.009,.006,.006),0,1)
parts=[]
HEIGHT_SCALE=.961
HEIGHT_OFFSET=-.05

def model_point(point):
    return (point[0],point[1],point[2]*HEIGHT_SCALE+HEIGHT_OFFSET)

def weight_part(obj, bone, material):
    obj.data.materials.append(material)
    vg=obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    parts.append(obj)
    return obj

def ellipsoid(name, position, radii, bone, material=bone_mat, segments=16, rings=10):
    position=model_point(position)
    radii=(radii[0],radii[1],radii[2]*HEIGHT_SCALE)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=position)
    o=bpy.context.object; o.name=name
    o.scale=radii
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return weight_part(o,bone,material)

def rod(name, start, end, radius, bone, material=bone_mat, vertices=10):
    v1,v2=Vector(model_point(start)),Vector(model_point(end))
    delta=v2-v1
    if delta.length<1e-5: return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length, location=(v1+v2)*.5)
    o=bpy.context.object; o.name=name
    o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return weight_part(o,bone,material)

def chained(name, pts, radius, bone, material=bone_mat):
    for i in range(len(pts)-1): rod(f'{name}_{i:02}',pts[i],pts[i+1],radius,bone,material)

# Bones deliberately use clear Unity-friendly names; body in Blender Z-up, forward -Y.
B={}
def bone(name, head, tail, parent=None, deform=True):
    B[name]=(model_point(head),model_point(tail),parent,deform)

bone('Hips',(0,0,.94),(0,0,1.08))
bone('Spine',(0,0,1.08),(0,0,1.27),'Hips')
bone('Chest',(0,0,1.27),(0,0,1.49),'Spine')
bone('Neck',(0,0,1.49),(0,0,1.61),'Chest')
bone('Head',(0,0,1.61),(0,0,1.85),'Neck')
bone('Jaw',(0,-.035,1.66),(0,-.095,1.63),'Head')
for side,sign in [('Left',1),('Right',-1)]:
    bone(side+'Shoulder',(.11*sign,0,1.47),(.31*sign,0,1.47),'Chest')
    bone(side+'UpperArm',(.31*sign,0,1.47),(.55*sign,0,1.22),side+'Shoulder')
    bone(side+'LowerArm',(.55*sign,0,1.22),(.80*sign,0,.98),side+'UpperArm')
    bone(side+'Hand',(.80*sign,0,.98),(.88*sign,0,.89),side+'LowerArm')
    for finger,offset,length in [('Thumb',-.055,.085),('Index',-.035,.115),
                                 ('Middle',-.012,.135),('Ring',.012,.12),
                                 ('Pinky',.036,.095)]:
        bone(side+finger,(.87*sign,offset,.90),
             ((.87+length)*sign,offset*1.15,.90-length*.72),side+'Hand')
    bone(side+'UpperLeg',(.145*sign,0,.96),(.155*sign,0,.55),'Hips')
    bone(side+'LowerLeg',(.155*sign,0,.55),(.155*sign,0,.15),side+'UpperLeg')
    bone(side+'Foot',(.155*sign,0,.15),(.155*sign,-.18,.075),side+'LowerLeg')
    bone(side+'Toes',(.155*sign,-.18,.075),(.155*sign,-.27,.075),side+'Foot')

arm_data=bpy.data.armatures.new('HalloweenSkeleton_ArmatureData')
arm=bpy.data.objects.new('HalloweenSkeleton_Rig',arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm;arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,(h,t,parent,deform) in B.items():
    eb=arm_data.edit_bones.new(name);eb.head=h;eb.tail=t;eb.use_deform=deform
for name,(_,_,parent,_) in B.items():
    if parent: arm_data.edit_bones[name].parent=arm_data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');arm.select_set(False)

# Anatomical skeleton proportions and landmark detail; not a medical scan.
ellipsoid('Cranium',(0,-.012,1.775),(.125,.105,.15),'Head',segments=24,rings=16)
ellipsoid('Occipital',(0,.047,1.704),(.092,.072,.089),'Head')
ellipsoid('Face_Muzzle',(0,-.08,1.696),(.075,.063,.058),'Head')
ellipsoid('Nasal_Aperture',(0,-.146,1.711),(.018,.007,.032),'Head',socket_mat)
for s,n in [(-1,'R'),(1,'L')]:
    ellipsoid(n+'_EyeSocket',(s*.054,-.106,1.775),(.040,.014,.049),'Head',socket_mat)
    rod(n+'_Brow',(s*.019,-.123,1.826),(s*.095,-.115,1.822),.013,'Head')
    rod(n+'_Zygomatic',(s*.035,-.118,1.728),(s*.105,-.095,1.713),.014,'Head')
    ellipsoid(n+'_Cheek',(s*.083,-.106,1.703),(.032,.035,.020),'Head')
    ellipsoid(n+'_JawSide',(s*.061,-.084,1.645),(.018,.017,.026),'Jaw')
rod('LowerJaw',(-.07,-.12,1.623),(.07,-.12,1.623),.018,'Jaw')
for i in range(9):
    x=(i-4)*.017
    rod('TeethUpper%02d'%i,(x,-.145,1.664),(x,-.149,1.645),.007,'Head')
    rod('TeethLower%02d'%i,(x,-.145,1.628),(x,-.148,1.647),.007,'Jaw')
# Cervical, thoracic and lumbar vertebrae, with a continuous visible column.
for i in range(24):
    z=.99+i*.023
    bone_name='Spine' if z<1.28 else 'Chest'
    size=.024 if z<1.12 else .029
    ellipsoid(f'Vertebra_{i:02}',(0,.018,z),(size,.033,.019),bone_name)
    ellipsoid(f'Vertebral_Arch_{i:02}',(0,.047,z),(.022,.018,.014),bone_name,accent_mat)
for s,n in [(-1,'Right'),(1,'Left')]:
    chained(n+'_Clavicle',[(0,-.045,1.475),(s*.16,-.065,1.49),(s*.29,0,1.47)],.019,n+'Shoulder')
    ellipsoid(n+'_Scapula',(s*.22,.073,1.4),(.079,.025,.11),'Chest')
    chained(n+'_Iliac_Crest',[(s*.04,.005,1.04),(s*.12,.008,1.10),
                              (s*.22,.002,1.06),(s*.24,-.005,.98)],.018,'Hips')
    ellipsoid(n+'_Ilium',(s*.145,0,1.015),(.12,.068,.11),'Hips')
    ellipsoid(n+'_Acetabulum',(s*.155,-.056,.952),(.043,.018,.045),'Hips',accent_mat)
    rod(n+'_Pubis',(s*.11,-.037,.95),(0,-.09,.89),.027,'Hips')
ellipsoid('Sacrum',(0,.037,.98),(.07,.044,.085),'Hips')
# Twelve curved rib pairs with tapered lower ribs and visible intercostal gaps.
for row in range(12):
    z=1.455-row*.025
    width=.185 + .015*math.sin(min(row,7)/7*math.pi) - max(0,row-7)*.009
    for s,n in [(-1,'R'),(1,'L')]:
        pts=[(s*.035,-.075,z-.013),(s*width*.52,-.105,z+.012),
             (s*width,-.008,z+.014),(s*width*.82,.096,z+.010),(s*.05,.112,z-.014)]
        chained(f'Rib_{row:02}_{n}',pts,.0095,'Chest' if row<8 else 'Spine')
rod('Sternum_Manubrium',(0,-.115,1.47),(0,-.12,1.405),.024,'Chest')
rod('Sternum_Body',(0,-.12,1.405),(0,-.105,1.23),.019,'Chest')
rod('Xiphoid_Process',(0,-.105,1.23),(0,-.09,1.19),.012,'Chest')
# Limbs and joints, resting in the gently abducted stance shown in the reference.
for side,s in [('Left',1),('Right',-1)]:
    ellipsoid(side+'_ShoulderBall',(s*.31,0,1.47),(.043,.043,.043),side+'UpperArm')
    rod(side+'_Humerus',(s*.32,0,1.46),(s*.54,0,1.23),.029,side+'UpperArm')
    ellipsoid(side+'_Elbow',(s*.55,0,1.22),(.030,.032,.034),side+'LowerArm')
    rod(side+'_Radius',(s*.565,-.016,1.22),(s*.79,-.023,.99),.017,side+'LowerArm')
    rod(side+'_Ulna',(s*.535,.020,1.23),(s*.77,.018,1.00),.014,side+'LowerArm')
    ellipsoid(side+'_Wrist',(s*.80,0,.98),(.025,.026,.026),side+'Hand')
    ellipsoid(side+'_Palm',(s*.835,0,.94),(.042,.035,.052),side+'Hand')
    for finger,off,length in [('Thumb',-.055,.085),('Index',-.035,.115),
                              ('Middle',-.012,.135),('Ring',.012,.12),
                              ('Pinky',.036,.095)]:
        start=(s*.855,off,.91)
        end=(s*(.855+length),off*1.15,.91-length*.72)
        rod(side+finger+'_Digit',start,end,.0075,side+finger)
    ellipsoid(side+'_HipSocket',(s*.145,0,.95),(.057,.055,.063),side+'UpperLeg')
    rod(side+'_Femur',(s*.145,0,.92),(s*.155,0,.57),.042,side+'UpperLeg')
    ellipsoid(side+'_Knee',(s*.155,-.025,.55),(.046,.04,.05),side+'LowerLeg')
    rod(side+'_Tibia',(s*.155,-.008,.535),(s*.155,-.005,.165),.031,side+'LowerLeg')
    rod(side+'_Fibula',(s*.185,.017,.52),(s*.182,.025,.17),.012,side+'LowerLeg')
    ellipsoid(side+'_Ankle',(s*.155,0,.15),(.042,.05,.044),side+'Foot')
    ellipsoid(side+'_FootBones',(s*.155,-.11,.085),(.061,.13,.033),side+'Foot')
    for j,length in enumerate((.11,.095,.08,.065,.05)):
        xx=s*(.095+j*.028)
        rod(side+f'_Toe_{j}',(xx,-.18,.065),(xx,-.18-length,.061),.009,side+'Toes')

# Join all mesh pieces: Blender merges matching named vertex groups.
bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.join()
mesh=bpy.context.object;mesh.name='HalloweenSkeleton_SkinnedMesh'
mesh.parent=arm
modifier=mesh.modifiers.new('Armature_Skin','ARMATURE');modifier.object=arm
mesh.data.name='HalloweenSkeleton_Geometry'
# rigid weights still count as fully rigged skinning and deform correctly with bones
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True)
bpy.context.view_layer.objects.active=arm

bone_names=set(arm.data.bones.keys())
mesh_group_names={group.name for group in mesh.vertex_groups}
if mesh.parent != arm or not any(mod.type=='ARMATURE' and mod.object == arm for mod in mesh.modifiers):
    raise RuntimeError('Skinned mesh is not parented to the generated armature.')
if not mesh_group_names or not mesh_group_names.issubset(bone_names):
    raise RuntimeError('Mesh vertex groups do not map exclusively to rig bones.')
unweighted=[vertex.index for vertex in mesh.data.vertices
            if len(vertex.groups) != 1 or abs(vertex.groups[0].weight-1.0) > 1e-5]
if unweighted:
    raise RuntimeError(f'{len(unweighted)} vertices do not have one rigid 1.0 bone weight.')

def evaluated_positions():
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    evaluated_mesh=evaluated.to_mesh()
    positions=[vertex.co.copy() for vertex in evaluated_mesh.vertices]
    evaluated.to_mesh_clear()
    return positions

before=evaluated_positions()
arm.pose.bones['LeftUpperArm'].rotation_mode='XYZ'
arm.pose.bones['LeftUpperArm'].rotation_euler[2]=math.radians(20)
bpy.context.view_layer.update()
after=evaluated_positions()
arm.pose.bones['LeftUpperArm'].rotation_euler[2]=0
bpy.context.view_layer.update()
if len(before) != len(after) or max((a-b).length for a,b in zip(before,after)) < 1e-5:
    raise RuntimeError('Armature pose smoke test did not deform the skinned mesh.')
print(f'Rig/weight validation passed: {len(arm.data.bones)} bones, '
      f'{len(mesh.data.vertices)} fully weighted vertices; arm pose deforms mesh.')

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a.out,'HalloweenSkeleton.blend'))
fbx=os.path.join(a.out,'HalloweenSkeleton.fbx')
try:
    bpy.ops.export_scene.fbx(filepath=fbx,use_selection=True,add_leaf_bones=False,
                              apply_unit_scale=True,axis_forward='-Z',axis_up='Y',
                              bake_anim=False,mesh_smooth_type='FACE')
    print('FBX exported:',fbx)
except Exception as ex:
    raise RuntimeError(f'FBX exporter failed: {ex}') from ex
try:
    bpy.ops.export_scene.gltf(filepath=os.path.join(a.out,'HalloweenSkeleton.glb'),
                              export_format='GLB',use_selection=True,export_skins=True,
                              export_animations=False)
except Exception as ex: print('GLB exporter failed:',ex)
print('Finished; bones:',len(B),'mesh parts:',len(parts),'export directory:',a.out)
