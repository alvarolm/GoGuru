# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

from .._posix import get_shell_env


def get_env(shell=None, for_subprocess=False):
    """
    Uses the user's login shell to fetch the environmental variables that are
    set when a new shell is opened. This is necessary since on OS X, Sublime
    Text is launched from the dock, which does not pick up the user's shell
    environment.

    :param shell:
        The shell to get the env from, if None, uses the current user's login
        shell

    :param for_subprocess:
        If True, and the code is being run in Sublime Text 2, the result will
        be byte strings instead of unicode strings

    :return:
        A 2-element tuple:

         - [0] unicode string shell path
         - [1] env dict with keys and values as unicode strings
    """

    return get_shell_env(shell, for_subprocess=for_subprocess)
