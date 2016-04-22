import sys
import locale

from ._types import str_cls, byte_cls, type_name


py2 = sys.version_info < (3,)

# Encoding used for environment variables with ST2
_env_encoding = locale.getpreferredencoding() if sys.platform == 'win32' else 'utf-8'

# Encoding used for fileystem paths with ST2
_fs_encoding = 'mbcs' if sys.platform == 'win32' else 'utf-8'


def env_encode(value):
    """
    Ensures a environment variable name or value is encoded properly to be
    used with subprocess.Popen()

    :param value:
        A unicode string

    :return:
        On Python 3, a unicode string, on Python 2, a byte string
    """

    if not isinstance(value, str_cls):
        raise TypeError('value must be a unicode string, not %s' % type_name(value))

    if not py2:
        return value

    return value.encode(_env_encoding)


def env_decode(value):
    """
    Decodes an environment variable name or value that was returned by
    get_env(for_subprocess=True)

    :param value:
        On Python 3, a unicode string, on Python 2, a byte string

    :return:
        A unicode string
    """

    if not py2:
        if not isinstance(value, str_cls):
            raise TypeError('value must be a unicode string, not %s' % type_name(value))

        return value

    if not isinstance(value, byte_cls):
        raise TypeError('value must be a byte string, not %s' % type_name(value))

    return value.decode(_env_encoding)


def path_encode(value):
    """
    Ensures a filesystem path is encoded properly to be used with
    subprocess.Popen()

    :param value:
        A unicode string

    :return:
        On Python 3, a unicode string, on Python 2, a byte string
    """

    if not isinstance(value, str_cls):
        raise TypeError('value must be a unicode string, not %s' % type_name(value))

    if not py2:
        return value

    return value.encode(_fs_encoding)


def path_decode(value):
    """
    Decodes a filesystem path that was returned by get_env(for_subprocess=True)

    :param value:
        On Python 3, a unicode string, on Python 2, a byte string

    :return:
        A unicode string
    """

    if not py2:
        if not isinstance(value, str_cls):
            raise TypeError('value must be a unicode string, not %s' % type_name(value))

        return value

    if not isinstance(value, byte_cls):
        raise TypeError('value must be a byte string, not %s' % type_name(value))

    return value.decode(_fs_encoding)
