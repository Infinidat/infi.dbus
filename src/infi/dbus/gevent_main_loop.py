import gevent
import gevent.hub
import gevent.event
from .libdbus import (dbus_connection_set_watch_functions, dbus_connection_set_timeout_functions,
                      dbus_connection_set_wakeup_main_function, dbus_watch_get_enabled, dbus_timeout_get_enabled,
                      dbus_connection_ref, dbus_connection_unref, dbus_watch_get_socket,
                      dbus_watch_get_flags, DBUS_WATCH_READABLE, DBUS_WATCH_WRITABLE,
                      dbus_timeout_get_interval, dbus_timeout_handle, dbus_watch_handle,
                      dbus_connection_dispatch, dbus_connection_get_dispatch_status,
                      DBUS_DISPATCH_DATA_REMAINS, dbus_timeout_get_data, dbus_timeout_set_data,
                      dbus_watch_get_data, dbus_watch_set_data)
from .python_dbus_binding import DBusPythonMainLoop

__all__ = ['GEventMainLoop', 'set_debug_enabled']


_debug_enabled = False


def _debug(msg, *args, **kwargs):
    global _debug_enabled
    if _debug_enabled:
        print("<>" + msg.format(*args, **kwargs))


def set_debug_enabled(flag):
    global _debug_enabled
    _debug_enabled = flag


class WakeupException(Exception):
    pass


class Watch(object):
    def __init__(self, dbus_connection, watch):
        self.dbus_connection = dbus_connection
        self.watch = watch
        self.fd = dbus_watch_get_socket(watch)
        self.io = None
        self.canceled = False

    def schedule(self):
        _debug("watch.schedule fd={}", self.fd)
        self.canceled = False
        self.clear()
        if dbus_watch_get_enabled(self.watch):
            flags = dbus_watch_get_flags(self.watch)
            gevent_flags = 0
            if flags & DBUS_WATCH_READABLE:
                _debug("watch.schedule DBUS_WATCH_READABLE")
                gevent_flags |= 1
            if flags & DBUS_WATCH_WRITABLE:
                _debug("watch.schedule DBUS_WATCH_WRITABLE")
                gevent_flags |= 2

            if gevent_flags != 0:
                self.io = gevent.hub.get_hub().loop.io(self.fd, gevent_flags)
                self.io.start(self._trigger, pass_events=True)

    def cancel(self):
        _debug("watch.cancel")
        self.canceled = True
        self.clear()

    def clear(self):
        if self.io:
            self.io.stop()
            self.io = None

    def _trigger(self, events):
        _debug("watch._trigger events={}", events)
        if dbus_watch_get_enabled(self.watch):
            dbus_connection_ref(self.dbus_connection)
            try:
                dbus_flags = 0
                if events & 1:
                    dbus_flags |= DBUS_WATCH_READABLE
                if events & 2:
                    dbus_flags |= DBUS_WATCH_WRITABLE
                dbus_watch_handle(self.watch, dbus_flags)
            finally:
                dbus_connection_unref(self.dbus_connection)
            if not self.canceled:
                self.schedule()


class Timeout(object):
    def __init__(self, dbus_connection, timeout):
        self.dbus_connection = dbus_connection
        self.timeout = timeout
        self.timer = None

    def schedule(self):
        interval = float(dbus_timeout_get_interval(self.timeout)) / 1000
        _debug("timeout.schedule interval={}", interval)
        self.timer = gevent.hub.get_hub().loop.timer(interval)
        self.timer.start(self._trigger)

    def cancel(self):
        self.clear()

    def clear(self):
        if self.timer:
            self.timer.stop()
            self.timer = None

    def _trigger(self):
        dbus_connection_ref(self.dbus_connection)
        try:
            dbus_timeout_handle(self.timeout)
        finally:
            dbus_connection_unref(self.dbus_connection)


class ConnectionHolder(object):
    def __init__(self, dbus_connection):
        self.dbus_connection = dbus_connection
        self.watch_flags = 0
        self.wakeup_event = gevent.event.Event()
        self.shutdown = False
        self.thread = None
        self.selecting = False
        self.id_counter = 0

    def spawn(self):
        self.thread = gevent.spawn(self.run)

    def run(self):
        if not dbus_connection_set_watch_functions(self.dbus_connection, self.add_watch, self.remove_watch,
                                                   self.watch_toggled, None):
            raise Exception("dbus_connection_set_watch_functions failed")
        if not dbus_connection_set_timeout_functions(self.dbus_connection, self.add_timeout, self.remove_timeout,
                                                     self.timeout_toggled, None):
            raise Exception("dbus_connection_set_timeout_functions failed")

        dbus_connection_set_wakeup_main_function(self.dbus_connection, self.wakeup, None)

        while not self.shutdown:
            _debug("wakup event: wait")
            self.wakeup_event.wait()
            self.wakeup_event.clear()
            _debug("wakup event: woke up")
            need_dispatch = dbus_connection_get_dispatch_status(self.dbus_connection) == DBUS_DISPATCH_DATA_REMAINS
            while need_dispatch:
                dbus_connection_ref(self.dbus_connection)
                try:
                    need_dispatch = dbus_connection_dispatch(self.dbus_connection) == DBUS_DISPATCH_DATA_REMAINS
                finally:
                    dbus_connection_unref(self.dbus_connection)
                if need_dispatch:
                    gevent.sleep(0)  # don't starve other threads

    def add_watch(self, watch, _=None):
        _debug("add_watch {} {}", watch, _)
        if not dbus_watch_get_enabled(watch):
            _debug("add_watch: not enabled, returning.")
            return True

        py_watch = dbus_watch_get_data(watch)
        if py_watch:
            _debug("add_watch: canceling existing watch")
            py_watch.cancel()

        py_watch = Watch(self.dbus_connection, watch)
        dbus_watch_set_data(watch, py_watch)
        py_watch.schedule()
        return True

    def remove_watch(self, watch, _=None):
        _debug("remove_watch {} {}", watch, _)

        py_watch = dbus_watch_get_data(watch)
        if py_watch:
            py_watch.cancel()
            dbus_watch_set_data(watch, None)
        else:
            _debug("WARNING: remove_watch called with an unknown watch.")

        return True

    def watch_toggled(self, watch, _=None):
        _debug("watch_toggled {} {}", watch, _)
        if dbus_watch_get_enabled(watch):
            return self.remove_watch(watch, _)
        else:
            return self.add_watch(watch, _)

    def add_timeout(self, timeout, _=None):
        _debug("add_timeout {} {}", timeout, _)
        if not dbus_timeout_get_enabled(timeout):
            _debug("add_timeout: not enabled, returning.")
            return True

        py_timeout = dbus_timeout_get_data(timeout)
        if py_timeout:
            _debug("add_timeout: canceling existing timeout")
            py_timeout.cancel()

        py_timeout = Timeout(self.dbus_connection, timeout)
        dbus_timeout_set_data(timeout, py_timeout)
        py_timeout.schedule()

        return True

    def remove_timeout(self, timeout, _=None):
        _debug("remove_timeout {} {}", timeout, _)

        py_timeout = dbus_timeout_get_data(timeout)
        if py_timeout:
            py_timeout.cancel()
            dbus_timeout_set_data(timeout, None)
        else:
            _debug("WARNING: remove_timeout called with an unknown timeout.")

        return True

    def timeout_toggled(self, timeout, _=None):
        _debug("timeout_toggled {} {}", timeout, _)
        if dbus_timeout_get_enabled(timeout):
            return self.remove_timeout(timeout, _)
        else:
            return self.add_timeout(timeout, _)

    def _on_timeout(self, timeout):
        _debug("_on_timeout {}", timeout)

        dbus_connection_ref(self.dbus_connection)
        try:
            dbus_timeout_handle(timeout)
        finally:
            dbus_connection_unref(self.dbus_connection)

    def wakeup(self, _=None):
        _debug("wakeup")
        self.wakeup_event.set()


# We try here to do similar things like dbus-gmain.c (glib's dbus integration).
class GEventMainLoop(DBusPythonMainLoop):
    def __init__(self, set_as_default=False):
        super(GEventMainLoop, self).__init__()

        if set_as_default:
            self.set_as_default()

    def conn_setup(self, dbus_connection):
        _debug("conn_setup")
        ConnectionHolder(dbus_connection).spawn()
        return True

    def run(self):
        while True:
            gevent.sleep(0.1)
