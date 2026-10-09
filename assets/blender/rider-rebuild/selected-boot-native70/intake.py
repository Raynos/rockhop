"""Exact actual67 joint receipt and actual68 native proof admission."""
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'assets/blender/rider-rebuild'
ADMISSION63=BASE/'selected-boot-native63/admission.py'
ADMISSION63_SHA='46a5f5479aaf55c459944a9e4e60fda4347a7b77005e7b3b8b40d393d4b5eccd'

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

# The generic exact-array verifier is frozen; actual62-specific admission is unused.
import hashlib
assert hashlib.sha256(ADMISSION63.read_bytes()).hexdigest()==ADMISSION63_SHA
frozen=load(ADMISSION63,'native70_frozen_admission63')
sha=frozen.sha;pin=frozen.pin;arrays=frozen.array_package
RECEIPT=ROOT/'harness/out/rider-rebuild/selected-boot-surface67/candidate01/constructor.json'
RECEIPT_SHA='14b4f68aee996befc290a5cfc135029b5a7e5b6933d42398e3eae1a2347eb487'
CANDIDATE_SHA='d86bf09de091e17ee7ccdbdd2bea00636861bf50a620c38510c36ba5a2a07bde'
CONSTRUCTOR67=BASE/'selected-boot-surface67/construct.mjs'
CONSTRUCTOR67_SHA='e04871f48c80819f6bc2b62b61d9c473708fc2f30cf6bb1a12b63491c1e586d4'
CLOSURE67_SHA='63994435703329695c7a7553cbd64de678a088ae5edba1682f78306caf676c8b'
SURFACE67_SHA='4c68f83bfd76f2fedb2cec42de6cfef4ee8d1cca74f3959cffa813521778d07a'
PROOF68=ROOT/'harness/out/rider-rebuild/selected-boot-witness68/proof01/diagnostic.json'
PROOF68_SHA='9373ab042e0899ec5366a92386fd775dc82837c511345f8110917c26632b15ae'
WITNESS68=BASE/'selected-boot-witness68/witness68.py'
WITNESS68_SHA='b52d42550d1c16367095424f207a0303e1f80d4452747eaf6f3941e8298b912e'
OUTPUT_BASE=ROOT/'harness/out/rider-rebuild/selected-boot-native70'


def verify_proof():
    pin(WITNESS68,WITNESS68_SHA)
    validator=load(WITNESS68,'native70_frozen_witness68')
    return validator.verify(PROOF68,PROOF68_SHA)


def metadata(receipt):
    assert receipt['status']=='UNACCEPTED_SCENE_BUDGET_PENDING' and receipt['acceptedArt'] is False
    assert receipt['candidateAttempts']==5 and receipt['fixedPoint']['complete'] is True
    assert receipt['fixedPoint']['minimumNormalDot']==.25
    assert receipt['recipeSHA256']==CONSTRUCTOR67_SHA
    assert receipt['closureRecipeSHA256']==CLOSURE67_SHA and receipt['surfaceRecipeSHA256']==SURFACE67_SHA
    pin(CONSTRUCTOR67,CONSTRUCTOR67_SHA);pin(CONSTRUCTOR67.with_name('closure.mjs'),CLOSURE67_SHA);pin(CONSTRUCTOR67.with_name('surface.mjs'),SURFACE67_SHA)
    for key in ['constructorAncestry','fanConstructorAncestry','fixedPointConstructorAncestry62','initialFaceDiagnosis','exhaustiveNative63Preflight']:
        row=receipt[key];pin(ROOT/row['path'],row['sha256'])
    census=json.loads((ROOT/receipt['census']['path']).read_text());pin(ROOT/receipt['census']['path'],frozen.CENSUS35_SHA)
    pin(frozen.POLICY46,frozen.POLICY46_SHA);policy=json.loads(frozen.POLICY46.read_text())
    for key in ['policy','originalTopology','attributes','attributeWeights']:
        assert receipt[key]==policy['topology' if key=='originalTopology' else key]
    assert receipt['censusSourcePins']==census['sourcePins'] and receipt['sourceArrayPackage']==census['sourceArrayPackage']
    assert receipt['groupNames']==census['sourceArrayPackage']['groupNames']
    assert receipt['sourceVertices']==census['sourceVertices'] and receipt['sourceTriangles']==census['sourceTriangles']
    assert receipt['simplificationTargetIsSoft'] is True and receipt['simplificationTargetTriangles']==8000
    assert receipt['sceneBudgetPassed'] is False and receipt['allocationPassed'] is False
    for key in ['bakeCompleted','movingReviewPassed','devicePassed']:assert receipt[key] is False
    for key in ['sourceInputBytesUnchanged','exactOriginalPositionsAndNamedFields','nativeFaceAncestryProofRequired']:assert receipt[key] is True
    assert receipt['nativeFaceAncestryPolicyChanged'] is False
    assert receipt['geometricQualification']=='CPU_VERTEX_AND_FACE_PASSED_NATIVE_GEOMETRY_PENDING'
    assert receipt['candidate']['sha256']==CANDIDATE_SHA
    rows=receipt['fixedPoint']['iterations'];assert len(rows)==5
    for key in ['candidate','returnedOriginalIndices','fanProtection','fanRetention','targetTriangles','targetVertices',
                'approximateCombinedErrorM','vertexNormalCensus','faceCentroidCensus','faceCentroidArrays']:
        assert receipt[key]==rows[-1][key]
    assert receipt['finalFanProtection']==rows[-1]['protection']
    for index,row in enumerate(rows):
        final=index==len(rows)-1;assert row['iteration']==index+1
        assert row['status']==('CPU_VERTEX_AND_FACE_FIXED_POINT_UNACCEPTED' if final else 'REQUIRES_MORE_SOURCE_FAN_CONSTRAINTS')
        v=row['vertexNormalCensus'];f=row['faceCentroidCensus'];retained=row['fanRetention']
        assert v['threshold']==.25 and v['undefinedNormals']==0
        assert v['verticesExamined']==row['targetVertices'] and v['trianglesExamined']==row['targetTriangles']
        assert v['failingVertices']==len(v['failures']) and v['passed']==(not v['failures'])
        assert np.isfinite(v['minimumNormalDot']) and v['passed']==(v['minimumNormalDot']>=.25)
        assert f['samples']==row['targetTriangles']==f['exactInheritedFaces']+f['newFaces']
        assert f['minimumNormalDotRequired']==.25 and f['maximumDistanceRequiredM']==.001
        assert np.isfinite(f['minimumNormalDot']) and np.isfinite(f['maximumDistanceM'])
        assert f['failingFaces']==len(f['failures']) and f['passed']==(not f['failures'])
        assert f['passed']==(f['minimumNormalDot']>=.25 and f['maximumDistanceM']<=.001)
        assert (v['passed'] and f['passed']) is final
        assert retained['passed'] is True
        assert retained['missingCount']==retained['unexpectedCount']==retained['duplicateFaces']==0
        assert retained['requiredSourceFaces']==retained['actualProtectedIncidentFaces']==row['fanProtection']['exactRequiredSourceFaces']


def failure_centers(row):
    centers=set()
    for failure in row['vertexNormalCensus']['failures']:
        assert failure['normalDot'] is None or failure['normalDot']<.25;centers.add(failure['originalVertexId'])
    for failure in row['faceCentroidCensus']['failures']:
        assert failure['normalDot']<.25 or failure['distanceM']>.001
        assert failure['exactInheritedSourceFace'] is False
        centers.update(failure['originalVertexIds']);centers.update(failure['sourceBearingOriginalVertexIds'])
    return centers


def admit(receipt_path,reviewed_sha,out):
    receipt_path=Path(receipt_path).resolve();out=Path(out).resolve()
    assert receipt_path==RECEIPT and reviewed_sha==RECEIPT_SHA,'Exact actual67 receipt required'
    assert out.is_relative_to(OUTPUT_BASE) and out!=OUTPUT_BASE and not out.exists(),'Fresh native70 output required'
    receipt_pin=pin(receipt_path,reviewed_sha);proof=verify_proof();receipt=json.loads(receipt_path.read_text());metadata(receipt)
    source=arrays(receipt['sourceArrayPackage']);prior=None;checks=[]
    initial=arrays(receipt['initialConstraintArrays'])
    expected=set(initial['centerOriginalVertexIds'].tolist())|set(receipt['initialCPUAddedFanCenters'])
    for index,row in enumerate(receipt['fixedPoint']['iterations']):
        for key in ['candidate','returnedOriginalIndices','protection','faceCentroidArrays']:
            assert (ROOT/row[key]['path']).resolve().parent==RECEIPT.parent
        candidate=arrays(row['candidate']);returned=arrays(row['returnedOriginalIndices']);protection=arrays(row['protection'])
        checked=frozen.verify_arrays(source,candidate,returned,protection,dict(row,groupNames=receipt['groupNames']))
        centers=set(protection['centerOriginalVertexIds'].tolist());assert centers==expected,'Joint fan growth changed'
        if prior is not None:
            for key in ['centerOriginalVertexIds','lockedOriginalVertexIds','requiredSourceFaceIds']:
                assert np.isin(prior[key],protection[key]).all()
            previous_edges=set(map(tuple,prior['requiredEdgesOriginal'].reshape(-1,2)))
            assert previous_edges<=set(map(tuple,protection['requiredEdgesOriginal'].reshape(-1,2)))
        assert np.array_equal(candidate['lockedOriginalVertexIds'],protection['lockedOriginalVertexIds'])
        assert np.array_equal(candidate['requiredEdgesOriginal'],protection['requiredEdgesOriginal'])
        declared=row['fanProtection']
        assert declared['protectedCenters']==checked['protectedCenters'] and declared['originalFanVertices']==checked['protectedVertices']
        assert declared['originalFanEdges']==checked['protectedEdges'] and declared['exactRequiredSourceFaces']==checked['exactOrientedSourceFaces']
        face=arrays(row['faceCentroidArrays']);assert set(face)=={'sourceFaceId','distanceM','normalDot'}
        assert all(len(values)==row['targetTriangles'] for values in face.values())
        assert np.isfinite(face['normalDot']).all() and np.isfinite(face['distanceM']).all()
        assert np.all(face['sourceFaceId']>=0) and np.all(face['sourceFaceId']<receipt['sourceTriangles'])
        assert np.all(face['distanceM']>=0)
        failed=np.flatnonzero((face['normalDot']<.25)|(face['distanceM']>.001))
        assert failed.tolist()==[failure['targetFaceId'] for failure in row['faceCentroidCensus']['failures']]
        if index<4:
            added=failure_centers(row)-centers;assert added and sorted(added)==row['addedOriginalFanCenters']
            expected=centers|added;assert row['nextProtectedCenters']==len(expected)
        prior=protection;checks.append(dict(checked,iteration=index+1,completeVertexCensus=row['vertexNormalCensus']['passed'],completeFaceCensus=row['faceCentroidCensus']['passed']))
    return {'status':'EXACT_ACTUAL67_AND_NATIVE68_ADMITTED_NATIVE_QUALIFICATION_PENDING','acceptedArt':False,
        'recipeSHA256':sha(__file__),'constructor':receipt_pin,'actualProof68':proof,
        'candidateSHA256':CANDIDATE_SHA,'iterationVerification':checks,'sceneBudgetPassed':False,
        'limits':'Admission only. Native70 keeps frozen shape/skin and new-face nearest/surface gates. Left boot only; no bilateral32 bake, atlas, contact, motion, device or scene-allocation acceptance.'}
