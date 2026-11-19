"""Test group 1: fast tests for add()."""

import unittest

from app.calculator import add, divide, subtract


class TestAdd(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(add(1, 2), 3)


class TestSubtract(unittest.TestCase):
    def test_subtract(self) -> None:
        self.assertEqual(subtract(5, 3), 2)


class TestDivide(unittest.TestCase):
    def test_divide(self) -> None:
        self.assertEqual(divide(6, 3), 2)


if __name__ == "__main__":
    unittest.main()
