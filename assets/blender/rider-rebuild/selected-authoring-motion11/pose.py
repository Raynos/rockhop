"""Map the six authored movement scores onto native controls."""
import math
import bpy
from mathutils import Matrix, Quaternion, Vector
from controls import ctrl

X, F, Z = Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
I = Quaternion((1, 0, 0, 0))


def rotation(axis, degrees): return Quaternion(axis, math.radians(degrees))


def arm_direction(elevation, azimuth, sign):
    e, a = math.radians(elevation), math.radians(azimuth)
    return (F*math.cos(a)+X*(sign*math.sin(a)))*math.sin(e)-Z*math.cos(e)


def range_pose(label, context):
    r = {'root': Vector((0, 0, 0)), 'pitch': 0., 'roll': 0., 'chest': 0.,
         'chestPitch': 0., 'headYaw': 0., 'headNod': 0., 'shoulder': 0., 'grip': 0., 'arms': {}}
    for side, sign in [('L', 1), ('R', -1)]:
        limb = next(l for l in context['limbs'] if l['kind']=='arm' and l['side']==side)
        h=context['heads']; upper=(h[limb['lowers'][0]]-h[limb['uppers'][0]]).normalized()
        lower=(h[limb['end']]-h[limb['lowers'][0]]).normalized()
        if label in ('A', 'T', 'overhead'):
            upper=arm_direction({'A':45., 'T':90., 'overhead':172.}[label], 90., sign)
            lower=upper.copy()
            if label=='overhead': lower=(upper+F*.08).normalized(); r['shoulder']=12.
        elif label in ('reach', 'crouch'):
            upper=arm_direction(80. if label=='reach' else 70., 8., sign)
            lower=rotation(X, -15.)@upper
        elif label=='asymmetric':
            upper=arm_direction(125. if side=='L' else 45., 15. if side=='L' else 70., sign)
            lower=rotation(X, -20.)@upper
        r['arms'][side]=(upper,lower)
    if label=='asymmetric': r.update(roll=6., chest=20., headYaw=-10., grip=.35)
    if label=='crouch': r.update(root=Vector((0, .105, -.40)), pitch=12., chestPitch=18., headNod=-12., grip=.1)
    if label=='head': r.update(headYaw=35., headNod=15.)
    return r


def apply(rig, context, row):
    for name in context['controls']:
        b=rig.pose.bones[name]; b.location=(0,0,0); b.rotation_quaternion=I; b.scale=(1,1,1)
    current=dict(row); current['root']=Vector(row['root']); current['chestPitch']=0.; current['shoulder']=0.
    range_arms=None
    if 'range' in row:
        a=range_pose(row['range']['from'],context); b=range_pose(row['range']['to'],context); u=row['range']['blend']
        for key in a:
            if key!='arms': current[key]=a[key]*(1-u)+b[key]*u
        range_arms={side:tuple(x.lerp(y,u).normalized() for x,y in zip(a['arms'][side],b['arms'][side])) for side in ('L','R')}
    rest=context['rest']; heads=context['heads']; roles=context['roles']; pelvis=roles['pelvis']
    yaw=rotation(Z,current['yaw']); pelvis_rotation=yaw@rotation(F,current['roll'])@rotation(X,current['pitch'])
    m=(pelvis_rotation@rest[pelvis].to_quaternion()).to_matrix().to_4x4(); m.translation=heads[pelvis]+current['root']
    rig.pose.bones[ctrl(pelvis)].matrix=m
    for name in roles['trunk'][1:]:
        q=rotation(Z,current['chest']/3)@rotation(X,current['chestPitch']/3); r=rest[name].to_quaternion()
        rig.pose.bones[ctrl(name)].rotation_quaternion=r.inverted()@q@r
    for name,share in zip([*roles['neck'],roles['head']],(.20,.25,.55)):
        r=rest[name].to_quaternion(); q=rotation(Z,current['headYaw']*share)@rotation(X,current['headNod']*share)
        rig.pose.bones[ctrl(name)].rotation_quaternion=r.inverted()@q@r
    for side,sign,role_side in [('L',1,'Left'),('R',-1,'Right')]:
        name=roles['shoulder'+role_side]; r=rest[name].to_quaternion()
        rig.pose.bones[ctrl(name)].rotation_quaternion=r.inverted()@rotation(F,sign*current['shoulder'])@r
        palm=rig.pose.bones['CTRL-palm.'+side]
        for digit in ('thumb','index','middle','ring','pinky'): palm[digit]=current['grip']
    bpy.context.view_layer.update()
    intended={}
    for limb in context['limbs']:
        side=limb['side']; sign=1 if side=='L' else -1; target=limb['targetControl']; pole=limb['poleControl']
        if limb['kind']=='leg':
            foot=current['feet'][side]; q=rotation(Z,foot.get('yaw',0.)); m=(q@rest[limb['socket']].to_quaternion()).to_matrix().to_4x4()
            point=heads[limb['socket']].copy()
            if 'turnFrom' in foot:
                pivot=Vector((heads[pelvis].x,heads[pelvis].y,0.))
                a=rotation(Z,foot['turnFrom'])@(point-pivot)+pivot
                b=rotation(Z,foot['turnTo'])@(point-pivot)+pivot
                point=a.lerp(b,foot['turnBlend'])
            point+=F*foot['forward']+Z*foot['up']; m.translation=point; rig.pose.bones[target].matrix=m
            ankle=m@rest[limb['socket']].inverted()@rest[limb['end']]
            start=rig.pose.bones[limb['uppers'][0]].matrix.translation.copy()
            source_ray=(heads[limb['end']]-heads[limb['uppers'][0]]).normalized()
            bend=heads[limb['lowers'][0]]-heads[limb['uppers'][0]]; bend-=source_ray*bend.dot(source_ray)
            rig.pose.bones[pole].matrix=Matrix.Translation((start+ankle.translation)*.5+yaw@bend.normalized()*.5)
            intended[side]={'sole':list(point),'planted':foot['planted'],'plant':foot.get('plant')}
        else:
            start=rig.pose.bones[limb['uppers'][0]].matrix.translation.copy(); a,b=limb['lengths']
            if range_arms is not None: upper,lower=range_arms[side]
            elif current['arms'] in ('swing','jump'):
                angle=current['armSwing']*(-sign if current['arms']=='swing' else 1.)
                upper=(rotation(X,-angle)@(-Z)+X*(sign*.12)).normalized()
                lower=rotation(X,-current['elbow'])@upper
            else:
                upper=(heads[limb['lowers'][0]]-heads[limb['uppers'][0]]).normalized()
                lower=(heads[limb['end']]-heads[limb['lowers'][0]]).normalized()
            upper,lower=yaw@upper,yaw@lower; elbow=start+upper*a; wrist=elbow+lower*b
            rest_lower=(heads[limb['end']]-heads[limb['lowers'][0]]).normalized()
            q=rest_lower.rotation_difference(lower)@rest[limb['end']].to_quaternion()
            m=q.to_matrix().to_4x4(); m.translation=wrist
            rig.pose.bones[target].matrix=m@rest[limb['end']].inverted()@rest[limb['socket']]
            ray=(wrist-start).normalized(); bend=elbow-start-ray*(elbow-start).dot(ray)
            if bend.length<1e-6:
                bend=yaw@F; bend-=ray*bend.dot(ray)
            rig.pose.bones[pole].matrix=Matrix.Translation(elbow+bend.normalized()*.4)
    bpy.context.view_layer.update()
    limb_checks={}
    for limb in context['limbs']:
        start=rig.pose.bones[limb['uppers'][0]].matrix.translation
        middle=rig.pose.bones[limb['lowers'][0]].matrix.translation
        end=rig.pose.bones[limb['end']].matrix.translation
        target=rig.pose.bones[limb['target']].matrix.translation
        length_error=max(abs((middle-start).length-limb['lengths'][0]),abs((end-middle).length-limb['lengths'][1]))
        target_error=(end-target).length
        assert length_error<.0001 and target_error<.0001,('Native limb failed target/length',limb['kind'],limb['side'],length_error,target_error)
        flex=math.degrees((middle-start).angle(end-middle))
        limb_checks[limb['kind']+limb['side']]={'targetM':target_error,'lengthM':length_error,'flexDegrees':flex}
    for side in ('L','R'):
        actual=rig.pose.bones['SoleSocket.'+side].matrix.translation
        intended[side]['actualSole']=list(actual); intended[side]['errorM']=(actual-Vector(intended[side]['sole'])).length
        assert intended[side]['errorM']<.0001, ('Unreachable/sliding sole target',side,intended[side])
    return {'feet':intended,'limbs':limb_checks}
