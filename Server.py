import random
from socket import *
from Packet import Packet
import sys
import time

serverSocket = socket(AF_INET, SOCK_DGRAM)

serverSocket.bind(('', int(sys.argv[1])))
while True:
	#To estimate RTT
	message, address = serverSocket.recvfrom(2048)
	packet = Packet.parse_packet(message)
	serverSocket.sendto(Packet(1,int('1010101010101010',2),'').packet,address)

	#To estimate FileSize
	while True:
		message, address = serverSocket.recvfrom(2048)
		packet = Packet.parse_packet(message)
		try:
			max_size = int(packet.data)
			#filename = packet.data.split(',')[0]
			#p = float(packet.data.split(',')[2])
			serverSocket.sendto(Packet(1,int('1010101010101010',2),'okay').packet,address)
			break
		except:
			serverSocket.sendto(Packet(1,int('1010101010101010',2),'no').packet,address)
			
	#print p,filename,max_size
	filename = sys.argv[2]
	p = float(sys.argv[3])

	latest_ack = 0
	f = open(filename,'w')
	while True:

		message, address = serverSocket.recvfrom(2048)
		msg = ''
		packet = Packet.parse_packet(message)
		if not packet == None:
			if packet.sequence_no<=latest_ack:
				if random.random()>p:
					latest_ack = packet.sequence_no + len(packet.data)
					serverSocket.sendto(Packet(latest_ack,int('1010101010101010',2),'').packet,address)
					f.write(packet.data)
				else:
					print 'Packet Loss, Sequence No. :' + str(packet.sequence_no)
		if latest_ack>=max_size:
			break
	f.close()
	serverSocket.sendto(Packet(latest_ack,int('1010101010101010',2),'DONE').packet,address)

			
	

