import time
from socket import *
import os
import math
from _cffi_backend import string
import sys
from array import array
import struct
from Packet import Packet
from threading import Thread
from threading import RLock
from threading import Timer
from threading import Lock
import random
import logging
import signal
import traceback
import thread

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

serverName = ""
serverPort = 7735
N = None
start = 0
end = 0
prev_start = 0
prev_end = 0
segment = {}
timeout_lock = RLock()
end_lock = RLock()
last_ack_seq = 0
RTT = 0
MSS = 0

class ClientListener(Thread):
	def __init__(self,clientSocket, fileSize):
		Thread.__init__(self)
		self.clientSocket = clientSocket
		self.fileSize = fileSize
	
	def run(self):
		global segment,last_ack_seq,end,end_lock,prev_start, prev_end,MSS
		max_seq = sorted(segment.keys())[-1:]
		logging.debug(str(max_seq))
		last_ack_seq = -1
		prev_packet_seq = 0
		while True:
			message,address = self.clientSocket.recvfrom(2048)
			packet = Packet.parse_packet(message)
			if not packet == None:
				#print last_ack_seq,packet.sequence_no
				if packet.sequence_no>last_ack_seq:
					#timeout_lock.acquire()
					no_of_packets = (packet.sequence_no - last_ack_seq)/MSS
					if no_of_packets>2: #Cumulative ACKs
						signal.alarm(0)
						s = sorted(segment.keys()).index(last_ack_seq) + 1
						e = sorted(segment.keys()).index(packet.sequence_no)
						for i in range(s,e):
							r = sorted(segment.keys())[i]
							segment[r][1] = True
						last_ack_seq = segment[sorted(segment.keys())[e-1]][0].sequence_no
					#timeout_lock.release()
				if last_ack_seq<packet.sequence_no and last_ack_seq>=packet.sequence_no-(2*MSS) or last_ack_seq == -1:
					#timeout_lock.acquire()
					#logging.debug('ACK. Sequence No. :' + str(packet.sequence_no) + ', Packet Size:' +  str(len(packet.data)))
					last_ack_seq = prev_packet_seq
					segment[last_ack_seq][1] = True
					prev_packet_seq = packet.sequence_no
					end = end + 1
					prev_start = prev_start + 1
					prev_end = end
					#timeout_lock.release()
				if packet.sequence_no >= self.fileSize:
					break

	def stop(self):
		self.stopped = True


def read_file(sendFile, maxSegments, MSS):
	global segment
	with open(sendFile,"rb") as f:
		byte = f.read(1)
		msg = []
		count = 1
		SegmentNumber = 0
		while SegmentNumber <maxSegments:
			msg.append(byte)
			if count%MSS == 0 or f.read==None:
				sequenceNumber = (SegmentNumber) * MSS
				message = ''.join(msg)
				msg = []
				#segment.append(packetFormat(sequenceNumber, message))
				segment[sequenceNumber] = [Packet(sequenceNumber,int('0101010101010101',2),message),False]
				SegmentNumber = SegmentNumber+1

			
			byte = f.read(1)
			count +=1

	

# reads the file in bytes and makes a segment if the byte count reaches MSS value
def main(clientSocket):
	global N, start, end, segment, timeout_lock, end_lock, prev_start, prev_end,MSS,serverPort
	
	count = 1
	sendFile = sys.argv[1]
	N = int(sys.argv[2])
	MSS = int(sys.argv[3])
	SegmentNumber = 0
	sequenceNumber = 1
	fileSize = os.path.getsize(sendFile)
	maxSegments = math.ceil(float(fileSize)/MSS)
	c= ClientListener(clientSocket, fileSize)
	addr =(sys.argv[4], serverPort)
	signal.signal(signal.SIGALRM, trigger_restart)

	#Testing RTT
	m = ''
	for i in range(0,MSS):
		m = m + 'a'
	p = Packet(0,int('01010101010101010',2),m)
	s = time.time()
	clientSocket.sendto(p.packet,addr)
	ack,a = clientSocket.recvfrom(2048)
	e = time.time()
	RTT = 10*(e - s)
	RTT = 0.1
	print RTT

	#Sending maxsize
	while True:
		p = Packet(0,int('01010101010101010',2),str(fileSize))
		clientSocket.sendto(p.packet,addr)
		ack,a = clientSocket.recvfrom(2048)
		ack_pack = Packet.parse_packet(ack)
		if 'okay' in ack_pack.data:
			break

	#print 'FileSize sent'


	
	
	'''with open(sendFile,"rb") as f:
		byte = f.read(1)
		msg = []
		while SegmentNumber <maxSegments:
			msg.append(byte)
			if count%MSS == 0 or f.read==None:
				sequenceNumber = (SegmentNumber) * MSS
				message = ''.join(msg)
				msg = []
				#segment.append(packetFormat(sequenceNumber, message))
				segment[sequenceNumber] = [Packet(sequenceNumber,int('0101010101010101',2),message),False]
				SegmentNumber = SegmentNumber+1


			byte = f.read(1)
			count +=1'''
	thread.start_new_thread( read_file,(sendFile, maxSegments, MSS, ) )
	i = 0
	start = 0
	end = start + N - 1
	prev_end = end
	prev_start = start
	while len(segment)==0:
		time.sleep(0.01)

	c.start()
	while True:
		l = sorted(segment.keys())
		while start>=len(l) and start<maxSegments - 1:
			l = sorted(segment.keys())
			time.sleep(0.01)
		if start>=maxSegments:
			if segment[l[-1]][1] == True:
				signal.alarm(0)
				break
		else:	
			l = sorted(segment.keys())
			p = segment[l[start]][0]
			clientSocket.sendto(p.packet, addr)
			#logging.debug(str(l[start]) + ' ' + str(p.sequence_no))
			signal.setitimer(signal.ITIMER_REAL, RTT)
			#print 'SENDING Sequence No. :' + str(p.sequence_no) + ', Packet Size:' +  str(len(p.data))
			start = start + 1
			if start>end:
				while start>end:
					time.sleep(0.001)
				continue
	c.stop()

def trigger_restart(s,f):
	global segment,start,end, timeout_lock, last_ack_seq
	signal.alarm(0)
	timeout_lock.acquire()
	if start >= len(segment):
		start = sorted(segment.keys()).index(last_ack_seq)+1
		logging.debug('Timeout, Sequence No ' + str(sorted(segment.keys())[start]) + ',Everything acked till ' + str(last_ack_seq))
	elif last_ack_seq<sorted(segment.keys())[start]:
		if last_ack_seq == -1:
			temp = sorted(segment.keys()).index(0)
		else:
			temp = sorted(segment.keys()).index(last_ack_seq) + 1
		if segment[sorted(segment.keys())[temp]][1] == False:
			if last_ack_seq == -1:
				start = sorted(segment.keys()).index(0)
			else:
				start = sorted(segment.keys()).index(last_ack_seq) + 1
			logging.debug('Timeout, Sequence No ' + str(sorted(segment.keys())[start]) + ',Everything acked till ' + str(last_ack_seq))
	#print traceback.print_stack(f)
	timeout_lock.release()
		


clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.bind(('',int(sys.argv[5])))
main(clientSocket)	
message,address = clientSocket.recvfrom(2048)
