import telnetlib
import json
class TelnetManager:
	def __init__(self) -> None:
		with open('config.json') as f:
			config = json.load(f)["ifsei"]
		self.tn = telnetlib.Telnet(config["host"], config["port"])

	def read(self):
		return self.tn.read_until(bytes([0x0D]),timeout=0.1).decode()
		
	def write(self, command):
		self.tn.write(bytes(command, 'ascii') + bytes([0x0D]))