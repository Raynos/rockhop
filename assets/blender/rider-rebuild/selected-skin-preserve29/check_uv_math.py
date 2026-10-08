import importlib.util
import json
from pathlib import Path
import numpy as np
p = Path(__file__).with_name('uv_math.py'); spec = importlib.util.spec_from_file_location('skin29_uv_fixture', p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
s = np.array([[[0,0],[1,0],[.5,.5]],[[1,0],[1,1],[.5,.5]],[[1,1],[0,1],[.5,.5]],[[0,1],[0,0],[.5,.5]]], dtype=np.float32)
t = np.array([[[0,0],[1,0],[1,1]],[[0,0],[1,1],[0,1]]], dtype=np.float32)
assert m.compare(m.chart(s,[1]*4),m.chart(t,[1]*2))['exactSelectedChartBoundaries']
for u, mats in [(t*.5,[1,1]),(t,[1,2]),(t[:,[0,2,1]],[1,1])]:
 try: m.compare(m.chart(s,[1]*4),m.chart(u,mats))
 except AssertionError: pass
 else: raise AssertionError('Changed UV layout/material/orientation was accepted')
assert 2*m.rgba8_mip_bytes(1024,1024)+m.rgba8_mip_bytes(256,256) == 11534332
print(json.dumps({'passed':True,'actualNativeRun':False,'fixtures':['Retriangulation preserves exact original UV chart footprint','Scaling, material reassignment and winding changes rejected','Complete RGBA8 mip arithmetic'],'selectedSkinMiB':11534332/1048576}))
