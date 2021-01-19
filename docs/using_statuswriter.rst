==================
Using statuswriter
==================

This document provides information on how to use the statuswriter
package to display status messages in your command line application.


Quickstart
----------
Want to get started quickly? Here you go.

The following sections assume that you have the current version of
statuswriter installed.


Stand Up the status_writer
~~~~~~~~~~~~~~~~~~~~~~~~~~
The status_writer is designed to be run in a separate thread from
the application it's monitoring. That allows it to update the time
the application has been running while its waiting for an update
from the application.

To do that, two things are required:

*   A :class:queue.Queue object the application can use to pass
    messages to the status_writer,
*   A :class:threading.Thread object to run the status_writer.

The code to do that looks something like this::

    from queue import Queue
    from threading import Thread
    
    import statuswriter as sw
    
    
    # This is the queue to share between the writer and application.
    cmd_queue = Queue()
    
    # Other required arguments.
    app_name = 'SPAM'
    progress_steps = 6
    writer_args = (
        cmd_queue,
        app_name,
        progress_steps,
    )
    
    # Setting up the thread.
    t = Thread(target=sw.status_writer, args=writer_args)
    t.start()

The arguments for status_writer are:

*   cmd_queue: The queue the application will use to send messages
    to the status_writer.
*   title: The application's name.
*   stages: The number of steps the application needs to complete.
*   maxlines: (Optional.) The number of lines of status messages to
    display.
*   refresh: (Optional.) If the cmd_queue is empty, how many seconds
    to wait before checking again.


Initializing the status_writer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
With the status_writer running in a separate thread, your application
can't call it or otherwise interact with it directly to pass messages
to it. So, how to you get it to do anything?

You have to pass it a command through the command queue.

The first command to send is the INIT command to tell the writer to
write the initial display to the terminal. The code to do that should
probably happen right after spinning up the thread with the
status_writer, and it looks something like this::

    # Initialize the status display.
    cmd = (sw.INIT,)
    cmd_queue.put(cmd)

In response, the following should be written to your terminal::

    SPAM
    ┌      ┐
    │░░░░░░│
    └      ┘
    
    
    
    00:00:00 Starting...

A couple of quick points on the commands:

*   The commands are a tuple because some have multiple items.
*   All commands start with a command code.
*   A command code is just an integer, but they have been given
    short names to make them a little more memorable.
*   sw.INIT is the command code to initialize the status_writer.


Providing a Status Message
~~~~~~~~~~~~~~~~~~~~~~~~~~
Once the status_writer has been stood up and initialized, the next
thing you probably want to do is have it display a message. This is
done with the MSG command.

Let's say you want to send a message when you are starting a process
that will take a long time to complete. The code for that might look
like::

    # Send the message to the status display.
    cmd = (sw.MSG, 'Long process started...',)
    cmd_queue.put(cmd)
    
    # Your code does its thing.
    result = long_running_process()

The `long_running_process()` in the example is whatever long
running function you want. The result of that code will look
something like this:

    SPAM
    ┌      ┐
    │░░░░░░│
    └      ┘
    
    
    00:00:00 Starting...
    00:00:01 Long process started...

NOTE: The MSG requires both the command code and a message as a
string. The string should not contain a timestamp. That's handled
by status_writer, which gives the time in hours, minutes, and
seconds since status_writer was stood up.


Updating the Progress Bar
~~~~~~~~~~~~~~~~~~~~~~~~~
The progress bar gives a visual representation of how much the
application has accomplished. This is only useful if the work being
done can be separated into discrete subtasks or steps that can be
tracked by your application. The status_writer doesn't track those
steps for you. It just gives you a way to display how many of them
are done.

The code to update the status bar when a step is complete looks like
the following::

    # Your code does its thing.
    completed_things.append(result)
    
    # Update the progress in the status display.
    cmd_queue((sw.PROG,))
    cmd_queue((sw.MSG, 'Long process result stored.'))

The display will be updated to look like this::

    SPAM
    ┌      ┐
    │█░░░░░│
    └      ┘
    
    00:00:00 Starting...
    00:00:01 Long process started...
    00:15:23 Long process result stored.

Some things to keep in mind when updating the progress bar.

*   The PROG command only updates the progress bar.
*   If you want to display a message for the progress update, you'll
    need to send a separate MSG command.


Terminating the status_writer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Your work is done. You want to close the status_writer, but its in
a separate thread. How do you do that?

You send it the END command.

The code for that looks something like this::

    # Your application does its last thing.
    save_output(completed_things)
    
    # Close the status display.
    cmd_queue.put((sw.MSG, 'SPAM complete.'))
    cmd_queue.put((sw.END,))

Assuming your application has completed all the steps and it updated
status_writer as it did so. The result of that code would look
something like this::

    SPAM
    ┌      ┐
    │██████│
    └      ┘
    01:19:42 Long process result stored.
    01:19:42 Long process started...
    01:35:16 Long process result stored.
    01:35:16 SPAM Complete.
    bash-3.2$

Where the last line is the command prompt for the shell you ran your
application from.

Like the PROG command, END doesn't display a message. If you want a
message to appear marking the completion of the application, you will
need to send that as a MSG command before you send the END command.


Advanced Usage
--------------
This section covers information about statuswriter that might be
useful, but you don't need to get started.


Avoid Clobbering Exception Traces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The status_writer manipulates the location of the cursor in the
terminal, and it runs in a separate thread from your application.
If your application throws an exception and prints the trace,
status_writer will often overwrite some of the text of that trace.

This can be avoided by catching the exception in your application
and passing it to status_writer with the KILL command. The code to
do that looks something like the following::

    # Your code does its thing.
    try:
        result = needs_an_integer(a_string)
    
    # To use KILL, you need to catch the exception.
    except ValueError as e:
        cmd_queue((sw.KILL, e))

The status_writer will then raise the exception passed in the command
and print out the trace safely.

Something to keep in mind: by catching the exception and passing it
to the status_writer in this example, nothing is specifically done to
terminate the application that had the exception in the first place.
So, if you are going to use the KILL command, you probably want to
make sure the application terminates itself after. How this is best
done will depend on the details of your application.

If you want the application and the status_writer to continue to run
after the exception, you probably don't want to use the KILL command.
In those cases, consider using MSG to send a message about the
exception to the status display, and then logging the exception trace
for review after the application completes.
