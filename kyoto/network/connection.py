import kyoto.conf
import gevent.coros
import gevent.socket


class BaseConnectionManager(object):

    def __init__(self, address):
        self.address = address
        self.timeout = kyoto.conf.settings.CONNECTION_TIMEOUT

    def create(self):
        """
        Creates TCP connection
        """
        connection = gevent.socket.create_connection(self.address, self.timeout)
        connection.setsockopt(gevent.socket.SOL_SOCKET, gevent.socket.SO_KEEPALIVE, 1)
        connection.setsockopt(gevent.socket.IPPROTO_TCP, gevent.socket.TCP_NODELAY, 1)
        return connection

    def destroy(self, connection):
        """
        Closes connection
        """
        connection.close()

    def is_alive(self, connection):
        """
        Checks that connection is still alive
        """
        return not connection.closed

    def acquire(self):
        """
        Acquires connection
        """
        raise NotImplementedError

    def release(self, connection):
        """
        Releases connection
        """
        raise NotImplementedError

    def clear(self):
        """
        Closes all opened connections, must be used in __del__ method
        """
        raise NotImplementedError

class SingleConnectionManager(BaseConnectionManager):

    """
    One connection per request
    """

    def acquire(self):
        return self.create()

    def release(self, connection):
        self.destroy(connection)

    def clear(self):
        pass

class SharedConnectionManager(BaseConnectionManager):

    """
    One shared connection with lock
    """

    def __init__(self, *args, **kwargs):
        self.connection = None
        self.semaphore = gevent.coros.BoundedSemaphore()
        super(SharedConnectionManager, self).__init__(*args, **kwargs)

    def acquire(self):
        if self.connection:
            if not self.is_alive(self.connection):
                self.destroy(self.connection)
                self.connection = self.create()
        else:
            self.connection = self.create()
        self.semaphore.acquire(timeout=self.timeout)
        return self.connection

    def release(self, connection):
        self.semaphore.release()

    def clear(self):
        if self.connection:
            self.semaphore.acquire()
            self.connection.close()
            self.semaphore.release()
