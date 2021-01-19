"""
statuswriter
~~~~~~~~~~~~

A module for writing basic status updates to a command line interface.
"""
from collections import deque
from queue import Queue
import sys
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
    t0 = time.time()
    while True:
        yield time.time() - t0


def update_progress(total: int, complete: int, lines:int = 0) -> None:
    incomplete = total - complete
    bar = '\u2588' * complete + '\u2591' * incomplete
    frame_with_bar = f'\u2502{bar}\u2502'

    if lines:
        write(LN_UP * (lines + 2) + '\r')
    write(frame_with_bar)
    if lines:
        write(LN_DOWN * (lines + 2) + '\r')


def update_status(msgs: deque, new_msg: str, maxlines: int = 4) -> None:
    # Clear old messages. Deques don't support standard slicing, so
    # having to loop through the indices rather than the deque.
    for i in range(len(msgs))[::-1]:
        write(f'\r{LN_UP}' + ' ' * len(msgs[i]))

    # Add the new message to the message queue and roll off old
    # messages.
    msgs.append(new_msg)
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
    msgs = deque()
    for _ in range(maxlines - 1):
        msgs.append('')
    timer_ = timer()
    msg_tmp = '{h:02d}:{m:02d}:{s:02d} {msg}'
    stages_complete = 0
    msg = 'Starting...'
    is_running = False

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
                msg = args[0]
                new_msg = msg_tmp.format(h=h, m=m, s=s, msg=msg)
                update_status(msgs, new_msg, maxlines)
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

        elif refresh and is_running:
            time.sleep(refresh)
            msgs.pop()
            msgs.appendleft('')
            new_msg = msg_tmp.format(h=h, m=m, s=s, msg=msg)
            update_status(msgs, new_msg, maxlines)
            flush()

