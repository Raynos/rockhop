"""Authored selected hoodie joint receiver. CPU mesh construction only.

The cut, loop schedule, radial shaping, armhole tangents and rolled cuff are
explicit modeling decisions. Original selected geometry remains the shape and
detail source. This is not a dense fitting optimizer or an accepted garment.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def checked(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], row
    return path
SOURCE = {'path': 'harness/out/rider-rebuild/selected-hoodie-production76/receiver02/receiver.npz',
          'sha256': '190307f6f6956770b03c71e0f8458cfd985cd57e9eb6fee4dd3949474754ec60'}
REST = {'path': 'harness/out/rider-rebuild/selected-sleeve-component47/intake01/intake-qualified.json',
        'sha256': '55adfeb1c0a6ff43d640338af1062d05c2893b56695cc94fa79a46144fd532c5'}
BODY = {'path': 'harness/out/rider-rebuild/selected-seated-anatomical09/reference05/original-full-reference.npz',
        'sha256': '01f752d72e94dbab81cc7a193adbd2dd7bba26df919b48454d8937fa9665dcc5'}
NATIVE_GEOMETRY = {'path': 'harness/out/rider-rebuild/selected-proximal-fit-review54/original01/actual-hoodie-geometry.npz',
                   'sha256': '370a8bc8569113e422b66d05a8677f6d206628eb362cf731fb6903ac641e06fd'}


def unit(value):
    return value/np.linalg.norm(value, axis=-1, keepdims=True)


def cut_width(z):
    # Source-specific curved armhole: preserve the hood and hem, retain chest
    # panels, descend into the selected underarm rather than laying a shelf
    # across it. Values are editable seam design, not contact tolerances.
    return np.interp(z, [.85, 1.18, 1.25, 1.34, 1.42, 1.47, 1.50, 1.53, 1.7],
                    [.24, .212, .175, .135, .130, .153, .210, .40, .60])


class Mesh:
    def __init__(self, source):
        self.source = source
        self.positions = source['positions'].tolist()
        self.reference_positions = source['positions'].tolist()
        self.parents = [[i, i] for i in range(len(self.positions))]
        self.fractions = [0. for _ in self.positions]
        self.roles = ['selected_original' for _ in self.positions]
        self.skin_blend = [0. for _ in self.positions]
        self.skin_seam = [(-1,-1,0.) for _ in self.positions]
        self.faces, self.uvs, self.ancestry, self.face_roles = [], [], [], []
        self.cut_ids = {1: set(), -1: set()}
        self.edgecuts = {}
        self.decisions = []

    def append(self, p, role, parents=(-1, -1), fraction=0.):
        index = len(self.positions)
        self.positions.append(np.asarray(p).tolist())
        self.reference_positions.append(np.asarray(p).tolist())
        self.parents.append(list(parents)); self.fractions.append(float(fraction)); self.roles.append(role)
        self.skin_blend.append(0.)
        self.skin_seam.append((-1,-1,0.))
        return index

    def face(self, vertices, uv, ancestry, role):
        assert len(vertices) == len(set(vertices)) >= 3
        self.faces.append(list(vertices)); self.uvs.append(np.asarray(uv).tolist())
        self.ancestry.append(ancestry); self.face_roles.append(role)

    def clip(self):
        a = self.source
        points = a['positions']
        for fi, (s, n) in enumerate(zip(a['polygonStarts'], a['polygonCounts'])):
            ids = a['cornerVertexIds'][s:s+n].tolist()
            corners = [(i, uv.copy()) for i, uv in zip(ids, a['cornerUV'][s:s+n])]
            for side in (1, -1):
                result = []
                for (ia, uva), (ib, uvb) in zip(corners, corners[1:]+corners[:1]):
                    pa, pb = np.asarray(self.positions[ia]), np.asarray(self.positions[ib])
                    fa, fb = side*pa[0]-cut_width(pa[2]), side*pb[0]-cut_width(pb[2])
                    if fa <= 0: result.append((ia, uva))
                    if (fa < 0) != (fb < 0):
                        fraction = fa/(fa-fb)
                        key = (side, min(ia, ib), max(ia, ib))
                        if key not in self.edgecuts:
                            index = self.append(pa+(pb-pa)*fraction, 'armhole_seam', (ia, ib), fraction)
                            self.edgecuts[key] = index; self.cut_ids[side].add(index)
                        result.append((self.edgecuts[key], uva+(uvb-uva)*fraction))
                corners = result
                if not corners: break
            if len(corners) >= 3:
                self.face([i for i, _ in corners], [uv for _, uv in corners], fi, 'selected_retained')

    def boundary(self, side):
        edges = Counter(); directed = {}
        for f in self.faces:
            for a, b in zip(f, f[1:]+f[:1]):
                key = tuple(sorted((a, b))); edges[key] += 1; directed[key] = (a, b)
        adj = defaultdict(list)
        for (a, b), count in edges.items():
            if count == 1 and a in self.cut_ids[side] and b in self.cut_ids[side]:
                adj[a].append(b); adj[b].append(a)
        assert all(len(v) == 2 for v in adj.values()), Counter(map(len, adj.values()))
        loops, visited = [], set()
        for start in sorted(adj):
            if start in visited: continue
            loop, current, last = [], start, None
            while current not in visited:
                visited.add(current); loop.append(current)
                options = [i for i in adj[current] if i != last]
                last, current = current, options[0]
            assert current == start
            if directed[tuple(sorted((loop[0], loop[1])))] != tuple(loop[:2]): loop.reverse()
            loops.append(loop)
        return loops

    def discard_detached_cut_scrap(self):
        adjacency = defaultdict(set)
        for i, face in enumerate(self.faces):
            for v in face: adjacency[v].add(i)
        seen, components = set(), []
        for i in range(len(self.faces)):
            if i in seen: continue
            stack, component = [i], []
            while stack:
                face = stack.pop()
                if face in seen: continue
                seen.add(face); component.append(face)
                for v in self.faces[face]: stack.extend(adjacency[v]-seen)
            components.append(component)
        keep = sorted(max(components, key=len))
        self.decisions.append({'discardedDetachedCutPolygons': len(self.faces)-len(keep)})
        for field in ('faces', 'uvs', 'ancestry', 'face_roles'):
            old = getattr(self, field); setattr(self, field, [old[i] for i in keep])

    def orient_and_measure(self):
        edges=defaultdict(list)
        for fi,face in enumerate(self.faces):
            for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))].append((fi,a<b))
        assert max(map(len,edges.values()))==2
        # Original selected faces are the winding authority. Orientation then
        # propagates across every authored join, including opposite inner wall.
        known={i:False for i,role in enumerate(self.face_roles) if role=='selected_retained'}
        adjacency=defaultdict(list)
        for rows in edges.values():
            if len(rows)!=2:continue
            (a,da),(b,db)=rows;different=da==db
            adjacency[a].append((b,different));adjacency[b].append((a,different))
        stack=list(known)
        while stack:
            fi=stack.pop()
            for other,change in adjacency[fi]:
                flip=known[fi]^change
                if other in known:assert known[other]==flip,('Nonorientable joint',fi,other)
                else:known[other]=flip;stack.append(other)
        assert len(known)==len(self.faces)
        for i,flip in known.items():
            if flip:self.faces[i].reverse();self.uvs[i].reverse()
        points=np.asarray(self.positions);areas=[];boundary_roles=Counter();boundary=[]
        wrong=0
        for key,rows in edges.items():
            if len(rows)==2:
                (a,da),(b,db)=rows
                wrong+=int((da^known[a])==(db^known[b]))
            else:
                fi,_=rows[0];boundary_roles[self.face_roles[fi]]+=1;boundary.append(list(key))
        for face in self.faces:
            for j in range(1,len(face)-1):
                areas.append(float(np.linalg.norm(np.cross(points[face[j]]-points[face[0]],points[face[j+1]]-points[face[0]]))/2))
        assert wrong==0 and min(areas)>0
        report={'verticesUsed':len({i for f in self.faces for i in f}),'polygons':len(self.faces),
                'triangles':len(areas),'edgeIncidences':dict(Counter(map(len,edges.values()))),
                'sameDirectionSharedEdges':wrong,'minimumFanAreaM2':min(areas),'zeroAreaFans':sum(x==0 for x in areas),
                'boundaryEdgesByOwningFaceRole':dict(boundary_roles),'authoredFacesReversed':int(sum(known.values()))}
        self.decisions.append({'actualTopology':report})
        return report


class Surface:
    def __init__(self, points, triangles):
        self.points, self.faces = np.asarray(points), np.asarray(triangles)
        self.tri = self.points[self.faces]
        self.low, self.high = self.tri.min(1), self.tri.max(1)

    def nearest(self, point):
        vertex_bound = np.min(np.sum((self.points-point)**2,axis=1))
        box = np.maximum(self.low-point,0)+np.minimum(self.high-point,0)
        ids=np.flatnonzero(np.sum(box*box,axis=1)<=vertex_bound)
        t=self.tri[ids];a,b,c=t[:,0],t[:,1],t[:,2]
        ab,ac=b-a,c-a;ap=point-a
        aa=np.einsum('ij,ij->i',ab,ab);bb=np.einsum('ij,ij->i',ac,ac);cross=np.einsum('ij,ij->i',ab,ac)
        d=np.einsum('ij,ij->i',ap,ab);e=np.einsum('ij,ij->i',ap,ac)
        determinant=aa*bb-cross*cross;safe=determinant>0;divisor=np.where(safe,determinant,1)
        v=(bb*d-cross*e)/divisor;w=(aa*e-cross*d)/divisor
        bary=np.stack([1-v-w,v,w],axis=1);projected=np.einsum('ij,ijk->ik',bary,t)
        distance=np.linalg.norm(projected-point,axis=1);distance[~safe|(bary.min(1)<0)]=np.inf
        for i,j in ((0,1),(1,2),(2,0)):
            edge=t[:,j]-t[:,i];norm=np.einsum('ij,ij->i',edge,edge)
            fraction=np.clip(np.einsum('ij,ij->i',point-t[:,i],edge)/np.where(norm>0,norm,1),0,1)
            candidate=t[:,i]+fraction[:,None]*edge;other=np.linalg.norm(candidate-point,axis=1);better=other<distance
            distance[better]=other[better];bary[better]=0;bary[better,i]=1-fraction[better];bary[better,j]=fraction[better]
        best=int(np.argmin(distance));face=int(ids[best]);weights=bary[best]
        q=weights@self.tri[face];normal=unit(np.cross(self.tri[face,1]-self.tri[face,0],self.tri[face,2]-self.tri[face,0]))
        signed=float(np.dot(point-q,normal))
        return face,weights,q,normal,float(distance[best])*(1 if signed>=0 else -1)

    def ray(self, origin, direction, maximum=np.inf):
        near, far = np.full(len(self.faces), -np.inf), np.full(len(self.faces), np.inf)
        valid = np.ones(len(self.faces), bool)
        for axis in range(3):
            if abs(direction[axis]) < 1e-14:
                valid &= (self.low[:, axis] <= origin[axis]) & (self.high[:, axis] >= origin[axis])
            else:
                a = (self.low[:, axis]-origin[axis])/direction[axis]
                b = (self.high[:, axis]-origin[axis])/direction[axis]
                near = np.maximum(near, np.minimum(a, b)); far = np.minimum(far, np.maximum(a, b))
        ids = np.flatnonzero(valid & (far >= np.maximum(near, 0)) & (near <= maximum))
        t = self.tri[ids]; e1, e2 = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]
        h = np.cross(direction, e2); det = np.sum(e1*h, axis=1)
        valid = abs(det) > 1e-18; inv = 1/np.where(valid, det, 1.)
        delta = origin-t[:, 0]; u = np.sum(delta*h, axis=1)*inv
        q = np.cross(delta, e1); v = q@direction*inv; distance = np.sum(e2*q, axis=1)*inv
        good = np.flatnonzero(valid & (u >= -1e-10) & (v >= -1e-10) & (u+v <= 1+1e-10) &
                              (distance > 0) & (distance <= maximum))
        return sorted((float(distance[i]), float(np.cross(e1[i], e2[i])@direction), int(ids[i]),
                       np.asarray([1-u[i]-v[i], u[i], v[i]])) for i in good)


def triangulate(a):
    faces, uv, ancestry = [], [], []
    for fi, (s, n) in enumerate(zip(a['polygonStarts'], a['polygonCounts'])):
        ids = a['cornerVertexIds'][s:s+n]; corners = a['cornerUV'][s:s+n]
        for j in range(1, n-1):
            faces.append(ids[[0,j,j+1]]); uv.append(corners[[0,j,j+1]]); ancestry.append(fi)
    return np.asarray(faces), np.asarray(uv), np.asarray(ancestry)


def bone_frame(rest, side):
    sign = 1 if side == 'L' else -1
    bones = {r[0]: r for r in rest}
    shoulder = np.asarray(bones['DEF-upper_arm.'+side][2])
    elbow = np.asarray(bones['DEF-forearm.'+side][2])
    wrist = np.asarray(bones['DEF-hand.'+side][2])
    upper, lower = unit(elbow-shoulder), unit(wrist-elbow)
    lengths = np.linalg.norm(elbow-shoulder), np.linalg.norm(wrist-elbow)
    def frame(s):
        # Rounded rest centerline through the real75 elbow; the source wearer
        # already has slight elbow flexion. No new bind or joint placement.
        blend = np.clip((s-lengths[0]+.035)/.07, 0, 1)
        blend = blend*blend*(3-2*blend)
        axis = unit(upper*(1-blend)+lower*blend)
        center = shoulder+upper*s if s <= lengths[0] else elbow+lower*(s-lengths[0])
        forward = unit(np.array([0.,-1.,0.])-axis*np.dot(axis,[0.,-1.,0.]))
        outward = -sign*np.cross(axis,forward)
        return center, axis, forward, outward
    return frame, lengths


def outward_hit(surface, origin, direction, maximum):
    hits = surface.ray(origin,direction,maximum)
    outer = [h for h in hits if h[1] > 0]
    return outer[0] if outer else (hits[0] if hits else None)


def dress_retained_torso(mesh, donor, body):
    """Local penetration repair on the retained selected panels only.

    Exact nearest body triangles identify the actual intersecting patches.
    The failed02 radial-first-wall method is deliberately not used: its ray
    could cross a source fold and move otherwise healthy panels106.9mm.
    """
    used = sorted({i for f in mesh.faces for i in f})
    normals=np.zeros_like(donor.points)
    tn=np.cross(donor.tri[:,1]-donor.tri[:,0],donor.tri[:,2]-donor.tri[:,0])
    for corner in range(3):np.add.at(normals,donor.faces[:,corner],tn)
    norms=np.linalg.norm(normals,axis=1);normals/=np.where(norms>0,norms,1)[:,None]
    moved, distances,extrema = [], [],[]
    for i in used:
        p = np.asarray(mesh.positions[i])
        if not 1.135 < p[2] < 1.50: continue
        face,bary,q,normal,gap=body.nearest(p)
        ia,ib=mesh.parents[i];fraction=mesh.fractions[i]
        cloth_normal=normals[ia]*(1-fraction)+normals[ib]*fraction
        outer=np.dot(cloth_normal,normal)>=0
        ease=.0053 if outer else .003
        if gap < ease:
            corrected=q+normal*ease;displacement=float(np.linalg.norm(corrected-p))
            mesh.positions[i]=corrected.tolist();moved.append(i);distances.append(displacement)
            extrema.append({'id':i,'distanceM':displacement,'signedBodyGapM':gap,'original':p.tolist(),
                            'result':corrected.tolist(),'bodyTriangle':face,'outerWall':bool(outer)})
    mesh.decisions.append({'retainedTorsoFitting':'Local actual negative/near-contact correction; original selected topology and UV retained',
                           'changedVertices':len(moved),'maximumDisplacementM':max(distances,default=0.),
                           'hoodAndHemExact':True,'innerOuterAuthoringEaseM':[.003,.0053],
                           'largestActualCorrections':sorted(extrema,key=lambda x:-x['distanceM'])[:12]})


def contain_cap(points,frame,body,layer):
    # The cap's axial/circumferential layout is authored above. This final local
    # radius bound keeps its inside lining outside the actual rest shoulder.
    result=[]
    for p in points:
        face,bary,q,normal,gap=body.nearest(p)
        ease=.003 if layer else .0053
        result.append(q+ease*normal if gap<ease else p)
    return np.asarray(result)


def build_sleeve(mesh, side, rest, donor, body, donor_uv,glove):
    sign = 1 if side == 'L' else -1
    frame, lengths = bone_frame(rest,side)
    loops = mesh.boundary(sign)
    assert len(loops) == 2
    center, axis, forward, outward = frame(0)
    # Largest projected enclosed area identifies the exterior of the two actual
    # selected garment layers; each source boundary retains its exact vertices.
    def area(loop):
        p = np.asarray(mesh.positions)[loop]-center
        q = np.stack([p@forward,p@outward],axis=1)
        return abs(np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1)))/2
    loops.sort(key=area,reverse=True)
    theta = np.arange(48)*2*np.pi/48
    elbow, total = lengths[0],sum(lengths)
    # Deliberate deformation-loop density at cap, flexion/compression zones,
    # cuff gather, rib transition and rolled lip, with wider fabric panels.
    stations = np.asarray([.145,.168,.194,.218,elbow-.039,elbow-.024,elbow-.011,
                           elbow,elbow+.011,elbow+.025,elbow+.044,.343,.375,.407,
                           total-.100,total-.080,total-.068,total-.061,total-.055,
                           total-.048,total-.042,total-.036,total-.030,total-.024])
    stations = np.unique(np.sort(stations))
    rings, source_radii, body_radii = [], [], []
    missed = []
    for s in stations:
        origin, tangent, f, o = frame(s)
        row, sr, br = [],[],[]
        for angle in theta:
            direction = f*np.cos(angle)+o*np.sin(angle)
            selected = outward_hit(donor,origin,direction,.15)
            wearer = outward_hit(body,origin,direction,.15)
            if selected is None:
                # The selected open cuff ends unevenly. Its termination is
                # deliberately rebuilt from the nearest earlier cuff section.
                assert s > total-.04
                for retreat in (.006,.012,.020,.030):
                    prior_origin,_,prior_f,prior_o=frame(s-retreat)
                    prior_direction=prior_f*np.cos(angle)+prior_o*np.sin(angle)
                    selected=outward_hit(donor,prior_origin,prior_direction,.15)
                    if selected is not None:
                        missed.append({'station':float(s),'theta':float(angle),
                                       'surface':'selected cuff end','sourceSectionRetreatM':retreat})
                        break
            if wearer is None: missed.append({'station':float(s),'theta':float(angle),'surface':'body'})
            assert selected is not None and wearer is not None, missed[-1]
            sr.append(selected[0]);br.append(wearer[0])
            row.append((selected[2], selected[3]))
        source_radii.append(sr);body_radii.append(br);rings.append(row)
    source_radii,body_radii = np.asarray(source_radii),np.asarray(body_radii)
    # Keep source fold phase and silhouette. A light circular fairing removes
    # faceted section noise; the selected folded radius remains the authority.
    radii = .7*source_radii+.15*np.roll(source_radii,1,axis=1)+.15*np.roll(source_radii,-1,axis=1)
    ease = np.interp(stations,[.145,elbow,total-.06,total],[.007,.008,.005,.004])
    radii = np.maximum(radii,body_radii+ease[:,None])
    cuff_measurements=[]
    wall=np.interp(stations,[total-.100,total-.055,total-.024],[.0023,.0008,.0008])
    for si,s in enumerate(stations):
        if s<total-.10:continue
        origin,_,f,o=frame(s)
        taper=np.clip((s-(total-.10))/.04,0,1);taper=taper*taper*(3-2*taper)
        for i,angle in enumerate(theta):
            direction=f*np.cos(angle)+o*np.sin(angle)
            hits=glove.ray(origin,direction,.13)
            # A narrow tucked knitted cuff has its own deliberate structure,
            # instead of carrying the malformed selected open termination.
            tucked=body_radii[si,i]+.0015+wall[si]
            radii[si,i]=radii[si,i]*(1-taper)+tucked*taper
            if hits:
                radii[si,i]=min(radii[si,i],hits[0][0]-.001)
                cuff_measurements.append({'s':float(s),'theta':float(angle),
                    'bodyToGloveInnerM':float(hits[0][0]-body_radii[si,i]),
                    'sleeveOuterRadiusM':float(radii[si,i]),'bodyRadiusM':float(body_radii[si,i]),
                    'gloveInnerRadiusM':float(hits[0][0])})
    assert np.all(radii-wall[:,None]>body_radii)
    layer_rows = []
    for layer, boundary in enumerate(loops):
        p0 = np.asarray(mesh.positions)[boundary]
        source_p0=np.asarray(mesh.reference_positions)[boundary]
        values = np.arctan2((source_p0-center)@outward,(source_p0-center)@forward)%(2*np.pi)
        order = np.argsort(values); ids = np.asarray(boundary)[order]; values = values[order]
        p0 = p0[order]
        # Source boundary sample by angular sector, independently on each wall.
        extended = np.r_[values[-1]-2*np.pi,values,values[0]+2*np.pi]
        xyz = np.concatenate([p0[-1:],p0,p0[:1]])
        extended_ids=np.r_[ids[-1],ids,ids[0]]
        seam = np.stack([np.interp(theta,extended,xyz[:,i])for i in range(3)],axis=1)
        seam_fields=[]
        for angle in theta:
            j=int(np.searchsorted(extended,angle,side='right')-1)
            fraction=(angle-extended[j])/(extended[j+1]-extended[j])
            seam_fields.append((int(extended_ids[j]),int(extended_ids[j+1]),float(fraction)))
        first_points = []
        for i,angle in enumerate(theta):
            origin,_,f,o=frame(stations[0]);r=radii[0,i]-(.0023 if layer else 0.)
            first_points.append(origin+r*(f*np.cos(angle)+o*np.sin(angle)))
        first_points=np.asarray(first_points)
        # Cubic cap: source shoulder tangent begins laterally, then turns along
        # upper arm. Axilla uses shorter handles; no ruled/shelf bridge.
        delta=first_points-seam;distance=np.linalg.norm(delta,axis=1)
        lateral=np.tile([float(sign),0.,0.],(len(theta),1))
        cap_turn=.9*(np.sin(theta)+1)*.5
        start_tangent=unit(lateral*cap_turn[:,None]+axis*(1-cap_turn[:,None]))
        end_tangent=np.tile(frame(stations[0])[1],(len(theta),1))
        cap=[]
        for u in (.06,.15,.30,.50,.72,.88):
            h00=2*u**3-3*u*u+1;h10=u**3-2*u*u+u;h01=-2*u**3+3*u*u;h11=u**3-u*u
            points=h00*seam+h10*distance[:,None]*start_tangent+h01*first_points+h11*distance[:,None]*end_tangent
            points=contain_cap(points,frame,body,layer)
            row=[mesh.append(p,'shoulder_cap_'+side if np.sin(theta[i])>.15 else 'axilla_'+side)
                 for i,p in enumerate(points)]
            for vi,seam_field in zip(row,seam_fields):
                mesh.skin_blend[vi]=u*u*(3-2*u);mesh.skin_seam[vi]=seam_field
            cap.append(row)
        rows=list(cap)
        for si,s in enumerate(stations):
            origin,_,f,o=frame(s)
            region='elbow' if abs(s-elbow)<.05 else ('cuff' if s>total-.06 else 'sleeve_panel')
            row=[mesh.append(origin+(radii[si,i]-(wall[si] if layer else 0.))*(f*np.cos(angle)+o*np.sin(angle)),region+'_'+side)
                 for i,angle in enumerate(theta)]
            for vi in row:mesh.skin_blend[vi]=1.
            rows.append(row)
        # The source armhole spans a long shoulder cap but a short axilla cap.
        # Its field transition follows actual meridian arc length, so a tiny
        # underarm step cannot shed a large torso influence. The80mm painter
        # width is an explicit local rigging design, not an acceptance limit.
        lengths=[];distance=np.zeros(len(theta));previous=seam
        for row in rows:
            current=np.asarray(mesh.positions)[row]
            distance+=np.linalg.norm(current-previous,axis=1)
            lengths.append(distance.copy());previous=current
        blend_length=np.maximum(.080,lengths[len(cap)])
        for row,travel in zip(rows,lengths):
            blend=np.clip(travel/blend_length,0,1);blend=blend*blend*(3-2*blend)
            for vi,fraction,seam_field in zip(row,blend,seam_fields):
                mesh.skin_blend[vi]=float(fraction);mesh.skin_seam[vi]=seam_field
        # Angular zipper joins the real variable-count source boundary to the
        # first48-loop. It introduces local triangles only at that join.
        ordered=np.r_[ids,ids[:1]];angles=np.r_[values,values[0]+2*np.pi]
        # Re-index both closed loops at the first regular sample after cut0.
        start=int(np.searchsorted(theta,values[0])%len(theta))
        regular=np.roll(np.asarray(rows[0]),-start);ta=np.roll(theta,-start)
        ta=np.unwrap(ta);ta+=2*np.pi*np.ceil((values[0]-ta[0])/(2*np.pi))
        # Begin at the smallest-angle pair; zipper walks each circumference once.
        i=j=0
        while i<len(ids) or j<len(regular):
            aa=ordered[i%len(ids)];bb=regular[j%len(regular)]
            na=angles[i+1] if i<len(ids) else np.inf
            nb=ta[j+1] if j+1<len(regular) else (ta[0]+2*np.pi if j<len(regular) else np.inf)
            if na<nb:
                face=[aa,ordered[(i+1)%len(ids)],bb];i+=1
            else:
                face=[aa,regular[(j+1)%len(regular)],bb];j+=1
            mesh.face(face,np.zeros((len(face),2)),-1,'authored_armhole_'+side)
        for a,b in zip(rows,rows[1:]):
            for i in range(len(theta)):
                j=(i+1)%len(theta)
                mesh.face([a[i],a[j],b[j],b[i]],np.zeros((4,2)),-1,'authored_'+('inner'if layer else'outer')+'_'+side)
        layer_rows.append(rows)
    # Continuous circular garment rim: full rings close both sleeve layers.
    outer,inner=layer_rows[0][-1],layer_rows[1][-1]
    lip=[outer];origin,tangent,f,o=frame(stations[-1])
    for phi in (np.pi/4,np.pi/2,3*np.pi/4):
        row=[]
        for i,angle in enumerate(theta):
            direction=f*np.cos(angle)+o*np.sin(angle)
            radius=radii[-1,i]-wall[-1]/2+wall[-1]/2*np.cos(phi)
            row.append(mesh.append(origin+radius*direction+tangent*wall[-1]/2*np.sin(phi),'cuff_rolled_lip_'+side))
        for vi in row:mesh.skin_blend[vi]=1.
        lip.append(row)
    lip.append(inner)
    for a,b in zip(lip,lip[1:]):
        for i in range(len(theta)):
            j=(i+1)%len(theta)
            mesh.face([a[i],a[j],b[j],b[i]],np.zeros((4,2)),-1,'authored_cuff_rim_'+side)
    mesh.decisions.append({'side':side,'perimeterVertices':len(theta),'stationsM':stations.tolist(),
                           'capTransitionRings':6,'sourceBoundaryVertices':[len(l)for l in loops],
                           'sourceRadiusM':[float(source_radii.min()),float(source_radii.max())],
                           'bodyRadiusM':[float(body_radii.min()),float(body_radii.max())],
                           'authoredEaseM':ease.tolist(),'wallThicknessM':wall.tolist(),
                           'tuckedCuffBodyEaseM':.0015,'cuffGloveLipOffsetM':.001,
                           'cuffEndBeforeActual75WristM':.024,'actualGlove41CuffSections':cuff_measurements,
                           'sourceShapeGuideMissingRays':missed})


def limb_fields(point,side,rest,names):
    """Explicit smooth twist/flex distribution on the existing native75 bones."""
    frame,lengths=bone_frame(rest,side);elbow,total=lengths[0],sum(lengths)
    start,axis,_,_=frame(0);joint,lower,_,_=frame(elbow+.07)
    actual_elbow=frame(elbow)[0]
    su=float((point-start)@axis);sl=elbow+float((point-actual_elbow)@lower)
    s=su if su<elbow else sl
    centers=np.asarray([.08,.19,elbow-.040,elbow+.040,elbow+.075,elbow+.190])
    upper='DEF-upper_arm.'+side;upper2=upper+'.001';fore='DEF-forearm.'+side;fore2=fore+'.001'
    if s<=centers[0]:pair=(upper,upper);fraction=0.
    elif s<centers[1]:pair=(upper,upper2);fraction=(s-centers[0])/(centers[1]-centers[0])
    elif s<centers[2]:pair=(upper2,upper2);fraction=0.
    elif s<centers[3]:pair=(upper2,fore);fraction=(s-centers[2])/(centers[3]-centers[2])
    elif s<centers[4]:pair=(fore,fore);fraction=0.
    elif s<centers[5]:pair=(fore,fore2);fraction=(s-centers[4])/(centers[5]-centers[4])
    else:pair=(fore2,fore2);fraction=0.
    fraction=fraction*fraction*(3-2*fraction)
    row=np.zeros(len(names));row[names.index(pair[0])]+=1-fraction;row[names.index(pair[1])]+=fraction
    return row


def package(mesh,a,donor,donor_uv,rest,guides,out):
    used=np.asarray(sorted({i for f in mesh.faces for i in f}),np.int32)
    remap=np.full(len(mesh.positions),-1,np.int32);remap[used]=np.arange(len(used))
    positions=np.asarray(mesh.positions)[used]
    parents=np.zeros((len(used),3),np.int32);weights=np.zeros((len(used),3))
    preview_uv=np.zeros((len(used),2));source_point=np.zeros_like(positions);source_distance=[]
    for vi,old in enumerate(used):
        ia,ib=mesh.parents[old];fraction=mesh.fractions[old]
        if ia>=0:
            parents[vi]=[ia,ib,ib];weights[vi]=[1-fraction,fraction,0]
        else:
            face,bary,q,normal,gap=donor.nearest(positions[vi])
            parents[vi]=donor.faces[face];weights[vi]=bary
        q=np.sum(a['positions'][parents[vi]]*weights[vi,:,None],axis=0)
        source_point[vi]=q;face,bary,_,_,_=donor.nearest(q)
        preview_uv[vi]=bary@donor_uv[face]
        source_distance.append(float(np.linalg.norm(positions[vi]-q)))
        if vi and vi%3000==0:print('receiver source correspondences',vi,len(used),flush=True)
    # Exact full named fields from the actual original47 cache. No top4 drop.
    names=guides['groupNames'].tolist();native_faces=np.load(checked(NATIVE_GEOMETRY))['faces']
    source_fields=np.zeros((len(a['positions']),len(names)))
    offsets,indices,values=guides['fieldOffsets'],guides['fieldIndices'],guides['fieldWeights']
    for vi,(face,bary)in enumerate(zip(a['sourceTriangle'],a['sourceBarycentric'])):
        for original,coefficient in zip(native_faces[face],bary):
            start,stop=offsets[original:original+2]
            source_fields[vi,indices[start:stop]]+=coefficient*values[start:stop]
    baseline=np.sum(source_fields[parents]*weights[:,:,None],axis=1)
    fields=baseline.copy()
    for vi,old in enumerate(used):
        blend=mesh.skin_blend[old]
        if blend:
            side=mesh.roles[old][-1]
            ia,ib,fraction=mesh.skin_seam[old]
            seam_baseline=(baseline[remap[ia]]*(1-fraction)+baseline[remap[ib]]*fraction)if ia>=0 else baseline[vi]
            fields[vi]=(1-blend)*seam_baseline+blend*limb_fields(positions[vi],side,rest,names)
    assert np.isfinite(fields).all() and fields.min()>=-1e-10 and np.max(abs(fields.sum(1)-1))<2e-6
    starts=[];counts=[];corners=[];uvs=[];bake=[]
    for face,original_uv,role in zip(mesh.faces,mesh.uvs,mesh.face_roles):
        f=remap[face];starts.append(len(corners));counts.append(len(f));corners.extend(f)
        if role=='selected_retained':
            uvs.extend(original_uv);bake.extend((np.asarray(original_uv)*[.64,.98]+[.005,.01]).tolist())
        else:
            uvs.extend(preview_uv[f]);side=role[-1];frame,lengths=bone_frame(rest,side)
            origin,axis,forward,outward=frame(0)
            p=positions[f];s=(p-origin)@axis
            angles=np.arctan2((p-origin)@outward,(p-origin)@forward)%(2*np.pi)
            if np.ptp(angles)>np.pi:angles[angles<np.pi]+=2*np.pi
            start=.67 if side=='L'else .835
            bake.extend(np.stack([start+angles/(2*np.pi)*.15,.01+(s+.09)/.65*.98],axis=1).tolist())
    arrays={'positions':positions.astype(np.float64),'polygonStarts':np.asarray(starts,np.int32),
            'polygonCounts':np.asarray(counts,np.int32),'cornerVertexIds':np.asarray(corners,np.int32),
            'cornerUV':np.asarray(uvs),'REJECTED_DRAFT_cornerBakeUV':np.asarray(bake),
            'polygonMaterialIds':np.zeros(len(counts),np.int32),'sourceCompactFace':np.asarray(mesh.ancestry,np.int32),
            'sourceReceiverVertexIds':parents,'sourceReceiverCoefficients':weights,
            'sourceAppearancePoints':source_point,'selectedToReceiverDistanceM':np.asarray(source_distance),
            'vertexRoles':np.asarray(mesh.roles)[used],'faceRoles':np.asarray(mesh.face_roles),
            'sourceOnlyNamedFields':baseline.astype(np.float32),'namedFields':fields.astype(np.float32),
            'groupNames':np.asarray(names),'authoredSkinBlend':np.asarray(mesh.skin_blend)[used],
            'constructionVertexIds':used,'referencePositions':np.asarray(mesh.reference_positions)[used]}
    arrays['authoredCapSeamParents']=np.asarray([[int(remap[int(ia)]),int(remap[int(ib)])]if ia>=0 else[-1,-1]
                                               for ia,ib,f in np.asarray(mesh.skin_seam)[used]],np.int32)
    arrays['authoredCapSeamFraction']=np.asarray([f for ia,ib,f in np.asarray(mesh.skin_seam)[used]])
    np.savez(out/'receiver.npz',**arrays)
    with (out/'selected-hoodie-joints77.obj').open('w')as stream:
        stream.write('# UNACCEPTED selected garment joint receiver; genuine detail bake and motion review pending\n')
        for p in positions:stream.write('v %.10g %.10g %.10g\n'%tuple(p))
        for uv in arrays['cornerUV']:stream.write('vt %.10g %.10g\n'%tuple(uv))
        for start,count in zip(starts,counts):
            stream.write('f '+' '.join(f'{corners[i]+1}/{i+1}'for i in range(start,start+count))+'\n')
    return arrays,{'maximumSourceCorrespondenceDistanceM':max(source_distance),
        'fullNamedFieldCount':len(names),'maximumFieldSumError':float(np.max(abs(fields.sum(1)-1))),
        'newAnatomicalFieldVertices':int(np.count_nonzero(arrays['authoredSkinBlend'])),
        'unchangedFieldVertices':int(np.count_nonzero(arrays['authoredSkinBlend']==0)),
        'healthyFieldsExactBeforeFloat32':bool(np.array_equal(fields[arrays['authoredSkinBlend']==0],baseline[arrays['authoredSkinBlend']==0])),
        'UVStatus':'Retained original cornerUV exact. New joint previewUV is source sampling only. Draft bake coordinates are REJECTED (inner/outer overlap and angular seam spill); never installed or admitted for baking.',
        'skinStatus':'Healthy source fields retained. Cap starts at exact two-neighbor seam interpolation and smoothstep blends over actual meridian arc length (at least80mm) to native75 limb fields; moved-source nearest skin is not used. Posed qualification pending.'}


def diagnostic(mesh, output, body=None):
    # Construction wire views only. These are not posed/game art evidence.
    from PIL import Image, ImageDraw
    p = np.asarray(mesh.positions)
    image = Image.new('RGB', (1600, 1000), '#10131a'); draw = ImageDraw.Draw(image)
    views = [(0, 2), (1, 2)]
    for col, axes in enumerate(views):
        def xy(point): return (round(col*800+400+point[axes[0]]*880), round(910-(point[axes[1]]-.80)*1000))
        if body is not None:
            for point in body[::10]:
                x, y = xy(point); draw.point((x, y), fill='#283846')
        for f, role in zip(mesh.faces, mesh.face_roles):
            color = '#5c6d77' if role == 'selected_retained' else '#f4be4b'
            row = [xy(point) for point in p[f]]
            draw.line(row+[row[0]], fill=color, width=1)
        draw.text((col*800+12, 12), '77 construction wire — front' if col == 0 else '77 construction wire — side', fill='white')
    image.save(output)


def main(out):
    out = Path(out).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77') and not out.exists()
    a = dict(np.load(checked(SOURCE)))
    mesh = Mesh(a); mesh.clip()
    mesh.discard_detached_cut_scrap()
    faces,uv,ancestry=triangulate(a);donor=Surface(a['positions'],faces)
    body_a=np.load(checked(BODY));body=Surface(body_a['RiderBody__FullAnatomyReference_basis'],body_a['RiderBody__FullAnatomyReference_triangles'])
    rest=json.loads(checked(REST).read_text())['expectedRest']
    dress_retained_torso(mesh,donor,body)
    guide_path=ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77/guides01/actual-guides.json'
    guide=json.loads(guide_path.read_text());assert guide['native']==json.loads(checked(REST).read_text())['native']
    guide_arrays=np.load(checked(guide['arrays']))
    mesh.decisions.append({'actualGloveGuideReceipt':pin(guide_path)})
    for side in ('L','R'):
        gp=guide_arrays['ActualSelectedGlove.'+side+'_positions'];gf=guide_arrays['ActualSelectedGlove.'+side+'_triangles']
        frame,lengths=bone_frame(rest,side);origin,axis,_,_=frame(sum(lengths));s=(gp-origin)@axis
        glove=Surface(gp,gf[np.any(s[gf]<.015,axis=1)])
        build_sleeve(mesh,side,rest,donor,body,uv,glove)
    mesh.orient_and_measure()
    out.mkdir(parents=True)
    diagnostic(mesh, out/'authored-wire.png',body.points)
    np.savez(out/'authored.npz', positions=np.asarray(mesh.positions), faces=np.asarray(mesh.faces,dtype=object))
    arrays,package_report=package(mesh,a,donor,uv,rest,guide_arrays,out)
    (out/'construction.json').write_text(json.dumps(mesh.decisions,indent=2)+'\n')
    report={'status':'AUTHORED_SELECTED_HOODIE_JOINT_RECEIVER_UNACCEPTED','acceptedArt':False,
        'recipe':pin(__file__),'sourceReceiver':SOURCE,'source47Receipt':REST,'fullBody':BODY,'original47Geometry':NATIVE_GEOMETRY,
        'actualGuides':pin(guide_path),'receiver':pin(out/'receiver.npz'),'editableOBJ':pin(out/'selected-hoodie-joints77.obj'),
        'construction':pin(out/'construction.json'),'topology':mesh.decisions[-1]['actualTopology'],
        'correspondenceAndSkin':package_report,'detailBakePassed':False,'posedContactPassed':False,
        'nativeSaved':False,'movingArtPassed':False,'genuineBakeAtlasPresent':False,'limitations':[
            'Construction receiver only. Source-selected high-frequency geometry/PBR detail needs a genuine controlled bake.',
            'Cap/axilla silhouette, actual finite body/glove contact and both directions of real-input motion need parent judgment.',
            'Source hood/hem openings and small original holes are retained; source-oriented edge checks are not a fit or art pass.',
            'The discarded draft atlas is quarantined in REJECTED_DRAFT_cornerBakeUV for diagnosis only; native assembly does not install it.',
            'Cuff authored thickness/ease is a design choice; it does not satisfy or waive earlier dense relation gates.']}
    (out/'receiver.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
