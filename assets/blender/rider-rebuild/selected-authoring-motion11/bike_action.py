"""One source-driven seated/forward/back score on native M11 controls.

Only two pelvis translations solve the fixed, finite jeans support cores. Torso
bend follows a declared elbow-flex score; poles come from the exact two-link
triangle. No bind, object transform, vertex or old author04 pose is rewritten.
"""
import math
import bpy
from mathutils import Matrix, Quaternion, Vector
from controls import ctrl

FPS, SECONDS = 24, 10
KEYS = [(0.,25.,75.),(1.,25.,75.),(2.5,35.,95.),(3.5,35.,95.),
        (5.,25.,75.),(6.,25.,75.),(7.5,15.,55.),(8.5,15.,55.),(10.,25.,75.)]
PAIRS = [('DEF-pelvis.L','DEF-spine'),('DEF-pelvis.R','DEF-spine'),
         ('DEF-thigh.L.001','DEF-thigh.L'),('DEF-thigh.R.001','DEF-thigh.R')]


def score(time):
    for a,b in zip(KEYS,KEYS[1:]):
        if time <= b[0]:
            u=max(0.,(time-a[0])/(b[0]-a[0])); u=u*u*u*(10+u*(-15+6*u))
            return {'pelvisPitchDegrees':a[1]+u*(b[1]-a[1]),'elbowFlexDegrees':a[2]+u*(b[2]-a[2])}
    return {'pelvisPitchDegrees':KEYS[-1][1],'elbowFlexDegrees':KEYS[-1][2]}


def pitch(degrees): return Quaternion((1,0,0),math.radians(degrees))


def bend_triangle(start,end,lengths,bend_hint):
    ray=end-start; distance=ray.length; a,b=lengths
    assert abs(a-b)+.001 < distance < a+b-.001, ('Joint target outside finite reach',distance,lengths)
    ray.normalize(); bend=bend_hint-ray*bend_hint.dot(ray)
    assert bend.length>.001, 'Pole plane is degenerate'
    bend.normalize(); along=(a*a-b*b+distance*distance)/(2*distance)
    middle=start+ray*along+bend*math.sqrt(max(0.,a*a-along*along))
    return middle,middle+bend*.45


def body_fk(context,root,pelvis_pitch,chest_pitch):
    rest=context['rest']; roles=context['roles']; pelvis=roles['pelvis']; result={}
    matrix=(pitch(pelvis_pitch)@rest[pelvis].to_quaternion()).to_matrix().to_4x4(); matrix.translation=root
    result[pelvis]=matrix
    for name in context['fk'][1:]:
        parent=context['parents'][name]; local=rest[parent].inverted()@rest[name]
        q=Quaternion((1,0,0,0))
        if name in roles['trunk'][1:]:
            basis=rest[name].to_quaternion(); q=basis.inverted()@pitch(chest_pitch/3)@basis
        result[name]=result[parent]@local@q.to_matrix().to_4x4()
    return result


def chest_for_reach(context,bike,root,params,strict=True):
    # One monotone geometric bisection, not a pose/parameter sweep. Both arms
    # share the same torso angle and each keeps its own measured wrist target.
    arms=[l for l in context['limbs'] if l['kind']=='arm']; rest=context['rest']
    def residual(angle):
        body=body_fk(context,root,params['pelvisPitchDegrees'],angle); differences=[]
        for limb in arms:
            parent=context['parents'][limb['uppers'][0]]
            start=(body[parent]@rest[parent].inverted()@rest[limb['uppers'][0]]).translation
            end=(Matrix(bike['nativeControlMatrices'][limb['targetControl']])@rest[limb['socket']].inverted()@rest[limb['end']]).translation
            a,b=limb['lengths']; wanted=math.sqrt(a*a+b*b+2*a*b*math.cos(math.radians(params['elbowFlexDegrees'])))
            differences.append((end-start).length-wanted)
        return sum(differences)/len(differences)
    lo,hi=0.,45.; a,b=residual(lo),residual(hi)
    if a*b>0:
        assert not strict, ('Final torso reach score has no supported bracket',params,list(root),a,b)
        # The pelvis initial estimate has not yet been located by its surface.
        # This temporary torso cannot influence the verified pelvis/thigh-only
        # support cores; the final pose must solve the strict reach bracket.
        return lo if abs(a)<abs(b) else hi
    for _ in range(18):
        middle=(lo+hi)/2; value=residual(middle)
        if value*a>0:lo,a=middle,value
        else:hi=middle
    return (lo+hi)/2


def pose(rig,context,bike,root,params,strict_chest=True):
    for name in context['controls']: rig.pose.bones[name].matrix_basis=Matrix.Identity(4)
    chest=chest_for_reach(context,bike,root,params,strict_chest); pelvis=context['roles']['pelvis']; rest=context['rest']
    matrix=(pitch(params['pelvisPitchDegrees'])@rest[pelvis].to_quaternion()).to_matrix().to_4x4(); matrix.translation=root
    rig.pose.bones[ctrl(pelvis)].matrix=matrix
    for name in context['roles']['trunk'][1:]:
        basis=rest[name].to_quaternion(); rig.pose.bones[ctrl(name)].rotation_quaternion=basis.inverted()@pitch(chest/3)@basis
    nod=10.-params['pelvisPitchDegrees']-chest
    for name,share in zip([*context['roles']['neck'],context['roles']['head']],(.2,.25,.55)):
        basis=rest[name].to_quaternion(); rig.pose.bones[ctrl(name)].rotation_quaternion=basis.inverted()@pitch(nod*share)@basis
    for name,values in bike['nativeControlMatrices'].items():rig.pose.bones[name].matrix=Matrix(values)
    for side in ('L','R'):
        for digit in ('thumb','index','middle','ring','pinky'):rig.pose.bones['CTRL-palm.'+side][digit]=.75
    bpy.context.view_layer.update()
    for limb in context['limbs']:
        start=rig.pose.bones[limb['mechanismUpper']].matrix.translation.copy()
        end=rig.pose.bones[limb['target']].matrix.translation.copy(); sign=1 if limb['side']=='L' else -1
        hint=Vector((sign*.16,-1.,0.)) if limb['kind']=='leg' else Vector((sign*.75,.35,-.35))
        _,pole=bend_triangle(start,end,limb['lengths'],hint)
        rig.pose.bones[limb['poleControl']].matrix=Matrix.Translation(pole)
    bpy.context.view_layer.update()
    limbs=[];contacts=[]
    for limb in context['limbs']:
        start=rig.pose.bones[limb['uppers'][0]].matrix.translation
        middle=rig.pose.bones[limb['lowers'][0]].matrix.translation
        end=rig.pose.bones[limb['end']].matrix.translation; target=rig.pose.bones[limb['target']].matrix.translation
        row={'name':limb['kind']+limb['side'],'startNative':list(start),'middleNative':list(middle),'endNative':list(end),
             'targetNative':list(target),'targetM':(end-target).length,
             'lengthM':max(abs((middle-start).length-limb['lengths'][0]),abs((end-middle).length-limb['lengths'][1])),
             'outerReachMarginM':sum(limb['lengths'])-(target-start).length,
             'flexDegrees':math.degrees((middle-start).angle(end-middle))}
        limbs.append(row)
        intended=Matrix(bike['nativeControlMatrices'][limb['targetControl']]);actual=rig.pose.bones[limb['socket']].matrix
        operator=actual@intended.inverted()
        physical=2*math.sqrt(sum((operator[i][j]-(i==j))**2 for i in range(3) for j in range(3)))+operator.translation.length
        contacts.append({'socket':limb['socket'],'frameAffineBoundWithin2mM':physical,'positionResidualM':(actual.translation-intended.translation).length})
    assert all(max(r['targetM'],r['lengthM'])<.0001 for r in limbs), limbs
    assert all(r['frameAffineBoundWithin2mM']<.0001 for r in contacts), contacts
    return {'pelvisNative':list(root),'pelvisPitchDegrees':params['pelvisPitchDegrees'],'chestPitchDegrees':chest,
            'headNodDegrees':nod,'limbs':limbs,'contactFrames':contacts}


def skinned(points,rig,context):
    operators={n:rig.pose.bones[n].matrix@context['rest'][n].inverted() for n in context['names']}
    return {i:sum((operators[n]@p*w for n,w in weights.items()),Vector())/sum(weights.values()) for i,(p,weights) in points.items()}


def centroid(points,triangles):
    total=0.; result=Vector()
    for ids in triangles:
        a,b,c=[points[i] for i in ids]; area=(b-a).cross(c-a).length/2
        total+=area;result+=(a+b+c)*(area/3)
    assert total>0;return result/total


def solve_seat(rig,context,bike,document,support,params,previous=None):
    to_native=Matrix(document['bikeToNative']); to_bike=Matrix(document['nativeToBike'])
    targets=support['guideCentersBike']; target=(Vector(targets['left'])+Vector(targets['right']))/2
    rest_center=sum((centroid({i:p for i,(p,_) in support['points'].items()},support['triangles'][s]) for s in ('left','right')),Vector())/2
    # Initial geometry comes from the real rest core, not an inherited pose.
    initial=to_native@target-pitch(params['pelvisPitchDegrees'])@(rest_center-context['heads'][context['roles']['pelvis']])
    root=previous.copy() if previous is not None else initial.copy(); history=[]
    def residual(position):
        witness=pose(rig,context,bike,position,params,strict_chest=False); actual=skinned(support['points'],rig,context)
        centers={s:to_bike@centroid(actual,support['triangles'][s]) for s in ('left','right')}
        midpoint=(centers['left']+centers['right'])/2
        return Vector((midpoint.x-target.x,midpoint.y-target.y)),witness,centers
    for iteration in range(7):
        error,witness,centers=residual(root); history.append({'iteration':iteration,'pelvisNative':list(root),'centroidErrorBikeXY':list(error)})
        if error.length < .0001:
            witness=pose(rig,context,bike,root,params,strict_chest=True)
            return root,{**witness,'finiteCoreCentroidsBike':{s:list(c) for s,c in centers.items()},'supportSolve':history}
        epsilon=.001; columns=[]
        for delta in (Vector((epsilon,0,0)),Vector((0,epsilon,0))):
            shifted=residual(root+to_native.to_3x3()@delta)[0];columns.append((shifted-error)/epsilon)
        a,b=columns; determinant=a.x*b.y-b.x*a.y
        assert abs(determinant)>.05, ('Seat support cannot locate pelvis',history)
        correction=Vector(((-error.x*b.y+b.x*error.y)/determinant,(-a.x*error.y+error.x*a.y)/determinant,0.))
        if correction.length>.04:correction*=.04/correction.length
        root+=to_native.to_3x3()@correction
        assert (root-initial).length<.15, ('Seat requires anatomical reauthoring, not a large pelvis move',history)
    raise AssertionError(('Fixed finite support centroids did not converge; retain failure',history))
