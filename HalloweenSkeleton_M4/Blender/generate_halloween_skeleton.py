"""Generate a horror-realistic, full-body anatomical skeleton with a real Blender armature.
Run: blender --background --python generate_halloween_skeleton.py -- --out /absolute/path/output
Outputs .blend, .fbx and .glb if the installed Blender exporters support them.
Anatomy: skull with orbits/teeth/mandible, 24 vertebrae, 12 rib pairs with costal
cartilage, sternum, clavicles, scapulae, pelvis, tapered long bones, hands and feet.
Red glowing eyes live in the Cursed_Red_Eyes material. All mesh vertices are rigidly
weighted (1.0) to a single named bone. No external assets or add-ons.
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

bone_mat=mat('Ancient_Ivory', (.68,.60,.46),0,.82)
accent_mat=mat('Shadowed_Bone',(.38,.32,.25),0,.95)
socket_mat=mat('Deep_Eye_Sockets',(.006,.004,.004),0,1)
red_mat=mat('Cursed_Red_Eyes',(.85,.008,.004),0,.2,emission=(1,.014,.008),power=8)
parts=[]

def weight_part(obj, bone, material):
    obj.data.materials.append(material)
    for poly in obj.data.polygons: poly.use_smooth=True
    vg=obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    parts.append(obj)
    return obj

def ellipsoid(name, position, radii, bone, material=bone_mat, segments=20, rings=12, rot=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=position)
    o=bpy.context.object; o.name=name
    o.scale=radii
    if rot: o.rotation_euler=[math.radians(r) for r in rot]
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return weight_part(o,bone,material)

def rod(name, start, end, radius, bone, material=bone_mat, vertices=12, radius2=None):
    v1,v2=Vector(start),Vector(end)
    delta=v2-v1
    if delta.length<1e-5: return None
    r2=radius if radius2 is None else radius2
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=r2,
                                    depth=delta.length, location=(v1+v2)*.5)
    o=bpy.context.object; o.name=name
    o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return weight_part(o,bone,material)

def chained(name, pts, radius, bone, material=bone_mat, radius2=None):
    n=len(pts)-1
    for i in range(n):
        r1=radius if radius2 is None else radius+(radius2-radius)*i/n
        r2=radius if radius2 is None else radius+(radius2-radius)*(i+1)/n
        rod(f'{name}_{i:02}',pts[i],pts[i+1],r1,bone,material,radius2=r2)

def long_bone(name, start, end, shaft, head_r, bone, end_r=None, flat=1.0):
    """Tapered shaft with bulbous epiphyses on both ends."""
    v1,v2=Vector(start),Vector(end)
    d=(v2-v1).normalized()
    end_r=end_r or head_r
    rod(name+'_Shaft',v1+d*head_r*.6,v2-d*end_r*.6,shaft*1.15,bone,radius2=shaft*.9)
    ellipsoid(name+'_Head',v1,(head_r,head_r*flat,head_r),bone)
    ellipsoid(name+'_End',v2,(end_r,end_r*flat,end_r),bone)

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
FINGERS=[('Thumb',-.045),('Index',-.012),('Middle',.014),('Ring',.037),('Pinky',.058)]
for side,sign in [('Left',1),('Right',-1)]:
    bone(side+'Shoulder',(.11*sign,0,1.47),(.31*sign,0,1.47),'Chest')
    bone(side+'UpperArm',(.31*sign,0,1.47),(.59*sign,0,1.47),side+'Shoulder')
    bone(side+'LowerArm',(.59*sign,0,1.47),(.85*sign,0,1.47),side+'UpperArm')
    bone(side+'Hand',(.85*sign,0,1.47),(.96*sign,0,1.47),side+'LowerArm')
    for finger,offset in FINGERS:
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

# ---------------------------------------------------------------- skull
ellipsoid('Cranium',(0,.012,1.762),(.077,.097,.088),'Head',segments=28,rings=18)
ellipsoid('Occiput',(0,.05,1.72),(.06,.05,.055),'Head')
ellipsoid('Maxilla',(0,-.07,1.682),(.044,.036,.038),'Head')
ellipsoid('Nasal_Aperture',(0,-.103,1.700),(.011,.008,.024),'Head',socket_mat)
ellipsoid('Nasal_Bridge',(0,-.092,1.742),(.012,.012,.02),'Head')
rod('Brow_Ridge',(-.056,-.084,1.782),(.056,-.084,1.782),.0105,'Head')
for s,n in [(-1,'R'),(1,'L')]:
    ellipsoid(n+'_OrbitRim',(s*.034,-.079,1.744),(.031,.015,.033),'Head')
    ellipsoid(n+'_EyeSocket',(s*.034,-.082,1.744),(.026,.014,.028),'Head',socket_mat)
    ellipsoid(n+'_RedEye',(s*.034,-.089,1.744),(.014,.011,.017),'Head',red_mat,segments=16,rings=10)
    ellipsoid(n+'_Cheekbone',(s*.058,-.068,1.707),(.022,.024,.016),'Head')
    chained(n+'_ZygomaticArch',[(s*.062,-.066,1.708),(s*.080,-.03,1.712),(s*.078,.01,1.716)],.0075,'Head')
    ellipsoid(n+'_Temple',(s*.073,-.02,1.76),(.014,.04,.045),'Head')
upper_teeth=[(-.0195+.0049*i) for i in range(9)]
for i,x in enumerate(upper_teeth):
    y=-.099+abs(x)*0.9
    rod('TeethUpper%02d'%i,(x,y,1.664),(x,y-.001,1.643),.0042,'Head',radius2=.0036)
for i,x in enumerate(upper_teeth):
    y=-.093+abs(x)*0.9
    rod('TeethLower%02d'%i,(x,y,1.618+.003),(x,y-.001,1.640),.0038,'Jaw',radius2=.0042)
for s,n in [(-1,'R'),(1,'L')]:
    chained(n+'_MandibleBody',[(s*.07,.0,1.64),(s*.064,-.03,1.628),(s*.036,-.078,1.617),(s*.0,-.093,1.614)],
            .0125,'Jaw',radius2=.011)
    rod(n+'_MandibleRamus',(s*.072,.0,1.68),(s*.07,.0,1.642),.0115,'Jaw')
    ellipsoid(n+'_Condyle',(s*.072,.0,1.684),(.012,.014,.012),'Jaw')

# ---------------------------------------------------------------- spine
def spine_y(z):
    return .028+.022*math.sin((z-1.0)/.62*math.pi*1.7+.3)-.008

verts=[]
for i in range(7):     # cervical C1..C7
    verts.append((1.505+i*.017,'Neck',.015,.016))
for i in range(12):    # thoracic T1..T12
    verts.append((1.488-i*.0255,'Chest' if 1.488-i*.0255>1.27 else 'Spine',.020+i*.0007,.020))
for i in range(5):     # lumbar L1..L5
    verts.append((1.175-i*.0405,'Spine' if 1.175-i*.0405>1.08 else 'Hips',.030,.025))
thoracic_z=[]
for idx,(z,b,rx,rz) in enumerate(verts):
    y=spine_y(z)
    ellipsoid(f'VertebraBody_{idx:02}',(0,y,z),(rx,rx*.9,rz),b)
    rod(f'SpinousProcess_{idx:02}',(0,y+rx*.6,z+.003),(0,y+rx+.014,z-.008),.0045,b,radius2=.0028)
    for s in (-1,1):
        rod(f'Transverse_{idx:02}_{"L" if s>0 else "R"}',(s*rx*.6,y+rx*.5,z),(s*(rx+.012+(.012 if idx>=7 else 0)),y+rx*.6,z),.004,b,radius2=.003)
    if 7<=idx<19: thoracic_z.append((z,y,b))
    # disc
    if idx<len(verts)-1:
        nz=verts[idx+1][0]
        ellipsoid(f'Disc_{idx:02}',(0,spine_y((z+nz)/2),(z+nz)/2),(rx*.92,rx*.82,.004),b,accent_mat,segments=14,rings=6)
ellipsoid('Sacrum',(0,.052,.985),(.05,.026,.07),'Hips',rot=(-14,0,0))
rod('Coccyx',(0,.062,.925),(0,.078,.872),.012,'Hips',radius2=.004)

# ---------------------------------------------------------------- rib cage
ster_top,ster_bot=1.490,1.225
ster_y=-.108
rod('Manubrium',(0,ster_y,ster_top),(0,ster_y-.001,ster_top-.05),.021,'Chest',radius2=.019)
rod('Sternum_Body',(0,ster_y,ster_top-.052),(0,ster_y-.002,ster_bot+.02),.016,'Chest',radius2=.014)
rod('Xiphoid',(0,ster_y-.002,ster_bot+.02),(0,ster_y-.004,ster_bot-.01),.007,'Chest',radius2=.002)
prev_end=None
for row,(z,sy,b) in enumerate(thoracic_z):
    w=.085+.095*math.sin(math.pi*min(row+2.2,12)/13.5)
    depth=.062+.014*min(row,6)/6.0
    cy=(sy+.012+(-.108+.0))/2+.003
    for s,n in [(-1,'R'),(1,'L')]:
        pts=[]
        a0,a1=.22,(math.pi*.9 if row<10 else math.pi*.62)
        steps=9
        for k in range(steps+1):
            t=k/steps; ang=a0+(a1-a0)*t
            x=s*w*math.sin(ang)
            y=cy+depth*math.cos(ang)
            zz=z-.085*(t**1.4)*(0.7+0.4*row/11.0)
            pts.append((x,y,zz))
        bone_name='Chest' if b=='Chest' else 'Spine'
        chained(f'Rib_{row+1:02}_{n}',pts,.0085,bone_name,radius2=.0065)
        if row<10:
            end=Vector(pts[-1])
            target=Vector((s*.012,ster_y,min(max(end.z+.012,ster_bot),ster_top-.01)))
            if row>6: target=Vector((s*.03,ster_y+.01,end.z+.035))
            chained(f'Cartilage_{row+1:02}_{n}',[tuple(end),tuple((end+target)*.5+Vector((0,-.004,.006))),tuple(target)],
                    .0075,'Chest' if row<6 else 'Spine',accent_mat)

# ---------------------------------------------------------------- girdles
for s,n in [(-1,'Right'),(1,'Left')]:
    chained(n+'_Clavicle',[(s*.012,-.058,1.482),(s*.10,-.075,1.496),(s*.2,-.052,1.492),(s*.29,-.012,1.476)],.0105,n+'Shoulder',radius2=.0095)
    ellipsoid(n+'_Scapula',(s*.17,.086,1.42),(.052,.012,.078),'Chest',rot=(0,0,s*-10))
    rod(n+'_ScapularSpine',(s*.115,.083,1.46),(s*.27,.052,1.485),.0085,'Chest')
    ellipsoid(n+'_Acromion',(s*.285,.012,1.485),(.026,.02,.011),n+'Shoulder')
    ellipsoid(n+'_Ilium',(s*.12,.025,1.02),(.062,.026,.07),'Hips',rot=(0,s*-15,0))
    ellipsoid(n+'_IliacCrest',(s*.15,.02,1.082),(.05,.022,.01),'Hips',rot=(0,s*-15,0))
    ellipsoid(n+'_Ischium',(s*.108,.026,.915),(.026,.03,.045),'Hips')
    chained(n+'_PubicRamus',[(s*.115,-.012,.945),(s*.085,-.06,.93),(s*.012,-.085,.935)],.0125,'Hips')
    ellipsoid(n+'_Acetabulum',(s*.138,-.004,.955),(.032,.03,.034),'Hips',accent_mat)
rod('PubicSymphysis',(-.014,-.088,.935),(.014,-.088,.935),.012,'Hips')

# ---------------------------------------------------------------- limbs
for side,s in [('Left',1),('Right',-1)]:
    ellipsoid(side+'_ShoulderBall',(s*.322,0,1.47),(.027,.03,.03),side+'UpperArm')
    long_bone(side+'_Humerus',(s*.325,0,1.47),(s*.585,0,1.47),.0155,.026,side+'UpperArm',end_r=.022)
    ellipsoid(side+'_Olecranon',(s*.598,.026,1.47),(.014,.016,.016),side+'LowerArm')
    long_bone(side+'_Radius',(s*.608,-.016,1.474),(s*.842,-.016,1.474),.0105,.014,side+'LowerArm',end_r=.017)
    long_bone(side+'_Ulna',(s*.608,.016,1.466),(s*.842,.020,1.466),.011,.016,side+'LowerArm',end_r=.011)
    for k in range(4):
        ellipsoid(side+f'_Carpal_{k}',(s*.855,-.021+k*.014,1.47),(.01,.0085,.0075),side+'Hand')
    for (finger,off),meta_y in zip(FINGERS,[-.04,-.016,.008,.03,.05]):
        x0=.87 if finger!='Thumb' else .865
        rod(side+f'_Metacarpal_{finger}',(s*x0,meta_y,1.47),(s*.938,off,1.47),.0065,side+'Hand',radius2=.0055)
        ellipsoid(side+f'_Knuckle_{finger}',(s*.942,off,1.47),(.0075,.0075,.0075),side+'Hand')
        n_ph=2 if finger=='Thumb' else 3
        L=.098
        for ph in range(n_ph):
            t0=ph/n_ph*0.0+ph*(L/ n_ph)*(1.0)
            x1=.945+t0; x2=x1+L/n_ph-.004
            r=.0052-.0009*ph
            rod(side+f'_Phalanx_{finger}_{ph}',(s*x1,off*(1+ph*.04),1.47),(s*x2,off*(1+(ph+1)*.04),1.47),r,side+finger,radius2=r*.85)
    ellipsoid(side+'_FemurHead',(s*.138,0,.953),(.026,.026,.026),side+'UpperLeg')
    chained(side+'_FemurNeck',[(s*.138,0,.953),(s*.17,0,.925)],.013,side+'UpperLeg')
    ellipsoid(side+'_GreaterTrochanter',(s*.178,.006,.92),(.019,.022,.026),side+'UpperLeg')
    long_bone(side+'_Femur',(s*.17,0,.9),(s*.155,0,.565),.0235,.022,side+'UpperLeg',end_r=.036)
    ellipsoid(side+'_Patella',(s*.155,-.05,.55),(.022,.011,.026),side+'LowerLeg')
    long_bone(side+'_Tibia',(s*.153,-.004,.535),(s*.152,-.004,.17),.0185,.036,side+'LowerLeg',end_r=.024)
    long_bone(side+'_Fibula',(s*.19,.02,.52),(s*.182,.018,.17),.0085,.0135,side+'LowerLeg')
    ellipsoid(side+'_Talus',(s*.155,-.005,.13),(.03,.04,.026),side+'Foot')
    ellipsoid(side+'_Calcaneus',(s*.155,.035,.072),(.025,.05,.03),side+'Foot')
    ellipsoid(side+'_Tarsals',(s*.155,-.085,.075),(.044,.06,.024),side+'Foot')
    for j in range(5):
        xx=s*(.125+j*.0155)
        rod(side+f'_Metatarsal_{j}',(xx,-.08,.07),(xx+s*.002*j,-.178,.052),.0075,side+'Foot',radius2=.0062)
        rod(side+f'_ToeBone_{j}',(xx+s*.002*j,-.184,.05),(xx+s*.002*j,-.225-(0 if j else .01),.045),.0058,side+'Toes',radius2=.0045)
        if j<4: rod(side+f'_ToeTip_{j}',(xx+s*.002*j,-.228,.045),(xx+s*.002*j,-.255+j*.006,.042),.0045,side+'Toes',radius2=.0032)

# Join all mesh pieces: Blender merges matching named vertex groups.
bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.join()
mesh=bpy.context.object;mesh.name='HalloweenSkeleton_SkinnedMesh'
mesh.parent=arm
modifier=mesh.modifiers.new('Armature_Skin','ARMATURE');modifier.object=arm
mesh.data.name='HalloweenSkeleton_Geometry'
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
