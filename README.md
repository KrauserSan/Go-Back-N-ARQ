# Go-Back-N-ARQ

In this project, I evaluated the efficiency of the two schemes, go-back-n and selective repeat ARQ, by building a multithreaded FTP server-client paradigm which works on UDP socket interface. Several experiments are performed on the window size and MSS to compute the efficiency of the schemes. A loss probability is introduced to better the performance computation metrics. Both, the server and client side was built using Python.
Project 2 toward ECE/CSC 573

GO-BACK-N ARQ

We wrote three Python files - Client, Server and Packet. 
To run the server, just type "python Server.py file-name port p". We specified the port no here rather than making it well known as we required different port numbers for doign the tasks simultaneously.
To run the Client, just type "python Client.py file-to-transfer window-size MSS server-host-name client-port"
