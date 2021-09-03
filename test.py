# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 08:38:01 2019

@author: bpanneti
"""
import socket, threading
class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
 
    def handle_client(self, client):
        # Server will just close the connection after it opens it
        print('client received')
        client.close()
        return

    def start_listening(self):
        sock = socket.socket()
        sock.bind((self.host, self.port))
        sock.listen(5)

        client, addr = sock.accept()
        client_handler = threading.Thread(target=self.handle_client,args=(client,))
        client_handler.start()
def main():
    server = Server('127.0.0.1',8080)
    server.start_listening()
    print('done')
if __name__ == "__main__":
    main()