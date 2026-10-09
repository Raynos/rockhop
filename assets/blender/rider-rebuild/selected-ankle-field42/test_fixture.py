"""Small regression fixtures for the frozen ray and ranged GLB identity reader."""
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('field42',HERE/'derive.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class Fixtures(unittest.TestCase):
    def test_outward_barycentric_same_leg(self):
        # Exact outward plane x=.5, origin x=.25; opposite leg is excluded.
        p=np.array([[.5,-1,0],[.5,1,0],[.5,0,2],[-.5,-1,0],[-.5,0,2],[-.5,1,0]])
        f=np.array([[0,1,2],[3,4,5]])
        hits=d.ray_rows(np.array([[1.,0,1]]),p,f,np.array([.25,0,0]),np.array([.25,0,2]),1)
        self.assertEqual(hits[0][0],0);np.testing.assert_allclose(hits[0][1],[.25,.25,.5]);self.assertEqual(hits[0][2],.5)

    def test_padded_joint_zero_does_not_erase_positive_weight(self):
        arrays=[np.array([0],'<u4'),np.array([[1,3,2]],'<f4'),np.array([[0,1,0,0]],'u1'),np.array([[.6,.4,0,0]],'<f4'),np.array([0,0,0],'<u4')]
        raw=b'';views=[];accessors=[]
        for a,kind,component in zip(arrays,['SCALAR','VEC3','VEC4','VEC4','SCALAR'],[5125,5126,5121,5126,5125]):
            views.append({'buffer':0,'byteOffset':len(raw),'byteLength':a.nbytes});raw+=a.tobytes()
            accessors.append({'bufferView':len(views)-1,'componentType':component,'count':len(a),'type':kind})
        doc={'buffers':[{'byteLength':len(raw)}],'bufferViews':views,'accessors':accessors,'nodes':[{'name':'jeans','mesh':0,'skin':0},{'name':'root'},{'name':'shin'}],'skins':[{'joints':[1,2]}],'meshes':[{'primitives':[{'attributes':{'_NATIVE_ID':0,'POSITION':1,'JOINTS_0':2,'WEIGHTS_0':3},'indices':4}]}]}
        encoded=json.dumps(doc).encode();encoded+=b' '*((-len(encoded))%4)
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'fixture.glb';path.write_bytes(struct.pack('<5I',0x46546c67,2,28+len(encoded)+len(raw),len(encoded),0x4e4f534a)+encoded+struct.pack('<2I',len(raw),0x004e4942)+raw)
            reader=d.GLB(path)
            try:p,f,w,n=reader.mesh('jeans')
            finally:reader.file.close()
            np.testing.assert_array_equal(p,[[1,-2,3]]);np.testing.assert_array_equal(w,[arrays[3][0,:2]])
            self.assertEqual(n,['root','shin'])

if __name__=='__main__':unittest.main()
