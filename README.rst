============
statuswriter
============

A package for writing basic status messages to a command line
interface, such as the following::

    bash-3.2$ python -m examples.example
    EXAMPLE: a statuswriter example.
    ┌      ┐
    │██████│
    └      ┘
    00:00:08 Stage 3 complete.
    00:00:10 Stage 4 complete.
    00:00:12 Stage 5 complete.
    00:00:12 Example complete.


Why did you write this?
-----------------------
I wrote it largely to get soem experience building and maintaining
Python packages. I tend to prefer CLIs where possible, so I'd written
code similar to this pattern a lot. I figured this would be a good
candidate, and it would simplify a bunch of other code I've written.


How do I run the code?
----------------------
The best ways to get started is to clone this repository to your
local system and take a look at the following file:

*   examples/example.py

This provides a simple example of how to use the statuswriter module.


Is it portable/will it work in all terminals?
---------------------------------------------
It uses an ANSI escape code to position the cursor. I think it should
work in any terminal that supports those. But, I have not tested it
extensively.


Can I install this package from pip?
------------------------------------
Yes, but statuswriter is not currently available on PyPI. You will
need to clone the repository to the system you want to install
statuswriter on and run the following::

    pip install path/to/local/copy

Replace `path/to/local/copy` with the path for your local clone of
this repository.


How do I run the tests?
-----------------------
The `precommit.py` script in the root of the repository will run the
unit tests and a few other tests beside. Otherwise, the unit tests
are written with the standard unittest module, so you can run the
tests with::

    python -m unittest discover tests


How do I contribute?
--------------------
At this time, this is code is really just me exploring and learning.
I've made it available in case it helps anyone else, but I'm not really
intending to turn this into anything other than a personal project.

That said, if other people do find it useful and start using it, I'll
reconsider. If you do use it and see something you want changed or
added, go ahead and open an issue. If anyone ever does that, I'll
figure out how to handle it.
