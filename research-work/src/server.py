import asyncore
import socket

class EchoHandler(asyncore.dispatcher_with_send):
    def __init__(self, sock, chunk_size=8192):
        self.chunk_size = chunk_size
        asyncore.dispatcher.__init__(self, sock=sock)
        self.data_to_write = []

    def handle_read(self):
        data = self.recv(self.chunk_size)
        self.data_to_write.insert(0, data)

    def writable(self):
        response = bool(self.data_to_write)
        return response

    def handle_write(self):
        data = self.data_to_write.pop()
        self.send(data)

    def handle_close(self):
        self.close()

class EchoServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print ('Incoming connection from %s' % repr(addr))
            handler = EchoHandler(sock)


if __name__ == '__main__':
    server = EchoServer('localhost', 8080)
    asyncore.loop()
