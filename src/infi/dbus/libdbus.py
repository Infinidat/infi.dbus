import ctypes

__all__ = ['DBusError', 'DBUS_BUS_SESSION', 'DBUS_BUS_SYSTEM', 'DBUS_BUS_STARTER',
           'DBUS_WATCH_READABLE', 'DBUS_WATCH_WRITABLE', 'DBUS_WATCH_ERROR', 'DBUS_WATCH_HANGUP',
           'DBusConnection_p', 'dbus_bus_get_id', 'dbus_connection_set_watch_functions',
           'dbus_connection_set_timeout_functions', 'dbus_connection_set_wakeup_main_function',
           'dbus_connection_get_unix_fd', 'dbus_connection_get_socket',
           'dbus_connection_ref', 'dbus_connection_unref', 'dbus_watch_get_enabled', 'dbus_watch_get_flags',
           'dbus_watch_get_unix_fd', 'dbus_watch_get_socket', 'dbus_watch_handle', 'dbus_timeout_get_enabled',
           'dbus_timeout_handle', 'dbus_timeout_get_interval', 'dbus_connection_dispatch',
           'dbus_connection_get_dispatch_status', 'dbus_timeout_set_data', 'dbus_timeout_get_data',
           'dbus_watch_get_data', 'dbus_watch_set_data']

LIBC = ctypes.CDLL("libc.so.6")
DBUS = ctypes.CDLL("libdbus-1.so.3")


class free_c_char_p(ctypes.c_uint):
    def __str__(self):
        return ctypes.string_at(self.value)

    def __del__(self):
        LIBC.free(self.value)


# dbus-shared.h
DBUS_BUS_SESSION = 0
DBUS_BUS_SYSTEM = 1
DBUS_BUS_STARTER = 2


# dbus-errors.h
class DBusError(ctypes.Structure):
    _fields_ = [("name", ctypes.c_char_p),
                ("message", ctypes.c_char_p),
                ("dummy", ctypes.c_uint),
                ("padding1", ctypes.c_void_p)]
DBusError_p = ctypes.POINTER(DBusError)


# dbus-memory.h
DBusFreeFunction = ctypes.CFUNCTYPE(None, ctypes.c_void_p)


# dbus-connection.h

# typedef enum
# {
#   DBUS_WATCH_READABLE = 1 << 0, /**< As in POLLIN */
#   DBUS_WATCH_WRITABLE = 1 << 1, /**< As in POLLOUT */
#   DBUS_WATCH_ERROR    = 1 << 2, /**< As in POLLERR (can't watch for
#                                  *   this, but can be present in
#                                  *   current state passed to
#                                  *   dbus_watch_handle()).
#                                  */
#   DBUS_WATCH_HANGUP   = 1 << 3  /**< As in POLLHUP (can't watch for
#                                  *   it, but can be present in current
#                                  *   state passed to
#                                  *   dbus_watch_handle()).
#                                  */
#   /* Internal to libdbus, there is also _DBUS_WATCH_NVAL in dbus-watch.h */
# } DBusWatchFlags;
DBUS_WATCH_READABLE = 1 << 0
DBUS_WATCH_WRITABLE = 1 << 1
DBUS_WATCH_ERROR = 1 << 2
DBUS_WATCH_HANGUP = 1 << 3

# /**
#  * Indicates the status of incoming data on a #DBusConnection. This determines whether
#  * dbus_connection_dispatch() needs to be called.
#  */
# typedef enum
# {
#   DBUS_DISPATCH_DATA_REMAINS,  /**< There is more data to potentially convert to messages. */
#   DBUS_DISPATCH_COMPLETE,      /**< All currently available data has been processed. */
#   DBUS_DISPATCH_NEED_MEMORY    /**< More memory is needed to continue. */
# } DBusDispatchStatus;
DBUS_DISPATCH_DATA_REMAINS = 0
DBUS_DISPATCH_COMPLETE = 1
DBUS_DISPATCH_NEED_MEMORY = 2


# forward declaration
class DBusConnection(ctypes.Structure):
    pass
DBusConnection_p = ctypes.POINTER(DBusConnection)


class DBusWatch(ctypes.Structure):
    pass
DBusWatch_p = ctypes.POINTER(DBusWatch)


class DBusTimeout(ctypes.Structure):
    pass
DBusTimeout_p = ctypes.POINTER(DBusTimeout)

# typedef dbus_bool_t (* DBusAddTimeoutFunction)     (DBusTimeout    *timeout,
#                                                     void           *data);
# typedef void        (* DBusTimeoutToggledFunction) (DBusTimeout    *timeout,
#                                                     void           *data);
# typedef void        (* DBusRemoveTimeoutFunction)  (DBusTimeout    *timeout,
#                                                     void           *data);
# Since they're all the same let's call it DBusTimeoutCallbackFunction and be done with it...
DBusAddTimeoutCallbackFunction = ctypes.CFUNCTYPE(ctypes.c_bool, DBusTimeout_p, ctypes.py_object)
DBusRemoveOrToggleTimeoutCallbackFunction = ctypes.CFUNCTYPE(None, DBusTimeout_p, ctypes.py_object)

# typedef void        (* DBusAddWatchFunction)   (DBusWatch      *watch,
#                                                 void           *data);
# typedef void        (* DBusWatchToggledFunction)   (DBusWatch      *watch,
#                                                     void           *data);
# typedef void        (* DBusRemoveWatchFunction)    (DBusWatch      *watch,
#                                                     void           *data);
# Since they're all the same let's call it DBusWatchCallbackFunction and be done with it...
DBusAddWatchCallbackFunction = ctypes.CFUNCTYPE(ctypes.c_bool, DBusWatch_p, ctypes.py_object)
DBusRemoveOrToggleWatchCallbackFunction = ctypes.CFUNCTYPE(None, DBusWatch_p, ctypes.py_object)

# typedef void        (* DBusWakeupMainFunction)     (void           *data);
DBusWakeupMainFunction = ctypes.CFUNCTYPE(None, ctypes.py_object)

#
# dbus_bool_t        dbus_connection_set_watch_functions          (DBusConnection             *connection,
#                                                                  DBusAddWatchFunction        add_function,
#                                                                  DBusRemoveWatchFunction     remove_function,
#                                                                  DBusWatchToggledFunction    toggled_function,
#                                                                  void                       *data,
#                                                                  DBusFreeFunction            free_data_function);
DBUS.dbus_connection_set_watch_functions.argtypes = [DBusConnection_p, DBusAddWatchCallbackFunction,
                                                     DBusRemoveOrToggleWatchCallbackFunction,
                                                     DBusRemoveOrToggleWatchCallbackFunction,
                                                     ctypes.py_object, DBusFreeFunction]
DBUS.dbus_connection_set_watch_functions.restype = ctypes.c_bool

# DBusConnection*    dbus_connection_ref                          (DBusConnection             *connection);
# void               dbus_connection_unref                        (DBusConnection             *connection);
DBUS.dbus_connection_ref.argtypes = [DBusConnection_p]
DBUS.dbus_connection_ref.restype = DBusConnection_p
DBUS.dbus_connection_unref.argtypes = [DBusConnection_p]
DBUS.dbus_connection_unref.restype = None

# dbus_bool_t dbus_connection_get_unix_fd            (DBusConnection              *connection,
#                                                     int                         *fd);
# dbus_bool_t dbus_connection_get_socket             (DBusConnection              *connection,
#                                                     int                         *fd);
DBUS.dbus_connection_get_unix_fd.argtypes = [DBusConnection_p, ctypes.POINTER(ctypes.c_int)]
DBUS.dbus_connection_get_unix_fd.restype = ctypes.c_bool
DBUS.dbus_connection_get_socket.argtypes = [DBusConnection_p, ctypes.POINTER(ctypes.c_int)]
DBUS.dbus_connection_get_socket.restype = ctypes.c_bool

# dbus_bool_t  dbus_watch_get_enabled (DBusWatch        *watch);
DBUS.dbus_watch_get_enabled.argtypes = [DBusWatch_p]
DBUS.dbus_watch_get_enabled.restype = ctypes.c_bool

# unsigned int dbus_watch_get_flags   (DBusWatch        *watch);
DBUS.dbus_watch_get_flags.argtypes = [DBusWatch_p]
DBUS.dbus_watch_get_flags.restype = ctypes.c_uint

# int          dbus_watch_get_unix_fd (DBusWatch        *watch);
DBUS.dbus_watch_get_unix_fd.argtypes = [DBusWatch_p]
DBUS.dbus_watch_get_unix_fd.restype = ctypes.c_int

# int          dbus_watch_get_socket  (DBusWatch        *watch);
DBUS.dbus_watch_get_socket.argtypes = [DBusWatch_p]
DBUS.dbus_watch_get_socket.restype = ctypes.c_int

# dbus_bool_t  dbus_watch_handle      (DBusWatch        *watch,
#                                      unsigned int      flags);
DBUS.dbus_watch_handle.argtypes = [DBusWatch_p, ctypes.c_uint]
DBUS.dbus_watch_handle.restype = ctypes.c_bool

# void*        dbus_watch_get_data    (DBusWatch        *watch);
# void         dbus_watch_set_data    (DBusWatch        *watch,
#                                      void             *data,
#                                      DBusFreeFunction  free_data_function);
DBUS.dbus_watch_get_data.argtypes = [DBusWatch_p]
DBUS.dbus_watch_get_data.restype = ctypes.c_void_p
DBUS.dbus_watch_set_data.argtypes = [DBusWatch_p, ctypes.py_object, DBusFreeFunction]
DBUS.dbus_watch_set_data.restype = None

# dbus_bool_t        dbus_connection_set_timeout_functions        (DBusConnection             *connection,
#                                                                  DBusAddTimeoutFunction      add_function,
#                                                                  DBusRemoveTimeoutFunction   remove_function,
#                                                                  DBusTimeoutToggledFunction  toggled_function,
#                                                                  void                       *data,
#                                                                  DBusFreeFunction            free_data_function);
DBUS.dbus_connection_set_timeout_functions.argtypes = [DBusConnection_p, DBusAddTimeoutCallbackFunction,
                                                       DBusRemoveOrToggleTimeoutCallbackFunction,
                                                       DBusRemoveOrToggleTimeoutCallbackFunction,
                                                       ctypes.py_object, DBusFreeFunction]
DBUS.dbus_connection_set_timeout_functions.restype = ctypes.c_bool

# DBusDispatchStatus dbus_connection_dispatch                     (DBusConnection             *connection);
DBUS.dbus_connection_dispatch.argtypes = [DBusConnection_p]
DBUS.dbus_connection_dispatch.restype = ctypes.c_int

# DBusDispatchStatus dbus_connection_get_dispatch_status          (DBusConnection             *connection);
DBUS.dbus_connection_get_dispatch_status.argtypes = [DBusConnection_p]
DBUS.dbus_connection_get_dispatch_status.restype = ctypes.c_int

# dbus_bool_t  dbus_timeout_get_enabled (DBusTimeout        *timeout);
DBUS.dbus_timeout_get_enabled.argtypes = [DBusTimeout_p]
DBUS.dbus_timeout_get_enabled.restype = ctypes.c_bool

# dbus_bool_t dbus_timeout_handle       (DBusTimeout      *timeout);
DBUS.dbus_timeout_handle.argtypes = [DBusTimeout_p]
DBUS.dbus_timeout_handle.restype = ctypes.c_bool

# int         dbus_timeout_get_interval (DBusTimeout      *timeout);
DBUS.dbus_timeout_get_interval.argtypes = [DBusTimeout_p]
DBUS.dbus_timeout_get_interval.restype = ctypes.c_int

# void*       dbus_timeout_get_data     (DBusTimeout      *timeout);
# void        dbus_timeout_set_data     (DBusTimeout      *timeout,
#                                        void             *data,
#                                        DBusFreeFunction  free_data_function);
DBUS.dbus_timeout_get_data.argtypes = [DBusTimeout_p]
DBUS.dbus_timeout_get_data.restype = ctypes.c_void_p
DBUS.dbus_timeout_set_data.argtypes = [DBusTimeout_p, ctypes.py_object, DBusFreeFunction]
DBUS.dbus_timeout_set_data.restype = None

# void               dbus_connection_set_wakeup_main_function     (DBusConnection             *connection,
#                                                                  DBusWakeupMainFunction      wakeup_main_function,
#                                                                  void                       *data,
#                                                                  DBusFreeFunction            free_data_function);
DBUS.dbus_connection_set_wakeup_main_function.argtypes = [DBusConnection_p, DBusWakeupMainFunction, ctypes.py_object,
                                                          DBusFreeFunction]
DBUS.dbus_connection_set_wakeup_main_function.restype = None

# dbus-bus.h
DBUS.dbus_bus_get.argtypes = [ctypes.c_int, DBusError_p]
DBUS.dbus_bus_get.restype = DBusConnection_p

DBUS.dbus_bus_get_id.argtypes = [DBusConnection_p, DBusError_p]
DBUS.dbus_bus_get_id.restype = free_c_char_p

# Python API
Py_IncRef = ctypes.pythonapi.Py_IncRef
Py_IncRef.argtypes = [ctypes.py_object]
Py_IncRef.restype = None

Py_DecRef = ctypes.pythonapi.Py_DecRef
Py_DecRef.argtypes = [ctypes.py_object]
Py_DecRef.restype = None

## Wrappers

# DEBUG only:
def __refcount(obj):
    addr = id(obj)
    return ctypes.c_long.from_address(addr).value - 1


def dbus_bus_get_id(conn, error):
    assert isinstance(conn, DBusConnection_p)
    assert isinstance(error, (DBusError, DBusError_p))
    return str(DBUS.dbus_bus_get_id(conn, error))


def _register_py_object(obj):
    py_obj = ctypes.py_object(obj)
    Py_IncRef(py_obj)
    return obj, py_obj


def _free_py_object(ptr):
    if ptr is not None:
        Py_DecRef(ctypes.cast(ptr, ctypes.py_object))
_c_free_py_object = DBusFreeFunction(_free_py_object)


class _WatchOrTimeoutCallbackKeeper(object):
    def __init__(self, c_add_func_type, c_remove_or_toggle_func_type, add_func, remove_func, toggled_func, data):
        self.add_func = add_func
        self.remove_func = remove_func
        self.toggled_func = toggled_func
        self.data = data
        self.c_add_func = c_add_func_type(self.add_cb)
        self.c_remove_func = c_remove_or_toggle_func_type(self.remove_cb)
        self.c_toggled_func = c_remove_or_toggle_func_type(self.toggled_cb)

    def add_cb(self, dbus_obj, _):
        return self.add_func(dbus_obj, self.data)

    def remove_cb(self, dbus_obj, _):
        self.remove_func(dbus_obj, self.data)

    def toggled_cb(self, dbus_obj, _):
        self.toggled_func(dbus_obj, self.data)


def _new_watch_or_timeout_callback_keeper(c_add_func_type, c_remove_or_toggle_func_type, add_func, remove_func,
                                          toggled_func, data):
    return _register_py_object(_WatchOrTimeoutCallbackKeeper(c_add_func_type, c_remove_or_toggle_func_type,
                                                             add_func, remove_func, toggled_func, data))


def dbus_connection_set_watch_functions(conn, add_watch_func, remove_watch_func, watch_toggled_func, data):
    assert isinstance(conn, DBusConnection_p)
    assert callable(add_watch_func) and callable(remove_watch_func) and callable(watch_toggled_func)

    cb_keeper, py_obj = _new_watch_or_timeout_callback_keeper(DBusAddWatchCallbackFunction,
                                                              DBusRemoveOrToggleWatchCallbackFunction,
                                                              add_watch_func, remove_watch_func, watch_toggled_func,
                                                              data)
    res = DBUS.dbus_connection_set_watch_functions(conn, cb_keeper.c_add_func, cb_keeper.c_remove_func,
                                                   cb_keeper.c_toggled_func, py_obj, _c_free_py_object)
    return res


def dbus_connection_set_timeout_functions(conn, add_timeout_func, remove_timeout_func, timeout_toggled_func, data):
    assert isinstance(conn, DBusConnection_p)
    assert callable(add_timeout_func) and callable(remove_timeout_func) and callable(timeout_toggled_func)

    cb_keeper, py_obj = _new_watch_or_timeout_callback_keeper(DBusAddTimeoutCallbackFunction,
                                                              DBusRemoveOrToggleTimeoutCallbackFunction,
                                                              add_timeout_func, remove_timeout_func,
                                                              timeout_toggled_func, data)
    res = DBUS.dbus_connection_set_timeout_functions(conn, cb_keeper.c_add_func, cb_keeper.c_remove_func,
                                                     cb_keeper.c_toggled_func, py_obj, _c_free_py_object)
    return res


class _WakeupCallbackKeeper(object):
    def __init__(self, wakeup_func, data):
        self.wakeup_func = wakeup_func
        self.data = data
        self.c_wakeup_func = DBusWakeupMainFunction(self.wakeup_cb)

    def wakeup_cb(self, _):
        self.wakeup_func(self.data)


def dbus_connection_set_wakeup_main_function(conn, wakeup_func, data):
    assert isinstance(conn, DBusConnection_p)
    assert callable(wakeup_func)

    cb_keeper, py_obj = _register_py_object(_WakeupCallbackKeeper(wakeup_func, data))
    DBUS.dbus_connection_set_wakeup_main_function(conn, cb_keeper.c_wakeup_func, py_obj, _c_free_py_object)


def dbus_connection_get_unix_fd(conn):
    assert isinstance(conn, DBusConnection_p)

    fd = ctypes.c_int()
    if not DBUS.dbus_connection_get_unix_fd(conn, ctypes.byref(fd)):
        return None
    return fd.value


def dbus_connection_get_socket(conn):
    assert isinstance(conn, DBusConnection_p)

    fd = ctypes.c_int()
    if not DBUS.dbus_connection_get_socket(conn, ctypes.byref(fd)):
        return None
    return fd.value


def dbus_timeout_get_data(timeout):
    assert isinstance(timeout, DBusTimeout_p)
    ptr = DBUS.dbus_timeout_get_data(timeout)
    if ptr is None:
        return None
    return ctypes.cast(ptr, ctypes.py_object).value


def dbus_timeout_set_data(timeout, data):
    assert isinstance(timeout, DBusTimeout_p)
    _, py_obj = _register_py_object(data)
    return DBUS.dbus_timeout_set_data(timeout, py_obj, _c_free_py_object)


def dbus_watch_get_data(watch):
    assert isinstance(watch, DBusWatch_p)
    ptr = DBUS.dbus_watch_get_data(watch)
    if ptr is None:
        return None
    return ctypes.cast(ptr, ctypes.py_object).value


def dbus_watch_set_data(watch, data):
    assert isinstance(watch, DBusWatch_p)
    _, py_obj = _register_py_object(data)
    return DBUS.dbus_watch_set_data(watch, py_obj, _c_free_py_object)

dbus_connection_ref = DBUS.dbus_connection_ref
dbus_connection_unref = DBUS.dbus_connection_unref
dbus_connection_dispatch = DBUS.dbus_connection_dispatch
dbus_connection_get_dispatch_status = DBUS.dbus_connection_get_dispatch_status
dbus_watch_get_enabled = DBUS.dbus_watch_get_enabled
dbus_watch_get_flags = DBUS.dbus_watch_get_flags
dbus_watch_get_unix_fd = DBUS.dbus_watch_get_unix_fd
dbus_watch_get_socket = DBUS.dbus_watch_get_socket
dbus_watch_handle = DBUS.dbus_watch_handle
dbus_timeout_get_enabled = DBUS.dbus_timeout_get_enabled
dbus_timeout_handle = DBUS.dbus_timeout_handle
dbus_timeout_get_interval = DBUS.dbus_timeout_get_interval
