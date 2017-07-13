import diff
import unittest

class BadInput(unittest.TestCase):
    def testNegative(self):
        """Diff should fail with negative values"""
        self.assertRaises(diff.OutOfRangeError, diff.diff, -10,'test')

    def testInteger(self):
        """Diff should fail with non-integer values"""
        self.assertRaises(diff.NotIntegerError, diff.diff, 0.5,'test')

    def testInvalidName(self):
        """Diff should fail with invalid filenames"""
        self.assertRaises(diff.InvalidFilename, diff.diff, 0,'')

class BadOutput(unittest.TestCase):
    def testNegative(self):
        """Diff should never output negative values"""
        result = diff.diff(0,'test')
        self.assertFalse(result < 0)

if __name__ == "__main__":
    unittest.main()
