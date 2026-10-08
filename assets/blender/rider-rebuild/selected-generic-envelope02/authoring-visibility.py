"""Transient dense-mesh suspension; no geometry, modifiers or curves changed.

Blender's hide_viewport marks an object disabled in viewports; hide_set alone
is per-layer viewing state. The viewport depsgraph optimizes enabled components
and propagates dependency visibility, so this makes no timing guarantee:
https://github.com/blender/blender/blob/main/source/blender/makesrna/intern/rna_object.cc
https://github.com/blender/blender/blob/main/source/blender/depsgraph/intern/eval/deg_eval_visibility.cc
"""
from contextlib import contextmanager
import bpy


def snapshot(scene):
    return {obj.name: {'hideViewport':obj.hide_viewport,'hideRender':obj.hide_render,
        'hideSet':{layer.name:obj.hide_get(view_layer=layer) for layer in scene.view_layers if obj.name in layer.objects}}
        for obj in scene.objects}


class DenseViewportSuspend:
    def __init__(self, scene, meshes, rig):
        self.scene=scene;self.meshes=list(meshes);self.names={obj.name for obj in self.meshes}
        assert len(self.names)==7 and all(obj.type=='MESH' for obj in self.meshes)
        assert not rig.hide_viewport and rig.visible_get(view_layer=bpy.context.view_layer),'Rig must remain viewport evaluated'
        assert bpy.context.evaluated_depsgraph_get().mode=='VIEWPORT'
        self.before=snapshot(scene);self.restored=False
        for obj in self.meshes:self._hidden(obj,True)
        bpy.context.view_layer.update();self.assert_suspended()

    def _hidden(self,obj,hidden):
        obj.hide_viewport=hidden
        for layer in self.scene.view_layers:
            if obj.name in layer.objects:obj.hide_set(hidden,view_layer=layer)

    def assert_suspended(self):
        current=snapshot(self.scene)
        assert set(current)==set(self.before)
        for name,row in current.items():
            if name not in self.names:assert row==self.before[name],('Unrelated viewport state changed',name)
            else:
                assert row['hideViewport'] and all(row['hideSet'].values())
                assert row['hideRender']==self.before[name]['hideRender']

    @contextmanager
    def visible_for_measurement(self,objects):
        objects=list(objects);assert all(obj.name in self.names for obj in objects)
        self.assert_suspended()
        try:
            for obj in objects:self._hidden(obj,False)
            bpy.context.view_layer.update()
            assert all(obj.visible_get(view_layer=bpy.context.view_layer) for obj in objects)
            yield bpy.context.evaluated_depsgraph_get()
        finally:
            for obj in objects:self._hidden(obj,True)
            bpy.context.view_layer.update();self.assert_suspended()

    def restore(self):
        self.assert_suspended()
        for obj in self.meshes:
            row=self.before[obj.name];obj.hide_viewport=row['hideViewport']
            for name,hidden in row['hideSet'].items():obj.hide_set(hidden,view_layer=self.scene.view_layers[name])
        bpy.context.view_layer.update();after=snapshot(self.scene)
        assert after==self.before,'All scene viewport hide_set/hide_viewport and hide_render states must restore exactly'
        self.restored=True
        return {'restoredExact':True,'suspendedMeshes':sorted(self.names),'before':self.before,'after':after,
                'evaluationMode':'VIEWPORT','timingImprovementMeasured':False}
