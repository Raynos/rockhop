"""Pixel-only layout and byte verification of completed neutral anatomy evidence."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/Users/raynos/projects/games/rockhop')
BASE=Path('one-rider-v2/glove-cleanup/mpfb-trial2')
OUT=ROOT/'docs/evidence/hero-remaster'/BASE
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
REPORT=OUT/'neutral-anatomy/display-complete/report.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(REPORT.read_text())
assert all(m['vertices']==1668 and m['faces']==1656 and m['topology']=={'boundaryEdges':22,'nonmanifoldBeyondWrist':0} and m['nonadjacentBVHOverlapPairs']==0 for m in d['metrics'])
for p,h in d['sourceNPZs'].items():assert sha(Path(p))==h
for row in d['views']:assert sha(Path(row['file']))==row['sha256']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
board=Image.new('RGB',(1440,1080),(24,27,31));draw=ImageDraw.Draw(board)
draw.text((18,12),'NEUTRAL MODEL / natural source anatomy, parent judgment pending',font=font,fill='white')
for r,side in enumerate(['L','R']):
    for c,view in enumerate(['front','profile','back']):
        row=next(v for v in d['views'] if v['side']==side and v['view']==view)
        im=Image.open(row['file']).convert('RGB');im.thumbnail((480,480),Image.Resampling.LANCZOS)
        board.paste(im,(c*480,72+r*500));draw.text((c*480+12,46+r*500),f'{side} / {view}',font=small,fill='white')
draw.text((18,1053),'Complete wrist-cut n-gons retained; intentional open wrist / no gripping-pose or texture pass',font=small,fill='white')
path=OUT/'neutral-anatomy/display-complete/neutral-anatomy-board.jpg';board.save(path,quality=95,subsampling=0)
(OUT/'neutral-anatomy/display-complete/verification.json').write_text(json.dumps({'status':'Verified neutral evidence only; parent model judgment pending; separate fixedcurl failed','sourceNPZHashesMatch':True,'verifiedFrames':6,'board':{'path':str(path),'sha256':sha(path)},'completeFacesPerHand':1656,'expectedOpenWristEdgesPerHand':22,'neutralNonadjacentOverlapCandidatePairsPerHand':0,'scope':'Subsurf1 neutral display; no collision/contact or final deformation pass'},indent=2)+'\n')
source=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
raw=source.with_name('raw-shape.npz')
fresh=RUN/'fresh-anatomical-source.blend'
assert sha(source)=='f657aa963f2e582a9f70291b3dbd160dafd6e944419d48b21b0425521d4cd63a'
assert sha(raw)=='4a10d00eb42b08910e015efe117f6b28f07be2c7d76e311613a38ac5303d0247'
assert sha(fresh)=='3c255ac91f6983c51cc4307baf8c305dcd9f3035c48c3fc1711594666e81bce8'
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='final-verdict.json']
recipes=list((ROOT/'assets/blender/hero-remaster/rider/one-rider-v2/glove-cleanup').glob('*mpfb*.py'))
recipes+=[ROOT/'assets/blender/hero-remaster/rider/one-rider-v2/glove-cleanup'/p for p in ['render_neutral_cages.py','render_neutral_complete.py','compose_neutral_evidence.py']]
masters=[fresh,RUN/'body-gloves.blend',RUN/'body-gloves.glb',RUN/'mirror-corrected/body-gloves.blend',RUN/'mirror-corrected/body-gloves.glb',RUN/'mirror-corrected/temporary-wrist-diagnostic.blend',RUN/'neutral-anatomy/neutral-anatomical-hands.blend',RUN/'neutral-anatomy/display-complete/neutral-anatomical-cages.blend']
(OUT/'final-verdict.json').write_text(json.dumps({'status':'MODEL neutral evidence pending parent; POSE fixed-angle curl failed and stopped; no bake/promotion','sourceHashesUntouched':{str(p):sha(p) for p in [source,raw,fresh]},'anatomy':{'freshCC0MPFB':True,'completeNeutralCagePerHand':{'vertices':1668,'faces':1656,'intentionalWristBoundaryEdges':22,'nonmanifoldBeyondWrist':0},'nativeWeightsPreserved':True,'neutralDisplayNonadjacentOverlapCandidates':0,'parentAppearanceAccepted':False},'posing':{'initialNonadjacentOverlapTouchTrianglePairs':341,'mirroredCorrectionNonadjacentOverlapTouchTrianglePairs':66,'fixedCurlTechniqueStopped':True,'contactPass':False,'temporaryMotionOnly':True},'failedSetupsAndEvidenceCorrections':['addon registration corrected once','native mirrored signed axes corrected once; fixedcurl stopped after both setupcorrections','initial diagnostic clipped fingertips/missing distal temporaryweights corrected in separate inspector','neutral inheritedshape-key blankdisplay preserved','neutral tri/quad-only serialization omitted2wristcutngons; completeexport verified all1656faces'], 'sourceProtection':{'positionsAndUVFingerprintsVerified':True,'protects':'hood/cuffs/torso/feet/legs; distalconnectedglovecomponent only removed','globalNormalsHashPreserved':False},'reference':'actual-grip-reference.json contains consumedfullrubber surfacefit;22mm hypothesis superseded','proposedSpecificAlternative':'After parent decision, measured-grip nativechain solving with selfcollision; reviewed gripmorph and19bone adapter. Do not repeat blindfixedcurl.','files':{str(p):sha(p) for p in files+recipes+masters},'noFinalCharacterRigOrRuntime':True},indent=2)+'\n')
print('NEUTRAL_BOARD_AND_FINAL_MANIFEST_VERIFIED')
