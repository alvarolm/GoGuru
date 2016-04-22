# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import os
import sys

from .._posix import get_shell_env
from .getent import get_user_login_shell


def get_env(shell=None, for_subprocess=False):
    """
    Fetches the environmental variables for the current user. This is necessary
    since depending on how the sublime_text binary is launched, the process will
    not get the environment a user has in the terminal.

    Because sublime_text may have been launched from the terminal, the env from
    the shell specified and python's os.environ are compared to see which
    contains more information.

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

    # If we should compare the login shell env and os.environ
    # to see which seems to contain the correct information
    compare = False

    login_shell = get_user_login_shell()

    if shell is None:
        shell = login_shell
        compare = True
    elif shell == login_shell:
        compare = True

    if not compare:
        return get_shell_env(shell, for_subprocess=for_subprocess)

    _, login_env = get_shell_env(shell, for_subprocess=for_subprocess)

    if sys.version_info < (3,) and for_subprocess:
        shell = shell.encode('utf-8')

    if len(login_env) >= len(os.environ):
        return (shell, login_env)

    if sys.version_info < (3,) and not for_subprocess:
        values = {}
        for key, value in os.environ.items():
            values[key.decode('utf-8', 'replace')] = value.decode('utf-8', 'replace')
    else:
        values = dict(os.environ)

    return (shell, values)
