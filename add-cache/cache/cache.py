#!/usr/bin/python3

import socket
import signal
import sys
import os
import datetime
import time

# A constant for buffer size adn expiration time
BUFFER_SIZE = 1024
EXPIRATION_TIME = 120

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

# A function for creating conditional GET messages.
def prepare_get_message(req_file ,file_name):
    # if file exists in the cache, send conditional GET messages

    modifiedTime = os.path.getmtime(req_file)
    mtime_obj = datetime.datetime(*time.localtime(modifiedTime)[:6])
    mtime_obj.strftime('%a, %d %b %Y %H:%M:%S EDT')
    request = f'GET {file_name} HTTP/1.1\r\nIf-modified-since:{mtime_obj}\r\n\r\n'

    # otherwise, send HTTP GET message only
    #else:
    #    request = f'GET {file_name} HTTP/1.1\r\n\r\n'

    return request

# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.
# f' GET {file_name} HTTP/1.1\r\nHost: {host}:port}\r\n\r\n'
def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

# Create an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    elif value == '523':
        message = message + value + ' Origin Is Unreachable\r\n' + date_string + '\r\n'
    return message

# Send the given response and file back to the client.

def send_response_to_client(sock, code, file_name):

    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'

    # Get size of file

    file_size = os.path.getsize(file_name)

    # Construct header and send it

    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break

# Check whether the file in cache is expired

def check_file_timestamp(modifiedTime):
    # Get the current time
    current_time = datetime.datetime.now()
    time_diff = current_time - modifiedTime
    # Compare the time difference with expiration time
    return (time_diff.total_seconds() > EXPIRATION_TIME)

# Read a file from the socket and print it out.  (For errors primarily.)

def print_file_from_socket(sock, bytes_to_read):

    bytes_read = 0
    while (bytes_read < bytes_to_read):
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode())

# Read a file from the socket and save it out.

def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)

def main():

    # Register signal handler for shutting down the cache

    signal.signal(signal.SIGINT, signal_handler)

    # A random port is picked and will be printed out for clients to use

    cache_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cache_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(cache_socket.getsockname()[1]))
    cache_socket.listen(1)

    # Keep the cache running forever like server

    while(1):
        print('\nWaiting for incoming client connection ...\n')
        connection, client_address = cache_socket.accept()
        print('Accepted connection from client address:', client_address)
        print('Connection to client established, waiting to receive message...')

        # We obtain our request from the socket.  We look at the request and
        # figure out what to do based on the contents of things.

        request = get_line_from_socket(connection)
        print('Received request from connected client:  ' + request)
        request_list = request.split()

        # Get the information of server hostname and port
        server = get_line_from_socket(connection)
        server_list = server.split(':')
        server_host = server_list[1]
        server_port = int(server_list[2])

        server_path = server_host + '_' + server_list[2]

        # Ignore other headers if included any
        while (get_line_from_socket(connection) != ''):
            pass

        # Get the filename from the request
        #filename_list = request_list[1].split('/')
        #file_name = filename_list[len(filename_list) - 1]
        file_name = request_list[1]

        # Rewrite the file location by server host and port information
        req_file = server_path + request_list[1]

        # Get the dirpath for later if the dir need to be created
        dir_list = req_file.split('/')
        dir_path = ''
        counter = 0
        while counter < len(dir_list) - 1:
            dir_path = dir_path + dir_list[counter] + '/'
            counter += 1

        # Check if requested file exists and check the file timestamp

        if (os.path.exists(req_file)):
            # Get the last modified time of the file
            modifiedTime = datetime.datetime.fromtimestamp(os.path.getmtime(req_file))
            # call the function to check the timestamp of the file
            expire = check_file_timestamp(modifiedTime)

            if expire:
                conditionValue = False
                os.remove(req_file)
                print("The file expired, need update from server")
            else:
                conditionValue = True

        else:
            conditionValue = False

        try:
            socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_connection.connect((server_host, server_port))
        except ConnectionRefusedError:
            print('Error:  That host or port is not accepting connections.')
            send_response_to_client(connection, '523', '523.html')
            continue

        # The connection was successful, so we can prep and send our message.

        #print("Connecting to server ...")
        if conditionValue:
            message = prepare_get_message(req_file, file_name)
            print("File exists in the cache, connect server for checking file version...")
        else:
            message = request + '\r\n' + '\r\n\r\n'
            print("File does not exist in the cache, connect server for downloading...")
        socket_connection.send(message.encode())

        # Receive the response from the server and start taking a look at it

        response_line = get_line_from_socket(socket_connection)
        response_list = response_line.split(' ')
        headers_done = False

        # Error from server
        if response_list[1] != '200' and response_list[1] != '304':
            # send the same response message to client if error
            send_response_to_client(connection, response_list[1], response_list[1] + '.html')

            # Delete the file if exists when receive 404
            if response_list[1] == '404':
                try:
                    os.remove(req_file)
                except OSError:
                    pass

            #connection.send(socket_connection.recv(1))
            print('Error:  An error response was received from the server.  Details:\n')
            print(response_line);
            bytes_to_read = 0
            while (not headers_done):
                header_line = get_line_from_socket(socket_connection)
                print(header_line)
                header_list = header_line.split(' ')
                if (header_line == ''):
                    headers_done = True
                elif (header_list[0] == 'Content-Length:'):
                    bytes_to_read = int(header_list[1])
            print_file_from_socket(socket_connection, bytes_to_read)

        else:
            # Receive 200, then download file to the specified folder from the server
            if response_list[1] == '200':
                print(response_line)

                # Create the dir if the dir does not exist
                if not os.path.isdir(dir_path):
                    os.makedirs(dir_path)

                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(socket_connection)
                    header_list = header_line.split(' ')
                    print(header_line)
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])

                save_file_from_socket(socket_connection, bytes_to_read, req_file)
                print('Success:  Server is sending file.  Downloading it now.')

            # Receive 304, there is no need to update the file
            # Print the response to cache
            elif response_list[1] == '304':
                print(response_line);
                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(socket_connection)
                    print(header_line)
                    header_list = header_line.split(' ')
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])
                print_file_from_socket(socket_connection, bytes_to_read)

            # Send the specified file to server
            print('Requested file good to go!  Sending file ...')
            send_response_to_client(connection, '200', req_file)

        # We are all done with this client, so close the connection and
        # Go back to get another one!

        connection.close();


if __name__ == '__main__':
    main()
