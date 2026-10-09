"""Exact private71 export, scoped79; no normal player writes."""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
BASE71 = {'path':'assets/blender/rider-rebuild/selected-distal-engine71/export.py',
          'sha256':'970408d3dd6394a3677256861f0b5abf5bfb9eb2a0c99d925cbf2542e088df8c'}


def transformed_source():
    source = c['checked'](BASE71).read_text()
    changes = {'selected-distal71':'selected-receiver79',
               'UNACCEPTED_DISTAL71_RAW_SAVED_REOPEN_EXPORT_PENDING':
                   'UNACCEPTED_RECEIVER79_RAW_SAVED_REOPEN_EXPORT_PENDING',
               "'nativeIdentityReassigned':False,":
                   "'nativeIdentityReassigned':False,'nativeIdentitySemantic':'Saved native row; receiver77 derivative identity is separate from selected donor ancestry',"}
    for old,new in changes.items():
        assert source.count(old) >= 1,old
        source = source.replace(old,new)
    return source


exec(compile(transformed_source(),str(c['checked'](BASE71)),'exec'),globals())
