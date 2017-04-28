from array import array
import struct
from threading import Timer

class Packet:
	def __init__(self, sequence_no, is_data, data):
		self.sequence_no = sequence_no
		self.is_data = is_data
		self.data = data
		self.packet_header = 0
		self.checksum = 0
		self.generate_packet()
	
	
	def generate_packet(self):
		self.packet_header = self.sequence_no
		self.packet_header = self.packet_header<<32
		self.packet_header = self.packet_header + self.is_data
		#print "{0:064b}".format(self.packet_header)
		self.checksum = Packet.calculate_checksum(self.packet_header,self.data)
		shifted_checksum = self.checksum<<16
		self.packet_header = self.packet_header + shifted_checksum
		ph = struct.unpack("8B",struct.pack("!Q",self.packet_header))
		ph = list(ph)
		msg = array("B",self.data)
		ph.extend(msg)
		self.packet = array('B',ph).tostring()

	@staticmethod
	def parse_packet(packet):
		msg = array('B',packet)
		ph = msg[0:8]
		data = array('B',list(msg[8:])).tostring()
		checksum = msg[4]<<8
		checksum = checksum + msg[5]
		sequence_no = 0
		for i in range(0,4):
			sequence_no = sequence_no + (msg[i]<<((3-i)*8))
		is_data = msg[6]<<8
		is_data = is_data + msg[7]
		p = Packet(sequence_no, is_data, data)
		if checksum != p.checksum:
			return p
		else:
			return p

	
	@staticmethod
	def calculate_checksum(packet_header,val):
		ph = struct.unpack("8B", struct.pack("!Q", packet_header))
		ph = list(ph)
		msg = array("B",val)
		ph.extend(msg)
		msg = ph
		checksum = 0
		for i in range(0,len(msg),2):
			l = msg[i]
			l = l<<8
			if i == len(msg) - 1:
				l = l + 0
			else:
				l = l + msg[i+1]
			checksum = Packet.ones_comp_add16(checksum,l)
		return checksum
	
	@staticmethod	
	def ones_comp_add16(num1,num2):
		MOD = 1<<16
		result = num1 + num2
		return result if result < MOD else (result+1) % MOD
