server
------

To run the server, simple execute:

  python server.py


load balancer
-------------

To run balancer, execute:

  python balancer.py host1:port1,host2:port2,host3:port3

where host is where the server is running (e.g., localhost), port is the port
number reported by the server. For multiple servers, separate them with comma.

Note: load balancer uses thread to automatically rank the servers' performances (1 time per 2 min)


client
------

To run the client, execute:

  python client.py http://host:port/file

where host is where the load balancer is running (e.g. localhost), port is the port 
number reported by the load balancer where it is running and file is the name of the 
file you want to retrieve.

