After running the server.py, the server window will display its hostname and port for the client to connect

The client.py is needed to run with standard URL as its command argument
  
```bash	
python client.py http://host:12000/file
```

After the client connects to the server, the client window will wait for the users to enter their requests
```bash
GET /filename.html HTML/1.1
```

The requested file will be searched in the folder where stores server.py,
and if the file exists, it will be downloaded to the floder where stores client.py

The method os.getcwd() and path.exists(filename) is used in the code to get the working path
Therefore, the /filename.html (in the commend) will work directly, detailed path does not required.
