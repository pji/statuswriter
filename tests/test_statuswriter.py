"""
test_statuswriter
~~~~~~~~~~~~~~~~~

Unit tests for the statuswriter.statuswriter module.
"""
import unittest as ut

from statuswriter import statuswriter as sw


class SplitTimeTestCase(ut.TestCase):
    def test_splittime(self):
        """Given a duration in seconds, return the number of hours
        minutes, and seconds in that duration as a tuple.
        """
        # Expected value.
        exp = (4, 10, 35)

        # Set up test data and state.
        factors = (3600, 60, 1)
        duration = sum(e * f for e, f in zip(exp, factors))

        # Run test.
        act = sw.split_time(duration)

        # Determine if test passed.
        self.assertEqual(exp, act)
