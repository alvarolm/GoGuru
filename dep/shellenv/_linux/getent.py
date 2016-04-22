# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import subprocess
from getpass import getuser

from .._types import str_cls, type_name


_login_shells = {}


def get_user_login_shell(username=None):
    """
    Uses getent to get the user's login shell

    :param username:
        A unicode string of the user to get the shell for - None for the
        current user

    :return:
        A unicode string of the user's login shell
    """

    if username is None:
        username = getuser()
        if not isinstance(username, str_cls):
            username = username.decode('utf-8')

    if not isinstance(username, str_cls):
        raise TypeError('username must be a unicode string, not %s' % type_name(username))

    if username not in _login_shells:

        proc = subprocess.Popen(['getent', 'passwd', username], stdout=subprocess.PIPE)

        out = b''
        while proc.poll() is None:
            out += proc.stdout.read()
        out += proc.stdout.read()

        proc.stdout.close()

        line = out.decode('utf-8').strip()
        parts = line.split(':', 6)
        login_shell = parts[6]

        _login_shells[username] = login_shell

    return _login_shells.get(username)
