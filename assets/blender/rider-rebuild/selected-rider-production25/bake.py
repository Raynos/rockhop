"""Selected-source cage bake into five production family atlases.

Parent guarded execution only: -- INPUT GEOMETRY_REPORT OUT. Saves original
selected materials into derivative albedo/normal/ORM, with bilateral atlas
regions. Full and LOD are baked independently from the same actual source.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[4]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1048576):h.update(block)
    return h.hexdigest()


def image(name,size,color):
    result=bpy.data.images.new(name,width=size,height=size,alpha=True,float_buffer=False,is_data=not color)
    result.colorspace_settings.name='sRGB' if color else 'Non-Color'
    return result


def receiver(family,size):
    mat=bpy.data.materials.new('SelectedProduction.'+family);mat.use_nodes=True
    mat.diffuse_color=(.5,.5,.5,1)
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    images={name:image(family+'.'+name,resolution,name=='albedo') for name,resolution in size.items()}
    nodes={}
    for name,im in images.items():
        n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;n.name='Production_'+name;nodes[name]=n
    mat.node_tree.links.new(nodes['albedo'].outputs['Color'],shader.inputs['Base Color'])
    normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');normal.uv_map='SelectedProductionAtlas'
    mat.node_tree.links.new(nodes['normal'].outputs['Color'],normal.inputs['Color'])
    mat.node_tree.links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    orm=mat.node_tree.nodes.new('ShaderNodeSeparateColor');orm.mode='RGB'
    mat.node_tree.links.new(nodes['orm'].outputs['Color'],orm.inputs['Color'])
    mat.node_tree.links.new(orm.outputs['Green'],shader.inputs['Roughness'])
    mat.node_tree.links.new(orm.outputs['Blue'],shader.inputs['Metallic'])
    return mat,images,nodes


def emission_source(source,socket_name):
    """Clone materials for this bake pass; original selected graph is immutable."""
    obj=source.copy();obj.data=source.data.copy();obj.name='BakeDonor.'+source.name
    bpy.context.scene.collection.objects.link(obj);obj.hide_render=False;obj.hide_set(False)
    for mod in list(obj.modifiers):obj.modifiers.remove(mod)
    if obj.data.shape_keys:
        for key in obj.data.shape_keys.key_blocks:key.value=0
    copies=[]
    for slot in obj.material_slots:
        mat=slot.material.copy();slot.material=mat;copies.append(mat)
        if socket_name is None:continue
        nt=mat.node_tree;principled=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
        output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
        emit=nt.nodes.new('ShaderNodeEmission');socket=principled.inputs[socket_name]
        if socket.is_linked:nt.links.new(socket.links[0].from_socket,emit.inputs['Color'])
        else:
            value=socket.default_value
            emit.inputs['Color'].default_value=tuple(value) if socket.type=='RGBA' else (float(value),)*3+(1.,)
        for link in list(output.inputs['Surface'].links):nt.links.remove(link)
        nt.links.new(emit.outputs['Emission'],output.inputs['Surface'])
    return obj,copies


def cage(target,distance):
    obj=target.copy();obj.data=target.data.copy();obj.name='BakeCage.'+target.name
    bpy.context.scene.collection.objects.link(obj)
    if obj.data.shape_keys:obj.shape_key_clear()
    for mod in list(obj.modifiers):obj.modifiers.remove(mod)
    for v in obj.data.vertices:v.co+=v.normal*distance
    obj.hide_render=True;obj.hide_set(True);return obj


def select(source,target):
    bpy.ops.object.select_all(action='DESELECT')
    for o in (source,target):o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=target


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args) in (3,4)
    input_path=Path(args[0]).resolve();geometry_path=Path(args[1]).resolve();out=Path(args[2]).resolve()
    config=json.loads(input_path.read_text());geometry=json.loads(geometry_path.read_text());level=geometry['level']
    requested=set(args[3].split(',')) if len(args)==4 else set(geometry['authoredFamilies'])
    assert requested and requested<=set(geometry['authoredFamilies'])
    config['objects']={n:r for n,r in config['objects'].items() if r['family'] in requested}
    assert sha(input_path)==geometry['inputSHA256'],'Source/bake manifest mismatch'
    native=ROOT/geometry['native']['path'];assert sha(native)==geometry['native']['sha256']
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-rider-production25') and not out.exists()
    out.mkdir(parents=True);bpy.ops.wm.open_mainfile(filepath=str(native))
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=config['textures']['bakeSamples'];scene.cycles.use_denoising=False
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=True
    scene.render.bake.margin=config['textures']['marginPixels'];scene.render.bake.normal_space='TANGENT'
    # Source and target share the original rest frame. Disable skin modifiers
    # only during rest baking, then restore the exact native armature setup.
    modifier_states=[]
    for obj in scene.objects:
        if obj.type=='MESH':
            for mod in obj.modifiers:
                if mod.type=='ARMATURE':
                    modifier_states.append((mod,mod.show_render,mod.show_viewport));mod.show_render=False;mod.show_viewport=False
    sizes={k:config['textures'][k] for k in ('albedo','normal','orm')}
    families={}
    for name,spec in config['objects'].items():families.setdefault(spec['family'],[]).append(name)
    report={'acceptedArt':False,'status':'UNACCEPTED_SELECTED_CAGE_BAKE','geometryReportSHA256':sha(geometry_path),
            'sourceMaster':geometry['sourceMaster'],'inputSHA256':sha(input_path),'recipeSHA256':sha(__file__),
            'level':level,'requestedFamilies':sorted(requested),'families':{},'movingReviewPassed':False,'actualRuntimeBudgetPassed':False}
    for family,names in families.items():
        print('BAKE selected '+family,flush=True)
        mat,images,nodes=receiver(family,sizes)
        scratch={k:image(family+'.'+k,sizes['orm'],False) for k in ('roughness','metallic')}
        for name in names:
            target=bpy.data.objects['Production.'+level+'.'+name]
            target.data.materials.clear();target.data.materials.append(mat)
            for face in target.data.polygons:face.material_index=0
        for pass_name,socket in [('albedo','Base Color'),('normal',None),('roughness','Roughness'),('metallic','Metallic')]:
            im=images[pass_name] if pass_name in images else scratch[pass_name]
            node=nodes[pass_name] if pass_name in nodes else mat.node_tree.nodes.new('ShaderNodeTexImage')
            node.image=im;mat.node_tree.nodes.active=node
            for n in mat.node_tree.nodes:n.select=n==node
            for index,name in enumerate(names):
                target=bpy.data.objects['Production.'+level+'.'+name];source=bpy.data.objects[name]
                donor,materials=emission_source(source,socket)
                shell=cage(target,config['objects'][name]['cageM']*config['levels'][level]['surfaceErrorMultiplier'])
                scene.render.bake.cage_object=shell;scene.render.bake.use_clear=index==0
                select(donor,target);bpy.context.view_layer.update()
                bpy.ops.object.bake(type='NORMAL' if pass_name=='normal' else 'EMIT')
                bpy.data.objects.remove(shell,do_unlink=True);bpy.data.objects.remove(donor,do_unlink=True)
                for material in materials:bpy.data.materials.remove(material)
            if pass_name not in nodes:mat.node_tree.nodes.remove(node)
        rough=np.empty(sizes['orm']**2*4,np.float32);metal=rough.copy()
        scratch['roughness'].pixels.foreach_get(rough);scratch['metallic'].pixels.foreach_get(metal)
        packed=np.ones((sizes['orm']**2,4),np.float32);packed[:,1]=rough.reshape(-1,4)[:,0];packed[:,2]=metal.reshape(-1,4)[:,0]
        images['orm'].pixels.foreach_set(packed.ravel());images['orm'].update()
        rows={}
        for kind,im in images.items():
            path=out/(family+'-'+kind+'.png');im.filepath_raw=str(path);im.file_format='PNG';im.save();im.pack()
            rows[kind]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'size':list(im.size),
                        'residentRGBA8MipMiB':im.size[0]*im.size[1]*4*4/3/1048576}
        report['families'][family]={'maps':rows,'actualSelectedSources':names,'cageMethod':'Actual corresponding derivative mesh topology, outward vertex-normal extrusion bounded per original selected family; original shader albedo/roughness/metallic and tangent surface normal baked selected-to-active.'}
        for im in scratch.values():bpy.data.images.remove(im)
        (out/'bake.json').write_text(json.dumps(report,indent=2)+'\n')
    for mod,render,viewport in modifier_states:mod.show_render=render;mod.show_viewport=viewport
    for name in config['objects']:
        bpy.data.objects[name].hide_render=True;bpy.data.objects[name].hide_set(True)
    estimate=sum(m['residentRGBA8MipMiB'] for f in report['families'].values() for m in f['maps'].values())
    assert estimate<=config['textures']['maximumResidentMiB']+1e-6
    report.update(activeRiderTextureMiB=estimate,bakeCompleted=True,
                  limits='Saved selected-source bake needs missing-ray/UV coverage inspection and matched moving high-resolution/compact review. Target/source surface bounds do not prove shading, dense contact, track budget, runtime timing, heap or physical device qualification.')
    native=out/('UNACCEPTED-selected-production-'+level+'-baked.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    report['native']={'path':str(native.relative_to(ROOT)),'sha256':sha(native)}
    (out/'bake.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'native':report['native'],'activeRiderTextureMiB':estimate}),flush=True)


if __name__=='__main__':main()
