#!/usr/bin/python3

import socket
import signal
import sys
import time
from random import choice
import threading
import datetime

# Constant for our buffer size

BUFFER_SIZE = 1024

# Constant for updating time period

CHECK_FREQUENCY = 120

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

def prepare_server_message(host, port, file_name):
    info = f'HTTP/1.1 301 Moved Permanently\r\nhttp://{host}:{port}/{file_name}\r\n\r\n'
    return info

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n'
    return request

# Read a file from the socket and save it out.

def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)

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

# Connect to each server for performance test
def server_performance_test(host, port):

    try:
        balancer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        balancer_socket.connect((host,port))
    except ConnectionRefusedError:
        print('Error:  That host or port of server is not accepting connections.')
        return False

    # The connection was successful, so we can prep and send our message.
    message = prepare_get_message(host, port, 'test.jpg')
    # The time that balancer send the request
    request_time = datetime.datetime.now()
    balancer_socket.send(message.encode())

    # Receive the response from the server
    response_line = get_line_from_socket(balancer_socket)
    response_list = response_line.split(' ')
    headers_done = False

    # Error occured
    if response_list[1] != '200':
        return False

    # If it's OK, we retrieve and write the file out.
    else:

        bytes_to_read = 0
        while (not headers_done):
            header_line = get_line_from_socket(balancer_socket)
            header_list = header_line.split(' ')
            if (header_line == ''):
                headers_done = True
            elif (header_list[0] == 'Content-Length:'):
                bytes_to_read = int(header_list[1])
        save_file_from_socket(balancer_socket, bytes_to_read, 'test.jpg')

    # Now count the time that the given server perform the test

    respone_time = datetime.datetime.now()
    total_time = respone_time - request_time
    # Convert into seconds since the number maybe really small
    total_time = total_time.total_seconds()
    return total_time

# Randomly pick a server for client
def arrange_server_to_client():
    num_server = len(ranked_server_list)
    i = 0
    temp_list = []
    while(i <= (num_server - 1)):
        temp = num_server - i
        while(temp > 0):
            temp_list.append(i)
            temp -= 1
        i += 1

    return choice(temp_list)

# Check performance for each server

def check_server_performance():
    servers_info = sys.argv[1]
    server_list = servers_info.split(",")
    while True:
        global ranked_server_list
        ranked_server_list = []
        print("Load balancer is doing the server performance test...")

        list_rtime = {}
        for eachserver in server_list:
            host = eachserver.split(":")[0]
            port = int(eachserver.split(":")[1])
            performance_time = server_performance_test(host, port)

            if not performance_time:
                print("Load balancer may need to be restarted since " + eachserver + " is not available.")
            else:
                list_rtime[eachserver] = performance_time

        list_rtime = {key: value for key, value in sorted(list_rtime.items(), key=lambda item: item[1])}

        for key in list_rtime:
            ranked_server_list.append(key)

        print("Available servers are ranked as below:")
        for key in ranked_server_list:
            print(f'{key}\t\tPerformance time: {list_rtime[key]}')

        time.sleep(CHECK_FREQUENCY)


# A threading for updating the server test performance
def update_serve_performance():
    t1 = threading.Thread(target=check_server_performance)
    t1.start()

def main():

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(1)

    # Keep the server running forever.

    while(1):
        print('Waiting for incoming client connection ...')
        conn, addr = server_socket.accept()
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...')

        request = get_line_from_socket(conn)
        print('Received request:  ' + request)
        request_list = request.split()
        file_name = request_list[1]
        while (file_name[0] == '/'):
            file_name = file_name[1:]

        server_index = arrange_server_to_client()
        print(f'Server {ranked_server_list[server_index]} is picked to connect with client.')

        host = ranked_server_list[server_index].split(":")[0]
        port = ranked_server_list[server_index].split(":")[1]

        message = prepare_server_message(host, port, file_name)
        conn.send(message.encode())

        # We are all done with this client, so close the connection and
        # Go back to get another one!

        #conn.close();


if __name__ == '__main__':
    update_serve_performance()
    main()
