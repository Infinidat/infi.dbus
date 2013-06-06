import ctypes
import sys

import _dbus_bindings
from libdbus import DBusConnection_p

__all__ = ['DBusPythonMainLoop']

IS_64 = sys.maxint > (1 << 32)
PTR_SIZE = 8 if IS_64 else 4


def deref_mem_addr(addr):
    import struct
    return struct.unpack("P", ctypes.string_at(addr, PTR_SIZE))[0]


def _dbus_bindings_c_api_address():
    PyCObject_Import = ctypes.pythonapi.PyCObject_Import
    PyCObject_Import.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    PyCObject_Import.restype = ctypes.c_ulong
    c_api_address = PyCObject_Import("_dbus_bindings", "_C_API")
    return c_api_address


# BEGIN MAGIC
# The C API is an array composed of an int length field and then method pointers (see dbus-python.h).
# The length field also counts itself (so length will be 3 for 2 members in the array).
# The code in dbus-python.h makes sure that length >= 3 so we do too.
# The API methods are:
# 1. c_dbus_connection = DBusPyConnection_BorrowDBusConnection(PyConnection*)
# 2. mainloop = DBusPyNativeMainLoop_New4(conn_setup_func, serv_setup_func, free_func, data)
c_api_address = _dbus_bindings_c_api_address()
array_len_ptr = deref_mem_addr(c_api_address + PTR_SIZE * 0)
array_len = deref_mem_addr(array_len_ptr) & 0xFFFFFFFF  # int size is 4 bytes, and not always 8 bytes are cleared
if array_len < 3 or array_len > 10:  # 10 is just a safety
    raise Exception("_dbus_bindings._C_API isn't what we expect - are you using an incompatible package?")

DBusPyConnection_BorrowDBusConnection_address = deref_mem_addr(c_api_address + PTR_SIZE * 1)
DBusPyNativeMainLoop_New4_address = deref_mem_addr(c_api_address + PTR_SIZE * 2)

# typedef dbus_bool_t (*_dbus_py_conn_setup_func)(DBusConnection *, void *);
# typedef dbus_bool_t (*_dbus_py_srv_setup_func)(DBusServer *, void *);
# typedef void (*_dbus_py_free_func)(void *);
# extern DBusConnection *DBusPyConnection_BorrowDBusConnection(PyObject *);
# extern PyObject *DBusPyNativeMainLoop_New4(_dbus_py_conn_setup_func,
#                                            _dbus_py_srv_setup_func,
#                                            _dbus_py_free_func,
#                                            void *);
_dbus_py_conn_setup_func = ctypes.CFUNCTYPE(ctypes.c_bool, DBusConnection_p, ctypes.c_void_p)
_dbus_py_srv_setup_func = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
_dbus_py_free_func = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
DBusPyNativeMainLoop_New4_func_ptr = ctypes.CFUNCTYPE(ctypes.py_object, _dbus_py_conn_setup_func,
                                                      _dbus_py_srv_setup_func,
                                                      _dbus_py_free_func, ctypes.c_void_p)

DBusPyNativeMainLoop_New4 = DBusPyNativeMainLoop_New4_func_ptr.from_address(c_api_address + PTR_SIZE * 2)


class DBusPythonMainLoop(object):
    def __init__(self):
        self.native_loop = None

    def conn_setup(self, dbus_connection):
        raise NotImplementedError()

    def srv_setup(self, srv_connection):
        raise NotImplementedError()

    def free(self, data):
        pass

    def create_native_loop(self):
        def conn_setup_wrapper(dbus_connection, data):
            return self.conn_setup(dbus_connection)

        def srv_setup_wrapper(dbus_connection, data):
            return self.srv_setup(dbus_connection)

        def free(_):
            pass

        # We need to keep the thunks so Python's GC won't claim them and then when dbus calls it will SEGV
        self._dbus_py_conn_setup_func_ptr = _dbus_py_conn_setup_func(conn_setup_wrapper)
        self._dbus_py_srv_setup_func_ptr = _dbus_py_srv_setup_func(srv_setup_wrapper)
        self._dbus_py_free_func_ptr = _dbus_py_free_func(free)

        self.native_loop = DBusPyNativeMainLoop_New4(self._dbus_py_conn_setup_func_ptr,
                                                     self._dbus_py_srv_setup_func_ptr,
                                                     self._dbus_py_free_func_ptr, None)
        return self.native_loop

    def set_as_default(self):
        if not self.native_loop:
            self.create_native_loop()

        _dbus_bindings.set_default_main_loop(self.native_loop)
