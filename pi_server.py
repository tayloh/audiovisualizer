# Takes visualization data from the audio_client and displays it on leds.

import socket
import struct

IP = "127.0.0.1"
PORT = 65432
CHUNK = 1024 * 2
BUFFER_SIZE = CHUNK * 4 # size of each chunk of audioframes in bytes

tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSocket.bind((IP, PORT))

tcpSocket.listen()
connection, sourceAddr = tcpSocket.accept()

print("Connection from:", sourceAddr)

while True:
    data = connection.recv(BUFFER_SIZE)
    if not data:
        break
    dataInt = struct.unpack(str(CHUNK) + "i", data)
    print(sum(dataInt)/len(dataInt))

connection.close()
tcpSocket.close()
