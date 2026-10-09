"""Parent-guarded actual67 native intake with actual68 exact-face proof.

--python author.py -- ACTUAL67_RECEIPT REVIEWED_RECEIPT_SHA NEW_NATIVE70_OUTPUT
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import intake
import surface

AUTHOR70=Path(__file__).resolve()
AUTHOR63=intake.BASE/'selected-boot-native63/author.py'
AUTHOR63_SHA='0f756829d1cb83d8f3be28b38dc82a0b9150e4754ef113d498095cd10798d934'


def adapted_source():
    intake.pin(AUTHOR63,AUTHOR63_SHA)
    previous=intake.load(AUTHOR63,'native70_author63')
    source,author57,author56,adapter46=previous.adapted_source()
    patches=[
        ("receipt['candidateAttempts'] == 2", "receipt['candidateAttempts'] == 5"),
        ('ADMITTED63_RECEIPT','ADMITTED70_RECEIPT'),('ADMITTED63_SHA','ADMITTED70_SHA'),
        ('Reviewed actual constructor62 receipt changed','Reviewed actual constructor67 receipt changed'),
        ("base = ROOT/'harness/out/rider-rebuild/selected-boot-closure62'", "base = ROOT/'harness/out/rider-rebuild/selected-boot-surface67'"),
        ("output_base63 = ROOT/'harness/out/rider-rebuild/selected-boot-native63'", "output_base63 = ROOT/'harness/out/rider-rebuild/selected-boot-native70'"),
        ("sha(CONSTRUCTOR62) == CONSTRUCTOR62_SHA", "sha(CONSTRUCTOR67) == CONSTRUCTOR67_SHA"),
        ("'recipeSHA256': sha(AUTHOR63), 'nativeAdmission63': ADMISSION63,",
         "'recipeSHA256': sha(AUTHOR70), 'nativeAdmission70': ADMISSION70, 'author63Ancestry': {'path': str(AUTHOR63.relative_to(ROOT)), 'sha256': AUTHOR63_SHA}, 'exactFaceBearing70': {'actualProof68': PROOF68_PIN, 'surfaceRecipeSHA256': sha(SURFACE70.__file__), 'policy': 'Only exact cyclic original-index/position/material faces use their own geometric ancestry at identical centroids, forward and reverse. New faces and all edge samples keep original global BVH nearest. All frozen thresholds/skin/contact gates remain.'},"),
        ("(out/'admission63.json').write_text(json.dumps(ADMISSION63, indent=2)", "(out/'admission70.json').write_text(json.dumps(ADMISSION70, indent=2)"),
        ("'Constructor62.protected-fan-original-position-topology'", "'Constructor67.joint-closure-original-position-topology'"),
        ("'UNACCEPTED_CONSTRUCTOR62_BEFORE_QUALIFICATION'", "'UNACCEPTED_CONSTRUCTOR67_BEFORE_QUALIFICATION'"),
        ("'UNACCEPTED-constructor62-before-transfer.blend'", "'UNACCEPTED-constructor67-before-transfer.blend'"),
        ("'REJECTED_NATIVE_CONSTRUCTOR62_UNACCEPTED'", "'REJECTED_NATIVE_CONSTRUCTOR67_UNACCEPTED'"),
    ]
    for old,new in patches:
        assert source.count(old)==1,('Native70 intake adapter drift',old);source=source.replace(old,new)
    return source,previous,author57,author56,adapter46


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==3
    admitted=intake.admit(args[0],args[1],args[2])
    source,previous,author57,author56,adapter46=adapted_source()
    orientation=intake.load(previous.ORIENTATION57,'native70_orientation57')
    proof57=orientation.verify_proof(previous.PROOF57,previous.PROOF57_SHA)
    namespace={'__file__':str(AUTHOR70),'__name__':'native70_frozen_qualification',
        'FROZEN':adapter46.FROZEN,'FROZEN_SHA':adapter46.FROZEN_SHA,
        'AUTHOR56_SHA':author57.AUTHOR56_SHA,'AUTHOR70':AUTHOR70,'AUTHOR63':AUTHOR63,'AUTHOR63_SHA':AUTHOR63_SHA,
        'AUTHOR57':previous.AUTHOR57,'AUTHOR57_SHA':previous.AUTHOR57_SHA,
        'AUTHOR46':author56.AUTHOR46,'AUTHOR46_SHA':author56.AUTHOR46_SHA,
        'KERNEL56':orientation.kernel,'ORIENTATION57':orientation,'PROOF57':proof57,
        'ADMISSION70':admitted,'ADMITTED70_RECEIPT':Path(args[0]).resolve(),'ADMITTED70_SHA':args[1],
        'CONSTRUCTOR67':intake.CONSTRUCTOR67,'CONSTRUCTOR67_SHA':intake.CONSTRUCTOR67_SHA,
        'SURFACE70':surface,'PROOF68_PIN':admitted['actualProof68']}
    old_argv=sys.argv[:];sys.argv=old_argv[:old_argv.index('--')+1]+[args[0],args[2]]
    try:
        exec(compile(source,str(AUTHOR63)+'[native70]','exec'),namespace)
        surface.install(namespace,admitted['actualProof68'])
        namespace['main']()
    finally:sys.argv=old_argv


if __name__=='__main__':main()
