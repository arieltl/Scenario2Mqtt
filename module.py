import json
			
class Zone:
	def __init__(self, id) -> None:
		self.id = id
		self.state = dict()

	def process_ifsei_msg(self, msg, *args):
		return
	def process_ha_msg(self, msg):
		return
	

class DimmerZone(Zone):
	def __init__(self, id) -> None:
		super().__init__(id)
		self.state = {"state":"OFF", "brightness":0}

	def process_ifsei_msg(self, status,*args):
		self.state["brightness"] = status
		self.state["state"] = "ON" if status > 0 else "OFF"

	def process_ha_msg(self, msg):
		data = json.loads(msg)
		if "brightness" in data:
			self.state["brightness"] = data["brightness"]
		if "state" in data:
			self.state["state"] = data["state"]
			if data["state"] == "ON":
				if self.state["brightness"] == 0:
					self.state["brightness"] = 63
			else:
				self.state["brightness"] = 0
		return ((self.id, self.state["brightness"]),)
	
class SwitchZone(Zone):
	def __init__(self, id) -> None:
		super().__init__(id)
		self.state = {"state":"OFF"}

	def process_ifsei_msg(self, status,*args):
		self.state["state"] = "ON" if status > 0 else "OFF"
	def process_ha_msg(self, msg):
		data = json.loads(msg)
		if "state" in data:
			self.state["state"] = data["state"]
		return ((self.id,63 if self.state["state"] == "ON" else 0),)
class BlindsZone(Zone):
	def __init__(self, open_zone_n,close_zone_n) -> None:
		super().__init__(open_zone_n)
		self.close_zone_n = close_zone_n
		self.state = "stopped"
	def process_ifsei_msg(self, status,*args):
		if self.state == "opening":
			if status == 0 and args[0] == self.id:
				self.state = "stopped"
		elif self.state == "closing":
			if self.state == 0 and args[0] == self.close_zone_n:
				self.state = "stopped"
		if status>0:
			self.state["state"] = "opening" if args[0] == self.id else "closing"
	def process_ha_msg(self, data):
		if data == "open":
			self.state = "opening"
		elif data == "close":
			self.state = "closing"
		elif data == "stop":
			self.state = "stopped"
		return ((self.id,63 if self.state == "opening" else 0),(self.close_zone_n,63 if self.state== "closing" else 0))

class Module:
	def __init__(self, id, zones:list[Zone]) -> None:
		self.id = id
		self.zones: dict[int,Zone] = dict()
		for zone in zones:
			self.zones[zone.id] = zone
			if isinstance(zone,BlindsZone):
				self.zones[zone.close_zone_n] = zone
		self.state = dict()
		
	def process_telnet_msg(self, msg):
		changed_zones = []
		zones_data = msg.lower().split("z")[1:]
		for zone_data in zones_data:
			zone_n = int(zone_data[0])
			if zone_n not in self.zones:
				continue
			zone = self.zones[zone_n]
			zone_status = int(zone_data[1:])
			zone.process_ifsei_msg(zone_status)
			changed_zones.append(zone_n)
		return changed_zones
	
	def process_mqtt_msg(self, msg, zone_n):
		telnet_msg = ""
		if zone_n not in self.zones:
			return ""
		zone_status = self.zones[zone_n].process_ha_msg(msg)
		return f"$D{self.id:02d}"+"".join(f"Z{z:01d}{v:02d}" for z,v in zone_status)+"T1"
		
			
#Olde architechture
# class DimmerModule:
# 	def __init__(self, id, zones) -> None:
# 		self.id = id
# 		self.zones = set(zones)
# 		self.state = dict()
# 		for zone in zones:
# 			self.state[zone] = {"state":"OFF", "brightness":0}


# 	def process_telnet_msg(self, msg):
# 		changed_zones = []
# 		zones_data = msg.lower().split("z")[1:]
# 		for zone_data in zones_data:
# 			zone = zone_data[0]
# 			changed_zones.append(zone)
# 			brightness = int(zone_data[1:])
# 			self.state[zone] = {"brightness": brightness,"state": "ON" if brightness > 0 else "OFF"}
# 		return changed_zones
	
# 	def process_mqtt_msg(self, msg, zone):
# 		telnet_msg = ""
# 		data = json.loads(msg.payload)
# 		print(data)
# 		if "brightness" in data:
# 			self.state[zone]["brightness"] = data["brightness"]
# 		if "state" in data:
# 			self.state[zone]["state"] = data["state"]
# 			if data["state"] == "ON":
# 				if self.state[zone]["brightness"] == 0:
# 					self.state[zone]["brightness"] = 63
# 				return f"$D{self.id:02d}Z{zone}{self.state[zone]['brightness']:02d}T1"
# 			else:
# 				return f"$D{self.id:02d}Z{zone}00T1"