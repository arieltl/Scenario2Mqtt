from mqtt import MqttManager
from telnetManager import TelnetManager
import json

class Manager:
	def __init__(self, modules) -> None:
		self.modules = {module.id: module for module in modules}
		self.mqtt = MqttManager(self.on_message)
		self.telnet = TelnetManager()
		for modId in self.modules:
			module = self.modules[modId]
			for zone in module.zones:
				#publish home assistant auto discovery light json mode unique id = modId+zone
				#subscribe to modId+zone
				self.mqtt.publish(f"homeassistant/light/{modId}-{zone}/config", json.dumps({
					"schema": "json",
					"name": f"Scenario {modId} {zone}",
					"state_topic": f"ifsei/{modId}-{zone}/state",
					"command_topic": f"ifsei/{modId}-{zone}/set",
					"brightness": True,
					"unique_id":f"scenario-{modId}-{zone}",
					"brightness_scale": 63,
					"device": {
						"identifiers": f"scenario-{modId}-{zone}",
						"name": "Scenario Light" ,
						"model": "Dimmer Channel",
						"manufacturer": "Scenario"
					}
				}))
				self.mqtt.subscribe(f"ifsei/{modId}-{zone}/set")
				self.mqtt.subscribe(f"ifsei/{modId}-{zone}/state")


	def loop(self):
		self.mqtt.loop()
		msg = self.telnet.read()
		if msg is not None and msg.startswith("*D") and "z" in msg.lower():
			module = int(msg[1:3])
			if module not in self.modules:
				return
			zones_data = msg.lower().split("z")[1:]
			for zone_data in zones_data:
				zone = zone_data[0]
				brightness = int(zone_data[1:])
				self.modules[module].state[zone] = {"brightness": brightness,"state": "ON" if brightness > 0 else "OFF"}
				self.mqtt.publish(f"ifsei/{module}-{zone}/state", json.dumps(self.modules[module].state[zone]))
				
			
		
	def on_message(self, msg):
		print(msg.topic+" "+str(msg.payload))
		if msg.topic.startswith("ifsei/"):
			module, zone = [int(n) for n in msg.topic.split("/")[1].split("-")]
			data = json.loads(msg.payload)
			print(data)
			if "brightness" in data:
				self.modules[module].state[zone]["brightness"] = data["brightness"]
			if "state" in data:
				self.modules[module].state[zone]["state"] = data["state"]
				if data["state"] == "ON":
					self.telnet.write(f"$D{module:02d}Z{zone}{self.modules[module].state[zone]['brightness']:02d}T1")
				else:
					self.telnet.write(f"$D{module:02d}Z{zone}00T1")
			if msg.topic.endswith("state"):
				self.mqtt.client.unsubscribe(msg.topic)
			self.mqtt.publish(f"ifsei/{module}-{zone}/state", json.dumps(self.modules[module].state[zone]))
			
		