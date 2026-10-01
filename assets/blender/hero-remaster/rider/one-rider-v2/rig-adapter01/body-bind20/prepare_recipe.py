"""Freeze the source-sheet clipper with separately declared inner surgery ROI."""
from pathlib import Path
base=Path(__file__).resolve().parent
source=base.parent/'body-bind13/build_orbits_clearance.py'
prefix=source.read_text().split('bridge=[]')[0]
prefix=prefix.replace("ROOT/'rig-adapter01/body-bind13/construction01/correction02'", "ROOT/'rig-adapter01/body-bind20/construction01'")
prefix=prefix.replace("REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind13/construction01/correction02'", "REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20/construction01'")
prefix=prefix.replace('WIDTH=.018;HEIGHT=.009', '''WIDTH=.018;HEIGHT=.009;INNER_WIDTH=.022;INNER_HEIGHT=.017
+selection=np.load(ROOT/'rig-adapter01/body-bind20/sheet-preflight01/sheet-selection.npz')
+assert np.array_equal(selection['sourcePositions'],v.astype('<f4')) and np.array_equal(selection['sourceTriangles'],tri)
+INWARD_SOURCE_FACES=set(map(int,selection['inwardSourceFaces']))
+EXTERIOR_SOURCE_FACES=set(map(int,selection['exteriorSourceFaces']))
+assert not (INWARD_SOURCE_FACES&EXTERIOR_SOURCE_FACES)
+sheet_report=json.loads((REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20/sheet-preflight01/sheet-preflight.json').read_text())
+assert sheet_report['status'].startswith('PASS') and not sheet_report['normalSignClassifierUsed']
+'''.replace('\n+','\n'))
prefix=prefix.replace('    match=None\n    if points[:,0].min()>.72:', '    match=None\n    inward=fi in INWARD_SOURCE_FACES\n    cut_width=INNER_WIDTH if inward else WIDTH\n    cut_height=INNER_HEIGHT if inward else HEIGHT\n    if points[:,0].min()>(.69 if inward else .72):')
prefix=prefix.replace('cy+HEIGHT and points[:,1].max()>=cy-HEIGHT and points[:,2].min()<=cz+WIDTH and points[:,2].max()>=cz-WIDTH:', 'cy+cut_height and points[:,1].max()>=cy-cut_height and points[:,2].min()<=cz+cut_width and points[:,2].max()>=cz-cut_width:')
prefix=prefix.replace('    points=v[face]\n    match=None','    points=v[face]\n    if fi not in INWARD_SOURCE_FACES and fi not in EXTERIOR_SOURCE_FACES:output.append(face.tolist());origins.append(fi);continue\n    match=None')
prefix=prefix.replace('np.sin(theta+np.pi/64)/HEIGHT,np.cos(theta+np.pi/64)/WIDTH','np.sin(theta+np.pi/64)/cut_height,np.cos(theta+np.pi/64)/cut_width')
(base/'build_graft.py').write_text(prefix+'\n'+(base/'graft_fragment.py').read_text())
