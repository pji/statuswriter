"""
statuswriter
~~~~~~~~~~~~

A module for writing basic status updates to a command line interface.
"""
from collections import deque
from queue import Queue
import sys
from textwrap import wrap
import time


# Terminal control codes used to move the location of the cursor.
LN_UP = '\033[A'
LN_DOWN = '\n'

# Terminal configuration.
TERMINAL_WIDTH = 79

# The command codes used by status_writer.
INIT = 0x0
MSG = 0x1
PROG = 0x2
KILL = 0xe
END = 0xf

# Message templates.
PREFIX_TEMPLATE = '{h:02d}:{m:02d}:{s:02d} '
MSG_TEMPLATE = '{prefix}{msg}'

# Shortcuts for functions that write to the terminal.
write, flush = sys.stdout.write, sys.stdout.flush


# Utility functions.
def make_progress_frame(total: int) -> tuple[str, str, str]:
    """Create the strings for the initial state of the progress bar.

    :param total: The total number of steps needed to complete the
        monitored application.
    :return: A :class:tuple object.
    :rtype: tuple
    """
    lines = (
        ('\u250c', ' ', '\u2510',),
        ('\u2502', '\u2591', '\u2502',),
        ('\u2514', ' ', '\u2518'),
    )
    return tuple(f'{line[0]}{line[1] * total}{line[2]}' for line in lines)


def split_time(duration: float) -> tuple[int, int, int]:
    """Deremine how many hours, minutes, and seconds are in a number
    of seconds.

    :param duration: The number of seconds.
    :return: A :class:tuple object.
    :rtype: tuple
    """
    s = duration % 60
    duration -= s
    m = duration % 3600
    duration -= m
    h = int(duration / 3600)
    m = int(m / 60)
    s = int(s)
    return h, m, s


def timer():
    """A simple generator for timing a process."""
    t0 = time.time()
    while True:
        yield time.time() - t0


def update_progress(total: int, complete: int, lines:int = 0) -> None:
    """Update the progress bar.

    :param total: The total number of steps before the monitored
        application is complete.
    :param complete: The number of steps that have been completed.
    :param lines: (Optional.) How far below the bottom of the progress
        bar frame the cursor is located when this function is called.
        This allows the cursor to start and end in a known position if
        status messages are displayed below the progress bar.
    :return: None.
    :rtype: NoneType
    """
    incomplete = total - complete
    bar = '\u2588' * complete + '\u2591' * incomplete
    frame_with_bar = f'\u2502{bar}\u2502'

    if lines:
        write(LN_UP * (lines + 2) + '\r')
    write(frame_with_bar)
    if lines:
        write(LN_DOWN * (lines + 2) + '\r')


def update_status(msgs: deque,
                  new_msg: str,
                  maxlines: int = 4,
                  hang_indent: int = 0) -> None:
    """Update the status messages.

    :param msgs: The messages currently displayed in the terminal.
    :param new_msg: The new message to display.
    :param maxlines: (Optional.) The number of lines to display in the
        terminal. This isn't exactly the number of messages because
        long messages can wrap into multiple lines.
    :param term_width: (Optional.) The number of fixed-width characters
        that can fit in a single line in the terminal. Messages longer
        than this are wrapped into multiple lines.
    :param hang_indent: (Optional.) The number of spaces to indent
        wrapped lines.
    :return: None.
    :rtype: NoneType
    """
    # Clear old messages. Deques don't support standard slicing, so
    # having to loop through the indices rather than the deque.
    for i in range(len(msgs))[::-1]:
        write(f'\r{LN_UP}' + ' ' * len(msgs[i]))

    # Add the new message to the message queue and roll off old
    # messages.
    indent = ' ' * hang_indent
    new_lines = wrap(new_msg, TERMINAL_WIDTH, subsequent_indent=indent)
    for line in new_lines:
        msgs.append(line)
    while len(msgs) > maxlines:
        msgs.popleft()

    # Write the remaining messages to the terminal
    for msg in msgs:
        write(f'\r{msg}\n')


# status_writer command functions.
def _init(msgs: deque,
          title: str,
          stages: int,
          maxlines: int,
          timer_: timer) -> None:
    """Write the initial status display."""
    # Write the title.
    write(f'{title}\n')

    # Set up the progress bar.
    if stages:
        prog_bar = make_progress_frame(stages)
        for line in prog_bar:
            write(f'{line}\n')

    # Set up the messages.
    if maxlines:
        h, m, s = split_time(next(timer_))
        prefix = PREFIX_TEMPLATE.format(h=h, m=m, s=s)
        new_msg = MSG_TEMPLATE.format(prefix=prefix, msg='Starting...')
        msgs.append(new_msg)
        for line in msgs:
            write(f'{line}\n')

    # Finish the initialization.
    flush()


def _kill(msgs: deque, ex: Exception, maxlines: int, timer_: timer) -> None:
    """Write an exception to the status display."""
    h, m, s = split_time(next(timer_))
    prefix = PREFIX_TEMPLATE.format(h=h, m=m, s=s)
    new_msg = MSG_TEMPLATE.format(prefix=prefix, msg='Aborting...')
    update_status(msgs, new_msg, maxlines)
    flush()
    raise ex


def _msg(msgs: deque,
         msg: str,
         maxlines: int,
         timer_: timer,
         was_waiting: str) -> None:
    """Write a message to the status display."""
    # If the writer was not configured to write messages,
    # there is no place to put them.
    if not maxlines:
        msg = 'Not configured to allow messages.'
        raise ValueError(msg)

    # If the writer has been waiting for an update, remove
    # the waiting message so it doesn't stay in the
    # display, and add the old top message back into the
    # deque to prevent problems when update_status() rolls
    # the messages.
    if was_waiting:
        msgs.pop()
        msgs.appendleft(was_waiting)

    # Display the message.
    h, m, s = split_time(next(timer_))
    prefix = PREFIX_TEMPLATE.format(h=h, m=m, s=s)
    new_msg = MSG_TEMPLATE.format(prefix=prefix, msg=msg)
    update_status(msgs, new_msg, maxlines, len(prefix))
    flush()


def _prog(stages: int, stages_complete: int, maxlines: int) -> None:
    """Advance the progress bar."""
    if not stages:
        msg = 'Not configured to show a progress bar.'
        raise ValueError(msg)
    stages_complete += 1
    update_progress(stages, stages_complete, maxlines)
    flush()


# Public function.
def status_writer(cmd_queue: Queue,
                  title: str,
                  stages: int = 0,
                  maxlines: int = 4,
                  refresh: int = 0) -> None:
    """A coroutine to display status messages and progress to the
    command line.

    :param cmd_queue: A queue used to pass commands to the coroutine.
        Commands are passed as a tuple that contains a command code
        and command arguments. See the table below for the list of
        command codes and arguments.
    :param stages: (Optional.) The number of steps the program will
        complete before it is done. This is used to determine the size
        of the progress bar. If this is zero, the progress bar will
        not be displayed.
    :param maxlines: (Optional.) The number of messages that will be
        displayed by status_writer. If the maximum number of lines is
        reached, the oldest messages will roll off. If this is set to
        zero, there will be no message display area.
    :param refresh: (Optional.) How frequently status_writer should
        check the command queue for new commands in seconds. If a
        number other than zero is given, the status_writer will update
        the time on the last displayed message to indicate it's waiting
        for a new message. If zero is given, status_writer will check
        continuously and not update the last status.
    :return: None.
    :rtype: NoneType

    Commands
    ========
    The following table gives the available command codes and what
    arguments are needed for that command code.

    ------- ----------- ------------------------------------------------
    Code    Arguments   Description
    ------- ----------- ------------------------------------------------
    INIT    N/A         Write the initial display.
    MSG     message     Update the display with the given message.
    PROG    N/A         Advance the progress bar.
    KILL    exception   Abort the write and raise the given exception.
    END     N/A         Terminate the writer.
    ------- ----------- ------------------------------------------------

    For usage examples, see the example scripts.
    """
    timer_ = timer()

    # Basic configuration for the progress bar.
    stages_complete = 0

    # Basic configuration for messages.
    msgs = deque()
    for _ in range(maxlines - 1):
        msgs.append('')
    msg_tmp = '{h:02d}:{m:02d}:{s:02d} {msg}'

    # Flags that allow the writer to monitor its state.
    is_running = False
    was_waiting = False

    # The application loop.
    while True:
        if not cmd_queue.empty():
            cmd, *args = cmd_queue.get()

            # Initialize the status display in the terminal.
            if cmd == INIT:
                _init(msgs, title, stages, maxlines, timer_)
                is_running = True

            # Write a status message to the status display.
            elif cmd == MSG:
                _msg(msgs, args[0], maxlines, timer_, was_waiting)
                was_waiting = ''

            # Advance the progress bar.
            elif cmd == PROG:
                _prog(stages, stages_complete, maxlines)

            # Abort the status display when an exception is caught in
            # the monitored application, and display the trace of that
            # exception. This is needed because status_writer runs in
            # a separate thread from the application, so it will
            # overwrite the trace printed by the monitored application.
            # It only works if the monitored application catches the
            # exception and sends it to status_writer the the KILL
            # command code.
            elif cmd == KILL:
                _kill(msgs, args[0], maxlines, timer_)

            # Terminate the status_writer.
            elif cmd == END:
                break

            # Raise an exception if an unknown command is received.
            else:
                msg = f'Command {cmd} not recognized.'
                raise ValueError(msg)

        # Update the status messages periodically to let the user
        # know how long as elapsed since the monitored application
        # began.
        elif refresh and is_running and maxlines:
            h, m, s = split_time(next(timer_))
            time.sleep(refresh)

            # If the writer has been waiting for an update, there is
            # already a waiting line in the message deque. Remove it
            # and add back the old top message to make sure the
            # messages roll well.
            if was_waiting:
                msgs.pop()
                msgs.appendleft(was_waiting)

            # If we are adding a waiting message to the deque, we need
            # to store the top message in the deque that will roll off
            # due to the waiting message. Otherwise, update_status()
            # won't roll the messages properly.
            else:
                was_waiting = msgs[0]

            # Display the waiting message.
            new_msg = msg_tmp.format(h=h, m=m, s=s, msg='Waiting...')
            update_status(msgs, new_msg, maxlines)
            flush()
