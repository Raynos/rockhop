import * as THREE from 'three';
import { describe, expect, it, vi } from 'vitest';
import { fogUniforms, gradeUniforms } from '../../lighting/environment';
import { buildCoastWater } from './coastWater';
import { ZONE_TIME } from './zoneKit';
const options={x0:-260,x1:760,seaY:-2.82,groundAt:(x:number,z:number)=>-3.4-(Math.abs(z)-15)*.025+Math.sin(x*.07)*.1};
function compile(material: THREE.MeshStandardMaterial) {
  const shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  material.onBeforeCompile(shader as THREE.WebGLProgramParametersWithUniforms,{} as THREE.WebGLRenderer);
  return shader;
}
describe('Coast water shader/ownership candidate',()=>{
  it('preserves exact sea footprint/height with one tiny opaque draw and sampled depth',()=>{
    const delivery=buildCoastWater(options);expect(delivery.root.children).toHaveLength(1);
    const mesh=delivery.root.children[0] as THREE.Mesh;const g=mesh.geometry,mat=mesh.material as THREE.MeshStandardMaterial;
    expect(g.boundingBox!.min.toArray()).toEqual([-260,expect.closeTo(-2.82,5),-205]);
    expect(g.boundingBox!.max.toArray()).toEqual([760,expect.closeTo(-2.82,5),-15]);
    const p=g.getAttribute('position'),d=g.getAttribute('coastDepth'),n=g.getAttribute('normal');
    expect(g.index!.count/3).toBe(576);expect(mat.transparent).toBe(false);expect(mat.depthWrite).toBe(true);
    for(let i=0;i<p.count;i++){
      expect([p.getX(i),p.getY(i),p.getZ(i),d.getX(i)].every(Number.isFinite)).toBe(true);
      expect(p.getY(i)).toBeCloseTo(-2.82,5);expect(n.getY(i)).toBeCloseTo(1,5);
      expect(d.getX(i)).toBeCloseTo(options.seaY-options.groundAt(p.getX(i),p.getZ(i)),5);
    }
    expect(delivery.textureBytes).toBe(0);delivery.dispose();
  });
  it('chains library compile callback while retaining fog/grade and one shared simulation time',()=>{
    const extra=vi.fn();const delivery=buildCoastWater({...options,completeMaterial(m){const prev=m.onBeforeCompile;m.onBeforeCompile=(s,r)=>{prev.call(m,s,r);extra();s.uniforms.uLibraryProbe={value:1};};}});
    const mat=(delivery.root.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;
    const shader=compile(mat);expect(extra).toHaveBeenCalledOnce();
    expect(shader.uniforms).toMatchObject({uFogFloor:fogUniforms.uFogFloor,uGradeA:gradeUniforms.uGradeA,uLibraryProbe:{value:1},uCoastWaterTime:ZONE_TIME});
    expect(shader.vertexShader).toContain('vCoastWaterWorld = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;');
    expect(shader.vertexShader).not.toContain('transformed.y +=');
    expect(shader.fragmentShader).toContain('fwidth( d )');expect(shader.fragmentShader).toContain('fwidth( e )');
    expect(shader.fragmentShader).toContain('normal = normalize( mat3( viewMatrix ) * coastWorldNormal )');
    expect(shader.fragmentShader).toContain('0.11 / max( coastSpecularLuma');
    expect(shader.fragmentShader.indexOf('coastSpecularLimit')).toBeLessThan(shader.fragmentShader.indexOf('#include <tonemapping_fragment>'));
    expect(shader.fragmentShader.indexOf('coastBody')).toBeLessThan(shader.fragmentShader.indexOf('#include <normal_fragment_maps>'));
    delivery.dispose();
  });
  it('does not recompile or allocate new clocks when simulated time changes',()=>{
    const time={value:0};const delivery=buildCoastWater({...options,time});
    const mat=(delivery.root.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;
    const shader=compile(mat);const key=mat.customProgramCacheKey(),version=mat.version;
    time.value=7.25;expect((shader.uniforms as Record<string,{value:unknown}>).uCoastWaterTime).toBe(time);
    expect(mat.customProgramCacheKey()).toBe(key);expect(mat.version).toBe(version);
    expect(key).toContain('coast-water-analytic-v1');delivery.dispose();
  });
  it('owns only geometry/material and never disposes library maps',()=>{
    const neutral=new THREE.DataTexture();const mapDispose=vi.spyOn(neutral,'dispose');
    const delivery=buildCoastWater({...options,completeMaterial(m){m.map=neutral;m.normalMap=neutral;m.roughnessMap=neutral;m.metalnessMap=neutral;m.aoMap=neutral;m.emissiveMap=neutral;}});
    const mesh=delivery.root.children[0] as THREE.Mesh;const gd=vi.spyOn(mesh.geometry,'dispose'),md=vi.spyOn(mesh.material as THREE.Material,'dispose');
    delivery.dispose();delivery.dispose();expect(gd).toHaveBeenCalledOnce();expect(md).toHaveBeenCalledOnce();expect(mapDispose).not.toHaveBeenCalled();
  });
  it('fails explicitly if Three shader anchors change, preserving the inherited hook',()=>{
    const delivery=buildCoastWater(options);const mat=(delivery.root.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;
    expect(()=>mat.onBeforeCompile({uniforms:{},vertexShader:'void main(){}',fragmentShader:'void main(){}'} as THREE.WebGLProgramParametersWithUniforms,{} as THREE.WebGLRenderer)).toThrow('anchor missing');delivery.dispose();
  });
  it('rejects invalid footprint or ground and cleans a completion failure',()=>{
    expect(()=>buildCoastWater({...options,x1:-260})).toThrow('bounds');
    expect(()=>buildCoastWater({...options,nearZ:-205})).toThrow('bounds');
    expect(()=>buildCoastWater({...options,groundAt:()=>NaN})).toThrow('Nonfinite');
    const gd=vi.spyOn(THREE.BufferGeometry.prototype,'dispose'),md=vi.spyOn(THREE.Material.prototype,'dispose');
    expect(()=>buildCoastWater({...options,completeMaterial(){throw new Error('completion failed');}})).toThrow('completion failed');expect(gd).toHaveBeenCalledOnce();expect(md).toHaveBeenCalledOnce();vi.restoreAllMocks();
  });
});
