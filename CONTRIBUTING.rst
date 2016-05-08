============
Contributing
============

Thank you for considering making a contribution to the Growler project!

Growler is a community effort and only will survive with help from people who see the value in
the product and want to see that value grow.
Being released in a standard open source license, it is free for you to use and improve this
software however you see fit, but it'd be great if your improvements  were given back to the
community.

Currently, all community interaction can found on the main project's github page at
https://github.com/pyGrowler/Growler.

Bug Reports
~~~~~~~~~~~

Often the most useful and easiest contribution one can make is to report a bug you encounter
while using the software.
Bug reports are a standard feature in github's 'Issues' project tab.
Before submitting a bug, be sure that it's actually a problem with the core growler package,
and not an issue with an extension.
To provide the most help, please include as much information as you can, including:

* Operation system, python version, growler version
* Any extensions or potentially relavant modules
* Minimum steps required to reproduce the bug
  * Better would be link to a gist or your project

File the issue online with the tag 'bug'.


Contributing Code
~~~~~~~~~~~~~~~~~

Formatting
^^^^^^^^^^

Code comprising Growler is written in python, and follows the pep8_ coding
standard with a few modifications; chiefly, maximum line length is extended
from 80 to 95.
It is still recommended that code be refactored to line length 80.
The length of docstring lines is currently not standardized.
Exceptions for formatting rules may be made in the ``tests/`` directory.

Formating should be checked with the flake8_ utility before commiting.

Testing
^^^^^^^

Testing is done via the pytest_ package.
All tests **MUST** pass before a merge is permitted.
No removal of tests to make tests pass is allowed.
Testing can be done by simply running setup.py with the pytest option,
:code:`./setup.py pytest`, or the standard pytest method :code:`py.test tests/`.

Git
^^^

Features added or bug fixes should be taken care of in a separate git branch.
The name of the git branch is at the discretion of the author, but it is
recommended to clearly state intent (eg: feature-foo, bugfix-infinite-loop,
bugfix-1234).
The feature branches will be merged into the main development branch 'dev' with
a pull request via github.

Upon a version release, a commit to the dev branch updating the version and date
in the metadata file ``growler/__meta__.py`` is made with the commit message
'Version X.Y.Z'.
A non-fastforwarding merge is made into the master branch with the 'short' part
of commit message as 'vX.Y.Z' and the 'long' part as summary of changes in this
merge (the changelog).

To make feature merging clean, it is **mandatory** that you rebase the feature branch to
at least the most recent release, and is *recommended* to rebase to the head
of the development branch, or an appropriate commit nearer the head.

Growler authors are encouraged to do many small commits, each one with a clear
intent.
To this end, it is advised to minimize the number of files changed in each git commit.
Often, this involves changing a single class, and adding/changing the corresponding
test file so that all tests pass.
It is not required that all tests pass in every commit of a feature branch, but it
is a good habbit to form, and easily shows which tests check the new code.

Growler uses a convention of prepending the class/module/file name changed to the
beginning of commit messages.
This, again, encourages minimal file changes and clearly identifies the intent of the commit.
Also, it increases reading the ``git log``.

Foul-language/rude/unhelpful commit messages **will not be accepted**.

Emojis, while cute, are *discouraged* in commit messages.


Contributing Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Documentation is provided via standard python docstrings in the source code and
a separate documentation repository containing instructions to build the full
documentation.
This repository is external to minimize the size of the code repository and
separate contributions to code vs docs.

It is encouraged to start each new sentence on a new line.
The purpose of this is to simplify file diffs.
Changing one word in a sentence could potentially modify many lines of
length-limited docstrings; we want the git diff to show only what REALLY changed.

As with contributing code, it is encouraged to limit the number of files changed
per commit to a small handful.
There are probably more exceptions to this rule with docstrings, as you could
probably file 10 puctuation mistakes in 10 files; commiting all ten files would
be acceptable, along with a general commit message of 'Typo fixes in various
docstrings.'
Adding a few paragraphs to the docstring of 10 class constructors would not be
appropriate for one commit, unless they all had the same basic raison d'être.

-----------

Thanks again for your involement in the Growler project.
Happy Coding!


.. _pep8: http://pep8.org/
.. _flake8: https://pypi.python.org/pypi/flake8
.. _pytest: https://pypi.python.org/pypi/pytest
