"""Pinned input/proof checks for one inherited native63 source-face bearing."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
PRODUCTION=ROOT/'harness/out/rider-rebuild/selected-boot-native63/native01/production.json'
PRODUCTION_SHA='ba31a23f3489296c97ca02d3e34808cc10e8f869cc1f035d347b148efdba7644'
NATIVE63=PRODUCTION.with_name('UNACCEPTED-constructor62-before-transfer.blend')
NATIVE63_SHA='ba78d4c8ffc5a5c7f51122f0d6f93aa52c7a6afbafb63d7450c2da88d5a5ecc5'
NATIVE34=ROOT/'harness/out/rider-rebuild/selected-production-diagnostic34/bootL01/REJECTED-bootL-before-transfer.blend'
NATIVE34_SHA='a155d13f9b4df422bf851f847c7d392fbd3451c5d20c675093e8913bd05138ad'
ENGINE=ROOT/'assets/blender/rider-rebuild/selected-rider-production25/author.py'
ENGINE_SHA='bc9e03aa6d99eba0d4b5037ceff49424c34ddcde99f0f2aae0f84a5090cbc483'
WITNESS=ROOT/'assets/blender/rider-rebuild/selected-production-family31/witness.py'
WITNESS_SHA='95c7813b503c7d5539b2d7082e14229d484060bacefae294d28160e2c30755d5'
ADMISSION63=ROOT/'assets/blender/rider-rebuild/selected-boot-native63/admission.py'
ADMISSION63_SHA='46a5f5479aaf55c459944a9e4e60fda4347a7b77005e7b3b8b40d393d4b5eccd'
TARGET=15560; OWN=278671; BEARING=278672

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1048576):h.update(block)
    return h.hexdigest()
def pin(path,digest):
    assert sha(path)==digest,('Pinned input changed',str(path))
    return {'path':str(Path(path).relative_to(ROOT)),'sha256':digest}
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def validate(data):
    assert data['status']=='CONFIRMED_EXACT_INHERITED_FACE_NATIVE_BEARING_UNACCEPTED'
    assert data['recipeSHA256']==sha(Path(__file__).with_name('native-proof.py'))
    assert data['proofRecipeSHA256']==sha(__file__)
    assert data['production']==pin(PRODUCTION,PRODUCTION_SHA)
    assert data['native63']['sha256']==NATIVE63_SHA and data['source34']['sha256']==NATIVE34_SHA
    assert data['targetFaceId']==TARGET and data['ownSourceFaceId']==OWN
    assert data['sourceWitnessExact'] is True and data['sourceWitnessUnchangedAfterProbe'] is True
    assert data['raw63BytesUnchanged'] is True and data['source34BytesUnchanged'] is True
    assert data['targetOriginalVertexIds']==[138617,138618,139499]
    assert data['targetOriginalVertexIds']==data['ownSourceOriginalVertexIds']
    assert data['targetPositions']==data['ownSourcePositions'] and data['materialsExact'] is True
    points=np.asarray(data['targetPositions'],dtype=np.float64)
    centroid=points.mean(0);assert centroid.tolist()==data['centroidFloat64']
    assert centroid.astype(np.float32).astype(float).tolist()==data['queryFloat32']
    normal=np.cross(points[1]-points[0],points[2]-points[0]);normal/=np.linalg.norm(normal)
    assert normal.tolist()==data['targetGeometricNormal']==data['ownSourceGeometricNormal']
    assert float(normal@normal)==data['ownSourceNormalDot']>=.25
    near=data['fullBVHNearest'];assert near['sourceFaceId']==BEARING
    pin(ADMISSION63,ADMISSION63_SHA)
    admission=load(ADMISSION63,'proof67_cpu_admission63')
    admission.pin(admission.RECEIPT,admission.RECEIPT_SHA)
    source=admission.array_package(json.loads(admission.RECEIPT.read_text())['sourceArrayPackage'])
    positions=source['positions'].reshape(-1,3).astype(float);faces=source['triangles'].reshape(-1,3)
    assert data['ownSourcePositions']==positions[faces[OWN]].tolist()
    assert near['originalVertexIds']==faces[BEARING].tolist() and near['positions']==positions[faces[BEARING]].tolist()
    bearing=np.asarray(near['positions']);bn=np.cross(bearing[1]-bearing[0],bearing[2]-bearing[0]);bn/=np.linalg.norm(bn)
    assert near['geometricNormal']==bn.tolist() and near['normalDot']==float(normal@bn)
    assert data['materialIndex']==int(source['faceMaterialIds'][OWN])
    assert np.float32(near['normalDot'])==np.float32(.0709218829870224)
    assert np.float32(near['distanceM'])==np.float32(6.51925802230835e-09)
    for row in [near,data['ownFaceBVHNearest']]:
        assert len(row['point'])==3 and np.isfinite(row['point']).all()
        assert np.array_equal(np.asarray(row['point'],np.float32).astype(float),row['point'])
        assert np.isfinite(row['distanceM']) and 0<=row['distanceM']<=.001
    assert data['ownFaceBVHNearest']['sourceFaceId']==OWN
    assert data['ownSourceCentroidDistanceM']==0

def verify(path,reviewed_sha):
    path=Path(path).resolve();assert path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-boot-surface67')
    result=pin(path,reviewed_sha);validate(json.loads(path.read_text()));return result
