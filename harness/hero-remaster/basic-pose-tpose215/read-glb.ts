import { createHash } from 'node:crypto';
import { Matrix4, Quaternion, Vector3 } from 'three';
import { checkedMatrix, prepareBinding } from './fixture';
import type { Binding, Role } from './fixture';

export interface BindingManifest {
  schemaVersion: 1; sourceSHA256: string; skinIndex: number; sceneIndex: number;
  sceneToGameWorldColumnMajor: number[];
  joints: { role: Role; nodeIndex: number; name: string; anatomyLocalQuaternion: number[] }[];
}
interface GltfNode { name?: string; children?: number[]; matrix?: number[]; translation?: number[];
  rotation?: number[]; scale?: number[]; skin?: number; mesh?: number }
interface GltfAccessor { bufferView?: number; byteOffset?: number; componentType: number; count: number;
  type: string; sparse?: unknown }
interface Gltf {
  asset: { version: string }; nodes: GltfNode[];
  skins: { joints: number[]; inverseBindMatrices?: number }[];
  scenes: { nodes: number[] }[]; buffers: { byteLength: number; uri?: string }[];
  accessors: GltfAccessor[];
  bufferViews: { buffer: number; byteOffset?: number; byteLength: number; byteStride?: number; extensions?: unknown }[];
  meshes: { primitives: { attributes: { POSITION?: number }; extensions?: unknown }[] }[];
}
/** CPU reader; no loader normalization, texture decode, GPU or source edits. */
export function readGlbBinding(bytes: Uint8Array, declaration: BindingManifest): Binding {
  const sourceSHA256 = createHash('sha256').update(bytes).digest('hex');
  if (declaration.schemaVersion !== 1 || declaration.sourceSHA256 !== sourceSHA256)
    throw new Error('Consumed GLB SHA differs from explicit binding declaration');
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (bytes.byteLength < 20 || view.getUint32(0, true) !== 0x46546c67 || view.getUint32(4, true) !== 2
    || view.getUint32(8, true) !== bytes.byteLength) throw new Error('Not exact GLB2 bytes');
  let json: Gltf | undefined, bin: Uint8Array | undefined;
  for (let offset = 12; offset < bytes.byteLength;) {
    if (offset + 8 > bytes.byteLength) throw new Error('Truncated chunk header');
    const length = view.getUint32(offset, true), type = view.getUint32(offset + 4, true);
    offset += 8;
    if (length % 4 || offset + length > bytes.byteLength) throw new Error('Invalid chunk length');
    const chunk = bytes.subarray(offset, offset + length);
    if (type === 0x4e4f534a) {
      if (json) throw new Error('Multiple JSON chunks');
      json = JSON.parse(new TextDecoder().decode(chunk).trim()) as Gltf;
    } else if (type === 0x004e4942) {
      if (bin) throw new Error('Multiple BIN chunks');
      bin = chunk;
    } else throw new Error('Unsupported GLB chunk');
    offset += length;
  }
  if (!json || !bin || json.asset.version !== '2.0' || json.buffers.length !== 1 || json.buffers[0]!.uri
    || json.buffers[0]!.byteLength > bin.byteLength) throw new Error('Requires one embedded uncompressed GLB buffer');
  const gltf = json, buffer = bin;
  const readAccessor = (index: number, type: 'MAT4' | 'VEC3') => {
    const a = gltf.accessors[index];
    if (!a || a.type !== type || a.componentType !== 5126 || a.sparse || a.bufferView === undefined
      || !Number.isInteger(a.count) || a.count < 1) throw new Error('Requires dense FLOAT ' + type + ' accessor');
    const b = gltf.bufferViews[a.bufferView];
    if (!b || b.buffer !== 0 || b.extensions) throw new Error('Missing or compressed accessor buffer view');
    const components = type === 'MAT4' ? 16 : 3, packed = components * 4, stride = b.byteStride ?? packed;
    const start = (b.byteOffset ?? 0) + (a.byteOffset ?? 0);
    const end = start + (a.count - 1) * stride + packed;
    if (stride < packed || stride % 4 || start % 4 || start < (b.byteOffset ?? 0)
      || end > (b.byteOffset ?? 0) + b.byteLength || end > gltf.buffers[0]!.byteLength)
      throw new Error('Accessor exceeds consumed buffer bounds');
    const data = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);
    return Array.from({ length: a.count }, (_, i) => Array.from({ length: components }, (_, k) => {
      const value = data.getFloat32(start + i * stride + k * 4, true);
      if (!Number.isFinite(value)) throw new Error('Nonfinite accessor');
      return value;
    }));
  };
  const parents = new Map<number, number>();
  gltf.nodes.forEach((node, i) => {
    for (const child of node.children ?? []) {
      if (!gltf.nodes[child] || parents.has(child)) throw new Error('Invalid or multiply-parented node');
      parents.set(child, i);
    }
  });
  const scene = gltf.scenes[declaration.sceneIndex], skin = gltf.skins[declaration.skinIndex];
  if (!scene || !skin || skin.joints.length !== 19 || skin.inverseBindMatrices === undefined)
    throw new Error('Requires declared scene, actual 19-joint skin and inverse-bind accessor');
  const reachable = new Set<number>(), visiting = new Set<number>();
  const walk = (index: number) => {
    if (!gltf.nodes[index] || visiting.has(index) || reachable.has(index)) throw new Error('Invalid/cyclic scene hierarchy');
    visiting.add(index); reachable.add(index);
    for (const child of gltf.nodes[index]!.children ?? []) walk(child);
    visiting.delete(index);
  };
  for (const root of scene.nodes) {
    if (parents.has(root)) throw new Error('Scene root is parented');
    walk(root);
  }
  const game = checkedMatrix(declaration.sceneToGameWorldColumnMajor, 'scene-to-game');
  const worlds = new Map<number, Matrix4>();
  const world = (index: number): Matrix4 => {
    const cached = worlds.get(index); if (cached) return cached;
    if (!reachable.has(index)) throw new Error('Bound node outside consumed scene');
    const node = gltf.nodes[index]!, local = node.matrix ? checkedMatrix(node.matrix, 'node matrix') :
      new Matrix4().compose(new Vector3().fromArray(node.translation ?? [0, 0, 0]),
        new Quaternion().fromArray(node.rotation ?? [0, 0, 0, 1]), new Vector3().fromArray(node.scale ?? [1, 1, 1]));
    checkedMatrix(local.toArray(), 'node TRS');
    const parent = parents.get(index), result = (parent === undefined ? game : world(parent)).clone().multiply(local);
    worlds.set(index, result); return result;
  };
  const inverseBinds = readAccessor(skin.inverseBindMatrices, 'MAT4');
  if (inverseBinds.length !== skin.joints.length || declaration.joints.length !== 19)
    throw new Error('Bind/declaration joint count mismatch');
  const declaredNodes = new Set(declaration.joints.map(j => j.nodeIndex));
  if (declaredNodes.size !== 19 || new Set(skin.joints).size !== 19) throw new Error('Duplicate skin/declaration node');
  const joints = skin.joints.map((nodeIndex, i) => {
    const d = declaration.joints.find(j => j.nodeIndex === nodeIndex);
    if (!d || gltf.nodes[nodeIndex]?.name !== d.name) throw new Error('Actual source bone/name differs from mapping');
    return { ...d, parentNodeIndex: parents.get(nodeIndex) ?? null,
      restWorldColumnMajor: world(nodeIndex).toArray(), inverseBindColumnMajor: inverseBinds[i]! };
  });
  const root = joints.find(j => j.role === 'pelvis');
  if (!root) throw new Error('No declared pelvis');
  const min = new Vector3(Infinity, Infinity, Infinity), max = new Vector3(-Infinity, -Infinity, -Infinity);
  const meshRestWorldColumnMajor: number[][] = [];
  for (const index of reachable) {
    const node = gltf.nodes[index]!;
    if (node.skin !== declaration.skinIndex || node.mesh === undefined) continue;
    const matrix = world(index); meshRestWorldColumnMajor.push(matrix.toArray());
    const mesh = gltf.meshes[node.mesh]; if (!mesh) throw new Error('Missing consumed skinned mesh');
    for (const primitive of mesh.primitives) {
      if (primitive.extensions) throw new Error('Extended/compressed primitive requires explicit decoded source adapter');
      if (primitive.attributes.POSITION === undefined) throw new Error('Missing actual mesh positions');
      for (const p of readAccessor(primitive.attributes.POSITION, 'VEC3')) {
        const point = new Vector3().fromArray(p).applyMatrix4(matrix); min.min(point); max.max(point);
      }
    }
  }
  const result: Binding = { schemaVersion: 1, sourceSHA256, skinIndex: declaration.skinIndex, joints,
    rootParentWorldColumnMajor: root.parentNodeIndex === null ? game.toArray() : world(root.parentNodeIndex).toArray(),
    meshRestWorldColumnMajor, restBoundsWorld: meshRestWorldColumnMajor.length ? { min: min.toArray(), max: max.toArray() } : null };
  prepareBinding(result); return result;
}
