"""Release only registered temporary mesh copies after their object is removed."""


class OwnedMeshes:
    def __init__(self, objects, meshes):
        self.objects = objects
        self.meshes = meshes
        self.pending = {}
        self.created = []
        self.released = []

    def register(self, obj, original, role):
        pointer = obj.as_pointer(); mesh = obj.data
        assert pointer != original.as_pointer() and mesh.as_pointer() != original.data.as_pointer()
        assert pointer not in self.pending
        row = {'object': obj.name, 'mesh': mesh.name, 'source': original.name,
               'sourceMesh': original.data.name, 'role': role}
        self.pending[pointer] = (mesh, row)
        self.created.append(dict(row))

    def remove(self, obj, *args, **kwargs):
        pointer = obj.as_pointer()
        owned = self.pending.get(pointer)
        if owned:
            assert obj.data.as_pointer() == owned[0].as_pointer(), 'Owned object changed mesh'
        self.objects().remove(obj, *args, **kwargs)
        if owned:
            mesh, row = owned
            # Never force-unlink live data or clear a fake user to make it pass.
            assert mesh.users == 0, ('Temporary bake mesh still has a user', row, mesh.users)
            self.meshes().remove(mesh, do_unlink=False)
            del self.pending[pointer]
            self.released.append({**row, 'usersBeforeRemoval': 0})


class Proxy:
    """Module-local delegation, with no writes to bpy or its dynamic operators."""
    def __init__(self, target, **overrides):
        self.target = target
        self.overrides = overrides

    def __getattr__(self, name):
        return self.overrides[name] if name in self.overrides else getattr(self.target, name)

    def __getitem__(self, key):
        return self.target[key]


class BpyProxy:
    def __init__(self, module, remove):
        self.module = module
        self.remove = remove

    def __getattr__(self, name):
        if name == 'data':
            # open_mainfile replaces Main. Never cache its pre-open collections.
            data = self.module.data
            return Proxy(data, objects=Proxy(data.objects, remove=self.remove))
        return getattr(self.module, name)
