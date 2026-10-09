"""Light source-adapter check; never imports bpy or opens a native."""
import ast
import importlib.util
from pathlib import Path
p = Path(__file__).with_name('author.py')
spec = importlib.util.spec_from_file_location('allocation46_adapter', p)
adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
source = adapter.adapted_source(); ast.parse(source)
assert "assert len(f) <= spec['full']" not in source
assert "spec['full'] == 8000 and spec['maximumSurfaceErrorM'] == 0.001" in source
assert "report['objects'][name]['transfer'] = engine.transfer(source, target, rig, spec, 'full', config, out)" in source
assert "surface_checks(engine, source, target, spec['maximumSurfaceErrorM'], config['transfer']['minimumNormalDot'], out, save_surface)" in source
assert "assert before == witness.retained(sources, rig)" in source
assert "assert receipt['constructorAncestry']" in source
assert "'sceneBudgetPassed': False" in source
print('PASS: hash-pinned adapter compiles; only soft-count rejection retired; native gates retained')
