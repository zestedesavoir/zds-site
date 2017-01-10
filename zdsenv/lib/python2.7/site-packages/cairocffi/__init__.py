# coding: utf8
"""
    cairocffi
    ~~~~~~~~~

    CFFI-based cairo bindings for Python. See README for details.

    :copyright: Copyright 2013 by Simon Sapin
    :license: BSD, see LICENSE for details.

"""

import sys
import ctypes.util

from . import constants
from .compat import FileNotFoundError

try:
    from ._ffi import ffi
except ImportError:
    # PyPy < 2.6 compatibility
    from .ffi_build import ffi

VERSION = '0.7.2'
# pycairo compat:
version = '1.10.0'
version_info = (1, 10, 0)


def dlopen(ffi, *names):
    """Try various names for the same library, for different platforms."""
    for name in names:
        for lib_name in [name, 'lib' + name]:
            try:
                path = ctypes.util.find_library(lib_name)
                if path:
                    lib = ffi.dlopen(path)
                    if lib:
                        return lib
            except OSError:
                pass
    raise OSError("dlopen() failed to load a library: %s" % ' / '.join(names))


cairo = dlopen(ffi, 'cairo', 'cairo-2')


class CairoError(Exception):
    """Raised when cairo returns an error status."""
    def __init__(self, message, status):
        super(CairoError, self).__init__(message)
        self.status = status


Error = CairoError  # pycairo compat

STATUS_TO_EXCEPTION = {
    constants.STATUS_NO_MEMORY: MemoryError,
    constants.STATUS_READ_ERROR: IOError,
    constants.STATUS_WRITE_ERROR: IOError,
    constants.STATUS_TEMP_FILE_ERROR: IOError,
    constants.STATUS_FILE_NOT_FOUND: FileNotFoundError,
}


def _check_status(status):
    """Take a cairo status code and raise an exception if/as appropriate."""
    if status != constants.STATUS_SUCCESS:
        exception = STATUS_TO_EXCEPTION.get(status, CairoError)
        status_name = ffi.string(ffi.cast("cairo_status_t", status))
        message = 'cairo returned %s: %s' % (
            status_name, ffi.string(cairo.cairo_status_to_string(status)))
        raise exception(message, status)


def cairo_version():
    """Return the cairo version number as a single integer,
    such as 11208 for ``1.12.8``.
    Major, minor and micro versions are "worth" 10000, 100 and 1 respectively.

    Can be useful as a guard for method not available in older cairo versions::

        if cairo_version() >= 11000:
            surface.set_mime_data('image/jpeg', jpeg_bytes)

    """
    return cairo.cairo_version()


def cairo_version_string():
    """Return the cairo version number as a string, such as ``1.12.8``."""
    return ffi.string(cairo.cairo_version_string()).decode('ascii')


def install_as_pycairo():
    """Install cairocffi so that ``import cairo`` imports it.

    cairoffi’s API is compatible with pycairo as much as possible.

    """
    sys.modules['cairo'] = sys.modules[__name__]


# Implementation is in submodules, but public API is all here.

from .surfaces import (Surface, ImageSurface, PDFSurface, PSSurface,
                       SVGSurface, RecordingSurface, Win32PrintingSurface)
try:
    from .xcb import XCBSurface
except ImportError:
    pass
from .patterns import (Pattern, SolidPattern, SurfacePattern,
                       Gradient, LinearGradient, RadialGradient)
from .fonts import FontFace, ToyFontFace, ScaledFont, FontOptions
from .context import Context
from .matrix import Matrix

from .constants import *
