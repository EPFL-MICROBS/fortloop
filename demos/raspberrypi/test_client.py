import sys
import socket


if len(sys.argv) != 2:
    raise IOError("Must provide server address")

PORT = 4017
HOST = sys.argv[1]
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST,PORT))

while True:
    command = input('Enter your command: ')
    s.send(command.encode('utf-8'))
    rep = s.recv(1024)
    print(rep)
    if command == "shutdown":
        break
s.close()
