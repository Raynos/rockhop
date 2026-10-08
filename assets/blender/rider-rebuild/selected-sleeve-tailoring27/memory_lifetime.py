"""Drop finished construction scratch and skip unused hoodie-only scratch.

This helper changes lifetime only. The native finish implementation, its
returned geometry/report, actual Blender datablocks and every field are intact.
"""
import gc


class UnchangedHoodie:
    __slots__ = ('obj',)
    def __init__(self, obj): self.obj = obj


def install(base_module, record):
    original_class = base_module.Surgery
    original_finish = original_class.finish

    def finish_and_release(self, *args, **kwargs):
        # If finish raises, leave every diagnostic field intact. A caller may
        # only drop scratch after mesh, source ancestry and returned arrays exist.
        result = original_finish(self, *args, **kwargs)
        assert self.obj.name in {'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}
        assert isinstance(result, tuple) and len(result) == 3
        obj = self.obj
        row = {'operation': 'RELEASE_COMPLETED_GLOVE_PYTHON_SCRATCH', 'object': obj.name,
               'sourceVertices': self.old_count, 'sourceFaces': self.old_face_count,
               'releasedMemberNames': sorted(k for k in self.__dict__ if k != 'obj'),
               'returnedArraysAndReportPreserved': True, 'nativeDatablocksRemoved': False}
        self.__dict__.clear(); self.obj = obj
        gc.collect(); record(row)
        return result

    original_class.finish = finish_and_release

    def constructor(obj, source):
        if obj.name == 'RiderHoodie':
            record({'operation': 'SKIP_UNUSED_HOODIE_SURGERY', 'object': obj.name,
                    'nativeObjectUnchanged': True, 'scratchArraysAllocated': False})
            return UnchangedHoodie(obj)
        assert obj.name in {'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}
        return original_class(obj, source)

    # Existing left-glove instances pick up the patched class method. The next
    # right constructor runs after its predecessor's scratch has been released.
    base_module.Surgery = constructor
