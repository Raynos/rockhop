/** Unimported Coast-water candidate. One opaque plane, no new maps, no collider,
 * displacement, RNG or wall clock. Parent owns old-sea replacement and verdict.
 */
import * as THREE from 'three';
import type { CourseAssetDelivery } from '../courseAssets';
import { fogify } from '../../lighting/environment';
import { ZONE_TIME } from './zoneKit';

export interface CoastWaterOptions {
  /** Exact old sea footprint; pass the existing x0−260 / x1+260 bounds. */
  x0: number;
  x1: number;
  seaY: number;
  nearZ?: number;
  farZ?: number;
  groundAt: (x: number, z: number) => number;
  /** Library completion maps are borrowed; this delivery never disposes them. */
  completeMaterial?: (material: THREE.MeshStandardMaterial) => void;
  /** Same simulated-time object as zone water/gulls, never a private clock. */
  time?: { value: number };
  shallowColor?: THREE.ColorRepresentation;
  deepColor?: THREE.ColorRepresentation;
}
const VERTEX_DECLARATIONS = /* glsl */ `
attribute float coastDepth;
varying vec3 vCoastWaterWorld;
varying float vCoastWaterDepth;
`;
const FRAGMENT_DECLARATIONS = /* glsl */ `
uniform float uCoastWaterTime;
uniform vec3 uCoastWaterShallow;
uniform vec3 uCoastWaterDeep;
uniform float uCoastWaterNearZ;
varying vec3 vCoastWaterWorld;
varying float vCoastWaterDepth;
// Non-parallel, non-integral directions/wavelengths avoid rectangular tiles.
// Fine waves attenuate by pixel footprint so distant ripples cannot alias.
vec2 coastWaterSlope( vec2 p, float t ) {
  float bend = 0.31 * sin( dot( p, vec2( 0.037, -0.053 ) ) + t * 0.19 );
  float a = dot( p, vec2( 0.173, 0.071 ) ) - t * 0.53 + bend;
  float b = dot( p, vec2( -0.113, 0.197 ) ) - t * 0.39;
  float c = dot( p, vec2( 0.347, -0.229 ) ) + t * 0.64;
  vec2 slope = vec2( 0.925, 0.38 ) * ( 0.039 * cos( a ) );
  slope += vec2( -0.498, 0.867 ) * ( 0.030 * cos( b ) );
  slope += vec2( 0.835, -0.551 ) * ( 0.021 * cos( c ) );
  float d = dot( p, vec2( 2.713, 1.193 ) ) - t * 1.14 + 0.16 * sin( c );
  float e = dot( p, vec2( -3.337, 5.129 ) ) + t * 1.37 + 0.19 * sin( b );
  float filterD = 1.0 - smoothstep( 0.65, 2.7, fwidth( d ) );
  float filterE = 1.0 - smoothstep( 0.65, 2.7, fwidth( e ) );
  slope += vec2( 0.915, 0.403 ) * ( 0.015 * cos( d ) * filterD );
  slope += vec2( -0.545, 0.838 ) * ( 0.010 * cos( e ) * filterE );
  return slope;
}
`;
function inject(source: string, anchor: string, addition: string): string {
  if (!source.includes(anchor)) throw new Error(`Coast water shader anchor missing: ${anchor}`);
  return source.replace(anchor, anchor + '\n' + addition);
}

/** Material-only normal chop keeps sea/shore height exactly authoritative.
 * Standard dielectric Fresnel/environment remain; combined specular energy is
 * capped before fog/grade/tone mapping, avoiding a giant white sun reflection.
 */
export function buildCoastWater(options: CoastWaterOptions): CourseAssetDelivery {
  const nearZ=options.nearZ ?? -15,farZ=options.farZ ?? -205;
  if (![options.x0,options.x1,options.seaY,nearZ,farZ].every(Number.isFinite) || options.x1<=options.x0 || farZ>=nearZ)
    throw new Error('Invalid Coast water bounds');
  const time=options.time ?? ZONE_TIME;
  const position: number[]=[],uv: number[]=[],depth: number[]=[],indices: number[]=[];
  const segments=Math.max(1,Math.ceil((options.x1-options.x0)/32));
  const rows=[0,.006,.015,.035,.065,.11,.18,.32,.55,1];
  for(let row=0;row<rows.length;row++) {
    const z=nearZ+(farZ-nearZ)*rows[row]!;
    for(let column=0;column<=segments;column++) {
      const x=options.x0+(options.x1-options.x0)*column/segments;
      const bottom=options.groundAt(x,z);
      if(!Number.isFinite(bottom))throw new Error('Nonfinite Coast water ground');
      position.push(x,options.seaY,z);uv.push(x/8,z/8);
      depth.push(Math.max(0,Math.min(12,options.seaY-bottom)));
      if(row && column) {
        const i=row*(segments+1)+column;
        // Shore->deep rows run toward -Z; this winding keeps the normal +Y.
        indices.push(i-1,i-segments-2,i,i,i-segments-2,i-segments-1);
      }
    }
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(position,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  geometry.setAttribute('coastDepth',new THREE.Float32BufferAttribute(depth,1));
  geometry.setIndex(indices);geometry.computeVertexNormals();geometry.computeBoundingBox();geometry.computeBoundingSphere();
  const material=fogify(new THREE.MeshStandardMaterial({color:0xffffff,roughness:.30,metalness:0,envMapIntensity:.65,transparent:false,depthWrite:true}));
  material.name='coast-water candidate';
  try {
    options.completeMaterial?.(material);
    const previous=material.onBeforeCompile;
    const previousKey=material.customProgramCacheKey.bind(material);
    // Capture the inherited cache key before the callback changes (default Three
    // key reads onBeforeCompile). It must not recurse or vary with simulation time.
    const inheritedKey=previousKey();
    material.customProgramCacheKey=()=>`${inheritedKey}|coast-water-analytic-v1`;
    material.onBeforeCompile=(shader,renderer)=>{
      previous.call(material,shader,renderer);
      shader.uniforms.uCoastWaterTime=time;
      shader.uniforms.uCoastWaterShallow={value:new THREE.Color(options.shallowColor ?? 0x376864)};
      shader.uniforms.uCoastWaterDeep={value:new THREE.Color(options.deepColor ?? 0x1b4350)};
      shader.uniforms.uCoastWaterNearZ={value:nearZ};
      shader.vertexShader=inject(shader.vertexShader,'#include <common>',VERTEX_DECLARATIONS);
      shader.vertexShader=inject(shader.vertexShader,'#include <worldpos_vertex>',/* glsl */ `
        vCoastWaterWorld = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;
        vCoastWaterDepth = coastDepth;
      `);
      shader.fragmentShader=inject(shader.fragmentShader,'#include <common>',FRAGMENT_DECLARATIONS);
      shader.fragmentShader=inject(shader.fragmentShader,'#include <color_fragment>',/* glsl */ `
        float coastDepthMix = smoothstep( 0.15, 4.5, vCoastWaterDepth );
        float coastOffshore = smoothstep( 3.0, 55.0, uCoastWaterNearZ - vCoastWaterWorld.z );
        coastDepthMix = max( coastDepthMix, coastOffshore * 0.78 );
        vec3 coastBody = mix( uCoastWaterShallow, uCoastWaterDeep, coastDepthMix );
        // Subtle contact tint over sampled shallow bottom, never a white foam line.
        float coastContact = 1.0 - smoothstep( 0.04, 0.8, vCoastWaterDepth );
        coastBody = mix( coastBody, vec3( 0.064, 0.105, 0.081 ), coastContact * 0.23 );
        diffuseColor.rgb *= coastBody;
      `);
      shader.fragmentShader=inject(shader.fragmentShader,'#include <normal_fragment_maps>',/* glsl */ `
        vec2 coastSlope = coastWaterSlope( vCoastWaterWorld.xz, uCoastWaterTime );
        // Calm against the shore; no vertex displacement or water-height drift.
        coastSlope *= mix( 0.42, 1.0, smoothstep( 0.0, 1.1, vCoastWaterDepth ) );
        vec3 coastWorldNormal = normalize( vec3( -coastSlope.x, 1.0, -coastSlope.y ) );
        normal = normalize( mat3( viewMatrix ) * coastWorldNormal );
      `);
      shader.fragmentShader=inject(shader.fragmentShader,'#include <lights_fragment_end>',/* glsl */ `
        vec3 coastSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
        float coastSpecularLuma = dot( coastSpecular, vec3( 0.2126, 0.7152, 0.0722 ) );
        float coastSpecularLimit = min( 1.0, 0.11 / max( coastSpecularLuma, 0.00001 ) );
        reflectedLight.directSpecular *= coastSpecularLimit;
        reflectedLight.indirectSpecular *= coastSpecularLimit;
      `);
    };
    const root=new THREE.Group();root.name='coast-water-owned';
    const mesh=new THREE.Mesh(geometry,material);mesh.name='zone:sea';mesh.receiveShadow=true;mesh.castShadow=false;root.add(mesh);
    let disposed=false;
    return {root,textureBytes:0,dispose(){if(disposed)return;disposed=true;root.clear();geometry.dispose();material.dispose();}};
  } catch(error) {geometry.dispose();material.dispose();throw error;}
}
