"""Numeric certificate regressions only; no synthetic character/appearance assets."""
import unittest
from qualified_assembly_preflight import validate_frame, validate_digit_controls, validate_sole_certificate, validate_body_operator, STALE_DRIVER_KEYS

class SourceCertificateGuards(unittest.TestCase):
    def setUp(self):
        self.frame = [[1.,0,0,.2],[0,1.,0,.3],[0,0,1.,.4],[0,0,0,1]]

    def test_proper_rigid_frame(self):
        self.assertEqual(validate_frame(self.frame), [[1,0,0],[0,1,0],[0,0,1]])

    def test_scaled_frame_is_not_proper_socket(self):
        self.frame[0][0]=1.01
        with self.assertRaises(AssertionError): validate_frame(self.frame)

    def test_positive_determinant_shear_is_rejected(self):
        self.frame[0][1]=.01
        with self.assertRaises(AssertionError): validate_frame(self.frame)

    def test_reflected_and_nonfinite_frames_fail(self):
        self.frame[0][0]=-1
        with self.assertRaises(AssertionError): validate_frame(self.frame)
        self.frame[0][0]=float('nan')
        with self.assertRaises(AssertionError): validate_frame(self.frame)

    def test_projective_frame_is_not_native_socket(self):
        self.frame[3][0]=.01
        with self.assertRaises(AssertionError): validate_frame(self.frame)

    def controls(self):
        spec={'jointNames':{},'hands':{}}
        receipt={'rigNativeSHA256':'measured-new-rig-identity','qualification':'INDEPENDENT_SMALL_SKIN_CURL_SIGN_VERIFIED_MOVING_ART_PENDING','digitFlex':{}}
        motion={'native':{'sha256':'measured-new-rig-identity'},'exactSourceGeometryIDsAndOutsideFields':True,'smallCurlSkinSigns':[],'movingFields':[]}
        for side in ('left','right'):
            digits={name:[name+str(i)+side for i in range(3)] for name in ('thumb','index','middle','ring','pinky')}
            spec['hands'][side]={'digits':digits}
            spec['jointNames'].update({name:name for chain in digits.values() for name in chain})
            receipt['digitFlex'][side]={name:{'axisLocal':[0.,0,1.],'maxRadians':.8} for chain in digits.values() for name in chain}
            native_side='L' if side=='left' else 'R'
            motion['smallCurlSkinSigns'].extend({'side':native_side,'digit':digit,'smallCurlMeanSkinDisplacementTowardPalmM':.001} for digit in digits)
            motion['movingFields'].append({'pose':native_side+'-whole-hand-curl','nativeFourVsLinearEvaluatorMaximumM':1e-7,
                'rotations':[{'joint':name,'axisLocal':[0.,0,1.],'radians':.5} for name in receipt['digitFlex'][side]]})
        return receipt,spec,motion

    def test_complete_numeric_control_certificate(self):
        receipt,spec,motion=self.controls()
        validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)

    def test_digit_source_identity_and_missing_control_fail(self):
        receipt,spec,motion=self.controls()
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'old-rig-identity',spec,motion)
        receipt['digitFlex']['left'].pop('thumb0left')
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)

    def test_invalid_axis_and_claimed_gate_fail(self):
        receipt,spec,motion=self.controls();receipt['digitFlex']['right']['index1right']['axisLocal']=[0,0,2]
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)
        receipt,spec,motion=self.controls();receipt['gates']={'jointRangeValidated':True}
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)


    def test_measured_sign_and_exact_control_motion_required(self):
        receipt,spec,motion=self.controls();motion['smallCurlSkinSigns'][0]['smallCurlMeanSkinDisplacementTowardPalmM']=-.001
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)
        receipt,spec,motion=self.controls();motion['movingFields'][0]['rotations'][0]['axisLocal']=[1.,0,0]
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)

    def test_measured_motion_must_fit_declared_envelope_and_native_parity(self):
        receipt,spec,motion=self.controls();motion['movingFields'][0]['rotations'][0]['radians']=1.5
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)
        receipt,spec,motion=self.controls();motion['movingFields'][0]['nativeFourVsLinearEvaluatorMaximumM']=4e-6
        with self.assertRaises(AssertionError): validate_digit_controls(receipt,'measured-new-rig-identity',spec,motion)

    def test_actual_old_adaptive_parameters_are_stale_for_changed_rig(self):
        import json
        from pathlib import Path
        source=Path(__file__).resolve().parents[4]/'docs/evidence/rider-rebuild/runtime02/combined04-adaptive20-pose.json'
        driver=json.loads(source.read_text())['driver']
        self.assertEqual(STALE_DRIVER_KEYS.intersection(driver), {'maxSpineFlexRadians','palmForwardBike','palmNormalBike'})

    def sole_metadata(self):
        import hashlib
        from pathlib import Path
        source=Path(__file__).resolve().parents[4]/'harness/out/rider-rebuild/selected-boot02/selected-boot-checkpoint.blend'
        if not source.exists(): self.skipTest('Ignored actual original boot native absent; no generated asset substitutes')
        native={'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
        patch={'domain':'actual-outer-sole','triangleRows':[0],'barycentrics':[[.2,.3,.5]],
               'pointNative':[.2,.3,.4],'outwardNormalNative':[0,0,-1],'forwardTangentNative':[0,1,0]}
        support={'object':'ActualSelectedBoot.R','nativeFrame':self.frame,'boneLengthM':.02,'supportPatch':patch,
                 'outwardNormalInFrame':[0,0,-1],'forwardTangentInFrame':[0,1,0]}
        receipt={**support,'native':native,'gates':{'actualOuterSolePatchValidated':True,'properFrameValidated':True}}
        return support,receipt,{'native':native}

    def test_sole_metadata_binds_same_native_and_declared_patch(self):
        # Certificate shape only; actual patch geometry is separately checked
        # inside the Blender assembler. This is not boot art/fit qualification.
        support,receipt,unit=self.sole_metadata()
        validate_sole_certificate('R',support,receipt,unit)

    def test_sole_native_identity_and_patch_mismatch_fail(self):
        import copy
        support,receipt,unit=self.sole_metadata()
        changed=copy.deepcopy(receipt);changed['native']['sha256']='0'*64
        with self.assertRaises(AssertionError): validate_sole_certificate('R',support,changed,unit)
        changed=copy.deepcopy(receipt);changed['supportPatch']['triangleRows']=[1]
        with self.assertRaises(AssertionError): validate_sole_certificate('R',support,changed,unit)

    def test_sole_frame_must_match_measured_patch_axes(self):
        support,receipt,unit=self.sole_metadata()
        support['outwardNormalInFrame']=[0,0,1]
        with self.assertRaises(AssertionError): validate_sole_certificate('R',support,receipt,unit)

    def body_operator(self):
        # Operator certificate shape, never a synthetic model or geometry pass.
        native={'path':'/measured/native.blend','sha256':'a'*64}
        arm={'index':1,'name':'actual-armature','type':'ARMATURE','options':{
            'show_viewport':True,'show_render':True,'use_deform_preserve_volume':False,
            'use_vertex_groups':True,'use_bone_envelopes':False,'use_multi_modifier':False,
            'vertex_group':'','invert_vertex_group':False}}
        tri={'index':0,'name':'actual-static-triangulation','type':'TRIANGULATE','options':{
            'show_viewport':True,'show_render':True,'quad_method':'BEAUTY','ngon_method':'BEAUTY','min_vertices':4}}
        receipt={'native':native,'exactSourceGeometryIDsAndOutsideFields':True,
            'exportTriangleWindingAndOriginalPolygonLoopCornerLineageExact':True,
            'nativeTriangulationLineage':{'everyTriangleAndUVCornerHasOriginalPolygonLoopAncestry':True,
                'triangles':2,'sourcePolygons':1,'sourceUVLayer':'measured-source-uv'},
            'bodyModifierOperators':[tri,arm]}
        return receipt,native

    def test_static_triangulation_operator_is_preserved(self):
        receipt,native=self.body_operator()
        self.assertEqual(validate_body_operator(receipt,native,receipt['bodyModifierOperators']),receipt['bodyModifierOperators'])

    def test_static_triangulation_order_and_options_must_match(self):
        import copy
        receipt,native=self.body_operator();actual=copy.deepcopy(receipt['bodyModifierOperators'])
        actual[0]['options']['quad_method']='FIXED'
        with self.assertRaises(AssertionError): validate_body_operator(receipt,native,actual)
        with self.assertRaises(AssertionError): validate_body_operator(receipt,native,list(reversed(receipt['bodyModifierOperators'])))

    def test_unsupported_body_operator_and_dqs_fail(self):
        receipt,native=self.body_operator();receipt['bodyModifierOperators'][0]['type']='SUBSURF'
        with self.assertRaises(AssertionError): validate_body_operator(receipt,native)
        receipt,native=self.body_operator();receipt['bodyModifierOperators'][1]['options']['use_deform_preserve_volume']=True
        with self.assertRaises(AssertionError): validate_body_operator(receipt,native)

    def test_static_operator_requires_current_source_and_corner_proof(self):
        receipt,native=self.body_operator();native={**native,'sha256':'b'*64}
        with self.assertRaises(AssertionError): validate_body_operator(receipt,native)
        receipt,native=self.body_operator();receipt['nativeTriangulationLineage']['everyTriangleAndUVCornerHasOriginalPolygonLoopAncestry']=False
        with self.assertRaises(AssertionError): validate_body_operator(receipt,native)

if __name__=='__main__': unittest.main()
