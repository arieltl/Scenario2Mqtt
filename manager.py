from mqtt import MqttManager
from telnetManager import TelnetManager
from module import *
import json

class Manager:
	def __init__(self, modules:Module) -> None:
		self.modules : dict[int,Module] = {module.id: module for module in modules}
		self.mqtt = MqttManager(self.on_message)
		self.telnet = TelnetManager()
		for modId in self.modules:
			module = self.modules[modId]
			for zone in module.zones.values():
				#publish home assistant auto discovery light json mode unique id = modId+zone
				#subscribe to modId+zone
				zone_n = zone.id
				if isinstance(zone, BlindsZone):
					module_config = {
						"name": f"Blinds {modId} {zone_n}",
						"command_topic": f"ifsei/{modId}-{zone_n}/set",
						"state_topic": f"ifsei/{modId}-{zone_n}/state",
						"position_topic": f"ifsei/{modId}-{zone_n}/position",
						"payload_open": "open",
						"payload_close": "close",
						"payload_stop": "stop",
						"state_stopped": "stopped",
						"state_opening": "opening",
						"state_closing": "closing",
						"optimistic": False,
						"unique_id":f"blinds-{modId}-{zone_n}",
						"qos": 2,
						"device": {
							"identifiers": f"blinds-{modId}-{zone_n}",
							"name": "Blinds Device" ,
							"model": "Blinds Channel",
							"manufacturer": "Blinds"
						}
					}
					self.mqtt.publish(f"homeassistant/cover/{modId}-{zone_n}/config", module_config)
					self.mqtt.publish(f"ifsei/{modId}-{zone_n}/position", 50)
					self.mqtt.subscribe(f"ifsei/{modId}-{zone_n}/set")
					continue

				module_config = {
					"schema": "json",
					"name": f"Scenario {modId} {zone_n}",
					"state_topic": f"ifsei/{modId}-{zone_n}/state",
					"command_topic": f"ifsei/{modId}-{zone_n}/set",
					"unique_id":f"scenario-{modId}-{zone_n}",
					"qos": 2,
					"device": {
						"identifiers": f"scenario-{modId}-{zone_n}",
						"name": "Scenario Device" ,
						"model": "Switch Channel",
						"manufacturer": "Scenario"
					}
				}
				#check if zone is dimmable and set brightness to true and brightness_scale to 63
				if isinstance(zone, DimmerZone):
					module_config["brightness"] = True
					module_config["brightness_scale"] = 63
					module_config["device"]["model"] = "Dimmer Channel"
				
				self.mqtt.publish(f"homeassistant/light/{modId}-{zone_n}/config", module_config)
				self.mqtt.subscribe(f"ifsei/{modId}-{zone_n}/set")
				


	def loop(self):
		self.mqtt.loop()
		msg = self.telnet.read()
		print(msg)
		if msg is not None and msg.startswith("*D") and "z" in msg.lower():
			module = int(msg[2:4])
			if module not in self.modules:
				return
			
			zones_data = self.modules[module].process_telnet_msg(msg)
			for zone in zones_data:
				print(zone)
				self.mqtt.publish(f"ifsei/{module}-{zone}/state", self.modules[module].zones[zone].state)
			
				
			
		
	def on_message(self, msg):
		print(msg.topic+" "+str(msg.payload))
		if msg.topic.startswith("ifsei/"):
			module, zone = [int(n) for n in msg.topic.split("/")[1].split("-")]
			telnet_msg = self.modules[module].process_mqtt_msg(msg.payload.decode(), zone)
			if telnet_msg != "":
				self.telnet.write(telnet_msg)
			if msg.topic.endswith("state"):
				self.mqtt.client.unsubscribe(msg.topic)
			
			self.mqtt.publish(f"ifsei/{module}-{zone}/state", self.modules[module].zones[zone].state)
			
		