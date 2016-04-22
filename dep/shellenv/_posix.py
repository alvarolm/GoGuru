# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import re
import os
import sys
import subprocess

from ._types import str_cls, type_name

if sys.platform == 'darwin':
    from ._osx.open_directory import get_user_login_shell
else:
    from ._linux.getent import get_user_login_shell


_envs = {'bytes': {}, 'unicode': {}}


def get_shell_env(shell=None, for_subprocess=False):
    """
    Fetches the environmental variables that are set when a new shell is opened.

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

    if shell is not None and not isinstance(shell, str_cls):
        raise TypeError('shell must be a unicode string, not %s' % type_name(shell))

    if shell is None:
        shell = get_user_login_shell()
    _, shell_name = shell.rsplit('/', 1)

    output_type = 'bytes' if sys.version_info < (3,) and for_subprocess else 'unicode'

    if shell not in _envs[output_type]:
        args = [shell, '-l']
        # For bash we invoke interactively or else ~/.bashrc is not
        # loaded, and many distros and users use .bashrc for env vars
        if shell_name == 'bash':
            args.append('-i')
        env_proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        stdout, _ = env_proc.communicate(b'/usr/bin/env\n')

        _envs[output_type][shell] = {}

        entries = re.split(b'\n(?=\\w+=)', stdout.strip())
        for entry in entries:
            if entry == b'':
                continue
            parts = entry.split(b'=', 1)
            if len(parts) < 2:
                continue
            name = parts[0]
            value = parts[1]
            if output_type == 'unicode':
                name = name.decode('utf-8', 'replace')
                value = value.decode('utf-8', 'replace')
            _envs[output_type][shell][name] = value

    if output_type == 'bytes':
        shell = shell.encode('utf-8')

    return (shell, _envs[output_type][shell].copy())
