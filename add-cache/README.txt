Sample code server.py and client.py is used and modified for assignment 3.

server
------

To run the server, simple execute:

  python server.py


cache
-----

To run the cache, execute:

  python cache.py


client
------

To run the client, execute:

  python client.py http://host:port/file

where host is where the server is running (e.g. localhost), port is the port 
number reported by the server where it is running and file is the name of the 
file you want to retrieve.

-----

To connect with cache instead of server:

  python client.py -proxy cachehost:cacheport http://host:port/file

where cachehost is where the cache is running (e.g., localhost), cacheport is 
the port number reported by the cache.