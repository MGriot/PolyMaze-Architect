import os
import tempfile
import unittest
from polymaze.core.adventure import AdventureEngine, delete_profile, migrate_legacy_profiles, profile_path

class TestAdventure(unittest.TestCase):
    def test_save_load_delete(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(AdventureEngine.get_profile_info(1, d)["exists"])
            engine = AdventureEngine(1, d)
            engine.process_result(10.0, 50, False, False, 20, 3)
            info = AdventureEngine.get_profile_info(1, d)
            self.assertTrue(info["exists"])
            self.assertEqual(info["total_mazes"], 1)
            self.assertGreater(AdventureEngine(1, d).data["exp"], 0)
            engine.process_reset()
            delete_profile(1, d)
            self.assertFalse(os.path.exists(profile_path(1, d)))

    def test_migrate_legacy_profiles(self):
        with tempfile.TemporaryDirectory() as old, tempfile.TemporaryDirectory() as new:
            AdventureEngine(3, old).save_profile()
            migrate_legacy_profiles(new, legacy_dir=old)
            self.assertTrue(os.path.exists(profile_path(3, new)))
            self.assertFalse(os.path.exists(profile_path(3, old)))

if __name__ == "__main__":
    unittest.main()
