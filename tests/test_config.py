import unittest
import sys
import os

# Put root dir in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent.config as config

class TestConfig(unittest.TestCase):
    def test_config_defaults(self):
        self.assertIsNotNone(config.TARGET_URL)
        self.assertIsNotNone(config.MAX_STEPS)
        self.assertIsInstance(config.HEADLESS, bool)
        self.assertIsNotNone(config.SCREENSHOTS_DIR)

if __name__ == '__main__':
    unittest.main()
