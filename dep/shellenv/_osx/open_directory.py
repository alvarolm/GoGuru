# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

from getpass import getuser
import ctypes
from ctypes.util import find_library
from ctypes import c_void_p, c_uint32, POINTER, c_bool, byref

from .core_foundation import CoreFoundation, unicode_to_cfstring, cfstring_to_unicode
from .._types import str_cls, type_name

od_path = find_library('OpenDirectory')
OpenDirectory = ctypes.CDLL(od_path, use_errno=True)


ODAttributeType = CoreFoundation.CFStringRef
ODMatchType = c_uint32
ODRecordType = CoreFoundation.CFStringRef

ODSessionRef = c_void_p
ODNodeRef = c_void_p
ODQueryRef = c_void_p
ODRecordRef = c_void_p

OpenDirectory.ODSessionCreate.argtypes = [
    CoreFoundation.CFAllocatorRef,
    CoreFoundation.CFDictionaryRef,
    POINTER(CoreFoundation.CFErrorRef)
]
OpenDirectory.ODSessionCreate.restype = ODSessionRef

OpenDirectory.ODNodeCreateWithName.argtypes = [
    CoreFoundation.CFAllocatorRef,
    ODSessionRef,
    CoreFoundation.CFStringRef,
    POINTER(CoreFoundation.CFErrorRef)
]
OpenDirectory.ODNodeCreateWithName.restype = ODNodeRef

OpenDirectory.ODQueryCreateWithNode.argtypes = [
    CoreFoundation.CFAllocatorRef,
    ODNodeRef,
    CoreFoundation.CFTypeRef,
    ODAttributeType,
    ODMatchType,
    CoreFoundation.CFTypeRef,
    CoreFoundation.CFTypeRef,
    CoreFoundation.CFIndex,
    POINTER(CoreFoundation.CFErrorRef)
]
OpenDirectory.ODQueryCreateWithNode.restype = ODQueryRef

OpenDirectory.ODQueryCopyResults.argtypes = [
    ODQueryRef,
    c_bool,
    POINTER(CoreFoundation.CFErrorRef)
]
OpenDirectory.ODQueryCopyResults.restype = CoreFoundation.CFArrayRef

OpenDirectory.ODRecordCopyValues.argtypes = [
    ODRecordRef,
    ODAttributeType,
    POINTER(CoreFoundation.CFErrorRef)
]
OpenDirectory.ODRecordCopyValues.restype = CoreFoundation.CFArrayRef

kODMatchEqualTo = ODMatchType(0x2001)

kODRecordTypeUsers = ODRecordType.in_dll(OpenDirectory, 'kODRecordTypeUsers')
kODAttributeTypeRecordName = ODAttributeType.in_dll(OpenDirectory, 'kODAttributeTypeRecordName')
kODAttributeTypeUserShell = ODAttributeType.in_dll(OpenDirectory, 'kODAttributeTypeUserShell')


_login_shells = {}


def get_user_login_shell(username=None):
    """
    Uses OS X's OpenDirectory.framework to get the user's login shell

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

        error_ref = CoreFoundation.CFErrorRef()

        session = OpenDirectory.ODSessionCreate(
            CoreFoundation.kCFAllocatorDefault,
            None,
            byref(error_ref)
        )
        if bool(error_ref):
            raise OSError('Error!')

        node = OpenDirectory.ODNodeCreateWithName(
            CoreFoundation.kCFAllocatorDefault,
            session,
            unicode_to_cfstring("/Local/Default"),
            byref(error_ref)
        )
        if bool(error_ref):
            raise OSError('Error!')

        query = OpenDirectory.ODQueryCreateWithNode(
            CoreFoundation.kCFAllocatorDefault,
            node,
            kODRecordTypeUsers,
            kODAttributeTypeRecordName,
            kODMatchEqualTo,
            unicode_to_cfstring(username),
            kODAttributeTypeUserShell,
            1,
            byref(error_ref)
        )
        if bool(error_ref):
            raise OSError('Error!')

        results = OpenDirectory.ODQueryCopyResults(
            query,
            False,
            byref(error_ref)
        )
        if bool(error_ref):
            raise OSError('Error!')

        login_shell = None

        num_results = CoreFoundation.CFArrayGetCount(results)
        if num_results == 1:
            od_record = CoreFoundation.CFArrayGetValueAtIndex(results, 0)
            attributes = OpenDirectory.ODRecordCopyValues(od_record, kODAttributeTypeUserShell, byref(error_ref))
            if bool(error_ref):
                raise OSError('Error!')
            num_attributes = CoreFoundation.CFArrayGetCount(results)
            if num_attributes == 1:
                string_ref = CoreFoundation.CFArrayGetValueAtIndex(attributes, 0)
                login_shell = cfstring_to_unicode(string_ref)

        _login_shells[username] = login_shell

    return _login_shells.get(username)
