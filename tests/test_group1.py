"""Test group 1: fast tests for add()."""

import unittest

from app.calculator import add


class TestAdd(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(add(1, 2), 3)


if __name__ == "__main__":
    unittest.main()
