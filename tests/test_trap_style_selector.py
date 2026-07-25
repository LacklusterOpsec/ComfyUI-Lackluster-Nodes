import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("trap_style_selector", ROOT / "trap_style_selector.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_selector_returns_expected_text():
    node = module.TrapStyleSelectorNode()
    result = node.generate("Phonk-Style Aggressive Trap")

    assert result == ("• Phonk-Style Aggressive Trap — Cowbells, Memphis rap chops, drift scene",)
