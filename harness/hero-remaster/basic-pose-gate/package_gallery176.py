"""Package the exact pushed review source without PAX metadata overhead.

Use a fresh --out path. Both compressed and expanded archives must fit the cap.
This CPU recipe does not alter source, images or movies and needs no GPU.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,tarfile
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
R=Path('/Users/raynos/projects/games/rockhop');S=R/'harness/out/hero-remaster/rider-review-site';E=R/'docs/evidence/hero-remaster/one-rider-v2/gallery176'
b=json.loads((E/'build.json').read_text());m=json.loads((E/'source-manifest.json').read_text())
assert subprocess.check_output(['git','branch','--show-current'],cwd=S,text=True).strip()=='main'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==b['sourceCommit']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S,text=True).strip()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(S/'dist/index.html')==m['htmlSHA256']
for name,h in m['oldMediaHashes'].items():assert sha(S/'dist'/name)==h
assert sha(S/'dist'/m['addedMedia']['relativePath'])==m['addedMedia']['SHA256']
out=Path(a.out).resolve();assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
with tarfile.open(out,'w:gz',format=tarfile.USTAR_FORMAT)as t:
 t.add(S/'.openai/hosting.json',arcname='.openai/hosting.json');t.add(S/'dist',arcname='dist')
with out.open('rb')as f:f.seek(-4,2);expanded=struct.unpack('<I',f.read())[0]
assert out.stat().st_size<268435456 and expanded<268435456
r={'sourceCommit':b['sourceCommit'],'archive':str(out),'archiveSHA256':sha(out),'compressedBytes':out.stat().st_size,'expandedTarBytes':expanded,'limitBytes':268435456,'format':'USTAR with original file contents; no PAX headers','mediaFilesPreserved':81,'addedMovieBytes':144949,'limits':'Packaging only. Push/source/save/deployment and hosted playback must be verified separately.'}
out.with_suffix(out.suffix+'.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
