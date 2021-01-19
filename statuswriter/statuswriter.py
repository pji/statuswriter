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


# Static values.
LN_UP = '\033[A'
LN_DOWN = '\n'
write, flush = sys.stdout.write, sys.stdout.flush

# Status message commands.
INIT = 0x0
MSG = 0x1
PROG = 0x2
KILL = 0xe
END = 0xf


# Utility functions.
def make_progress_frame(total: int) -> tuple[str, str, str]:
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
    """Update the progress bar."""
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
                  term_width: int = 72,
                  hang_indent: int = 0) -> None:
    # Clear old messages. Deques don't support standard slicing, so
    # having to loop through the indices rather than the deque.
    """Update the status messages."""
    for i in range(len(msgs))[::-1]:
        write(f'\r{LN_UP}' + ' ' * len(msgs[i]))

    # Add the new message to the message queue and roll off old
    # messages.
    indent = ' ' * hang_indent
    new_lines = wrap(new_msg, term_width, subsequent_indent=indent)
    for line in new_lines:
        msgs.append(line)
    while len(msgs) > maxlines:
        msgs.popleft()

    # Write the remaining messages to the terminal
    for msg in msgs:
        write(f'\r{msg}\n')


# Public function.
def status_writer(cmd_queue: Queue,
                  title: str,
                  stages: int,
                  maxlines: int = 4,
                  refresh: int = 0) -> None:
    """A coroutine to display status messages and progress to the
    command line.

    :param cmd_queue: A queue used to pass commands to the coroutine.
        Commands are passed as a tuple that contains a command code
        and command arguments. See the table below for the list of
        command codes and arguments.
    :param stages: The number of steps the program will complete before
        it is done. This is used to determine the size of the progress
        bar.
    :param maxlines: (Optional.) The number of messages that will be
        displayed by status_writer. If the maximum number of lines is
        reached, the oldest messages will roll off.
    :param refresh: (Optional.) How frequently status_writer should
        check the command queue for new commands in seconds. If a
        number other than zero is given, the status_writer will update
        the time on the last displayed message to indicate it's waiting
        for a new message. If zero is given, status_writer will check
        continuously and not update the last status.
    :return: None.
    :rtype: None.

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
    msgs = deque()
    for _ in range(maxlines - 1):
        msgs.append('')
    timer_ = timer()
    msg_tmp = '{h:02d}:{m:02d}:{s:02d} {msg}'
    stages_complete = 0
    msg = 'Starting...'
    is_running = False
    was_waiting = False

    while True:
        h, m, s = split_time(next(timer_))
        if not cmd_queue.empty():
            cmd, *args = cmd_queue.get()

            if cmd == INIT:
                prog_bar = make_progress_frame(stages)
                write(f'{title}\n')
                for line in prog_bar:
                    write(f'{line}\n')

                new_msg = msg_tmp.format(h=h, m=m, s=s, msg=msg)
                msgs.append(new_msg)
                for line in msgs:
                    write(f'{line}\n')
                flush()
                is_running = True

            elif cmd == MSG:
                # If the writer has been waiting for an update, remove
                # the waiting message so it doesn't stay in the
                # display, and add the old top message back into the
                # deque to prevent problems when update_status() rolls
                # the messages.
                if was_waiting:
                    msgs.pop()
                    msgs.appendleft(old_msg)
                    was_waiting = False
                msg = args[0]
                new_msg = msg_tmp.format(h=h, m=m, s=s, msg=msg)
                t_width = 72
                h_indent = 9
                update_status(msgs, new_msg, maxlines, t_width, h_indent)
                flush()

            elif cmd == PROG:
                stages_complete += 1
                update_progress(stages, stages_complete, maxlines)
                flush()

            elif cmd == KILL:
                new_msg = msg_tmp.format(h=h, m=m, s=s, msg='Aborting...')
                update_status(msgs, new_msg, maxlines)
                flush()
                raise args[0]

            elif cmd == END:
                break

            else:
                msg = f'Command {cmd} not recognized.'
                raise ValueError(msg)

        # Update the status messages periodically to let the user
        # know how long as elapsed since the monitored application
        # began.
        elif refresh and is_running:
            time.sleep(refresh)

            # If the writer has been waiting for an update, there is
            # already a waiting line in the message deque. Remove it
            # and add back the old top message to make sure the
            # messages roll well.
            if was_waiting:
                msgs.pop()
                msgs.appendleft(old_msg)

            # If we are adding a waiting message to the deque, we need
            # to store the top message in the deque that will roll off
            # due to the waiting message. Otherwise, update_status()
            # won't roll the messages properly.
            else:
                old_msg = msgs[0]

            # Display the waiting message.
            new_msg = msg_tmp.format(h=h, m=m, s=s, msg='Waiting...')
            update_status(msgs, new_msg, maxlines)
            flush()
            was_waiting = True
