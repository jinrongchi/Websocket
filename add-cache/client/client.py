import socket
import os
import sys
import argparse
from urllib.parse import urlparse

# Define a constant for our buffer size

BUFFER_SIZE = 1024

# A function for creating HTTP GET messages.

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost:{host}:{port}\r\n\r\n'
    return request


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

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


# Our main function.

def main():

    # Check command line arguments to retrieve a URL.

    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to fetch with an HTTP GET request")
    # add to support -proxy comment line option
    parser.add_argument("-proxy", help="Proxy to fetch with a web cache connection")
    args = parser.parse_args()

    try:

        # If the cache is trying to connect to web cache
        # Keep track the information of hostname and port of cache for later
        if args.proxy:
            parsed_proxy = args.proxy.split(':')
            # The host name of web cache
            cache_host = parsed_proxy[0]
            # The port number of web cache
            cache_port = int(parsed_proxy[1])

        # Check the URL passed in and make sure it's valid.  If so, keep track of
        # things for later.
        parsed_url = urlparse(args.url)
        if ((parsed_url.scheme != 'http') or (parsed_url.port == None) or (parsed_url.path == '') or (parsed_url.path == '/') or (parsed_url.hostname == None)):
            raise ValueError
        server_host = parsed_url.hostname
        server_port = parsed_url.port
        file_name = parsed_url.path

    except ValueError:
        print('Error:  Invalid URL.  Enter a URL of the form:  http://host:port/file')
        sys.exit(1)

    if args.proxy:
        host = cache_host
        port = cache_port
        connect_message = "Connecting to cache ..."
        sending_message = "Connection to cache established. Sending message...\n"
    else:
        host = server_host
        port = server_port
        connect_message = "Connecting to server ..."
        sending_message = "Connection to server established. Sending message...\n"

    # Now we try to make a connection to the server.

    print(connect_message)
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.')
        sys.exit(1)

    # The connection was successful, so we can prep and send our message.

    print(sending_message)
    message = prepare_get_message(server_host, server_port, file_name)
    client_socket.send(message.encode())

    # Receive the response from the server and start taking a look at it

    response_line = get_line_from_socket(client_socket)
    response_list = response_line.split(' ')
    headers_done = False

    # If an error is returned from the server, we dump everything sent and
    # exit right away.
    print(response_list[1])
    if response_list[1] != '200':
        print('Error:  An error response was received from the server.  Details:\n')
        print(response_line);
        bytes_to_read = 0
        while (not headers_done):
            header_line = get_line_from_socket(client_socket)
            print(header_line)
            header_list = header_line.split(' ')
            if (header_line == ''):
                headers_done = True
            elif (header_list[0] == 'Content-Length:'):
                bytes_to_read = int(header_list[1])
        print_file_from_socket(client_socket, bytes_to_read)
        sys.exit(1)


    # If it's OK, we retrieve and write the file out.

    else:

        print(response_line)

        # If requested file begins with a / we strip it off.

        while (file_name[0] == '/'):
            #file_name = file_name[1:]
            file_name = file_name.split('/')[-1]

        # Go through headers and find the size of the file, then save it.

        bytes_to_read = 0
        while (not headers_done):
            header_line = get_line_from_socket(client_socket)
            header_list = header_line.split(' ')
            print(header_line)
            if (header_line == ''):
                headers_done = True
            elif (header_list[0] == 'Content-Length:'):
                bytes_to_read = int(header_list[1])
        save_file_from_socket(client_socket, bytes_to_read, file_name)
        print('Success:  Server is sending file.  Downloading it now.')

if __name__ == '__main__':
    main()
