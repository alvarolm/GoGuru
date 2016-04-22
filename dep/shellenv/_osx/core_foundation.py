# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import ctypes
from ctypes.util import find_library
from ctypes import c_void_p, c_char_p, c_uint32, POINTER, c_long


cf_path = find_library('CoreFoundation')
CoreFoundation = ctypes.CDLL(cf_path, use_errno=True)


CFIndex = c_long
CFStringEncoding = c_uint32
CFString = c_void_p
CFArray = c_void_p
CFDictionary = c_void_p
CFError = c_void_p
CFType = c_void_p

CFAllocatorRef = c_void_p
CFStringRef = POINTER(CFString)
CFArrayRef = POINTER(CFArray)
CFDictionaryRef = POINTER(CFDictionary)
CFErrorRef = POINTER(CFError)
CFTypeRef = POINTER(CFType)

CoreFoundation.CFStringGetCStringPtr.argtypes = [CFStringRef, CFStringEncoding]
CoreFoundation.CFStringGetCStringPtr.restype = c_char_p

CoreFoundation.CFStringGetCString.argtypes = [CFStringRef, c_char_p, CFIndex, CFStringEncoding]
CoreFoundation.CFStringGetCString.restype = ctypes.c_bool

CoreFoundation.CFStringCreateWithCString.argtypes = [CFAllocatorRef, c_char_p, CFStringEncoding]
CoreFoundation.CFStringCreateWithCString.restype = CFStringRef

CoreFoundation.CFArrayGetCount.argtypes = [CFArrayRef]
CoreFoundation.CFArrayGetCount.restype = CFIndex

CoreFoundation.CFArrayGetValueAtIndex.argtypes = [CFArrayRef, CFIndex]
CoreFoundation.CFArrayGetValueAtIndex.restype = CFTypeRef

kCFStringEncodingUTF8 = CFStringEncoding(0x08000100)
setattr(CoreFoundation, 'kCFAllocatorDefault', CFAllocatorRef.in_dll(CoreFoundation, 'kCFAllocatorDefault'))
setattr(CoreFoundation, 'CFIndex', CFIndex)
setattr(CoreFoundation, 'CFStringRef', CFStringRef)
setattr(CoreFoundation, 'CFTypeRef', CFTypeRef)
setattr(CoreFoundation, 'CFAllocatorRef', CFAllocatorRef)
setattr(CoreFoundation, 'CFArrayRef', CFArrayRef)
setattr(CoreFoundation, 'CFDictionaryRef', CFDictionaryRef)
setattr(CoreFoundation, 'CFErrorRef', CFErrorRef)


def cfstring_to_unicode(value):
    """
    Creates a python unicode string from a CoreFoundation CFStringRef

    :param value:
        A CFStringRef

    :return:
        A unicode string
    """

    string = CoreFoundation.CFStringGetCStringPtr(
        ctypes.cast(value, CFStringRef),
        kCFStringEncodingUTF8
    )
    if string is None:
        buf = ctypes.create_string_buffer(1024)
        result = CoreFoundation.CFStringGetCString(
            ctypes.cast(value, CFStringRef),
            buf,
            1024,
            kCFStringEncodingUTF8
        )
        if not result:
            raise OSError('Error copying C string from CFStringRef')
        string = buf.value
    if string is not None:
        string = string.decode('utf-8')
    return string


def unicode_to_cfstring(value):
    """
    Creates a CoreFoundation CFStringRef from a python unicode string

    :param value:
        A unicode string

    :return:
        A CFStringRef
    """

    return CoreFoundation.CFStringCreateWithCString(
        CoreFoundation.kCFAllocatorDefault,
        value.encode('utf-8'),
        kCFStringEncodingUTF8
    )
