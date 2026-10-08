"""Behavior fixtures execute the exact wrapper lifetime helper without Blender."""
import gc
import json
import runpy
import weakref
from pathlib import Path
from types import SimpleNamespace

helper = runpy.run_path(str(Path(__file__).with_name('memory_lifetime.py')))

class Payload: pass
class Surgery:
    constructed = []
    def __init__(self, obj, source):
        self.obj = obj; self.source = source; self.scratch = Payload()
        self.old_count = 284571; self.old_face_count = 569142
        self.returned = ([1., 2., 3.], [0, 1, 2], {'ancestrySaved': True})
        self.finished = False; self.fail = False; self.constructed.append(obj.name)
    def finish(self, output):
        assert self.scratch and self.source
        if self.fail: raise RuntimeError('Intentional failed native finish')
        self.finished = True; return self.returned

module = SimpleNamespace(Surgery=Surgery); events = []
left = module.Surgery(SimpleNamespace(name='ActualSelectedGlove.L'), 'immutable source')
old_scratch = weakref.ref(left.scratch); returned = left.returned
helper['install'](module, events.append)
actual = left.finish('fixture-output')
assert actual is returned and actual[2]['ancestrySaved']
assert left.__dict__ == {'obj': left.obj} and old_scratch() is None
right = module.Surgery(SimpleNamespace(name='ActualSelectedGlove.R'), 'immutable source')
assert len(events) == 1 and events[0]['object'] == 'ActualSelectedGlove.L'
right.fail = True
try: right.finish('fixture-output')
except RuntimeError: pass
else: raise AssertionError('The native finish failure was swallowed')
assert right.scratch and right.source and right.fail and len(events) == 1
right.fail = False; right_result = right.returned
assert right.finish('fixture-output') is right_result
hoodie_obj = SimpleNamespace(name='RiderHoodie', geometry='exact native mesh')
hoodie = module.Surgery(hoodie_obj, 'large unused source')
assert isinstance(hoodie, helper['UnchangedHoodie']) and hoodie.obj is hoodie_obj
assert Surgery.constructed == ['ActualSelectedGlove.L', 'ActualSelectedGlove.R']
assert hoodie_obj.geometry == 'exact native mesh'
gc.collect()
print(json.dumps({'passed': True, 'actualNativeRun': False,
    'fixtures': ['Existing left instance releases scratch only after successful finish',
                 'Returned actual arrays/report survive scratch release before right construction',
                 'Failed finish preserves diagnostic scratch and propagates failure',
                 'Hoodie sentinel bypasses the original constructor and preserves native object'],
    'events': events}))
