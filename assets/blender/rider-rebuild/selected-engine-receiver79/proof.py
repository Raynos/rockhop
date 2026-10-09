"""Private71 proof reuse with actual compact77 authority and exact52/replay."""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
BASE71 = {'path':'assets/blender/rider-rebuild/selected-distal-engine71/proof.py',
          'sha256':'bccfd7ccc626a16e6662dd234982dbe9ce72da28c12b483ef8b7fad32b5fd2e4'}


def transformed_source():
    source = c['checked'](BASE71).read_text()
    start = source.index('    # Explicit actual69 admission,')
    end = source.index("    package = read(target['sourcePins']['gameplayPoses'])",start)
    source = source[:start]+"    runpy.run_path(str(HERE/'component.py'))['donor_gate'](sleeve,read(sleeve['input']))\n"+source[end:]
    start = source.index('PROXIMAL69 = ')
    end = source.index('\nKIND = ',start)
    source = source[:start]+source[end+1:]
    changes = {
        'selected-distal-engine71':'selected-engine-receiver79',
        'selected-distal-wardrobe51/merge51.py':'selected-engine-receiver79/merge.py',
        'qualified-distal-topology51-native52-fields':'qualified-selected-receiver77-native52-fields',
        'UNACCEPTED_DISTAL71_DECODED_NATIVE_TRANSPORT_GAMEPLAY_PENDING':
            'UNACCEPTED_RECEIVER79_DECODED_NATIVE_TRANSPORT_GAMEPLAY_PENDING',
        'UNACCEPTED_MERGED51_ORIGINAL08_MATRIX_REPLAY_PASS_ART_PENDING':
            'UNACCEPTED_MERGED79_ORIGINAL08_MATRIX_REPLAY_PASS_ART_PENDING',
        'SINGLE_DISTAL51_MERGE_NATIVE_WITNESS_ONLY':'SINGLE_RECEIVER79_MERGE_NATIVE_WITNESS_ONLY',
        'THREE_SEPARATE_REOPENED_COMPONENT_TARGET_MERGED_NATIVES':
            'SOURCE_REOPEN_TARGET_AT_MERGE_ASSEMBLY_REOPEN',
        'UNACCEPTED_DISTAL_TOPOLOGY_TRANSPORT':'UNACCEPTED_RECEIVER_TOPOLOGY_TRANSPORT',
        "'nativeIdentityReassigned':False,":
            "'nativeIdentityReassigned':False,'nativeIdentitySemantic':'Saved native row; receiver77 derivative identity is separate from selected donor ancestry',",
        "'runtimeAnimationChannels':0,":
            "'runtimeAnimationChannels':0,'assemblyEligibility':merge_config['eligibility'],"}
    for old,new in changes.items():
        assert source.count(old) >= 1,old
        source = source.replace(old,new)
    return source


# Export71 imports this ordinary module. Its immutable functions resolve this
# owned __file__/scope while all native/decoded transport implementation stays71.
exec(compile(transformed_source(),str(c['checked'](BASE71)),'exec'),globals())
