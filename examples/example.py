"""
example
~~~~~~~

A simple example for how to use the statuswriter module.
"""
from queue import Queue
from threading import Thread
from time import sleep

import statuswriter as sw


# Set up the status_writer.
status = Queue()
title = 'EXAMPLE: a statuswriter example.'
progress_stages = 6
maxlines = 4
refresh = 1
args = (status, title, progress_stages, maxlines, refresh)

# Start the status_writer in a separate thread.
t = Thread(target=sw.status_writer, args=args)
t.start()
status.put((sw.INIT,))

# Run your application, sending commands to status_writer through
# the queue.
for i in range(progress_stages):
    sleep(2)
    status.put((sw.PROG,))
    status.put((sw.MSG, f'Stage {i} complete.'))
status.put((sw.MSG, 'Example complete.'))
status.put((sw.END,))
