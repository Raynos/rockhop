"""Six authored movement scores in native X-left, -Y-forward, Z-up metres.

Foot locations are world-space sole targets, not sinusoidal ankle rotations.
Walk/jog contain one travelling cycle; root displacement is explicit metadata.
"""
import math

FPS = 24
SCORES = {
    'RiderIdle': {'seconds': 3., 'loop': True},
    'RiderWalk': {'seconds': 1.25, 'loop': True, 'rootForwardM': .70},
    'RiderJog': {'seconds': .75, 'loop': True, 'rootForwardM': .95},
    'RiderTurn90': {'seconds': 3., 'loop': False},
    'RiderJumpLand': {'seconds': 2.5, 'loop': False},
    'RiderRangeOfMotion': {'seconds': 12., 'loop': False},
}


def smooth(x):
    x = max(0., min(1., x)); return x*x*(3-2*x)


def mix(a, b, t):
    return a+(b-a)*t


def hermite(a, b, va, vb, duration, u):
    return (2*u**3-3*u*u+1)*a+(u**3-2*u*u+u)*duration*va+(-2*u**3+3*u*u)*b+(u**3-u*u)*duration*vb


def range_body(label):
    """Body targets shared with the source-length reach preflight."""
    r={'root':[0.,0.,0.],'pitch':0.,'roll':0.,'chest':0.,'chestPitch':0.,'headYaw':0.,'headNod':0.,'grip':0.}
    # A planted asymmetrical roll needs knee yield: the old straight-legged
    # stance raised the left hip beyond its 0.803744 m physical leg reach.
    if label=='asymmetric':r.update(root=[0.,0.,-.020],roll=6.,chest=20.,headYaw=-10.,grip=.35)
    if label=='crouch':r.update(root=[0.,.105,-.40],pitch=12.,chestPitch=18.,headNod=-12.,grip=.1)
    if label=='head':r.update(headYaw=35.,headNod=15.)
    return r


def foot_cycle(t, seconds, stride, duty, offset, clearance):
    phase = t/seconds+offset; step = math.floor(phase+1e-10); q = phase-step
    if q < 0: q = 0.
    plant = (step-offset)*stride+stride*duty*.5
    if q <= duty:
        return {'forward': plant, 'up': 0., 'planted': True, 'plant': step}
    u = (q-duty)/(1-duty)
    return {'forward': plant+stride*smooth(u), 'up': clearance*math.sin(math.pi*u)**2,
            'planted': False, 'plant': None}


def score(name, t):
    """Small explicit score; Blender maps these controls to the pinned skeleton."""
    seconds = SCORES[name]['seconds']; t = max(0., min(seconds, t)); phase = t/seconds
    r = {'root': [0., 0., 0.], 'yaw': 0., 'pitch': 0., 'roll': 0., 'chest': 0.,
         'headYaw': 0., 'headNod': 0., 'arms': 'rest', 'armSwing': 0., 'elbow': 15.,
         'grip': .12, 'feet': {s: {'forward': 0., 'up': 0., 'planted': True, 'plant': 0}
                              for s in ('L', 'R')}}
    if name == 'RiderIdle':
        r['root'] = [.004*math.sin(2*math.pi*phase), 0., -.009*(1-math.cos(2*math.pi*phase))]
        r['chest'] = .8*math.sin(2*math.pi*phase); r['headYaw'] = 3.*math.sin(2*math.pi*phase)
    elif name in ('RiderWalk', 'RiderJog'):
        jogging = name == 'RiderJog'; stride = SCORES[name]['rootForwardM']; duty = .40 if jogging else .62
        r['root'] = [.012*math.cos(2*math.pi*phase), -stride*phase,
                     (-.090+.030*math.cos(4*math.pi*(phase-.45))) if jogging else (-.075+.012*math.cos(4*math.pi*phase))]
        r['yaw'] = 3.*math.sin(2*math.pi*phase); r['pitch'] = 7. if jogging else 2.
        r['chest'] = -3.*math.sin(2*math.pi*phase)
        r['arms'] = 'swing'; r['armSwing'] = (32. if jogging else 20.)*math.cos(2*math.pi*phase)
        r['elbow'] = 78. if jogging else 24.; r['grip'] = .28 if jogging else .17
        r['feet'] = {s: foot_cycle(t, seconds, stride, duty, offset, .13 if jogging else .075)
                     for s, offset in [('L', 0.), ('R', .5)]}
    elif name == 'RiderTurn90':
        step = min(2, int(t)); u = min(1., t-step); lift = smooth(u)
        target = [45., 90., 90.][step]; previous = [0., 45., 90.][step]
        r['yaw'] = mix(previous, target, lift); r['root'][2] = -.035-.01*math.sin(math.pi*u)**2
        for s in ('L', 'R'):
            from_yaw = {'L': [0., 45., 45.], 'R': [0., 0., 90.]}[s][step]
            to_yaw = target if s == ['L', 'R', 'L'][step] else from_yaw
            moving = to_yaw != from_yaw
            r['feet'][s].update(turnFrom=from_yaw, turnTo=to_yaw, turnBlend=lift,
                                yaw=mix(from_yaw, to_yaw, lift),
                                up=.085*math.sin(math.pi*u)**2 if moving else 0.,
                                planted=not moving or u in (0., 1.))
        r['arms'] = 'swing'; r['armSwing'] = -8.*math.sin(math.pi*u); r['elbow'] = 20.
    elif name == 'RiderJumpLand':
        takeoff, touchdown = .85, 1.35; flight = touchdown-takeoff; speed = 9.81*flight/2
        if t < .60:
            compression = smooth(t/.60); r['root'][2] = -.25*compression
            r['pitch'] = 16.*compression; r['arms'] = 'jump'; r['armSwing'] = -22.*compression
        elif t < takeoff:
            u = (t-.60)/(takeoff-.60); r['root'][2] = hermite(-.25, 0., 0., speed, .25, u)
            r['pitch'] = 16.*(1-smooth(u)); r['arms'] = 'jump'; r['armSwing'] = mix(-22., 100., smooth(u))
        elif t < touchdown:
            elapsed = t-takeoff; u = elapsed/flight; height = speed*elapsed-.5*9.81*elapsed*elapsed
            r['root'][2] = height; r['arms'] = 'jump'; r['armSwing'] = mix(100., 40., smooth(u))
            for foot in r['feet'].values(): foot.update(up=height+.08*math.sin(math.pi*u)**2, planted=False, plant=None)
        elif t < 1.55:
            u = (t-touchdown)/.20; r['root'][2] = hermite(0., -.23, -speed, 0., .20, u)
            r['pitch'] = 18.*smooth(u); r['arms'] = 'jump'; r['armSwing'] = mix(40., 55., smooth(u))
        else:
            u = smooth((t-1.55)/.70); r['root'][2] = -.23*(1-u); r['pitch'] = 18.*(1-u)
            r['arms'] = 'jump'; r['armSwing'] = 55.*(1-u)
        r['root'][1] = -.10*r['root'][2] if r['root'][2] < 0 else 0.
    elif name == 'RiderRangeOfMotion':
        # Neutral, genuine 45-degree A, 90-degree T, overhead, reach, asymmetric
        # bend, deep crouch, head turn/nod, neutral. Holds separate transitions.
        keys = [(0., 'rest'), (.5, 'rest'), (1.3, 'A'), (1.8, 'A'), (2.6, 'T'), (3.1, 'T'),
                (4., 'overhead'), (4.5, 'overhead'), (5.3, 'reach'), (5.8, 'reach'),
                (6.6, 'asymmetric'), (7.1, 'asymmetric'), (8.1, 'crouch'), (8.8, 'crouch'),
                (9.7, 'head'), (10.4, 'head'), (11.5, 'rest'), (12., 'rest')]
        a, b = next(((a, b) for a, b in zip(keys, keys[1:]) if t <= b[0]), (keys[-2], keys[-1]))
        r['range'] = {'from': a[1], 'to': b[1], 'blend': smooth((t-a[0])/(b[0]-a[0]))}
    return r
