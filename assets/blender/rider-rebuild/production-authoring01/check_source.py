"""Cheap AST and explicit input pins only; never loads Blender."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block:=handle.read(1024*1024):h.update(block)
    return h.hexdigest()


def pins(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:yield value
        else:
            for child in value.values():yield from pins(child)
    elif isinstance(value,list):
        for child in value:yield from pins(child)


manifest=json.loads((HERE/'inputs.json').read_text())
rows=list(pins(manifest))
for row in rows:assert sha(ROOT/row['path'])==row['sha256'],('Changed pin',row['path'])
for source in HERE.glob('*.py'):
    tree=ast.parse(source.read_text(),filename=str(source))
    if source.name=='assemble.py':
        calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        assert not any('bake' in call or 'export' in call or 'render' in call or 'modifier_apply' in call for call in calls)
assert manifest['canonical']['sha256']=='42fca617ea8d246a6c3e3ca68a90cd3cb5f3ce8b9bb78130e0e2bbd65f605fac'
assert manifest['bodyCandidate']['native']['sha256']=='6c80f6e8acc9b50c1d3cc30c92ca70e65148d84be6315e2100584b6f573953e4'
assert {u['part'] for u in manifest['units']}=={'Hoodie','Jeans','Gloves','Boots'}
report={'accepted':False,'stage':'PRIVATE_EDITABLE_ASSEMBLY_SOURCE_READY_PENDING_EXECUTION',
        'pythonASTPassed':True,'explicitSourcePinsPassed':len(rows),'noHeavyJobExecutedByThisChecker':True,
        'sourceFiles':{str(p.relative_to(ROOT)):sha(p) for p in HERE.iterdir() if p.is_file()},
        'method':['Open explicit joined selected-head/body6c80 as current REJECTED context; one visible body only.',
                  'Compare its75 rest records with canonical42f rig; body and rest remain unchanged.',
                  'Append actual jeans/gloves/boots and compact hoodie with explicit editable lattice/offline-rig dependencies.',
                  'Display fitted original-PBR dense garments; compact targets and source-rest pieces remain toggleable references.',
                  'Place actual original dense hoodie once with frozen fit_point(dense=True) after exact GLB axis intake; no outside finishing.',
                  'Save real-source editable native with explicit source/status notes before any review or rendering.'],
        'replacementContract':'After parent review, explicitly replace bodyCandidate.native/receipt/verdict/status; the candidate must keep canonical75 rest. No head crop or duplicate visible body.',
        'command':['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python-exit-code','1','--python',str((HERE/'assemble.py').relative_to(ROOT)),'--',str((HERE/'inputs.json').relative_to(ROOT)),'harness/out/rider-rebuild/production-authoring01/working01'],
        'runtimeIntakePending':['Exact source object names and dependency closure inside actual native files.',
                                'Exact body-candidate/native75 rest; existing source75 rest and pose before shared modeling modifier rebind.',
                                'Original packed PBR bytes and original dense hoodie importer axes.'],
        'limits':manifest['limits']}
(ROOT/'docs/evidence/rider-rebuild/production-authoring01/source-checkpoint.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('stage','pythonASTPassed','explicitSourcePinsPassed','noHeavyJobExecutedByThisChecker','sourceFiles')},indent=2))
