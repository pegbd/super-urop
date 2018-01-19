import asyncore, socket

class HTTPClientSender(asyncore.dispatcher):
    def __init__(self, host, path):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, 8080))

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_write(self):
        while True:
            inp = input('arousal/valence:')
            input_check = inp.split(' ')

            if len(input_check) == 2:
                try:
                    float(input_check[0])
                    float(input_check[1])

                    print("Arousal and Valence Value to Send =" + inp)

                    self.send(inp.encode('utf-8'))
                except ValueError:
                    print('invalid input')


class HTTPClientReceiver(asyncore.dispatcher):
    def __init__(self, host, path):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, 8080))
        self.received_data = []
        self.chunk_size = 8192

        self.last_message = None
        self.last_message_read = True

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        data = self.recv(self.chunk_size)
        self.received_data.append(data)

        print(data)

        self.last_message = data
        self.last_message_read = False

    def message_available(self):
        return not self.last_message_read

    def get_message(self):
        return self.last_message


if __name__ == '__main__':
    client = HTTPClientSender('localhost', '/')
    asyncore.loop()
