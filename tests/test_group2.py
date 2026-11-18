"""Test group 2: a deliberately slow test, standing in for the real suite."""

import os
import time
import unittest

from app.calculator import multiply


class TestMultiply(unittest.TestCase):
    def test_multiply(self) -> None:
        # Sleep so a run takes long enough to watch, like the real 6-minute suite.
        time.sleep(int(os.environ.get("SLOW_SECONDS", "30")))
        self.assertEqual(multiply(2, 3), 6)


if __name__ == "__main__":
    unittest.main()
