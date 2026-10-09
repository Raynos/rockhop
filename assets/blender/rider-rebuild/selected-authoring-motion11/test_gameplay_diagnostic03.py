"""Prove diagnostic instrumentation changes only two read-only observer calls."""
import ast
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('gameplay_diagnostic03', HERE/'gameplay_diagnostic03.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FROZEN = (HERE/'gameplay_controls02.py').read_text()
FUNCTION = next(node for node in ast.parse(FROZEN).body if isinstance(node, ast.FunctionDef) and node.name == 'reconstruct')
SOURCE = ast.get_source_segment(FROZEN, FUNCTION)+'\n'


class Observation(unittest.TestCase):
    def test_original_solver_ast_is_unchanged_after_removing_observers(self):
        observed = ast.parse(MODULE.inject_observers(SOURCE))
        calls = [node for node in observed.body[0].body if isinstance(node, ast.Expr)
                 and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                 and node.value.func.id == '_snapshot']
        self.assertEqual([node.value.args[0].value for node in calls], ['before-ik', 'after-ik'])
        observed.body[0].body = [node for node in observed.body[0].body if node not in calls]
        self.assertEqual(ast.dump(observed), ast.dump(ast.parse(SOURCE)))

    def test_changed_or_duplicate_solver_boundary_is_rejected(self):
        with self.assertRaises(AssertionError):
            MODULE.inject_observers(SOURCE.replace('constraint.mute = False', 'constraint.mute = True'))
        with self.assertRaises(AssertionError):
            MODULE.inject_observers(SOURCE+SOURCE)


if __name__ == '__main__':
    unittest.main()
