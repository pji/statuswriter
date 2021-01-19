"""
test_statuswriter
~~~~~~~~~~~~~~~~~

Unit tests for the statuswriter.statuswriter module.
"""
from collections import deque
from queue import Queue
import unittest as ut
from unittest.mock import call, patch

from statuswriter import statuswriter as sw


# Test classes.
class MakeProgressFrameTestCase(ut.TestCase):
    def test_make_frame(self):
        """Given the total number of progress steps,
        make_progress_frame should return a tuple that
        contains the top, middle, and bottom of the
        progress frame.
        """
        # Expected value.
        exp = (
            '┌      ┐',
            '│░░░░░░│',
            '└      ┘',
        )

        # Set up test data and state.
        total = 6

        # Run test.
        act = sw.make_progress_frame(total)

        # Determine if test passed.
        self.assertTupleEqual(exp, act)


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


class StatusWriter(ut.TestCase):
    def setUp(self):
        self.title = 'SPAM: the Eggening'
        self.progress_frame = (
            '┌      ┐',
            '│░░░░░░│',
            '└      ┘',
        )
        self.msg_tmp = '{:02d}:{:02d}:{:02d} {}'
        self.init_write_calls = [
            call(self.title + '\n'),
            call(self.progress_frame[0] + '\n'),
            call(self.progress_frame[1] + '\n'),
            call(self.progress_frame[2] + '\n'),
            call('\n'),
            call(self.msg_tmp.format(0, 0, 0, 'Starting...') + '\n'),
        ]
        self.init_flush_calls = [
            call(),
        ]

    @patch('statuswriter.statuswriter.write')
    @patch('statuswriter.statuswriter.flush')
    @patch('time.time', return_value=1000)
    def test_initialize(self, _, mock_flush, mock_write):
        """Given a deque for messages, a title and a maximum number of
        messages to display, status_writer should write the initial
        status display to the terminal.
        """
        # Expected value.
        exp_write = self.init_write_calls
        exp_flush = self.init_flush_calls

        # Set up test data and status.
        cmd_queue = Queue()
        cmd_queue.put((sw.INIT,))
        cmd_queue.put((sw.END,))
        title = self.title
        stages = 6
        maxlines = 2

        # Run test.
        _ = sw.status_writer(cmd_queue, title, stages, maxlines)

        # Extract actual results.
        act_write = mock_write.mock_calls
        act_flush = mock_flush.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp_write, act_write)
        self.assertListEqual(exp_flush, act_flush)

    @patch('statuswriter.statuswriter.write')
    @patch('statuswriter.statuswriter.flush')
    @patch('time.time', side_effect=[1000, 1000, 4661, 4661])
    def test_kill(self, _, mock_flush, mock_write):
        """When a message command is sent to the message queue, the
        message should be written to the terminal.
        """
        # Expected value.
        exp_write = [
            *self.init_write_calls,
            call('\r\033[A' + ' ' * 20),
            call('\r\033[A' + ''),
            call('\r' + self.msg_tmp.format(0, 0, 0, 'Starting...') + '\n'),
            call('\r' + self.msg_tmp.format(1, 1, 1, 'Aborting...') + '\n')
        ]
        exp_flush = [
            *self.init_flush_calls,
            call(),
        ]
        exp_exception = ValueError
        exp_msg = 'sausages'

        # Set up test data and status.
        cmd_queue = Queue()
        cmd_queue.put((sw.INIT,))
        cmd_queue.put((sw.KILL, exp_exception(exp_msg)))
        cmd_queue.put((sw.END,))
        title = self.title
        stages = 6
        maxlines = 2

        # Run test.
        with self.assertRaisesRegex(exp_exception, exp_msg):
            _ = sw.status_writer(cmd_queue, title, stages, maxlines)

        # Extract actual results.
        act_write = mock_write.mock_calls
        act_flush = mock_flush.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp_write, act_write)
        self.assertListEqual(exp_flush, act_flush)

    @patch('statuswriter.statuswriter.write')
    @patch('statuswriter.statuswriter.flush')
    @patch('time.time', side_effect=[1000, 1000, 4661, 4661])
    def test_message(self, _, mock_flush, mock_write):
        """When a message command is sent to the message queue, the
        message should be written to the terminal.
        """
        # Expected value.
        exp_write = [
            *self.init_write_calls,
            call('\r\033[A' + ' ' * 20),
            call('\r\033[A' + ''),
            call('\r' + self.msg_tmp.format(0, 0, 0, 'Starting...') + '\n'),
            call('\r' + self.msg_tmp.format(1, 1, 1, 'bacon') + '\n')
        ]
        exp_flush = [
            *self.init_flush_calls,
            call(),
        ]

        # Set up test data and status.
        cmd_queue = Queue()
        cmd_queue.put((sw.INIT,))
        cmd_queue.put((sw.MSG, 'bacon'))
        cmd_queue.put((sw.END,))
        title = self.title
        stages = 6
        maxlines = 2

        # Run test.
        _ = sw.status_writer(cmd_queue, title, stages, maxlines)

        # Extract actual results.
        act_write = mock_write.mock_calls
        act_flush = mock_flush.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp_write, act_write)
        self.assertListEqual(exp_flush, act_flush)

    @patch('statuswriter.statuswriter.write')
    @patch('statuswriter.statuswriter.flush')
    @patch('time.time', return_value=1000)
    def test_progress(self, _, mock_flush, mock_write):
        """When a progress command is sent to the message queue, the
        progress bar should be updated in the terminal
        """
        # Expected value.
        exp_write = [
            *self.init_write_calls,
            call('\033[A\033[A\033[A\033[A\r'),
            call('│█░░░░░│'),
            call('\n\n\n\n\r'),
        ]
        exp_flush = [
            *self.init_flush_calls,
            call(),
        ]

        # Set up test data and status.
        cmd_queue = Queue()
        cmd_queue.put((sw.INIT,))
        cmd_queue.put((sw.PROG,))
        cmd_queue.put((sw.END,))
        title = self.title
        stages = 6
        maxlines = 2

        # Run test.
        _ = sw.status_writer(cmd_queue, title, stages, maxlines)

        # Extract actual results.
        act_write = mock_write.mock_calls
        act_flush = mock_flush.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp_write, act_write)
        self.assertListEqual(exp_flush, act_flush)


class TimerTestCase(ut.TestCase):
    @patch('time.time', side_effect=[1000, 1050])
    def test_time_event(self, mock_time):
        """After initialization, timer should return the number of
        seconds since the timer was initialized.
        """
        # Expected value.
        exp = 50

        # Set up test data and state.
        timer = sw.timer()

        # Run test.
        act = next(timer)

        # Determine if test passed.
        self.assertEqual(exp, act)


class UpdateStatusTestCase(ut.TestCase):
    @patch('statuswriter.statuswriter.write')
    def test_update(self, mock_write):
        """Given an empty deque of status messages and a new message
        not in the queue, add the new message to the deque, and write
        the new message to the terminal.
        """
        # Expected value.
        exp = [
            call('\r' + 'spam' + '\n'),
        ]
        exp_msgs = deque(['spam',])

        # Set up test data and state.
        act_msgs = deque()
        new = 'spam'

        # Run test.
        sw.update_status(act_msgs, new)

        # Extract test result.
        act = mock_write.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp, act)
        self.assertEqual(exp_msgs, act_msgs)

    @patch('statuswriter.statuswriter.write')
    def test_update_with_old_messages(self, mock_write):
        """Given a deque of status messages and a new message not yet
        in the queue, write those messages to the terminal.
        """
        # Expected value.
        exp = [
            call('\r\033[A' + '     '),
            call('\r\033[A' + '    '),
            call('\r' + 'eggs' + '\n'),
            call('\r' + 'bacon' + '\n'),
            call('\r' + 'spam' + '\n'),
        ]
        exp_msgs = deque([
            'eggs',
            'bacon',
            'spam',
        ])

        # Set up test data and state.
        act_msgs = deque([
            'eggs',
            'bacon',
        ])
        new = 'spam'
        maxlines = 3

        # Run test.
        sw.update_status(act_msgs, new, maxlines)

        # Extract test result.
        act = mock_write.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp, act)
        self.assertEqual(exp_msgs, act_msgs)

    @patch('statuswriter.statuswriter.write')
    def test_update_with_roll_off(self, mock_write):
        """Given a deque of status messages, write those messages to
        the terminal.
        """
        # Expected value.
        exp = [
            call('\r\033[A' + '     '),
            call('\r\033[A' + '    '),
            call('\r' + 'bacon' + '\n'),
            call('\r' + 'spam' + '\n'),
        ]
        exp_msgs = deque([
            'bacon',
            'spam',
        ])

        # Set up test data and state.
        act_msgs = deque([
            'eggs',
            'bacon',
        ])
        new = 'spam'
        maxlines = 2

        # Run test.
        sw.update_status(act_msgs, new, maxlines)

        # Extract test result.
        act = mock_write.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp, act)
        self.assertEqual(exp_msgs, act_msgs)


class UpdateProgressTestCase(ut.TestCase):
    @patch('statuswriter.statuswriter.write')
    def test_update(self, mock_write):
        """Given the total number of steps and the number of completed
        steps, write a bar that shows the progress.
        """
        # Expected value.
        exp = [
            call('│██░░░░│'),
        ]

        # Set up test data and state.
        total = 6
        complete = 2

        # Run test.
        sw.update_progress(total, complete)

        # Extract actual result.
        act = mock_write.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp, act)

    @patch('statuswriter.statuswriter.write')
    def test_update_with_lines(self, mock_write):
        """Given the total number of steps, the number of completed
        steps, and the number of lines the bar is located above the
        current cursor location, write a bar that shows the progress.
        """
        # Expected value.
        exp = [
            call('\033[A' * 4 + '\r'),
            call('│██░░░░│'),
            call('\n' * 4 + '\r'),
        ]

        # Set up test data and state.
        total = 6
        complete = 2
        lines = 2

        # Run test.
        sw.update_progress(total, complete, lines)

        # Extract actual result.
        act = mock_write.mock_calls

        # Determine if test passed.
        self.assertListEqual(exp, act)
