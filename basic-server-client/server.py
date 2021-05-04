#!/usr/bin/python3

import socket
import time
import os
import os.path
from os import path
import datetime
import sys

# a method which is hard-coded that provide the response message for each status
def responseMessage(status, filename):
    timeGMT = 'Date:' + time.strftime("%a, %d %b %Y %I:%M:%S %p %Z")+ '\r\n'

    if (status==200):
        if(filename.split('.')[1] == 'jpg'  or filename.split('.')[1] == 'gif' or filename.split('.')[1] == 'jpeg'):
            contentType = 'Content-Type: image/jpeg/gif\r\n'
        else:
            contentType = 'Content-Type: text/html\r\n'

        modifiedTime = os.path.getmtime(filename)
        mtime_obj = datetime.datetime(*time.localtime(modifiedTime)[:6])
        mTime = "Last-Modified: " + mtime_obj.strftime("%a, %d %b %Y %I:%M:%S %p %Z") + "\r\n"

        contentLength = os.stat(filename).st_size

        response = "HTTP/1.1 200 OK\r\nConnection: close\r\n" + timeGMT + mTime + "Content-Length: {}\r\n".format(contentLength) + contentType + "\r\n[data not shown]\r\n Please check the file downloading.\r\n"

    if (status==404):
        response = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n" + timeGMT +'\r\n<html><head><meta http-equiv="Content-Type" content="text/html; charset=windows-1252"> \n\
<title>404 Not Found</title> \n\
</head><body data-new-gr-c-s-check-loaded="14.980.0"> \n\
<h1>Not Found</h1> \n\
The requested URL was not found on this server.<p> \n\
</p><hr> \n\
</body></html>\r\n'

    if (status==501):
        response = "HTTP/1.1 501 Method Not Implemented\r\nConnection: close\r\n" + timeGMT +'\r\n<html><head><meta http-equiv="Content-Type" content="text/html; charset=windows-1252"> \n\
<title>501 Method Not Implemented</title> \n\
</head><body data-new-gr-c-s-check-loaded="14.980.0"> \n\
<h1>Method Not Implemented</h1> \n\
Invalid method in request.<p> \n\
</p><hr> \n\
</body></html>\r\n'

    if (status==505):
        response = "HTTP/1.1 505 Version Not Supported\r\nConnection: close\r\n" + timeGMT +'\r\n<html><head><meta http-equiv="Content-Type" content="text/html; charset=windows-1252"> \n\
<title>505 Version Not Supported</title> \n\
</head><body data-new-gr-c-s-check-loaded="14.980.0"> \n\
<h1>Version Not Supported</h1> \n\
This web server only supports HTTP/1.1.<p> \n\
</p><hr> \n\
</body></html>\r\n'

    return response

serverDir = os.getcwd()

# get the hostname which server is running on
hostname = socket.gethostname()
PORT = 12000
# create TCP welcoming socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((hostname, PORT))
print("Host: " + hostname + "\nPort:", PORT)

# server begins listening for incoming TCP requests
serverSocket.listen(1)

while True:
    try:
        print("\nThe server is waiting for connection...\n")
        # server waits on accept() for incoming requests
        connection, clientAddress = serverSocket.accept()
        clientRequest = connection.recv(1024).decode()

        print('Request Message From Connected Client:')
        print(clientRequest)

        try:
            request = clientRequest.split('\r\n')[0]

            # analyze the request
            method = request.split(' ')[0]
            filename = request.split(' ')[1].split('/')[1]
            version = request.split(' ')[2]
        # threw error if the commend does not valid, and go back to while re-wait client request
        except IndexError:
            print("\nERROR, error information is sent back to client.")
            response = "ERROR. Please enter the valid common e.g., GET /filename.html HTTP/1.1"
            connection.send(response.encode())
            connection.close()
            continue

        if(path.exists(filename)):
            status = 200
        # 501 Method Not Implemented if method != GET
        elif(method != 'GET'):
            status = 501
        # 505 Version Not Supported if version != HTTP/1.1
        elif(version != 'HTTP/1.1'):
            status = 505
        else:
            status = 404

        # call the responseMessage to get response message
        response = responseMessage(status, filename)
        # send the message back to the client
        connection.send(response.encode())

        # if status == 200, which means the request file exists, send the file data to the client
        if(status == 200):
            f = open(filename,'rb')
            l = f.read(1024)
            while (l):
                connection.send(l)
                l = f.read(1024)
            f.close()

        print("The response message is sent back to the client, close connection with the client.")
        connection.close()

    # server close only if keyboard interrupt happens
    except KeyboardInterrupt:
        serverSocket.close()
        sys.exit(0)
