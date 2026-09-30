export interface NodeSpec { name: string; mesh?: number; children?: number[]; matrix?: number[]; translation?: number[]; rotation?: number[]; scale?: number[] }
export interface AccessorSpec { bufferView: number; byteOffset?: number; componentType: number; count: number; type: string; normalized?: boolean; sparse?: unknown }
export interface ViewSpec { buffer: number; byteOffset?: number; byteLength: number; byteStride?: number; target?: number;
  extensions?: { EXT_meshopt_compression?: { buffer: number; byteOffset?: number; byteLength: number; byteStride: number; count: number; mode: string; filter?: string } } }
export interface ImageSpec { name: string; mimeType: string; bufferView: number }
export interface PrimitiveSpec { attributes: Record<string, number>; indices: number; material: number; mode?: number }
export interface MaterialSpec { name: string; [key: string]: unknown }
export interface GltfSpec { nodes: NodeSpec[]; meshes: { name: string; primitives: PrimitiveSpec[] }[];
  materials: MaterialSpec[]; bufferViews: ViewSpec[]; accessors: AccessorSpec[]; images: ImageSpec[];
  textures: { source: number; sampler?: number }[]; samplers: Record<string, unknown>[] }
export interface ComponentSpec { component: number; sourceVertexIndices: number[]; sourceTriangleOrdinals: number[] }
export interface DecodedSpec { sourceSHA256: string; logical: string; url: string; nodeIndex: number; sourceMeshIndex: number;
  primitiveIndex: number; material: MaterialSpec; localPositions: number[][]; fileFramePositions: number[][];
  indices: number[]; uv: number[][]; normals: number[][]; sourceNodeMatrix: number[]; images: ImageSpec[];
  bikeFrameOriginFileFrame: number[]; gripMarkersFileFrame: { side: string; sourceNode: number; fileFrame: number[] }[];
  textures: GltfSpec['textures']; samplers: GltfSpec['samplers'] }
