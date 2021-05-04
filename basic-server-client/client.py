#!/usr/bin/python3

import socket
import sys
import os

downloadDir = os.getcwd()

# analyze the hostname and port from command line: http://host:port/filename
url = sys.argv[1]
serverHost = url.split("/")[2].split(":")[0]
serverPort = int(url.split("/")[2].split(":")[1])
filename = url.split("/")[3]

# create TCP socket for server
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverHost, serverPort))


# wait for the request e.g., GET /index.html HTTP/1.1
request = input("Connect successfully, please enter your request: ")
# add the Host: head to the request
request += "\r\n" + "Host: " + serverHost + "\r\n" + "Connection: close\r\nAccept-language: en\r\n\r\n"
# send the request to server
clientSocket.send(request.encode())

response = clientSocket.recv(1024)

# receive the file data from server and write it to the file
with open(filename, 'wb') as f:
    while True:
        data = clientSocket.recv(1024)
        if not data:
            break
        # write data to a file
        f.write(data)

# delete the file if the status is not 200, which will create an empty file
if os.stat(filename).st_size == 0:
    os.remove(filename)

print("\nResponse Message From Connected Server:")
print(response.decode())

clientSocket.close()
