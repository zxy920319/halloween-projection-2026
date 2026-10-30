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
red_mat=mat('Cursed_Red_Eyes',(.75,.009,.004),0,.22,emission=(1,.014,.008),power=5)
parts=[]

def weight_part(obj, bone, material):
    obj.data.materials.append(material)
    vg=obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    parts.append(obj)
    return obj

def ellipsoid(name, position, radii, bone, material=bone_mat, segments=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=position)
    o=bpy.context.object; o.name=name
    o.scale=radii
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return weight_part(o,bone,material)

def rod(name, start, end, radius, bone, material=bone_mat, vertices=10):
    v1,v2=Vector(start),Vector(end)
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
    B[name]=(head,tail,parent,deform)

bone('Hips',(0,0,.94),(0,0,1.08))
bone('Spine',(0,0,1.08),(0,0,1.27),'Hips')
bone('Chest',(0,0,1.27),(0,0,1.49),'Spine')
bone('Neck',(0,0,1.49),(0,0,1.61),'Chest')
bone('Head',(0,0,1.61),(0,0,1.85),'Neck')
bone('Jaw',(0,-.035,1.66),(0,-.095,1.63),'Head')
for side,sign in [('Left',1),('Right',-1)]:
    bone(side+'Shoulder',(.11*sign,0,1.47),(.31*sign,0,1.47),'Chest')
    bone(side+'UpperArm',(.31*sign,0,1.47),(.59*sign,0,1.47),side+'Shoulder')
    bone(side+'LowerArm',(.59*sign,0,1.47),(.85*sign,0,1.47),side+'UpperArm')
    bone(side+'Hand',(.85*sign,0,1.47),(.96*sign,0,1.47),side+'LowerArm')
    for finger,offset in [('Thumb',-.045),('Index',-.012),('Middle',.014),('Ring',.039)]:
        bone(side+finger,(.94*sign,offset,1.47), (1.04*sign,offset*1.15,1.47),side+'Hand')
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

# Anatomical-ish geometry. This is a game prototype, not an anatomical scan.
ellipsoid('Cranium',(0,-.012,1.775),(.125,.105,.15),'Head')
ellipsoid('Face_Muzzle',(0,-.08,1.696),(.086,.07,.068),'Head')
ellipsoid('Nasal_Aperture',(0,-.146,1.711),(.018,.007,.032),'Head',socket_mat)
for s,n in [(-1,'R'),(1,'L')]:
    ellipsoid(n+'_EyeSocket',(s*.054,-.106,1.775),(.040,.014,.049),'Head',socket_mat)
    ellipsoid(n+'_RedEye',(s*.054,-.120,1.778),(.018,.009,.023),'Head',red_mat)
    rod(n+'_Brow',(s*.019,-.123,1.826),(s*.095,-.115,1.822),.013,'Head')
    ellipsoid(n+'_Cheek',(s*.083,-.106,1.703),(.032,.035,.020),'Head')
    ellipsoid(n+'_JawSide',(s*.061,-.084,1.645),(.018,.017,.026),'Jaw')
rod('LowerJaw',(-.07,-.12,1.623),(.07,-.12,1.623),.018,'Jaw')
for i in range(9):
    x=(i-4)*.017
    rod('TeethUpper%02d'%i,(x,-.145,1.664),(x,-.149,1.645),.007,'Head')
# Spine, clavicles, scapulae, pelvis
for i in range(7):
    z=1.11+i*.064
    ellipsoid(f'Vertebra_{i}',(0,.016,z),(.043,.039,.034),'Spine' if i<3 else 'Chest')
for s,n in [(-1,'Right'),(1,'Left')]:
    chained(n+'_Clavicle',[(0,-.045,1.475),(s*.16,-.065,1.49),(s*.29,0,1.47)],.019,n+'Shoulder')
    ellipsoid(n+'_Scapula',(s*.22,.073,1.4),(.079,.025,.11),'Chest')
    ellipsoid(n+'_Ilium',(s*.135,0,1.015),(.11,.068,.104),'Hips')
    rod(n+'_Pubis',(s*.11,-.037,.95),(0,-.09,.89),.027,'Hips')
ellipsoid('Sacrum',(0,.037,.98),(.07,.044,.085),'Hips')
# Nine curved bilateral ribs, 4 rods each, with actual volume and dark gaps.
for row in range(9):
    z=1.455-row*.039
    width=(.185 if row<4 else .185-(row-4)*.019)
    for s,n in [(-1,'R'),(1,'L')]:
        pts=[(s*.035,-.075,z-.017),(s*width*.50,-.100,z+.015),
             (s*width,.008,z+.018),(s*width*.82,.103,z+.014),(s*.050,.112,z-.018)]
        chained(f'Rib_{row}_{n}',pts,.0105,'Chest' if row<6 else 'Spine')
rod('Sternum',(0,-.115,1.47),(0,-.093,1.205),.019,'Chest')
# limbs and joints
for side,s in [('Left',1),('Right',-1)]:
    ellipsoid(side+'_ShoulderBall',(s*.31,0,1.47),(.043,.043,.043),side+'UpperArm')
    rod(side+'_Humerus',(s*.32,0,1.47),(s*.58,0,1.47),.029,side+'UpperArm')
    ellipsoid(side+'_Elbow',(s*.59,0,1.47),(.030,.032,.034),side+'LowerArm')
    rod(side+'_Radius',(s*.61,-.016,1.478),(s*.838,-.023,1.477),.017,side+'LowerArm')
    rod(side+'_Ulna',(s*.61,.020,1.462),(s*.838,.018,1.463),.014,side+'LowerArm')
    ellipsoid(side+'_Wrist',(s*.85,0,1.47),(.025,.026,.026),side+'Hand')
    ellipsoid(side+'_Palm',(s*.908,0,1.47),(.055,.039,.025),side+'Hand')
    for finger,off in [('Thumb',-.045),('Index',-.012),('Middle',.014),('Ring',.039)]:
        rod(side+finger+'_Digit',(s*.943,off,1.47),(s*1.038,off*1.15,1.47),.008,side+finger)
    ellipsoid(side+'_HipSocket',(s*.145,0,.95),(.057,.055,.063),side+'UpperLeg')
    rod(side+'_Femur',(s*.145,0,.92),(s*.155,0,.57),.042,side+'UpperLeg')
    ellipsoid(side+'_Knee',(s*.155,-.025,.55),(.046,.04,.05),side+'LowerLeg')
    rod(side+'_Tibia',(s*.155,-.008,.535),(s*.155,-.005,.165),.031,side+'LowerLeg')
    rod(side+'_Fibula',(s*.185,.017,.52),(s*.182,.025,.17),.012,side+'LowerLeg')
    ellipsoid(side+'_Ankle',(s*.155,0,.15),(.042,.05,.044),side+'Foot')
    ellipsoid(side+'_FootBones',(s*.155,-.11,.085),(.061,.13,.033),side+'Foot')
    for j in range(4):
        xx=s*(.115+j*.027)
        rod(side+f'_Toe_{j}',(xx,-.18,.065),(xx,-.26,.061),.009,side+'Toes')

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
