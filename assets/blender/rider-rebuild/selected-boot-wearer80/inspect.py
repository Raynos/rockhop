"""Read exact own-side boot/foot sections; no deformation or native execution."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT/'harness/out/rider-rebuild/selected-boot-family75/cpu01/source.json'
SOURCE_SHA = '22236d6c2f4a874a57c7f945a4e1b186d6d400dab04c006f3658f96afc8e7ed1'
BODY = ROOT/'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz'
BODY_SHA = 'e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2'
PRIOR = ROOT/'docs/evidence/rider-rebuild/selected-boot-family75/preflight.json'
PRIOR_SHA = 'fad6e5a0945c000085fde19babeeb1c71ddd4d1e51054328b5da8320080e8a09'


def pin(path, expected=None):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if expected is not None:
        assert digest == expected, str(path)
    return {'path': str(Path(path).relative_to(ROOT)), 'sha256': digest}


def intake():
    pin(SOURCE, SOURCE_SHA)
    pin(BODY, BODY_SHA)
    pin(PRIOR, PRIOR_SHA)
    source = json.loads(SOURCE.read_text())
    package = source['arrays']
    path = ROOT/package['path']
    pin(path, package['sha256'])
    raw = path.read_bytes()
    arrays = {key: np.frombuffer(raw, dtype=row['dtype'],
              count=row['byteLength']//np.dtype(row['dtype']).itemsize,
              offset=row['byteOffset']).reshape(row['shape'])
              for key, row in package['layout'].items()}
    return source, arrays, dict(np.load(BODY)), json.loads(PRIOR.read_text())


def frame(body, side):
    names = body['jointNames'].tolist()
    ankle = body['jointHeads'][names.index('DEF-foot.'+side)].astype(float)
    toe = body['jointHeads'][names.index('DEF-toe.'+side)].astype(float)
    forward = toe-ankle
    forward[2] = 0
    forward /= np.linalg.norm(forward)
    # Semantic transverse positive = medial on BOTH sides. Explicit reflection
    # here is a diagnostic coordinate choice, never a fitting assumption.
    medial = np.cross([0., 0., 1.], forward)*(1 if side == 'L' else -1)
    if medial[0]*(1 if side == 'R' else -1) < 0:
        medial *= -1
    basis = np.column_stack([forward, medial, [0., 0., 1.]])
    origin = ankle.copy()
    origin[2] = 0
    return origin, basis


def section(points, faces, axis, value):
    tri = points[faces]
    low, high = tri[:, :, axis].min(1), tri[:, :, axis].max(1)
    tri = tri[(low < value) & (high > value)]
    segments = []
    for t in tri:
        hits = []
        for a, b in [(0, 1), (1, 2), (2, 0)]:
            aa, bb = t[a, axis]-value, t[b, axis]-value
            if aa*bb < 0:
                hits.append(t[a]+aa/(aa-bb)*(t[b]-t[a]))
        if len(hits) == 2:
            segments.append(hits)
    return np.array(segments)


def main():
    from PIL import Image, ImageDraw, ImageFont
    assert len(sys.argv) == 2
    out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-boot-wearer80')
    assert not out.exists()
    out.mkdir(parents=True)
    source, arrays, body, prior = intake()
    report = {'status': 'OWN_SIDE_SECTION_DIAGNOSTIC_UNACCEPTED', 'acceptedArt': False,
              'source': pin(SOURCE, SOURCE_SHA), 'body': pin(BODY, BODY_SHA),
              'prior': pin(PRIOR, PRIOR_SHA), 'recipe': pin(Path(__file__)), 'sides': {}}
    for side in ('L', 'R'):
        origin, basis = frame(body, side)
        boot = (arrays[side+'Positions'].astype(float)-origin)@basis
        bf = arrays[side+'Triangles']
        native = (body['vertices'].astype(float)-origin)@basis
        nf = body['faces']
        # The 180 mm height limit is a section diagnostic, not foot qualification.
        # Own side uses the anatomical world-X midline without a transverse crop.
        own_side = body['vertices'][nf, 0]*np.sign(origin[0]) > 0
        use = np.all((native[nf, 2] < .18) & own_side, axis=1)
        nf = nf[use]
        outside = np.array(prior['sides'][side]['actualNative02FootEnclosure']['outsideOriginalBodyVertexIds'])
        q = native[outside]
        sections = []
        diagram = Image.new('RGB', (2000, 1400), 'white')
        draw = ImageDraw.Draw(diagram)
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 17)
        except OSError:
            font = ImageFont.load_default()
        draw.text((20, 12), 'GEOMETRY DIAGNOSTIC ONLY - selected boot navy / actual wearer orange / prior outside red',
                  fill='#172638', font=font)
        stations = ([(2, z) for z in (.015, .035, .060, .090)] +
                    [(0, u) for u in (-.03, .015, .080, .150, .195)] +
                    [(1, w) for w in (-.04, .02, .045)])
        for panel, (axis, value) in enumerate(stations):
            xy = [i for i in range(3) if i != axis]
            bs = section(boot, bf, axis, value)
            ns = section(native, nf, axis, value)
            nearby = q[np.abs(q[:, axis]-value) < .004]
            cloud = [s[:, :, xy].reshape(-1, 2)*1000 for s in (bs, ns) if len(s)]
            if len(nearby):
                cloud.append(nearby[:, xy]*1000)
            points = np.concatenate(cloud) if cloud else np.array([[0., 0.], [1., 1.]])
            low, high = points.min(0), points.max(0)
            center = (low+high)/2
            span = np.maximum(high-low, 1.)*1.12+4.
            x0, y0 = (panel % 4)*500, 48+(panel//4)*448
            left, top, width, height = x0+58, y0+52, 414, 334
            scale = min(width/span[0], height/span[1])
            lower = center-np.array([width, height])/(2*scale)
            upper = center+np.array([width, height])/(2*scale)

            def pixel(point):
                return (float(left+(point[0]-lower[0])*scale),
                        float(top+height-(point[1]-lower[1])*scale))

            step = 20. if max(upper-lower) > 150. else 10.
            for dimension in (0, 1):
                for tick in np.arange(np.ceil(lower[dimension]/step)*step, upper[dimension], step):
                    a, b = lower.copy(), upper.copy()
                    a[dimension] = b[dimension] = tick
                    pa, pb = pixel(a), pixel(b)
                    draw.line([pa, pb], fill='#e4e7eb', width=1)
                    label = f'{tick:.0f}'
                    label_xy = (pa[0]-10, top+height+5) if dimension == 0 else (left-44, pa[1]-9)
                    draw.text(label_xy, label, fill='#657180', font=font)
            draw.rectangle((left, top, left+width, top+height), outline='#aab2bc')
            for lines, color, line_width in [(bs, '#172638', 1), (ns, '#d56435', 2)]:
                for segment in lines:
                    draw.line([pixel(point[xy]*1000) for point in segment], fill=color, width=line_width)
            for point in nearby:
                px, py = pixel(point[xy]*1000)
                draw.ellipse((px-2, py-2, px+2, py+2), fill='#d51e34')
            names = ['forward', 'medial', 'height']
            draw.text((left, y0), f'{side}: {names[axis]} {value*1000:.0f} mm', fill='#172638', font=font)
            draw.text((left, y0+24), names[xy[1]]+' mm (vertical)', fill='#657180', font=font)
            draw.text((left+width/2-45, top+height+29), names[xy[0]]+' mm', fill='#657180', font=font)
            sections.append({'axis': axis, 'valueM': value, 'boot': bs.tolist(), 'body': ns.tolist()})
        diagram.save(out/(side+'-sections.png'))
        report['sides'][side] = {'origin': origin.tolist(), 'basisColumns': basis.T.tolist(),
            'sourceBoundsLocalM': [boot.min(0).tolist(), boot.max(0).tolist()],
            'outsideSamples': [{'originalBodyId': int(i), 'localM': p.tolist()} for i, p in zip(outside, q)],
            'sectionImage': pin(out/(side+'-sections.png'))}
        (out/(side+'-sections.json')).write_text(json.dumps(sections))
    report['limits'] = ('Actual own-side sections diagnose shape only; parity outside can include entry/cavity. '
                        'No shape edit, field edit, native, bake, moving art or acceptance.')
    (out/'inspection.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'output': str(out)}))


if __name__ == '__main__':
    main()
