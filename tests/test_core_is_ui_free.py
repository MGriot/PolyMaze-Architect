import os
import subprocess
import sys
import unittest

CORE = ["topology", "algorithms", "adventure", "settings", "catalog", "geometry", "game_state"]
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")

class TestCoreIsUIFree(unittest.TestCase):
    def test_core_imports_no_ui_toolkit(self):
        code = (
            "import sys\n"
            + "".join(f"import polymaze.core.{m}\n" for m in CORE)
            + "bad = [m for m in sys.modules if m.split('.')[0] in ('kivy', 'arcade', 'pyglet')]\n"
            + "assert not bad, bad\n"
        )
        env = {**os.environ, "PYTHONPATH": SRC}
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
